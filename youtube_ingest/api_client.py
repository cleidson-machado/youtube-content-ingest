"""Content API client for posting video records."""

import logging
from typing import List, Dict, Any
import requests

from .models import Video
from .config import Config


logger = logging.getLogger(__name__)


class APIClient:
    """Client for interacting with the content API."""
    
    def __init__(self, config: Config):
        """Initialize the API client.
        
        Args:
            config: Configuration object with API credentials.
        """
        self.config = config
        self.base_url = config.content_api_url.rstrip('/')
        self.session = requests.Session()
        
        # Set up authentication headers if API key is provided
        if config.content_api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {config.content_api_key}',
                'Content-Type': 'application/json',
            })
    
    def post_videos(self, videos: List[Video]) -> Dict[str, Any]:
        """Post videos to the content API.
        
        Args:
            videos: List of videos to post.
            
        Returns:
            API response with posting results.
        """
        if not videos:
            logger.info("No videos to post")
            return {"success": True, "posted": 0, "failed": 0}
        
        logger.info(f"Posting {len(videos)} videos to content API")
        
        results = {
            "success": True,
            "posted": 0,
            "failed": 0,
            "errors": []
        }
        
        for video in videos:
            try:
                response = self._post_single_video(video)
                if response.get('success'):
                    results['posted'] += 1
                    logger.debug(f"Successfully posted video: {video.video_id}")
                else:
                    results['failed'] += 1
                    error_msg = response.get('error', 'Unknown error')
                    results['errors'].append({
                        'video_id': video.video_id,
                        'error': error_msg
                    })
                    logger.warning(f"Failed to post video {video.video_id}: {error_msg}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'video_id': video.video_id,
                    'error': str(e)
                })
                logger.error(f"Error posting video {video.video_id}: {e}")
        
        if results['failed'] > 0:
            results['success'] = False
        
        logger.info(
            f"Posted {results['posted']} videos successfully, "
            f"{results['failed']} failed"
        )
        
        return results
    
    def _post_single_video(self, video: Video) -> Dict[str, Any]:
        """Post a single video to the API.
        
        Args:
            video: Video to post.
            
        Returns:
            API response.
        """
        url = f"{self.base_url}/videos"
        data = video.to_dict()
        
        try:
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_existing_video_ids(self) -> set:
        """Fetch existing video IDs from the content API.
        
        Returns:
            Set of existing video IDs.
        """
        url = f"{self.base_url}/videos/ids"
        
        try:
            logger.info("Fetching existing video IDs from API")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            video_ids = set(data.get('video_ids', []))
            logger.info(f"Retrieved {len(video_ids)} existing video IDs")
            
            return video_ids
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch existing video IDs: {e}")
            return set()
