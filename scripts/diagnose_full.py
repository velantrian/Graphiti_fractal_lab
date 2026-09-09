from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "please_change_me")

driver = GraphDatabase.driver(uri, auth=(user, password))

def run_full_diagnostics():
    with driver.session() as session:
        print("\n--- 1.1 Entity Counts by Layer ---")
        result1 = session.run("""
            MATCH (e:Entity)
            RETURN e.group_id as group_id, count(*) as cnt
            ORDER BY cnt DESC
        """)
        for record in result1:
            print(record.data())

        print("\n--- 1.2 Cross-Layer Duplicates (Exact Name Match) ---")
        result2 = session.run("""
            MATCH (e:Entity)
            WHERE e.name IS NOT NULL
            WITH toLower(trim(e.name)) AS key, collect(e) AS ents, collect(DISTINCT e.group_id) AS gids
            WHERE size(gids) > 1 AND size(ents) > 1
            RETURN key, [x IN ents | {uuid:x.uuid, group_id:x.group_id, name:x.name}] AS entities
            LIMIT 10
        """)
        for record in result2:
            print(record.data())

        print("\n--- 1.3 Existing Entity-Entity Relations ---")
        result3 = session.run("""
            MATCH ()-[r:RELATES_TO]->()
            RETURN count(r) as relates_to_cnt
        """)
        for record in result3:
            print(record.data())

    driver.close()

if __name__ == "__main__":
    run_full_diagnostics()
