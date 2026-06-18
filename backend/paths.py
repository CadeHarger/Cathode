import os

BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
CHUNK_INDICES = (1, 2, 3, 4)


def get_data_dir() -> str:
    return os.path.join(BACKEND_ROOT, "data")


def get_models_dir() -> str:
    return os.path.join(BACKEND_ROOT, "models")


def get_finetuned_model_path() -> str:
    return os.path.join(get_models_dir(), "mpnet_lyrics_lora", "epoch_1")


def chunk_is_complete(chunk_index: int) -> bool:
    """True if a chunk has both embeddings and metadata files."""
    data_dir = get_data_dir()
    emb_path = os.path.join(data_dir, f"embeddings_chunk_{chunk_index}.npy")
    if not os.path.exists(emb_path):
        return False
    pkl_path = os.path.join(data_dir, f"other_columns_chunk_{chunk_index}.pkl")
    csv_path = os.path.join(data_dir, f"other_columns_chunk_{chunk_index}.csv")
    return os.path.exists(pkl_path) or os.path.exists(csv_path)


def list_present_chunks() -> list[int]:
    return [i for i in CHUNK_INDICES if chunk_is_complete(i)]


def list_missing_chunks() -> list[int]:
    present = set(list_present_chunks())
    return [i for i in CHUNK_INDICES if i not in present]


def data_files_present() -> bool:
    """True if at least one complete chunk exists."""
    return bool(list_present_chunks())


def describe_missing_data() -> str:
    data_dir = get_data_dir()
    return (
        f"No dataset chunks found in {data_dir}/. "
        "See README.md for Kaggle download and embedding pipeline instructions. "
        "Need at least one of embeddings_chunk_1..4.npy with matching other_columns_chunk_*.pkl"
    )


def format_chunk_status() -> str:
    present = list_present_chunks()
    missing = list_missing_chunks()
    if not present:
        return "no chunks loaded"
    parts = [f"loaded chunks {present}"]
    if missing:
        parts.append(f"missing chunks {missing}")
    return "; ".join(parts)
