# Refactoring Changelog

## Version 2.0.0 - Architecture Improvements

### 1. Centralized Configuration (`core/config.py`)

All settings now in one place with Pydantic validation:

```python
from core.config import get_config

config = get_config()
config.db.neo4j_uri        # Database settings
config.llm.openai_model    # LLM settings
config.cache.embedding_cache_max_size  # Cache settings
config.memory.personal_group_id        # Memory layer settings
config.app.max_chat_turn_chars         # App settings
```

### 2. Type Definitions (`core/types.py`)

All TypedDict and dataclass definitions centralized:

- `SearchResult`, `ContextResult` - Memory search results
- `EpisodeDict`, `EntityDict`, `EdgeDict` - Graph node types
- `MemoryType`, `EpisodeKind`, `JobStage` - Enums
- `UploadJobStatus`, `IngestResult` - API response types

### 3. Text Utilities (`core/text_utils.py`)

Consolidated text processing functions:

- `fingerprint()` - SHA256 hash for deduplication
- `normalize_text()` - Text normalization
- `is_correction_text()` - Detect correction markers
- `split_into_paragraphs()` - Text chunking
- `extract_names_from_text()` - Entity extraction

### 4. Embedding Cache with LRU/TTL (`core/embeddings.py`)

New `EmbeddingCache` class with:

- LRU eviction (configurable max size, default 10000)
- TTL expiration (configurable, default 7 days)
- Persistent storage to disk
- Cache statistics

```python
from core.embeddings import get_cache_stats, cleanup_cache

stats = get_cache_stats()  # {'size': 100, 'hits': 50, 'misses': 10, ...}
await cleanup_cache()      # Remove expired entries
```

### 5. Job Management (`api/jobs.py`)

Extracted from `api.py` to fix circular imports:

```python
from api.jobs import create_upload_job, update_upload_job, get_upload_job
```

### 6. File Renames

- `api.py` → `app.py` (to avoid conflict with `api/` package)

Update your imports and commands:
```bash
# Old
python -m uvicorn api:app --host 0.0.0.0 --port 8000

# New
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### 7. Logging Improvements

All `print()` statements replaced with proper `logging`:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Message", extra={"key": "value"})
logger.debug("Debug info")
logger.error("Error", exc_info=True)
```

### 8. OpenAPI Documentation

All API endpoints now have:
- Descriptions
- Tags for grouping
- Request/Response model documentation

Access at: `http://localhost:8000/docs`

### 9. Integration Tests

New test suite in `tests/integration/`:

- `test_memory_flow.py` - Memory operations
- `test_api_endpoints.py` - API endpoints
- `test_embedding_cache.py` - Cache behavior

Run with:
```bash
# Requires NEO4J_URI to be set
python -m pytest tests/integration/ -v
```

### Migration Guide

1. Update imports:
```python
# Old
from core.settings import settings
from api import UPLOAD_JOBS

# New
from core.config import get_config, settings
from api.jobs import get_upload_job
```

2. Update uvicorn command:
```bash
# Old
uvicorn api:app

# New
uvicorn app:app
```

3. Install new dependencies:
```bash
pip install pydantic-settings httpx
```
