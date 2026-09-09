#!/usr/bin/env python3
from __future__ import annotations

"""
Read-only audit of group_id coverage and distributions.

Runs queries from scripts/audit_group_ids.cypher via Graphiti's Neo4j driver and prints a compact report.

Usage:
  docker compose exec -T app python scripts/audit_group_ids.py
"""

from pathlib import Path


def _split_cypher(text: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(buf).strip()
            stmt = stmt[:-1].strip()
            if stmt:
                parts.append(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _print_records(records) -> None:
    if not records:
        print("(no records)")
        return
    # Print dict rows (truncate long strings)
    for rec in records:
        d = dict(rec)
        for k, v in list(d.items()):
            if isinstance(v, str) and len(v) > 200:
                d[k] = v[:200] + "…"
        print(d)


async def main() -> None:
    from core.graphiti_client import get_graphiti_client

    graphiti = await get_graphiti_client().ensure_ready()
    driver = graphiti.driver

    cypher_path = Path(__file__).resolve().parent / "audit_group_ids.cypher"
    raw = cypher_path.read_text(encoding="utf-8")
    statements = _split_cypher(raw)

    for i, stmt in enumerate(statements, start=1):
        head = stmt.splitlines()[0][:90]
        print(f"\n=== [{i}/{len(statements)}] {head} ===")
        res = await driver.execute_query(stmt)
        _print_records(getattr(res, "records", None) or [])


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


