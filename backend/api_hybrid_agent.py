"""
Modified version of hybrid_agent.py that returns structured data for API use
and accepts a progress callback function for real-time updates.
"""
import os
import sys
import json
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from typing import List, Tuple, Optional, Callable, Dict, Any
import pandas as pd
import time
import asyncio

# HYPERPARAMETERS
LLM_RERANK_COUNT = 100  # Number of top vector search results to re-rank with LLM
LLM_WEIGHT = 0.3        # Weight for LLM score in final ranking (0.0 to 1.0)
VECTOR_WEIGHT = 0.7     # Weight for vector similarity score in final ranking (0.0 to 1.0)

from vector_search import VectorSearcher
from data_manager import get_data_manager
from llm_filter import rate_song_with_gemini, get_lyrics_for_candidates

# Safety settings to avoid Gemini API blocking
GEMINI_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def combine_scores(vector_score: float, llm_score: int) -> float:
    # Normalize LLM score to 0-1 range
    normalized_llm_score = llm_score / 100.0
    
    # Weighted combination
    combined = (VECTOR_WEIGHT * vector_score) + (LLM_WEIGHT * normalized_llm_score)
    return combined

def initialize_apis():
    """Initialize Spotify API client and Google AI"""
    load_dotenv()
    
    # Configure Google AI
    google_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        raise ValueError("Missing GEMINI_API_KEY or GOOGLE_API_KEY in environment variables")
    genai.configure(api_key=google_api_key)
    
    # Configure Spotify
    spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
    spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not spotify_client_id or not spotify_client_secret:
        raise ValueError("Missing Spotify API credentials in environment variables")
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=spotify_client_id,
        client_secret=spotify_client_secret
    )
    
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def generate_spotify_queries(user_experience: str, genres: List[str], gemini_model, n_queries: int = 5) -> List[str]:
    """Generate Spotify search queries based on user experience"""
    genre_context = f" Focus on {', '.join(genres)} music." if genres else ""
    
    prompt = f"""
    Based on this user's life experience, generate {n_queries} specific Spotify playlist search queries that would find music matching their emotional state and situation.
    
    User experience: "{user_experience}"
    {genre_context}
    
    Return only the search queries, one per line, without quotes or numbering.
    Make them specific enough to find relevant playlists but broad enough to get good results.
    
    Examples of good queries:
    - rainy day chill vibes
    - heartbreak acoustic songs
    - workout motivation hip hop
    - late night driving music
    """
    
    try:
        response = gemini_model.generate_content(
            prompt,
            safety_settings=GEMINI_SAFETY_SETTINGS
        )
        
        queries = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
        return queries[:n_queries]
    
    except Exception as e:
        print(f"Error generating queries: {e}")
        # Fallback queries
        return ["chill vibes", "emotional songs", "mood music", "life experiences", "feelings playlist"]

def get_songs_from_spotify(queries: List[str], sp_client: spotipy.Spotify, n_playlists: int = 10) -> List[dict]:
    """Get songs from Spotify playlists based on search queries"""
    song_list = []
    song_ids = set()
    
    for query in queries:
        try:
            playlists = sp_client.search(q=query, type='playlist', limit=n_playlists)
            
            for playlist in playlists['playlists']['items']:
                if playlist is None:
                    continue
                
                playlist_id = playlist['id']
                
                offset = 0
                printed_for_playlist = False
                while True:
                    playlist_tracks = sp_client.playlist_tracks(playlist_id, offset=offset)
                    if not playlist_tracks['items']:
                        break
                    
                    if not printed_for_playlist:
                        print(f"\n--- Songs from playlist: {playlist.get('name')} ---")
                        for i, item in enumerate(playlist_tracks['items'][:10]):
                            print(json.dumps(item.get('track'), indent=2))
                        printed_for_playlist = True
                        
                    for item in playlist_tracks['items']:
                        track = item.get('track')
                        if track and track['id'] not in song_ids:
                            song_ids.add(track['id'])
                            song_list.append(track)
                    
                    offset += len(playlist_tracks['items'])
                    if not playlist_tracks['next']:
                        break

        except Exception as e:
            print(f"⚠️ Could not fetch songs for query '{query}': {e}")
    
    return song_list

