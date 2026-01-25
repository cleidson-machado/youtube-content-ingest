"""Deduplication functionality for video catalog."""

import logging
from typing import List, Set

from .models import Video
from .config import Config


logger = logging.getLogger(__name__)


class Deduplicator:
    """Handles deduplication of videos against existing catalog."""
    
    def __init__(self, config: Config, existing_urls: Set[str] = None):
        """Initialize the deduplicator.
        
        Args:
            config: Configuration object.
            existing_urls: Set of video URLs that already exist in the catalog.
        """
        self.config = config
        self.existing_urls = existing_urls or set()
    
    def deduplicate(self, videos: List[Video]) -> List[Video]:
        """Remove duplicate videos from the list.
        
        Args:
            videos: List of videos to deduplicate.
            
        Returns:
            List of unique videos not in the existing catalog.
        """
        if not self.config.enable_deduplication:
            logger.info("Deduplication is disabled, skipping")
            return videos
        
        logger.info(f"Deduplicating {len(videos)} videos against catalog of {len(self.existing_urls)} URLs")
        
        unique_videos = []
        duplicate_count = 0
        
        for video in videos:
            video_url = f"https://www.youtube.com/watch?v={video.video_id}"
            
            if video_url not in self.existing_urls:
                unique_videos.append(video)
                self.existing_urls.add(video_url)
            else:
                duplicate_count += 1
                logger.debug(f"Duplicate video found: {video.video_id} - {video.title}")
        
        logger.info(f"Found {duplicate_count} duplicates, {len(unique_videos)} unique videos")
        return unique_videos
    
    def add_existing_urls(self, urls: Set[str]) -> None:
        """Add URLs to the existing catalog.
        
        Args:
            urls: Set of URLs to add.
        """
        self.existing_urls.update(urls)
        logger.info(f"Added {len(urls)} URLs to catalog")
