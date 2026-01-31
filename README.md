# youtube-content-ingest

Automated YouTube discovery and ingest pipeline: searches YouTube, enriches video metadata, deduplicates against your catalog, and posts new video records to a content API.

**Refactored from:** `main_orig_bkp.py` - A professional modular architecture for better maintainability, security, and scalability.

## Features

- **YouTube Search**: Query YouTube using the YouTube Data API v3 with pagination support
- **Rich Metadata Extraction**: Comprehensive video data including:
  - Basic info (title, description, channel, thumbnail)
  - Statistics (views, likes, comments)
  - Categories (ID and name)
  - Duration (ISO 8601 and seconds)
  - Quality (HD/SD, captions)
  - Language information
- **Incremental Search**: Searches page-by-page until target number of new videos is found
- **Deduplication**: Prevents duplicate videos by checking against existing URLs in your database
- **API Integration**: Posts new video records to your content API with Bearer token authentication
- **Secure Configuration**: Environment variables for API keys (no hardcoded credentials)
- **Configurable**: Easy configuration via environment variables

## Architecture

The project is organized in a modular structure for better maintainability:

```
youtube-content-ingest/
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment configuration
├── .env                      # Your actual configuration (gitignored)
└── youtube_ingest/           # Main package
    ├── __init__.py
    ├── config.py             # Configuration management
    ├── models.py             # Data models (Video, SearchQuery)
    ├── youtube_search.py     # YouTube API integration
    ├── deduplicator.py       # Duplicate detection
    ├── metadata_enricher.py  # Metadata enhancement
    ├── api_client.py         # Content API client
    └── pipeline.py           # Pipeline orchestration
```

## Installation

### macOS (Recomendado)

```bash
# 1. Criar ambiente virtual
python3 -m venv venv

# 2. Ativar ambiente virtual
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar credenciais
cp .env.template .env
nano .env  # Edite com suas credenciais
```

**📘 Guia completo:** Veja [SETUP_MACOS.md](x_temp_files/SETUP_MACOS.md) para troubleshooting e dicas.  
**🔒 Segurança:** Leia [SECURITY.md](SECURITY.md) para práticas de segurança com credenciais.

### Linux/Windows

```bash
# 1. Clone o repositório
git clone https://github.com/cleidson-machado/youtube-content-ingest.git
cd youtube-content-ingest

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Configurar credenciais
cp .env.template .env
# Edite .env com suas credenciais
```

**🔒 Importante:** Nunca commite o arquivo `.env` com suas credenciais reais! Leia [SECURITY.md](SECURITY.md) para mais detalhes.

## Configuration

Create a `.env` file based on `.env.example` with the following variables:

### Required Variables

- `YOUTUBE_API_KEY`: Your YouTube Data API v3 key ([Get one here](https://console.cloud.google.com/apis/credentials))
- `CONTENT_API_URL`: Base URL of your content API endpoint
- `CONTENT_API_TOKEN`: Bearer token for content API authentication

### Optional Variables

- `SEARCH_QUERY`: YouTube search query (default: "tipos de visto para portugal")
- `TARGET_NEW_VIDEOS`: Number of new videos to find (default: 10)
- `MAX_PAGES_TO_SEARCH`: Maximum pages to search (default: 10)
- `MAX_RESULTS_PER_PAGE`: Results per page (default: 10, max: 50)
- `ENABLE_DEDUPLICATION`: Enable/disable deduplication (default: true)
- `ENABLE_ENRICHMENT`: Enable/disable metadata enrichment (default: false)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

## Usage

### Basic Usage

Run the pipeline with configuration from `.env`:
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

## How It Works

The pipeline follows the same incremental search logic as the original `main_orig_bkp.py`:

1. **Fetch Existing URLs**: Retrieves all existing video URLs from your content API to prevent duplicates
2. **Incremental Search**: Searches YouTube page by page until:
   - Target number of new videos is found, OR
   - Maximum pages searched, OR
   - No more results available
3. **Rich Metadata Extraction**: For each video, extracts comprehensive metadata including categories, statistics, duration, quality, and language info
4. **Duplicate Check**: Filters out videos that already exist in your database or in the current batch
5. **API Submission**: Posts each new video to your content API with detailed logging

## Pipeline Flow

```
Start → Load Config → Fetch Existing URLs
  ↓
Search YouTube (Page 1)
  ↓
Extract Video Metadata (Categories, Stats, Duration, etc.)
  ↓
Filter Duplicates
  ↓
Enough new videos? → NO → Search Next Page → (repeat)
  ↓ YES
Post New Videos to API
  ↓
Done ✓
```

## API Requirements

Your content API should implement the following endpoints:

### GET endpoint (for fetching existing content)
- **URL**: Base URL configured in `CONTENT_API_URL`
- **Headers**: `Authorization: Bearer {CONTENT_API_TOKEN}`
- **Response**: Array of content items or object with `items` array
  ```json
  [
    {"url": "https://www.youtube.com/watch?v=...", ...},
    ...
  ]
  ```
  OR
  ```json
  {
    "items": [
      {"url": "https://www.youtube.com/watch?v=...", ...},
      ...
    ]
  }
  ```

### POST endpoint (for creating new content)
- **URL**: Base URL configured in `CONTENT_API_URL`
- **Headers**: `Authorization: Bearer {CONTENT_API_TOKEN}`, `Content-Type: application/json`
- **Status**: Returns `201 Created` on success
- **Body**: Video record in the following format:
  ```json
  {
    "title": "Video Title",
    "description": "Video description",
    "url": "https://www.youtube.com/watch?v=video_id",
    "channelName": "Channel Name",
    "type": "VIDEO",
    "thumbnailUrl": "https://...",
    "categoryId": "10",
    "categoryName": "Music",
    "tags": "tag1, tag2, tag3",
    "durationSeconds": 180,
    "durationIso": "PT3M",
    "definition": "hd",
    "caption": true,
    "viewCount": 1000,
    "likeCount": 50,
    "commentCount": 10,
    "defaultLanguage": "pt",
    "defaultAudioLanguage": "pt"
  }
  ```

## Improvements Over Original Script

This refactored version improves upon `main_orig_bkp.py` with:

### ✅ Security
- **No hardcoded credentials**: All API keys and tokens in environment variables
- **No hardcoded endpoints**: API URLs configurable via `.env`
- **Secure by default**: `.env` in `.gitignore` prevents credential leaks

### ✅ Maintainability
- **Modular architecture**: Separated concerns (search, deduplication, API client, etc.)
- **Clear responsibilities**: Each module has a single, well-defined purpose
- **Easy to test**: Each component can be tested independently
- **Easy to extend**: Add new features without touching existing code

### ✅ Code Quality
- **Type hints**: Full type annotations for better IDE support
- **Logging**: Proper logging framework instead of print statements
- **Error handling**: Comprehensive exception handling with detailed error messages
- **Documentation**: Docstrings for all classes and methods

### ✅ Functionality
- **Same behavior**: Replicates exact functionality of original script
- **Incremental search**: Continues searching until target met or max pages reached
- **Rich metadata**: Extracts all fields from original (categories, duration, stats, etc.)
- **URL-based deduplication**: Uses URLs for duplicate checking (same as original)
- **Detailed logging**: Beautiful console output with emojis and progress indicators

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
