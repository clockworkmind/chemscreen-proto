"""
History page for ChemScreen multipage application.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import logging
from datetime import datetime

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

# Import ChemScreen modules
from chemscreen.config import initialize_config
from chemscreen.session_manager import SessionManager
from chemscreen.errors import show_error_with_help

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
    page_title="History - ChemScreen",
    page_icon="📜",
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


def show_history_page():
    """Display the search history page."""
    st.title("📜 Search History")

    st.markdown("View and manage your previous search sessions.")

    # Initialize session manager
    session_manager = SessionManager()

    # Get session list
    sessions = session_manager.list_sessions()

    if not sessions:
        st.info(
            "No search history available. Run a search to create your first session."
        )
        if st.button("Go to Search"):
            try:
                st.switch_page("pages/2_🔍_Search.py")
            except AttributeError:
                st.info("💡 Navigate to the **Search** page to run your first search.")
        return

    # Session management controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader(f"Found {len(sessions)} Sessions")

    with col2:
        if st.button("🧹 Cleanup Old Sessions"):
            deleted_count = session_manager.cleanup_old_sessions(days_to_keep=30)
            if deleted_count > 0:
                st.success(f"Deleted {deleted_count} old sessions")
                st.rerun()
            else:
                st.info("No old sessions to clean up")

    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Convert sessions to DataFrame for display
    history_data = []
    for session_meta in sessions:
        try:
            created_at = datetime.fromisoformat(session_meta["created_at"])
            history_data.append(
                {
                    "Batch ID": session_meta["session_id"],
                    "Date": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "Chemicals": session_meta["chemical_count"],
                    "Status": "✅ Complete"
                    if session_meta.get("status") == "completed"
                    else "⚠️ Partial",
                    "Results": session_meta.get("result_count", 0),
                    "Session Name": session_meta.get("session_name", "Unnamed Session"),
                }
            )
        except Exception as e:
            logger.error(f"Error processing session metadata: {e}")
            continue

    if not history_data:
        st.warning("No valid sessions found in history.")
        return

    history_df = pd.DataFrame(history_data)

    # Display history table with actions
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

    # Session actions
    st.markdown("---")
    st.subheader("Session Actions")

    # Session selection for actions
    selected_session_id = st.selectbox(
        "Select Session",
        options=[session["session_id"] for session in sessions],
        format_func=lambda x: f"{x} - {next((s['session_name'] or 'Unnamed') for s in sessions if s['session_id'] == x)}",
    )

    if selected_session_id:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📂 Load Session", type="primary"):
                # Load session and set as current
                loaded_session = session_manager.load_session(selected_session_id)
                if loaded_session:
                    st.session_state.current_session = loaded_session
                    st.session_state.chemicals = loaded_session.chemicals
                    st.session_state.search_results = list(
                        loaded_session.results.values()
                    )
                    st.session_state.current_batch_id = loaded_session.batch_id

                    # Update search parameters in session state
                    st.session_state.date_range = (
                        loaded_session.parameters.date_range_years
                    )
                    st.session_state.max_results = loaded_session.parameters.max_results
                    st.session_state.include_reviews = (
                        loaded_session.parameters.include_reviews
                    )

                    st.success(f"Session {selected_session_id} loaded successfully!")
                    st.info(
                        "Session data has been restored. Navigate to Results or Export pages to view the data."
                    )

                    # Quick navigation to results
                    if st.button("📊 View Results", type="secondary"):
                        try:
                            st.switch_page("pages/3_📊_Results.py")
                        except AttributeError:
                            st.info(
                                "💡 Navigate to the **Results** page to view the loaded data."
                            )
                else:
                    show_error_with_help(
                        "session_load_failed",
                        f"Could not load session {selected_session_id}. The session file may be corrupted or missing.",
                    )

        with col2:
            if st.button("🗑️ Delete Session"):
                if session_manager.delete_session(selected_session_id):
                    st.success(f"Session {selected_session_id} deleted")
                    st.rerun()
                else:
                    show_error_with_help(
                        "session_delete_failed",
                        f"Could not delete session {selected_session_id}. Check file permissions.",
                    )

        with col3:
            if st.button("📋 View Details"):
                # Show session details
                session_details = session_manager.load_session(selected_session_id)
                if session_details:
                    st.json(
                        {
                            "Batch ID": session_details.batch_id,
                            "Created": session_details.created_at.isoformat(),
                            "Chemicals": len(session_details.chemicals),
                            "Results": len(session_details.results),
                            "Status": session_details.status,
                            "Parameters": {
                                "Date Range": f"{session_details.parameters.date_range_years} years",
                                "Max Results": session_details.parameters.max_results,
                                "Include Reviews": session_details.parameters.include_reviews,
                            },
                        }
                    )
                else:
                    show_error_with_help(
                        "session_details_failed",
                        f"Could not load details for session {selected_session_id}",
                    )


# Main execution
if __name__ == "__main__":
    show_history_page()
else:
    show_history_page()
