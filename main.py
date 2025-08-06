import os
import json
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius
from sentence_transformers import SentenceTransformer, util
import numpy as np
from dotenv import load_dotenv

# --- 1. INITIALIZATION & CONFIGURATION ---
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
    
    # Configure Genius
    genius = lyricsgenius.Genius(os.getenv("GENIUS_ACCESS_TOKEN"), verbose=False, remove_section_headers=True)
    genius.verbose = True
    
    # Load Sentence Transformer model for embeddings
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    return spotify, genius, model


# --- 2. GENERATE SPOTIFY SEARCH QUERIES WITH GEMINI ---
def generate_spotify_queries(user_experience, gemini_model):
    """
    Uses the Gemini LLM to generate 5 Spotify playlist search queries based on the user's experience.
    """
    # This prompt is engineered to ask for a specific JSON output format.
    prompt = f"""
    <BEGIN INSTRUCTIONS>
    Based on the following life experience, generate a JSON object containing a single key "queries" which holds a list of 5 distinct and creative search queries for Spotify playlists. These queries should capture the core and nuanced emotions, themes, and moods of the text. These are fed into Spotify's search, so word queries to maximize result quality.Ideally, resulting playlists should contain songs with cathartic lyrics related to the user's experience in detail. Do not include anything else in your response except for the JSON.
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
        response = gemini_model.generate_content(prompt)
        # Clean up the response to ensure it's valid JSON
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        queries = json.loads(json_response).get("queries", [])
        print(f"✅ Generated Spotify queries: {queries}")
        return queries
    except Exception as e:
        print(f"❌ Error generating queries with Gemini: {e}")
        return []

# --- 3. FETCH SONGS FROM SPOTIFY ---
def get_songs_from_spotify(queries, sp_client, min_songs=5, max_playlist_songs=100, max_songs=30):
    """
    Searches Spotify for playlists matching the queries and extracts unique tracks, only from playlists with a song count within [min_songs, max_playlist_songs].
    """
    song_list = []
    song_ids = set() # Use a set to avoid duplicate songs

    for query in queries:
        try:
            # Search for playlists that match the query
            results = sp_client.search(q=query, type='playlist', limit=5)
            if not results['playlists']['items']:
                continue

            # Iterate through playlists to find one within the song count range
            playlist_found = False
            for playlist in results['playlists']['items']:
                playlist_id = playlist['id']
                playlist_details = sp_client.playlist(playlist_id, fields="tracks.total")
                num_tracks = playlist_details['tracks']['total']
                if min_songs <= num_tracks <= max_playlist_songs:
                    playlist_found = True
                    break
            if not playlist_found:
                continue
            # Get tracks from the first playlist found within the range
            playlist_tracks = sp_client.playlist_tracks(playlist_id)
            for item in playlist_tracks['items']:
                if len(song_list) >= max_songs:
                    return song_list
                track = item.get('track')
                if track and track['id'] not in song_ids:
                    song_ids.add(track['id'])
                    song_list.append(track)
        except Exception as e:
            print(f"⚠️ Could not fetch songs for query '{query}': {e}")
    
    print(f"✅ Fetched {len(song_list)} unique songs from Spotify.")
    # Limit the number of songs to process to keep runtime reasonable
    return song_list


# --- 4. GET LYRICS & CREATE EMBEDDINGS ---
def get_lyrics_and_embeddings(songs, genius_client, embedding_model):
    """
    Fetches lyrics for each song and creates a vector embedding.
    """
    lyrics_data = []
    for song in songs:
        try:
            # Search for the song lyrics on Genius
            genius_song = genius_client.search_song(song['name'], song['artists'][0]['name'])
            if genius_song and genius_song.lyrics:
                # Clean lyrics by removing the first line (title) and common tags
                lyrics = genius_song.lyrics.split("\n", 1)[-1]
                lyrics = lyrics.replace("EmbedShare URLCopyEmbedCopy", "").strip()
                print(lyrics)
                
                if lyrics: # Ensure lyrics are not empty after cleaning
                    embedding = embedding_model.encode(lyrics, convert_to_tensor=False)
                    lyrics_data.append({
                        'name': song['name'],
                        'artists': song['artists'],
                        'lyrics': lyrics,
                        'embedding': embedding
                    })
                    print(f"  - Got lyrics for '{song['name']}'")
        except Exception as e:
            print(f"⚠️ Could not find lyrics for '{song['name']}' by {song['artists'][0]['name']}: {e}")
            
    print(f"✅ Got lyrics and created embeddings for {len(lyrics_data)} songs.")
    return lyrics_data

# --- 5. RANK SONGS USING COSINE SIMILARITY ---
def rank_songs(user_experience, user_embedding, songs_with_lyrics, num_recommendations=7):
    """
    Ranks songs based on the cosine similarity between the user's experience and the song lyrics.
    """
    if not songs_with_lyrics:
        return []
        
    # Extract song embeddings into a matrix
    song_embeddings = np.array([song['embedding'] for song in songs_with_lyrics])
    
    # Calculate cosine similarity between the user's embedding and all song embeddings
    # The formula is: similarity = cos(θ) = (A · B) / (||A|| ||B||)
    similarities = util.pytorch_cos_sim(user_embedding, song_embeddings)[0]
    
    # Pair songs with their scores and sort them
    ranked_songs = sorted(zip(similarities, songs_with_lyrics), key=lambda x: x[0], reverse=True)
    
    # Return the top N recommendations
    return ranked_songs[:num_recommendations]

# --- MAIN EXECUTION ---
def main():
    """Main function to run the entire recommendation pipeline."""
    # Step 1: Initialize APIs and models
    spotify, genius, embedding_model = initialize_apis()
    
    # Get user input
    user_experience = input("Please describe your recent life experience in a few sentences:\n> ")
    
    # Step 2: Generate search queries
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    queries = generate_spotify_queries(user_experience, gemini_model)
    if not queries:
        print("Could not generate search queries. Exiting.")
        return

    # Step 3: Get a list of candidate songs from Spotify
    candidate_songs = get_songs_from_spotify(queries, spotify)
    if not candidate_songs:
        print("Could not find any songs on Spotify. Exiting.")
        return
        
    # Step 4: Get lyrics and create embeddings for the songs
    songs_with_lyrics = get_lyrics_and_embeddings(candidate_songs, genius, embedding_model)
    if not songs_with_lyrics:
        print("Could not retrieve lyrics for any songs. Exiting.")
        return

    # Step 5: Create embedding for the user's query and rank songs
    user_embedding = embedding_model.encode(user_experience, convert_to_tensor=False)
    recommendations = rank_songs(user_experience, user_embedding, songs_with_lyrics)

    # Final Output
    print("\n" + "="*50)
    print("✨ Here are your cathartic song recommendations: ✨")
    print("="*50)
    if recommendations:
        for i, (score, song) in enumerate(recommendations):
            print(f"{i+1}. '{song['name']}' by {song['artists'][0]['name']} (Similarity: {score:.2f})")
    else:
        print("Sorry, I couldn't find any suitable song recommendations for you.")
    print("="*50)

if __name__ == "__main__":
    main()

    # Test query: I just got cheated on by my girlfriend  