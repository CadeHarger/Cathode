import os
import re
from typing import List, Optional, Sequence, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _get_data_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "data")


def _find_pkl_chunks(data_dir: str) -> List[str]:
    if not os.path.isdir(data_dir):
        return []
    pattern = re.compile(r"^other_columns_chunk_(\d+)\.pkl$")
    files = []
    for name in os.listdir(data_dir):
        match = pattern.match(name)
        if match:
            files.append((int(match.group(1)), os.path.join(data_dir, name)))
    files.sort(key=lambda x: x[0])
    return [path for _, path in files]


def _load_views_from_pkls(data_dir: str) -> pd.Series:
    pkl_paths = _find_pkl_chunks(data_dir)
    if not pkl_paths:
        raise FileNotFoundError(
            f"No PKL files found in {data_dir}. Expected files like 'other_columns_chunk_1.pkl'."
        )

    series_list: List[pd.Series] = []
    for path in pkl_paths:
        df = pd.read_pickle(path)
        # Be tolerant to capitalization or naming variations
        candidate_cols = [c for c in df.columns if c.lower() == "views"]
        if not candidate_cols:
            continue
        views_col = candidate_cols[0]
        series_list.append(df[views_col])

    if not series_list:
        raise ValueError("No 'views' column found in any PKL chunk.")

    views = pd.concat(series_list, ignore_index=True)
    # Coerce to numeric and drop NaNs/non-numeric
    views = pd.to_numeric(views, errors="coerce").dropna()
    # Remove negative values if any
    views = views[views >= 0]
    return views.astype(float)


def plot_views_histogram(
    views: pd.Series,
    bins: Union[int, Sequence[float]] = 10,
    save_path: Optional[str] = None,
    x_max: Optional[float] = None,
) -> None:
    plt.figure(figsize=(10, 6))
    if isinstance(bins, int) and x_max is not None:
        plt.hist(views.values, bins=bins, range=(0, x_max), color="#4C72B0", edgecolor="white")
    else:
        plt.hist(views.values, bins=bins, color="#4C72B0", edgecolor="white")
    plt.title("Distribution of Song Views")
    plt.xlabel("Views")
    plt.ylabel("Number of Songs")
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150)
        print(f"Saved histogram to: {save_path}")

    plt.show()


def main():
    # === CONFIGURATION SECTION ===
    # Manually set bucket sizes here - define 10 bucket edges to create 9 buckets
    # Set use_custom_buckets to True to use these values, False for equal-width bins
    
    use_custom_buckets: bool = True  # Set to True to use the bucket edges below
    
    # Define your 10 bucket edges (creates 9 buckets between them)
    # Adjust these values as needed for your analysis
    bucket_edge_1: float = 0           # Start edge
    bucket_edge_2: float = 100     
    bucket_edge_3: float = 1_000      
    bucket_edge_4: float = 10_000   
    bucket_edge_5: float = 100_000   
    bucket_edge_6: float = 500_000   
    bucket_edge_7: float = 1_000_000 
    bucket_edge_8: float = 2_000_000  
    bucket_edge_9: float = 5_000_000  
    bucket_edge_10: float = 10_000_000 
    
    # If use_custom_buckets is False, use equal-width bins with this cap
    max_views_cap: float = 10_000_000  # Cap views at this value for equal-width bins
    
    # === END CONFIGURATION SECTION ===

    data_dir = _get_data_dir()
    print(f"Loading 'views' from PKL chunks in: {data_dir}")
    views = _load_views_from_pkls(data_dir)
    print(f"Loaded {len(views):,} rows with valid 'views'.")

    # Build manual bin edges from individual variables if using custom buckets
    manual_bin_edges: Optional[List[float]] = None
    if use_custom_buckets:
        manual_bin_edges = [
            bucket_edge_1, bucket_edge_2, bucket_edge_3, bucket_edge_4, bucket_edge_5,
            bucket_edge_6, bucket_edge_7, bucket_edge_8, bucket_edge_9, bucket_edge_10
        ]
        
        # Validate the bucket edges
        if any(b < 0 for b in manual_bin_edges):
            raise ValueError("All bucket edges must be non-negative")
        if sorted(manual_bin_edges) != manual_bin_edges:
            raise ValueError("Bucket edges must be sorted in ascending order")
        print(f"Using custom bucket edges: {[f'{edge:,.0f}' for edge in manual_bin_edges]}")

    # Trim outliers if using equal-width bins (only when not using custom buckets)
    if manual_bin_edges is None:
        original_count = len(views)
        views = views[views <= max_views_cap]
        trimmed_count = original_count - len(views)
        if trimmed_count > 0:
            print(f"Trimmed {trimmed_count:,} songs above {max_views_cap:,.0f} views.")
        else:
            print(f"No songs above {max_views_cap:,.0f} views.")
    else:
        print("Using custom buckets - no view count capping applied.")

    # Also print counts per bin in case a GUI is not available
    if manual_bin_edges is not None:
        bins_spec: Union[int, Sequence[float]] = manual_bin_edges
        counts, bin_edges = np.histogram(views.values, bins=manual_bin_edges)
        out_name = "views_histogram_custom_bins.png"
        print(f"\nUsing custom bin edges ({len(manual_bin_edges)-1} bins)")
    else:
        bins_spec = 10
        counts, bin_edges = np.histogram(views.values, bins=10, range=(0, max_views_cap))
        out_name = "views_histogram_capped_10M.png"
    
    num_bins = len(manual_bin_edges)-1 if manual_bin_edges is not None else 10
    print(f"\nHistogram ({num_bins} bins):")
    def _fmt_edge(x: float) -> str:
        return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.2f}"
    for i in range(len(counts)):
        left = bin_edges[i]
        right = bin_edges[i + 1]
        print(f"[{_fmt_edge(left)}, {_fmt_edge(right)}) -> {counts[i]:,} songs")

    save_path = os.path.join(data_dir, out_name)
    plot_views_histogram(views, bins=bins_spec, save_path=save_path, x_max=(None if manual_bin_edges else max_views_cap))


if __name__ == "__main__":
    main()

