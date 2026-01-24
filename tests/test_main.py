"""
Tests for YouTube Content Ingest System
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from googleapiclient.errors import HttpError
import requests

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import YouTubeContentIngest


@pytest.fixture
def ingest_system():
    """Create a YouTubeContentIngest instance for testing."""
    with patch('main.build'):
        ingest = YouTubeContentIngest(
            youtube_api_key="test_youtube_key",
            content_api_base_url="https://api.test.com",
            content_api_bearer_token="test_bearer_token",
        )
        yield ingest


class TestYouTubeContentIngest:
    """Test cases for YouTubeContentIngest class."""

    def test_initialization(self, ingest_system):
        """Test that the system initializes correctly."""
        assert ingest_system.youtube_api_key == "test_youtube_key"
        assert ingest_system.content_api_base_url == "https://api.test.com"
        assert ingest_system.content_api_bearer_token == "test_bearer_token"

    def test_parse_duration_full(self, ingest_system):
        """Test duration parsing with hours, minutes, and seconds."""
        duration = ingest_system._parse_duration("PT1H2M10S")
        assert duration == 3730  # 1*3600 + 2*60 + 10

    def test_parse_duration_minutes_seconds(self, ingest_system):
        """Test duration parsing with minutes and seconds."""
        duration = ingest_system._parse_duration("PT5M30S")
        assert duration == 330  # 5*60 + 30

    def test_parse_duration_seconds_only(self, ingest_system):
        """Test duration parsing with seconds only."""
        duration = ingest_system._parse_duration("PT45S")
        assert duration == 45

    def test_parse_duration_invalid(self, ingest_system):
        """Test duration parsing with invalid format."""
        duration = ingest_system._parse_duration("INVALID")
        assert duration == 0

    def test_search_videos_success(self, ingest_system):
        """Test successful video search."""
        mock_response = {
            "items": [
                {
                    "id": {"videoId": "test_video_1"},
                    "snippet": {"title": "Test Video 1"},
                },
                {
                    "id": {"videoId": "test_video_2"},
                    "snippet": {"title": "Test Video 2"},
                },
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        
        ingest_system.youtube = Mock()
        ingest_system.youtube.search.return_value.list.return_value = mock_request
        
        videos = ingest_system.search_videos("test query", max_results=2)
        
        assert len(videos) == 2
        assert videos[0]["id"]["videoId"] == "test_video_1"
        assert videos[1]["id"]["videoId"] == "test_video_2"

    def test_search_videos_http_error(self, ingest_system):
        """Test video search with HTTP error."""
        mock_request = Mock()
        mock_request.execute.side_effect = HttpError(
            resp=Mock(status=403), content=b"API key invalid"
        )
        
        ingest_system.youtube = Mock()
        ingest_system.youtube.search.return_value.list.return_value = mock_request
        
        with pytest.raises(HttpError):
            ingest_system.search_videos("test query")

    def test_enrich_video_metadata_success(self, ingest_system):
        """Test successful metadata enrichment."""
        mock_response = {
            "items": [
                {
                    "id": "test_video_id",
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test Description",
                        "channelId": "test_channel",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "tags": ["python", "tutorial"],
                        "categoryId": "28",
                    },
                    "statistics": {
                        "viewCount": "1000",
                        "likeCount": "100",
                        "commentCount": "10",
                    },
                    "contentDetails": {
                        "duration": "PT10M30S",
                    },
                }
            ]
        }
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        
        ingest_system.youtube = Mock()
        ingest_system.youtube.videos.return_value.list.return_value = mock_request
        
        enriched = ingest_system.enrich_video_metadata("test_video_id")
        
        assert enriched is not None
        assert enriched["video_id"] == "test_video_id"
        assert enriched["title"] == "Test Video"
        assert enriched["view_count"] == 1000
        assert enriched["like_count"] == 100
        assert enriched["duration_seconds"] == 630  # 10*60 + 30
        assert enriched["tags"] == ["python", "tutorial"]

    def test_enrich_video_metadata_not_found(self, ingest_system):
        """Test metadata enrichment when video is not found."""
        mock_response = {"items": []}
        
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        
        ingest_system.youtube = Mock()
        ingest_system.youtube.videos.return_value.list.return_value = mock_request
        
        enriched = ingest_system.enrich_video_metadata("nonexistent_video")
        
        assert enriched is None

    def test_check_duplicate_exists(self, ingest_system):
        """Test duplicate check when video exists."""
        mock_response = [
            {"video_id": "test_video_id", "title": "Existing Video"}
        ]
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            is_duplicate = ingest_system.check_duplicate("test_video_id")
            
            assert is_duplicate is True
            mock_get.assert_called_once()

    def test_check_duplicate_not_exists(self, ingest_system):
        """Test duplicate check when video does not exist."""
        mock_response = []
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            is_duplicate = ingest_system.check_duplicate("new_video_id")
            
            assert is_duplicate is False

    def test_check_duplicate_404(self, ingest_system):
        """Test duplicate check with 404 response."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            
            is_duplicate = ingest_system.check_duplicate("new_video_id")
            
            assert is_duplicate is False

    def test_check_duplicate_request_error(self, ingest_system):
        """Test duplicate check with request error."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection error")
            
            with pytest.raises(requests.RequestException):
                ingest_system.check_duplicate("test_video_id")

    def test_post_content_success(self, ingest_system):
        """Test successful content posting."""
        video_data = {
            "video_id": "test_video_id",
            "title": "Test Video",
            "view_count": 1000,
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            
            result = ingest_system.post_content(video_data)
            
            assert result is True
            mock_post.assert_called_once()

    def test_post_content_failure(self, ingest_system):
        """Test content posting failure."""
        video_data = {
            "video_id": "test_video_id",
            "title": "Test Video",
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.text = "Bad request"
            
            result = ingest_system.post_content(video_data)
            
            assert result is False

    def test_post_content_request_error(self, ingest_system):
        """Test content posting with request error."""
        video_data = {"video_id": "test_video_id"}
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.RequestException("Connection error")
            
            with pytest.raises(requests.RequestException):
                ingest_system.post_content(video_data)

    def test_process_videos_complete_flow(self, ingest_system):
        """Test complete video processing flow."""
        # Mock search response
        search_response = {
            "items": [
                {"id": {"videoId": "video_1"}},
                {"id": {"videoId": "video_2"}},
            ]
        }
        
        # Mock enriched data
        enriched_data = {
            "video_id": "video_1",
            "title": "Test Video",
            "view_count": 1000,
        }
        
        # Setup mocks
        ingest_system.search_videos = Mock(return_value=search_response["items"])
        ingest_system.enrich_video_metadata = Mock(return_value=enriched_data)
        ingest_system.check_duplicate = Mock(return_value=False)
        ingest_system.post_content = Mock(return_value=True)
        
        stats = ingest_system.process_videos("test query", max_results=2)
        
        assert stats["searched"] == 2
        assert stats["enriched"] == 2
        assert stats["duplicates"] == 0
        assert stats["posted"] == 2
        assert stats["errors"] == 0

    def test_process_videos_with_duplicates(self, ingest_system):
        """Test video processing with duplicates."""
        search_response = {
            "items": [
                {"id": {"videoId": "video_1"}},
                {"id": {"videoId": "video_2"}},
            ]
        }
        
        enriched_data = {
            "video_id": "video_1",
            "title": "Test Video",
        }
        
        ingest_system.search_videos = Mock(return_value=search_response["items"])
        ingest_system.enrich_video_metadata = Mock(return_value=enriched_data)
        ingest_system.check_duplicate = Mock(return_value=True)  # All duplicates
        ingest_system.post_content = Mock(return_value=True)
        
        stats = ingest_system.process_videos("test query", max_results=2)
        
        assert stats["searched"] == 2
        assert stats["enriched"] == 2
        assert stats["duplicates"] == 2
        assert stats["posted"] == 0

    def test_process_videos_with_errors(self, ingest_system):
        """Test video processing with errors."""
        search_response = {
            "items": [
                {"id": {"videoId": "video_1"}},
            ]
        }
        
        ingest_system.search_videos = Mock(return_value=search_response["items"])
        ingest_system.enrich_video_metadata = Mock(return_value=None)  # Enrichment fails
        
        stats = ingest_system.process_videos("test query", max_results=1)
        
        assert stats["searched"] == 1
        assert stats["enriched"] == 0
        assert stats["errors"] == 1


@pytest.mark.parametrize("duration_string,expected_seconds", [
    ("PT1H", 3600),
    ("PT30M", 1800),
    ("PT45S", 45),
    ("PT1H30M45S", 5445),
    ("PT0S", 0),
])
def test_parse_duration_parametrized(ingest_system, duration_string, expected_seconds):
    """Test duration parsing with various inputs."""
    result = ingest_system._parse_duration(duration_string)
    assert result == expected_seconds
