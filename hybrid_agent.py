import os
import json
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from typing import List
import time

# 1. Generate 5 Spotify playlist search queries based on the user's experience.
# 2. Get a list of candidate songs from Spotify playlists from the search queries.
# 3. Filter to keep only the candidate songs that are in our local dataset.
# 4. Perform vector search on the filtered songs.
# 5. Return the top 7 songs. 

from vectorSearch import VectorSearcher

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
        response = gemini_model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.0))
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

    # Step 5: Perform vector search on the filtered songs
    recommendations = vector_searcher.search(user_experience, top_k=top_k, candidates=songs_in_dataset)

    # Final Output
    print('\n\n')
    print("Prompt: ", user_experience)
    print("\n" + "="*50)
    print("✨ Here are your cathartic song recommendations: ✨")
    print("="*50)
    if recommendations:
        for i, (score, title, artist, views) in enumerate(recommendations, 1):
            print(f"{i}. '{title}' by {artist} \t(Score: {score:.4f}, Views: {views})")
    else:
        print("Sorry, I couldn't find any suitable song recommendations for you.")
    print("="*50)
    end_time = time.time()
    print(f"Total time taken: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    user_query = input("Please describe your recent life experience in a few sentences:\n> ").strip()
    if user_query:
        run_hybrid_search(user_query)