#!/usr/bin/env python3
"""
Analyze graph structure for user/sergey relationships.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.graphiti_client import get_graphiti_client


async def analyze_graph():
    """Analyze graph structure."""
    print("=== GRAPH ANALYSIS ===")

    try:
        graphiti_client = get_graphiti_client()
        graphiti = await graphiti_client.ensure_ready()
        driver = graphiti.driver

        print("\n1. Node counts by label:")
        result = await driver.execute_query("""
            MATCH (n)
            UNWIND labels(n) AS label
            RETURN label, count(*) AS count
            ORDER BY count DESC
        """)

        for record in result.records:
            print(f"  {record['label']}: {record['count']}")

        print("\n2. Episodic nodes by name pattern:")
        result = await driver.execute_query("""
            MATCH (n:Episodic)
            RETURN n.name, count(*) AS count
            ORDER BY count DESC
            LIMIT 10
        """)

        for record in result.records:
            print(f"  '{record['n.name']}': {record['count']}")

        print("\n3. User nodes:")
        result = await driver.execute_query("""
            MATCH (u:User)
            RETURN u.user_id, u.name
            ORDER BY u.user_id
        """)

        for record in result.records:
            print(f"  User ID: {record['u.user_id']}, Name: {record.get('u.name', 'N/A')}")

        print("\n4. User relationships:")
        result = await driver.execute_query("""
            MATCH (u:User)-[r]->(n)
            RETURN u.user_id, type(r), labels(n), n.name, count(*) AS count
            ORDER BY count DESC
            LIMIT 10
        """)

        for record in result.records:
            print(f"  {record['u.user_id']} -[{record['type(r)']}]-> {record['labels(n)'][0]} '{record['n.name'][:50]}...': {record['count']}")

        print("\n5. Entity nodes related to Sergey:")
        result = await driver.execute_query("""
            MATCH (e:Entity {name: 'Сергей'})
            RETURN e.name, e.summary
            LIMIT 1
        """)

        for record in result.records:
            summary = record['e.summary'][:100] + "..." if len(record['e.summary']) > 100 else record['e.summary']
            print(f"  Сергей entity: {summary}")

        print("\n6. Recent Episodic nodes:")
        result = await driver.execute_query("""
            MATCH (n:Episodic)
            WHERE n.created_at IS NOT NULL
            RETURN n.name, n.group_id, n.created_at
            ORDER BY n.created_at DESC
            LIMIT 5
        """)

        for record in result.records:
            print(f"  {record['n.name']} (group: {record['n.group_id']}, created: {record['n.created_at']})")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(analyze_graph())