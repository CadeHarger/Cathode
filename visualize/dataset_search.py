#!/usr/bin/env python3
"""
Dataset Search Tool

This script loads the song dataset from multiple chunks and allows users to search
for songs by title in an interactive loop. It displays the complete row data for
each matching song.
"""

import os
import pandas as pd
import logging
from typing import List, Dict, Any

# Configure logging (console only, no log files)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatasetSearcher:
    def __init__(self, data_dir: str = 'data'):
        """
        Initialize the dataset searcher.
        
        Args:
            data_dir: Directory containing the dataset chunks
        """
        self.data_dir = data_dir
        self.dataset = None
        self.load_dataset()
    
    def load_dataset(self) -> None:
        """Load all dataset chunks into a single DataFrame."""
        logger.info("Loading dataset chunks...")
        
        chunks = []
        chunk_files = []
        
        # Find all other_columns chunk files
        for i in range(1, 5):  # Assuming chunks 1-4 based on your data structure
            csv_path = os.path.join(self.data_dir, f'other_columns_chunk_{i}.csv')
            if os.path.exists(csv_path):
                chunk_files.append(csv_path)
                logger.info(f"Found chunk file: {csv_path}")
        
        if not chunk_files:
            raise FileNotFoundError(f"No chunk files found in {self.data_dir}")
        
        # Load each chunk
        for chunk_file in chunk_files:
            try:
                logger.info(f"Loading {chunk_file}...")
                chunk_df = pd.read_csv(chunk_file)
                chunks.append(chunk_df)
                logger.info(f"Loaded {len(chunk_df)} rows from {chunk_file}")
            except Exception as e:
                logger.error(f"Error loading {chunk_file}: {e}")
                continue
        
        if not chunks:
            raise RuntimeError("No chunks were successfully loaded")
        
        # Combine all chunks
        self.dataset = pd.concat(chunks, ignore_index=True)
        logger.info(f"Dataset loaded successfully! Total rows: {len(self.dataset)}")
        logger.info(f"Columns: {list(self.dataset.columns)}")
    
    def search_songs(self, title_term: str = "", artist_term: str = "", case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Search for songs by title and/or artist.
        
        Args:
            title_term: The term to search for in song titles (optional)
            artist_term: The term to search for in artist names (optional)
            case_sensitive: Whether the search should be case sensitive
            
        Returns:
            List of matching rows as dictionaries
        """
        if self.dataset is None:
            logger.error("Dataset not loaded")
            return []
        
        # Start with all rows
        mask = pd.Series([True] * len(self.dataset))
        
        # Apply title filter if provided
        if title_term.strip():
            if case_sensitive:
                title_mask = self.dataset['title'].str.contains(title_term, na=False)
            else:
                title_mask = self.dataset['title'].str.contains(title_term, case=False, na=False)
            mask = mask & title_mask
        
        # Apply artist filter if provided
        if artist_term.strip():
            if case_sensitive:
                artist_mask = self.dataset['artist'].str.contains(artist_term, na=False)
            else:
                artist_mask = self.dataset['artist'].str.contains(artist_term, case=False, na=False)
            mask = mask & artist_mask
        
        matches = self.dataset[mask]
        
        # Convert to list of dictionaries for easier handling
        results = matches.to_dict('records')
        
        # Create search description
        search_parts = []
        if title_term.strip():
            search_parts.append(f"title: '{title_term}'")
        if artist_term.strip():
            search_parts.append(f"artist: '{artist_term}'")
        search_desc = " AND ".join(search_parts) if search_parts else "no criteria"
        
        logger.info(f"Search for {search_desc} found {len(results)} matches")
        
        return results
    
    def display_results(self, results: List[Dict[str, Any]], search_description: str) -> None:
        """
        Display search results in a formatted way.
        
        Args:
            results: List of matching rows
            search_description: Description of the search criteria
        """
        if not results:
            print(f"\nNo matches found for {search_description}")
            return
        
        print(f"\n{'='*80}")
        print(f"Found {len(results)} match(es) for {search_description}:")
        print(f"{'='*80}")
        
        for i, row in enumerate(results, 1):
            print(f"\n--- Match {i} ---")
            
            # Display formatted output to user
            for key, value in row.items():
                print(f"{key:15}: {value}")
            
            # Log the complete row data to console
            logger.info(f"Match {i} complete row data: {row}")
            
            if i < len(results):
                print("-" * 40)
    
    def interactive_search(self) -> None:
        """Run the interactive search loop."""
        print("\n" + "="*80)
        print("DATASET SEARCH TOOL")
        print("="*80)
        print(f"Dataset loaded with {len(self.dataset)} songs")
        print("Search by title and/or artist")
        print("Leave either field blank to search by the other field only")
        print("Type 'quit', 'exit', or 'q' in title field to stop searching")
        print("Type 'help' in title field for search tips")
        print("="*80)
        
        while True:
            try:
                # Get user input for title
                title_term = input("\nEnter song title to search for (or press Enter to skip): ").strip()
                
                # Handle special commands
                if title_term.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    logger.info("User exited the search tool")
                    break
                
                if title_term.lower() == 'help':
                    self.show_help()
                    continue
                
                # Get user input for artist
                artist_term = input("Enter artist name to search for (or press Enter to skip): ").strip()
                
                # Check if both are empty
                if not title_term and not artist_term:
                    print("Please enter at least one search term (title or artist)")
                    continue
                
                # Perform search
                results = self.search_songs(title_term, artist_term)
                
                # Create search description
                search_parts = []
                if title_term:
                    search_parts.append(f"title: '{title_term}'")
                if artist_term:
                    search_parts.append(f"artist: '{artist_term}'")
                search_desc = " AND ".join(search_parts)
                
                # Display results
                self.display_results(results, search_desc)
                
            except KeyboardInterrupt:
                print("\n\nSearch interrupted by user")
                logger.info("Search interrupted by KeyboardInterrupt")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                logger.error(f"Error during search: {e}")
    
    def show_help(self) -> None:
        """Display help information."""
        help_text = """
SEARCH TIPS:
- Search is case-insensitive by default
- Use partial titles/artists (e.g., "love" will find "Love Song", "I Love You", etc.)
- Search terms can include spaces and special characters
- You can search by title only, artist only, or both
- Leave a field blank to skip that search criteria
- All matching rows will be displayed and logged to console

SEARCH EXAMPLES:
- Title only: Enter "love" for title, leave artist blank
- Artist only: Leave title blank, enter "jay" for artist  
- Both: Enter "love" for title and "jay" for artist (finds songs with "love" in title by artists with "jay" in name)

COMMANDS:
- 'quit', 'exit', or 'q' (in title field): Exit the program
- 'help' (in title field): Show this help message

DATASET INFO:
- Total songs: {}
- Columns: {}
        """.format(len(self.dataset), ', '.join(self.dataset.columns))
        
        print(help_text)

def main():
    """Main function to run the dataset search tool."""
    try:
        # Initialize the searcher
        searcher = DatasetSearcher()
        
        # Start interactive search
        searcher.interactive_search()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure you're running this script from the correct directory")
        print("and that the data files exist in the 'data' folder")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logger.error(f"Unexpected error in main: {e}")

if __name__ == "__main__":
    main()