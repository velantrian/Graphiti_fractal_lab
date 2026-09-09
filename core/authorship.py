
import logging
from core.graphiti_client import get_graphiti_client

logger = logging.getLogger(__name__)

async def attach_author(episode_uuid: str, user_id: str):
    """
    Explicitly attaches an author to an episode via [:AUTHORED] relationship.
    Run this IMMEDIATELY after creating an episode.
    """
    if not episode_uuid or not user_id:
        logger.warning(f"Skipping attach_author: missing uuid={episode_uuid} or user_id={user_id}")
        return

    try:
        client = get_graphiti_client()
        graphiti = await client.ensure_ready()
        driver = graphiti.driver
        
        query = """
        MERGE (u:User {user_id:$user_id})
        WITH u
        MATCH (e:Episodic {uuid:$episode_uuid})
        MERGE (u)-[:AUTHORED]->(e)
        RETURN e.uuid AS uuid
        """
        
        result = await driver.execute_query(query, user_id=user_id, episode_uuid=episode_uuid)
        
        if result.records:
            logger.info(f"Attached author '{user_id}' to episode '{episode_uuid}'")
        else:
            logger.warning(f"Failed to attach author: episode '{episode_uuid}' not found?")
            
    except Exception as e:
        logger.error(f"Error attaching author for episode '{episode_uuid}': {e}")
