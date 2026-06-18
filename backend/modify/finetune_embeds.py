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
from multiprocessing import Pool
import time

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from paths import get_data_dir

DATA_DIR = get_data_dir()
OUT_DIR = "mpnet_lyrics_lora"
EPOCHS = 3
TRAIN_BATCH_SIZE = 18            # per device batch size
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
        # Use memory mapping for faster CSV loading
        df = pd.read_csv(path, memory_map=True, engine='c')
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


def build_positive_pairs_from_chunk(df: pd.DataFrame, samples_per_song: int = 2) -> List[InputExample]:
    """Process all songs at once instead of row by row - vectorized approach."""
    examples = []
    
    # Split all lyrics at once - vectorized operation
    df['passages'] = df['lyrics'].astype(str).apply(_chunk_into_passages)
    
    # Filter songs with enough passages
    df = df[df['passages'].apply(len) >= 2]
    
    print(f"    Processing {len(df)} songs with sufficient passages")
    
    # Generate pairs for all songs simultaneously
    for _, row in df.iterrows():
        passages = row['passages']
        # Generate multiple pairs per song
        for _ in range(samples_per_song):
            if len(passages) >= 2:
                a, b = random.sample(passages, 2)
                examples.append(InputExample(texts=[a, b]))
    
    print(f"    Generated {len(examples)} positive pairs")
    return examples


def build_synthetic_query_pairs(df: pd.DataFrame, samples_per_song: int = 1) -> List[InputExample]:
    """Create (synthetic_query, passage) pairs - vectorized approach."""
    examples = []
    templates = [
        "I'm going through: {}",
        "This sounds like: {}",
        "I feel like: {}",
        "Relates to: {}",
        "A story about: {}"
    ]
    
    # Use the passages already computed in build_positive_pairs_from_chunk
    if 'passages' not in df.columns:
        df['passages'] = df['lyrics'].astype(str).apply(_chunk_into_passages)
    
    # Filter songs with passages
    df = df[df['passages'].apply(len) > 0]
    
    print(f"    Processing {len(df)} songs for synthetic queries")
    
    for _, row in df.iterrows():
        passages = row['passages']
        for _ in range(samples_per_song):
            if passages:
                passage = random.choice(passages)
                # create a short summary-ish seed: take first sentence or 20 words
                words = passage.split()
                seed = " ".join(words[:20])
                template = random.choice(templates)
                synthetic_query = template.format(seed)
                examples.append(InputExample(texts=[synthetic_query, passage]))
    
    print(f"    Generated {len(examples)} synthetic queries")
    return examples


def parallel_load_chunks(file_paths, n_workers=4):
    """Load chunks in parallel using multiprocessing."""
    print(f"Loading {len(file_paths)} chunks in parallel using {n_workers} workers...")
    start_time = time.time()
    
    with Pool(n_workers) as pool:
        results = pool.map(_load_lyrics_chunk, file_paths)
    
    # Filter out None results (failed loads)
    loaded_chunks = [r for r in results if r is not None]
    load_time = time.time() - start_time
    print(f"Loaded {len(loaded_chunks)} chunks in {load_time:.2f} seconds")
    
    return loaded_chunks


def batch_process_chunks(chunks, total_samples, samples_per_song=1):
    """Process multiple chunks efficiently to generate target number of samples."""
    examples = []
    
    # Calculate how many samples we need per chunk to reach our target
    # Each song can generate multiple examples (positive pairs + synthetic queries)
    samples_per_chunk = total_samples // len(chunks)
    print(f"Target: {total_samples} samples, {len(chunks)} chunks, ~{samples_per_chunk} samples per chunk")
    
    for chunk_idx, chunk in enumerate(chunks):
        print(f"Processing chunk {chunk_idx + 1}/{len(chunks)} (shape: {chunk.shape})")
        
        # Calculate how many songs we need to sample from this chunk
        # We need enough songs to generate samples_per_chunk examples
        # Each song generates (samples_per_song * 2) examples (positive + synthetic)
        examples_per_song = samples_per_song * 2  # positive + synthetic
        songs_needed = max(100, samples_per_chunk // examples_per_song)
        
        # Sample songs from this chunk
        sampled = chunk.sample(min(songs_needed, len(chunk)))
        print(f"  Sampled {len(sampled)} songs from chunk")
        
        # Generate examples from this chunk
        positive_examples = build_positive_pairs_from_chunk(sampled, samples_per_song)
        synthetic_examples = build_synthetic_query_pairs(sampled, samples_per_song)
        
        chunk_examples = positive_examples + synthetic_examples
        examples.extend(chunk_examples)
        
        print(f"  Generated {len(chunk_examples)} examples from chunk (total: {len(examples)})")
        
        # If we have enough samples, we can stop early
        if len(examples) >= total_samples:
            print(f"  Reached target of {total_samples} samples, stopping early")
            break
    
    # Ensure we don't exceed the target
    final_examples = examples[:total_samples]
    print(f"Final sample count: {len(final_examples)}")
    
    return final_examples


def streaming_training_examples(data_dir: str, total_samples: int) -> List[InputExample]:
    """Optimized sampling using batch processing and parallel loading."""
    files = _find_lyric_chunks(data_dir)
    if not files:
        raise FileNotFoundError(
            "No data files found. Expected 'song_lyrics_chunk_{n}.csv' (or .pkl) under the data directory."
        )
    
    print(f"Found {len(files)} data files")
    
    # Load chunks in parallel
    chunks = parallel_load_chunks(files, n_workers=min(4, len(files)))
    
    if not chunks:
        raise FileNotFoundError("No usable chunks were loaded successfully")
    
    print(f"Processing {len(chunks)} loaded chunks...")
    
    # Process chunks in batches
    examples = batch_process_chunks(chunks, total_samples)
    
    print(f"Generated {len(examples)} training examples")
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
    
    # Ensure the PEFT model is also on the correct device
    wrapped.to(device)
    
    # Verify device placement
    print(f"Model device: {next(model.parameters()).device}")
    print(f"PEFT model device: {next(wrapped.parameters()).device}")
    
    return model


# -------------------------
# Training orchestration
# -------------------------
def train():
    print(f"Device: {device}. FP16: {FP16}. Batch size: {TRAIN_BATCH_SIZE}, grad acc: {GRAD_ACCUM_STEPS}")

    model = prepare_model_with_lora(MODEL_NAME, lora_r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT)

    for epoch in range(EPOCHS):
        print(f"\n==== EPOCH {epoch+1}/{EPOCHS} ====")
        
        # Verify model is still on GPU before training
        print(f"Model device before training: {next(model.parameters()).device}")
        if torch.cuda.is_available():
            print(f"CUDA memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
            print(f"CUDA memory cached: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
        
        # sample/generate examples for this epoch
        examples = streaming_training_examples(DATA_DIR, SAMPLES_PER_EPOCH)
        print(f"Collected {len(examples)} training examples")

        train_dataloader = DataLoader(examples, shuffle=True, batch_size=TRAIN_BATCH_SIZE, drop_last=False)
        train_loss = losses.MultipleNegativesRankingLoss(model)
        
        # Verify that the loss function is on the correct device
        print(f"Loss function device: {next(train_loss.parameters()).device if hasattr(train_loss, 'parameters') else 'N/A'}")

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
