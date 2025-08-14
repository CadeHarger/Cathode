import os
import json
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from typing import List, Tuple
import time
import asyncio

# HYPERPARAMETERS
LLM_RERANK_COUNT = 100  # Number of top vector search results to re-rank with LLM
LLM_WEIGHT = 0.3        # Weight for LLM score in final ranking (0.0 to 1.0)
VECTOR_WEIGHT = 0.7     # Weight for vector similarity score in final ranking (0.0 to 1.0)

# 1. Generate 5 Spotify playlist search queries based on the user's experience.
# 2. Get a list of candidate songs from Spotify playlists from the search queries.
# 3. Filter to keep only the candidate songs that are in our local dataset.
# 4. Perform vector search to get top candidates.
# 5. Use LLM (Gemini) to re-rank the top candidates based on lyrical relevance.
# 6. Return the final top 7 songs. 

from vector_search import VectorSearcher
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

async def rerank_with_llm(user_experience: str, vector_results: List[Tuple[float, str, str, float]], 
                   songs_in_dataset, gemini_model) -> List[Tuple[float, str, str, float, int]]:
    """
    Re-rank vector search results using LLM scores.
    
    Args:
        user_experience: Original user query
        vector_results: List of (score, title, artist, views) from vector search
        songs_in_dataset: DataFrame with song metadata for lyrics lookup
        gemini_model: Initialized Gemini model
        
    Returns:
        Re-ranked list of (combined_score, title, artist, views, llm_score)
    """
    if not vector_results:
        return []
    
    print(f"Re-ranking top {len(vector_results)} results with LLM...")
    
    # Create a lookup for song metadata
    song_lookup = {}
    for _, row in songs_in_dataset.iterrows():
        key = (row['title'], row['artist'])
        song_lookup[key] = row
    
    # Get lyrics for the songs we need to re-rank
    candidate_songs = []
    for _, title, artist, _ in vector_results:
        key = (title, artist)
        if key in song_lookup:
            candidate_songs.append(song_lookup[key])
    
    if not candidate_songs:
        print("⚠️ No songs found for LLM re-ranking")
        return vector_results
    
    # Convert to DataFrame for lyrics retrieval
    import pandas as pd
    candidates_df = pd.DataFrame(candidate_songs)
    lyrics_map = get_lyrics_for_candidates(candidates_df)
    
    tasks = []
    for vector_score, title, artist, views in vector_results:
        song_key = (title, artist)
        if song_key in lyrics_map:
            lyrics = lyrics_map[song_key]
            tasks.append(
                rate_song_with_gemini(user_experience, title, artist, lyrics, gemini_model)
            )

    llm_scores = await asyncio.gather(*tasks)
    
    reranked_results = []
    score_index = 0
    for vector_score, title, artist, views in vector_results:
        song_key = (title, artist)
        
        if song_key in lyrics_map:
            llm_score = llm_scores[score_index]
            score_index += 1
            combined_score = combine_scores(vector_score, llm_score)
            
            print(f"  '{title}' by {artist}: Vector={vector_score:.4f}, LLM={llm_score}, Combined={combined_score:.4f}")
            reranked_results.append((combined_score, title, artist, views, llm_score))
        else:
            # Keep original score if no lyrics found, set LLM score to 0
            reranked_results.append((vector_score, title, artist, views, 0))
    
    # Sort by combined score
    reranked_results.sort(key=lambda x: x[0], reverse=True)
    return reranked_results

def initialize_apis():
    """Load environment variables and configure API clients."""
    load_dotenv()
    
    # Configure Gemini
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Configure Spotify
    spotify_client_id = os.getenv("SPOTIPY_CLIENT_ID")
    spotify_client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    spotify_auth_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
    spotify = spotipy.Spotify(auth_manager=spotify_auth_manager)
    
    return spotify

