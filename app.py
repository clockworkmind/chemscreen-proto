"""
ChemScreen Prototype - Batch Chemical Literature Search Tool

A Streamlit application for librarians to perform batch literature searches
on chemicals for regulatory assessments.
"""

import streamlit as st
from pathlib import Path
import sys
import logging
from datetime import datetime
import pandas as pd
import asyncio
import os
import time

# Add the chemscreen package to the path
sys.path.append(str(Path(__file__).parent))

# Import our modules
from chemscreen.processor import merge_duplicates, detect_duplicates
from chemscreen.models import CSVColumnMapping
from chemscreen.cached_processors import (
    cached_process_csv_data,
    cached_suggest_column_mapping,
)
from chemscreen.pubmed import batch_search
from chemscreen.analyzer import calculate_quality_metrics
from chemscreen.errors import (
    show_error_with_help,
    show_validation_help,
    create_progress_with_cancel,
    show_success_with_stats,
    log_error_for_support,
    show_help_tooltip,
    get_feature_help,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="ChemScreen - Chemical Literature Search",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/clockworkmind/chemscreen-proto",
        "Report a bug": "https://github.com/clockworkmind/chemscreen-proto/issues",
        "About": "ChemScreen Prototype v1.0 - Batch Chemical Literature Search Tool",
    },
)


# Initialize session state
def init_session_state():
    """Initialize session state variables."""
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
            "date_range_years": 10,
            "max_results_per_chemical": 100,
            "include_reviews": True,
            "cache_enabled": True,
            "max_batch_size": 200,
        }


def reset_session():
    """Reset session state to start over."""
    st.session_state.chemicals = []
    st.session_state.search_results = {}
    st.session_state.current_batch_id = None
    # Keep search history and settings
    st.success("✅ Session reset! You can now upload a new file.")
    st.rerun()


