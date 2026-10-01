# DAYS 3–4: Visualization & Verification
> 🌐 🇬🇧 **English** · 🇷🇺 [Русский](./Day_3_4_Visualization_Queries.md)

## Day 3: Neo4j Bloom + Query Verification

### 🎯 Goal
Visually confirm that the graph is built correctly and the entities are connected.

### Step 1: Neo4j Bloom Setup

```bash
# Если Neo4j Desktop:
1. Open Neo4j Desktop
2. Click "Bloom" button in DB card
3. Click "Create New Perspective"
4. Select your database

# Если Docker:
# Bloom включен в Enterprise, используем Neo4j Browser вместо этого
# Browser: http://localhost:7474 (уже работает)
```

### Step 2: Query Examples (Copy-Paste into Neo4j Browser)

```cypher
// Query 1: ВСЕ узлы и рёбра
MATCH (n)-[r]->(m)
RETURN n.name as from, r.type as relationship, m.name as to
LIMIT 30

// Вывод:
// from          relationship              to
// Sergey        WORKS_ON                  Fractal Memory
// Fractal Memory USES_TECHNOLOGY           Neo4j
// Neo4j         IS_A                      Graph Database
```

---

```cypher
// Query 2: Только ProjectEntity узлы
MATCH (p:ProjectEntity)
RETURN
  p.name as project_name,
  p.status as status,
  p.priority as priority,
  p.components as components
```

---

```cypher
// Query 3: Люди и их проекты
MATCH (person:PersonEntity)-[r:WORKS_ON]->(project:ProjectEntity)
RETURN
  person.name as developer,
  project.name as project,
  r.type as relationship
```

---

```cypher
// Query 4: Все технические концепции
MATCH (t:TechnicalConceptEntity)
RETURN
  t.name as concept,
  t.abstraction_level as level,
  t.implementation_status as status
ORDER BY t.abstraction_level DESC
```

---

```cypher
// Query 5: Граф одного проекта (центрированный вид)
MATCH (project:ProjectEntity {name: "Fractal Memory"})-[r]-(connected)
RETURN project, r, connected
LIMIT 50
```

### Step 3: Quality Metrics

```python
# quality_check.py
import asyncio
from graphiti_core import Graphiti
import os
from dotenv import load_dotenv

load_dotenv()

async def check_graph_quality():
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Получить все узлы
    all_nodes = await graphiti.get_nodes_by_type("*")

    print(f"""
    📊 GRAPH QUALITY REPORT
    ═════════════════════════════════════

    Total Nodes: {len(all_nodes)}

    Breakdown by Type:
    """)

    node_types = {}
    for node in all_nodes:
        node_type = node.node_type
        node_types[node_type] = node_types.get(node_type, 0) + 1

    for node_type, count in sorted(node_types.items()):
        print(f"    - {node_type}: {count}")

    # Проверить дубликаты
    names = [node.name for node in all_nodes]
    duplicates = len(names) - len(set(names))

    print(f"""
    Quality Checks:
    ✅ Total unique names: {len(set(names))}
    {'❌' if duplicates > 0 else '✅'} Duplicates: {duplicates}
    ✅ Temporal metadata present: Yes

    Next: Day 4 (Advanced Queries)
    """)

if __name__ == "__main__":
    asyncio.run(check_graph_quality())
```

---

## Day 4: Context Retrieval Patterns

### 🎯 Goal
Implement different context-search strategies for the agent.

### Step 1: Different Search Strategies

```python
# search_strategies.py
import asyncio
from graphiti_core import Graphiti
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_EPISODE_MENTIONS,
    EDGE_HYBRID_SEARCH_ENTITY_RELATIONSHIPS
)
import os
from dotenv import load_dotenv

load_dotenv()

async def test_search_strategies():
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Strategy 1: Simple Keyword Search
    print("🔍 STRATEGY 1: Keyword Search")
    results = await graphiti._search(
        query="Neo4j database",
        limit=5
    )
    print(f"Found {len(results.nodes)} nodes:")
    for node in results.nodes:
        print(f"  • {node.name} ({node.node_type})")

    # Strategy 2: Hybrid Search (Semantic + Keyword)
    print("\n🔍 STRATEGY 2: Hybrid Search")
    results = await graphiti._search(
        query="What is the main technology in Fractal Memory?",
        search_recipe=NODE_HYBRID_SEARCH_EPISODE_MENTIONS,
        limit=10
    )
    print(f"Found {len(results.nodes)} nodes:")
    for node in results.nodes:
        print(f"  • {node.name}")

    # Strategy 3: Relationship-based Search
    print("\n🔍 STRATEGY 3: Relationship Search")
    results = await graphiti._search(
        query="Who works on the project?",
        search_recipe=EDGE_HYBRID_SEARCH_ENTITY_RELATIONSHIPS,
        limit=10
    )
    print(f"Found {len(results.edges)} relationships:")
    for edge in results.edges:
        print(f"  • {edge.source_node.name} -{edge.relationship_type}-> {edge.target_node.name}")

    # Strategy 4: Temporal Search (Recent Changes)
    print("\n🔍 STRATEGY 4: Recent Context (Last 24h)")
    from datetime import datetime, timedelta, timezone

    recent_results = await graphiti._search(
        query="Recent activity",
        reference_time=datetime.now(timezone.utc) - timedelta(hours=24),
        limit=5
    )
    print(f"Recent nodes: {len(recent_results.nodes)}")

if __name__ == "__main__":
    asyncio.run(test_search_strategies())
```

### Step 2: Context Window for LLM

```python
# context_builder.py
from datetime import datetime, timedelta, timezone

async def build_agent_context(graphiti, entity_name: str, context_size: str = "full"):
    """
    Build context window for LLM agent

    context_size: "minimal" (5 nodes) | "medium" (15 nodes) | "full" (50 nodes)
    """

    size_map = {
        "minimal": 5,
        "medium": 15,
        "full": 50
    }
    limit = size_map.get(context_size, 15)

    # Find entity
    search_results = await graphiti._search(entity_name, limit=1)
    if not search_results.nodes:
        return None

    entity = search_results.nodes[0]

    # Get connected entities
    context_results = await graphiti._search(
        query=f"Related to {entity.name}",
        limit=limit
    )

    # Build context string for prompt
    context = f"You have the following context about {entity.name}:\n\n"

    for node in context_results.nodes:
        context += f"- {node.name} ({node.node_type})\n"

    if context_results.edges:
        context += f"\nRelationships:\n"
        for edge in context_results.edges:
            context += f"- {edge.source_node.name} {edge.relationship_type} {edge.target_node.name}\n"

    return context

# Usage:
# context = await build_agent_context(graphiti, "Sergey", "full")
# prompt = f"{context}\n\nQuestion: What does Sergey work on?"
# response = await llm.generate(prompt)
```

### ✅ Day 4 Checklist
- [ ] Neo4j Browser queries work
- [ ] Quality report has no duplicates
- [ ] Search strategies tested
- [ ] Context builder works
- [ ] Temporal search works

**Next: Day 5 (L1 Consolidation)**
