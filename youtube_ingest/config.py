"""Configuration management for the YouTube content ingest pipeline."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration for the YouTube content ingest pipeline."""
    
    # YouTube API Configuration
    youtube_api_key: str
    
    # Content API Configuration
    content_api_url: str
    content_api_key: Optional[str] = None
    
    # Pipeline Configuration
    max_results_per_query: int = 50
    enable_deduplication: bool = True
    enable_enrichment: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        # Parse max_results_per_query with error handling
        max_results_str = os.getenv("MAX_RESULTS_PER_QUERY", "50")
        try:
            max_results = int(max_results_str)
        except ValueError:
            raise ValueError(
                f"MAX_RESULTS_PER_QUERY must be a valid integer, got: {max_results_str}"
            )
        
        return cls(
            youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
            content_api_url=os.getenv("CONTENT_API_URL", ""),
            content_api_key=os.getenv("CONTENT_API_KEY"),
            max_results_per_query=max_results,
            enable_deduplication=os.getenv("ENABLE_DEDUPLICATION", "true").lower() == "true",
            enable_enrichment=os.getenv("ENABLE_ENRICHMENT", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY is required")
        if not self.content_api_url:
            raise ValueError("CONTENT_API_URL is required")
