"""YouTube Content Ingest Pipeline.

Automated YouTube discovery and ingest pipeline that searches YouTube,
enriches video metadata, deduplicates against your catalog, and posts
new video records to a content API.
"""

__version__ = "0.1.0"

from .pipeline import Pipeline
from .models import Video, SearchQuery

__all__ = ["Pipeline", "Video", "SearchQuery"]
