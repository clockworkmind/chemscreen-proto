"""PubMed E-utilities API client for literature searches."""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict
import xml.etree.ElementTree as ET

from chemscreen.models import Chemical, Publication, SearchResult

logger = logging.getLogger(__name__)

# PubMed E-utilities base URLs
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_BASE}/efetch.fcgi"

# Rate limiting
DEFAULT_RATE_LIMIT = 3  # requests per second without API key
API_KEY_RATE_LIMIT = 10  # requests per second with API key


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

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.rate_limit = API_KEY_RATE_LIMIT if api_key else DEFAULT_RATE_LIMIT
        self.rate_limiter = RateLimiter(self.rate_limit)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "PubMedClient":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _build_search_query(
        self,
        chemical: Chemical,
        date_range_years: int = 10,
        include_reviews: bool = True,
    ) -> str:
        """Build PubMed search query for a chemical."""
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
        max_results: int = 100,
        date_range_years: int = 10,
        include_reviews: bool = True,
    ) -> SearchResult:
        """
        Search PubMed for publications about a chemical.

        Args:
            chemical: Chemical to search for
            max_results: Maximum number of results to retrieve
            date_range_years: Years to search back
            include_reviews: Whether to include review articles

        Returns:
            SearchResult object
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Build search query
            query = self._build_search_query(
                chemical, date_range_years, include_reviews
            )

            # Search for PMIDs
            pmids = await self._esearch(query, max_results)

            if not pmids:
                return SearchResult(
                    chemical=chemical,
                    total_count=0,
                    publications=[],
                    search_time_seconds=asyncio.get_event_loop().time() - start_time,
                    error=None,
                    from_cache=False,
                )

            # Fetch publication details
            publications = await self._efetch(pmids)

            # Determine total count (may be more than retrieved)
            total_count = len(pmids)  # TODO: Get actual count from esearch

            return SearchResult(
                chemical=chemical,
                total_count=total_count,
                publications=publications,
                search_time_seconds=asyncio.get_event_loop().time() - start_time,
                error=None,
                from_cache=False,
            )

        except Exception as e:
            logger.error(f"Search failed for {chemical.name}: {str(e)}")
            return SearchResult(
                chemical=chemical,
                total_count=0,
                publications=[],
                error=str(e),
                search_time_seconds=asyncio.get_event_loop().time() - start_time,
                from_cache=False,
            )

    async def _esearch(self, query: str, max_results: int) -> List[str]:
        """Execute E-search to get PMIDs."""
        await self.rate_limiter.wait()

        params: Dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        if self.session is None:
            raise RuntimeError("Session not initialized")

        async with self.session.get(ESEARCH_URL, params=params) as response:
            response.raise_for_status()
            data = await response.json()

            # Extract PMIDs
            id_list = data.get("esearchresult", {}).get("idlist", [])
            return id_list  # type: ignore[no-any-return]

    async def _efetch(self, pmids: List[str]) -> List[Publication]:
        """Fetch publication details for PMIDs."""
        if not pmids:
            return []

        await self.rate_limiter.wait()

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        if self.session is None:
            raise RuntimeError("Session not initialized")

        async with self.session.get(EFETCH_URL, params=params) as response:
            response.raise_for_status()
            xml_data = await response.text()

            # Parse XML to extract publications
            return self._parse_pubmed_xml(xml_data)

    def _parse_pubmed_xml(self, xml_data: str) -> List[Publication]:
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
            title = (
                title_elem.text if title_elem is not None and title_elem.text else ""
            )

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
            year = (
                int(pub_date.text) if pub_date is not None and pub_date.text else None
            )

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
    chemicals: List[Chemical],
    max_results_per_chemical: int = 100,
    date_range_years: int = 10,
    include_reviews: bool = True,
    api_key: Optional[str] = None,
    progress_callback: Optional[Any] = None,
) -> List[SearchResult]:
    """
    Perform batch search for multiple chemicals.

    Args:
        chemicals: List of chemicals to search
        max_results_per_chemical: Max results per chemical
        date_range_years: Years to search back
        include_reviews: Include review articles
        api_key: PubMed API key
        progress_callback: Callback for progress updates

    Returns:
        List of SearchResult objects
    """
    results = []

    async with PubMedClient(api_key) as client:
        for i, chemical in enumerate(chemicals):
            # Search for chemical
            result = await client.search(
                chemical, max_results_per_chemical, date_range_years, include_reviews
            )
            results.append(result)

            # Progress callback
            if progress_callback:
                progress = (i + 1) / len(chemicals)
                await progress_callback(progress, chemical)

    return results
