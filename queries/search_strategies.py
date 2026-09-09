import asyncio
from datetime import datetime, timedelta, timezone

from core import get_graphiti_client

try:
    from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_EPISODE_MENTIONS
except ImportError:
    NODE_HYBRID_SEARCH_EPISODE_MENTIONS = None

# EDGE_HYBRID_SEARCH_ENTITY_RELATIONSHIPS отсутствует в текущей версии graphiti_core,
# поэтому fallback на обычный поиск.
EDGE_RELATIONSHIP_RECIPE = None


async def test_search_strategies():
    graphiti_client = get_graphiti_client()
    graphiti = await graphiti_client.ensure_ready()

    print("🔍 STRATEGY 1: Keyword Search")
    edges = await graphiti.search("Neo4j database", num_results=5)
    print(f"Found {len(edges)} relationships:")
    for edge in edges:
        src = getattr(edge, "source_node_uuid", "?")
        rel = getattr(edge, "relationship_type", "RELATES_TO")
        tgt = getattr(edge, "target_node_uuid", "?")
        print(f"  • {src} -{rel}-> {tgt}")

    print("\n🔍 STRATEGY 2: Hybrid Search")
    hybrid_args = {}
    if NODE_HYBRID_SEARCH_EPISODE_MENTIONS:
        hybrid_args["search_recipe"] = NODE_HYBRID_SEARCH_EPISODE_MENTIONS
    edges = await graphiti.search(
        "What is the main technology in Fractal Memory?", num_results=10, **hybrid_args
    )
    print(f"Found {len(edges)} relationships:")
    for edge in edges:
        src = getattr(edge, "source_node_uuid", "?")
        rel = getattr(edge, "relationship_type", "RELATES_TO")
        tgt = getattr(edge, "target_node_uuid", "?")
        print(f"  • {src} -{rel}-> {tgt}")

    print("\n🔍 STRATEGY 3: Relationship Search")
    rel_args = {}
    if EDGE_RELATIONSHIP_RECIPE:
        rel_args["search_recipe"] = EDGE_RELATIONSHIP_RECIPE
    edges = await graphiti.search("Who works on the project?", num_results=10, **rel_args)
    print(f"Found {len(edges)} relationships:")
    for edge in edges:
        src = getattr(edge, "source_node_uuid", "?")
        rel = getattr(edge, "relationship_type", "RELATES_TO")
        tgt = getattr(edge, "target_node_uuid", "?")
        print(f"  • {src} -{rel}-> {tgt}")

    print("\n🔍 STRATEGY 4: Recent Context (Last 24h)")
    recent_edges = await graphiti.search("Recent activity", num_results=5)
    print(f"Recent relationships: {len(recent_edges)}")


if __name__ == "__main__":
    asyncio.run(test_search_strategies())

