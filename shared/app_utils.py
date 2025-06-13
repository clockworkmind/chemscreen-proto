"""
Application utilities for ChemScreen multipage application.

Contains functions for session state management, demo data loading, and other app utilities.
"""

import logging
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# Add the chemscreen package to the path
sys.path.append(str(Path(__file__).parent.parent))

from chemscreen.cached_processors import cached_process_csv_data
from chemscreen.config import initialize_config
from chemscreen.errors import (
    log_error_for_support,
    show_error_with_help,
)
from chemscreen.models import CSVColumnMapping

logger = logging.getLogger(__name__)


def init_session_state() -> None:
    """Initialize session state variables."""
    config = initialize_config()

    if "chemicals" not in st.session_state:
        st.session_state.chemicals = []
    if "search_results" not in st.session_state:
        st.session_state.search_results = {}
    if "current_batch_id" not in st.session_state:
        st.session_state.current_batch_id = None
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "date_range_years": config.default_date_range_years,
            "max_results_per_chemical": config.max_results_per_chemical,
            "include_reviews": config.default_include_reviews,
            "cache_enabled": config.cache_enabled,
            "max_batch_size": config.max_batch_size,
        }


def reset_session() -> None:
    """Reset session state to start over."""
    st.session_state.chemicals = []
    st.session_state.search_results = {}
    st.session_state.current_batch_id = None
    # Keep search history and settings
    st.success("✅ Session reset! You can now upload a new file.")
    st.rerun()


def load_demo_data(size: str) -> None:
    """Load demo dataset into session state.

    Args:
        size: One of 'small', 'medium', or 'large'
    """
    try:
        # Map size to filename
        size_map = {
            "small": "demo_small.csv",
            "medium": "demo_medium.csv",
            "large": "demo_large.csv",
        }

        if size not in size_map:
            show_error_with_help(
                "invalid_parameter",
                f"Invalid demo size '{size}'. Available sizes: {', '.join(size_map.keys())}",
            )
            return

        # Load the demo file
        demo_file_path = Path(__file__).parent.parent / "data" / "raw" / size_map[size]

        if not demo_file_path.exists():
            show_error_with_help(
                "file_not_found",
                f"Demo file missing: {demo_file_path.name}",
                expand_help=True,
            )
            logger.error(f"Demo file not found: {demo_file_path}")
            return

        # Read the CSV file
        demo_data = pd.read_csv(demo_file_path)

        if demo_data.empty:
            show_error_with_help(
                "empty_file", f"Demo file {demo_file_path.name} contains no data"
            )
            return

        # Create column mapping for demo data
        column_mapping = CSVColumnMapping(
            name_column="chemical_name",
            cas_column="cas_number",
            synonyms_column="synonyms",
            notes_column="notes",
        )

        # Process the demo data with enhanced loading states
        with st.spinner(f"Loading {size} demo dataset..."):
            # Show detailed progress
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("📂 Reading demo file...")
                progress_bar.progress(0.2)
                time.sleep(0.2)

                status_text.text("🔍 Processing chemical data...")
                progress_bar.progress(0.4)

                result = cached_process_csv_data(demo_data, column_mapping)

                status_text.text("✅ Validating chemicals...")
                progress_bar.progress(0.8)
                time.sleep(0.2)

                status_text.text("✨ Demo data ready!")
                progress_bar.progress(1.0)
                time.sleep(0.3)
                progress_container.empty()

            if result.valid_chemicals:
                st.session_state.chemicals = result.valid_chemicals

        # Store demo loading result in session state for main area display
        if result.valid_chemicals:
            st.session_state.chemicals = result.valid_chemicals
            st.session_state.demo_load_result = {
                "size": size,
                "valid_count": len(result.valid_chemicals),
                "warnings": result.warnings,
                "invalid_rows": result.invalid_rows,
                "success": True,
            }

            # Show success message
            st.success(
                f"✅ {size.title()} demo dataset loaded! "
                f"{len(result.valid_chemicals)} chemicals ready for search."
            )

            # Navigate to upload page to show results
            st.switch_page("pages/1_📤_Upload_Chemicals.py")
        else:
            st.session_state.demo_load_result = {
                "size": size,
                "success": False,
                "error": "Demo data contains no valid chemicals after processing",
            }

    except FileNotFoundError:
        show_error_with_help(
            "file_not_found",
            f"Demo file for size '{size}' is missing",
            expand_help=True,
        )
        logger.error(f"Demo file not found for size: {size}")
    except Exception as e:
        show_error_with_help("demo_data_error", f"Failed to load demo data: {str(e)}")
        log_error_for_support(e, "demo data loading")
