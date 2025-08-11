import os
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import heapq
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple
from sentence_transformers import SentenceTransformer
import time
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor, as_completed


# Source: 
# https://www.kaggle.com/datasets/carlosgdcj/genius-song-lyrics-with-language-information


def _get_data_dir():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "data")


def _load_metadata_chunk(data_dir: str, chunk_index: int) -> pd.DataFrame:
    pkl_path = os.path.join(data_dir, f"other_columns_chunk_{chunk_index}.pkl")
    csv_path = os.path.join(data_dir, f"other_columns_chunk_{chunk_index}.csv")
    if os.path.exists(pkl_path):
        return pd.read_pickle(pkl_path)
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    raise FileNotFoundError(f"Missing metadata for chunk {chunk_index}: {pkl_path} or {csv_path}")


def _load_embeddings_chunk(data_dir: str, chunk_index: int) -> np.ndarray:
    emb_path = os.path.join(data_dir, f"embeddings_chunk_{chunk_index}.npy")
    if not os.path.exists(emb_path):
        raise FileNotFoundError(f"Missing embeddings for chunk {chunk_index}: {emb_path}")
    # mmap to keep memory low when iterating chunks
    return np.load(emb_path, mmap_mode="r")


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def _normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


@lru_cache(maxsize=2)
def _get_encoder(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def _infer_embeddings_dim(data_dir: str) -> Optional[int]:
    """Inspect the first available embeddings chunk to determine vector dimensionality."""
    for chunk_index in range(1, 5):
        emb_path = os.path.join(data_dir, f"embeddings_chunk_{chunk_index}.npy")
        if os.path.exists(emb_path):
            arr = np.load(emb_path, mmap_mode="r")
            if arr.ndim == 2 and arr.shape[1] > 0:
                return int(arr.shape[1])
    return None


def _choose_model_for_dim(emb_dim: Optional[int], requested_model: str) -> str:
    """Pick a SentenceTransformer model that matches the stored embedding dimension when possible."""
    if emb_dim is None:
        return requested_model
    if emb_dim == 384:
        return "all-MiniLM-L6-v2"
    if emb_dim == 768:
        return "all-mpnet-base-v2"
    return requested_model


def _chunk_topk(
    chunk_index: int,
    data_dir: str,
    query_embedding: np.ndarray,
    top_k: int,
    candidate_indices: Optional[List[int]] = None,
) -> List[Tuple[float, str, str, Optional[float]]]:
    emb_path = os.path.join(data_dir, f"embeddings_chunk_{chunk_index}.npy")
    if not os.path.exists(emb_path):
        return []

    embeddings = _load_embeddings_chunk(data_dir, chunk_index)
    metadata = _load_metadata_chunk(data_dir, chunk_index)

    if len(metadata) != embeddings.shape[0]:
        min_len = min(len(metadata), embeddings.shape[0])
        embeddings = embeddings[:min_len]
        metadata = metadata.iloc[:min_len]

    if len(metadata) == 0:
        return []

    # If embeddings appear pre-normalized (norm ~ 1), skip normalization
    should_normalize = True
    try:
        sample = np.asarray(embeddings[:512])
        if sample.size > 0:
            sample_norm = np.linalg.norm(sample, axis=1)
            mean_norm = float(np.mean(sample_norm))
            if 0.98 <= mean_norm <= 1.02:
                should_normalize = False
    except Exception:
        should_normalize = True

    if should_normalize:
        # Ensure float32 for stable normalization and matmul
        embeddings_arr = _normalize_rows(np.asarray(embeddings, dtype=np.float32, order="C"))
    else:
        # Use as-is, upcast to float32 for matmul if needed
        if embeddings.dtype != np.float32:
            embeddings_arr = np.asarray(embeddings, dtype=np.float32, order="C")
        else:
            embeddings_arr = embeddings  # may still be memmap

    cosine_similarities = embeddings_arr @ query_embedding

    # Vectorized scoring
    # Coerce non-numeric views to NaN, then fill with 1.0
    views = pd.to_numeric(metadata["views"], errors="coerce").fillna(1.0).to_numpy(dtype=np.float32)
    # Ensure views are at least 1 to avoid issues with log10
    views[views < 1] = 1.0
    
    # Multiplier boosts score for high-view songs.
    # A song with 10k views gets a 1.0x multiplier.
    # A song with 1M views (10^6) gets a 1.8x multiplier.
    views_multiplier = 1.0 + (np.log10(views) - 3.0) * 0.2
    # Set a floor for the multiplier to avoid overly penalizing low-view songs.
    np.maximum(views_multiplier, 0.1, out=views_multiplier)

    scores = cosine_similarities * views_multiplier
    
    # Invalidate scores for rows with missing title or artist
    invalid_mask = metadata[["title", "artist"]].isna().any(axis=1).to_numpy()
    scores[invalid_mask] = -1e9  # Use a large negative number

    if candidate_indices is not None:
        candidate_mask = np.zeros_like(scores, dtype=bool)
        candidate_mask[candidate_indices] = True
        scores[~candidate_mask] = -1e9


    n = scores.shape[0]
    
    # Efficiently find top_k from all scores
    k_for_partition = min(top_k, n)
    if k_for_partition <= 0:
        return []
        
    if n <= k_for_partition:
        # Sort all if k is larger or equal to n
        top_indices = np.argsort(-scores)
    else:
        # Use argpartition for efficiency when n is large
        top_indices = np.argpartition(scores, -k_for_partition)[-k_for_partition:]
        # Sort only the top_k results
        top_indices = top_indices[np.argsort(-scores[top_indices])]

    local = []
    for idx in top_indices:
        # Skip any invalidated rows that might still be included
        if scores[idx] < -1e8:
            continue
        row = metadata.iloc[int(idx)]
        score = float(scores[idx])
        # Title/artist should be valid here due to the score invalidation
        local.append((score, row["title"], row["artist"], row["views"]))

    # Release references to allow memmap closing in child
    del embeddings, metadata, cosine_similarities, scores
    return local


class VectorSearcher:
    def __init__(self, data_dir: Optional[str] = None, model_name: str = "all-mpnet-base-v2"):
        self.data_dir = data_dir or _get_data_dir()
        if not os.path.isdir(self.data_dir):
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

        inferred_dim = _infer_embeddings_dim(self.data_dir)
        self.model_name = _choose_model_for_dim(inferred_dim, model_name)
        self.model = _get_encoder(self.model_name)
        
        self.all_metadata = self._load_all_metadata()
        if not self.all_metadata.empty:
            self.all_metadata['norm_title'] = self.all_metadata['title'].str.lower().str.strip()
            self.all_metadata['norm_artist'] = self.all_metadata['artist'].str.lower().str.strip()

    def _load_all_metadata(self) -> pd.DataFrame:
        all_meta = []
        for i in range(1, 5): # Assuming up to 4 chunks
            try:
                meta_chunk = _load_metadata_chunk(self.data_dir, i)
                meta_chunk.reset_index(drop=True, inplace=True)
                meta_chunk['chunk_index'] = i
                meta_chunk['original_index'] = meta_chunk.index
                all_meta.append(meta_chunk)
            except FileNotFoundError:
                continue
        if not all_meta:
            return pd.DataFrame()
        return pd.concat(all_meta, ignore_index=True)

    def find_songs_in_dataset(self, spotify_songs: List[dict]) -> pd.DataFrame:
        if self.all_metadata.empty or not spotify_songs:
            return pd.DataFrame()

        titles = [(s.get('name') or "").lower().strip() for s in spotify_songs]
        artists = []
        for s in spotify_songs:
            artist_name = ""
            if s.get('artists') and s['artists']:
                first_artist = s['artists'][0]
                if first_artist and first_artist.get('name'):
                    artist_name = first_artist['name'].lower().strip()
            artists.append(artist_name)

        spotify_df = pd.DataFrame({'norm_title': titles, 'norm_artist': artists})
        spotify_df.drop_duplicates(inplace=True)
        
        found_df = pd.merge(self.all_metadata, spotify_df, on=['norm_title', 'norm_artist'], how='inner')
        return found_df

    def search(self, user_query: str, top_k: int = 7, candidates: Optional[pd.DataFrame] = None):
        query_embedding = self.model.encode(user_query, convert_to_tensor=False, normalize_embeddings=True)
        query_embedding = np.asarray(query_embedding, dtype=np.float32)

        if candidates is not None and not candidates.empty:
            return self._search_within_candidates(query_embedding, top_k, candidates)
        else:
            return self._search_all_chunks(query_embedding, top_k)

    def _search_all_chunks(self, query_embedding: np.ndarray, top_k: int):
        min_heap = []
        chunk_indices = [i for i in range(1, 5) if os.path.exists(os.path.join(self.data_dir, f"embeddings_chunk_{i}.npy"))]
        
        with ProcessPoolExecutor(max_workers=min(4, len(chunk_indices))) as executor:
            futures = [executor.submit(_chunk_topk, ci, self.data_dir, query_embedding, max(top_k, 10)) for ci in chunk_indices]
            
            for future in as_completed(futures):
                local_results = future.result()
                for score, title, artist, views in local_results:
                    if len(min_heap) < top_k:
                        heapq.heappush(min_heap, (score, title, artist, views))
                    elif score > min_heap[0][0]:
                        heapq.heapreplace(min_heap, (score, title, artist, views))
                        
        return sorted(min_heap, key=lambda x: x[0], reverse=True)

    def _search_within_candidates(self, query_embedding: np.ndarray, top_k: int, candidates: pd.DataFrame):
        candidates_by_chunk = candidates.groupby('chunk_index')
        min_heap = []

        with ProcessPoolExecutor(max_workers=min(4, len(candidates_by_chunk))) as executor:
            futures = []
            for chunk_idx, group in candidates_by_chunk:
                candidate_indices = group['original_index'].tolist()
                future = executor.submit(_chunk_topk, chunk_idx, self.data_dir, query_embedding, max(top_k, 10), candidate_indices)
                futures.append(future)

            for future in as_completed(futures):
                local_results = future.result()
                for score, title, artist, views in local_results:
                    if len(min_heap) < top_k:
                        heapq.heappush(min_heap, (score, title, artist, views))
                    elif score > min_heap[0][0]:
                        heapq.heapreplace(min_heap, (score, title, artist, views))

        return sorted(min_heap, key=lambda x: x[0], reverse=True)


def main():
    # This main function is here for standalone testing of the vector search.
    # The primary entry point for the application is main.py.
    try:
        searcher = VectorSearcher()
        user_query = input("Enter your search query describing the song theme/mood:\n> ").strip()
        if user_query:
            start_time = time.time()
            results = searcher.search(user_query, top_k=10)
            end_time = time.time()

            if not results:
                print("No results found.")
            else:
                print("\n" + "=" * 50)
                print("Top matches:")
                for rank, (score, title, artist, views) in enumerate(results, start=1):
                    print(f"{rank}. {title} — {artist} - views: {views} \t(Score: {score:.4f})")
                print("=" * 50)
            
            print(f"Time taken: {end_time - start_time:.2f} seconds")

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()