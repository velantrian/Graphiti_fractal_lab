from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "please_change_me")

driver = GraphDatabase.driver(uri, auth=(user, password))

def normalize_names():
    with driver.session() as session:
        print("Normalizing entity names...")
        result = session.run("""
            MATCH (e:Entity)
            WHERE e.name IS NOT NULL
            SET e.name_norm = toLower(trim(e.name))
            RETURN count(e) as updated_count
        """)
        cnt = result.single()["updated_count"]
        print(f"Updated {cnt} entities with name_norm.")

    driver.close()

if __name__ == "__main__":
    normalize_names()
