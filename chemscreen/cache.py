"""File-based caching system for API responses."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from chemscreen.config import Config, get_config
from chemscreen.models import Chemical, Publication, SearchResult

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages file-based caching of search results."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_seconds: Optional[int] = None,
        config: Optional[Config] = None,
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files (uses config if None)
            ttl_seconds: Time-to-live for cache entries in seconds (uses config if None)
            config: Configuration instance (uses global if None)
        """
        self.config = config or get_config()
        self.cache_dir = cache_dir or self.config.cache_dir
        self.ttl_seconds = ttl_seconds or self.config.cache_ttl
        self.enabled = self.config.cache_enabled

        # Create cache directory if it doesn't exist
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_cache_key(
        self,
        chemical: Chemical,
        date_range_years: int,
        max_results: int,
        include_reviews: bool,
    ) -> str:
        """Generate unique cache key for a search."""
        # Create a unique identifier based on search parameters
        key_parts = [
            chemical.name.lower(),
            chemical.cas_number or "no_cas",
            str(date_range_years),
            str(max_results),
            str(include_reviews),
        ]

        key_string = "|".join(key_parts)

        # Create hash for filename
        hash_object = hashlib.md5(key_string.encode())
        return hash_object.hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get full path for cache file."""
        return self.cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid."""
        if not cache_path.exists():
            return False

        # Check age
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - file_time

        return age < timedelta(seconds=self.ttl_seconds)

    def get(
        self,
        chemical: Chemical,
        date_range_years: int,
        max_results: int,
        include_reviews: bool,
    ) -> Optional[SearchResult]:
        """
        Retrieve cached search result if available and valid.

        Args:
            chemical: Chemical that was searched
            date_range_years: Years searched back
            max_results: Maximum results requested
            include_reviews: Whether reviews were included

        Returns:
            SearchResult if cached and valid, None otherwise
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(
            chemical, date_range_years, max_results, include_reviews
        )
        cache_path = self._get_cache_path(cache_key)

        if not self._is_cache_valid(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct SearchResult
            result = self._deserialize_search_result(data, chemical)
            result.from_cache = True

            logger.info(f"Cache hit for {chemical.name}")
            return result

        except (IOError, OSError) as e:
            logger.error(f"Cache file read error for {chemical.name}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Cache JSON decode error for {chemical.name}: {str(e)}")
            # Optionally remove the corrupted cache file
            try:
                cache_path.unlink()
                logger.info(f"Removed corrupted cache file for {chemical.name}")
            except OSError:
                pass
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Cache deserialization error for {chemical.name}: {str(e)}")
            return None

    def save(
        self,
        result: SearchResult,
        date_range_years: int,
        max_results: int,
        include_reviews: bool,
    ) -> bool:
        """
        Save search result to cache.

        Args:
            result: SearchResult to cache
            date_range_years: Years searched back
            max_results: Maximum results requested
            include_reviews: Whether reviews were included

        Returns:
            bool: True if saved successfully
        """
        if not self.enabled or result.error:
            # Don't cache if disabled or if there are errors
            return False

        cache_key = self._generate_cache_key(
            result.chemical, date_range_years, max_results, include_reviews
        )
        cache_path = self._get_cache_path(cache_key)

        try:
            # Serialize to JSON
            data = self._serialize_search_result(result)

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Cached results for {result.chemical.name}")
            return True

        except (IOError, OSError) as e:
            logger.error(f"Cache file write error for {result.chemical.name}: {str(e)}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(
                f"Cache serialization error for {result.chemical.name}: {str(e)}"
            )
            return False

    def clear(self) -> int:
        """
        Clear all cache files.

        Returns:
            int: Number of files cleared
        """
        count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.error(f"Error deleting cache file {cache_file}: {str(e)}")

        logger.info(f"Cleared {count} cache files")
        return count

    def clear_expired(self) -> int:
        """
        Clear only expired cache files.

        Returns:
            int: Number of files cleared
        """
        count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            if not self._is_cache_valid(cache_file):
                try:
                    cache_file.unlink()
                    count += 1
                except Exception as e:
                    logger.error(
                        f"Error deleting expired cache file {cache_file}: {str(e)}"
                    )

        logger.info(f"Cleared {count} expired cache files")
        return count

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_files = 0
        total_size = 0
        expired_files = 0

        for cache_file in self.cache_dir.glob("*.json"):
            total_files += 1
            total_size += cache_file.stat().st_size

            if not self._is_cache_valid(cache_file):
                expired_files += 1

        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "expired_files": expired_files,
            "valid_files": total_files - expired_files,
            "cache_directory": str(self.cache_dir),
        }

    def _serialize_search_result(self, result: SearchResult) -> dict[str, Any]:
        """Serialize SearchResult to JSON-compatible dict."""
        return {
            "search_date": result.search_date.isoformat(),
            "total_count": result.total_count,
            "search_time_seconds": result.search_time_seconds,
            "publications": [
                {
                    "pmid": pub.pmid,
                    "title": pub.title,
                    "authors": pub.authors,
                    "journal": pub.journal,
                    "year": pub.year,
                    "abstract": pub.abstract,
                    "doi": pub.doi,
                    "is_review": pub.is_review,
                }
                for pub in result.publications
            ],
        }

    def _deserialize_search_result(
        self, data: dict[str, Any], chemical: Chemical
    ) -> SearchResult:
        """Deserialize JSON data to SearchResult."""
        publications = [Publication(**pub_data) for pub_data in data["publications"]]

        return SearchResult(
            chemical=chemical,
            search_date=datetime.fromisoformat(data["search_date"]),
            total_count=data["total_count"],
            publications=publications,
            search_time_seconds=data.get("search_time_seconds"),
            error=None,
            from_cache=True,
        )


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(config: Optional[Config] = None) -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(config=config)

    return _cache_manager


def reset_cache_manager() -> None:
    """Reset the global cache manager instance (for testing)."""
    global _cache_manager
    _cache_manager = None
