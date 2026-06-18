import os
import numpy as np
import pandas as pd
from typing import Optional, List, Dict
import faiss
import logging
from google.cloud import aiplatform, bigquery, storage
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
import io


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages preloaded embeddings, metadata, and FAISS index for fast vector search.
    Loads all data into memory on initialization for optimal performance.
    """
    
    def __init__(self):
        self.embeddings = None
        self.faiss_index = None
        self.embedding_dim = None
        self.song_ids = None # Will store BigQuery song IDs
        
        # GCP Project and Endpoint details
        self.gcp_project = "819206197072"
        self.gcp_endpoint_id = "6143915944872771584"
        self.gcp_location = "us-central1"
        self.api_endpoint = "us-central1-aiplatform.googleapis.com"

        # GCS bucket for embeddings
        self.gcs_bucket_name = "my-lyrics-data"
        self.storage_client = storage.Client()

        # Initialize the Vertex AI client
        client_options = {"api_endpoint": self.api_endpoint}
        self.prediction_client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

        # Initialize everything else
        self._load_all_data()
        self._build_faiss_index()
        
        logger.info(f"✅ DataManager initialized with {self.faiss_index.ntotal} songs and FAISS index")
    
    def _load_embeddings_chunk(self, chunk_index: int) -> np.ndarray:
        """Load embeddings for a specific chunk from GCS"""
        bucket = self.storage_client.bucket(self.gcs_bucket_name)
        blob_name = f"embeddings_chunk_{chunk_index}.npy"
        blob = bucket.blob(blob_name)

        try:
            # Download the contents of the blob as a bytes object.
            logger.info(f"Downloading {blob_name} from GCS bucket {self.gcs_bucket_name}...")
            content = blob.download_as_bytes()
            # Use io.BytesIO to treat the bytes object as a file
            return np.load(io.BytesIO(content))
        except Exception as e:
            raise FileNotFoundError(f"Missing or unable to load embeddings for chunk {chunk_index} from GCS bucket '{self.gcs_bucket_name}': {e}")
    
    def _get_metadata_for_ids(self, ids: List[int]) -> pd.DataFrame:
        """Fetch song metadata for a list of specific song IDs from BigQuery."""
        if not ids:
            return pd.DataFrame()

        logger.info(f"Fetching metadata for {len(ids)} song IDs from BigQuery...")
        try:
            client = bigquery.Client()
            # Use a query parameter to safely pass the list of IDs
            query = """
                SELECT *
                FROM `lyric_data.other_columns_merged`
                WHERE id IN UNNEST(@ids)
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("ids", "INT64", ids),
                ]
            )
            query_job = client.query(query, job_config=job_config)
            df = query_job.to_dataframe()

            # Set the 'id' column as the index for quick lookups
            df.set_index('id', inplace=True)
            return df

        except Exception as e:
            logger.error(f"Failed to fetch metadata from BigQuery for IDs: {e}")
            raise RuntimeError("Could not load metadata from BigQuery.") from e

    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit vectors"""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms

    def _load_all_data(self):
        """
        Load embeddings into memory and get song IDs from BigQuery.
        Metadata is not loaded into memory.
        """
        logger.info("Loading embeddings into memory and fetching song IDs from BigQuery...")
        
        # 1. Fetch only the song IDs from BigQuery, in the correct order
        try:
            client = bigquery.Client()
            query = "SELECT id FROM `lyric_data.other_columns_merged` ORDER BY id ASC"
            self.song_ids = client.query(query).to_dataframe()['id'].values.astype(np.int64)
            logger.info(f"Fetched {len(self.song_ids)} song IDs from BigQuery.")
        except Exception as e:
            logger.error(f"Failed to fetch song IDs from BigQuery: {e}")
            raise RuntimeError("Could not load song IDs from BigQuery.") from e

        # 2. Load all embedding chunks from GCS
        all_embeddings = []
        for chunk_idx in range(1, 5):  # Assuming chunks 1-4
            try:
                embeddings_chunk = self._load_embeddings_chunk(chunk_idx)
                all_embeddings.append(embeddings_chunk)
                logger.info(f"Loaded embeddings chunk {chunk_idx}")
            except FileNotFoundError:
                logger.warning(f"Embeddings chunk {chunk_idx} not found, stopping.")
                break
        
        if not all_embeddings:
            raise RuntimeError("No embedding chunks found!")
        
        # Concatenate all embedding chunks
        self.embeddings = np.vstack(all_embeddings).astype(np.float32)
        
        # 3. Ensure song IDs and embeddings align
        min_len = min(len(self.song_ids), len(self.embeddings))
        self.song_ids = self.song_ids[:min_len]
        self.embeddings = self.embeddings[:min_len]
        
        # 4. Normalize embeddings
        self.embeddings = self._normalize_embeddings(self.embeddings)
        self.embedding_dim = self.embeddings.shape[1]
        
        logger.info(f"Loaded {len(self.embeddings)} embeddings with {self.embedding_dim}D")

    def _build_faiss_index(self):
        """Build FAISS index mapping to actual BigQuery song IDs."""
        logger.info("Building FAISS index with ID mapping...")
        
        # Use IndexFlatIP for inner product (cosine similarity with normalized vectors)
        index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Create a map from the index's sequential IDs to our BigQuery song IDs
        self.faiss_index = faiss.IndexIDMap(index)
        
        # Add all embeddings to the index with their corresponding song IDs
        self.faiss_index.add_with_ids(self.embeddings, self.song_ids)
        
        logger.info(f"✅ FAISS index built with {self.faiss_index.ntotal} vectors")
    
    def get_views_multiplier(self, views: np.ndarray) -> np.ndarray:
        """Calculate views-based score multiplier"""
        return 1.0 + ((np.log10(np.maximum(views, 1.0)) - 3.0) * 0.1)
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding from the Vertex AI endpoint."""
        try:
            instances = [{"text": text}]
            # The format of each instance should conform to the deployed model's prediction input schema.
            instances = [
                json_format.ParseDict(instance_dict, Value()) for instance_dict in instances
            ]
            parameters_dict = {}
            parameters = json_format.ParseDict(parameters_dict, Value())
            endpoint = self.prediction_client.endpoint_path(
                project=self.gcp_project, location=self.gcp_location, endpoint=self.gcp_endpoint_id
            )
            response = self.prediction_client.predict(
                endpoint=endpoint, instances=instances, parameters=parameters
            )
            
            # The predictions are a google.protobuf.Value representation of the model's predictions.
            prediction = response.predictions[0]
            return np.array(prediction, dtype=np.float32)

        except Exception as e:
            logger.error(f"Error getting embedding for '{text}': {e}")
            raise RuntimeError("Failed to connect to the embedding service.") from e

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
        query_embedding = self._get_embedding(user_query)
        
        if candidates is not None and not candidates.empty:
            return self._search_within_candidates(query_embedding, top_k, candidates)
        else:
            return self._search_all(query_embedding, top_k)
    
    def _search_all(self, query_embedding: np.ndarray, top_k: int) -> List[Dict]:
        """Search across all songs using FAISS"""
        # Search with FAISS (returns more than top_k for reranking)
        search_k = min(top_k * 3, self.faiss_index.ntotal)
        scores, ids = self.faiss_index.search(query_embedding.reshape(1, -1), search_k)
        
        # Flatten results
        scores = scores[0]
        ids = ids[0]
        
        # Apply views-based reranking
        return self._rerank_with_views(scores, ids, top_k)
    
    def _search_within_candidates(self, query_embedding: np.ndarray, top_k: int, candidates: pd.DataFrame) -> List[Dict]:
        """Search within specific candidate songs"""
        # Get BigQuery IDs of candidate songs
        candidate_ids = candidates['id'].values
        
        # We need to map these IDs to their positions in the self.embeddings array
        # This requires a lookup. Let's create a map from ID to index.
        id_to_idx_map = {id_val: i for i, id_val in enumerate(self.song_ids)}
        candidate_indices = [id_to_idx_map[id_val] for id_val in candidate_ids if id_val in id_to_idx_map]
        
        if not candidate_indices:
            return []
            
        # Get embeddings for candidates
        candidate_embeddings = self.embeddings[candidate_indices]
        
        # Compute similarities
        similarities = np.dot(candidate_embeddings, query_embedding)
        
        # Get top candidates
        top_local_indices = np.argsort(-similarities)[:top_k * 2]  # Get more for reranking
        
        # Map back to BigQuery song IDs
        top_song_ids = np.array(candidate_ids)[top_local_indices]
        scores = similarities[top_local_indices]
        
        return self._rerank_with_views(scores, top_song_ids, top_k)
    
    def _rerank_with_views(self, scores: np.ndarray, ids: np.ndarray, top_k: int) -> List[Dict]:
        """Apply views-based reranking to search results"""
        # Filter out invalid IDs (-1 is used by FAISS for no result)
        valid_ids = [int(id_val) for id_val in ids if id_val != -1]
        if not valid_ids:
            return []
        
        # Fetch metadata for the top candidates from BigQuery
        metadata_df = self._get_metadata_for_ids(valid_ids)
        
        if metadata_df.empty:
            return []

        results = []
        for score, id_val in zip(scores, valid_ids):
            if id_val not in metadata_df.index:
                continue
                
            row = metadata_df.loc[id_val]
            
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
                'views_multiplier': float(views_multiplier),
                'id': int(id_val) # Include the song ID
            })
        
        # Sort by final score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def find_songs_in_dataset(self, spotify_songs: List[dict]) -> pd.DataFrame:
        """Find Spotify songs in the dataset by querying BigQuery directly."""
        if not spotify_songs:
            return pd.DataFrame()
        
        # Extract normalized titles and artists from Spotify songs
        conditions = []
        params = []
        for s in spotify_songs:
            title = (s.get('name') or "").lower().strip()
            artist = ""
            if s.get('artists') and s['artists'] and s['artists'][0] and s['artists'][0].get('name'):
                artist = s['artists'][0]['name'].lower().strip()
            
            if title and artist:
                conditions.append("(LOWER(TRIM(title)) = ? AND LOWER(TRIM(artist)) = ?)")
                params.extend([title, artist])

        if not conditions:
            return pd.DataFrame()
        
        try:
            client = bigquery.Client()
            query = f"""
                SELECT id, title, artist 
                FROM `lyric_data.other_columns_merged`
                WHERE {' OR '.join(conditions)}
            """
            # Define query parameters to prevent SQL injection
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(None, "STRING", p) for p in params
                ]
            )
            
            query_job = client.query(query, job_config=job_config)
            found_df = query_job.to_dataframe()
            return found_df

        except Exception as e:
            logger.error(f"Failed to find songs in BigQuery: {e}")
            return pd.DataFrame() # Return empty on error
    
    def get_total_songs(self) -> int:
        """Get total number of songs from the FAISS index"""
        return self.faiss_index.ntotal if self.faiss_index else 0

# Global instance (will be initialized on server startup)
data_manager: Optional[DataManager] = None

def get_data_manager() -> DataManager:
    """Get the global data manager instance"""
    global data_manager
    if data_manager is None:
        raise RuntimeError("DataManager not initialized. Call initialize_data_manager() first.")
    return data_manager

def initialize_data_manager() -> DataManager:
    """Initialize the global data manager"""
    global data_manager
    if data_manager is None:
        data_manager = DataManager()
    return data_manager
