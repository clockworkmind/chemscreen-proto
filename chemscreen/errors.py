"""
Error handling utilities for ChemScreen.

This module provides user-friendly error messages and consistent error handling
patterns for the ChemScreen application.
"""

import logging
from typing import Any

import streamlit as st

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
