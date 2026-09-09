from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "please_change_me")

driver = GraphDatabase.driver(uri, auth=(user, password))

def run_diagnostics():
    with driver.session() as session:
        print("--- Query 1: Episodic Nodes ---")
        result1 = session.run("""
            MATCH (ep:Episodic)
            RETURN ep.uuid as uuid, labels(ep) as labels, ep.group_id as group_id, ep.name as name
            LIMIT 3
        """)
        for record in result1:
            print(record.data())

        print("\n--- Query 2: MENTIONS Relationships ---")
        # Check directionality explicitly
        result2 = session.run("""
            MATCH (ep:Episodic)-[r:MENTIONS]-(e:Entity)
            RETURN type(r) as t, count(*) as c, startNode(r) = ep as is_source_ep, endNode(r) = ep as is_target_ep
            LIMIT 5
        """)
        for record in result2:
            print(record.data())

    driver.close()

if __name__ == "__main__":
    run_diagnostics()
