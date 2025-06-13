"""Configuration management for ChemScreen."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Config:
    """Central configuration class for ChemScreen application."""

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize configuration with environment variables.

        Args:
            env_file: Optional path to .env file to load
        """
        # Load environment variables from .env file if it exists
        if env_file and env_file.exists():
            load_dotenv(env_file)
        else:
            # Try to load from project root
            project_root = Path(__file__).parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file)

        # Initialize all configuration values
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load all configuration values from environment variables."""
        # API Configuration
        self.pubmed_api_key = os.getenv("PUBMED_API_KEY")
        self.pubmed_email = os.getenv("PUBMED_EMAIL")
        self.pubmed_tool_name = os.getenv("PUBMED_TOOL_NAME", "ChemScreen")

        # Rate Limiting
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))

        # Batch Processing
        self.max_batch_size = int(os.getenv("MAX_BATCH_SIZE", "200"))
        self.max_results_per_chemical = int(os.getenv("MAX_RESULTS_PER_CHEMICAL", "100"))
        self.default_date_range_years = int(os.getenv("DEFAULT_DATE_RANGE_YEARS", "10"))

        # Directory Configuration
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.cache_dir = Path(os.getenv("CACHE_DIR", "./data/cache"))
        self.sessions_dir = Path(os.getenv("SESSIONS_DIR", "./data/sessions"))
        self.exports_dir = Path(os.getenv("EXPORTS_DIR", "./data/processed"))
        self.raw_data_dir = Path(os.getenv("RAW_DATA_DIR", "./data/raw"))

        # Cache Configuration
        self.cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
        self.cache_max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # Max entries

        # Export Configuration
        self.export_chunk_size = int(os.getenv("EXPORT_CHUNK_SIZE", "10000"))
        self.export_format_default = os.getenv("EXPORT_FORMAT_DEFAULT", "csv")
        self.export_include_abstracts = (
            os.getenv("EXPORT_INCLUDE_ABSTRACTS", "false").lower() == "true"
        )

        # Session Management
        self.session_cleanup_days = int(os.getenv("SESSION_CLEANUP_DAYS", "30"))
        self.auto_save_sessions = (
            os.getenv("AUTO_SAVE_SESSIONS", "true").lower() == "true"
        )

        # Search Defaults
        self.default_include_reviews = (
            os.getenv("DEFAULT_INCLUDE_REVIEWS", "true").lower() == "true"
        )
        self.search_progress_update_interval = int(
            os.getenv("SEARCH_PROGRESS_UPDATE_INTERVAL", "5")
        )

        # Performance Configuration
        self.memory_limit_mb = int(os.getenv("MEMORY_LIMIT_MB", "512"))
        self.concurrent_requests = int(os.getenv("CONCURRENT_REQUESTS", "1"))

        # Development/Debug
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.enable_performance_logging = (
            os.getenv("ENABLE_PERFORMANCE_LOGGING", "false").lower() == "true"
        )

        # Security
        self.max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
        self.allowed_file_extensions = os.getenv("ALLOWED_FILE_EXTENSIONS", "csv").split(
            ","
        )

        # UI Configuration
        self.page_title = os.getenv(
            "PAGE_TITLE", "ChemScreen - Chemical Literature Search"
        )
        self.page_icon = os.getenv("PAGE_ICON", "🧪")
        self.theme_primary_color = os.getenv("THEME_PRIMARY_COLOR", "#0066CC")

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_dir,
            self.cache_dir,
            self.sessions_dir,
            self.exports_dir,
            self.raw_data_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_api_rate_limit(self) -> float:
        """
        Get appropriate rate limit based on API key availability.

        Returns:
            float: Requests per second limit
        """
        if self.pubmed_api_key:
            # With API key: 10 requests/second
            return 10.0
        else:
            # Without API key: 3 requests/second
            return 3.0

    def validate_configuration(self) -> list[str]:
        """
        Validate configuration and return list of warnings/errors.

        Returns:
            List of validation messages
        """
        warnings = []

        # Check API configuration
        if not self.pubmed_api_key:
            warnings.append(
                "PUBMED_API_KEY not set - searches will be rate limited to 3 requests/second"
            )

        if not self.pubmed_email:
            warnings.append(
                "PUBMED_EMAIL not set - recommended for API usage identification"
            )

        # Check directory permissions
        try:
            self.create_directories()
        except PermissionError:
            warnings.append("Cannot create required directories - check permissions")

        # Check batch size limits
        if self.max_batch_size > 500:
            warnings.append(
                f"MAX_BATCH_SIZE ({self.max_batch_size}) is very large - may cause memory issues"
            )

        # Rate limiting is now automatically managed based on API key presence

        # Check memory limits
        if self.memory_limit_mb < 256:
            warnings.append(
                f"MEMORY_LIMIT_MB ({self.memory_limit_mb}) is very low - may cause processing issues"
            )

        return warnings

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary for logging/debugging.

        Returns:
            Dictionary of configuration values (excluding sensitive data)
        """
        return {
            "pubmed_api_key_configured": bool(self.pubmed_api_key),
            "pubmed_email_configured": bool(self.pubmed_email),
            "pubmed_tool_name": self.pubmed_tool_name,
            "api_rate_limit": self.get_api_rate_limit(),
            "request_timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "max_batch_size": self.max_batch_size,
            "max_results_per_chemical": self.max_results_per_chemical,
            "default_date_range_years": self.default_date_range_years,
            "data_dir": str(self.data_dir),
            "cache_dir": str(self.cache_dir),
            "sessions_dir": str(self.sessions_dir),
            "exports_dir": str(self.exports_dir),
            "raw_data_dir": str(self.raw_data_dir),
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cache_max_size": self.cache_max_size,
            "export_chunk_size": self.export_chunk_size,
            "export_format_default": self.export_format_default,
            "export_include_abstracts": self.export_include_abstracts,
            "session_cleanup_days": self.session_cleanup_days,
            "auto_save_sessions": self.auto_save_sessions,
            "default_include_reviews": self.default_include_reviews,
            "search_progress_update_interval": self.search_progress_update_interval,
            "memory_limit_mb": self.memory_limit_mb,
            "concurrent_requests": self.concurrent_requests,
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "enable_performance_logging": self.enable_performance_logging,
            "max_upload_size_mb": self.max_upload_size_mb,
            "allowed_file_extensions": self.allowed_file_extensions,
            "page_title": self.page_title,
            "page_icon": self.page_icon,
            "theme_primary_color": self.theme_primary_color,
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def initialize_config(env_file: Optional[Path] = None) -> Config:
    """
    Initialize the global configuration instance.

    Args:
        env_file: Optional path to .env file

    Returns:
        Config instance
    """
    global _config
    _config = Config(env_file)
    return _config


def reset_config() -> None:
    """Reset the global configuration instance (for testing)."""
    global _config
    _config = None
