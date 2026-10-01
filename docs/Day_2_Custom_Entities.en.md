# DAY 2: Custom Entity Types & Extraction
> 🌐 🇬🇧 **English** · 🇷🇺 [Русский](./Day_2_Custom_Entities.md)

## 🎯 Goal for the day
Define and test automatic extraction of custom entities from text.

---

## 📝 Theory: What Are Custom Entity Types?

By default, Graphiti extracts:
- **PersonEntity** (people)
- **OrganizationEntity** (companies)
- **LocationEntity** (places)
- **EventEntity** (events)

But you want your own:
- **ProjectEntity** (projects with components)
- **TechnicalConceptEntity** (architecture-level ideas)
- **DecisionEntity** (decisions that can later be overturned)

---

## 💻 Step 1: Define Pydantic Models

```python
# custom_entities.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProjectEntity(BaseModel):
    """Проект с компонентами и статусом"""
    name: str = Field(
        description="Название проекта"
    )
    status: str = Field(
        description="Статус: Concept, Development, Testing, Production, Archived",
        default="Development"
    )
    components: List[str] = Field(
        description="Список компонентов проекта",
        default_factory=list
    )
    owner: str = Field(
        description="Владелец/lead проекта",
        default="Unknown"
    )
    priority: int = Field(
        description="Приоритет: 1-Critical, 2-High, 3-Medium, 4-Low",
        default=3
    )

class TechnicalConceptEntity(BaseModel):
    """Техническая концепция или архитектурный паттерн"""
    name: str = Field(
        description="Название концепции (Fractal, Graph, Memory, etc)"
    )
    description: str = Field(
        description="Краткое описание концепции"
    )
    abstraction_level: int = Field(
        description="Уровень: 1-Basic, 2-Intermediate, 3-Advanced, 4-Research",
        default=2
    )
    related_concepts: List[str] = Field(
        description="Связанные концепции",
        default_factory=list
    )
    implementation_status: str = Field(
        description="Статус реализации: Theoretical, Prototype, Production-Ready",
        default="Theoretical"
    )

class DecisionEntity(BaseModel):
    """Решение, которое может быть переоценено"""
    decision_text: str = Field(
        description="Формулировка решения"
    )
    decision_date: datetime = Field(
        description="Когда было принято решение"
    )
    decision_maker: str = Field(
        description="Кто принял решение"
    )
    rationale: str = Field(
        description="Причины, по которым было принято решение"
    )
    status: str = Field(
        description="Статус: Active, Superseded, Rejected, Pending-Review",
        default="Active"
    )
    dependencies: List[str] = Field(
        description="На что влияет это решение",
        default_factory=list
    )

class TeamEntity(BaseModel):
    """Команда или группа людей"""
    team_name: str = Field(
        description="Название команды"
    )
    members: List[str] = Field(
        description="Члены команды"
    )
    focus: str = Field(
        description="На чём фокусируется команда"
    )
    communication_tool: Optional[str] = Field(
        description="Инструмент общения (Telegram, Slack, Discord)",
        default=None
    )
```

---

## 🔧 Step 2: Updated Main Script

