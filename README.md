# YouTube Content Ingest

Automated YouTube discovery and ingest pipeline: searches YouTube, enriches video metadata, deduplicates against your catalog, and posts new video records to a content API.

## Features

- 🔍 **YouTube Search**: Search videos via YouTube Data API v3
- 📊 **Metadata Enrichment**: Extract title, views, duration, tags, and more
- 🔄 **Duplicate Detection**: Check existing content via REST API (GET /contents)
- 📤 **API Integration**: Post new videos to content API (POST /contents) with Bearer authentication
- 🐍 **Python 3.13**: Built with the latest Python features
- 🧪 **Tested**: Comprehensive pytest test suite
- 🐳 **Dockerized**: Ready-to-run Alpine-based container
- 📝 **Type-Safe**: Full type hints throughout
- 🔐 **Secure**: Environment-based configuration

## Requirements

- Python 3.13.7
- YouTube Data API v3 key
- Content API endpoint with Bearer token authentication

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/cleidson-machado/youtube-content-ingest.git
cd youtube-content-ingest
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Run the application:
```bash
python src/main.py
```

### Docker Setup

1. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

Or run with Docker directly:
```bash
docker build -t youtube-ingest .
docker run --env-file .env youtube-ingest
```

## Configuration

All configuration is done via environment variables. Copy `.env.example` to `.env` and configure:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `YOUTUBE_API_KEY` | Yes | YouTube Data API v3 key | - |
| `CONTENT_API_BASE_URL` | Yes | Base URL for content API | - |
| `CONTENT_API_BEARER_TOKEN` | Yes | Bearer token for API auth | - |
| `SEARCH_QUERY` | No | YouTube search query | `python programming` |
| `MAX_RESULTS` | No | Maximum videos to fetch | `10` |
| `LOG_LEVEL` | No | Logging level | `INFO` |

### Getting a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API key)
5. Copy the API key to your `.env` file

## Usage

The application performs the following workflow:

1. **Search**: Queries YouTube for videos matching `SEARCH_QUERY`
2. **Enrich**: Fetches detailed metadata for each video:
   - Title and description
   - View count, like count, comment count
   - Duration (in seconds)
   - Tags and category
   - Channel information
   - Publication date
3. **Deduplicate**: Checks if video already exists via `GET /contents?video_id={id}`
4. **Post**: Submits new videos to `POST /contents` with Bearer authentication

### Example Output

```
2024-01-24 12:00:00 - main - INFO - YouTube Content Ingest system starting
2024-01-24 12:00:00 - main - INFO - YouTube API client initialized successfully
2024-01-24 12:00:00 - main - INFO - Starting video processing for query: 'python programming'
2024-01-24 12:00:00 - main - INFO - Searching YouTube for: 'python programming' (max results: 10)
2024-01-24 12:00:01 - main - INFO - Found 10 videos
2024-01-24 12:00:02 - main - INFO - Video abc123 already exists (duplicate)
2024-01-24 12:00:03 - main - INFO - Posting content: Python Tutorial for Beginners
2024-01-24 12:00:03 - main - INFO - Successfully posted video: xyz789
2024-01-24 12:00:04 - main - INFO - Processing complete. Stats: 10 searched, 10 enriched, 3 duplicates, 7 posted, 0 errors
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## Project Structure

```
youtube-content-ingest/
├── src/
│   └── main.py                 # Main application code
├── tests/
│   └── test_main.py           # Test suite
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── .python-version            # Python version specification
├── Dockerfile                 # Alpine-based container
├── docker-compose.yml         # Docker Compose configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## API Contract

### Content API Endpoints

#### GET /contents
Check for existing videos by video_id:
```
GET {CONTENT_API_BASE_URL}/contents?video_id={youtube_video_id}
Authorization: Bearer {token}
```

Response:
```json
[
  {
    "video_id": "abc123",
    "title": "Existing Video"
  }
]
```

#### POST /contents
Submit new video content:
```
POST {CONTENT_API_BASE_URL}/contents
Authorization: Bearer {token}
Content-Type: application/json

{
  "video_id": "xyz789",
  "title": "Video Title",
  "description": "Video description...",
  "channel_id": "UCxxxxxx",
  "channel_title": "Channel Name",
  "published_at": "2024-01-01T00:00:00Z",
  "view_count": 1000,
  "like_count": 100,
  "comment_count": 10,
  "duration_seconds": 630,
  "tags": ["python", "tutorial"],
  "category_id": "28"
}
```

## Development

### Code Quality

The codebase follows:
- Type hints throughout
- Comprehensive error handling
- Structured logging
- Clean code principles

### Adding Features

1. Update `src/main.py` with new functionality
2. Add tests in `tests/test_main.py`
3. Update documentation in README
4. Run tests: `pytest tests/`

## Troubleshooting

### Common Issues

**API Key Invalid**
```
Error: YouTube API error: <HttpError 403>
```
Solution: Verify your `YOUTUBE_API_KEY` is correct and the YouTube Data API v3 is enabled.

**Content API Authentication Failed**
```
Error: Failed to post video: Status 401
```
Solution: Check that `CONTENT_API_BEARER_TOKEN` is valid and has not expired.

**No Videos Found**
```
Warning: No videos were processed
```
Solution: Try a different `SEARCH_QUERY` or increase `MAX_RESULTS`.

## License

See [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request
