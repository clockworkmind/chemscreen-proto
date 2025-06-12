"""
Error handling utilities for ChemScreen.

This module provides user-friendly error messages and consistent error handling
patterns for the ChemScreen application.
"""

from typing import Any
import streamlit as st
import logging

logger = logging.getLogger(__name__)


class ChemScreenError(Exception):
    """Base exception for ChemScreen operations."""

    def __init__(
        self,
        message: str,
        user_message: str | None = None,
        suggestions: list[str] | None = None,
    ):
        self.user_message = user_message or message
        self.suggestions = suggestions or []
        super().__init__(message)


class FileUploadError(ChemScreenError):
    """File upload related errors."""

    pass


class ValidationError(ChemScreenError):
    """Data validation errors."""

    pass


class APIError(ChemScreenError):
    """API-related errors with user-friendly messages."""

    pass


class ProcessingError(ChemScreenError):
    """Chemical processing errors."""

    pass


def get_friendly_error_message(
    error_type: str, details: str | None = None
) -> dict[str, Any]:
    """
    Get user-friendly error messages for common error types.

    Args:
        error_type: Type of error (e.g., 'file_size', 'invalid_csv', etc.)
        details: Additional error details

    Returns:
        Dict with 'message', 'suggestions', and 'icon' keys
    """
    error_messages = {
        "file_size": {
            "message": "Your file is too large to process safely.",
            "suggestions": [
                "Split your file into smaller batches (max 200 chemicals each)",
                "Remove unnecessary columns to reduce file size",
                "Save as CSV format to reduce file size",
            ],
            "icon": "📏",
        },
        "file_empty": {
            "message": "The uploaded file appears to be empty.",
            "suggestions": [
                "Check that your CSV file contains data",
                "Ensure the file was saved properly",
                "Try uploading a different file",
            ],
            "icon": "📄",
        },
        "invalid_csv": {
            "message": "We couldn't read your CSV file properly.",
            "suggestions": [
                "Check that the file is in CSV format",
                "Ensure commas are used as separators",
                "Remove any special characters from headers",
                "Save your Excel file as CSV before uploading",
            ],
            "icon": "📊",
        },
        "no_columns_selected": {
            "message": "You need to select at least one column to continue.",
            "suggestions": [
                "Select either a Chemical Name column or CAS Number column",
                "Check that your CSV has the right headers",
                "Make sure column names match your data",
            ],
            "icon": "📋",
        },
        "invalid_cas": {
            "message": "Some CAS numbers in your file are not valid.",
            "suggestions": [
                "CAS numbers should be in format XXX-XX-X (like 75-09-2)",
                "Check for typos in your CAS numbers",
                "Leave CAS field blank if unknown",
            ],
            "icon": "🔢",
        },
        "batch_too_large": {
            "message": "Your batch has too many chemicals to process at once.",
            "suggestions": [
                "Split your file into batches of 200 chemicals or fewer",
                "Process the first 200 chemicals now and save the rest for later",
                "Contact support if you need to process larger batches regularly",
            ],
            "icon": "📦",
        },
        "network_error": {
            "message": "We're having trouble connecting to the search service.",
            "suggestions": [
                "Check your internet connection",
                "Try again in a few minutes",
                "Contact support if the problem continues",
            ],
            "icon": "🌐",
        },
        "api_timeout": {
            "message": "The search is taking longer than expected.",
            "suggestions": [
                "Try searching with a smaller batch",
                "Check your internet connection",
                "Use cached results if available",
            ],
            "icon": "⏱️",
        },
        "api_rate_limit": {
            "message": "We're searching too quickly and need to slow down.",
            "suggestions": [
                "The search will continue automatically",
                "Consider using an API key for faster searches",
                "This helps ensure reliable results",
            ],
            "icon": "🚦",
        },
        "processing_failed": {
            "message": "Something went wrong while processing your chemicals.",
            "suggestions": [
                "Check your data for unusual characters",
                "Try processing a smaller batch first",
                "Contact support if this keeps happening",
            ],
            "icon": "⚠️",
        },
    }

    error_info = error_messages.get(
        error_type,
        {
            "message": f"An unexpected error occurred: {details or 'Unknown error'}",
            "suggestions": ["Try again or contact support if the problem continues"],
            "icon": "❌",
        },
    )

    if details and error_type in error_messages:
        error_info["details"] = details

    return error_info


