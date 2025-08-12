# train_mpnet_peft.py
import os
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from typing import List, Iterator, Tuple, Optional
import random
import math
import glob
import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, models, losses
from torch.utils.data import DataLoader
import torch
from peft import get_peft_model, LoraConfig, TaskType
from tqdm.auto import tqdm

# -------------------------
# Config / hyperparameters
# -------------------------
def _get_data_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "data")

DATA_DIR = _get_data_dir()  # directory with lyric CSV/PKL files
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
OUT_DIR = "mpnet_lyrics_lora"
EPOCHS = 3
TRAIN_BATCH_SIZE = 16            # per device batch size
GRAD_ACCUM_STEPS = 2            # gradient accumulation -> effective batch = TRAIN_BATCH_SIZE * GRAD_ACCUM_STEPS
LR = 2e-5
FP16 = True                      # use mixed precision
MAX_CHUNKS_TO_LOAD = None       # None or integer
SAMPLES_PER_EPOCH = 200_000     # how many training pairs to sample per epoch (synthetic/weakly supervised)
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
SEED = 42

device = "cuda" if torch.cuda.is_available() else "cpu"
random.seed(SEED)


# -------------------------
# Utilities for data
# -------------------------
def _find_lyric_chunks(data_dir: str) -> List[str]:
    """Find expected lyric chunks: song_lyrics_chunk_{n}.csv (and optionally .pkl)."""
    patterns = [
        os.path.join(data_dir, "song_lyrics_chunk_*.csv"),
        os.path.join(data_dir, "song_lyrics_chunk_*.pkl"),
    ]
    files: List[str] = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    files = sorted(files)
    if MAX_CHUNKS_TO_LOAD:
        files = files[:MAX_CHUNKS_TO_LOAD]
    return files


