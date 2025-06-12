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
