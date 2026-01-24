"""YouTube search functionality."""

import logging
from typing import List, Optional
from datetime import datetime

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
                'maxResults': min(query.max_results, self.config.max_results_per_query),
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
        
        return Video(
            video_id=item['id'],
            title=snippet['title'],
            description=snippet['description'],
            channel_id=snippet['channelId'],
            channel_title=snippet['channelTitle'],
            published_at=published_at,
            view_count=int(statistics.get('viewCount', 0)),
            like_count=int(statistics.get('likeCount', 0)),
            comment_count=int(statistics.get('commentCount', 0)),
            tags=snippet.get('tags', []),
            category_id=snippet.get('categoryId'),
            duration=content_details.get('duration'),
            thumbnail_url=thumbnail_url,
        )