def _normalize_lyrics_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Normalize and validate columns used for training.

    Required: 'lyrics'. Optional: 'title', 'artist'. Will create 'song_id' if missing.
    """
    if "lyrics" not in df.columns:
        raise ValueError(f"Missing required 'lyrics' column in {source}.")

    # Ensure song_id exists
    if "song_id" not in df.columns:
        df = df.copy()
        df["song_id"] = df.index.astype(str)
    else:
        df = df.copy()
        df["song_id"] = df["song_id"].astype(str)

    # Standardize lyrics to string and drop empties
    df = df.dropna(subset=["lyrics"])  # type: ignore[index]
    df["lyrics"] = df["lyrics"].astype(str)

    # Optional columns
    keep_cols = ["song_id"]
    if "title" in df.columns:
        keep_cols.append("title")
    if "artist" in df.columns:
        keep_cols.append("artist")
    keep_cols.append("lyrics")
    return df[keep_cols]


def _load_lyrics_chunk(path: str) -> pd.DataFrame:
    """Load a chunk file and ensure it contains required fields.
    Accepts CSV/PKL and validates presence of a lyrics-like column.
    """
    if path.endswith(".pkl"):
        df = pd.read_pickle(path)
    else:
        df = pd.read_csv(path)
    return _normalize_lyrics_columns(df, source=path)


def _chunk_into_passages(lyrics: str, max_len_chars: int = 800) -> List[str]:
    """Split a lyrics string into passages/chunks. Keep them reasonably long (verses, choruses)."""
    # naive split by blank lines first
    parts = [p.strip() for p in lyrics.split("\n\n") if p.strip()]
    if not parts:
        parts = [lyrics.strip()]
    # merge micro parts to ensure minimum length
    merged = []
    cur = ""
    for p in parts:
        if len(cur) + len(p) < 200 and cur:
            cur += "\n\n" + p
        else:
            if cur:
                merged.append(cur)
            cur = p
    if cur:
        merged.append(cur)
    # ensure chunks are not too long
    final = []
    for m in merged:
        if len(m) <= max_len_chars:
            final.append(m)
        else:
            # split long chunk into sentence-ish pieces (fallback)
            for i in range(0, len(m), max_len_chars):
                final.append(m[i:i+max_len_chars])
    return final


def build_positive_pairs_from_chunk(df: pd.DataFrame, samples_per_song: int = 2) -> Iterator[InputExample]:
    """For each song, produce InputExample pairs (passage_a, passage_b) where both are from same song."""
    for _, row in df.iterrows():
        lyrics = str(row["lyrics"])
        passages = _chunk_into_passages(lyrics)
        if len(passages) < 2:
            continue
        # sample random pairs from same song
        for _ in range(samples_per_song):
            a, b = random.sample(passages, 2)
            yield InputExample(texts=[a, b])


def build_synthetic_query_pairs(df: pd.DataFrame, samples_per_song: int = 1) -> Iterator[InputExample]:
    """Create (synthetic_query, passage) pairs by templating/paraphrasing a passage into a query. This is cheap and deterministic."""
    templates = [
        "I'm going through: {}",
        "This sounds like: {}",
        "I feel like: {}",
        "Relates to: {}",
        "A story about: {}"
    ]
    for _, row in df.iterrows():
        lyrics = str(row["lyrics"])
        passages = _chunk_into_passages(lyrics)
        if not passages:
            continue
        for _ in range(samples_per_song):
            passage = random.choice(passages)
            # create a short summary-ish seed: take first sentence or 20 words
            words = passage.split()
            seed = " ".join(words[:20])
            template = random.choice(templates)
            synthetic_query = template.format(seed)
            yield InputExample(texts=[synthetic_query, passage])


def streaming_training_examples(data_dir: str, total_samples: int) -> List[InputExample]:
    """Sample training pairs from data_dir across chunks to build a single epoch's examples.
       We randomly walk chunks to produce diversity without loading everything at once.
    """
    files = _find_lyric_chunks(data_dir)
    if not files:
        raise FileNotFoundError(
            "No data files found. Expected 'song_lyrics_chunk_{n}.csv' (or .pkl) under the data directory."
        )
    examples = []
    # To avoid loading entire dataset, loop until we collect enough samples
    pbar = tqdm(total=total_samples, desc="Sampling training pairs")
    file_cycle = list(files)
    fidx = 0
    attempts_without_progress = 0
    last_examples_count = 0
    while len(examples) < total_samples:
        path = file_cycle[fidx % len(file_cycle)]
        fidx += 1
        try:
            df = _load_lyrics_chunk(path)
        except Exception as e:
            print(f"Skipping {path} due to error: {e}")
            continue
        # from this chunk, sample some songs
        sample_song_count = min(200, max(10, total_samples // (max(len(files), 1) * 4)))
        sampled = df.sample(min(sample_song_count, len(df)))
        # generate positives and synthetic queries
        for ex in build_positive_pairs_from_chunk(sampled, samples_per_song=1):
            examples.append(ex)
            pbar.update(1)
            if len(examples) >= total_samples:
                break
        if len(examples) >= total_samples:
            break
        for ex in build_synthetic_query_pairs(sampled, samples_per_song=1):
            examples.append(ex)
            pbar.update(1)
            if len(examples) >= total_samples:
                break

        # progress guard: if we loop through all files without adding examples, abort
        if fidx % max(len(file_cycle), 1) == 0:
            if len(examples) == last_examples_count:
                attempts_without_progress += 1
            else:
                attempts_without_progress = 0
                last_examples_count = len(examples)
            if attempts_without_progress >= 2:
                raise FileNotFoundError("No usable chunks with a 'lyrics' column were found in the expected files: other_columns_chunk_{n}.csv/pkl")
    pbar.close()
    random.shuffle(examples)
    return examples


# -------------------------
# Model + PEFT / LoRA
# -------------------------
def prepare_model_with_lora(base_model_name: str, lora_r: int = 8, lora_alpha: int = 16, lora_dropout: float = 0.05):
    print("Loading base SentenceTransformer:", base_model_name)
    model = SentenceTransformer(base_model_name)
    # SentencesTransformer is a torch.nn.Module; the underlying HuggingFace transformer is usually at model[0].auto_model
    # but to be robust we try a couple of access patterns.
    auto_model = None
    try:
        auto_model = model[0].auto_model
    except Exception:
        # fallback: find the first module of type transformers.PreTrainedModel
        for m in model.modules():
            # check for attribute config -> heuristic
            if hasattr(m, "config") and hasattr(m, "forward"):
                auto_model = m
                break
    if auto_model is None:
        raise RuntimeError("Couldn't find underlying HF transformer model inside SentenceTransformer wrapper.")

    print("Applying LoRA (PEFT) to transformer...")
    peft_config = LoraConfig(
        task_type=TaskType.FEATURE_EXTRACTION,
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["query", "key", "value", "dense", "dense_h_to_4h", "dense_4h_to_h"],  # common targets; PEFT ignores missing ones
        lora_dropout=lora_dropout,
        bias="none",
        inference_mode=False
    )
    wrapped = get_peft_model(auto_model, peft_config)
    # assign back the wrapped HF model into the sentence-transformer wrapper
    try:
        model[0].auto_model = wrapped
    except Exception:
        # fallback assign to detected module
        # NOTE: this may not work for all ST wrappers, but usually model[0].auto_model is present
        for name, m in model.named_modules():
            if hasattr(m, "config") and hasattr(m, "forward"):
                # replace by identity? This is edge-case; raise to inform user
                raise RuntimeError("Unable to set PEFT-wrapped model back into SentenceTransformer automatically.")

    # Move the model to device (keeps HF wrapped module on same device)
    model.to(device)
    return model


# -------------------------
# Training orchestration
# -------------------------
def train():
    print(f"Device: {device}. FP16: {FP16}. Batch size: {TRAIN_BATCH_SIZE}, grad acc: {GRAD_ACCUM_STEPS}")

    model = prepare_model_with_lora(MODEL_NAME, lora_r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT)

    for epoch in range(EPOCHS):
        print(f"\n==== EPOCH {epoch+1}/{EPOCHS} ====")
        # sample/generate examples for this epoch
        examples = streaming_training_examples(DATA_DIR, SAMPLES_PER_EPOCH)
        print(f"Collected {len(examples)} training examples")

        train_dataloader = DataLoader(examples, shuffle=True, batch_size=TRAIN_BATCH_SIZE, drop_last=False)
        train_loss = losses.MultipleNegativesRankingLoss(model)

        # sentence-transformers .fit wraps training; pass parameters to control optimizer
        model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=1,
            steps_per_epoch=math.ceil(len(examples) / TRAIN_BATCH_SIZE),
            warmup_steps=100,
            optimizer_params={'lr': LR},
            checkpoint_path=os.path.join(OUT_DIR, "checkpoint"),
            checkpoint_save_steps=0,  # disable internal checkpointing if you prefer
            use_amp=FP16,
            show_progress_bar=True
        )

        # Save intermediate model
        save_path = os.path.join(OUT_DIR, f"epoch_{epoch+1}")
        os.makedirs(save_path, exist_ok=True)
        print("Saving model to", save_path)
        model.save(save_path)

    print("Training complete. Final model saved to", OUT_DIR)


if __name__ == "__main__":
    train()
