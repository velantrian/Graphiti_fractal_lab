"""
Bootstrap utilities for initializing Graphiti and application state.
"""

from core.graphiti_client import get_graphiti_client


async def ensure_graphiti_ready():
    """
    Ensure Graphiti client is ready and initialized.
    
    Returns:
        Graphiti instance ready for use
    """
    client = get_graphiti_client()
    return await client.ensure_ready()

