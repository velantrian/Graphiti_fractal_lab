#!/usr/bin/env python3
"""
Debug chat to see what LLM receives
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.graphiti_client import get_graphiti_client
from core.memory_ops import MemoryOps
from simple_chat_agent import SimpleChatAgent
from core.llm import get_async_client

async def debug_chat():
    """Debug what happens in chat."""

    print("🔍 Debug chat processing...")

    # Setup
    graphiti_client = get_graphiti_client()
    graphiti = await graphiti_client.ensure_ready()
    memory = MemoryOps(graphiti, "sergey")
    llm_client = get_async_client()

    if not llm_client:
        print("❌ No LLM client")
        return

    agent = SimpleChatAgent(llm_client, memory)

    query = "Лена"

    # Get context
    print(f"Getting context for: {query}")
    context_result = await memory.build_context_for_query(
        query,
        max_tokens=2000,
        include_episodes=True,
        include_entities=True
    )

    print(f"Context tokens: {context_result.token_estimate}")
    print(f"Context text:\n{context_result.text}")
    print("-" * 50)

    # What LLM receives
    messages = [
                {
                    "role": "system",
                    "content": """You are a helpful AI assistant.

Use the provided context to answer questions. If the context contains information about people or topics, use that information in your answer.

Answer in Russian."""
                },
        {
            "role": "user",
            "content": f"""Context from memory:
{context_result.text}

User question: {query}

Please provide a helpful response based on the available context."""
        }
    ]

    print("Messages sent to LLM:")
    for msg in messages:
        print(f"{msg['role'].upper()}: {msg['content'][:200]}...")
        print()

    # Test LLM call
    print("Testing LLM call...")
    try:
        response = await llm_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()
        print(f"LLM Response: {reply}")
    except Exception as e:
        print(f"LLM Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_chat())