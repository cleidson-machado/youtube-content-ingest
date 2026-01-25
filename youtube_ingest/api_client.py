"""Content API client for posting video records."""

import logging
from typing import List, Dict, Any, Set
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
        
        # Set up authentication headers if API token is provided
        if config.content_api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {config.content_api_token}',
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
        logger.info("=" * 80)
        
        results = {
            "success": True,
            "posted": 0,
            "failed": 0,
            "errors": []
        }
        
        for video in videos:
            try:
                # Log video details before posting
                self._log_video_details(video)
                
                response = self._post_single_video(video)
                if response.get('success'):
                    results['posted'] += 1
                    logger.info(f"   ✓ Created successfully!")
                else:
                    results['failed'] += 1
                    error_msg = response.get('error', 'Unknown error')
                    results['errors'].append({
                        'video_id': video.video_id,
                        'error': error_msg
                    })
                    logger.warning(f"   ✗ Error: {error_msg}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'video_id': video.video_id,
                    'error': str(e)
                })
                logger.error(f"   ✗ Exception: {e}")
            
            logger.info("-" * 80)
        
        if results['failed'] > 0:
            results['success'] = False
        
        logger.info(
            f"\n✅ Process completed: {results['posted']} videos posted successfully, "
            f"{results['failed']} failed"
        )
        
        return results
    
    def _log_video_details(self, video: Video) -> None:
        """Log video details in a user-friendly format.
        
        Args:
            video: Video object to log.
        """
        title_display = video.title[:70] if len(video.title) > 70 else video.title
        logger.info(f"\n📹 Video: {title_display}")
        logger.info(f"   ID: {video.video_id}")
        logger.info(f"   Channel: {video.channel_title}")
        logger.info(f"\n   📊 COMPLETE DATA (SENDING TO API):")
        logger.info(f"   ├─ Category: {video.category_name or 'N/A'} (ID: {video.category_id or 'N/A'})")
        
        # Display tags preview
        tags_display = ', '.join(video.tags) if video.tags else 'No tags'
        if len(tags_display) > 100:
            tags_display = tags_display[:100] + '...'
        logger.info(f"   ├─ Tags: {tags_display}")
        
        logger.info(f"   ├─ Duration: {video.duration_seconds} seconds ({video.duration_iso})")
        logger.info(f"   ├─ Definition: {video.definition or 'N/A'}")
        logger.info(f"   ├─ Caption: {video.caption}")
        logger.info(f"   ├─ Views: {video.view_count:,}")
        logger.info(f"   ├─ Likes: {video.like_count:,}")
        logger.info(f"   ├─ Comments: {video.comment_count:,}")
        logger.info(f"   ├─ Language: {video.default_language or 'N/A'}")
        logger.info(f"   └─ Audio Language: {video.default_audio_language or 'N/A'}")
    
    def _post_single_video(self, video: Video) -> Dict[str, Any]:
        """Post a single video to the API.
        
        Args:
            video: Video to post.
            
        Returns:
            API response.
        """
        url = self.base_url  # Endpoint expects base URL directly
        data = video.to_dict()
        
        try:
            response = self.session.post(url, json=data, timeout=10)
            
            # Check for 201 Created status
            if response.status_code == 201:
                return {"success": True, "data": response.json() if response.text else None}
            else:
                return {
                    "success": False, 
                    "error": f"Status {response.status_code}: {response.text}"
                }
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_existing_urls(self) -> Set[str]:
        """Fetch existing video URLs from the content API.
        
        Returns:
            Set of existing video URLs.
        """
        url = self.base_url
        
        try:
            logger.info(f"🔍 Fetching existing URLs from endpoint: {url}")
            response = self.session.get(url, timeout=10)
            
            if response.ok:
                existing_data = response.json()
                
                # Handle both list and object-with-items formats
                items = existing_data if isinstance(existing_data, list) else existing_data.get('items', [])
                
                urls = {item['url'] for item in items if 'url' in item}
                logger.info(f"✓ Found {len(urls)} existing URLs in database\n")
                
                return urls
            else:
                logger.warning(
                    f"✗ Failed to fetch existing URLs. Status: {response.status_code}, "
                    f"Response: {response.text}"
                )
                if response.status_code in [401, 403]:
                    logger.warning("⚠️  AUTHENTICATION ERROR: Check if API token is correct")
                return set()
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"✗ Connection error while fetching existing URLs: {e}")
            return set()
