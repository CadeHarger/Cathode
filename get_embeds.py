import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from tqdm import tqdm
import pickle
import torch

def load_and_embed_lyrics():
    """
    Load song_lyrics.csv, embed the 'lyrics' column using sentence transformers,
    and save results in 4 chunks to manage memory usage.
    """
    
    # Check CUDA availability
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current CUDA device: {torch.cuda.current_device()}")
        print(f"CUDA device name: {torch.cuda.get_device_name()}")
    else:
        print("CUDA not available, will use CPU")
    
    # Load the CSV file
    print("Loading CSV file...")
    df = pd.read_csv('./data/song_lyrics.csv')
    print(f"Loaded {len(df)} rows")
    
    # Check if 'lyrics' column exists
    if 'lyrics' not in df.columns:
        print("Error: 'lyrics' column not found in CSV")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Get all columns except 'lyrics'
    other_columns = [col for col in df.columns if col != 'lyrics']
    print(f"Other columns to preserve: {other_columns}")
    
    # Load the sentence transformer model (MiniLM is much faster and smaller than MPNet)
    print("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Choose best available device: CUDA > MPS (Apple Silicon) > CPU
    target_device = 'cpu'
    if torch.cuda.is_available():
        target_device = 'cuda'
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        target_device = 'mps'
    model = model.to(target_device)
    print(f"Model device set to: {target_device}")
    
    # Verify device
    try:
        print(f"Model device: {model.device}")
    except Exception:
        pass
    
    # Calculate chunk size (25% of data each)
    total_rows = len(df)
    chunk_size = total_rows // 4
    print(f"Total rows: {total_rows}, Chunk size: {chunk_size}")
    
    # Process each chunk
    for chunk_idx in range(4):
        print(f"\nProcessing chunk {chunk_idx + 1}/4...")
        
        # Calculate start and end indices for this chunk
        start_idx = chunk_idx * chunk_size
        if chunk_idx == 3:  # Last chunk gets any remaining rows
            end_idx = total_rows
        else:
            end_idx = (chunk_idx + 1) * chunk_size
        
        print(f"Processing rows {start_idx} to {end_idx-1} ({end_idx - start_idx} rows)")
        
        # Extract lyrics for this chunk
        chunk_lyrics = df['lyrics'].iloc[start_idx:end_idx].tolist()
        
        # Remove any None or NaN values
        chunk_lyrics = [lyric for lyric in chunk_lyrics if pd.notna(lyric) and lyric is not None]
        
        print(f"Embedding {len(chunk_lyrics)} lyrics...")
        
    # Encode this chunk (normalized embeddings, efficient internal batching)
    with torch.inference_mode():
        embeddings_array = model.encode(
            chunk_lyrics,
            batch_size=128,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    print(f"Embeddings shape: {embeddings_array.shape}")
        
    # Save embeddings (float16 to reduce disk/IO and speed up loading)
    embeddings_filename = f'./data/embeddings_chunk_{chunk_idx + 1}.npy'
    np.save(embeddings_filename, embeddings_array.astype(np.float16))
        print(f"Saved embeddings to {embeddings_filename}")
        
        # Save corresponding other columns
        other_data = df[other_columns].iloc[start_idx:end_idx].copy()
        other_filename = f'./data/other_columns_chunk_{chunk_idx + 1}.csv'
        other_data.to_csv(other_filename, index=False)
        print(f"Saved other columns to {other_filename}")
        
        # Also save as pickle for easier loading later
        pickle_filename = f'./data/other_columns_chunk_{chunk_idx + 1}.pkl'
        other_data.to_pickle(pickle_filename)
        print(f"Saved other columns to {pickle_filename}")
        
        # Clear memory
        del embeddings_array, other_data, chunk_lyrics
        
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    print("\nAll chunks processed successfully!")
    print("Files created:")
    for i in range(1, 5):
        print(f"  - embeddings_chunk_{i}.npy")
        print(f"  - other_columns_chunk_{i}.csv")
        print(f"  - other_columns_chunk_{i}.pkl")

if __name__ == "__main__":
    load_and_embed_lyrics()



