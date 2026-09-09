
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.identity import ensure_user_identity_entity
from core.graphiti_client import get_graphiti_client

async def run_seed():
    print("Seeding Identity...")
    await ensure_user_identity_entity("sergey", "Сергей")
    
    print("\nVerifying Link...")
    client = get_graphiti_client()
    graphiti = await client.ensure_ready()
    driver = graphiti.driver
    
    query = """
    MATCH (u:User {user_id:"sergey"})-[:IS]->(p:Entity {name:"Сергей"}) 
    RETURN count(*) AS cnt, p.group_id AS gid
    """
    result = await driver.execute_query(query)
    
    if result.records:
        rec = result.records[0]
        print(f"Success! Count: {rec['cnt']}, Group: {rec['gid']}")
        if rec['cnt'] >= 1:
            print("VERIFICATION PASSED")
        else:
            print("VERIFICATION FAILED")
    else:
        print("VERIFICATION FAILED (No records)")

if __name__ == "__main__":
    asyncio.run(run_seed())

