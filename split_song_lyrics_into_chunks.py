import os
import sys
from typing import List

import numpy as np
import pandas as pd


def _get_data_dir() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "data")


def _find_embeddings_chunks(data_dir: str) -> List[str]:
    files: List[str] = []
    index = 1
    while True:
        path = os.path.join(data_dir, f"embeddings_chunk_{index}.npy")
        if os.path.exists(path):
            files.append(path)
            index += 1
            continue
        break
    return files


def _get_chunk_sizes_from_embeddings(data_dir: str) -> List[int]:
    files = _find_embeddings_chunks(data_dir)
    if not files:
        raise FileNotFoundError(
            f"No embeddings chunks found in {data_dir}. Expected files named 'embeddings_chunk_{1..N}.npy'."
        )
    sizes: List[int] = []
    for path in files:
        arr = np.load(path, mmap_mode="r")
        sizes.append(int(arr.shape[0]))
        del arr
    return sizes


def _write_frame(path: str, df: pd.DataFrame, write_header: bool) -> None:
    df.to_csv(path, mode="a" if os.path.exists(path) else "w", index=False, header=write_header)


def split_song_lyrics_into_chunks() -> None:
    data_dir = _get_data_dir()
    source_csv = os.path.join(data_dir, "song_lyrics.csv")
    if not os.path.exists(source_csv):
        raise FileNotFoundError(f"Missing source CSV: {source_csv}")

    chunk_sizes = _get_chunk_sizes_from_embeddings(data_dir)
    if not chunk_sizes:
        raise RuntimeError("Could not determine chunk sizes from embeddings")

    total_rows_target = sum(chunk_sizes)
    print(f"Detected {len(chunk_sizes)} chunks from embeddings: {chunk_sizes} (total rows: {total_rows_target:,})")

    current_chunk_index = 1
    rows_remaining_in_chunk = chunk_sizes[0]
    rows_written_total = 0

    out_paths: List[str] = [os.path.join(data_dir, f"song_lyrics_chunk_{i+1}.csv") for i in range(len(chunk_sizes))]
    for p in out_paths:
        if os.path.exists(p):
            os.remove(p)

    csv_iter = pd.read_csv(source_csv, chunksize=100_000)
    for frame in csv_iter:
        df = frame
        while len(df) > 0 and current_chunk_index <= len(chunk_sizes):
            take = min(rows_remaining_in_chunk, len(df))
            part = df.iloc[:take]
            df = df.iloc[take:]

            out_path = out_paths[current_chunk_index - 1]
            write_header = not os.path.exists(out_path)
            _write_frame(out_path, part, write_header=write_header)

            rows_remaining_in_chunk -= take
            rows_written_total += take

            if rows_remaining_in_chunk == 0:
                print(f"Wrote chunk {current_chunk_index}: {chunk_sizes[current_chunk_index - 1]:,} rows -> {out_path}")
                current_chunk_index += 1
                if current_chunk_index <= len(chunk_sizes):
                    rows_remaining_in_chunk = chunk_sizes[current_chunk_index - 1]

        if current_chunk_index > len(chunk_sizes):
            break

    if rows_written_total < total_rows_target:
        raise RuntimeError(
            f"Source CSV ended early: wrote {rows_written_total:,} < expected {total_rows_target:,} rows from embeddings."
        )

    if rows_written_total > total_rows_target:
        print(
            f"Warning: source CSV has extra rows beyond expected {total_rows_target:,}. "
            f"Ignored {rows_written_total - total_rows_target:,} trailing rows."
        )

    print("\nDone.")
    for path in out_paths:
        print(f"  - {os.path.basename(path)}: {sum(1 for _ in open(path)) - 1:,} data rows (plus header)")


if __name__ == "__main__":
    try:
        split_song_lyrics_into_chunks()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

