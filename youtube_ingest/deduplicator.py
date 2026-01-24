"""Deduplication functionality for video catalog."""

import logging
from typing import List, Set

from .models import Video
from .config import Config


logger = logging.getLogger(__name__)


class Deduplicator:
    """Handles deduplication of videos against existing catalog."""
    
    def __init__(self, config: Config, existing_video_ids: Set[str] = None):
        """Initialize the deduplicator.
        
        Args:
            config: Configuration object.
            existing_video_ids: Set of video IDs that already exist in the catalog.
        """
        self.config = config
        self.existing_video_ids = existing_video_ids or set()
    
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
        
        logger.info(f"Deduplicating {len(videos)} videos against catalog of {len(self.existing_video_ids)}")
        
        unique_videos = []
        duplicate_count = 0
        
        for video in videos:
            if video.video_id not in self.existing_video_ids:
                unique_videos.append(video)
                self.existing_video_ids.add(video.video_id)
            else:
                duplicate_count += 1
                logger.debug(f"Duplicate video found: {video.video_id} - {video.title}")
        
        logger.info(f"Found {duplicate_count} duplicates, {len(unique_videos)} unique videos")
        return unique_videos
    
    def add_existing_ids(self, video_ids: Set[str]) -> None:
        """Add video IDs to the existing catalog.
        
        Args:
            video_ids: Set of video IDs to add.
        """
        self.existing_video_ids.update(video_ids)
        logger.info(f"Added {len(video_ids)} video IDs to catalog")
