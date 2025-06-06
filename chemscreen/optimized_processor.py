"""Optimized processor functions for large datasets."""

import pandas as pd
from typing import List, Tuple, Generator
from chemscreen.models import Chemical


def optimized_detect_duplicates(chemicals: List[Chemical]) -> List[Tuple[int, int]]:
    """
    Optimized duplicate detection using vectorized operations.

    Args:
        chemicals: List of Chemical objects

    Returns:
        List of tuples with duplicate indices
    """
    if not chemicals:
        return []

    # Convert to DataFrame for vectorized operations
    data = []
    for i, chem in enumerate(chemicals):
        data.append(
            {
                "index": i,
                "name_lower": chem.name.lower() if chem.name else "",
                "cas_number": chem.cas_number or "",
            }
        )

    df = pd.DataFrame(data)
    duplicates = []

    # Find CAS duplicates (more reliable)
    cas_df = df[df["cas_number"] != ""]
    if not cas_df.empty:
        cas_dups = cas_df[cas_df.duplicated(subset=["cas_number"], keep="first")]
        for _, dup_row in cas_dups.iterrows():
            first_idx = df[df["cas_number"] == dup_row["cas_number"]].iloc[0]["index"]
            duplicates.append((int(first_idx), int(dup_row["index"])))

    # Find name duplicates (excluding already found CAS duplicates)
    already_found = {dup[1] for dup in duplicates}
    name_df = df[~df["index"].isin(already_found) & (df["name_lower"] != "")]
    if not name_df.empty:
        name_dups = name_df[name_df.duplicated(subset=["name_lower"], keep="first")]
        for _, dup_row in name_dups.iterrows():
            first_idx = df[df["name_lower"] == dup_row["name_lower"]].iloc[0]["index"]
            duplicates.append((int(first_idx), int(dup_row["index"])))

    return duplicates


def process_csv_in_chunks(
    df: pd.DataFrame, chunk_size: int = 1000
) -> Generator[pd.DataFrame, None, None]:
    """
    Process large DataFrames in chunks to reduce memory usage.

    Args:
        df: DataFrame to process
        chunk_size: Number of rows per chunk

    Yields:
        DataFrame chunks
    """
    for start in range(0, len(df), chunk_size):
        end = min(start + chunk_size, len(df))
        yield df.iloc[start:end]
