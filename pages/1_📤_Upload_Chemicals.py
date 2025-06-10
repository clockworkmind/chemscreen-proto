"""
Upload Chemicals page for ChemScreen multipage application.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import logging

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

# Import ChemScreen modules
from chemscreen.config import initialize_config
from chemscreen.processor import merge_duplicates, detect_duplicates
from chemscreen.models import CSVColumnMapping
from chemscreen.cached_processors import (
    cached_process_csv_data,
    cached_suggest_column_mapping,
)
from chemscreen.errors import (
    show_error_with_help,
    show_validation_help,
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
    page_title="Upload Chemicals - ChemScreen",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state and UI
init_session_state()
load_custom_css()

# Add sidebar title above page navigation
with st.sidebar:
    st.title("🧪 ChemScreen")
    st.markdown("---")

setup_sidebar()


def show_upload_page():
    """Display the chemical upload page."""
    st.title("📤 Upload Chemical List")

    # Check for demo load results and display them in main area
    if "demo_load_result" in st.session_state:
        result = st.session_state.demo_load_result
        if result["success"]:
            st.success(
                f"✅ {result['size'].title()} demo dataset loaded! "
                f"{result['valid_count']} chemicals ready for search."
            )

            # Show any warnings from processing
            if result.get("warnings"):
                with st.expander(
                    f"⚠️ Processing Warnings ({len(result['warnings'])})",
                    expanded=False,
                ):
                    for warning in result["warnings"]:
                        st.warning(warning)

            # Show invalid rows if any (expected for large dataset with edge cases)
            if result.get("invalid_rows"):
                with st.expander(
                    f"❌ Invalid Rows ({len(result['invalid_rows'])})", expanded=False
                ):
                    st.info("These are intentional edge cases in the demo data:")
                    for error in result["invalid_rows"]:
                        st.error(f"Row {error['row_number']}: {error['errors']}")

            # Navigate to search page after loading
            if st.button("▶️ Go to Search", type="primary"):
                try:
                    st.switch_page("pages/2_🔍_Search.py")
                except AttributeError:
                    st.info(
                        "💡 Navigate to the **Search** page to configure and run your search."
                    )
                # Clear demo result to avoid showing it again
                del st.session_state.demo_load_result
        else:
            show_error_with_help(
                "no_valid_data",
                result.get("error", "Demo data loading failed"),
            )

        # Clear demo result after showing (unless user clicked Go to Search)
        if "demo_load_result" in st.session_state:
            del st.session_state.demo_load_result

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
                MAX_BATCH_SIZE = config.max_batch_size
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
                    st.markdown("\\n".join(detected_cols))

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
                            MAX_BATCH_SIZE = config.max_batch_size
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
        st.caption(
            "Use the demo data buttons in the sidebar to load sample datasets for testing"
        )


# Main execution
if __name__ == "__main__":
    show_upload_page()
else:
    show_upload_page()
