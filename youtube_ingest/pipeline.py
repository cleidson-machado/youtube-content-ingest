"""Main pipeline orchestration for YouTube content ingest."""

import logging
from typing import List

from .config import Config
from .models import SearchQuery, Video
from .youtube_search import YouTubeSearcher
from .metadata_enricher import MetadataEnricher
from .deduplicator import Deduplicator
from .api_client import APIClient


logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the YouTube content ingest pipeline."""
    
    def __init__(self, config: Config):
        """Initialize the pipeline with configuration.
        
        Args:
            config: Configuration object.
        """
        self.config = config
        self.searcher = YouTubeSearcher(config)
        self.enricher = MetadataEnricher(config)
        self.api_client = APIClient(config)
        
        # Initialize deduplicator without existing IDs (loaded lazily in run())
        self.deduplicator = Deduplicator(config)
        
        logger.info("Pipeline initialized")
    
    def run(self, queries: List[SearchQuery]) -> dict:
        """Run the full pipeline for a list of search queries.
        
        Args:
            queries: List of search queries to process.
            
        Returns:
            Dictionary with pipeline execution results.
        """
        logger.info(f"Starting pipeline with {len(queries)} queries")
        
        # Load existing video URLs from API for deduplication
        try:
            existing_urls = self.api_client.get_existing_urls()
            self.deduplicator.add_existing_urls(existing_urls)
        except Exception as e:
            logger.warning(f"Failed to load existing video URLs: {e}")
        
        results = {
            "queries_processed": 0,
            "videos_found": 0,
            "videos_unique": 0,
            "videos_posted": 0,
            "videos_failed": 0,
            "errors": []
        }
        
        all_videos = []
        
        # Step 1: Search YouTube for videos
        for query in queries:
            try:
                videos = self.searcher.search(query)
                all_videos.extend(videos)
                results["queries_processed"] += 1
                results["videos_found"] += len(videos)
            except Exception as e:
                logger.error(f"Error searching for query '{query.query}': {e}")
                results["errors"].append({
                    "stage": "search",
                    "query": query.query,
                    "error": str(e)
                })
        
        if not all_videos:
            logger.warning("No videos found from any query")
            return results
        
        # Step 2: Deduplicate videos
        try:
            unique_videos = self.deduplicator.deduplicate(all_videos)
            results["videos_unique"] = len(unique_videos)
        except Exception as e:
            logger.error(f"Error during deduplication: {e}")
            results["errors"].append({
                "stage": "deduplication",
                "error": str(e)
            })
            unique_videos = all_videos
        
        if not unique_videos:
            logger.info("No new unique videos to process")
            return results
        
        # Step 3: Enrich metadata
        try:
            enriched_videos = self.enricher.enrich(unique_videos)
        except Exception as e:
            logger.error(f"Error during enrichment: {e}")
            results["errors"].append({
                "stage": "enrichment",
                "error": str(e)
            })
            enriched_videos = unique_videos
        
        # Step 4: Post to content API
        try:
            post_results = self.api_client.post_videos(enriched_videos)
            results["videos_posted"] = post_results["posted"]
            results["videos_failed"] = post_results["failed"]
            if post_results.get("errors"):
                results["errors"].extend([
                    {"stage": "api_post", **error}
                    for error in post_results["errors"]
                ])
        except Exception as e:
            logger.error(f"Error posting videos to API: {e}")
            results["errors"].append({
                "stage": "api_post",
                "error": str(e)
            })
        
        logger.info(
            f"Pipeline completed: {results['videos_posted']} videos posted, "
            f"{results['videos_failed']} failed"
        )
        
        return results
    
    def run_incremental_search(self, search_query: str, target_count: int, max_pages: int) -> dict:
        """Run incremental search until target count of new videos is reached.
        
        This method searches YouTube page by page, deduplicating as it goes,
        until either the target count of new videos is reached or max pages searched.
        
        Args:
            search_query: The YouTube search query string.
            target_count: Number of new videos to find before stopping.
            max_pages: Maximum number of pages to search.
            
        Returns:
            Dictionary with pipeline execution results.
        """
        logger.info("🚀 STARTING INCREMENTAL SEARCH FOR NEW VIDEOS")
        logger.info("=" * 80)
        logger.info(f"Search query: '{search_query}'")
        logger.info(f"Target: {target_count} new videos")
        logger.info(f"Max pages: {max_pages}")
        
        # Load existing video URLs from API for deduplication
        try:
            existing_urls = self.api_client.get_existing_urls()
            self.deduplicator.add_existing_urls(existing_urls)
        except Exception as e:
            logger.warning(f"Failed to load existing video URLs: {e}")
            existing_urls = set()
        
        new_videos = []
        pages_searched = 0
        next_page_token = None
        
        # Search incrementally page by page
        while len(new_videos) < target_count and pages_searched < max_pages:
            try:
                # Search current page
                videos, next_page_token = self.searcher.search_page(
                    query=search_query,
                    page_token=next_page_token
                )
                pages_searched += 1
                
                # Deduplicate and collect new videos
                for video in videos:
                    video_url = f"https://www.youtube.com/watch?v={video.video_id}"
                    
                    if video_url not in existing_urls:
                        # Also check against current batch
                        if video_url not in {f"https://www.youtube.com/watch?v={v.video_id}" for v in new_videos}:
                            logger.info(f"  ✓ New video found: {video.title[:60]}...")
                            new_videos.append(video)
                            
                            if len(new_videos) >= target_count:
                                break
                
                # Check if there are more pages
                if not next_page_token:
                    logger.info("\n⚠️  No more result pages available on YouTube for this search")
                    break
                    
            except Exception as e:
                logger.error(f"Error during search on page {pages_searched}: {e}")
                break
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"✅ SEARCH COMPLETED: {len(new_videos)} NEW VIDEOS FOUND")
        logger.info("=" * 80)
        
        # Prepare results
        results = {
            "queries_processed": 1,
            "pages_searched": pages_searched,
            "videos_found": len(new_videos),
            "videos_unique": len(new_videos),
            "videos_posted": 0,
            "videos_failed": 0,
            "errors": []
        }
        
        if not new_videos:
            logger.info("\n📭 No new videos to send")
            return results
        
        # Enrich metadata if enabled
        try:
            enriched_videos = self.enricher.enrich(new_videos)
        except Exception as e:
            logger.error(f"Error during enrichment: {e}")
            results["errors"].append({
                "stage": "enrichment",
                "error": str(e)
            })
            enriched_videos = new_videos
        
        # Post to content API
        try:
            post_results = self.api_client.post_videos(enriched_videos)
            results["videos_posted"] = post_results["posted"]
            results["videos_failed"] = post_results["failed"]
            if post_results.get("errors"):
                results["errors"].extend([
                    {"stage": "api_post", **error}
                    for error in post_results["errors"]
                ])
        except Exception as e:
            logger.error(f"Error posting videos to API: {e}")
            results["errors"].append({
                "stage": "api_post",
                "error": str(e)
            })
        
        return results
