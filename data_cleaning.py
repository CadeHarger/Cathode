import os
import shutil
import pandas as pd
import numpy as np

def clean_data_chunks(source_dir='data', dest_dir='data/cleaned'):
    """
    Loads song data chunks, filters them, and saves the cleaned chunks to a new directory.

    Filters:
    - Year >= 1800
    - Language is 'en' or 'es'
    """
    # Clean up the destination directory before starting
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
        print(f"Removed existing directory: {dest_dir}")
    os.makedirs(dest_dir)
    print(f"Created directory: {dest_dir}")

    # Assuming chunks are numbered 1 through 4
    for i in range(1, 5):
        print(f"Processing chunk {i}...")

        # Define file paths for the current chunk
        other_cols_csv_path = os.path.join(source_dir, f'other_columns_chunk_{i}.csv')
        other_cols_pkl_path = os.path.join(source_dir, f'other_columns_chunk_{i}.pkl')
        lyrics_path = os.path.join(source_dir, f'song_lyrics_chunk_{i}.csv')
        embeddings_path = os.path.join(source_dir, f'embeddings_chunk_{i}.npy')

        # Check if all required files for the chunk exist
        if not all(os.path.exists(p) for p in [other_cols_csv_path, lyrics_path, embeddings_path]):
            print(f"Skipping chunk {i} due to missing files.")
            continue
        
        # Load the data for the current chunk
        try:
            other_cols_df = pd.read_csv(other_cols_csv_path)
            lyrics_df = pd.read_csv(lyrics_path)
            embeddings = np.load(embeddings_path)
        except Exception as e:
            print(f"Error loading data for chunk {i}: {e}")
            continue

        # --- Data Integrity Check ---
        min_rows = min(len(other_cols_df), len(lyrics_df), len(embeddings))
        if len(other_cols_df) != min_rows or len(lyrics_df) != min_rows or len(embeddings) != min_rows:
            print(f"Chunk {i}: Mismatch in row counts. Trimming to {min_rows} rows.")
            other_cols_df = other_cols_df.iloc[:min_rows]
            lyrics_df = lyrics_df.iloc[:min_rows]
            embeddings = embeddings[:min_rows]

        # --- Data Cleaning ---

        # 1. Filter by year
        initial_rows = len(other_cols_df)
        other_cols_df['year'] = pd.to_numeric(other_cols_df['year'], errors='coerce')
        year_filter = other_cols_df['year'] >= 1800
        
        # 2. Filter by language
        lang_filter = other_cols_df['language'].isin(['en', 'es'])
        
        # Combine filters
        combined_filter = year_filter & lang_filter
        
        # Get the indices to keep
        indices_to_keep = other_cols_df[combined_filter].index
        
        # Ensure indices are within the bounds of the embeddings array
        indices_to_keep = indices_to_keep[indices_to_keep < len(embeddings)]
        
        if len(indices_to_keep) == initial_rows:
            print(f"Chunk {i}: No rows were filtered.")
        else:
            print(f"Chunk {i}: Filtered from {initial_rows} to {len(indices_to_keep)} rows.")

        # Apply the filter to all dataframes and embeddings
        cleaned_other_cols_df = other_cols_df.loc[indices_to_keep].reset_index(drop=True)
        cleaned_lyrics_df = lyrics_df.loc[indices_to_keep].reset_index(drop=True)
        cleaned_embeddings = embeddings[indices_to_keep]

        # --- Save Cleaned Data ---
        
        # Define destination paths
        cleaned_other_cols_csv_path = os.path.join(dest_dir, f'other_columns_chunk_{i}.csv')
        cleaned_other_cols_pkl_path = os.path.join(dest_dir, f'other_columns_chunk_{i}.pkl')
        cleaned_lyrics_path = os.path.join(dest_dir, f'song_lyrics_chunk_{i}.csv')
        cleaned_embeddings_path = os.path.join(dest_dir, f'embeddings_chunk_{i}.npy')

        # Save the cleaned data
        cleaned_other_cols_df.to_csv(cleaned_other_cols_csv_path, index=False)
        cleaned_other_cols_df.to_pickle(cleaned_other_cols_pkl_path)
        cleaned_lyrics_df.to_csv(cleaned_lyrics_path, index=False)
        np.save(cleaned_embeddings_path, cleaned_embeddings)

        print(f"Successfully saved cleaned chunk {i} to {dest_dir}")

if __name__ == '__main__':
    # You can run this script directly to perform the cleaning.
    # Make sure your 'data' directory is in the same folder as this script.
    clean_data_chunks()
    print("\nCleaning process complete.")