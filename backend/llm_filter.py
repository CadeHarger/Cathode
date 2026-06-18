import os
import json
import asyncio
import pandas as pd
import google.generativeai as genai
from typing import List, Tuple, Dict
from dotenv import load_dotenv

from config import GEMINI_MODEL
from paths import get_data_dir

def _load_lyrics_chunk(data_dir: str, chunk_index: int) -> pd.DataFrame:
    """Load lyrics from a specific chunk."""
    csv_path = os.path.join(data_dir, f"song_lyrics_chunk_{chunk_index}.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing lyrics chunk {chunk_index}: {csv_path}")
    return pd.read_csv(csv_path)

def get_lyrics_for_candidates(candidates_df: pd.DataFrame) -> Dict[Tuple[str, str], str]:
    """
    Retrieve lyrics for candidate songs from the dataset chunks.
    
    Args:
        candidates_df: DataFrame with candidate songs containing 'chunk_index', 'original_index', 'title', 'artist'
        
    Returns:
        Dictionary mapping (title, artist) tuples to lyrics strings
    """
    if candidates_df.empty:
        return {}
    
    data_dir = get_data_dir()
    lyrics_map = {}
    
    # Group candidates by chunk to minimize file I/O
    candidates_by_chunk = candidates_df.groupby('chunk_index')
    
    for chunk_index, chunk_candidates in candidates_by_chunk:
        try:
            # Load the full lyrics chunk
            lyrics_chunk = _load_lyrics_chunk(data_dir, chunk_index)
            
            # Get lyrics for each candidate in this chunk
            for _, candidate in chunk_candidates.iterrows():
                original_index = candidate['original_index']
                title = candidate['title']
                artist = candidate['artist']
                
                # Get lyrics from the chunk using original_index
                if original_index < len(lyrics_chunk):
                    lyrics = lyrics_chunk.iloc[original_index]['lyrics']
                    if pd.notna(lyrics) and lyrics.strip():
                        lyrics_map[(title, artist)] = str(lyrics).strip()
                        
        except Exception as e:
            print(f"⚠️ Error loading lyrics for chunk {chunk_index}: {e}")
            continue
    
    return lyrics_map

async def rate_song_with_gemini(user_query: str, song_title: str, artist: str, lyrics: str, gemini_model) -> int:
    """
    Use Gemini Flash 2.5 Lite to rate how well song lyrics match the user query.
    
    Args:
        user_query: The original user experience/query
        song_title: Title of the song
        artist: Artist name
        lyrics: Song lyrics
        gemini_model: Initialized Gemini model
        
    Returns:
        Integer score from 0-100 inclusive
    """
    # Truncate lyrics if too long to avoid token limits
    max_lyrics_length = 5000
    if len(lyrics) > max_lyrics_length:
        lyrics = lyrics[:max_lyrics_length] + "..."
    
    prompt = f"""
    <BEGIN INSTRUCTIONS>
    You are a music recommendation expert. Rate how well the following song lyrics match the user's emotional experience and needs and their ability to provide catharsis on a scale from 0 to 100 (inclusive).

    Consider:
    - Emotional resonance with the user's experience
    - Potential for catharsis or emotional connection
    - Thematic relevance to their situation
    - Lyrical depth and relatability

    Respond ONLY with a JSON object containing a single key "score" with an integer value from 0-100. Do not include any other text or explanation.

    Example response format:
    {{"score": 85}}
    <END INSTRUCTIONS>

    <BEGIN USER EXPERIENCE>
    {user_query}
    <END USER EXPERIENCE>

    <BEGIN SONG>
    Title: {song_title}
    Artist: {artist}
    
    Lyrics:
    {lyrics}
    <END SONG>

    <BEGIN JSON RESPONSE>
    """
    
    # Safety settings to avoid blocking by safety filters
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    try:
        response = await gemini_model.generate_content_async(
            prompt, 
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=256000  # Increased from 50
            ),
            safety_settings=safety_settings
        )
        
        # Check if the response is valid before accessing .text
        if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
            print(response)
            # Log details if available
            if response.prompt_feedback:
                print(f"   Prompt Feedback: {response.prompt_feedback}")
            if response.candidates:
                 print(f"   Finish Reason: {response.candidates[0].finish_reason}")
                 print(f"   Safety Ratings: {response.candidates[0].safety_ratings}")
            return 0
        
        # Clean and parse the response
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        result = json.loads(json_response)
        score = result.get("score", 0)
        
        # Ensure score is within valid range
        score = max(0, min(100, int(score)))
        return score
        
    except Exception as e:
        print(f"⚠️ Error rating song '{song_title}' by {artist}: {e}")
        return 0

async def filter_songs_with_llm(user_query: str, candidates_df: pd.DataFrame, min_score: int = 50) -> pd.DataFrame:
    """
    Filter candidate songs using Gemini Flash 2.5 Lite to rate lyrics relevance.
    
    Args:
        user_query: The original user experience/query
        candidates_df: DataFrame with candidate songs
        min_score: Minimum score threshold (0-100) to keep songs
        
    Returns:
        Filtered DataFrame with songs that scored >= min_score, sorted by score descending
    """
    # Initialize Gemini
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel(GEMINI_MODEL)
    
    # Get lyrics for all candidates
    print("🎵 Retrieving lyrics for candidate songs...")
    lyrics_map = get_lyrics_for_candidates(candidates_df)
    
    if not lyrics_map:
        print("❌ No lyrics found for candidate songs")
        return pd.DataFrame()
    
    print(f"📝 Found lyrics for {len(lyrics_map)} songs. Rating with Gemini...")
    
    tasks = []
    for _, candidate in candidates_df.iterrows():
        title = candidate['title']
        artist = candidate['artist']
        song_key = (title, artist)
        
        if song_key in lyrics_map:
            lyrics = lyrics_map[song_key]
            tasks.append(
                rate_song_with_gemini(user_query, title, artist, lyrics, gemini_model)
            )

    scores = await asyncio.gather(*tasks)
    
    scored_songs = []
    for i, (_, candidate) in enumerate(candidates_df.iterrows()):
        title = candidate['title']
        artist = candidate['artist']
        song_key = (title, artist)

        if song_key in lyrics_map:
            score = scores.pop(0)
            if score >= min_score:
                candidate_with_score = candidate.copy()
                candidate_with_score['llm_score'] = score
                scored_songs.append(candidate_with_score)
            
            print(f"  {i+1}/{len(candidates_df)}: '{title}' by {artist} - Score: {score}")
        else:
            print(f"  {i+1}/{len(candidates_df)}: '{title}' by {artist} - No lyrics found")
    
    if not scored_songs:
        print(f"❌ No songs scored >= {min_score}")
        return pd.DataFrame()
    
    # Convert to DataFrame and sort by score
    result_df = pd.DataFrame(scored_songs)
    result_df = result_df.sort_values('llm_score', ascending=False).reset_index(drop=True)
    
    print(f"✅ Filtered to {len(result_df)} songs with LLM scores >= {min_score}")
    return result_df
