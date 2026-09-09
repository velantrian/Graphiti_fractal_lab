
import logging
from core.graphiti_client import get_graphiti_client

logger = logging.getLogger(__name__)

async def ensure_user_identity_entity(user_id: str, person_name: str = "Сергей"):
    """
    Ensures that a semantic Entity representing the person exists
    and is linked to the User account via [:IS].
    
    Creates:
    (p:Entity {name: $person_name, group_id: "personal"})
    (u:User {user_id: $user_id})
    (u)-[:IS]->(p)
    """
    if not user_id:
        return

    try:
        client = get_graphiti_client()
        graphiti = await client.ensure_ready()
        driver = graphiti.driver
        
        # We ensure the Entity exists as a semantic node (not just episodic)
        query = """
        MERGE (u:User {user_id: $user_id})
        MERGE (p:Entity {name: $person_name})
        ON CREATE SET p.group_id = 'personal', p.created_at = datetime()
        MERGE (u)-[:IS]->(p)
        RETURN u.user_id, p.name
        """
        
        result = await driver.execute_query(query, user_id=user_id, person_name=person_name)
        
        if result.records:
            logger.info(f"[IDENTITY] Verified identity: User('{user_id}') -[:IS]-> Entity('{person_name}')")
        
    except Exception as e:
        logger.error(f"[IDENTITY] Failed to ensure identity for {user_id}: {e}")
