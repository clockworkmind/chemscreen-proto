"""
UI utilities for ChemScreen multipage application.

Contains functions for CSS styling, sidebar setup, and other UI components.
"""

import streamlit as st
from pathlib import Path
import sys

# Add the chemscreen package to the path
sys.path.append(str(Path(__file__).parent.parent))

from chemscreen.config import initialize_config


def load_custom_css() -> None:
    """Load custom CSS styles."""
    config = initialize_config()

    st.markdown(
        """
    <style>
    /* Main container styling */
    .main {
        padding-top: 2rem;
    }

    /* Header styling */
    .stApp h1 {
        color: """
        + config.theme_primary_color
        + """;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }

    /* Button styling */
    .stButton > button {
        background-color: """
        + config.theme_primary_color
        + """;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
    }

    .stButton > button:hover {
        background-color: #0052a3;
    }

    /* Success message styling */
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }

    /* Warning message styling */
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }

    /* Info box styling */
    .info-box {
        background-color: #e3f2fd;
        border: 1px solid #bbdefb;
        color: #1565c0;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }

    /* Progress bar custom styling */
    .stProgress > div > div > div > div {
        background-color: """
        + config.theme_primary_color
        + """;
    }

    /* Table styling */
    .dataframe {
        font-size: 14px;
    }

    /* File uploader styling */
    .stFileUploader {
        border: 2px dashed #cccccc;
        border-radius: 4px;
        padding: 2rem;
        text-align: center;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def setup_sidebar() -> None:
    """Configure the sidebar with settings and status (without navigation)."""

    with st.sidebar:
        # Quick Settings
        st.subheader("⚙️ Quick Settings")

        with st.expander("Search Settings", expanded=False):
            st.session_state.settings["date_range_years"] = st.slider(
                "Date Range (years)",
                min_value=1,
                max_value=20,
                value=st.session_state.settings["date_range_years"],
                help="Search for publications from the last N years",
            )

            st.session_state.settings["max_results_per_chemical"] = st.number_input(
                "Max Results per Chemical",
                min_value=10,
                max_value=10000,
                value=st.session_state.settings["max_results_per_chemical"],
                step=10,
                help="Maximum number of results to retrieve per chemical",
            )

            st.session_state.settings["include_reviews"] = st.checkbox(
                "Include Review Articles",
                value=st.session_state.settings["include_reviews"],
                help="Include review articles in search results",
            )

            st.session_state.settings["cache_enabled"] = st.checkbox(
                "Enable Caching",
                value=st.session_state.settings["cache_enabled"],
                help="Cache search results to speed up repeated searches",
            )

        st.markdown("---")

        # Status Information
        st.subheader("📈 Current Status")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Chemicals", len(st.session_state.chemicals))
        with col2:
            st.metric("Results", len(st.session_state.search_results))

        # Session info
        if st.session_state.current_batch_id:
            st.info(f"Batch ID: {st.session_state.current_batch_id}")

        st.markdown("---")

        # Demo Data Quick Access
        st.subheader("📊 Demo Data")
        from .app_utils import load_demo_data

        demo_col1, demo_col2 = st.columns(2)

        with demo_col1:
            if st.button(
                "Small (10)",
                help="Load 10 demo chemicals",
                use_container_width=True,
                key="sidebar_small",
            ):
                load_demo_data("small")

        with demo_col2:
            if st.button(
                "Medium (50)",
                help="Load 50 demo chemicals",
                use_container_width=True,
                key="sidebar_medium",
            ):
                load_demo_data("medium")

        if st.button(
            "Large (150)",
            help="Load 150 demo chemicals with edge cases",
            use_container_width=True,
            key="sidebar_large",
        ):
            load_demo_data("large")

        st.markdown("---")

        # Reset functionality
        if (
            len(st.session_state.chemicals) > 0
            or len(st.session_state.search_results) > 0
        ):
            st.subheader("🔄 Reset")
            if st.button(
                "🗑️ Clear All Data",
                help="Clear uploaded chemicals and search results to start over",
                use_container_width=True,
                type="secondary",
            ):
                from .app_utils import reset_session

                reset_session()

        st.markdown("---")

        # Footer
        st.caption("ChemScreen Prototype v1.0")
        st.caption("© 2025 - For Research Use Only")


def create_progress_with_cancel(
    label: str = "Processing...",
) -> tuple[any, any, any, any]:
    """
    Create a progress bar with cancel functionality.

    Args:
        label: Label for the progress operation

    Returns:
        Tuple of (progress_bar, status_text, cancel_button, progress_container)
    """
    progress_container = st.container()

    with progress_container:
        st.markdown(f"**{label}**")
        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.container():
            cancel_button = st.button("⏸️ Cancel", key=f"cancel_{label}")

    return progress_bar, status_text, cancel_button, progress_container


def show_success_with_stats(
    message: str, stats: dict[str, any], show_balloons: bool = True
) -> None:
    """
    Show success message with statistics.

    Args:
        message: Success message
        stats: Dictionary of statistics to display
        show_balloons: Whether to show celebration balloons
    """
    st.success(f"✅ {message}")

    if stats:
        cols = st.columns(len(stats))
        for i, (key, value) in enumerate(stats.items()):
            with cols[i]:
                st.metric(key, value)

    if show_balloons:
        st.balloons()


def show_help_tooltip(title: str, content: str, icon: str = "💡") -> None:
    """
    Show a help tooltip with consistent styling.

    Args:
        title: Tooltip title
        content: Tooltip content
        icon: Icon to display
    """
    with st.expander(f"{icon} {title}", expanded=False):
        st.markdown(content)


def get_feature_help(feature: str) -> dict[str, str]:
    """
    Get help content for specific features.

    Args:
        feature: Name of the feature

    Returns:
        Dict with 'title', 'content', and 'icon' keys
    """
    help_content = {
        "csv_upload": {
            "title": "CSV Upload Tips",
            "content": """
**Required Format:**
- CSV file with headers
- At least one column with chemical names or CAS numbers
- UTF-8 encoding recommended

**Column Types:**
- **Chemical Name**: Common or IUPAC names (e.g., "Methylene chloride")
- **CAS Number**: Registry numbers in XXX-XX-X format (e.g., "75-09-2")
- **Synonyms**: Alternative names (optional)
- **Notes**: Additional information (optional)

**Tips:**
- Remove duplicate rows before uploading
- Use standard chemical names when possible
- Keep file size under 10MB
- Maximum 200 chemicals per batch
            """,
            "icon": "📤",
        },
        "column_mapping": {
            "title": "Column Mapping Guide",
            "content": """
**Auto-Detection:**
The system tries to automatically detect your columns based on common names like:
- "chemical_name", "name", "compound"
- "cas_number", "cas", "registry_number"

**Manual Selection:**
If auto-detection fails, select the correct columns manually:
- **Chemical Name**: Column containing compound names
- **CAS Number**: Column with CAS Registry Numbers

**Requirements:**
- At least ONE column must be selected (name OR CAS)
- Both columns can be selected for better results
            """,
            "icon": "🔗",
        },
        "search_settings": {
            "title": "Search Settings Explained",
            "content": """
**Date Range:**
- Limits search to publications from recent years
- Shorter ranges = faster searches, fewer results
- Longer ranges = more comprehensive, slower searches

**Max Results per Chemical:**
- Controls how many papers to find for each chemical
- Higher numbers = more comprehensive but slower
- Recommended: 50-100 for most use cases

**Include Reviews:**
- Review articles provide good overviews
- Turn off to focus only on original research

**Cache:**
- Saves previous search results
- Dramatically speeds up repeated searches
- Safe to keep enabled
            """,
            "icon": "⚙️",
        },
        "batch_processing": {
            "title": "Batch Processing Info",
            "content": """
**Performance:**
- Each chemical takes ~30 seconds to search
- 100 chemicals ≈ 50 minutes total time
- Progress is shown in real-time

**Limitations:**
- Maximum 200 chemicals per batch
- Larger batches need to be split
- Memory usage increases with batch size

**Recommendations:**
- Start with smaller batches (10-50 chemicals)
- Monitor progress during searches
- Use cache to avoid re-searching
            """,
            "icon": "⚡",
        },
        "quality_scoring": {
            "title": "Quality Scoring System",
            "content": """
**Scoring Factors:**
- Journal impact factor
- Publication date (newer = higher score)
- Study type (original research vs. review)
- Citation count
- Relevance to chemical name

**Score Ranges:**
- **90-100**: High-quality, recent, relevant studies
- **70-89**: Good quality with minor limitations
- **50-69**: Moderate quality, may be older or less relevant
- **Below 50**: Lower quality, proceed with caution

**Usage:**
- Use scores to prioritize which papers to review first
- Don't exclude lower-scored papers entirely
- Consider context of your specific needs
            """,
            "icon": "📊",
        },
    }

    return help_content.get(
        feature,
        {
            "title": "Help",
            "content": "Help content not available for this feature.",
            "icon": "❓",
        },
    )