```python
# main_day2.py
import asyncio
import os
from dotenv import load_dotenv
from graphiti_core import Graphiti
from datetime import datetime, timezone
from custom_entities import (
    ProjectEntity,
    TechnicalConceptEntity,
    DecisionEntity,
    TeamEntity
)

load_dotenv()

async def main():
    # Initialize Graphiti
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    print("🔧 Building indices...")
    await graphiti.build_indices_and_constraints()
    print("✅ Indices built\n")

    # Регистрируем кастомные типы
    custom_entity_types = [
        ProjectEntity,
        TechnicalConceptEntity,
        DecisionEntity,
        TeamEntity
    ]

    # Episode 1: Project Overview
    print("📝 Episode 1: Project Overview")
    episode1_text = """
    Sergey and Natasha are working on a Fractal Memory project.

    The project has three main components:
    1. Graph Engine - built with Neo4j for knowledge representation
    2. LLM Integration - using GPT-4 for entity extraction and reasoning
    3. Temporal Processing - maintaining bi-temporal data (valid_from, valid_to)

    The project status is in Development phase.
    Sergey is the primary developer.
    Priority is High - this is a core research initiative.

    Key concepts involved:
    - Fractal Architecture: a hierarchical representation system
    - Knowledge Graph: semantic network of entities and relationships
    - Temporal Logic: maintaining contradictions over time

    These concepts are at Advanced abstraction level (3-4).
    """

    await graphiti.add_episode(
        name="Project Overview",
        episode_body=episode1_text,
        source_description="project_documentation",
        reference_time=datetime.now(timezone.utc),
        custom_entities=custom_entity_types
    )
    print("✅ Episode 1 added\n")

    # Episode 2: Decision Log
    print("📝 Episode 2: Decision Log")
    episode2_text = """
    Decision made on 2025-12-10:

    "We decided to simplify the Fractal Memory implementation by starting with
    vanilla Graphiti instead of building custom Redis buffer layer."

    Made by: Natasha
    Rationale: Reduce complexity, avoid Integration Hell, focus on core value.
    Dependencies: This affects L0 optimization, L1 consolidation logic.
    Status: Active - this is our current strategy.
    """

    await graphiti.add_episode(
        name="Strategic Decision - Vanilla First",
        episode_body=episode2_text,
        source_description="decision_log",
        reference_time=datetime.now(timezone.utc),
        custom_entities=custom_entity_types
    )
    print("✅ Episode 2 added\n")

    # Episode 3: Team Structure
    print("📝 Episode 3: Team Structure")
    episode3_text = """
    The development team consists of:
    - Sergey: Senior Developer, specializing in AI/ML and Python
    - Natasha: Technical Lead and Business Advisor, strategic guidance

    Team Name: Fractal Memory Core Team
    Focus: Building production-grade memory system for AI agents
    Communication: Primarily Telegram for async discussions
    """

    await graphiti.add_episode(
        name="Team Structure",
        episode_body=episode3_text,
        source_description="team_documentation",
        reference_time=datetime.now(timezone.utc),
        custom_entities=custom_entity_types
    )
    print("✅ Episode 3 added\n")

    # Now search for extracted entities
    print("🔍 SEARCH RESULTS:\n")

    search_terms = [
        "Fractal Memory project components",
        "Sergey developer role",
        "Decision vanilla Graphiti",
        "Neo4j graph engine",
        "Team members communication"
    ]

    for search_term in search_terms:
        print(f"  Query: '{search_term}'")
        results = await graphiti._search(search_term, limit=5)

        if results.nodes:
            print(f"    Found {len(results.nodes)} entities:")
            for node in results.nodes:
                print(f"      • {node.name} ({node.node_type})")
                if hasattr(node, 'score'):
                    print(f"        Confidence: {node.score:.2%}")
        else:
            print(f"    No entities found")
        print()

    # Graph Statistics
    print("\n📊 GRAPH STATISTICS:")
    print("  To view: Open http://localhost:7474")
    print("  Query:   MATCH (n) RETURN n LIMIT 100")
    print("  Expected: ~15-20 nodes (entities)")

    # Verify custom types
    print("\n✨ CUSTOM ENTITY TYPES REGISTERED:")
    for entity_type in custom_entity_types:
        print(f"  ✅ {entity_type.__name__}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧪 Step 3: Running and Verification

```bash
# Run the script
python main_day2.py

# Expected output:
# 🔧 Building indices...
# ✅ Indices built
#
# 📝 Episode 1: Project Overview
# ✅ Episode 1 added
#
# 📝 Episode 2: Decision Log
# ✅ Episode 2 added
#
# 📝 Episode 3: Team Structure
# ✅ Episode 3 added
#
# 🔍 SEARCH RESULTS:
#
#   Query: 'Fractal Memory project components'
#     Found 5 entities:
#       • Fractal Memory (ProjectEntity)
#       • Neo4j (TechnicalConceptEntity)
#       • Graph Engine (ProjectEntity)
#       • Sergey (PersonEntity)
#       • Natasha (PersonEntity)
```

---

## 🔍 Step 4: Verification in Neo4j Browser

```cypher
// Query 1: See all custom entities
MATCH (n:ProjectEntity) RETURN n LIMIT 20

// Expected: ProjectEntity nodes with properties:
// {
//   name: "Fractal Memory",
//   status: "Development",
//   components: ["Graph Engine", "LLM Integration", "Temporal Processing"],
//   owner: "Sergey",
//   priority: 2
// }

// Query 2: See relationships between entities
MATCH (p:PersonEntity)-[r]-(t:ProjectEntity)
RETURN p.name, r.type, t.name

// Expected:
// Sergey  WORKS_ON  Fractal Memory
// Natasha LEADS     Fractal Memory

// Query 3: See decisions and their status
MATCH (d:DecisionEntity)
RETURN d.decision_text, d.status, d.decision_maker

// Query 4: See technical concepts and levels
MATCH (c:TechnicalConceptEntity)
RETURN c.name, c.abstraction_level, c.implementation_status
```

---

## 📊 Expected Results

After all episodes are completed, the graph should contain:

| Node type | Examples | Count |
|----------|---------|-------|
| ProjectEntity | Fractal Memory, Graph Engine | 2-3 |
| PersonEntity | Sergey, Natasha | 2 |
| TechnicalConceptEntity | Fractal, Knowledge Graph, Temporal Logic | 3-5 |
| DecisionEntity | Vanilla First strategy | 1+ |
| TeamEntity | Core Team | 1 |

**Total nodes: 10-15**
**Total edges: 15-20** (relationships between entities)

---

## ✅ Day 2 Checklist

- [ ] custom_entities.py created with 4 models
- [ ] main_day2.py run without errors
- [ ] 3 episodes added successfully
- [ ] Search returns custom types
- [ ] Neo4j Browser displays nodes
- [ ] All custom types registered ✅

**Next: Day 3 (Custom Entity Extraction Deep Dive)**
