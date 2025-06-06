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

# Add the chemscreen package to the path
sys.path.append(str(Path(__file__).parent))

# Import our modules
from chemscreen.processor import process_csv_data, merge_duplicates
from chemscreen.models import CSVColumnMapping

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
        "Get Help": "https://github.com/shanethacker/chemscreen-proto",
        "Report a bug": "https://github.com/shanethacker/chemscreen-proto/issues",
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
        }


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

        # Footer
        st.caption("ChemScreen Prototype v1.0")
        st.caption("© 2025 - For Research Use Only")

        return page


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
            "- [User Guide](https://github.com/shanethacker/chemscreen-proto/wiki)"
        )
        st.markdown(
            "- [Report Issue](https://github.com/shanethacker/chemscreen-proto/issues)"
        )
        st.markdown("- [Demo Data](data/raw/demo_chemicals.csv)")


def show_upload_page():
    """Display the chemical upload page."""
    st.title("📤 Upload Chemical List")

    st.markdown("""
    Upload a CSV file containing the chemicals you want to search. The file should have columns for
    chemical names and/or CAS Registry Numbers.
    """)

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
                    st.error(
                        f"❌ File too large ({file_size / 1024 / 1024:.1f}MB). Maximum size is 10MB."
                    )
                    return

                # Read CSV file
                df = pd.read_csv(uploaded_file)

                # Check if empty
                if df.empty:
                    st.error("❌ The uploaded CSV file is empty.")
                    return

                st.success(f"✅ File uploaded successfully! Found {len(df)} rows.")

                # Display preview
                st.subheader("Data Preview")

                # Check if dataframe is large
                if len(df) > 100:
                    st.info(
                        f"📊 Large dataset detected: {len(df)} rows. Showing first 100 rows in preview."
                    )
                    preview_df = df.head(100)
                else:
                    preview_df = df

                # Display with virtual scrolling for performance
                st.dataframe(
                    preview_df,
                    use_container_width=True,
                    height=400,  # Fixed height for virtual scrolling
                    hide_index=False,
                )

                # Column mapping
                st.subheader("Column Mapping")

                # Auto-detect columns
                from chemscreen.processor import suggest_column_mapping

                suggested_mapping = suggest_column_mapping(df)

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
                    st.warning(
                        "⚠️ Please select at least one column (Chemical Name or CAS Number)"
                    )
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
                        with st.spinner("Processing chemical list..."):
                            # Create column mapping
                            column_mapping = CSVColumnMapping(
                                name_column=name_col if name_col != "None" else None,
                                cas_column=cas_col if cas_col != "None" else None,
                            )

                            # Process CSV data
                            try:
                                result = process_csv_data(df, column_mapping)

                                # Store validated chemicals
                                st.session_state.chemicals = result.valid_chemicals

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

                                # Show errors if any
                                if result.invalid_rows:
                                    with st.expander(
                                        f"❌ Invalid Rows ({len(result.invalid_rows)})",
                                        expanded=True,
                                    ):
                                        for error in result.invalid_rows:
                                            st.error(
                                                f"Row {error['row_number']}: {error['errors']}"
                                            )

                                # Check for duplicates and offer to merge
                                if result.valid_chemicals:
                                    from chemscreen.processor import detect_duplicates

                                    duplicates = detect_duplicates(
                                        result.valid_chemicals
                                    )
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
                                    st.success(
                                        f"✅ Successfully processed {len(result.valid_chemicals)} chemicals!"
                                    )

                                    # Show preview of processed chemicals with duplicate highlighting
                                    with st.expander(
                                        "Preview Processed Chemicals", expanded=True
                                    ):
                                        # Get duplicates for highlighting
                                        from chemscreen.processor import (
                                            detect_duplicates,
                                        )

                                        duplicates_list = detect_duplicates(
                                            result.valid_chemicals
                                        )
                                        duplicate_indices = set()
                                        for dup1, dup2 in duplicates_list:
                                            duplicate_indices.add(dup1)
                                            duplicate_indices.add(dup2)

                                        preview_data = []
                                        for idx, chem in enumerate(
                                            result.valid_chemicals[:50]
                                        ):  # Show up to 50
                                            is_duplicate = idx in duplicate_indices
                                            preview_data.append(
                                                {
                                                    "Index": idx + 1,
                                                    "Name": chem.name,
                                                    "CAS Number": chem.cas_number
                                                    or "N/A",
                                                    "Validated": "✅"
                                                    if chem.validated
                                                    else "⚠️",
                                                    "Duplicate": "🔁"
                                                    if is_duplicate
                                                    else "",
                                                    "Synonyms": ", ".join(
                                                        chem.synonyms[:3]
                                                    )
                                                    + (
                                                        "..."
                                                        if len(chem.synonyms) > 3
                                                        else ""
                                                    )
                                                    if chem.synonyms
                                                    else "N/A",
                                                }
                                            )
                                        preview_df = pd.DataFrame(preview_data)

                                        # Apply custom styling to highlight duplicates
                                        st.dataframe(
                                            preview_df,
                                            use_container_width=True,
                                            height=400,
                                            hide_index=True,
                                            column_config={
                                                "Index": st.column_config.NumberColumn(
                                                    "Index",
                                                    help="Row number in the dataset",
                                                    width="small",
                                                ),
                                                "Duplicate": st.column_config.TextColumn(
                                                    "Dup",
                                                    help="🔁 indicates duplicate entry",
                                                    width="small",
                                                ),
                                                "Validated": st.column_config.TextColumn(
                                                    "Valid",
                                                    help="✅ = Valid CAS, ⚠️ = Invalid/No CAS",
                                                    width="small",
                                                ),
                                            },
                                        )

                                        if len(result.valid_chemicals) > 50:
                                            st.info(
                                                f"Showing first 50 of {len(result.valid_chemicals)} chemicals"
                                            )

                                    st.balloons()
                                else:
                                    st.error(
                                        "No valid chemicals found in the uploaded file."
                                    )

                            except Exception as e:
                                st.error(f"Error processing CSV: {str(e)}")
                                logger.error(
                                    f"CSV processing error: {e}", exc_info=True
                                )

            except pd.errors.EmptyDataError:
                st.error("❌ The uploaded file appears to be empty or invalid.")
                logger.error("Empty CSV file uploaded")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
                logger.error(f"File upload error: {str(e)}")

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

        # Demo data button
        if st.button("Load Demo Data"):
            st.info("Loading demo dataset...")
            try:
                # Create demo data
                demo_data = pd.DataFrame(
                    {
                        "Chemical Name": [
                            "TCE",
                            "Dichloromethane",
                            "Benzene",
                            "Formaldehyde",
                            "Acetone",
                            "Methanol",
                            "Toluene",
                            "Xylene",
                            "Styrene",
                            "Vinyl chloride",
                        ],
                        "CAS Number": [
                            "79-01-6",
                            "75-09-2",
                            "71-43-2",
                            "50-00-0",
                            "67-64-1",
                            "67-56-1",
                            "108-88-3",
                            "1330-20-7",
                            "100-42-5",
                            "75-01-4",
                        ],
                        "Notes": [
                            "Common solvent",
                            "Methylene chloride",
                            "Carcinogenic",
                            "Preservative",
                            "Common solvent",
                            "Wood alcohol",
                            "Paint thinner",
                            "Mixed isomers",
                            "Plastic monomer",
                            "PVC precursor",
                        ],
                    }
                )

                # Process demo data
                column_mapping = CSVColumnMapping(
                    name_column="Chemical Name",
                    cas_column="CAS Number",
                    notes_column="Notes",
                )

                result = process_csv_data(demo_data, column_mapping)
                st.session_state.chemicals = result.valid_chemicals

                st.success(
                    f"Demo data loaded! {len(result.valid_chemicals)} chemicals ready for search."
                )
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Error loading demo data: {str(e)}")
                logger.error(f"Demo data error: {e}", exc_info=True)


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
        st.info(f"**Chemicals to search**: {len(st.session_state.chemicals)}")

        # Estimate time
        estimated_time = (
            len(st.session_state.chemicals) * 0.5
        )  # 0.5 minutes per chemical
        st.info(f"**Estimated time**: {estimated_time:.1f} minutes")

        # API key status
        st.subheader("API Configuration")
        api_key_status = (
            "✅ Configured" if st.secrets.get("PUBMED_API_KEY") else "❌ Not configured"
        )
        st.markdown(f"**PubMed API Key**: {api_key_status}")

        if api_key_status == "❌ Not configured":
            st.warning("Without an API key, searches will be rate-limited.")

    st.markdown("---")

    # Chemical list preview
    with st.expander("View Chemical List", expanded=False):
        st.dataframe(st.session_state.chemicals, use_container_width=True)

    # Search execution
    st.subheader("Execute Search")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🚀 Start Search", type="primary", use_container_width=True):
            st.session_state.current_batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            _results_container = st.container()

            # TODO: Implement actual search logic
            # TODO: Use _results_container for displaying results
            import time

            for i, chemical in enumerate(
                st.session_state.chemicals[:5]
            ):  # Demo with first 5
                progress = (i + 1) / len(st.session_state.chemicals)
                progress_bar.progress(progress)
                status_text.text(
                    f"Searching for chemical {i + 1} of {len(st.session_state.chemicals)}..."
                )
                time.sleep(0.5)  # Simulate API call

            progress_bar.progress(1.0)
            status_text.text("Search complete!")
            st.success(
                f"✅ Batch search completed! Batch ID: {st.session_state.current_batch_id}"
            )
            st.balloons()

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

    # Results summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Chemicals", len(st.session_state.chemicals))
    with col2:
        st.metric("Successful Searches", len(st.session_state.search_results))
    with col3:
        st.metric("Failed Searches", 0)  # TODO: Calculate actual failures
    with col4:
        st.metric("Total Papers Found", 0)  # TODO: Sum all papers

    st.markdown("---")

    # Results table
    st.subheader("Results Summary")

    # TODO: Create actual results dataframe
    results_df = pd.DataFrame(
        {
            "Chemical Name": ["Example Chemical 1", "Example Chemical 2"],
            "CAS Number": ["123-45-6", "789-01-2"],
            "Papers Found": [45, 23],
            "Review Articles": [5, 2],
            "Quality Score": [85, 72],
            "Status": ["✅ Complete", "✅ Complete"],
        }
    )

    st.dataframe(
        results_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Quality Score": st.column_config.ProgressColumn(
                "Quality Score",
                help="Overall quality score based on multiple factors",
                format="%d",
                min_value=0,
                max_value=100,
            ),
        },
    )

    # Visualizations
    st.subheader("📈 Results Analysis")

    tab1, tab2, tab3 = st.tabs(["Distribution", "Trends", "Quality Metrics"])

    with tab1:
        st.info("Paper count distribution chart will appear here")
        # TODO: Add distribution chart

    with tab2:
        st.info("Publication trends over time will appear here")
        # TODO: Add trends chart

    with tab3:
        st.info("Quality score breakdown will appear here")
        # TODO: Add quality metrics


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

    # Export button
    if st.button("📥 Generate Export", type="primary"):
        with st.spinner("Generating export file..."):
            # TODO: Implement actual export logic
            import time

            time.sleep(2)  # Simulate export generation

            st.success("✅ Export file generated successfully!")

            # TODO: Provide actual download button
            st.download_button(
                label="📥 Download Export",
                data="Sample export data",  # TODO: Use actual export data
                file_name=f"chemscreen_export_{st.session_state.current_batch_id}.csv",
                mime="text/csv",
            )


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
