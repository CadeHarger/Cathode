import os
import sys
import json
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from typing import List, Tuple, Optional
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


async def score_debug_songs(user_experience: str, debug_found_songs: List[Tuple[str, str]], 
                           songs_in_dataset, vector_searcher, gemini_model) -> List[Tuple[str, str, float, int, float, float]]:
    """
    Score debug songs using both vector search and LLM reranking.
    
    Returns:
        List of (title, artist, vector_score, llm_score, combined_score, views)
    """
    if not debug_found_songs:
        return []
    
    print(f"\n🔍 Scoring {len(debug_found_songs)} debug songs...")
    
    # Create a DataFrame with just the debug songs
    debug_rows = []
    for title, artist in debug_found_songs:
        matches = songs_in_dataset[(songs_in_dataset['title'] == title) & (songs_in_dataset['artist'] == artist)]
        if not matches.empty:
            debug_rows.append(matches.iloc[0])
    
    if not debug_rows:
        return []
    
    import pandas as pd
    debug_df = pd.DataFrame(debug_rows)
    
    # Get vector scores for debug songs
    vector_results = vector_searcher.search(user_experience, top_k=len(debug_df), candidates=debug_df)
    
    # Get LLM scores using the same reranking function
    reranked_results = await rerank_with_llm(user_experience, vector_results, debug_df, gemini_model)
    
    # Format results
    scored_debug_songs = []
    for combined_score, title, artist, views, llm_score in reranked_results:
        # Find the original vector score
        vector_score = None
        for v_score, v_title, v_artist, v_views in vector_results:
            if v_title == title and v_artist == artist:
                vector_score = v_score
                break
        
        scored_debug_songs.append((title, artist, vector_score, llm_score, combined_score, views))
    
    return scored_debug_songs

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

def generate_spotify_queries(user_experience, genres, gemini_model, n_queries):
    """
    Uses the Gemini LLM to generate n Spotify playlist search queries based on the user's experience.
    """
    # This prompt is engineered to ask for a specific JSON output format.
    prompt = f"""
    <BEGIN INSTRUCTIONS>
    Based on the following life experience, generate a JSON object containing a single key "queries" which holds a list of {n_queries} distinct and creative search queries for Spotify playlists. 
    These queries should capture the core and nuanced emotions, themes, and moods of the text. These are fed into Spotify's search, so word queries to maximize result quality. 
    Do not include words like "songs about" in queries. Structure your queries to match how the titles of human-created playlists are formatted.
    Ideally, resulting playlists should contain songs with cathartic lyrics related to the user's experience in detail. Do not include anything else in your response except for the JSON.
    While queries should still try to capture the overall theme, queries should have different focusesin order to capture the details of the user's experience.
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
    {user_experience + '(' + ' '.join(genres) + ')'}
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


def run_hybrid_search(user_experience: str, genres: List[str], top_k: int = 7, n_queries: int = 5, n_playlists: int = 10, debug: bool = False, debug_songs: List[str] = None):
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
    queries = generate_spotify_queries(user_experience, genres, gemini_model, n_queries)
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

    # Debug mode: Check if specific songs are in the results and track found songs
    debug_found_songs = []
    if debug and debug_songs:
        print(f"\n🔍 Checking for {len(debug_songs)} debug songs in current results...")
        
        for debug_song in debug_songs:
            # Check if the song is in the current dataset results
            matches = songs_in_dataset[songs_in_dataset['title'].str.contains(debug_song, case=False, na=False)]
            if not matches.empty:
                print(f"✅ Found '{debug_song}':")
                for _, match in matches.iterrows():
                    print(f"   - {match['title']} by {match['artist']}")
                    debug_found_songs.append((match['title'], match['artist']))
            else:
                print(f"❌ '{debug_song}' not found in current results")
        print()

    # Apply genre filter if provided
    if genres != []:
        if 'tag' in songs_in_dataset.columns:
            # Convert genres list to lowercase for case-insensitive matching
            genres_lower = [genre.lower().strip() for genre in genres]
            songs_in_dataset = songs_in_dataset[songs_in_dataset['tag'].str.lower().isin(genres_lower)]
            if songs_in_dataset.empty:
                print(f"No songs found for the genres '{', '.join(genres)}'. Exiting.")
                return
            print(f"Filtered down to {len(songs_in_dataset)} songs for the genres '{', '.join(genres)}'.")
        else:
            print("Warning: 'tag' column not found in the dataset. Cannot apply genre filter.")

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
    
    # Debug mode: Score and log debug songs after final results
    if debug and debug_found_songs:
        debug_scores = asyncio.run(score_debug_songs(user_experience, debug_found_songs, songs_in_dataset, vector_searcher, gemini_model))
        
        if debug_scores:
            print("\n" + "="*50)
            print("🐛 DEBUG: Scores for requested songs")
            print("="*50)
            for title, artist, vector_score, llm_score, combined_score, views in debug_scores:
                print(f"'{title}' by {artist}")
                print(f"   Vector Score: {vector_score:.4f} | LLM Score: {llm_score}/100 | Combined Score: {combined_score:.4f} | Views: {views}")
                
                # Check if this song appeared in final recommendations
                in_final = any(title == rec_title and artist == rec_artist for _, rec_title, rec_artist, _, _ in final_recommendations)
                if in_final:
                    print(f"   ✅ This song appeared in your final recommendations")
                else:
                    print(f"   ❌ This song did not make it to your final recommendations")
                print()
    
    print("="*50)
    end_time = time.time()
    print(f"Total time taken: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    # Check for debug flag in command line arguments
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    
    if debug_mode:
        print("🐛 DEBUG MODE ENABLED")
    
    user_query = input("Please describe your recent life experience in a few sentences:\n> ").strip()
    
    # Optional: Ask for genre
    genre_input = input("Enter a genre to filter by separated by commas (ex: pop, rock, rap, country) or press Enter to skip:\n> ").strip()
    genre_input = genre_input.split(', ')
    if not genre_input:
        genre_input = [] # Unfiltered
    
    # Debug mode: Ask for songs to check upfront
    debug_songs_list = []
    if debug_mode:
        debug_songs = input("🐛 DEBUG: Enter song titles to check if they're in the results (separated by commas), or press Enter to skip:\n> ").strip()
        if debug_songs:
            debug_songs_list = [song.strip() for song in debug_songs.split(',')]

    if user_query:
        run_hybrid_search(user_query, genres=genre_input, debug=debug_mode, debug_songs=debug_songs_list)