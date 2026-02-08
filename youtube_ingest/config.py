"""Configuration management for the YouTube content ingest pipeline."""

import os
import logging
from dataclasses import dataclass
from typing import Optional


logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration for the YouTube content ingest pipeline."""
    
    # YouTube API Configuration
    youtube_api_key: str
    
    # Content API Configuration
    content_api_url: str
    content_api_email: str
    content_api_password: str
    content_api_token: Optional[str] = None  # Bearer token (will be obtained via login)
    
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
            content_api_email=os.getenv("CONTENT_API_EMAIL", ""),
            content_api_password=os.getenv("CONTENT_API_PASSWORD", ""),
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
        """Validate configuration with format checks."""
        # Validate YouTube API key
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY is required")
        
        # Check for placeholder values
        placeholder_values = ['your_youtube_api_key_here', 'your_api_key', 'xxx', 'test']
        if self.youtube_api_key.lower() in placeholder_values:
            raise ValueError("YOUTUBE_API_KEY appears to be a placeholder. Please set a real API key.")
        
        # Validate YouTube API key format (should start with 'AIza')
        if not self.youtube_api_key.startswith('AIza'):
            logger.warning("⚠️  YouTube API key format appears unusual (typically starts with 'AIza')")
        
        # Validate Content API URL
        if not self.content_api_url:
            raise ValueError("CONTENT_API_URL is required")
        
        # Validate URL format
        if not self.content_api_url.startswith(('http://', 'https://')):
            raise ValueError("CONTENT_API_URL must be a valid HTTP(S) URL")
        
        # Check for placeholder URLs
        if 'example.com' in self.content_api_url.lower() or 'your-api' in self.content_api_url.lower():
            raise ValueError("CONTENT_API_URL appears to be a placeholder. Please set a real API URL.")
        
        # Validate Content API token
        if not self.content_api_token:
            raise ValueError("CONTENT_API_TOKEN is required")
        
        # Check for placeholder tokens
        token_placeholders = ['your_api_token_here', 'your_token', 'token', 'xxx', 'test']
        if self.content_api_token.lower() in token_placeholders:
            raise ValueError("CONTENT_API_TOKEN appears to be a placeholder. Please set a real API token.")
