"""
Results page for ChemScreen multipage application.
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
from chemscreen.analyzer import calculate_quality_metrics

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
    page_title="Results - ChemScreen",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state and UI
init_session_state()
load_custom_css()

setup_sidebar()


def show_results_page() -> None:
    """Display the search results page."""
    st.title("📊 Search Results")

    if not st.session_state.search_results:
        st.warning("⚠️ No search results available. Please run a search first.")
        st.page_link("pages/2_🔍_Search.py", label="Go to Search", icon="▶️")
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

    # Quick action buttons
    st.markdown("---")
    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Export Results", type="primary", use_container_width=True):
            st.switch_page("pages/4_📥_Export.py")

    with col2:
        if st.button("🔍 New Search", use_container_width=True):
            st.switch_page("pages/2_🔍_Search.py")

    with col3:
        if st.button("📜 View History", use_container_width=True):
            st.switch_page("pages/5_📜_History.py")


# Main execution
if __name__ == "__main__":
    show_results_page()
else:
    show_results_page()
