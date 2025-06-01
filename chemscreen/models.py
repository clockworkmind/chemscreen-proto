"""Data models for ChemScreen using Pydantic."""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class Chemical(BaseModel):
    """Chemical entity with name and CAS number."""

    name: str = Field(..., description="Chemical name")
    cas_number: Optional[str] = Field(None, description="CAS Registry Number")
    synonyms: List[str] = Field(default_factory=list, description="Alternative names")
    validated: bool = Field(
        False, description="Whether the chemical has been validated"
    )

    model_config = ConfigDict(validate_assignment=True)


class SearchParameters(BaseModel):
    """Parameters for literature search."""

    date_range_years: int = Field(10, ge=1, le=50, description="Years to search back")
    max_results: int = Field(
        100, ge=10, le=1000, description="Maximum results per chemical"
    )
    include_reviews: bool = Field(True, description="Include review articles")
    use_cache: bool = Field(True, description="Use cached results when available")

    model_config = ConfigDict(validate_assignment=True)


class Publication(BaseModel):
    """Individual publication/paper."""

    pmid: str = Field(..., description="PubMed ID")
    title: str = Field(..., description="Publication title")
    authors: List[str] = Field(default_factory=list, description="Author list")
    journal: Optional[str] = Field(None, description="Journal name")
    year: Optional[int] = Field(None, description="Publication year")
    abstract: Optional[str] = Field(None, description="Abstract text")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    is_review: bool = Field(False, description="Whether this is a review article")
    publication_date: Optional[datetime] = Field(
        None, description="Full publication date"
    )

    model_config = ConfigDict(validate_assignment=True)


class SearchResult(BaseModel):
    """Search results for a single chemical."""

    chemical: Chemical = Field(..., description="The chemical that was searched")
    search_date: datetime = Field(
        default_factory=datetime.now, description="When the search was performed"
    )
    total_count: int = Field(0, description="Total number of publications found")
    publications: List[Publication] = Field(
        default_factory=list, description="List of publications"
    )
    error: Optional[str] = Field(None, description="Error message if search failed")
    search_time_seconds: Optional[float] = Field(
        None, description="Time taken to search"
    )
    from_cache: bool = Field(False, description="Whether results came from cache")

    model_config = ConfigDict(validate_assignment=True)


class QualityMetrics(BaseModel):
    """Quality metrics for a chemical's literature."""

    total_publications: int = Field(0, description="Total number of publications")
    review_count: int = Field(0, description="Number of review articles")
    recent_publications: int = Field(0, description="Publications in last 3 years")
    publication_trend: str = Field(
        "stable", description="Trend: increasing/decreasing/stable"
    )
    quality_score: float = Field(
        0.0, ge=0.0, le=100.0, description="Overall quality score"
    )
    has_recent_review: bool = Field(False, description="Has review in last 5 years")

    model_config = ConfigDict(validate_assignment=True)


class BatchSearchSession(BaseModel):
    """A batch search session."""

    batch_id: str = Field(..., description="Unique batch identifier")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Session creation time"
    )
    chemicals: List[Chemical] = Field(
        default_factory=list, description="Chemicals in this batch"
    )
    parameters: SearchParameters = Field(..., description="Search parameters used")
    results: Dict[str, SearchResult] = Field(
        default_factory=dict, description="Results by chemical name"
    )
    status: str = Field(
        "pending", description="Status: pending/running/completed/failed"
    )
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress percentage")

    model_config = ConfigDict(validate_assignment=True)


class ExportData(BaseModel):
    """Data structure for export."""

    session: BatchSearchSession = Field(..., description="The search session")
    quality_metrics: Dict[str, QualityMetrics] = Field(
        default_factory=dict, description="Quality metrics by chemical"
    )
    export_format: str = Field("csv", description="Export format: csv/xlsx/json")
    include_metadata: bool = Field(True, description="Include search metadata")
    include_abstracts: bool = Field(False, description="Include publication abstracts")

    model_config = ConfigDict(validate_assignment=True)
