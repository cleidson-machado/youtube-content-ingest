"""YouTube search functionality."""

import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import isodate

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Video, SearchQuery
from .config import Config


logger = logging.getLogger(__name__)


class YouTubeSearcher:
    """Handles YouTube video searches using the YouTube Data API."""
    
    def __init__(self, config: Config):
        """Initialize the YouTube searcher.
        
        Args:
            config: Configuration object with YouTube API credentials.
        """
        self.config = config
        self.youtube = build('youtube', 'v3', developerKey=config.youtube_api_key,
                            cache_discovery=False)
        self._category_cache: Dict[str, str] = {}
        self._load_categories()
    
    def _load_categories(self, region_code: str = 'BR') -> None:
        """Load YouTube video categories for a region.
        
        Args:
            region_code: Region code for categories (default: BR for Brazil).
        """
        try:
            categories_request = self.youtube.videoCategories().list(
                part='snippet',
                regionCode=region_code
            )
            categories_response = categories_request.execute()
            
            for item in categories_response.get('items', []):
                category_id = item['id']
                category_title = item['snippet']['title']
                self._category_cache[category_id] = category_title
            
            logger.info(f"Loaded {len(self._category_cache)} video categories for region {region_code}")
        except HttpError as e:
            logger.warning(f"Failed to load video categories: {e}")
    
    def _get_category_name(self, category_id: Optional[str]) -> Optional[str]:
        """Get category name from ID.
        
        Args:
            category_id: YouTube category ID.
            
        Returns:
            Category name or None if not found.
        """
        if not category_id:
            return None
        return self._category_cache.get(category_id)
    
    def search(self, query: SearchQuery) -> List[Video]:
        """Search for videos on YouTube.
        
        Args:
            query: Search query parameters.
            
        Returns:
            List of Video objects from search results.
        """
        try:
            # Prepare search parameters
            search_params = {
                'q': query.query,
                'part': 'snippet',
                'type': 'video',
                'maxResults': query.max_results,
                'order': query.order,
            }
            
            # Add optional parameters
            if query.published_after:
                search_params['publishedAfter'] = query.published_after.isoformat() + 'Z'
            if query.published_before:
                search_params['publishedBefore'] = query.published_before.isoformat() + 'Z'
            if query.region_code:
                search_params['regionCode'] = query.region_code
            if query.relevance_language:
                search_params['relevanceLanguage'] = query.relevance_language
            
            # Execute search
            logger.info(f"Searching YouTube for: {query.query}")
            search_response = self.youtube.search().list(**search_params).execute()
            
            # Extract video IDs
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                logger.warning(f"No videos found for query: {query.query}")
                return []
            
            # Get detailed video information
            videos = self._get_video_details(video_ids)
            logger.info(f"Found {len(videos)} videos for query: {query.query}")
            
            return videos
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise
    
    def search_page(self, query: str, page_token: Optional[str] = None, 
                    max_results: int = 10) -> Tuple[List[Video], Optional[str]]:
        """Search for a single page of videos on YouTube.
        
        Args:
            query: Search query string.
            page_token: Token for pagination (None for first page).
            max_results: Maximum results per page.
            
        Returns:
            Tuple of (list of videos, next page token).
        """
        try:
            logger.info(f"🔍 Searching page of results on YouTube for '{query}'...")
            
            # Execute search
            search_response = self.youtube.search().list(
                q=query,
                part='snippet',
                type='video',
                maxResults=max_results,
                pageToken=page_token
            ).execute()
            
            # Extract video IDs
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                logger.warning(f"No videos found on this page")
                return [], None
            
            # Get detailed video information
            videos = self._get_video_details(video_ids)
            logger.info(f"✓ Search completed. {len(videos)} videos found on this page\n")
            
            next_page_token = search_response.get('nextPageToken')
            
            return videos, next_page_token
            
        except HttpError as e:
            logger.error(f"✗ YouTube API error: {e}")
            raise
    
    def _get_video_details(self, video_ids: List[str]) -> List[Video]:
        """Get detailed information for a list of video IDs.
        
        Args:
            video_ids: List of YouTube video IDs.
            
        Returns:
            List of Video objects with detailed information.
        """
        try:
            videos_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            videos = []
            for item in videos_response.get('items', []):
                video = self._parse_video_item(item)
                videos.append(video)
            
            return videos
            
        except HttpError as e:
            logger.error(f"Error fetching video details: {e}")
            raise
    
    def _parse_video_item(self, item: dict) -> Video:
        """Parse a video item from YouTube API response.
        
        Args:
            item: Video item from YouTube API.
            
        Returns:
            Video object.
        """
        snippet = item['snippet']
        statistics = item.get('statistics', {})
        content_details = item.get('contentDetails', {})
        
        # Parse published date
        published_at = datetime.fromisoformat(
            snippet['publishedAt'].replace('Z', '+00:00')
        )
        
        # Get thumbnail URL (prefer high quality)
        thumbnails = snippet.get('thumbnails', {})
        thumbnail_url = None
        for quality in ['maxres', 'high', 'medium', 'default']:
            if quality in thumbnails:
                thumbnail_url = thumbnails[quality]['url']
                break
        
        # Parse duration from ISO 8601 format to seconds
        duration_iso = content_details.get('duration', 'PT0S')
        duration_seconds = 0
        try:
            duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
        except Exception as e:
            logger.warning(f"Failed to parse duration '{duration_iso}': {e}")
        
        # Get category information
        category_id = snippet.get('categoryId')
        category_name = self._get_category_name(category_id)
        
        # Truncate title if needed (database limit: 1000 chars)
        title = snippet['title']
        if len(title) > 1000:
            title = title[:997] + '...'
        
        # Ensure description exists
        description = snippet.get('description') or "Este vídeo não possui descrição."
        
        return Video(
            video_id=item['id'],
            title=title,
            description=description,
            channel_id=snippet['channelId'],
            channel_title=snippet['channelTitle'],
            published_at=published_at,
            view_count=int(statistics.get('viewCount', 0)),
            like_count=int(statistics.get('likeCount', 0)),
            comment_count=int(statistics.get('commentCount', 0)),
            tags=snippet.get('tags', []),
            category_id=category_id,
            category_name=category_name,
            duration_seconds=duration_seconds,
            duration_iso=duration_iso,
            thumbnail_url=thumbnail_url,
            definition=content_details.get('definition'),
            caption=(content_details.get('caption', 'false') == 'true'),
            default_language=snippet.get('defaultLanguage'),
            default_audio_language=snippet.get('defaultAudioLanguage'),
        )