async def rerank_with_llm(user_experience: str, vector_results: List[Tuple[float, str, str, float]], 
                         songs_in_dataset, gemini_model, progress_callback: Optional[Callable] = None):
    """Re-rank vector search results using LLM"""
    
    if progress_callback:
        await progress_callback(85, "Getting lyrics for top candidates...")
    
    # Get lyrics for the candidates
    candidates_df = songs_in_dataset[
        songs_in_dataset.apply(
            lambda row: any((row['title'], row['artist']) == (title, artist) 
                          for _, title, artist, _ in vector_results), axis=1
        )
    ].copy()
    
    lyrics_dict = get_lyrics_for_candidates(candidates_df)
    
    if progress_callback:
        await progress_callback(90, "Re-ranking with AI analysis...")
    
    # Rate each song with LLM
    reranked_results = []
    for vector_score, title, artist, views in vector_results:
        lyrics = lyrics_dict.get((title, artist), "")
        
        if lyrics:
            try:
                llm_score = await rate_song_with_gemini(user_experience, title, artist, lyrics, gemini_model)
                combined_score = combine_scores(vector_score, llm_score)
                reranked_results.append((combined_score, title, artist, views, llm_score))
            except Exception as e:
                print(f"Error rating song '{title}' by {artist}: {e}")
                # Fallback to vector score only
                reranked_results.append((vector_score, title, artist, views, 50))
        else:
            # No lyrics available, use vector score with neutral LLM score
            combined_score = combine_scores(vector_score, 50)
            reranked_results.append((combined_score, title, artist, views, 50))
    
    # Sort by combined score (descending)
    reranked_results.sort(key=lambda x: x[0], reverse=True)
    
    return reranked_results

def create_vector_searcher():
    """Wrapper function to instantiate VectorSearcher for threading."""
    return VectorSearcher()

