"""
ChemScreen Prototype - Batch Chemical Literature Search Tool

A Streamlit multipage application for librarians to perform batch literature searches
on chemicals for regulatory assessments.

This is the main/home page of the application.
"""

import streamlit as st
from pathlib import Path
import sys
import logging

# Add the chemscreen package to the path
sys.path.append(str(Path(__file__).parent))

# Import and initialize configuration
from chemscreen.config import initialize_config

# Import shared utilities
from shared.ui_utils import load_custom_css, setup_sidebar
from shared.app_utils import init_session_state

# Initialize configuration system
config = initialize_config()

# Configure logging using config
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create required directories
config.create_directories()

# Log configuration warnings if any
config_warnings = config.validate_configuration()
if config_warnings:
    for warning in config_warnings:
        logger.warning(f"Configuration: {warning}")

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title=config.page_title,
    page_icon=config.page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/clockworkmind/chemscreen-proto",
        "Report a bug": "https://github.com/clockworkmind/chemscreen-proto/issues",
        "About": "ChemScreen Prototype v1.0 - Batch Chemical Literature Search Tool",
    },
)

# Initialize session state and UI
init_session_state()
load_custom_css()

setup_sidebar()


def show_home_page() -> None:
    """Display the home/welcome page."""
    st.title("🧪 ChemScreen - Chemical Literature Search Tool")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### Welcome to ChemScreen

        ChemScreen is a specialized tool designed for librarians supporting regulatory chemical risk assessments.
        It enables batch processing of chemical literature searches, reducing screening time from days to hours.

        #### 🎯 Key Features:
        - **Batch Processing**: Search 100+ chemicals simultaneously
        - **Quality Scoring**: Automated literature quality assessment
        - **Smart Caching**: Avoid redundant API calls
        - **Export Options**: CSV and Excel formats
        - **Progress Tracking**: Real-time search status

        #### 🚀 Getting Started:
        1. **Upload** your chemical list (CSV format)
        2. **Configure** search parameters
        3. **Run** the batch search
        4. **Export** results for analysis

        #### 📊 Typical Workflow:
        - Upload a CSV with chemical names or CAS numbers
        - Review and validate the chemical list
        - Start the batch search process
        - Monitor progress in real-time
        - Export comprehensive results
        """)

        st.info(
            "💡 **Tip**: Start with the demo dataset to familiarize yourself with the tool's capabilities."
        )

        # Quick start buttons
        st.markdown("### 🚀 Quick Start")

        col1a, col1b, col1c = st.columns(3)

        with col1a:
            if st.button(
                "📤 Upload Chemicals", type="primary", use_container_width=True
            ):
                try:
                    st.switch_page("pages/1_📤_Upload_Chemicals.py")
                except AttributeError:
                    st.info(
                        "💡 Navigate to the **Upload Chemicals** page using the sidebar."
                    )

        with col1b:
            if st.button("📊 Load Demo Data", use_container_width=True):
                from shared.app_utils import load_demo_data

                load_demo_data("medium")

        with col1c:
            if st.button("📜 View History", use_container_width=True):
                try:
                    st.switch_page("pages/5_📜_History.py")
                except AttributeError:
                    st.info("💡 Navigate to the **History** page using the sidebar.")

    with col2:
        st.markdown("### 📈 Session Stats")

        # Calculate real-time stats
        chemicals_count = (
            len(st.session_state.chemicals) if st.session_state.chemicals else 0
        )
        results_count = (
            len(st.session_state.search_results)
            if st.session_state.search_results
            else 0
        )

        # Estimate time saved (rough calculation: 2-3 minutes per chemical manually vs seconds with tool)
        time_saved_hours = chemicals_count * 2.5 / 60 if chemicals_count > 0 else 0

        # Success rate calculation
        if st.session_state.search_results:
            successful_searches = len(
                [r for r in st.session_state.search_results if not r.error]
            )
            success_rate = (
                successful_searches / len(st.session_state.search_results)
            ) * 100
        else:
            success_rate = 0

        st.metric(
            "Chemicals Loaded",
            chemicals_count,
            help="Total chemicals loaded in current session",
        )
        st.metric(
            "Search Results",
            results_count,
            help="Number of completed searches in current session",
        )
        st.metric(
            "Estimated Time Saved",
            f"{time_saved_hours:.1f} hours",
            help="Estimated time saved vs manual searching",
        )
        st.metric(
            "Success Rate",
            f"{success_rate:.0f}%",
            help="Percentage of successful searches",
        )

        st.markdown("---")

        st.markdown("### 🔗 Quick Links")
        st.markdown(
            "- [User Guide](https://github.com/clockworkmind/chemscreen-proto/wiki)"
        )
        st.markdown(
            "- [Report Issue](https://github.com/clockworkmind/chemscreen-proto/issues)"
        )
        st.markdown("- [Demo Data](data/raw/demo_chemicals.csv)")

        st.markdown("---")

        # Current session info
        st.markdown("### 📋 Current Session")
        if st.session_state.current_batch_id:
            st.success(f"Active Batch: {st.session_state.current_batch_id}")
        else:
            st.info("No active search session")

        # Quick status
        if chemicals_count > 0:
            st.success(f"✅ {chemicals_count} chemicals ready")
        else:
            st.warning("⚠️ No chemicals loaded")

        if results_count > 0:
            st.success(f"📊 {results_count} results available")

    # Feature highlights
    st.markdown("---")
    st.markdown("### ✨ What Makes ChemScreen Special")

    feature_col1, feature_col2, feature_col3 = st.columns(3)

    with feature_col1:
        st.markdown("""
        #### ⚡ Speed & Efficiency
        - Process 100+ chemicals in minutes
        - Parallel API requests with rate limiting
        - Smart caching reduces redundant calls
        - Real-time progress tracking
        """)

    with feature_col2:
        st.markdown("""
        #### 📊 Quality Analysis
        - Automated quality scoring
        - Publication trend analysis
        - Review article identification
        - Recency-based prioritization
        """)

    with feature_col3:
        st.markdown("""
        #### 📤 Export & Integration
        - Multiple export formats (CSV, Excel, JSON)
        - Structured data for analysis
        - Session persistence and history
        - Comprehensive metadata inclusion
        """)


# Main execution
if __name__ == "__main__":
    show_home_page()
else:
    show_home_page()
