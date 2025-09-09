import os
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from load_model import load_finetuned_model
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages preloaded embeddings, metadata, and FAISS index for fast vector search.
    Loads all data into memory on initialization for optimal performance.
    """
    
    def __init__(self, data_dir: Optional[str] = None, model_name: str = "finetuned"):
        self.data_dir = data_dir or self._get_data_dir()
        self.model_name = model_name
        self.model = None
        self.embeddings = None
        self.metadata = None
        self.faiss_index = None
        self.embedding_dim = None
        
        # Initialize everything
        self._load_model()
        self._load_all_data()
        self._build_faiss_index()
        
        logger.info(f"✅ DataManager initialized with {len(self.metadata)} songs and FAISS index")
    
    def _get_data_dir(self) -> str:
        """Get the data directory path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "data")
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if self.model_name == "finetuned":
            try:
                self.model = load_finetuned_model()
                logger.info("✅ Using finetuned model for vector search")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load finetuned model: {e}")
                logger.info("🔄 Falling back to base model")
                self.model = SentenceTransformer("all-mpnet-base-v2")
        else:
            self.model = SentenceTransformer(self.model_name)
    
    def _load_embeddings_chunk(self, chunk_index: int) -> np.ndarray:
        """Load embeddings for a specific chunk"""
        emb_path = os.path.join(self.data_dir, f"embeddings_chunk_{chunk_index}.npy")
        if not os.path.exists(emb_path):
            raise FileNotFoundError(f"Missing embeddings for chunk {chunk_index}: {emb_path}")
        return np.load(emb_path)
    
    def _load_metadata_chunk(self, chunk_index: int) -> pd.DataFrame:
        """Load metadata for a specific chunk"""
        pkl_path = os.path.join(self.data_dir, f"other_columns_chunk_{chunk_index}.pkl")
        csv_path = os.path.join(self.data_dir, f"other_columns_chunk_{chunk_index}.csv")
        
        if os.path.exists(pkl_path):
            return pd.read_pickle(pkl_path)
        elif os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        else:
            raise FileNotFoundError(f"Missing metadata for chunk {chunk_index}")
    
    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit vectors"""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms
    
    def _load_all_data(self):
        """Load all embeddings and metadata into memory"""
        logger.info("Loading all embeddings and metadata into memory...")
        
        all_embeddings = []
        all_metadata = []
        
        for chunk_idx in range(1, 5):  # Assuming chunks 1-4
            try:
                # Load embeddings
                embeddings_chunk = self._load_embeddings_chunk(chunk_idx)
                
                # Load metadata
                metadata_chunk = self._load_metadata_chunk(chunk_idx)
                
                # Ensure they have the same length
                min_len = min(len(metadata_chunk), embeddings_chunk.shape[0])
                embeddings_chunk = embeddings_chunk[:min_len]
                metadata_chunk = metadata_chunk.iloc[:min_len].copy()
                
                # Add chunk information for tracking
                metadata_chunk['chunk_index'] = chunk_idx
                metadata_chunk['global_index'] = len(all_metadata) + metadata_chunk.index
                
                all_embeddings.append(embeddings_chunk)
                all_metadata.append(metadata_chunk)
                
                logger.info(f"Loaded chunk {chunk_idx}: {len(metadata_chunk)} songs")
                
            except FileNotFoundError:
                logger.warning(f"Chunk {chunk_idx} not found, skipping")
                continue
        
        if not all_embeddings:
            raise RuntimeError("No data chunks found!")
        
        # Concatenate all chunks
        self.embeddings = np.vstack(all_embeddings).astype(np.float32)
        self.metadata = pd.concat(all_metadata, ignore_index=True)
        
        # Normalize embeddings
        self.embeddings = self._normalize_embeddings(self.embeddings)
        self.embedding_dim = self.embeddings.shape[1]
        
        # Add normalized title/artist for matching
        self.metadata['norm_title'] = self.metadata['title'].str.lower().str.strip()
        self.metadata['norm_artist'] = self.metadata['artist'].str.lower().str.strip()
        
        logger.info(f"Loaded {len(self.metadata)} total songs with {self.embedding_dim}D embeddings")
    
    def _build_faiss_index(self):
        """Build FAISS index for fast similarity search"""
        logger.info("Building FAISS index...")
        
        # Use IndexFlatIP for inner product (cosine similarity with normalized vectors)
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Add all embeddings to the index
        self.faiss_index.add(self.embeddings)
        
        logger.info(f"✅ FAISS index built with {self.faiss_index.ntotal} vectors")
    
    def get_views_multiplier(self, views: np.ndarray) -> np.ndarray:
        """Calculate views-based score multiplier"""
        return 1.0 + ((np.log10(np.maximum(views, 1.0)) - 3.0) * 0.1)
    
    def search(self, user_query: str, top_k: int = 8, candidates: Optional[pd.DataFrame] = None) -> List[Dict]:
        """
        Perform vector search using preloaded data and FAISS index
        
        Args:
            user_query: The search query
            top_k: Number of results to return
            candidates: Optional DataFrame to restrict search to specific songs
            
        Returns:
            List of song dictionaries with scores
        """
        # Encode the query
        query_embedding = self.model.encode(
            user_query, 
            convert_to_tensor=False, 
            normalize_embeddings=True
        )
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        if candidates is not None and not candidates.empty:
            return self._search_within_candidates(query_embedding[0], top_k, candidates)
        else:
            return self._search_all(query_embedding[0], top_k)
    
    def _search_all(self, query_embedding: np.ndarray, top_k: int) -> List[Dict]:
        """Search across all songs using FAISS"""
        # Search with FAISS (returns more than top_k for reranking)
        search_k = min(top_k * 3, len(self.metadata))  # Get more candidates for reranking
        scores, indices = self.faiss_index.search(query_embedding.reshape(1, -1), search_k)
        
        # Flatten results
        scores = scores[0]
        indices = indices[0]
        
        # Apply views-based reranking
        return self._rerank_with_views(scores, indices, top_k)
    
    def _search_within_candidates(self, query_embedding: np.ndarray, top_k: int, candidates: pd.DataFrame) -> List[Dict]:
        """Search within specific candidate songs"""
        # Get indices of candidate songs
        candidate_indices = candidates['global_index'].values
        
        # Get embeddings for candidates
        candidate_embeddings = self.embeddings[candidate_indices]
        
        # Compute similarities
        similarities = np.dot(candidate_embeddings, query_embedding)
        
        # Get top candidates
        top_indices = np.argsort(-similarities)[:top_k * 2]  # Get more for reranking
        
        # Map back to global indices
        global_indices = candidate_indices[top_indices]
        scores = similarities[top_indices]
        
        return self._rerank_with_views(scores, global_indices, top_k)
    
    def _rerank_with_views(self, scores: np.ndarray, indices: np.ndarray, top_k: int) -> List[Dict]:
        """Apply views-based reranking to search results"""
        results = []
        
        for score, idx in zip(scores, indices):
            if idx >= len(self.metadata):  # Safety check
                continue
                
            row = self.metadata.iloc[idx]
            
            # Skip songs with missing title or artist
            if pd.isna(row['title']) or pd.isna(row['artist']):
                continue
            
            # Apply views multiplier
            views = pd.to_numeric(row['views'], errors='coerce')
            if pd.isna(views):
                views = 1.0
            views = max(views, 1.0)
            
            views_multiplier = self.get_views_multiplier(np.array([views]))[0]
            views_multiplier = max(views_multiplier, 0.1)  # Floor
            
            final_score = score * views_multiplier
            
            results.append({
                'score': float(final_score),
                'title': row['title'],
                'artist': row['artist'],
                'views': float(views),
                'raw_score': float(score),
                'views_multiplier': float(views_multiplier)
            })
        
        # Sort by final score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def find_songs_in_dataset(self, spotify_songs: List[dict]) -> pd.DataFrame:
        """Find Spotify songs in the dataset"""
        if not spotify_songs:
            return pd.DataFrame()
        
        # Extract normalized titles and artists from Spotify songs
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
        
        # Find matches in our dataset
        found_df = pd.merge(self.metadata, spotify_df, on=['norm_title', 'norm_artist'], how='inner')
        return found_df
    
    def get_total_songs(self) -> int:
        """Get total number of songs in the dataset"""
        return len(self.metadata) if self.metadata is not None else 0

# Global instance (will be initialized on server startup)
data_manager: Optional[DataManager] = None

def get_data_manager() -> DataManager:
    """Get the global data manager instance"""
    global data_manager
    if data_manager is None:
        raise RuntimeError("DataManager not initialized. Call initialize_data_manager() first.")
    return data_manager

def initialize_data_manager(data_dir: Optional[str] = None, model_name: str = "finetuned") -> DataManager:
    """Initialize the global data manager"""
    global data_manager
    if data_manager is None:
        data_manager = DataManager(data_dir, model_name)
    return data_manager
