"""Main entry point for the YouTube content ingest pipeline."""

import logging
import sys
from dotenv import load_dotenv

from youtube_ingest.config import Config
from youtube_ingest.pipeline import Pipeline


def setup_logging(log_level: str) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(message)s',  # Simplified format for cleaner console output
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def main():
    """Main function to run the YouTube content ingest pipeline."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Load configuration from environment
    config = Config.from_env()
    
    # Setup logging
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        config.validate()
        logger.info("Configuration validated successfully\n")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        sys.exit(1)
    
    try:
        # Initialize and run pipeline with incremental search
        pipeline = Pipeline(config)
        results = pipeline.run_incremental_search(
            search_query=config.search_query,
            target_count=config.target_new_videos,
            max_pages=config.max_pages_to_search
        )
        
        # Log results summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"  Pages Searched: {results.get('pages_searched', 0)}")
        logger.info(f"  New Videos Found: {results['videos_found']}")
        logger.info(f"  Videos Posted: {results['videos_posted']}")
        logger.info(f"  Videos Failed: {results['videos_failed']}")
        
        if results['errors']:
            logger.warning(f"\n  ⚠️  Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                logger.warning(f"    - {error}")
        
        logger.info("=" * 80 + "\n")
        
        # Exit with appropriate code
        if results['videos_failed'] > 0 or results['errors']:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
