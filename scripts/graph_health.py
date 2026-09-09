from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "please_change_me")

driver = GraphDatabase.driver(uri, auth=(user, password))

def run_health_check():
    with driver.session() as session:
        print("\n=== Graph Health & Connectivity Check ===\n")

        # 1. General Stats
        print("--- 1. General Statistics ---")
        res = session.run("""
            MATCH (e:Entity)
            RETURN count(e) as entities
        """)
        entities = res.single()['entities']
        
        res = session.run("""
            MATCH ()-[r:RELATES_TO]->()
            RETURN count(r) as relations
        """)
        relations = res.single()['relations']
        
        res = session.run("""
            MATCH (ep:Episodic)
            RETURN count(ep) as episodes
        """)
        episodes = res.single()['episodes']
        
        print(f"Entities: {entities}")
        print(f"Relations (RELATES_TO): {relations}")
        print(f"Episodes: {episodes}")

        # 2. Bridge Stats
        print("\n--- 2. Connectivity (Bridges) ---")
        res = session.run("""
            MATCH ()-[r:SAME_AS]->()
            RETURN count(r) as bridges
        """)
        bridges = res.single()['bridges']
        print(f"Total SAME_AS bridges: {bridges}")

        # Entities with SAME_AS
        res = session.run("""
            MATCH (e:Entity)-[:SAME_AS]-()
            RETURN count(DISTINCT e) as bridged_entities
        """)
        bridged = res.single()['bridged_entities']
        print(f"Entities involved in bridges: {bridged} ({bridged/entities*100:.1f}%)" if entities > 0 else "Entities: 0")

        # 3. Top Bridges
        print("\n--- 3. Top Bridged Entities ---")
        res = session.run("""
            MATCH (e:Entity)-[r:SAME_AS]-(other)
            RETURN e.name as name, e.group_id as group_id, count(r) as degree, collect(other.group_id) as connected_groups
            ORDER BY degree DESC
            LIMIT 5
        """)
        for r in res:
            groups = set(r['connected_groups'])
            print(f"- {r['name']} ({r['group_id']}): {r['degree']} links -> {groups}")

        # 4. Layer Isolation Check
        print("\n--- 4. Layer Stats ---")
        res = session.run("""
            MATCH (e:Entity)
            RETURN e.group_id as group_id, count(e) as count
            ORDER BY count DESC
        """)
        print("Entity counts by layer:")
        for r in res:
            print(f"  {r['group_id']}: {r['count']}")

    driver.close()

if __name__ == "__main__":
    run_health_check()
