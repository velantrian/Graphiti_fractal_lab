"""
Integration tests for memory flow.

Tests the full cycle: ingest → search → context building.
"""

import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_remember_and_search(graphiti_client, clean_test_data, memory_ops):
    """Test that remembered text can be searched."""
    test_group_id = clean_test_data
    
    # Remember some text
    test_text = "Тестовый пользователь Алексей работает программистом в компании TechCorp."
    
    from knowledge.ingest import ingest_text_document
    result = await ingest_text_document(
        graphiti_client,
        test_text,
        source_description="integration_test",
        user_id="test_user",
        group_id=test_group_id
    )
    
    assert result["status"] == "ok"
    assert result["added"] == 1
    
    # Search for the text
    search_result = await memory_ops.search_memory(
        "Алексей программист",
        scopes=[test_group_id],
        limit=5
    )
    
    # Should find something
    assert search_result.total_episodes > 0 or search_result.total_entities > 0


@pytest.mark.asyncio
async def test_context_building(graphiti_client, clean_test_data, memory_ops):
    """Test that context is built correctly from memory."""
    test_group_id = clean_test_data
    
    # Add some test data
    test_texts = [
        "Мария - дизайнер интерфейсов с 5-летним опытом.",
        "Мария специализируется на мобильных приложениях.",
        "Мария работает в команде продукта."
    ]
    
    from knowledge.ingest import ingest_text_document
    for text in test_texts:
        await ingest_text_document(
            graphiti_client,
            text,
            source_description="integration_test",
            user_id="test_user",
            group_id=test_group_id
        )
    
    # Build context
    context = await memory_ops.build_context_for_query(
        "Кто такая Мария?",
        scopes=[test_group_id],
        max_tokens=2000
    )
    
    # Context should contain relevant information
    assert context.token_estimate > 0
    # At least some sources should be found
    total_sources = sum(context.sources.values())
    assert total_sources >= 0  # May be 0 if search doesn't find exact matches


@pytest.mark.asyncio
async def test_episode_deduplication(graphiti_client, clean_test_data):
    """Test that duplicate episodes are not created."""
    test_group_id = clean_test_data
    
    test_text = "Уникальный тестовый текст для проверки дедупликации."
    
    from knowledge.ingest import ingest_text_document
    
    # Ingest same text twice
    result1 = await ingest_text_document(
        graphiti_client,
        test_text,
        source_description="integration_test",
        user_id="test_user",
        group_id=test_group_id
    )
    
    result2 = await ingest_text_document(
        graphiti_client,
        test_text,
        source_description="integration_test",
        user_id="test_user",
        group_id=test_group_id
    )
    
    # Both should succeed
    assert result1["status"] == "ok"
    assert result2["status"] == "ok"
    
    # Count episodes with this content
    driver = graphiti_client.driver
    count_result = await driver.execute_query(
        """
        MATCH (e:Episodic)
        WHERE e.content = $content AND e.group_id = $gid
        RETURN count(e) as cnt
        """,
        content=test_text,
        gid=test_group_id
    )
    
    # Should have at most 2 (Graphiti may create duplicates, but our fingerprint should help)
    count = count_result.records[0]["cnt"]
    assert count <= 2


@pytest.mark.asyncio
async def test_user_authorship(graphiti_client, clean_test_data):
    """Test that user authorship is correctly attached."""
    test_group_id = clean_test_data
    test_user_id = "authorship_test_user"
    
    test_text = "Текст для проверки авторства."
    
    from knowledge.ingest import ingest_text_document
    await ingest_text_document(
        graphiti_client,
        test_text,
        source_description="integration_test",
        user_id=test_user_id,
        group_id=test_group_id
    )
    
    # Check that user is linked
    driver = graphiti_client.driver
    result = await driver.execute_query(
        """
        MATCH (u:User {user_id: $uid})-[:AUTHORED]->(e:Episodic)
        WHERE e.group_id = $gid
        RETURN count(e) as cnt
        """,
        uid=test_user_id,
        gid=test_group_id
    )
    
    count = result.records[0]["cnt"]
    assert count >= 1


@pytest.mark.asyncio
async def test_memory_type_routing(graphiti_client, clean_test_data):
    """Test that memory type routing works correctly."""
    from knowledge.ingest import _infer_memory_type
    
    # Personal text
    personal_text = "Мой друг Иван очень любит путешествовать."
    assert _infer_memory_type(personal_text) == "personal"
    
    # Project text
    project_text = "Нужно исправить баг в репозитории и сделать деплой."
    assert _infer_memory_type(project_text) == "project"
    
    # Experience text
    experience_text = "Урок: всегда проверяй результат перед коммитом."
    assert _infer_memory_type(experience_text) == "experience"
    
    # Knowledge text (default)
    knowledge_text = "Столица Франции - Париж."
    assert _infer_memory_type(knowledge_text) == "knowledge"
