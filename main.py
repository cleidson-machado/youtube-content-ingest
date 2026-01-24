"""Main entry point for the YouTube content ingest pipeline."""

import logging
import sys
from datetime import datetime, timedelta

from youtube_ingest.config import Config
from youtube_ingest.models import SearchQuery
from youtube_ingest.pipeline import Pipeline


def setup_logging(log_level: str) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def main():
    """Main function to run the YouTube content ingest pipeline."""
    # Load configuration from environment
    config = Config.from_env()
    
    # Setup logging
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Define search queries
    # In a real implementation, these might come from a config file or database
    queries = [
        SearchQuery(
            query="artificial intelligence tutorial",
            max_results=10,
            order="relevance",
            published_after=datetime.now() - timedelta(days=30)
        ),
        SearchQuery(
            query="machine learning explained",
            max_results=10,
            order="relevance",
            published_after=datetime.now() - timedelta(days=30)
        ),
    ]
    
    logger.info(f"Starting pipeline with {len(queries)} search queries")
    
    try:
        # Initialize and run pipeline
        pipeline = Pipeline(config)
        results = pipeline.run(queries)
        
        # Log results
        logger.info("=" * 50)
        logger.info("Pipeline Execution Summary:")
        logger.info(f"  Queries Processed: {results['queries_processed']}")
        logger.info(f"  Videos Found: {results['videos_found']}")
        logger.info(f"  Unique Videos: {results['videos_unique']}")
        logger.info(f"  Videos Posted: {results['videos_posted']}")
        logger.info(f"  Videos Failed: {results['videos_failed']}")
        
        if results['errors']:
            logger.warning(f"  Errors: {len(results['errors'])}")
            for error in results['errors']:
                logger.warning(f"    - {error}")
        
        logger.info("=" * 50)
        
        # Exit with appropriate code
        if results['videos_failed'] > 0 or results['errors']:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
