"""P0–P3: Graphiti + FalkorDBLite deterministic memory e2e (lab only).

PASS requires Graphiti.search evidence (not raw Cypher).
No OpenAI/network LLM. No Fractal Neo4j migrations.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from graphiti_core.nodes import EpisodeType

from fractal_lab.experiments.falkor_graphiti_bootstrap import open_lab_graphiti

# redislite may emit this during teardown if aclose-only paths run; keep lab suite honest
# but do not fail the whole run on known redislite destructor noise.
pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:coroutine 'AsyncManagementCommands.shutdown' was never awaited:RuntimeWarning"
    ),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = REPO_ROOT / "artifacts" / "run_001"
FINDINGS = ARTIFACTS / "findings"
DATA_ROOT = REPO_ROOT / "data" / "falkor_e2e"
RECEIPT_PATH = ARTIFACTS / "result.json"


def _marker() -> str:
    return f"VELANTRIM_FALKOR_E2E_{uuid.uuid4().hex}"


def _fixture_text(marker: str, who: str = "Alice", other: str = "Bob") -> str:
    return (
        f"{who} collaborated with {other} at MarkerCorp on a synthetic lab project. "
        f"The unique retrieval token is {marker}. "
        f"{who} confirmed the token {marker} must remain searchable via Graphiti.search."
    )


def _edges_mention(edges, marker: str) -> list:
    hits = []
    for e in edges:
        blob = f"{getattr(e, 'fact', '')} {getattr(e, 'name', '')}"
        if marker in blob:
            hits.append(e)
    return hits


def _record(phase: str, test_id: str, status: str, evidence: dict, finding_id: str | None = None):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    receipt = {"phases": []}
    if RECEIPT_PATH.exists():
        try:
            receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = {"phases": []}
    entry = {
        "phase": phase,
        "test_id": test_id,
        "status": status,
        "evidence": evidence,
        "finding_id": finding_id,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    phases = receipt.setdefault("phases", [])
    phases = [p for p in phases if not (p.get("phase") == phase and p.get("test_id") == test_id)]
    phases.append(entry)
    receipt["phases"] = phases
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    if status == "FAIL" and finding_id:
        finding_path = FINDINGS / f"{finding_id}.md"
        finding_path.write_text(
            f"# {finding_id}\n\nphase: {phase}\ntest: {test_id}\n\n```json\n"
            f"{json.dumps(evidence, indent=2)}\n```\n",
            encoding="utf-8",
        )


@pytest.fixture()
def db_path(tmp_path_factory) -> Path:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    # Unique path per test function invocation
    p = DATA_ROOT / f"lab_{uuid.uuid4().hex}.db"
    return p


@pytest.mark.asyncio
async def test_t0_p1_bootstrap_connect_indices(db_path: Path):
    """T0/P1: connect + build_indices_and_constraints with deterministic providers."""
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        assert stack.graphiti is not None
        assert stack.driver.provider.value == "falkordb" or str(stack.driver.provider).endswith(
            "FALKORDB"
        )
        # Light query against default graph to prove indices path is live
        rows, _, _ = await stack.driver.execute_query("RETURN 1 AS ok")
        assert rows and rows[0].get("ok") == 1
        _record(
            "P1",
            "T0_bootstrap",
            "PASS",
            {
                "db_path": str(db_path),
                "database": stack.driver._database,
                "query_ok": rows[0].get("ok"),
            },
        )
    except Exception as exc:
        _record("P1", "T0_bootstrap", "FAIL", {"error": repr(exc)}, finding_id="F-P1-BOOTSTRAP")
        raise
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p1_t1_add_episode_search_marker(db_path: Path):
    """P1 T1: add_episode then Graphiti.search finds unique marker (not raw Cypher)."""
    marker = _marker()
    group_id = f"g_t1_{uuid.uuid4().hex[:12]}"
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        body = _fixture_text(marker)
        result = await stack.graphiti.add_episode(
            name=f"lab_episode_{marker[-8:]}",
            episode_body=body,
            source_description="fractal_lab_deterministic_e2e",
            reference_time=datetime.now(timezone.utc),
            source=EpisodeType.text,
            group_id=group_id,
        )
        assert result.episode is not None
        assert len(result.nodes) >= 1
        assert len(result.edges) >= 1, "Deterministic LLM must produce searchable edges"

        edges = await stack.graphiti.search(
            marker, group_ids=[group_id], num_results=10
        )
        hits = _edges_mention(edges, marker)
        evidence = {
            "marker": marker,
            "group_id": group_id,
            "nodes_created": [n.name for n in result.nodes],
            "edges_created_facts": [e.fact for e in result.edges],
            "search_result_count": len(edges),
            "search_hit_count": len(hits),
            "search_facts": [e.fact for e in edges],
        }
        if not hits:
            _record("P1", "T1_add_episode_search", "FAIL", evidence, finding_id="F-P1-SEARCH-MISS")
            pytest.fail(f"Graphiti.search did not retrieve marker {marker}: {evidence}")
        _record("P1", "T1_add_episode_search", "PASS", evidence)
    except Exception as exc:
        if "F-P1-SEARCH-MISS" not in str(exc):
            _record(
                "P1",
                "T1_add_episode_search",
                "FAIL",
                {"error": repr(exc), "marker": marker},
                finding_id="F-P1-T1-EXCEPTION",
            )
        raise
    finally:
        await stack.aclose()


_PERSIST_HELPER = r'''
import asyncio, json, sys
from pathlib import Path
from fractal_lab.experiments.falkor_graphiti_bootstrap import open_lab_graphiti

async def main(db_path: str, group_id: str, marker: str) -> int:
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        edges = await stack.graphiti.search(marker, group_ids=[group_id], num_results=10)
        facts = [getattr(e, "fact", "") for e in edges]
        hits = [f for f in facts if marker in f]
        print(json.dumps({"count": len(edges), "hits": len(hits), "facts": facts}))
        return 0 if hits else 2
    finally:
        await stack.aclose()

if __name__ == "__main__":
    db_path, group_id, marker = sys.argv[1], sys.argv[2], sys.argv[3]
    raise SystemExit(asyncio.run(main(db_path, group_id, marker)))
'''


@pytest.mark.asyncio
async def test_p2_persistence_reopen_subprocess(db_path: Path):
    """P2: after close, subprocess reopens SAME db path and Graphiti.search finds marker."""
    marker = _marker()
    group_id = f"g_p2_{uuid.uuid4().hex[:12]}"
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        await stack.graphiti.add_episode(
            name=f"persist_{marker[-8:]}",
            episode_body=_fixture_text(marker, who="Carol", other="Dave"),
            source_description="fractal_lab_persistence",
            reference_time=datetime.now(timezone.utc),
            source=EpisodeType.text,
            group_id=group_id,
        )
        # Sanity in-process before close
        edges = await stack.graphiti.search(marker, group_ids=[group_id], num_results=10)
        assert _edges_mention(edges, marker), "pre-close search must hit before persistence test"
    finally:
        await stack.aclose()

    helper = DATA_ROOT / f"persist_helper_{uuid.uuid4().hex}.py"
    helper.write_text(_PERSIST_HELPER, encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, str(helper), str(db_path), group_id, marker],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=180,
        check=False,
    )
    evidence = {
        "marker": marker,
        "group_id": group_id,
        "db_path": str(db_path),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }
    if proc.returncode != 0:
        _record("P2", "persistence_reopen", "FAIL", evidence, finding_id="F-P2-PERSIST-MISS")
        pytest.fail(f"subprocess reopen search failed: {evidence}")
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    evidence["payload"] = payload
    _record("P2", "persistence_reopen", "PASS", evidence)


@pytest.mark.asyncio
async def test_p3_group_isolation_no_vanish_no_leak(db_path: Path):
    """P3: write A, search A; write B, search B; search A again — A survives; no B→A leak.

    Observes Falkor multi-group / driver-rebind behavior (upstream multi-tenant issues).
    If A disappears after B, FAIL with finding — do not workaround.
    """
    marker_a = _marker()
    marker_b = _marker()
    group_a = f"groupA_{uuid.uuid4().hex[:10]}"
    group_b = f"groupB_{uuid.uuid4().hex[:10]}"
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        await stack.graphiti.add_episode(
            name=f"ep_a_{marker_a[-8:]}",
            episode_body=_fixture_text(marker_a, who="Alice", other="Alpha"),
            source_description="group_a_fixture",
            reference_time=datetime.now(timezone.utc),
            source=EpisodeType.text,
            group_id=group_a,
        )
        edges_a1 = await stack.graphiti.search(marker_a, group_ids=[group_a], num_results=10)
        hits_a1 = _edges_mention(edges_a1, marker_a)
        assert hits_a1, f"A must be searchable before B write; got { [e.fact for e in edges_a1] }"

        await stack.graphiti.add_episode(
            name=f"ep_b_{marker_b[-8:]}",
            episode_body=_fixture_text(marker_b, who="Bob", other="Beta"),
            source_description="group_b_fixture",
            reference_time=datetime.now(timezone.utc),
            source=EpisodeType.text,
            group_id=group_b,
        )
        edges_b = await stack.graphiti.search(marker_b, group_ids=[group_b], num_results=10)
        hits_b = _edges_mention(edges_b, marker_b)
        assert hits_b, f"B must be searchable; got {[e.fact for e in edges_b]}"

        # B must not appear in A-only search for marker_b
        leak_b_in_a = await stack.graphiti.search(marker_b, group_ids=[group_a], num_results=10)
        leak_hits = _edges_mention(leak_b_in_a, marker_b)

        # A must still be found after B write (no vanish)
        edges_a2 = await stack.graphiti.search(marker_a, group_ids=[group_a], num_results=10)
        hits_a2 = _edges_mention(edges_a2, marker_a)

        # Also check A marker does not leak into B-only search
        leak_a_in_b = await stack.graphiti.search(marker_a, group_ids=[group_b], num_results=10)
        leak_a_hits = _edges_mention(leak_a_in_b, marker_a)

        evidence = {
            "group_a": group_a,
            "group_b": group_b,
            "marker_a": marker_a,
            "marker_b": marker_b,
            "hits_a_before_b": len(hits_a1),
            "hits_b": len(hits_b),
            "hits_a_after_b": len(hits_a2),
            "b_leak_into_a": len(leak_hits),
            "a_leak_into_b": len(leak_a_hits),
            "driver_database_after": getattr(stack.graphiti.driver, "_database", None),
            "facts_a_after": [e.fact for e in edges_a2],
            "facts_b": [e.fact for e in edges_b],
            "facts_b_in_a_search": [e.fact for e in leak_b_in_a],
        }

        if not hits_a2:
            _record(
                "P3",
                "group_isolation",
                "FAIL",
                evidence,
                finding_id="F-P3-GROUP-A-VANISH",
            )
            pytest.fail(
                "Group A marker vanished from Graphiti.search after writing group B "
                "(Falkor multi-group / driver rebind). Evidence recorded as F-P3-GROUP-A-VANISH."
            )
        if leak_hits:
            _record(
                "P3",
                "group_isolation",
                "FAIL",
                evidence,
                finding_id="F-P3-GROUP-B-LEAK-INTO-A",
            )
            pytest.fail("Group B marker leaked into A-only search")
        if leak_a_hits:
            _record(
                "P3",
                "group_isolation",
                "FAIL",
                evidence,
                finding_id="F-P3-GROUP-A-LEAK-INTO-B",
            )
            pytest.fail("Group A marker leaked into B-only search")

        _record("P3", "group_isolation", "PASS", evidence)
    except Exception as exc:
        # Avoid double-recording if we already wrote a FAIL above
        if RECEIPT_PATH.exists():
            data = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
            already = any(
                p.get("phase") == "P3" and p.get("status") == "FAIL" for p in data.get("phases", [])
            )
        else:
            already = False
        if not already:
            _record(
                "P3",
                "group_isolation",
                "FAIL",
                {"error": repr(exc)},
                finding_id="F-P3-EXCEPTION",
            )
        raise
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_t3_negative_control_nonexistent_marker(db_path: Path):
    """Optional T3: nonexistent marker must NOT be retrieved after a real write."""
    real_marker = _marker()
    missing = f"VELANTRIM_FALKOR_E2E_NOT_RETRIEVED_{uuid.uuid4().hex}"
    group_id = f"g_t3_{uuid.uuid4().hex[:12]}"
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        await stack.graphiti.add_episode(
            name=f"neg_{real_marker[-8:]}",
            episode_body=_fixture_text(real_marker, who="Eve", other="Frank"),
            source_description="negative_control",
            reference_time=datetime.now(timezone.utc),
            source=EpisodeType.text,
            group_id=group_id,
        )
        real_edges = await stack.graphiti.search(real_marker, group_ids=[group_id], num_results=10)
        assert _edges_mention(real_edges, real_marker), "positive control must hit"

        miss_edges = await stack.graphiti.search(missing, group_ids=[group_id], num_results=10)
        miss_hits = _edges_mention(miss_edges, missing)
        evidence = {
            "real_marker": real_marker,
            "missing_marker": missing,
            "positive_hits": len(_edges_mention(real_edges, real_marker)),
            "negative_hits": len(miss_hits),
            "negative_facts": [e.fact for e in miss_edges],
        }
        if miss_hits:
            _record("T3", "negative_control", "FAIL", evidence, finding_id="F-T3-FALSE-POSITIVE")
            pytest.fail("nonexistent marker was retrieved")
        _record("T3", "negative_control", "PASS", evidence)
    finally:
        await stack.aclose()
