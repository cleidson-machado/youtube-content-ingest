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
    content_api_token: Optional[str] = None  # Bearer token for authentication
    
    # Search Configuration
    search_query: str = "tipos de visto para portugal"
    target_new_videos: int = 10
    max_pages_to_search: int = 10
    max_results_per_page: int = 10
    
    # Pipeline Configuration
    enable_deduplication: bool = True
    enable_enrichment: bool = False  # Disable by default for simplicity
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        # Parse integer values with error handling
        target_new_videos_str = os.getenv("TARGET_NEW_VIDEOS", "10")
        max_pages_str = os.getenv("MAX_PAGES_TO_SEARCH", "10")
        max_results_per_page_str = os.getenv("MAX_RESULTS_PER_PAGE", "10")
        
        try:
            target_new_videos = int(target_new_videos_str)
            max_pages = int(max_pages_str)
            max_results_per_page = int(max_results_per_page_str)
        except ValueError as e:
            raise ValueError(f"Configuration parsing error: {e}")
        
        return cls(
            youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
            content_api_url=os.getenv("CONTENT_API_URL", ""),
            content_api_token=os.getenv("CONTENT_API_TOKEN"),
            search_query=os.getenv("SEARCH_QUERY", "tipos de visto para portugal"),
            target_new_videos=target_new_videos,
            max_pages_to_search=max_pages,
            max_results_per_page=max_results_per_page,
            enable_deduplication=os.getenv("ENABLE_DEDUPLICATION", "true").lower() == "true",
            enable_enrichment=os.getenv("ENABLE_ENRICHMENT", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY is required")
        if not self.content_api_url:
            raise ValueError("CONTENT_API_URL is required")
        if not self.content_api_token:
            raise ValueError("CONTENT_API_TOKEN is required")
