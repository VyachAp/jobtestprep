# Weather API Service

A simple, async weather API built with FastAPI that fetches data from OpenWeatherMap, with caching, local file storage, and event logging.

## Features

- **Single endpoint**: `/weather?city=London` - Get current weather for any city
- **5-minute caching**: Reduces API calls and improves response time
- **Local storage**: Saves each response as `{city}_{timestamp}.json`
- **Event logging**: Tracks all requests in SQLite database
- **Async architecture**: Built with httpx for efficient I/O operations
- **Cloud-ready abstractions**: Easy to swap local storage for S3, SQLite for DynamoDB

## Quick Start

### Option 1: Docker (Recommended)

1. **Clone and configure**:
   ```bash
   # Copy the example env file
   cp env.example .env
   
   # Edit .env and add your OpenWeatherMap API key
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Test the API**:
   ```bash
   curl "http://localhost:8000/weather?city=London"
   ```

### Option 2: Local Development

1. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or: .venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   export OPENWEATHERMAP_API_KEY=your_api_key_here
   ```

4. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### GET /weather

Fetch current weather for a city.

**Parameters**:
- `city` (required): City name, optionally with country code

**Example**:
```bash
curl "http://localhost:8000/weather?city=London"
curl "http://localhost:8000/weather?city=New%20York,US"
```

**Response**:
```json
{
  "data": {
    "city": "London",
    "country": "GB",
    "temperature": 12.5,
    "feels_like": 10.2,
    "humidity": 82,
    "pressure": 1015,
    "wind_speed": 4.12,
    "description": "overcast clouds",
    "icon": "04d",
    "timestamp": "2024-01-15T14:30:00"
  },
  "cached": false,
  "file_path": "data/london_20240115_143000.json"
}
```

### GET /health

Health check endpoint.

```bash
curl http://localhost:8000/health
```

### GET /events

View request history.

**Parameters**:
- `city` (optional): Filter by city name
- `limit` (optional): Max events to return (default: 100)

```bash
curl "http://localhost:8000/events?city=London&limit=10"
```

## Project Structure

```
weather-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and endpoints
│   ├── config.py            # Configuration with environment variables
│   ├── exceptions.py        # Custom exception handlers
│   ├── models/
│   │   ├── __init__.py
│   │   └── weather.py       # Pydantic data models
│   └── services/
│       ├── __init__.py
│       ├── weather.py       # OpenWeatherMap API client
│       ├── storage.py       # File storage (swappable for S3)
│       ├── cache.py         # In-memory cache (swappable for Redis)
│       └── event_logger.py  # SQLite logger (swappable for DynamoDB)
├── data/                    # Weather data JSON files
├── logs/                    # SQLite event database
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Architecture

### Storage Abstraction

The `StorageService` uses an abstract base class pattern, making it easy to swap implementations:

```python
# Current: Local file storage
storage = StorageService()

# Future: S3 storage
storage = StorageService(storage=S3Storage(bucket="weather-data"))
```

### Event Logger Abstraction

The `EventLogger` follows the same pattern:

```python
# Current: SQLite
logger = EventLogger()

# Future: DynamoDB
logger = EventLogger(logger=DynamoDBEventLogger(table="weather-events"))
```

### Caching

In-memory cache with TTL. For production, swap to Redis:

```python
# Current: In-memory
cache = CacheService(ttl_seconds=300)

# Future: Redis
cache = RedisCache(redis_url="redis://localhost:6379")
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OPENWEATHERMAP_API_KEY` | Your OpenWeatherMap API key | (required) |
| `CACHE_TTL_SECONDS` | Cache expiry time in seconds | 300 (5 min) |

## Error Handling

The API returns appropriate HTTP status codes:

| Status | Description |
|--------|-------------|
| 200 | Success |
| 404 | City not found |
| 401 | Invalid API key |
| 503 | Service unavailable (API down) |
| 504 | Request timeout |

## License

MIT

