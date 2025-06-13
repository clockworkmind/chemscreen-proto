"""Analyzer module for quality scoring and trend analysis."""

import logging
from collections import Counter
from datetime import datetime
from typing import Any

from chemscreen.models import Publication, QualityMetrics, SearchResult

logger = logging.getLogger(__name__)


def calculate_quality_metrics(result: SearchResult) -> QualityMetrics:
    """
    Calculate quality metrics for a chemical's search results.

    Args:
        result: SearchResult object

    Returns:
        QualityMetrics object
    """
    if result.error or not result.publications:
        return QualityMetrics(
            total_publications=0,
            quality_score=0.0,
            review_count=0,
            recent_publications=0,
            publication_trend="stable",
            has_recent_review=False,
        )

    # Basic counts
    total_pubs = len(result.publications)
    review_count = sum(1 for pub in result.publications if pub.is_review)

    # Recent publications (last 3 years)
    three_years_ago = datetime.now().year - 3
    recent_pubs = sum(
        1 for pub in result.publications if pub.year and pub.year >= three_years_ago
    )

    # Recent review (last 5 years)
    five_years_ago = datetime.now().year - 5
    has_recent_review = any(
        pub.is_review and pub.year and pub.year >= five_years_ago
        for pub in result.publications
    )

    # Calculate publication trend
    trend = calculate_publication_trend(result.publications)

    # Calculate quality score (0-100)
    score = calculate_quality_score(
        total_pubs=total_pubs,
        review_count=review_count,
        recent_pubs=recent_pubs,
        has_recent_review=has_recent_review,
        trend=trend,
    )

    return QualityMetrics(
        total_publications=total_pubs,
        review_count=review_count,
        recent_publications=recent_pubs,
        publication_trend=trend,
        quality_score=score,
        has_recent_review=has_recent_review,
    )


def calculate_publication_trend(publications: list[Publication]) -> str:
    """
    Calculate publication trend over time.

    Args:
        publications: List of publications

    Returns:
        str: "increasing", "decreasing", or "stable"
    """
    if not publications:
        return "stable"

    # Get publications by year
    years = [pub.year for pub in publications if pub.year]
    if len(years) < 3:
        return "stable"

    # Count by year
    year_counts = Counter(years)

    # Get recent 5 years
    current_year = datetime.now().year
    recent_years = range(current_year - 4, current_year + 1)
    recent_counts = [year_counts.get(year, 0) for year in recent_years]

    # Simple trend analysis
    first_half = sum(recent_counts[:2])
    second_half = sum(recent_counts[3:])

    if second_half > first_half * 1.5:
        return "increasing"
    elif second_half < first_half * 0.5:
        return "decreasing"
    else:
        return "stable"


def calculate_quality_score(
    total_pubs: int,
    review_count: int,
    recent_pubs: int,
    has_recent_review: bool,
    trend: str,
) -> float:
    """
    Calculate overall quality score (0-100).

    Scoring factors:
    - Total publications (40 points max)
    - Review articles (20 points max)
    - Recent activity (20 points max)
    - Recent review (10 points)
    - Positive trend (10 points)

    Args:
        total_pubs: Total publication count
        review_count: Number of review articles
        recent_pubs: Publications in last 3 years
        has_recent_review: Has review in last 5 years
        trend: Publication trend

    Returns:
        float: Quality score 0-100
    """
    score = 0.0

    # Total publications (40 points max)
    # 50+ pubs = full points, linear scale
    pub_score = min(40.0, (total_pubs / 50) * 40)
    score += pub_score

    # Review articles (20 points max)
    # 5+ reviews = full points
    review_score = min(20.0, (review_count / 5) * 20)
    score += review_score

    # Recent activity (20 points max)
    # 10+ recent pubs = full points
    recent_score = min(20.0, (recent_pubs / 10) * 20)
    score += recent_score

    # Recent review bonus (10 points)
    if has_recent_review:
        score += 10.0

    # Trend bonus (10 points)
    if trend == "increasing":
        score += 10.0
    elif trend == "stable":
        score += 5.0

    return round(score, 1)


def identify_high_priority_chemicals(
    results: list[tuple[SearchResult, QualityMetrics]],
    min_score: float = 70.0,
    min_publications: int = 20,
) -> list[tuple[SearchResult, QualityMetrics]]:
    """
    Identify high priority chemicals based on quality metrics.

    Args:
        results: List of (SearchResult, QualityMetrics) tuples
        min_score: Minimum quality score
        min_publications: Minimum publication count

    Returns:
        Filtered list of high priority chemicals
    """
    high_priority = []

    for result, metrics in results:
        if (
            metrics.quality_score >= min_score
            and metrics.total_publications >= min_publications
        ):
            high_priority.append((result, metrics))

    # Sort by quality score descending
    high_priority.sort(key=lambda x: x[1].quality_score, reverse=True)

    return high_priority


def generate_summary_statistics(
    results: list[tuple[SearchResult, QualityMetrics]],
) -> dict[str, Any]:
    """
    Generate summary statistics for a batch search.

    Args:
        results: List of (SearchResult, QualityMetrics) tuples

    Returns:
        Dictionary of summary statistics
    """
    if not results:
        return {
            "total_chemicals": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "total_publications": 0,
            "total_reviews": 0,
            "avg_quality_score": 0.0,
            "high_quality_count": 0,
        }

    successful = [r for r, m in results if not r.error]
    failed = [r for r, m in results if r.error]

    total_pubs = sum(m.total_publications for r, m in results)
    total_reviews = sum(m.review_count for r, m in results)

    quality_scores = [m.quality_score for r, m in results if not r.error]
    avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

    high_quality = sum(1 for r, m in results if m.quality_score >= 70)

    return {
        "total_chemicals": len(results),
        "successful_searches": len(successful),
        "failed_searches": len(failed),
        "total_publications": total_pubs,
        "total_reviews": total_reviews,
        "avg_quality_score": round(avg_score, 1),
        "high_quality_count": high_quality,
        "chemicals_with_reviews": sum(1 for r, m in results if m.review_count > 0),
        "chemicals_with_recent_activity": sum(
            1 for r, m in results if m.recent_publications > 0
        ),
    }


def group_chemicals_by_quality(
    results: list[tuple[SearchResult, QualityMetrics]],
) -> dict[str, list[tuple[SearchResult, QualityMetrics]]]:
    """
    Group chemicals into quality tiers.

    Args:
        results: List of (SearchResult, QualityMetrics) tuples

    Returns:
        Dictionary with quality tiers
    """
    tiers: dict[str, list[tuple[SearchResult, QualityMetrics]]] = {
        "high": [],  # 70+ score
        "medium": [],  # 40-69 score
        "low": [],  # 10-39 score
        "minimal": [],  # <10 score
        "failed": [],  # Search errors
    }

    for result, metrics in results:
        if result.error:
            tiers["failed"].append((result, metrics))
        elif metrics.quality_score >= 70:
            tiers["high"].append((result, metrics))
        elif metrics.quality_score >= 40:
            tiers["medium"].append((result, metrics))
        elif metrics.quality_score >= 10:
            tiers["low"].append((result, metrics))
        else:
            tiers["minimal"].append((result, metrics))

    return tiers
