import os
import sys
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup_test_data")

load_dotenv()

TEST_GROUPS = ["group_a", "group_b", "testing_layer"]

def cleanup_test_data():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "please_change_me")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        logger.info(f"Starting cleanup for groups: {TEST_GROUPS}")
        
        # Delete relationships first (to avoid orphan issues, though Neo4j handles it with DETACH DELETE)
        # Delete nodes in test groups
        res = session.run("""
            MATCH (n)
            WHERE n.group_id IN $groups
            DETACH DELETE n
            RETURN count(n) as deleted_count
        """, groups=TEST_GROUPS)
        
        deleted = res.single()['deleted_count']
        logger.info(f"Cleanup complete. Deleted {deleted} nodes and their relationships.")

    driver.close()

if __name__ == "__main__":
    confirm = input(f"Are you sure you want to delete all data from {TEST_GROUPS}? (y/n): ")
    if confirm.lower() == 'y':
        cleanup_test_data()
    else:
        logger.info("Cleanup cancelled.")