async def run_hybrid_search_api(user_experience: str, genres: List[str], progress_callback: Optional[Callable] = None, top_k: int = 50) -> Dict[str, Any]:
    """
    API version of run_hybrid_search that returns structured data and accepts progress callback
    """
    start_time = time.time()
    
    try:
        if progress_callback:
            await progress_callback(5, "Initializing APIs and models...")
        
        # Step 1: Initialize APIs and models
        spotify = initialize_apis()
        # Use preloaded DataManager instead of creating new VectorSearcher
        data_manager = get_data_manager()
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Get total dataset size for statistics
        total_dataset_size = data_manager.get_total_songs()
        
        if progress_callback:
            await progress_callback(10, f"Dataset loaded with {total_dataset_size:,} total songs")
        
        # Step 2: Generate search queries
        queries = await asyncio.to_thread(generate_spotify_queries, user_experience, genres, gemini_model, n_queries=5)
        if not queries:
            raise Exception("Could not generate search queries")
        
        if progress_callback:
            await progress_callback(20, "Fetching candidate songs from Spotify...")
        
        # Step 3: Get candidate songs from Spotify
        candidate_songs = await asyncio.to_thread(get_songs_from_spotify, queries, spotify, n_playlists=10)
        if not candidate_songs:
            raise Exception("Could not find any songs on Spotify")
        
        if progress_callback:
            await progress_callback(30, f"Found {len(candidate_songs):,} candidate songs from Spotify")
        
        if progress_callback:
            await progress_callback(35, "Finding songs in local dataset...")
        
        # Prepare Spotify tracks dataframe with normalized keys and URLs for merging
        def _normalize(value: Optional[str]) -> str:
            return (value or "").lower().strip()
        
        spotify_rows = []
        for tr in candidate_songs:
            if not tr:
                continue
            norm_title = _normalize(tr.get('name'))
            artist_name = ""
            try:
                if tr.get('artists') and len(tr['artists']) > 0:
                    first_artist = tr['artists'][0] or {}
                    artist_name = _normalize(first_artist.get('name'))
            except Exception:
                artist_name = ""
            spotify_rows.append({
                'norm_title': norm_title,
                'norm_artist': artist_name,
                'spotify_url': (tr.get('external_urls') or {}).get('spotify'),
                'spotify_track': tr,
            })
        spotify_tracks_df = pd.DataFrame(spotify_rows)
        if not spotify_tracks_df.empty:
            spotify_tracks_df.drop_duplicates(subset=['norm_title', 'norm_artist'], keep='first', inplace=True)
        
        # Step 4: Find which songs are in our local dataset
        songs_in_dataset = await asyncio.to_thread(data_manager.find_songs_in_dataset, candidate_songs)
        if songs_in_dataset.empty:
            raise Exception("None of the candidate songs were found in the local dataset")
        
        # Merge spotify URL and full track object onto dataset matches for easy lookup later
        if not spotify_tracks_df.empty:
            songs_in_dataset = songs_in_dataset.merge(
                spotify_tracks_df[['norm_title', 'norm_artist', 'spotify_url', 'spotify_track']],
                on=['norm_title', 'norm_artist'],
                how='left'
            )
        
        if progress_callback:
            await progress_callback(40, f"Found {len(songs_in_dataset):,} songs in local dataset")
        
        # Apply genre filter if provided
        if genres:
            if 'tag' in songs_in_dataset.columns:
                genres_lower = [genre.lower().strip() for genre in genres]
                songs_in_dataset = songs_in_dataset[songs_in_dataset['tag'].str.lower().isin(genres_lower)]
                if songs_in_dataset.empty:
                    raise Exception(f"No songs found for the genres '{', '.join(genres)}'")
                if progress_callback:
                    await progress_callback(45, f"Filtered to {len(songs_in_dataset):,} songs for selected genres")
        
        if progress_callback:
            await progress_callback(50, "Performing vector search...")
        
        # Step 5: Perform vector search using DataManager
        vector_results_raw = await asyncio.to_thread(data_manager.search, user_experience, top_k=LLM_RERANK_COUNT, candidates=songs_in_dataset)
        # Convert DataManager results to the expected format: (score, title, artist, views)
        vector_results = [(r['score'], r['title'], r['artist'], r['views']) for r in vector_results_raw]
        if not vector_results:
            raise Exception("No results from vector search")
        
        if progress_callback:
            await progress_callback(60, f"Vector search returned {len(vector_results):,} candidates")
        
        if progress_callback:
            await progress_callback(70, f"Reranking {len(vector_results)} songs with AI analysis...")
        
        # Step 6: Re-rank with LLM
        final_recommendations = await rerank_with_llm(user_experience, vector_results, songs_in_dataset, gemini_model, progress_callback)
        
        # Take only the top_k results
        final_recommendations = final_recommendations[:top_k]
        
        if progress_callback:
            await progress_callback(95, "Formatting results...")
        
        # Format results for API response
        songs = []
        for i, (combined_score, title, artist, views, llm_score) in enumerate(final_recommendations):
            # Find the song in the dataset to get additional metadata
            song_row = songs_in_dataset[
                (songs_in_dataset['title'] == title) & 
                (songs_in_dataset['artist'] == artist)
            ].iloc[0] if not songs_in_dataset[
                (songs_in_dataset['title'] == title) & 
                (songs_in_dataset['artist'] == artist)
            ].empty else None
            
            spotify_url = song_row.get('spotify_url', None) if song_row is not None else None
            
            # Safely extract album image URL from merged Spotify track object
            image_url = None
            if song_row is not None:
                spotify_track_obj = song_row.get('spotify_track', None)
                if isinstance(spotify_track_obj, dict):
                    album_obj = spotify_track_obj.get('album') or {}
                    images_list = album_obj.get('images') or []
                    if isinstance(images_list, list) and len(images_list) > 0 and isinstance(images_list[0], dict):
                        image_url = images_list[0].get('url')
            
            song_data = {
                "id": f"song_{i}_{hash(f'{title}_{artist}') % 10000}",
                "title": title,
                "artist": artist,
                "album": song_row.get('album', 'Unknown Album') if song_row is not None else 'Unknown Album',
                "genre": song_row.get('tag', 'Unknown Genre') if song_row is not None else 'Unknown Genre',
                "duration_ms": int(song_row.get('duration_ms', 180000)) if song_row is not None else 180000,
                "score": float(combined_score),
                "streams": int(views) if views else 0,
                "llm_score": int(llm_score),
                "url": spotify_url or "None",
                "image_url": image_url,
                "vector_score": float([vs for vs, t, a, _ in vector_results if t == title and a == artist][0]) if any(t == title and a == artist for _, t, a, _ in vector_results) else 0.0
            }
            songs.append(song_data)
        
        if progress_callback:
            await progress_callback(100, "Playlist created successfully!")
        
        end_time = time.time()
        
        return {
            "success": True,
            "songs": songs,
            "metadata": {
                "user_experience": user_experience,
                "genres": genres,
                "total_candidates": len(candidate_songs),
                "dataset_matches": len(songs_in_dataset),
                "processing_time": round(end_time - start_time, 2),
                "queries_used": queries
            }
        }
        
    except Exception as e:
        if progress_callback:
            await progress_callback(0, f"Error: {str(e)}")
        
        return {
            "success": False,
            "error": str(e),
            "songs": []
        }
