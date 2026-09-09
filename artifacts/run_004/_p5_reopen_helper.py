
import asyncio, json, sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure src on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src") if False else "")
# Caller sets PYTHONPATH=src

from fractal_lab.experiments.deterministic_temporal_llm import DeterministicTemporalLLMClient
from fractal_lab.experiments.falkor_graphiti_bootstrap import open_lab_graphiti
from graphiti_core.driver.driver import GraphProvider
from graphiti_core.edges import EntityEdge

async def main(db_path: str, group_id: str, old_m: str, new_m: str) -> int:
    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True, llm_client=client)
    try:
        try:
            driver = stack.graphiti.driver
            if group_id != getattr(driver, "_database", None):
                driver = driver.clone(database=group_id)
            edges = await EntityEdge.get_by_group_ids(driver, [group_id])
        except Exception as exc:
            print(json.dumps({"error": repr(exc), "edges": []}))
            return 3
        def pub(e):
            return {
                "uuid": e.uuid,
                "name": e.name,
                "fact": e.fact,
                "valid_at": e.valid_at.isoformat() if e.valid_at else None,
                "invalid_at": e.invalid_at.isoformat() if e.invalid_at else None,
                "expired_at": e.expired_at.isoformat() if e.expired_at else None,
            }
        old = [pub(e) for e in edges if old_m in (e.fact or "")]
        new = [pub(e) for e in edges if new_m in (e.fact or "")]
        owner = [pub(e) for e in edges if "owned by Alice" in (e.fact or "").lower() or e.name == "OWNED_BY"]
        out = {"old": old, "new": new, "owner": owner, "count": len(edges)}
        print(json.dumps(out))
        if not old or not new:
            return 2
        if old[0].get("invalid_at") is None:
            return 4
        return 0
    finally:
        await stack.aclose()

if __name__ == "__main__":
    db_path, group_id, old_m, new_m = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    raise SystemExit(asyncio.run(main(db_path, group_id, old_m, new_m)))
