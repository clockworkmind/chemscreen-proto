"""Cached versions of processor functions for performance optimization."""

import streamlit as st
import pandas as pd
from chemscreen.models import CSVColumnMapping, CSVUploadResult
from chemscreen import processor


@st.cache_data(show_spinner=False)
def cached_process_csv_data(
    df: pd.DataFrame,
    _column_mapping: CSVColumnMapping,
) -> CSVUploadResult:
    """
    Cached version of process_csv_data for better performance with large datasets.

    This function is cached by Streamlit to avoid reprocessing the same data.
    The underscore prefix on _column_mapping tells Streamlit not to hash this parameter.
    """
    return processor.process_csv_data(df, _column_mapping)


@st.cache_data(show_spinner=False)
def cached_suggest_column_mapping(df: pd.DataFrame) -> CSVColumnMapping:
    """
    Cached version of suggest_column_mapping to avoid recalculating suggestions.
    """
    return processor.suggest_column_mapping(df)


@st.cache_data(show_spinner=False)
def cached_validate_csv_file(
    file_content: str, delimiter: str = ",", encoding: str = "utf-8"
) -> tuple[bool, pd.DataFrame | None, str | None]:
    """
    Cached version of validate_csv_file for repeated validation checks.
    """
    return processor.validate_csv_file(file_content, delimiter, encoding)
