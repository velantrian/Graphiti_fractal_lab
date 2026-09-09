#!/usr/bin/env python3
"""
Debug script for memory search and context building.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.graphiti_client import get_graphiti_client
from core.memory_ops import MemoryOps


async def debug_memory_search():
    """Debug memory search for specific queries."""
    print("=== MEMORY DEBUG TEST ===")

    try:
        # Initialize
        graphiti_client = get_graphiti_client()
        graphiti = await graphiti_client.ensure_ready()
        memory = MemoryOps(graphiti, "sergey")

        # Test queries
        test_queries = [
            "Кто такой Марк?",
            "Что ты знаешь про Архетип Марка?",
            "Что ты знаешь про Щит смысла?",
            "Что ты знаешь про План защиты Марка?"
        ]

        for query in test_queries:
            print(f"\n--- Query: {query} ---")

            # Test search_memory
            search_result = await memory.search_memory(query, scopes=["personal", "knowledge", "project"], limit=10)
            print(f"Search result: {search_result.total_episodes} episodes, {search_result.total_entities} entities")

            # Test build_context
            context_result = await memory.build_context_for_query(query, max_tokens=2000)
            print(f"Context: {len(context_result.text)} chars, {context_result.token_estimate} tokens")
            print(f"Context preview: {context_result.text[:500]}...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def debug_neo4j_entities():
    """Debug entity group_ids in Neo4j."""
    print("\n=== NEO4J ENTITIES DEBUG ===")

    try:
        graphiti_client = get_graphiti_client()
        graphiti = await graphiti_client.ensure_ready()

        # Check entity group_ids
        driver = graphiti.driver

        # Query distinct group_ids
        result = await driver.execute_query("MATCH (e:Entity) RETURN DISTINCT e.group_id LIMIT 20")
        print(f"Entity group_ids: {[record['e.group_id'] for record in result.records]}")

        # Check specific entities
        entities_to_check = ['Марк', 'Сергей', 'План защиты', 'Щит смысла', 'Архетип Марка', 'Speaker', 'User Memory', 'персонаж']
        for entity_name in entities_to_check:
            result = await driver.execute_query("""
                MATCH (e:Entity {name: $name})
                RETURN e.name, e.summary, e.group_id, e.created_at
                LIMIT 1
            """, name=entity_name)

            if result.records:
                record = result.records[0]
                summary = record['e.summary'] or ""
                print(f"Entity '{entity_name}': group_id='{record['e.group_id']}', summary='{summary[:100]}...'")
            else:
                print(f"Entity '{entity_name}': NOT FOUND")

        # Check episodic group_ids
        result = await driver.execute_query("MATCH (n:Episodic) RETURN DISTINCT n.group_id, count(*) as cnt ORDER BY cnt DESC LIMIT 10")
        print("Episodic group_ids:")
        for record in result.records:
            print(f"  {record['n.group_id']}: {record['cnt']}")

    except Exception as e:
        print(f"Neo4j debug error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    async def main():
        await debug_memory_search()
        await debug_neo4j_entities()

    asyncio.run(main())