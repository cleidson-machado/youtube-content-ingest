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
    category_name: Optional[str] = None
    duration_seconds: int = 0
    duration_iso: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Video quality metadata
    definition: Optional[str] = None  # 'hd' or 'sd'
    caption: bool = False
    default_language: Optional[str] = None
    default_audio_language: Optional[str] = None
    
    # Enriched data
    enriched_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert video to dictionary format for API submission."""
        # Convert tags list to comma-separated string
        tags_string = ', '.join(self.tags) if self.tags else None
        
        # Format publishedAt without timezone info (API expects local datetime)
        published_at_str = self.published_at.replace(tzinfo=None).isoformat()
        
        return {
            "title": self.title,
            "description": self.description,
            "url": f"https://www.youtube.com/watch?v={self.video_id}",
            "channelName": self.channel_title,
            "type": "VIDEO",
            "thumbnailUrl": self.thumbnail_url,
            "categoryId": self.category_id,
            "categoryName": self.category_name,
            "tags": tags_string,
            "durationSeconds": self.duration_seconds,
            "durationIso": self.duration_iso,
            "definition": self.definition,
            "caption": self.caption,
            "viewCount": self.view_count,
            "likeCount": self.like_count,
            "commentCount": self.comment_count,
            "defaultLanguage": self.default_language,
            "defaultAudioLanguage": self.default_audio_language,
            "publishedAt": published_at_str,
        }
