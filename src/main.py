"""
YouTube Content Ingest System

This module searches for videos using YouTube Data API v3, enriches metadata,
checks for duplicates against a content API, and posts new videos to the API.
"""

import logging
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import timedelta

import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class YouTubeContentIngest:
    """Handles YouTube video search, metadata enrichment, and API posting."""

    def __init__(
        self,
        youtube_api_key: str,
        content_api_base_url: str,
        content_api_bearer_token: str,
    ) -> None:
        """
        Initialize the YouTube Content Ingest system.

        Args:
            youtube_api_key: YouTube Data API v3 key
            content_api_base_url: Base URL for the content API
            content_api_bearer_token: Bearer token for content API authentication
        """
        self.youtube_api_key = youtube_api_key
        self.content_api_base_url = content_api_base_url.rstrip("/")
        self.content_api_bearer_token = content_api_bearer_token
        self.youtube = None
        self._initialize_youtube_client()

    def _initialize_youtube_client(self) -> None:
        """Initialize the YouTube API client."""
        try:
            self.youtube = build("youtube", "v3", developerKey=self.youtube_api_key)
            logger.info("YouTube API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {e}")
            raise

    def search_videos(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for videos on YouTube.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of video items with basic information

        Raises:
            HttpError: If the YouTube API request fails
        """
        logger.info(f"Searching YouTube for: '{query}' (max results: {max_results})")
        
        try:
            request = self.youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=max_results,
                order="relevance",
            )
            response = request.execute()
            
            videos = response.get("items", [])
            logger.info(f"Found {len(videos)} videos")
            return videos
        
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during video search: {e}")
            raise

    def enrich_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Enrich video metadata with details like views, duration, and tags.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary containing enriched video metadata, or None if fetch fails

        Raises:
            HttpError: If the YouTube API request fails
        """
        logger.debug(f"Enriching metadata for video ID: {video_id}")
        
        try:
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id,
            )
            response = request.execute()
            
            items = response.get("items", [])
            if not items:
                logger.warning(f"No metadata found for video ID: {video_id}")
                return None
            
            video_data = items[0]
            snippet = video_data.get("snippet", {})
            statistics = video_data.get("statistics", {})
            content_details = video_data.get("contentDetails", {})
            
            # Parse duration from ISO 8601 format
            duration_iso = content_details.get("duration", "PT0S")
            duration_seconds = self._parse_duration(duration_iso)
            
            enriched_data = {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "duration_seconds": duration_seconds,
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId", ""),
            }
            
            logger.debug(f"Successfully enriched metadata for: {enriched_data['title']}")
            return enriched_data
        
        except HttpError as e:
            logger.error(f"YouTube API error while enriching video {video_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while enriching video {video_id}: {e}")
            raise

    def _parse_duration(self, duration_iso: str) -> int:
        """
        Parse ISO 8601 duration format to seconds.

        Args:
            duration_iso: Duration in ISO 8601 format (e.g., "PT1H2M10S")

        Returns:
            Duration in seconds
        """
        try:
            # Remove 'PT' prefix
            duration_str = duration_iso.replace("PT", "")
            
            hours = 0
            minutes = 0
            seconds = 0
            
            # Parse hours
            if "H" in duration_str:
                hours_str, duration_str = duration_str.split("H")
                hours = int(hours_str)
            
            # Parse minutes
            if "M" in duration_str:
                minutes_str, duration_str = duration_str.split("M")
                minutes = int(minutes_str)
            
            # Parse seconds
            if "S" in duration_str:
                seconds_str = duration_str.replace("S", "")
                seconds = int(seconds_str)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds
        
        except Exception as e:
            logger.warning(f"Failed to parse duration '{duration_iso}': {e}")
            return 0

    def check_duplicate(self, video_id: str) -> bool:
        """
        Check if a video already exists in the content API.

        Args:
            video_id: YouTube video ID

        Returns:
            True if video exists (is duplicate), False otherwise

        Raises:
            requests.RequestException: If the API request fails
        """
        logger.debug(f"Checking for duplicate video ID: {video_id}")
        
        try:
            url = f"{self.content_api_base_url}/contents"
            headers = {
                "Authorization": f"Bearer {self.content_api_bearer_token}",
                "Content-Type": "application/json",
            }
            params = {"video_id": video_id}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                contents = response.json()
                # Check if any content matches this video_id
                if isinstance(contents, list):
                    is_duplicate = any(
                        content.get("video_id") == video_id for content in contents
                    )
                else:
                    # If response is a dict with a 'data' or 'contents' key
                    data = contents.get("data", contents.get("contents", []))
                    is_duplicate = any(
                        content.get("video_id") == video_id for content in data
                    )
                
                if is_duplicate:
                    logger.info(f"Video {video_id} already exists (duplicate)")
                else:
                    logger.debug(f"Video {video_id} is not a duplicate")
                
                return is_duplicate
            
            elif response.status_code == 404:
                # No duplicates found
                logger.debug(f"Video {video_id} is not a duplicate (404)")
                return False
            
            else:
                logger.warning(
                    f"Unexpected status code {response.status_code} "
                    f"when checking duplicate for {video_id}"
                )
                return False
        
        except requests.RequestException as e:
            logger.error(f"Error checking duplicate for video {video_id}: {e}")
            raise

    def post_content(self, video_data: Dict[str, Any]) -> bool:
        """
        Post video content to the content API.

        Args:
            video_data: Enriched video metadata dictionary

        Returns:
            True if posted successfully, False otherwise

        Raises:
            requests.RequestException: If the API request fails
        """
        logger.info(f"Posting content: {video_data.get('title', 'Unknown')}")
        
        try:
            url = f"{self.content_api_base_url}/contents"
            headers = {
                "Authorization": f"Bearer {self.content_api_bearer_token}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(url, json=video_data, headers=headers, timeout=10)
            
            if response.status_code in (200, 201):
                logger.info(
                    f"Successfully posted video: {video_data.get('video_id')}"
                )
                return True
            else:
                logger.error(
                    f"Failed to post video {video_data.get('video_id')}: "
                    f"Status {response.status_code}, Response: {response.text}"
                )
                return False
        
        except requests.RequestException as e:
            logger.error(
                f"Error posting video {video_data.get('video_id')}: {e}"
            )
            raise

    def process_videos(self, query: str, max_results: int = 10) -> Dict[str, int]:
        """
        Main processing function: search, enrich, check duplicates, and post.

        Args:
            query: Search query string
            max_results: Maximum number of results to process

        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"Starting video processing for query: '{query}'")
        
        stats = {
            "searched": 0,
            "enriched": 0,
            "duplicates": 0,
            "posted": 0,
            "errors": 0,
        }
        
        try:
            # Step 1: Search videos
            videos = self.search_videos(query, max_results)
            stats["searched"] = len(videos)
            
            for video in videos:
                video_id = video.get("id", {}).get("videoId")
                
                if not video_id:
                    logger.warning("Skipping video with no ID")
                    stats["errors"] += 1
                    continue
                
                try:
                    # Step 2: Enrich metadata
                    enriched_data = self.enrich_video_metadata(video_id)
                    
                    if not enriched_data:
                        logger.warning(f"Failed to enrich video {video_id}")
                        stats["errors"] += 1
                        continue
                    
                    stats["enriched"] += 1
                    
                    # Step 3: Check for duplicates
                    if self.check_duplicate(video_id):
                        stats["duplicates"] += 1
                        continue
                    
                    # Step 4: Post to content API
                    if self.post_content(enriched_data):
                        stats["posted"] += 1
                    else:
                        stats["errors"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing video {video_id}: {e}")
                    stats["errors"] += 1
                    continue
            
            logger.info(
                f"Processing complete. Stats: {stats['searched']} searched, "
                f"{stats['enriched']} enriched, {stats['duplicates']} duplicates, "
                f"{stats['posted']} posted, {stats['errors']} errors"
            )
            
            return stats
        
        except Exception as e:
            logger.error(f"Fatal error during video processing: {e}")
            raise


def main() -> int:
    """
    Main entry point for the YouTube Content Ingest system.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("YouTube Content Ingest system starting")
    
    # Load configuration from environment variables
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    content_api_base_url = os.getenv("CONTENT_API_BASE_URL")
    content_api_bearer_token = os.getenv("CONTENT_API_BEARER_TOKEN")
    search_query = os.getenv("SEARCH_QUERY", "python programming")
    max_results = int(os.getenv("MAX_RESULTS", "10"))
    
    # Validate required configuration
    if not youtube_api_key:
        logger.error("YOUTUBE_API_KEY environment variable is required")
        return 1
    
    if not content_api_base_url:
        logger.error("CONTENT_API_BASE_URL environment variable is required")
        return 1
    
    if not content_api_bearer_token:
        logger.error("CONTENT_API_BEARER_TOKEN environment variable is required")
        return 1
    
    try:
        # Initialize and run the ingest system
        ingest = YouTubeContentIngest(
            youtube_api_key=youtube_api_key,
            content_api_base_url=content_api_base_url,
            content_api_bearer_token=content_api_bearer_token,
        )
        
        stats = ingest.process_videos(query=search_query, max_results=max_results)
        
        # Return success if we processed at least some videos
        if stats["searched"] > 0:
            logger.info("YouTube Content Ingest completed successfully")
            return 0
        else:
            logger.warning("No videos were processed")
            return 1
    
    except Exception as e:
        logger.error(f"YouTube Content Ingest failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