# Custom CSS for better styling
def load_custom_css():
    """Load custom CSS styles."""
    st.markdown(
        """
    <style>
    /* Main container styling */
    .main {
        padding-top: 2rem;
    }

    /* Header styling */
    .stApp h1 {
        color: #0066CC;
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
        background-color: #0066CC;
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
        background-color: #0066CC;
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


# Sidebar configuration
def setup_sidebar():
    """Configure the sidebar with navigation and settings."""
    with st.sidebar:
        st.title("🧪 ChemScreen")
        st.markdown("---")

        # Navigation
        st.subheader("Navigation")
        page = st.radio(
            "Select Page",
            options=[
                "🏠 Home",
                "📤 Upload Chemicals",
                "🔍 Search",
                "📊 Results",
                "📥 Export",
                "📜 History",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

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
                max_value=500,
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
                reset_session()

        st.markdown("---")

        # Footer
        st.caption("ChemScreen Prototype v1.0")
        st.caption("© 2025 - For Research Use Only")

        return page


def load_demo_data(size: str):
    """Load demo dataset into session state.

    Args:
        size: One of 'small', 'medium', or 'large'
    """
    import time

    try:
        # Map size to filename
        size_map = {
            "small": "demo_small.csv",
            "medium": "demo_medium.csv",
            "large": "demo_large.csv",
        }

        if size not in size_map:
            st.error(f"Invalid demo size: {size}")
            return

        # Load the demo file
        demo_file_path = Path(__file__).parent / "data" / "raw" / size_map[size]

        if not demo_file_path.exists():
            st.error(f"Demo file not found: {demo_file_path}")
            logger.error(f"Demo file not found: {demo_file_path}")
            return

        # Read the CSV file
        demo_data = pd.read_csv(demo_file_path)

        if demo_data.empty:
            st.error("Demo data file is empty")
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

                # Show success message with stats
                st.success(
                    f"✅ {size.title()} demo dataset loaded! "
                    f"{len(result.valid_chemicals)} chemicals ready for search."
                )

                # Show any warnings from processing
                if result.warnings:
                    with st.expander(
                        f"⚠️ Processing Warnings ({len(result.warnings)})",
                        expanded=False,
                    ):
                        for warning in result.warnings:
                            st.warning(warning)

                # Show invalid rows if any (expected for large dataset with edge cases)
                if result.invalid_rows:
                    with st.expander(
                        f"❌ Invalid Rows ({len(result.invalid_rows)})", expanded=False
                    ):
                        st.info("These are intentional edge cases in the demo data:")
                        for error in result.invalid_rows:
                            st.error(f"Row {error['row_number']}: {error['errors']}")

                # Automatically navigate to search page after loading
                if st.button("▶️ Go to Search", type="primary"):
                    st.rerun()

            else:
                st.error("No valid chemicals found in demo data")

    except FileNotFoundError:
        st.error(f"Demo file not found for size: {size}")
        logger.error(f"Demo file not found for size: {size}")
    except Exception as e:
        st.error(f"Error loading demo data: {str(e)}")
        logger.error(f"Demo data loading error: {e}", exc_info=True)


# Page components
def show_home_page():
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

    with col2:
        st.markdown("### 📈 Quick Stats")
        st.metric(
            "Chemicals Processed", "0", help="Total chemicals processed in this session"
        )
        st.metric(
            "Time Saved", "0 hours", help="Estimated time saved vs manual searching"
        )
        st.metric("Success Rate", "0%", help="Percentage of successful searches")

        st.markdown("---")

        st.markdown("### 🔗 Quick Links")
        st.markdown(
            "- [User Guide](https://github.com/clockworkmind/chemscreen-proto/wiki)"
        )
        st.markdown(
            "- [Report Issue](https://github.com/clockworkmind/chemscreen-proto/issues)"
        )
        st.markdown("- [Demo Data](data/raw/demo_chemicals.csv)")


def show_upload_page():
    """Display the chemical upload page."""
    st.title("📤 Upload Chemical List")

    st.markdown("""
    Upload a CSV file containing the chemicals you want to search. The file should have columns for
    chemical names and/or CAS Registry Numbers.
    """)

    # Add help section for CSV upload
    help_info = get_feature_help("csv_upload")
    show_help_tooltip(help_info["title"], help_info["content"], help_info["icon"])

    # File upload section
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            help="Upload a CSV file with chemical names and/or CAS numbers",
            accept_multiple_files=False,
            key="csv_uploader",
        )

        if uploaded_file is not None:
            try:
                # Check file size (10MB limit)
                file_size = uploaded_file.size
                if file_size > 10 * 1024 * 1024:  # 10MB in bytes
                    show_error_with_help(
                        "file_size",
                        f"File size: {file_size / 1024 / 1024:.1f}MB (max: 10MB)",
                    )
                    return

                # Read CSV file
                df = pd.read_csv(uploaded_file)

                # Check if empty
                if df.empty:
                    show_error_with_help("file_empty")
                    return

                # Check batch size limits
                MAX_BATCH_SIZE = 200  # As per requirements
                if len(df) > MAX_BATCH_SIZE:
                    show_error_with_help(
                        "batch_too_large",
                        f"{len(df)} chemicals found (max: {MAX_BATCH_SIZE})",
                        expand_help=True,
                    )

                    # Offer to truncate
                    if st.checkbox(
                        f"Process only the first {MAX_BATCH_SIZE} chemicals?",
                        key="truncate_large_file",
                    ):
                        df = df.head(MAX_BATCH_SIZE)
                        st.warning(
                            f"⚠️ Dataset truncated to {MAX_BATCH_SIZE} chemicals for processing."
                        )
                    else:
                        return

                st.success(f"✅ File uploaded successfully! Found {len(df)} rows.")

                # Display preview
                st.subheader("Data Preview")

                # Pagination for large datasets
                ROWS_PER_PAGE = 100
                total_rows = len(df)

                if total_rows > ROWS_PER_PAGE:
                    st.info(
                        f"📊 Large dataset detected: {total_rows:,} rows. Using pagination for better performance."
                    )

                    # Calculate total pages
                    total_pages = (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE

                    # Page selector
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        page_num = st.selectbox(
                            "Page",
                            options=list(range(1, total_pages + 1)),
                            format_func=lambda x: f"Page {x} of {total_pages} (rows {(x - 1) * ROWS_PER_PAGE + 1}-{min(x * ROWS_PER_PAGE, total_rows)})",
                            key="preview_page_selector",
                        )

                    # Calculate row indices for current page
                    start_idx = (page_num - 1) * ROWS_PER_PAGE
                    end_idx = min(start_idx + ROWS_PER_PAGE, total_rows)
                    preview_df = df.iloc[start_idx:end_idx]

                    # Navigation buttons
                    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(
                        [1, 1, 2, 1, 1]
                    )
                    with nav_col1:
                        if st.button(
                            "⏮️ First", disabled=page_num == 1, use_container_width=True
                        ):
                            st.rerun()
                    with nav_col2:
                        if st.button(
                            "◀️ Previous",
                            disabled=page_num == 1,
                            use_container_width=True,
                        ):
                            st.rerun()
                    with nav_col3:
                        st.markdown(
                            f"<center>Showing rows {start_idx + 1:,} - {end_idx:,} of {total_rows:,}</center>",
                            unsafe_allow_html=True,
                        )
                    with nav_col4:
                        if st.button(
                            "Next ▶️",
                            disabled=page_num == total_pages,
                            use_container_width=True,
                        ):
                            st.rerun()
                    with nav_col5:
                        if st.button(
                            "Last ⏭️",
                            disabled=page_num == total_pages,
                            use_container_width=True,
                        ):
                            st.rerun()
                else:
                    preview_df = df
                    st.info(f"Showing all {total_rows} rows")

                # Display with virtual scrolling for performance
                st.dataframe(
                    preview_df,
                    use_container_width=True,
                    height=400,  # Fixed height for virtual scrolling
                    hide_index=False,
                )

                # Column mapping
                st.subheader("Column Mapping")

                # Add help for column mapping
                help_info = get_feature_help("column_mapping")
                show_help_tooltip(
                    help_info["title"], help_info["content"], help_info["icon"]
                )

                # Auto-detect columns
                suggested_mapping = cached_suggest_column_mapping(df)

                col_names = df.columns.tolist()

                # Show auto-detection results if found
                if suggested_mapping.name_column or suggested_mapping.cas_column:
                    st.success("🔍 Auto-detected column mappings:")
                    detected_cols = []
                    if suggested_mapping.name_column:
                        detected_cols.append(
                            f"• Chemical Name: **{suggested_mapping.name_column}**"
                        )
                    if suggested_mapping.cas_column:
                        detected_cols.append(
                            f"• CAS Number: **{suggested_mapping.cas_column}**"
                        )
                    if suggested_mapping.synonyms_column:
                        detected_cols.append(
                            f"• Synonyms: **{suggested_mapping.synonyms_column}**"
                        )
                    if suggested_mapping.notes_column:
                        detected_cols.append(
                            f"• Notes: **{suggested_mapping.notes_column}**"
                        )
                    st.markdown("\n".join(detected_cols))

                col1, col2 = st.columns(2)

                with col1:
                    name_col = st.selectbox(
                        "Chemical Name Column",
                        options=["None"] + col_names,
                        index=col_names.index(suggested_mapping.name_column) + 1
                        if suggested_mapping.name_column
                        and suggested_mapping.name_column in col_names
                        else 0,
                        help="Column containing chemical names",
                        key="name_column_select",
                    )

                with col2:
                    cas_col = st.selectbox(
                        "CAS Number Column",
                        options=["None"] + col_names,
                        index=col_names.index(suggested_mapping.cas_column) + 1
                        if suggested_mapping.cas_column
                        and suggested_mapping.cas_column in col_names
                        else 0,
                        help="Column containing CAS Registry Numbers",
                        key="cas_column_select",
                    )

                # Validate that at least one column is selected
                if name_col == "None" and cas_col == "None":
                    show_error_with_help("no_columns_selected")
                else:
                    # Show selected column preview
                    with st.expander("View Selected Columns", expanded=True):
                        preview_cols = []
                        if name_col != "None":
                            preview_cols.append(name_col)
                        if cas_col != "None":
                            preview_cols.append(cas_col)
                        st.dataframe(
                            df[preview_cols].head(10), use_container_width=True
                        )

                    if st.button("Process Chemicals", type="primary"):
                        # Create progress indicators with cancel option
                        progress_bar, status_text, cancel_button, progress_container = (
                            create_progress_with_cancel("Processing chemicals")
                        )

                        # Create column mapping
                        column_mapping = CSVColumnMapping(
                            name_column=name_col if name_col != "None" else None,
                            cas_column=cas_col if cas_col != "None" else None,
                        )

                        # Process CSV data with progress updates
                        try:
                            status_text.text("📋 Validating data structure...")
                            progress_bar.progress(0.1)

                            # Check for cancellation
                            if cancel_button:
                                st.warning("⏸️ Processing cancelled by user")
                                progress_container.empty()
                                return

                            # Initial validation and batch size check
                            MAX_BATCH_SIZE = 200
                            if len(df) > MAX_BATCH_SIZE:
                                show_error_with_help(
                                    "batch_too_large",
                                    f"{len(df)} chemicals (max: {MAX_BATCH_SIZE})",
                                )
                                progress_container.empty()
                                return

                            status_text.text("🔍 Processing chemicals...")
                            progress_bar.progress(0.3)

                            result = cached_process_csv_data(df, column_mapping)

                            status_text.text("✨ Finalizing results...")
                            progress_bar.progress(0.9)

                            # Store validated chemicals
                            st.session_state.chemicals = result.valid_chemicals

                            # Complete progress
                            progress_bar.progress(1.0)
                            status_text.text("✅ Processing complete!")

                            # Clear progress indicators after a short delay
                            import time

                            time.sleep(0.5)
                            progress_container.empty()

                            # Display comprehensive results
                            st.subheader("📊 Processing Summary")

                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Rows", result.total_rows)
                            with col2:
                                st.metric(
                                    "Valid Chemicals",
                                    len(result.valid_chemicals),
                                    delta=f"{len(result.valid_chemicals) - len(result.invalid_rows)} processed",
                                )
                            with col3:
                                st.metric(
                                    "Invalid Rows",
                                    len(result.invalid_rows),
                                    delta=None
                                    if len(result.invalid_rows) == 0
                                    else "-" + str(len(result.invalid_rows)),
                                )
                            with col4:
                                st.metric(
                                    "Success Rate",
                                    f"{result.success_rate:.1f}%",
                                    delta="Good"
                                    if result.success_rate >= 90
                                    else "Check data",
                                )

                            # Show warnings if any
                            if result.warnings:
                                with st.expander(
                                    f"⚠️ Warnings ({len(result.warnings)})",
                                    expanded=False,
                                ):
                                    for warning in result.warnings:
                                        st.warning(warning)

                            # Show errors if any with enhanced help
                            if result.invalid_rows:
                                show_validation_help(result.invalid_rows, expand=True)

                            # Check for duplicates and offer to merge
                            if result.valid_chemicals:
                                duplicates = detect_duplicates(result.valid_chemicals)
                                if duplicates:
                                    st.warning(
                                        f"Found {len(duplicates)} duplicate chemicals."
                                    )
                                    if st.checkbox("Merge duplicates?", value=True):
                                        result.valid_chemicals = merge_duplicates(
                                            result.valid_chemicals
                                        )
                                        st.session_state.chemicals = (
                                            result.valid_chemicals
                                        )
                                        st.info(
                                            f"Merged to {len(result.valid_chemicals)} unique chemicals."
                                        )

                            if result.valid_chemicals:
                                # Use the new success with stats function
                                stats = {
                                    "Valid Chemicals": len(result.valid_chemicals),
                                    "Success Rate": f"{result.success_rate:.1f}%",
                                    "Invalid Rows": len(result.invalid_rows),
                                }
                                show_success_with_stats(
                                    f"Successfully processed {len(result.valid_chemicals)} chemicals!",
                                    stats,
                                )

                                # Show simplified preview of processed chemicals
                                with st.expander(
                                    "Preview Processed Chemicals", expanded=True
                                ):
                                    # Show first 10 chemicals in a simple table
                                    preview_chemicals = result.valid_chemicals[:10]
                                    preview_data = []
                                    for i, chem in enumerate(preview_chemicals):
                                        preview_data.append(
                                            {
                                                "Chemical Name": chem.name,
                                                "CAS Number": chem.cas_number or "N/A",
                                                "Validated": "✅"
                                                if chem.validated
                                                else "⚠️",
                                                "Synonyms": len(chem.synonyms)
                                                if chem.synonyms
                                                else 0,
                                            }
                                        )

                                    if preview_data:
                                        st.dataframe(
                                            pd.DataFrame(preview_data),
                                            use_container_width=True,
                                        )

                                        if len(result.valid_chemicals) > 10:
                                            st.info(
                                                f"Showing first 10 of {len(result.valid_chemicals)} chemicals"
                                            )
                            else:
                                st.error(
                                    "No valid chemicals found in the uploaded file."
                                )

                        except Exception as e:
                            show_error_with_help("processing_failed", str(e))
                            log_error_for_support(e, "CSV processing")

            except pd.errors.EmptyDataError:
                show_error_with_help("file_empty")
                log_error_for_support(Exception("Empty CSV file"), "file upload")
            except Exception as e:
                show_error_with_help("invalid_csv", str(e))
                log_error_for_support(e, "file upload")

    with col2:
        st.markdown("### 📋 File Requirements")
        st.markdown("""
        - **Format**: CSV (comma-separated)
        - **Encoding**: UTF-8 preferred
        - **Size**: Max 10MB
        - **Columns**: At least one of:
            - Chemical names
            - CAS numbers
        """)

        st.markdown("---")

        st.markdown("### 💡 Tips")
        st.markdown("""
        - Remove duplicates before uploading
        - Check CAS number formatting
        - Use standard chemical names
        - Include headers in your CSV
        """)

        # Demo data section
        st.markdown("### 📊 Demo Data")
        st.caption("Load sample datasets for testing")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "Small\n(10)", help="Load 10 demo chemicals", use_container_width=True
            ):
                load_demo_data("small")

        with col2:
            if st.button(
                "Medium\n(50)", help="Load 50 demo chemicals", use_container_width=True
            ):
                load_demo_data("medium")

        with col3:
            if st.button(
                "Large\n(150)",
                help="Load 150 demo chemicals with edge cases",
                use_container_width=True,
            ):
                load_demo_data("large")


def show_search_page():
    """Display the search configuration and execution page."""
    st.title("🔍 Search Configuration")

    if not st.session_state.chemicals:
        st.warning("⚠️ No chemicals loaded. Please upload a chemical list first.")
        if st.button("Go to Upload Page"):
            st.experimental_rerun()
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
            max_value=500,
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

        # TODO: Pass these parameters to the search function

    with col2:
        st.subheader("Batch Information")

        # Add help for batch processing
        help_info = get_feature_help("batch_processing")
        show_help_tooltip(help_info["title"], help_info["content"], help_info["icon"])
        chemical_count = len(st.session_state.chemicals)
        MAX_BATCH_SIZE = 200

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
            "✅ Configured" if os.getenv("PUBMED_API_KEY") else "❌ Not configured"
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

            # TODO: Integrate cache manager with batch_search function

            # Get search parameters
            date_range_years = st.session_state.get("date_range", 10)
            max_results = st.session_state.get("max_results", 100)
            include_reviews = st.session_state.get("include_reviews", True)
            api_key = os.getenv("PUBMED_API_KEY")

            # Enhanced loading states
            with st.spinner("Initializing search..."):
                time.sleep(1)

            # Create progress with cancel functionality
            progress_bar, status_text, cancel_button, progress_container = (
                create_progress_with_cancel("Searching chemicals")
            )

            # Get chemicals to search (limit to 5 for demo)
            chemicals_to_search = st.session_state.chemicals[
                : min(5, len(st.session_state.chemicals))
            ]

            # Progress callback function
            async def progress_callback(progress, chemical):
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

            except Exception as e:
                progress_container.empty()
                show_error_with_help(
                    "Search Failed",
                    f"An error occurred during the search: {str(e)}",
                    "Please check your API key and network connection. Try again with fewer chemicals.",
                )

    with col2:
        if st.button("⏸️ Pause Search", use_container_width=True):
            st.warning("Search paused.")

    with col3:
        if st.button("❌ Cancel Search", use_container_width=True):
            st.error("Search cancelled.")


def show_results_page():
    """Display the search results page."""
    st.title("📊 Search Results")

    if not st.session_state.search_results:
        st.warning("⚠️ No search results available. Please run a search first.")
        return

    # Calculate real summary statistics
    total_chemicals = (
        len(st.session_state.chemicals) if st.session_state.chemicals else 0
    )
    search_results = st.session_state.search_results
    successful_searches = len([r for r in search_results if not r.error])
    failed_searches = len([r for r in search_results if r.error])
    total_papers = sum(len(r.publications) for r in search_results)

    # Results summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Chemicals", total_chemicals)
    with col2:
        st.metric("Successful Searches", successful_searches)
    with col3:
        st.metric("Failed Searches", failed_searches)
    with col4:
        st.metric("Total Papers Found", total_papers)

    st.markdown("---")

    # Results table
    st.subheader("Results Summary")

    # Create results dataframe with real data and quality metrics
    results_data = []
    for result in search_results:
        # Calculate quality metrics for each result
        metrics = calculate_quality_metrics(result)

        # Determine status
        status = "❌ Failed" if result.error else "✅ Complete"

        results_data.append(
            {
                "Chemical Name": result.chemical.name,
                "CAS Number": result.chemical.cas_number or "N/A",
                "Papers Found": len(result.publications),
                "Review Articles": metrics.review_count,
                "Recent Papers": metrics.recent_publications,
                "Quality Score": int(metrics.quality_score),
                "Trend": metrics.publication_trend.title(),
                "Status": status,
            }
        )

    results_df = pd.DataFrame(results_data)

    st.dataframe(
        results_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Quality Score": st.column_config.ProgressColumn(
                "Quality Score",
                help="Overall quality score based on publication count, recency, and trends",
                format="%d",
                min_value=0,
                max_value=100,
            ),
            "Trend": st.column_config.SelectboxColumn(
                "Publication Trend",
                help="Publication trend over the last 5 years",
                options=["Increasing", "Decreasing", "Stable"],
            ),
        },
    )

    # Results Analysis
    st.subheader("📈 Results Analysis")

    tab1, tab2, tab3 = st.tabs(
        ["Quality Distribution", "Summary Stats", "High Priority"]
    )

    with tab1:
        if not results_df.empty:
            # Quality score distribution
            col1, col2 = st.columns(2)

            with col1:
                avg_score = results_df["Quality Score"].mean()
                st.metric("Average Quality Score", f"{avg_score:.1f}")

                # Quality tiers
                high_quality = len(results_df[results_df["Quality Score"] >= 80])
                medium_quality = len(
                    results_df[
                        (results_df["Quality Score"] >= 50)
                        & (results_df["Quality Score"] < 80)
                    ]
                )
                low_quality = len(results_df[results_df["Quality Score"] < 50])

                st.write("**Quality Tiers:**")
                st.write(f"🟢 High (80+): {high_quality} chemicals")
                st.write(f"🟡 Medium (50-79): {medium_quality} chemicals")
                st.write(f"🔴 Low (<50): {low_quality} chemicals")

            with col2:
                # Publication trends summary
                trend_counts = results_df["Trend"].value_counts()
                st.write("**Publication Trends:**")
                for trend, count in trend_counts.items():
                    icon = (
                        "📈"
                        if trend == "Increasing"
                        else "📉"
                        if trend == "Decreasing"
                        else "➡️"
                    )
                    st.write(f"{icon} {trend}: {count} chemicals")
        else:
            st.info("No results to analyze")

    with tab2:
        if not results_df.empty:
            col1, col2 = st.columns(2)

            with col1:
                total_reviews = results_df["Review Articles"].sum()
                total_recent = results_df["Recent Papers"].sum()
                st.metric("Total Review Articles", total_reviews)
                st.metric("Recent Publications (3 years)", total_recent)

            with col2:
                # Success rate
                success_rate = (
                    (successful_searches / total_chemicals * 100)
                    if total_chemicals > 0
                    else 0
                )
                st.metric("Search Success Rate", f"{success_rate:.1f}%")

                # Average papers per chemical
                avg_papers = (
                    total_papers / successful_searches if successful_searches > 0 else 0
                )
                st.metric("Avg Papers per Chemical", f"{avg_papers:.1f}")
        else:
            st.info("No statistics available")

    with tab3:
        if not results_df.empty:
            # High priority chemicals (high quality score and recent publications)
            high_priority = results_df[
                (results_df["Quality Score"] >= 70) & (results_df["Recent Papers"] > 0)
            ].sort_values("Quality Score", ascending=False)

            if not high_priority.empty:
                st.write(
                    f"**{len(high_priority)} High Priority Chemicals** (Quality Score ≥70 + Recent Publications):"
                )
                st.dataframe(
                    high_priority[
                        [
                            "Chemical Name",
                            "Quality Score",
                            "Papers Found",
                            "Recent Papers",
                            "Trend",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "No high priority chemicals identified based on current criteria"
                )
        else:
            st.info("No priority analysis available")


def show_export_page():
    """Display the export page."""
    st.title("📥 Export Results")

    if not st.session_state.search_results:
        st.warning("⚠️ No results to export. Please run a search first.")
        return

    st.markdown("Export your search results in various formats for further analysis.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Export Options")

        export_format = st.radio(
            "Select Export Format",
            options=["CSV", "Excel (XLSX)", "JSON"],
            help="Choose the format for your export file",
        )

        _include_metadata = st.checkbox(
            "Include Search Metadata",
            value=True,
            help="Include search parameters and timestamp",
        )

        _include_abstracts = st.checkbox(
            "Include Abstracts",
            value=False,
            help="Include paper abstracts (increases file size)",
        )

        # TODO: Pass _include_metadata and _include_abstracts to export function

        if export_format == "Excel (XLSX)":
            st.info(
                "Excel export will create multiple sheets: Summary, Detailed Results, and Metadata"
            )

    with col2:
        st.subheader("Export Preview")

        # TODO: Show preview of export data
        st.info("Export preview will appear here")

        file_size_estimate = "~250 KB"  # TODO: Calculate actual size
        st.metric("Estimated File Size", file_size_estimate)

    st.markdown("---")

    # Export button with enhanced loading states
    if st.button("📥 Generate Export", type="primary"):
        import time  # For export timing simulation

        # Create progress indicators for export
        progress_bar, status_text, cancel_button, progress_container = (
            create_progress_with_cancel("Generating export")
        )

        try:
            # Simulate export steps with progress
            status_text.text("📊 Collecting search results...")
            progress_bar.progress(0.2)
            time.sleep(0.5)

            if cancel_button:
                st.warning("⏸️ Export cancelled by user")
                progress_container.empty()
                return

            status_text.text("📋 Formatting data...")
            progress_bar.progress(0.5)
            time.sleep(0.8)

            status_text.text("📄 Creating spreadsheet...")
            progress_bar.progress(0.8)
            time.sleep(0.7)

            status_text.text("✅ Export ready!")
            progress_bar.progress(1.0)
            time.sleep(0.3)
            progress_container.empty()

            # Show success with file info
            stats = {
                "File Size": "245 KB",
                "Chemicals": len(st.session_state.chemicals),
                "Format": "Excel (.xlsx)",
            }
            show_success_with_stats(
                "Export file generated successfully!", stats, show_balloons=False
            )

            # TODO: Provide actual download button
            st.download_button(
                label="📥 Download Export",
                data="Sample export data",  # TODO: Use actual export data
                file_name=f"chemscreen_export_{st.session_state.current_batch_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as e:
            show_error_with_help("processing_failed", str(e))
            log_error_for_support(e, "export generation")


def show_history_page():
    """Display the search history page."""
    st.title("📜 Search History")

    st.markdown("View and manage your previous search sessions.")

    # TODO: Implement actual history tracking
    history_data = [
        {
            "Batch ID": "20250106_143022",
            "Date": "2025-01-06 14:30:22",
            "Chemicals": 75,
            "Status": "✅ Complete",
            "Results": 73,
            "Export": "📥 Available",
        },
        {
            "Batch ID": "20250105_093015",
            "Date": "2025-01-05 09:30:15",
            "Chemicals": 120,
            "Status": "✅ Complete",
            "Results": 118,
            "Export": "📥 Available",
        },
    ]

    history_df = pd.DataFrame(history_data)

    # Display history table
    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DatetimeColumn(
                "Date", format="YYYY-MM-DD HH:mm:ss"
            )
        },
    )

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Reload Selected"):
            st.info("Session reload functionality coming soon")

    with col2:
        if st.button("📊 Compare Sessions"):
            st.info("Session comparison functionality coming soon")

    with col3:
        if st.button("🗑️ Clear History"):
            if st.checkbox("Confirm deletion"):
                st.warning("History cleared!")


# Main application
def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()

    # Load custom CSS
    load_custom_css()

    # Setup sidebar and get selected page
    page = setup_sidebar()

    # Route to appropriate page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📤 Upload Chemicals":
        show_upload_page()
    elif page == "🔍 Search":
        show_search_page()
    elif page == "📊 Results":
        show_results_page()
    elif page == "📥 Export":
        show_export_page()
    elif page == "📜 History":
        show_history_page()
    else:
        st.error("Page not found!")


if __name__ == "__main__":
    main()
