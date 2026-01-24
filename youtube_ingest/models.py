"""Data models for the YouTube content ingest pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class SearchQuery:
    """Represents a YouTube search query."""
    
    query: str
    max_results: int = 10
    order: str = "relevance"  # relevance, date, rating, viewCount, title
    published_after: Optional[datetime] = None
    published_before: Optional[datetime] = None
    region_code: Optional[str] = None
    relevance_language: Optional[str] = None


@dataclass
class Video:
    """Represents a YouTube video with enriched metadata."""
    
    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    published_at: datetime
    
    # Statistics
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    category_id: Optional[str] = None
    duration: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Enriched data
    enriched_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert video to dictionary format."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "published_at": self.published_at.isoformat(),
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "tags": self.tags,
            "category_id": self.category_id,
            "duration": self.duration,
            "thumbnail_url": self.thumbnail_url,
            "enriched_metadata": self.enriched_metadata,
        }