def show_error_with_help(
    error_type: str, details: str | None = None, expand_help: bool = False
) -> None:
    """
    Display a user-friendly error message with helpful suggestions.

    Args:
        error_type: Type of error
        details: Additional error details
        expand_help: Whether to expand the help section by default
    """
    error_info = get_friendly_error_message(error_type, details)

    # Show main error message
    st.error(f"{error_info['icon']} {error_info['message']}")

    # Show detailed suggestions
    with st.expander("💡 How to Fix This", expanded=expand_help):
        for suggestion in error_info["suggestions"]:
            st.markdown(f"• {suggestion}")

        if "details" in error_info:
            st.markdown("---")
            st.caption(f"Technical details: {error_info['details']}")


def show_validation_help(
    validation_errors: list[dict[str, Any]], expand: bool = True
) -> None:
    """
    Show specific help for validation errors with context.

    Args:
        validation_errors: List of validation error dictionaries
        expand: Whether to expand the help section by default
    """
    if not validation_errors:
        return

    with st.expander("❓ How to Fix Validation Errors", expanded=expand):
        error_types = set()
        for error in validation_errors:
            error_msg = error.get("errors", str(error))
            if "CAS" in error_msg:
                error_types.add("cas")
            elif "empty" in error_msg.lower() or "missing" in error_msg.lower():
                error_types.add("empty")
            elif "invalid" in error_msg.lower():
                error_types.add("invalid")

        if "cas" in error_types:
            st.markdown("**CAS Number Issues:**")
            st.markdown("• Use format XXX-XX-X (e.g., 75-09-2)")
            st.markdown("• Check for typos or missing digits")
            st.markdown("• Leave blank if CAS number is unknown")
            st.markdown("")

        if "empty" in error_types:
            st.markdown("**Missing Information:**")
            st.markdown("• Each row needs either a chemical name or CAS number")
            st.markdown("• Remove completely empty rows")
            st.markdown("• Check for extra commas or formatting issues")
            st.markdown("")

        if "invalid" in error_types:
            st.markdown("**Data Format Issues:**")
            st.markdown("• Remove special characters from chemical names")
            st.markdown("• Use standard chemical nomenclature when possible")
            st.markdown("• Check for encoding issues (use UTF-8)")


def create_progress_with_cancel(
    label: str = "Processing...",
) -> tuple[Any, Any, Any, Any]:
    """
    Create a progress bar with cancel functionality.

    Args:
        label: Label for the progress operation

    Returns:
        Tuple of (progress_bar, status_text, cancel_button)
    """
    progress_container = st.container()

    with progress_container:
        st.markdown(f"**{label}**")
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Cancel button in a separate column
        col1, col2 = st.columns([4, 1])
        with col2:
            cancel_button = st.button("⏸️ Cancel", key=f"cancel_{label}")

    return progress_bar, status_text, cancel_button, progress_container


def show_success_with_stats(
    message: str, stats: dict[str, Any], show_balloons: bool = True
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


def log_error_for_support(error: Exception, context: str | None = None) -> None:
    """
    Log error details for support while keeping user messages friendly.

    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
    """
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
    }

    logger.error(
        f"ChemScreen error in {context}: {error}", exc_info=True, extra=error_details
    )


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


def handle_common_errors(func: Any) -> Any:
    """
    Decorator to handle common errors with user-friendly messages.
    """

    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return func(*args, **kwargs)
        except FileUploadError as e:
            show_error_with_help("file_upload", str(e))
            log_error_for_support(e, func.__name__)
        except ValidationError as e:
            show_error_with_help("validation", str(e))
            log_error_for_support(e, func.__name__)
        except APIError as e:
            show_error_with_help("network_error", str(e))
            log_error_for_support(e, func.__name__)
        except Exception as e:
            show_error_with_help("processing_failed", str(e))
            log_error_for_support(e, func.__name__)

    return wrapper
