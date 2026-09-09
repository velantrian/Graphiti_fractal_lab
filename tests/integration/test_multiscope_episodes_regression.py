import pytest
from uuid import uuid4
from datetime import datetime, timezone

from core.memory_ops import MemoryOps
from tests.helpers.assertions import assert_no_group_leak


@pytest.mark.asyncio
async def test_multiscope_search_returns_episodes(graphiti_client):
    """
    Regression test: multi-scope search must not zero out episodic results on Neo4j.

    We insert two Episodic nodes in different group_id values and search by a unique marker.
    The search must return at least one episode under scopes=["personal","knowledge"].
    """
    g = graphiti_client
    driver = g.driver

    marker = f"alpha_marker_{uuid4().hex}"
    u1, u2 = str(uuid4()), str(uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    await driver.execute_query(
        """
        CREATE (e:Episodic {
          uuid: $u,
          name: "test_regression",
          content: $content,
          source: "text",
          group_id: $gid,
          created_at: $ts,
          valid_at: $ts,
          source_description: "test_regression",
          episode_kind: "test"
          ,entity_edges: []
        })
        """,
        u=u1,
        content=f"Документ A {marker} (content long enough for filters)",
        gid="personal",
        ts=ts,
    )
    await driver.execute_query(
        """
        CREATE (e:Episodic {
          uuid: $u,
          name: "test_regression",
          content: $content,
          source: "text",
          group_id: $gid,
          created_at: $ts,
          valid_at: $ts,
          source_description: "test_regression",
          episode_kind: "test"
          ,entity_edges: []
        })
        """,
        u=u2,
        content=f"Документ B {marker} (content long enough for filters)",
        gid="knowledge",
        ts=ts,
    )

    try:
        m = MemoryOps(g, "sergey")
        allowed = {"personal", "knowledge"}

        res = await m.search_memory(marker, scopes=["personal", "knowledge"], limit=10)
        assert res.total_episodes >= 1, "Expected episodes in multi-scope search, got 0"

        assert_no_group_leak(res.episodes, allowed)
        assert_no_group_leak(res.entities, allowed)
        assert_no_group_leak(res.edges, allowed)
        assert_no_group_leak(res.communities, allowed)

    finally:
        await driver.execute_query(
            "MATCH (e:Episodic) WHERE e.uuid IN [$u1,$u2] DETACH DELETE e",
            u1=u1,
            u2=u2,
        )


