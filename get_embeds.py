import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from tqdm import tqdm
import pickle
import torch
import gc
from concurrent.futures import ThreadPoolExecutor
import psutil

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
    
    print("Loading sentence transformer model...")
    model = SentenceTransformer('all-mpnet-base-v2')
    
    # Choose best available device: CUDA > MPS (Apple Silicon) > CPU
    target_device = 'cpu'
    if torch.cuda.is_available():
        target_device = 'cuda'
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        target_device = 'mps'
    model = model.to(target_device)
    print(f"Model device set to: {target_device}")
    
    # Optimize model for inference
    if target_device == 'cuda':
        # Use half precision for faster inference on GPU
        model = model.half()
        print("Using half precision (float16) for faster GPU inference")
        
        # Compile model for better performance (PyTorch 2.0+)
        try:
            model = torch.compile(model, mode='max-autotune')
            print("Model compiled with torch.compile for better performance")
        except Exception as e:
            print(f"Could not compile model: {e}")
    
    # Verify device
    try:
        print(f"Model device: {model.device}")
    except Exception:
        pass
    
    # Determine optimal batch size based on available memory
    optimal_batch_size = 128  # default
    if target_device == 'cuda':
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"GPU memory: {gpu_memory_gb:.1f} GB")
        if gpu_memory_gb >= 16:
            optimal_batch_size = 512
        elif gpu_memory_gb >= 8:
            optimal_batch_size = 256
        else:
            optimal_batch_size = 128
    elif target_device == 'mps':
        optimal_batch_size = 256  # MPS can usually handle larger batches
    
    print(f"Using batch size: {optimal_batch_size}")
    
    # Process each chunk file
    for chunk_idx in range(4):
        chunk_num = chunk_idx + 1
        chunk_file = f'./data/song_lyrics_chunk_{chunk_num}.csv'
        
        print(f"\nProcessing chunk {chunk_num}/4...")
        print(f"Loading {chunk_file}...")
        
        # Load only the lyrics column for faster loading
        try:
            # First, peek at the file to get column names
            df_peek = pd.read_csv(chunk_file, nrows=1)
            if 'lyrics' not in df_peek.columns:
                print(f"Error: 'lyrics' column not found in {chunk_file}")
                print(f"Available columns: {list(df_peek.columns)}")
                continue
            
            # Load only lyrics column for embedding (much faster)
            df_lyrics = pd.read_csv(chunk_file, usecols=['lyrics'], dtype={'lyrics': 'string'})
            print(f"Loaded {len(df_lyrics)} lyrics from chunk {chunk_num}")
            
            # Load other columns separately only if we need to save them
            other_columns = [col for col in df_peek.columns if col != 'lyrics']
            if chunk_idx == 0:  # Only print this once
                print(f"Other columns to preserve: {other_columns}")
                
        except FileNotFoundError:
            print(f"Error: {chunk_file} not found. Skipping this chunk.")
            continue
        except Exception as e:
            print(f"Error loading {chunk_file}: {e}. Skipping this chunk.")
            continue
        
        # Extract and clean lyrics
        chunk_lyrics = df_lyrics['lyrics'].dropna().tolist()
        # Filter out empty strings and None values
        chunk_lyrics = [lyric for lyric in chunk_lyrics if lyric and str(lyric).strip()]
        
        print(f"Embedding {len(chunk_lyrics)} lyrics...")
        
        # Encode this chunk (normalized embeddings, efficient internal batching)
        with torch.inference_mode():
            embeddings_array = model.encode(
                chunk_lyrics,
                batch_size=optimal_batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True,
                device=target_device,
            )
        print(f"Embeddings shape: {embeddings_array.shape}")
            
        # Save embeddings (float16 to reduce disk/IO and speed up loading)
        embeddings_filename = f'./data/embeddings_chunk_{chunk_num}.npy'
        np.save(embeddings_filename, embeddings_array.astype(np.float16))
        print(f"Saved embeddings to {embeddings_filename}")
        
        # Only save other columns if they don't already exist (avoid redundant I/O)
        other_filename = f'./data/other_columns_chunk_{chunk_num}.csv'
        pickle_filename = f'./data/other_columns_chunk_{chunk_num}.pkl'
        
        if not os.path.exists(pickle_filename):
            # Load other columns only when needed
            df_other = pd.read_csv(chunk_file, usecols=other_columns)
            
            # Save as pickle only (faster loading, smaller files)
            df_other.to_pickle(pickle_filename)
            print(f"Saved other columns to {pickle_filename}")
            
            # Clean up
            del df_other
        else:
            print(f"Other columns file already exists: {pickle_filename}")
        
        # Clear memory more aggressively
        del embeddings_array, chunk_lyrics, df_lyrics
        gc.collect()  # Force garbage collection
        
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()  # Ensure all operations complete
        
        # Print memory usage
        if chunk_idx == 0:  # Only print once to avoid spam
            ram_usage = psutil.virtual_memory().percent
            print(f"RAM usage: {ram_usage:.1f}%")
            if torch.cuda.is_available():
                gpu_memory_used = torch.cuda.memory_allocated() / 1024**3
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                print(f"GPU memory: {gpu_memory_used:.1f}/{gpu_memory_total:.1f} GB")
    
    print("\nAll chunks processed successfully!")
    print("Files created:")
    for i in range(1, 5):
        print(f"  - embeddings_chunk_{i}.npy")
        print(f"  - other_columns_chunk_{i}.csv")
        print(f"  - other_columns_chunk_{i}.pkl")

if __name__ == "__main__":
    load_and_embed_lyrics()



