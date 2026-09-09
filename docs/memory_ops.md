# MemoryOps: High-Level Memory Operations

## Overview

MemoryOps provides a unified, high-level interface for working with Graphiti's memory system. It abstracts away the complexity of direct Graphiti operations while preserving all the intelligence of entity extraction, fact analysis, and temporal reasoning.

## Architecture

```
MemoryOps
├── remember_text() → knowledge.ingest.remember_text()
├── search_memory() → Graphiti search + node search
├── build_context_for_query() → search_memory() + formatting
└── remember_experience() → experience.ingest_experience()
```

## Quick Start

### Python Usage

```python
from core.graphiti_client import get_graphiti_client
from core.memory_ops import MemoryOps

# Initialize
graphiti = await get_graphiti_client().ensure_ready()
memory = MemoryOps(graphiti, user_id="your_user_id")

# Remember text with auto-classification
result = await memory.remember_text(
    "John works at OpenAI as a researcher",
    memory_type="personal"  # or None for auto-detection
)

# Search memory
results = await memory.search_memory("OpenAI", limit=5)
print(f"Found {results.total_episodes} episodes, {results.total_entities} entities")

# Build context for LLM
context = await memory.build_context_for_query(
    "What do you know about John?",
    max_tokens=2000
)
print(f"Context: {context.text[:200]}...")
```

### FastAPI Usage

```python
# POST /chat
{
  "message": "What projects is John working on?",
  "user_id": "user123"
}

# Response
{
  "reply": "Based on my memory, John is working at OpenAI as a researcher...",
  "duration_ms": 1250.5,
  "timing": {
    "answer_ms": 950.2,
    "total_ms": 1250.5
  }
}
```

### MCP Server Tools

#### memory.remember_text
```json
{
  "name": "memory.remember_text",
  "description": "Store text in memory with automatic classification",
  "input": {
    "text": "Your text here",
    "memory_type": "personal", // optional: personal/project/knowledge/experience
    "source_description": "chat", // optional
    "user_id": "user123" // optional, default: "mcp_user"
  }
}
```

#### memory.search_memory
```json
{
  "name": "memory.search_memory",
  "description": "Search across episodic and semantic memory",
  "input": {
    "query": "search term",
    "limit": 10, // optional
    "user_id": "user123" // optional
  },
  "output": {
    "episodes": [...],
    "entities": [...],
    "total_episodes": 5,
    "total_entities": 3
  }
}
```

#### memory.chat
```json
{
  "name": "memory.chat",
  "description": "Chat with memory-enabled agent",
  "input": {
    "message": "Your question here",
    "user_id": "user123" // optional
  },
  "output": {
    "reply": "Agent's response based on memory context"
  }
}
```

## Memory Types

MemoryOps supports automatic classification of content:

- **personal**: Personal information (people, relationships, preferences)
- **project**: Project-related knowledge (code, architecture, tasks)
- **knowledge**: General knowledge and facts
- **experience**: Success patterns and lessons learned

If `memory_type` is not specified, the system automatically classifies the content.

## Context Building

The `build_context_for_query()` method creates formatted context for LLM queries:

```
## Эпизоды памяти:
- Episode content excerpt...
- Another relevant episode...

## Сущности:
- Entity Name: Summary...
- Another Entity: Summary...
```

Context is automatically truncated to fit token limits and includes metadata about sources.

## Error Handling

MemoryOps gracefully handles Graphiti failures:

- Search failures return empty results instead of crashing
- LLM failures in chat agent provide fallback responses
- All operations include proper error logging

## Performance

MemoryOps adds minimal overhead over direct Graphiti calls:

- remember_text: ~10-50ms (same as Graphiti)
- search_memory: ~100-500ms (Graphiti search + formatting)
- build_context_for_query: ~200-800ms (search + formatting)
- chat: ~1000-3000ms (context + LLM call + storage)

## Integration

MemoryOps is designed to work seamlessly with:

- **FastAPI**: Direct API endpoints
- **MCP Server**: Standardized tool interface
- **Custom Agents**: Easy integration via MemoryOps interface
- **Existing Code**: Drop-in replacement for direct Graphiti calls

The layer preserves all Graphiti intelligence while providing a cleaner, more maintainable API.