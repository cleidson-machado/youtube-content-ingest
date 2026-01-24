# youtube-content-ingest

Automated YouTube discovery and ingest pipeline: searches YouTube, enriches video metadata, deduplicates against your catalog, and posts new video records to a content API.

## Features

- **YouTube Search**: Query YouTube using the YouTube Data API v3
- **Metadata Enrichment**: Enhance video metadata with additional information
- **Deduplication**: Prevent duplicate videos from being processed
- **API Integration**: Post new video records to your content API
- **Configurable**: Easy configuration via environment variables

## Installation

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

## Configuration

Create a `.env` file with the following variables:

- `YOUTUBE_API_KEY`: Your YouTube Data API v3 key (required)
- `CONTENT_API_URL`: URL of your content API endpoint (required)
- `CONTENT_API_KEY`: API key for content API authentication (optional)
- `MAX_RESULTS_PER_QUERY`: Maximum results per search query (default: 50)
- `ENABLE_DEDUPLICATION`: Enable/disable deduplication (default: true)
- `ENABLE_ENRICHMENT`: Enable/disable metadata enrichment (default: true)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

## Usage

### Basic Usage

Run the pipeline with default search queries:
```bash
python main.py
```

### Programmatic Usage

```python
from youtube_ingest.config import Config
from youtube_ingest.models import SearchQuery
from youtube_ingest.pipeline import Pipeline
from datetime import datetime, timedelta

# Load configuration
config = Config.from_env()

# Define search queries
queries = [
    SearchQuery(
        query="python tutorial",
        max_results=20,
        order="relevance",
        published_after=datetime.now() - timedelta(days=7)
    ),
]

# Run pipeline
pipeline = Pipeline(config)
results = pipeline.run(queries)

print(f"Posted {results['videos_posted']} videos")
```

## Project Structure

```
youtube-content-ingest/
├── youtube_ingest/          # Main package
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management
│   ├── models.py            # Data models
│   ├── youtube_search.py    # YouTube search functionality
│   ├── metadata_enricher.py # Metadata enrichment
│   ├── deduplicator.py      # Deduplication logic
│   ├── api_client.py        # Content API client
│   └── pipeline.py          # Pipeline orchestration
├── main.py                  # Entry point script
├── requirements.txt         # Python dependencies
├── .env.example            # Example configuration
└── README.md               # This file
```

## Pipeline Flow

1. **Search**: Query YouTube using the Data API v3
2. **Deduplicate**: Remove videos that already exist in your catalog
3. **Enrich**: Add additional metadata to video records
4. **Post**: Send new video records to your content API

## API Requirements

Your content API should implement the following endpoints:

- `GET /videos/ids`: Returns a list of existing video IDs
  ```json
  {
    "video_ids": ["video_id_1", "video_id_2", ...]
  }
  ```

- `POST /videos`: Accepts a video record
  ```json
  {
    "video_id": "abc123",
    "title": "Video Title",
    "description": "Video description",
    ...
  }
  ```

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
