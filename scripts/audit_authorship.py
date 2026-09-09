
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.graphiti_client import get_graphiti_client

async def run_audit():
    print("Connecting to Neo4j...")
    try:
        client = get_graphiti_client()
        graphiti = await client.ensure_ready()
        driver = graphiti.driver
        
        print("\n=== 1. Existing Authorship Links ===")
        query1 = """
        MATCH (u:User)-[r:AUTHORED]->(e:Episodic)
        RETURN u.user_id AS user_id, e.group_id AS group_id, count(*) AS cnt
        ORDER BY cnt DESC;
        """
        result1 = await driver.execute_query(query1)
        if not result1.records:
            print("No existing AUTHORED relationships found.")
        for record in result1.records:
            print(f"User: {record['user_id']}, Group: {record['group_id']}, Count: {record['cnt']}")

        print("\n=== 2. Orphan Episodes (No Author) Stats ===")
        query2 = """
        MATCH (e:Episodic)
        WHERE NOT EXISTS { MATCH (:User)-[:AUTHORED]->(e) }
        RETURN e.group_id AS group_id, e.source_description AS src, count(*) AS cnt
        ORDER BY cnt DESC;
        """
        result2 = await driver.execute_query(query2)
        if not result2.records:
            print("No orphan episodes found.")
        for record in result2.records:
            print(f"Group: {record['group_id']}, Source: {record['src']}, Count: {record['cnt']}")

        print("\n=== 3. Orphan Episodes Examples (Top 10) ===")
        query3 = """
        MATCH (e:Episodic)
        WHERE NOT EXISTS { MATCH (:User)-[:AUTHORED]->(e) }
        RETURN e.uuid AS uuid, e.group_id AS group_id, e.source AS source, e.source_description AS src, substring(e.content, 0, 120) AS preview
        LIMIT 10;
        """
        result3 = await driver.execute_query(query3)
        for record in result3.records:
            print(f"UUID: {record['uuid']}")
            print(f"  Group: {record['group_id']}")
            print(f"  Source: {record['source']}, Desc: {record['src']}")
            print(f"  Preview: {record['preview']}")
            print("-" * 40)

        print("\n=== 4. User <-> Entity 'Сергей' Link ===")
        query4 = """
        MATCH (u:User {user_id:"sergey"})-[r:IS]->(p:Entity {name:"Сергей"})
        RETURN u, p;
        """
        result4 = await driver.execute_query(query4)
        if result4.records:
            print("Link exists: User(sergey) -[:IS]-> Entity(Сергей)")
        else:
            print("Link DOES NOT exist.")
            
            # Check if User exists at all
            check_user = await driver.execute_query('MATCH (u:User {user_id:"sergey"}) RETURN u')
            if check_user.records:
                print("  -> User node 'sergey' EXISTS.")
            else:
                print("  -> User node 'sergey' DOES NOT exist.")
                
            # Check if Entity exists
            check_entity = await driver.execute_query('MATCH (e:Entity {name:"Сергей"}) RETURN e')
            if check_entity.records:
                print("  -> Entity node 'Сергей' EXISTS.")
            else:
                print("  -> Entity node 'Сергей' DOES NOT exist.")

    except Exception as e:
        print(f"Error during audit: {e}")
    finally:
        # We don't explicitly close the driver here as it might be shared, but for a script it's fine.
        pass

if __name__ == "__main__":
    asyncio.run(run_audit())
