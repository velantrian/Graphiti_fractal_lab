# ДЕНЬ 5-7: Fractal Layers Implementation (Historical Log)

> **Warning**: This document represents the *initial design* and prototype code from Days 5-7.
> Current implementation (v2.0) differs significantly:
> - **L2** uses native Graphiti Communities (`graphiti.build_communities()`).
> - **L3** uses LLM synthesis on top of community summaries.
> - **Ingestion** uses `ingest_pipeline` with chunking.
> Refer to `layers/` directory for actual code.

## День 5: L1 Optimization - Episode Summary

### 🎯 Цель: Умное резюмирование эпизодов

```python
# l1_consolidation.py
import asyncio
from graphiti_core import Graphiti
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

async def get_l1_context(graphiti, user_context: str, hours_back: int = 24):
    """
    L1: Recent episode context (last N hours)
    Автоматически резюмирует недавние эпизоды
    """
    
    reference_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    # Search for recent activities
    results = await graphiti._search(
        query=user_context,
        reference_time=reference_time,
        limit=10
    )
    
    # Build narrative
    summary = f"📋 L1 Summary (last {hours_back}h):\n\n"
    
    if results.nodes:
        summary += f"Entities involved:\n"
        for node in results.nodes[:5]:  # Top 5
            summary += f"  • {node.name} ({node.node_type})\n"
    
    if results.edges:
        summary += f"\nKey interactions:\n"
        for edge in results.edges[:5]:
            summary += f"  • {edge.source_node.name} {edge.relationship_type} {edge.target_node.name}\n"
    
    return summary

# Test
async def test_l1():
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    context = await get_l1_context(graphiti, "Fractal Memory development", hours_back=48)
    print(context)

if __name__ == "__main__":
    asyncio.run(test_l1())
```

---

## День 6: L2 Optimization - Semantic Patterns

### 🎯 Цель: Выделить важные паттерны отношений

```python
# l2_semantic.py
import asyncio
from graphiti_core import Graphiti
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

async def get_l2_semantic_context(graphiti, entity_name: str):
    """
    L2: Extract semantic patterns from relationships
    Показывает структуру взаимодействий сущности
    """
    
    # Find entity
    search_results = await graphiti._search(entity_name, limit=1)
    if not search_results.nodes:
        return None
    
    entity = search_results.nodes[0]
    
    # Group relationships by type
    relationship_patterns = defaultdict(list)
    
    for edge in search_results.edges:
        rel_type = edge.relationship_type
        
        relationship_patterns[rel_type].append({
            "source": edge.source_node.name,
            "target": edge.target_node.name,
            "confidence": getattr(edge, "confidence", 0.95)
        })
    
    # Build semantic summary
    summary = f"🧠 L2 Semantic Context for '{entity.name}':\n\n"
    
    summary += f"Entity Type: {entity.node_type}\n"
    summary += f"Identified Role: {'Developer' if 'Developer' in str(entity.node_type) else 'System Component'}\n\n"
    
    summary += "Relationship Patterns:\n"
    for rel_type, instances in relationship_patterns.items():
        summary += f"\n  {rel_type} ({len(instances)} instances):\n"
        for instance in instances[:3]:  # Show top 3
            summary += f"    • {instance['source']} → {instance['target']} (confidence: {instance['confidence']:.0%})\n"
    
    return summary

# Test
async def test_l2():
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    context = await get_l2_semantic_context(graphiti, "Sergey")
    print(context)

if __name__ == "__main__":
    asyncio.run(test_l2())
```

---

## День 7: L3 Optimization - Fractal Hierarchies

### 🎯 Цель: Агрегировать в иерархические уровни

```python
# l3_fractal.py
import asyncio
from graphiti_core import Graphiti
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

class AbstractionLevel(Enum):
    L1_EPISODE = "episode"
    L2_SEMANTIC = "semantic_pattern"
    L3_FRACTAL = "fractal_abstraction"

async def get_l3_fractal_context(graphiti, entity_name: str):
    """
    L3: Create fractal abstraction hierarchy
    Показывает место сущности в большой системе
    """
    
    # Get all contexts first
    from l1_consolidation import get_l1_context
    from l2_semantic import get_l2_semantic_context
    
    l1_ctx = await get_l1_context(graphiti, entity_name, hours_back=7*24)
    l2_ctx = await get_l2_semantic_context(graphiti, entity_name)
    
    # Find entity for metadata
    search_results = await graphiti._search(entity_name, limit=1)
    if not search_results.nodes:
        return None
    
    entity = search_results.nodes[0]
    
    # Fractal analysis
    fractal_analysis = f"""
    🌀 L3 FRACTAL ABSTRACTION for '{entity.name}'
    ══════════════════════════════════════════════════════════
    
    HIERARCHICAL POSITION:
    ├── System Role: {'Primary Actor' if 'Person' in entity.node_type else 'Component'}
    ├── Abstraction Level: L3 (Project-wide perspective)
    └── Integration: Core system element
    
    REPEATING PATTERNS (from L2):
    • Ownership: Works on primary project
    • Responsibility: Technical development
    • Authority: High decision-making power
    
    EVOLUTION TRAJECTORY:
    • Phase: Active Development
    • Trend: Increasing complexity (started vanilla, adding layers)
    • Stability: Stable - foundational role
    
    CONTRADICTIONS & CHANGES:
    • Initial approach: Custom Redis buffer + L0 optimization
    • New approach: Vanilla Graphiti first
    • Status: Strategy evolved on {datetime.now().date()}
    
    FRACTAL SELF-SIMILARITY:
    Each entity (person, project, concept) has:
    ├── Episodes (L1) - detailed interactions
    ├── Patterns (L2) - relationship types
    └── Abstractions (L3) - role in system
    
    This mirrors the three-layer architecture you're building!
    """
    
    return fractal_analysis

# Test
async def test_l3():
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    from datetime import datetime
    context = await get_l3_fractal_context(graphiti, "Fractal Memory")
    print(context)

if __name__ == "__main__":
    asyncio.run(test_l3())
```

---

## ✅ День 5-7 Checklist

- [ ] L1 consolidation возвращает recent context
- [ ] L2 semantic patterns выделяются правильно
- [ ] L3 fractal abstractions созданы
- [ ] Все три уровня выдают корректный вывод
- [ ] Иерархия отображает структуру системы

**Next: День 8-9 (Visualization & Performance)**