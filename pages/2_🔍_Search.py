"""
Search page for ChemScreen multipage application.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import asyncio
import time
import logging
from datetime import datetime

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

# Import ChemScreen modules
from chemscreen.config import initialize_config
from chemscreen.models import SearchParameters, BatchSearchSession, Chemical
from chemscreen.pubmed import batch_search
from chemscreen.session_manager import SessionManager
from chemscreen.errors import (
    show_error_with_help,
    create_progress_with_cancel,
    show_success_with_stats,
    log_error_for_support,
    show_help_tooltip,
    get_feature_help,
)

# Import shared utilities
from shared.ui_utils import load_custom_css, setup_sidebar
from shared.app_utils import init_session_state

# Initialize configuration and logging
config = initialize_config()
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Search - ChemScreen",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state and UI
init_session_state()
load_custom_css()

setup_sidebar()


def show_search_page() -> None:
    """Display the search configuration and execution page."""
    st.title("🔍 Search Configuration")

    if not st.session_state.chemicals:
        st.warning("⚠️ No chemicals loaded. Please upload a chemical list first.")
        if st.button("Go to Upload Page"):
            try:
                st.switch_page("pages/1_📤_Upload_Chemicals.py")
            except AttributeError:
                st.info(
                    "💡 Navigate to the **Upload Chemicals** page to load your chemical list."
                )
        return

    # Search configuration
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Search Parameters")

        # Add help for search settings
        help_info = get_feature_help("search_settings")
        show_help_tooltip(help_info["title"], help_info["content"], help_info["icon"])

        _date_range = st.slider(
            "Publication Date Range (years)",
            min_value=1,
            max_value=20,
            value=st.session_state.settings["date_range_years"],
            help="Search for publications from the last N years",
        )

        _max_results = st.number_input(
            "Maximum Results per Chemical",
            min_value=10,
            max_value=10000,
            value=st.session_state.settings["max_results_per_chemical"],
            step=10,
        )

        _include_reviews = st.checkbox(
            "Include Review Articles",
            value=st.session_state.settings["include_reviews"],
        )

        _use_cache = st.checkbox(
            "Use Cached Results",
            value=st.session_state.settings["cache_enabled"],
            help="Use previously cached results when available",
        )

    with col2:
        st.subheader("Batch Information")

        # Add help for batch processing
        help_info = get_feature_help("batch_processing")
        show_help_tooltip(help_info["title"], help_info["content"], help_info["icon"])
        chemical_count = len(st.session_state.chemicals)
        MAX_BATCH_SIZE = config.max_batch_size

        if chemical_count > MAX_BATCH_SIZE:
            st.error(f"❌ Too many chemicals: {chemical_count} (max: {MAX_BATCH_SIZE})")
        else:
            st.info(f"**Chemicals to search**: {chemical_count}")

        # Estimate time
        estimated_time = (
            min(chemical_count, MAX_BATCH_SIZE) * 0.5
        )  # 0.5 minutes per chemical
        st.info(f"**Estimated time**: {estimated_time:.1f} minutes")

        # API key status
        st.subheader("API Configuration")
        api_key_status = (
            "✅ Configured" if config.pubmed_api_key else "❌ Not configured"
        )
        st.markdown(f"**PubMed API Key**: {api_key_status}")

        if api_key_status == "❌ Not configured":
            st.warning("Without an API key, searches will be rate-limited.")

    st.markdown("---")

    # Chemical list preview
    with st.expander("View Chemical List", expanded=False):
        # Convert Chemical objects to a display-friendly DataFrame
        if st.session_state.chemicals:
            chemicals_data = []
            for chemical in st.session_state.chemicals:
                chemicals_data.append(
                    {
                        "Name": chemical.name,
                        "CAS Number": chemical.cas_number or "N/A",
                        "Synonyms": ", ".join(chemical.synonyms)
                        if chemical.synonyms
                        else "None",
                        "Validated": "✅" if chemical.validated else "❌",
                        "Notes": chemical.notes or "",
                    }
                )
            chemicals_df = pd.DataFrame(chemicals_data)
            st.dataframe(chemicals_df, use_container_width=True)
        else:
            st.info("No chemicals loaded.")

    # Search execution
    st.subheader("Execute Search")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🚀 Start Search", type="primary", use_container_width=True):
            st.session_state.current_batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Get search parameters
            date_range_years = st.session_state.get("date_range", 10)
            max_results = st.session_state.get("max_results", 100)
            include_reviews = st.session_state.get("include_reviews", True)
            api_key = config.pubmed_api_key

            # Enhanced loading states
            with st.spinner("Initializing search..."):
                time.sleep(1)

            # Create progress with cancel functionality
            progress_bar, status_text, cancel_button, progress_container = (
                create_progress_with_cancel("Searching chemicals")
            )

            # Get all chemicals to search
            chemicals_to_search = st.session_state.chemicals

            # Progress callback function
            async def progress_callback(progress: float, chemical: Chemical) -> None:
                if not cancel_button:
                    progress_bar.progress(progress)
                    status_text.text(f"🔍 Searching PubMed for: {chemical.name}")

            try:
                # Run the async batch search
                search_results = asyncio.run(
                    batch_search(
                        chemicals=chemicals_to_search,
                        max_results_per_chemical=max_results,
                        date_range_years=date_range_years,
                        include_reviews=include_reviews,
                        api_key=api_key,
                        progress_callback=progress_callback,
                    )
                )

                progress_bar.progress(1.0)
                status_text.text("✅ Search complete!")
                time.sleep(0.5)
                progress_container.empty()

                # Store results in session state
                st.session_state.search_results = search_results

                # Save session for persistence and history
                try:
                    session_manager = SessionManager()

                    # Create search parameters object
                    search_params = SearchParameters(
                        date_range_years=date_range_years,
                        max_results=max_results,
                        include_reviews=include_reviews,
                    )

                    # Create BatchSearchSession object
                    session = BatchSearchSession(
                        batch_id=st.session_state.current_batch_id,
                        chemicals=chemicals_to_search,
                        parameters=search_params,
                        results={
                            result.chemical.name: result for result in search_results
                        },
                        status="completed",
                    )

                    # Save session
                    session_filepath = session_manager.save_session(session)
                    st.session_state.current_session = session
                    logger.info(f"Session saved to {session_filepath}")

                except Exception as e:
                    logger.error(f"Failed to save session: {e}")
                    # Don't fail the search if session saving fails

                # Calculate real stats
                total_papers = sum(
                    len(result.publications) for result in search_results
                )
                stats = {
                    "Chemicals Searched": len(chemicals_to_search),
                    "Papers Found": total_papers,
                    "API Calls": len(
                        [result for result in search_results if not result.from_cache]
                    ),
                }
                show_success_with_stats(
                    f"Batch search completed! Batch ID: {st.session_state.current_batch_id}",
                    stats,
                )

                # Navigate to results page
                if st.button("📊 View Results", type="primary"):
                    try:
                        st.switch_page("pages/3_📊_Results.py")
                    except AttributeError:
                        st.info(
                            "💡 Navigate to the **Results** page to view your search results."
                        )

            except Exception as e:
                progress_container.empty()

                # Determine specific error type for better user guidance
                error_message = str(e).lower()
                if "rate limit" in error_message or "429" in error_message:
                    show_error_with_help(
                        "rate_limit_exceeded",
                        f"PubMed rate limit reached: {str(e)}",
                        expand_help=True,
                    )
                elif "network" in error_message or "connection" in error_message:
                    show_error_with_help(
                        "network_error", f"Network connectivity issue: {str(e)}"
                    )
                elif "api_key" in error_message or "unauthorized" in error_message:
                    show_error_with_help(
                        "api_key_required",
                        f"API authentication issue: {str(e)}",
                        expand_help=True,
                    )
                else:
                    show_error_with_help(
                        "search_failed", f"Search operation failed: {str(e)}"
                    )

                log_error_for_support(e, "batch search")

    with col2:
        if st.button("⏸️ Pause Search", use_container_width=True):
            st.warning("Search paused.")

    with col3:
        if st.button("❌ Cancel Search", use_container_width=True):
            st.error("Search cancelled.")


# Main execution
if __name__ == "__main__":
    show_search_page()
else:
    show_search_page()