def generate_spotify_queries(user_experience, gemini_model, n_queries):
    """
    Uses the Gemini LLM to generate n Spotify playlist search queries based on the user's experience.
    """
    # This prompt is engineered to ask for a specific JSON output format.
    prompt = f"""
    <BEGIN INSTRUCTIONS>
    Based on the following life experience, generate a JSON object containing a single key "queries" which holds a list of {n_queries} distinct and creative search queries for Spotify playlists. These queries should capture the core and nuanced emotions, themes, and moods of the text. These are fed into Spotify's search, so word queries to maximize result quality.Ideally, resulting playlists should contain songs with cathartic lyrics related to the user's experience in detail. Do not include anything else in your response except for the JSON.
    Example: User experience: "I'm feeling sad and lonely because my dog passed away"
    JSON Response:
    {{
        "queries": [
            "sad and lonely",
            "grieving dog loss",
            "pet died remembrance",  
            "sorrow and healing",
            "dog death comfort"
        ]
    }}
    <END INSTRUCTIONS>
    <BEGIN USER EXPERIENCE>
    {user_experience}
    <END USER EXPERIENCE>
    <BEGIN JSON RESPONSE>
    JSON Response:
    """
    
    try:
        response = gemini_model.generate_content(
            prompt, 
            generation_config=genai.types.GenerationConfig(temperature=0.0),
            safety_settings=GEMINI_SAFETY_SETTINGS
        )
        
        # Check if the response is valid before accessing .text
        if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
            print("❌ Query generation blocked by safety filters.")
            # Log details if available
            if response.prompt_feedback:
                print(f"   Prompt Feedback: {response.prompt_feedback}")
            if response.candidates:
                 print(f"   Finish Reason: {response.candidates[0].finish_reason}")
                 print(f"   Safety Ratings: {response.candidates[0].safety_ratings}")
            return []
            
        # Clean up the response to ensure it's valid JSON
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        queries = json.loads(json_response).get("queries", [])
        print(f"✅ Generated Spotify queries: {queries}")
        return queries
    except Exception as e:
        print(f"❌ Error generating queries with Gemini: {e}")
        return []

def get_songs_from_spotify(queries: List[str], sp_client: spotipy.Spotify, n_playlists: int) -> List[dict]:
    """
    Searches Spotify for playlists matching the queries and extracts all unique tracks.
    """
    song_list = []
    song_ids = set()  # Use a set to avoid duplicate songs

    for query in queries:
        try:
            results = sp_client.search(q=query, type='playlist', limit=n_playlists) # Search for more playlists
            if not results['playlists']['items']:
                continue

            print(f"Found {len(results['playlists']['items'])} playlists for query '{query}'")
            for playlist in results['playlists']['items']:
                if playlist is None:
                    continue
                
                playlist_id = playlist['id']
                
                offset = 0
                while True:
                    playlist_tracks = sp_client.playlist_tracks(playlist_id, offset=offset)
                    if not playlist_tracks['items']:
                        break
                    
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
    
    print(f"✅ Fetched {len(song_list)} unique songs from Spotify.")
    return song_list


def run_hybrid_search(user_experience: str, top_k: int = 7, n_queries: int = 5, n_playlists: int = 10):
    """
    Main function to run the entire recommendation pipeline.
    """
    start_time = time.time()

    # Step 1: Initialize APIs and models
    spotify = initialize_apis()
    print("🔍 Initializing vector search with finetuned model...")
    vector_searcher = VectorSearcher()

    # Step 2: Generate search queries
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    queries = generate_spotify_queries(user_experience, gemini_model, n_queries)
    if not queries:
        print("Could not generate search queries. Exiting.")
        return

    # Step 3: Get a list of candidate songs from Spotify
    candidate_songs = get_songs_from_spotify(queries, spotify, n_playlists)
    if not candidate_songs:
        print("Could not find any songs on Spotify. Exiting.")
        return
    
    print(f"Found {len(candidate_songs)} candidate songs from Spotify.")

    # Step 4: Find which of the candidate songs are in our local dataset
    songs_in_dataset = vector_searcher.find_songs_in_dataset(candidate_songs)
    if songs_in_dataset.empty:
        print("None of the candidate songs were found in the local dataset. Exiting.")
        return
    
    print(f"Found {len(songs_in_dataset)} songs in the local dataset.")

    # Step 5: Perform vector search to get top candidates for LLM re-ranking
    print(f"🔍 Getting top {LLM_RERANK_COUNT} candidates from vector search...")
    vector_results = vector_searcher.search(user_experience, top_k=LLM_RERANK_COUNT, candidates=songs_in_dataset)
    
    if not vector_results:
        print("No results from vector search. Exiting.")
        return
    
    print(f"✅ Vector search returned {len(vector_results)} candidates")
    
    # Step 6: Re-rank top candidates with LLM
    final_recommendations = asyncio.run(rerank_with_llm(user_experience, vector_results, songs_in_dataset, gemini_model))
    
    # Take only the top_k results for final output
    final_recommendations = final_recommendations[:top_k]

    # Final Output
    print('\n\n')
    print("Prompt: ", user_experience)
    print("\n" + "="*50)
    print("✨ Here are your cathartic song recommendations: ✨")
    print("="*50)
    if final_recommendations:
        for i, (score, title, artist, views, llm_score) in enumerate(final_recommendations, 1):
            print(f"{i}. '{title}' by {artist}")
            print(f"   Combined Score: {score:.4f} | LLM Score: {llm_score}/100 | Views: {views}")
    else:
        print("Sorry, I couldn't find any suitable song recommendations for you.")
    print("="*50)
    end_time = time.time()
    print(f"Total time taken: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    user_query = input("Please describe your recent life experience in a few sentences:\n> ").strip()
    if user_query:
        run_hybrid_search(user_query)