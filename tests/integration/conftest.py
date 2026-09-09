"""
Pytest fixtures for integration tests.
"""

import pytest
import os
import pytest_asyncio

# Skip all integration tests if NEO4J_URI is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_URI"),
    reason="NEO4J_URI not set - skipping integration tests"
)


@pytest_asyncio.fixture
async def graphiti_client():
    """
    Get Graphiti client for integration tests.
    
    Function-scoped: creates a new client for each test to avoid event loop conflicts.
    This ensures Neo4j async driver is bound to the correct event loop for each test.
    """
    from core.graphiti_client import get_graphiti_client, reset_graphiti_client
    
    # Create a new client instance (not singleton) for this test
    client = get_graphiti_client(force_new=True)
    graphiti = await client.ensure_ready()
    
    try:
        yield graphiti
    finally:
        # Cleanup: close Neo4j driver and reset singleton
        try:
            driver = getattr(graphiti, 'driver', None)
            if driver and hasattr(driver, 'close'):
                await driver.close()
        except Exception as e:
            # Log but don't fail on cleanup errors
            import logging
            logging.getLogger(__name__).warning(f"Error closing graphiti driver: {e}")
        finally:
            # Reset singleton so next test gets a fresh client
            reset_graphiti_client()


@pytest_asyncio.fixture
async def clean_test_data(graphiti_client):
    """
    Clean up test data before and after each test.
    
    Uses a specific test group_id to isolate test data.
    """
    test_group_id = "integration_test"
    driver = graphiti_client.driver
    
    # Clean before test
    await driver.execute_query(
        "MATCH (n) WHERE n.group_id = $gid DETACH DELETE n",
        gid=test_group_id
    )
    
    yield test_group_id
    
    # Clean after test
    await driver.execute_query(
        "MATCH (n) WHERE n.group_id = $gid DETACH DELETE n",
        gid=test_group_id
    )


@pytest_asyncio.fixture
async def memory_ops(graphiti_client):
    """Create MemoryOps instance for testing."""
    from core.memory_ops import MemoryOps
    
    return MemoryOps(graphiti_client, "test_user")


@pytest_asyncio.fixture
async def llm_client():
    """Get LLM client for testing."""
    from core.llm import get_async_client
    
    client = get_async_client()
    if not client:
        pytest.skip("OPENAI_API_KEY not set")
    return client
