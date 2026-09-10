#!/usr/bin/env python3
"""Lab MemoryOps CLI: ingest | query | inspect | demo | reopen-query.

Usage (from repo root, with .venv active / PYTHONPATH=src):
  python -m fractal_lab.memoryops.cli ingest --db PATH --group GID --text "..."
  python -m fractal_lab.memoryops.cli query  --db PATH --group GID --text "..." [--query-time ISO] [--provenance]
  python -m fractal_lab.memoryops.cli inspect --db PATH --group GID [--provenance]
  python -m fractal_lab.memoryops.cli demo --db PATH
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def _run(args: argparse.Namespace) -> int:
    from fractal_lab.memoryops.service import LabMemoryOps

    mem = await LabMemoryOps.open(args.db, default_group_id=args.group or "fm_default")
    try:
        if args.command == "ingest":
            receipt = await mem.ingest(
                args.text,
                group_id=args.group,
                reference_time=_parse_dt(args.reference_time),
                name=args.name,
            )
        elif args.command == "query":
            receipt = await mem.query(
                args.text,
                group_id=args.group,
                num_results=args.limit,
                query_time=_parse_dt(getattr(args, "query_time", None)),
                with_provenance=bool(getattr(args, "provenance", False)),
            )
        elif args.command == "inspect":
            receipt = await mem.inspect(
                group_id=args.group,
                with_provenance=bool(getattr(args, "provenance", False)),
            )
        elif args.command == "reopen-query":
            receipt = await mem.reopen_query(
                args.text,
                group_id=args.group,
                num_results=args.limit,
                query_time=_parse_dt(getattr(args, "query_time", None)),
                with_provenance=bool(getattr(args, "provenance", False)),
            )
        elif args.command == "demo":
            g = args.group or "fm_demo"
            t1 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
            receipts = []
            receipts.append(
                (
                    await mem.ingest(
                        "Alice works on ProjectOrion.",
                        group_id=g,
                        reference_time=t1,
                        name="demo_t1",
                    )
                ).to_dict()
            )
            receipts.append(
                (
                    await mem.ingest(
                        "ProjectOrion uses Python.",
                        group_id=g,
                        reference_time=t1,
                        name="demo_t2",
                    )
                ).to_dict()
            )
            receipts.append((await mem.query("Who works on ProjectOrion?", group_id=g)).to_dict())
            receipts.append((await mem.inspect(group_id=g)).to_dict())
            print(json.dumps({"demo_receipts": receipts}, indent=2, default=str))
            return 0
        else:
            print(f"unknown command: {args.command}", file=sys.stderr)
            return 2
        print(json.dumps(receipt.to_dict(), indent=2, default=str))
        return 0
    finally:
        await mem.aclose()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Lab MemoryOps (FalkorDBLite) CLI")
    p.add_argument("--db", required=True, type=Path, help="FalkorDBLite on-disk DB path")
    p.add_argument("--group", default=None, help="group_id / scope")
    sub = p.add_subparsers(dest="command", required=True)

    ing = sub.add_parser("ingest", help="MEMORY INGEST")
    ing.add_argument("--text", required=True)
    ing.add_argument("--reference-time", default=None)
    ing.add_argument("--name", default=None)

    q = sub.add_parser("query", help="MEMORY QUERY")
    q.add_argument("--text", required=True)
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--query-time", default=None, help="ISO evaluation time for FM-9 classify")
    q.add_argument("--provenance", action="store_true", help="Attach FM-10 provenance receipts")

    insp = sub.add_parser("inspect", help="MEMORY INSPECT")
    insp.add_argument("--provenance", action="store_true")

    rq = sub.add_parser("reopen-query", help="MEMORY REOPEN query (no ingest)")
    rq.add_argument("--text", required=True)
    rq.add_argument("--limit", type=int, default=10)
    rq.add_argument("--query-time", default=None)
    rq.add_argument("--provenance", action="store_true")

    sub.add_parser("demo", help="Small ingest+query+inspect demo")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
