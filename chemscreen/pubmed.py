"""PubMed E-utilities API client for literature searches."""

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Optional

import aiohttp

from chemscreen.config import Config, get_config
from chemscreen.models import Chemical, Publication, SearchResult

logger = logging.getLogger(__name__)

# PubMed E-utilities base URLs
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_BASE}/efetch.fcgi"


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_second: float):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """Wait if necessary to maintain rate limit."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_call

            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)

            self.last_call = asyncio.get_event_loop().time()


class PubMedClient:
    """Async client for PubMed E-utilities API."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None):
        self.config = config or get_config()
        self.api_key = api_key or self.config.pubmed_api_key
        self.rate_limit = self.config.get_api_rate_limit()
        self.rate_limiter = RateLimiter(self.rate_limit)
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)

    async def __aenter__(self) -> "PubMedClient":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _build_search_query(
        self,
        chemical: Chemical,
        date_range_years: Optional[int] = None,
        include_reviews: Optional[bool] = None,
    ) -> str:
        """Build PubMed search query for a chemical."""
        # Use config defaults if not provided
        date_range_years = date_range_years or self.config.default_date_range_years
        include_reviews = (
            include_reviews
            if include_reviews is not None
            else self.config.default_include_reviews
        )

        # Start with chemical name
        terms = [f'"{chemical.name}"[Title/Abstract]']

        # Add CAS number if available
        if chemical.cas_number:
            terms.append(f'"{chemical.cas_number}"[Title/Abstract]')

        # Add synonyms
        for synonym in chemical.synonyms:
            terms.append(f'"{synonym}"[Title/Abstract]')

        # Combine with OR
        query = " OR ".join(terms)
        query = f"({query})"

        # Add date filter
        date_filter = f"{(datetime.now() - timedelta(days=365 * date_range_years)).strftime('%Y/%m/%d')}[PDAT] : 3000[PDAT]"
        query = f"{query} AND {date_filter}"

        # Exclude reviews if requested
        if not include_reviews:
            query = f"{query} NOT Review[PT]"

        return query

    async def search(
        self,
        chemical: Chemical,
        max_results: Optional[int] = None,
        date_range_years: Optional[int] = None,
        include_reviews: Optional[bool] = None,
    ) -> SearchResult:
        """
        Search PubMed for publications about a chemical.

        Args:
            chemical: Chemical to search for
            max_results: Maximum number of results to retrieve (uses config default if None)
            date_range_years: Years to search back (uses config default if None)
            include_reviews: Whether to include review articles (uses config default if None)

        Returns:
            SearchResult object
        """
        start_time = asyncio.get_event_loop().time()

        # Use config defaults if not provided
        max_results = max_results or self.config.max_results_per_chemical

        try:
            # Build search query
            query = self._build_search_query(chemical, date_range_years, include_reviews)

            # Search for PMIDs
            pmids, total_count = await self._esearch(query, max_results)

            if not pmids:
                return SearchResult(
                    chemical=chemical,
                    total_count=total_count,
                    publications=[],
                    search_time_seconds=asyncio.get_event_loop().time() - start_time,
                    error=None,
                    from_cache=False,
                )

            # Fetch publication details
            publications = await self._efetch(pmids)

            # Use actual total count from PubMed (may be more than retrieved)

            return SearchResult(
                chemical=chemical,
                total_count=total_count,
                publications=publications,
                search_time_seconds=asyncio.get_event_loop().time() - start_time,
                error=None,
                from_cache=False,
            )

        except aiohttp.ClientConnectionError as e:
            logger.error(f"Connection error for {chemical.name}: {str(e)}")
            return SearchResult(
                chemical=chemical,
                total_count=0,
                publications=[],
                error=f"Connection failed: {str(e)}",
                search_time_seconds=asyncio.get_event_loop().time() - start_time,
                from_cache=False,
            )
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error for {chemical.name}: {str(e)}")
            return SearchResult(
                chemical=chemical,
                total_count=0,
                publications=[],
                error=f"Request timeout: {str(e)}",
                search_time_seconds=asyncio.get_event_loop().time() - start_time,
                from_cache=False,
            )
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error for {chemical.name}: {e.status} - {str(e)}")
            return SearchResult(
                chemical=chemical,
                total_count=0,
                publications=[],
                error=f"HTTP error {e.status}: {str(e)}",
                search_time_seconds=asyncio.get_event_loop().time() - start_time,
                from_cache=False,
            )
        except Exception as e:
            logger.error(f"Unexpected error for {chemical.name}: {str(e)}")
            return SearchResult(
                chemical=chemical,
                total_count=0,
                publications=[],
                error=f"Search failed: {str(e)}",
                search_time_seconds=asyncio.get_event_loop().time() - start_time,
                from_cache=False,
            )

    async def _esearch(self, query: str, max_results: int) -> tuple[list[str], int]:
        """Execute E-search to get PMIDs."""
        await self.rate_limiter.wait()

        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        # Add tool name and email if configured
        if self.config.pubmed_tool_name:
            params["tool"] = self.config.pubmed_tool_name
        if self.config.pubmed_email:
            params["email"] = self.config.pubmed_email

        if self.session is None:
            raise RuntimeError("Session not initialized")

        async with self.session.get(ESEARCH_URL, params=params) as response:
            response.raise_for_status()
            data = await response.json()

            # Extract PMIDs and total count
            esearch_result = data.get("esearchresult", {})
            id_list = esearch_result.get("idlist", [])
            total_count = int(esearch_result.get("count", 0))
            return id_list, total_count

    async def _efetch(self, pmids: list[str]) -> list[Publication]:
        """Fetch publication details for PMIDs using POST to avoid URL length limits."""
        if not pmids:
            return []

        await self.rate_limiter.wait()

        # Use POST with form data to avoid "Request-URI Too Long" errors
        # This allows fetching thousands of PMIDs in a single request
        data = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }

        if self.api_key:
            data["api_key"] = self.api_key

        # Add tool name and email if configured
        if self.config.pubmed_tool_name:
            data["tool"] = self.config.pubmed_tool_name
        if self.config.pubmed_email:
            data["email"] = self.config.pubmed_email

        if self.session is None:
            raise RuntimeError("Session not initialized")

        # Use POST instead of GET to avoid URL length limits
        async with self.session.post(EFETCH_URL, data=data) as response:
            response.raise_for_status()
            xml_data = await response.text()

            # Parse XML to extract publications
            return self._parse_pubmed_xml(xml_data)

    def _parse_pubmed_xml(self, xml_data: str) -> list[Publication]:
        """Parse PubMed XML response to extract publication data."""
        publications = []

        try:
            root = ET.fromstring(xml_data)

            for article in root.findall(".//PubmedArticle"):
                pub = self._extract_publication(article)
                if pub:
                    publications.append(pub)

        except Exception as e:
            logger.error(f"XML parsing error: {str(e)}")

        return publications

    def _extract_publication(self, article_elem: ET.Element) -> Optional[Publication]:
        """Extract publication data from XML element."""
        try:
            # Extract PMID
            pmid_elem = article_elem.find(".//PMID")
            if pmid_elem is None or pmid_elem.text is None:
                return None
            pmid = pmid_elem.text

            # Extract article details
            article = article_elem.find(".//Article")
            if article is None:
                return None

            # Title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None and title_elem.text else ""

            # Authors
            authors = []
            author_list = article.find(".//AuthorList")
            if author_list is not None:
                for author in author_list.findall(".//Author"):
                    last_name = author.find(".//LastName")
                    fore_name = author.find(".//ForeName")
                    if last_name is not None and last_name.text:
                        name = last_name.text
                        if fore_name is not None and fore_name.text:
                            name = f"{name} {fore_name.text}"
                        authors.append(name)

            # Journal
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else None

            # Year
            pub_date = article.find(".//PubDate/Year")
            year = int(pub_date.text) if pub_date is not None and pub_date.text else None

            # Abstract
            abstract_elem = article.find(".//Abstract/AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else None

            # DOI
            doi_elem = article_elem.find('.//ArticleId[@IdType="doi"]')
            doi = doi_elem.text if doi_elem is not None else None

            # Check if review
            pub_types = article.findall(".//PublicationType")
            is_review = any("Review" in (pt.text or "") for pt in pub_types)

            return Publication(
                pmid=pmid,
                title=title,
                authors=authors,
                journal=journal,
                year=year,
                abstract=abstract,
                doi=doi,
                is_review=is_review,
                publication_date=None,
            )

        except Exception as e:
            logger.error(f"Error extracting publication: {str(e)}")
            return None


async def batch_search(
    chemicals: list[Chemical],
    max_results_per_chemical: Optional[int] = None,
    date_range_years: Optional[int] = None,
    include_reviews: Optional[bool] = None,
    api_key: Optional[str] = None,
    progress_callback: Optional[Any] = None,
    config: Optional[Config] = None,
) -> list[SearchResult]:
    """
    Perform batch search for multiple chemicals.

    Args:
        chemicals: List of chemicals to search
        max_results_per_chemical: Max results per chemical (uses config default if None)
        date_range_years: Years to search back (uses config default if None)
        include_reviews: Include review articles (uses config default if None)
        api_key: PubMed API key (uses config if None)
        progress_callback: Callback for progress updates
        config: Configuration instance (uses global if None)

    Returns:
        List of SearchResult objects
    """
    import asyncio

    config = config or get_config()

    async with PubMedClient(api_key, config) as client:
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(config.concurrent_requests)

        async def search_with_semaphore(chemical: Chemical) -> SearchResult:
            """Search with semaphore control and progress tracking."""
            async with semaphore:
                return await client.search(
                    chemical,
                    max_results_per_chemical,
                    date_range_years,
                    include_reviews,
                )

        # Create all search tasks
        tasks = [search_with_semaphore(chemical) for chemical in chemicals]

        # Run tasks concurrently with progress updates
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            # Progress callback
            if progress_callback:
                progress = (i + 1) / len(chemicals)
                await progress_callback(progress, result.chemical)

    return results
