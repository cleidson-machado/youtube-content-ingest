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
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Authenticate and get token
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with the API and obtain access token."""
        auth_url = f"{self.base_url}/auth/login"
        auth_payload = {
            "email": self.config.content_api_email,
            "password": self.config.content_api_password
        }
        
        logger.info(f"🔐 Authenticating with API at {auth_url}")
        
        try:
            response = self.session.post(auth_url, json=auth_payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token') or data.get('access_token') or data.get('accessToken')
                
                if not token:
                    raise ValueError(f"Authentication response missing token field. Response: {data}")
                
                # Set Bearer token in session headers
                self.session.headers.update({'Authorization': f'Bearer {token}'})
                logger.info("✅ Authentication successful")
            else:
                raise ValueError(
                    f"Authentication failed with status {response.status_code}: {response.text}"
                )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Authentication request failed: {e}")
    
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
        logger.info(f"   ├─ Published At: {video.published_at.isoformat()}")
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
        url = f"{self.base_url}/contents"  # Use /contents endpoint
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
        """Fetch existing video URLs from the content API using pagination.
        
        Returns:
            Set of existing video URLs.
        """
        all_urls = set()
        page = 0
        page_size = 50  # Buscar 50 itens por página (padrão da API REST)
        total_pages = None
        
        try:
            logger.info(f"🔍 Fetching existing URLs from endpoint: {self.base_url}")
            
            while True:
                # Usar endpoint paginado /contents/paged
                url = f"{self.base_url}/contents/paged?page={page}&size={page_size}"
                
                response = self.session.get(url, timeout=10)
                
                if not response.ok:
                    if response.status_code in [401, 403]:
                        logger.warning("⚠️  AUTHENTICATION ERROR: Check if API token is correct")
                    logger.warning(
                        f"✗ Failed to fetch page {page}. Status: {response.status_code}, "
                        f"Response: {response.text}"
                    )
                    break
                
                data = response.json()
                
                # Extrair informações de paginação (adaptado à API)
                if total_pages is None:
                    total_pages = data.get('totalPages', 1)
                    total_items = data.get('totalItems', 0)
                    logger.info(f"📊 Total items: {total_items}, Total pages: {total_pages}")
                
                # Extrair items da página atual
                items = data.get('content', [])
                
                if not items:
                    logger.info(f"  ℹ️  Page {page + 1}: No items found")
                    break
                
                # Adicionar URLs ao set (campo agora é videoUrl)
                page_urls = {item['videoUrl'] for item in items if 'videoUrl' in item}
                all_urls.update(page_urls)
                
                current_page = data.get('currentPage', page)
                logger.info(f"  ✓ Page {current_page + 1}/{total_pages}: {len(page_urls)} URLs fetched")
                
                # Verificar se há mais páginas
                # A API retorna totalPages, então se currentPage + 1 >= totalPages, acabou
                if current_page + 1 >= total_pages:
                    break
                
                page += 1
                
                # Limite de segurança
                if page > 1000:
                    logger.warning("⚠️  Safety limit reached (1000 pages)")
                    break
            
            logger.info(f"✅ Total: {len(all_urls)} existing URLs in database\n")
            return all_urls
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"✗ Connection error while fetching existing URLs: {e}")
            return all_urls  # Retorna o que conseguiu buscar até agora
        except Exception as e:
            logger.error(f"✗ Unexpected error while fetching existing URLs: {e}")
            return all_urls
