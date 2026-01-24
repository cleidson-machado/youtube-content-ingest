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
        
        # Load existing video IDs from API for deduplication
        try:
            existing_ids = self.api_client.get_existing_video_ids()
            self.deduplicator.add_existing_ids(existing_ids)
        except Exception as e:
            logger.warning(f"Failed to load existing video IDs: {e}")
        
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
