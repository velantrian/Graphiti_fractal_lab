"""P5: Deterministic temporal update / contradiction (lab only).

Anti-hallucination labels:
  FIXTURE_FAIL — provider/fixture broken (STOP before Graphiti claims)
  GRAPHITI_TEMPORAL_CONTRADICTION_FAIL — fixture OK but Graphiti did not invalidate
  INCONCLUSIVE — cannot classify from available evidence

search hit ≠ currently applicable — classify STORED / RETRIEVABLE /
TEMPORALLY_CURRENT / TEMPORALLY_EXPIRED from edge metadata.

Uses DeterministicTemporalLLMClient only (not DeterministicLLMClient).
Does NOT start P6 / Fractal MemoryOps / Crystal / SVL / Ladybug / real LLM.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodeType
from graphiti_core.prompts.dedupe_edges import EdgeDuplicate
from graphiti_core.prompts.extract_edges import EdgeTimestamps
from graphiti_core.prompts.models import Message

from fractal_lab.experiments.deterministic_temporal_llm import DeterministicTemporalLLMClient
from fractal_lab.experiments.falkor_graphiti_bootstrap import open_lab_graphiti

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:coroutine 'AsyncManagementCommands.shutdown' was never awaited:RuntimeWarning"
    ),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = REPO_ROOT / "artifacts" / "run_004"
FINDINGS = ARTIFACTS / "findings"
DATA_ROOT = REPO_ROOT / "data" / "falkor_e2e_p5"
RECEIPT_PATH = ARTIFACTS / "result.json"
PROVIDER_RECEIPT = ARTIFACTS / "provider_decision_receipt.json"
EDGE_DUMP = ARTIFACTS / "raw_edge_dump.json"

T1 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
Q1 = datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc)  # between T1 and T2
Q2 = datetime(2026, 1, 3, 10, 0, 0, tzinfo=timezone.utc)  # after T2

# Module gate: P5-0 must pass before Graphiti phases.
_P5_0_OK: bool | None = None
_P5_0_EVIDENCE: dict | None = None

# Shared state across ordered phases (single db / markers)
_STATE: dict[str, Any] = {}


def _uuid() -> str:
    return uuid.uuid4().hex


def _dt_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _approx_eq(a: datetime | None, b: datetime | None, *, tol_seconds: float = 1.0) -> bool:
    if a is None or b is None:
        return a is b
    return abs((a - b).total_seconds()) <= tol_seconds


def _record(phase: str, test_id: str, status: str, evidence: dict, finding_id: str | None = None):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    receipt: dict = {"phases": [], "matrix": {}}
    if RECEIPT_PATH.exists():
        try:
            receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = {"phases": [], "matrix": {}}
    entry = {
        "phase": phase,
        "test_id": test_id,
        "status": status,
        "evidence": evidence,
        "finding_id": finding_id,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    phases = [
        p
        for p in receipt.setdefault("phases", [])
        if not (p.get("phase") == phase and p.get("test_id") == test_id)
    ]
    phases.append(entry)
    receipt["phases"] = phases
    receipt.setdefault("matrix", {})[test_id] = status
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    if status in {"FAIL", "FIXTURE_FAIL", "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL", "BLOCKED"} and finding_id:
        (FINDINGS / f"{finding_id}.md").write_text(
            f"# {finding_id}\n\nphase: {phase}\ntest: {test_id}\nstatus: {status}\n\n```json\n"
            f"{json.dumps(evidence, indent=2, default=str)}\n```\n",
            encoding="utf-8",
        )


def _edge_public(e: EntityEdge) -> dict:
    return {
        "uuid": e.uuid,
        "name": e.name,
        "fact": e.fact,
        "group_id": e.group_id,
        "valid_at": _dt_iso(e.valid_at),
        "invalid_at": _dt_iso(e.invalid_at),
        "expired_at": _dt_iso(e.expired_at),
        "reference_time": _dt_iso(getattr(e, "reference_time", None)),
        "source_node_uuid": e.source_node_uuid,
        "target_node_uuid": e.target_node_uuid,
        "episodes": list(e.episodes or []),
    }


def _classify_temporal(edge: EntityEdge, query_time: datetime) -> list[str]:
    """Classify from metadata only. search hit ≠ currently applicable."""
    labels = ["STORED"]
    va = edge.valid_at
    ia = edge.invalid_at
    if va is not None:
        if va.tzinfo is None:
            va = va.replace(tzinfo=timezone.utc)
    if ia is not None:
        if ia.tzinfo is None:
            ia = ia.replace(tzinfo=timezone.utc)

    if va is not None and va <= query_time and (ia is None or ia > query_time):
        labels.append("TEMPORALLY_CURRENT")
    elif ia is not None and ia <= query_time:
        labels.append("TEMPORALLY_EXPIRED")
    elif va is not None and va > query_time:
        labels.append("TEMPORALLY_NOT_YET_VALID")
    else:
        labels.append("TEMPORAL_UNKNOWN")
    return labels


def _fixture_t1(old_marker: str) -> str:
    return (
        f"ProjectOrion uses Python as its RUNTIME_LANGUAGE. "
        f"The unique retrieval marker is {old_marker}. "
        f"ProjectOrion is owned by Alice."
    )


def _fixture_t2(new_marker: str) -> str:
    return (
        f"ProjectOrion uses Rust as its RUNTIME_LANGUAGE. "
        f"The unique retrieval marker is {new_marker}."
    )


async def _dump_group_edges(graphiti, group_id: str) -> list[EntityEdge]:
    """Inspect EntityEdges via driver on the Falkor graph named after group_id.

    FalkorDBLite stores each group_id as a separate graph database. Querying
    default_db after reopen returns empty — clone to group_id first (same
    pattern as graphiti handle_multiple_group_ids).
    """
    driver = graphiti.driver
    try:
        if getattr(driver, "provider", None) == GraphProvider.FALKORDB:
            if group_id != getattr(driver, "_database", None):
                driver = driver.clone(database=group_id)
        return await EntityEdge.get_by_group_ids(driver, [group_id])
    except Exception:
        # Empty group / no edges yet
        return []


def _find_by_marker(edges: list[EntityEdge], marker: str) -> list[EntityEdge]:
    return [e for e in edges if marker in (e.fact or "")]


def _find_owner(edges: list[EntityEdge]) -> list[EntityEdge]:
    out = []
    for e in edges:
        blob = f"{e.name} {e.fact}"
        if "OWNED_BY" in blob or "owned by Alice" in blob.lower():
            out.append(e)
    return out


def _require_p5_0():
    if _P5_0_OK is not True:
        pytest.skip(
            f"BLOCKED/FIXTURE_FAIL: P5-0 provider self-control did not PASS "
            f"(ok={_P5_0_OK}, evidence={_P5_0_EVIDENCE})"
        )


# ---------------------------------------------------------------------------
# P5-0: provider self-control FIRST
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p5_0_provider_self_control():
    """P5-0: DeterministicTemporalLLMClient parses EdgeDuplicate + EdgeTimestamps."""
    global _P5_0_OK, _P5_0_EVIDENCE
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)

    client = DeterministicTemporalLLMClient()
    uid = _uuid()
    old_m = f"P5_OLD_{uid}"
    new_m = f"P5_NEW_{uid}"

    # --- EdgeTimestamps: must return reference_time, not None ---
    ts_messages = [
        Message(role="system", content="You extract temporal bounds from facts."),
        Message(
            role="user",
            content=(
                f"<FACT>\nProjectOrion uses Python. Marker {old_m}.\n</FACT>\n"
                f"<REFERENCE TIME>\n{T1.isoformat()}\n</REFERENCE TIME>"
            ),
        ),
    ]
    ts_resp = await client._generate_response(ts_messages, response_model=EdgeTimestamps)
    ts_ok = ts_resp.get("valid_at") is not None and _approx_eq(
        datetime.fromisoformat(str(ts_resp["valid_at"]).replace("Z", "+00:00")),
        T1,
        tol_seconds=2.0,
    )

    # --- EdgeDuplicate: OLD marker index from context (not hardcoded 0) ---
    # Put OLD at idx=2 (not 0) so hardcoding 0 would fail self-control
    existing = [{"idx": 0, "fact": f"ProjectOrion is owned by Alice."}]
    invalidation = [
        {"idx": 1, "fact": "Unrelated noise fact about widgets."},
        {
            "idx": 2,
            "fact": f"ProjectOrion uses Python as its RUNTIME_LANGUAGE. Retrieval marker {old_m}.",
        },
        {"idx": 3, "fact": "Another unrelated fact."},
    ]
    new_fact = f"ProjectOrion uses Rust as its RUNTIME_LANGUAGE. Retrieval marker {new_m}."
    dup_messages = [
        Message(role="system", content="You are a fact deduplication assistant."),
        Message(
            role="user",
            content=(
                f"<EXISTING FACTS>\n{existing}\n</EXISTING FACTS>\n"
                f"<FACT INVALIDATION CANDIDATES>\n{invalidation}\n</FACT INVALIDATION CANDIDATES>\n"
                f"<NEW FACT>\n{new_fact}\n</NEW FACT>"
            ),
        ),
    ]
    dup_resp = await client._generate_response(dup_messages, response_model=EdgeDuplicate)
    contradicted = dup_resp.get("contradicted_facts") or []
    dup_ok = contradicted == [2]  # must select OLD at idx 2 from context

    # Owner must NOT be selected when only language contradicts
    owner_ok = 0 not in contradicted

    evidence = {
        "edge_timestamps_response": ts_resp,
        "edge_timestamps_ok": ts_ok,
        "edge_duplicate_response": dup_resp,
        "edge_duplicate_ok": dup_ok,
        "owner_not_contradicted_ok": owner_ok,
        "expected_contradicted_idx": 2,
        "old_marker": old_m,
        "new_marker": new_m,
        "provider": "DeterministicTemporalLLMClient",
        "note": "DeterministicLLMClient returns contradicted_facts=[] and timestamps None — banned for P5",
    }
    PROVIDER_RECEIPT.write_text(
        json.dumps({"p5_0": evidence, "decisions": client.decisions}, indent=2, default=str),
        encoding="utf-8",
    )

    ok = bool(ts_ok and dup_ok and owner_ok)
    _P5_0_OK = ok
    _P5_0_EVIDENCE = evidence

    if not ok:
        _record(
            "P5-0",
            "P5-0",
            "FIXTURE_FAIL",
            evidence,
            finding_id="F-P5-0-PROVIDER-SELF-CONTROL",
        )
        pytest.fail(
            f"FIXTURE_FAIL / BLOCKED: P5-0 provider self-control failed: {evidence}"
        )

    _record("P5-0", "P5-0", "PASS", evidence)


# ---------------------------------------------------------------------------
# Shared fixture: one db, temporal client, T1 then T2 episodes
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def p5_markers():
    uid = _uuid()
    return {
        "uid": uid,
        "old": f"P5_OLD_{uid}",
        "new": f"P5_NEW_{uid}",
        "group_id": f"p5_orion_{uid[:10]}",
        "db_path": DATA_ROOT / f"p5_{uid}.db",
    }


@pytest.mark.asyncio
async def test_p5_a_old_baseline(p5_markers):
    """P5-A: after T1 only, OLD edge exists with valid_at≈T1, invalid_at None."""
    _require_p5_0()
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(
        p5_markers["db_path"], database="default_db", build_indices=True, llm_client=client
    )
    try:
        body = _fixture_t1(p5_markers["old"])
        result = await stack.graphiti.add_episode(
            name="p5_t1_python",
            episode_body=body,
            source_description="fractal_lab_p5_temporal",
            reference_time=T1,
            source=EpisodeType.text,
            group_id=p5_markers["group_id"],
        )
        edges = await _dump_group_edges(stack.graphiti, p5_markers["group_id"])
        old_edges = _find_by_marker(edges, p5_markers["old"])
        owner_edges = _find_owner(edges)

        evidence = {
            "group_id": p5_markers["group_id"],
            "old_marker": p5_markers["old"],
            "episode_nodes": [n.name for n in result.nodes],
            "episode_edges": [_edge_public(e) for e in result.edges],
            "driver_edges": [_edge_public(e) for e in edges],
            "old_edges": [_edge_public(e) for e in old_edges],
            "owner_edges": [_edge_public(e) for e in owner_edges],
            "provider_decisions": list(client.decisions),
        }

        if not old_edges:
            _record(
                "P5-A",
                "P5-A",
                "FIXTURE_FAIL",
                evidence,
                finding_id="F-P5-A-OLD-MISSING",
            )
            pytest.fail(f"FIXTURE_FAIL: OLD edge not created: {evidence}")

        old = old_edges[0]
        va_ok = _approx_eq(old.valid_at, T1, tol_seconds=2.0)
        ia_ok = old.invalid_at is None
        evidence["valid_at_ok"] = va_ok
        evidence["invalid_at_none_ok"] = ia_ok
        evidence["observed_valid_at"] = _dt_iso(old.valid_at)
        evidence["observed_invalid_at"] = _dt_iso(old.invalid_at)

        _STATE["markers"] = p5_markers
        _STATE["old_uuid_before"] = old.uuid
        _STATE["old_before"] = _edge_public(old)
        _STATE["owner_before"] = [_edge_public(e) for e in owner_edges]
        _STATE["db_path"] = str(p5_markers["db_path"])
        _STATE["group_id"] = p5_markers["group_id"]

        EDGE_DUMP.write_text(
            json.dumps({"phase": "P5-A", "edges": evidence["driver_edges"]}, indent=2),
            encoding="utf-8",
        )

        if not (va_ok and ia_ok):
            # If timestamps missing entirely → fixture/provider issue
            if old.valid_at is None:
                status = "FIXTURE_FAIL"
                fid = "F-P5-A-VALID-AT-NONE"
            else:
                status = "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL"
                fid = "F-P5-A-TIMESTAMP-MISMATCH"
            _record("P5-A", "P5-A", status, evidence, finding_id=fid)
            pytest.fail(f"{status}: P5-A baseline timestamps: {evidence}")

        _record("P5-A", "P5-A", "PASS", evidence)
    finally:
        # Persist decisions
        existing = {}
        if PROVIDER_RECEIPT.exists():
            try:
                existing = json.loads(PROVIDER_RECEIPT.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
        existing["p5_a"] = client.decisions
        PROVIDER_RECEIPT.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
        await stack.aclose()


@pytest.mark.asyncio
async def test_p5_b_add_contradiction(p5_markers):
    """P5-B: add T2 contradiction; record actual valid_at/invalid_at (do not invent)."""
    _require_p5_0()
    if "old_before" not in _STATE:
        pytest.skip("P5-A did not populate shared state")

    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(
        p5_markers["db_path"], database="default_db", build_indices=True, llm_client=client
    )
    try:
        body = _fixture_t2(p5_markers["new"])
        result = await stack.graphiti.add_episode(
            name="p5_t2_rust",
            episode_body=body,
            source_description="fractal_lab_p5_temporal",
            reference_time=T2,
            source=EpisodeType.text,
            group_id=p5_markers["group_id"],
        )
        edges = await _dump_group_edges(stack.graphiti, p5_markers["group_id"])
        old_edges = _find_by_marker(edges, p5_markers["old"])
        new_edges = _find_by_marker(edges, p5_markers["new"])
        owner_edges = _find_owner(edges)

        # Also include invalidated edges returned from add_episode if any
        ep_edges = list(result.edges or [])

        evidence = {
            "group_id": p5_markers["group_id"],
            "episode_edges": [_edge_public(e) for e in ep_edges],
            "driver_edges": [_edge_public(e) for e in edges],
            "old_edges_after": [_edge_public(e) for e in old_edges],
            "new_edges": [_edge_public(e) for e in new_edges],
            "owner_edges": [_edge_public(e) for e in owner_edges],
            "old_before": _STATE.get("old_before"),
            "contradiction_receipts": [
                d for d in client.decisions if d.get("model") == "EdgeDuplicate"
            ],
            "provider_decisions": list(client.decisions),
            "note": "Recorded observed timestamps; expectations not invented if Graphiti differs",
        }

        EDGE_DUMP.write_text(
            json.dumps(
                {
                    "phase": "P5-B",
                    "edges": evidence["driver_edges"],
                    "old_before": _STATE.get("old_before"),
                    "old_after": evidence["old_edges_after"],
                    "new": evidence["new_edges"],
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        if not new_edges:
            _record(
                "P5-B",
                "P5-B",
                "FIXTURE_FAIL",
                evidence,
                finding_id="F-P5-B-NEW-MISSING",
            )
            pytest.fail(f"FIXTURE_FAIL: NEW edge not created: {evidence}")

        if not old_edges:
            _record(
                "P5-B",
                "P5-B",
                "INCONCLUSIVE",
                evidence,
                finding_id="F-P5-B-OLD-GONE",
            )
            pytest.fail(f"INCONCLUSIVE: OLD edge missing after contradiction write: {evidence}")

        old = old_edges[0]
        new = new_edges[0]
        _STATE["old_after"] = _edge_public(old)
        _STATE["new_state"] = _edge_public(new)
        _STATE["owner_after"] = [_edge_public(e) for e in owner_edges]
        _STATE["contradiction_receipt"] = evidence["contradiction_receipts"]

        # Observe: did Graphiti invalidate OLD?
        invalidated = old.invalid_at is not None
        evidence["old_invalidated"] = invalidated
        evidence["observed_old_invalid_at"] = _dt_iso(old.invalid_at)
        evidence["observed_new_valid_at"] = _dt_iso(new.valid_at)
        evidence["new_valid_at_ok"] = _approx_eq(new.valid_at, T2, tol_seconds=2.0)

        # Check provider actually returned contradicted_facts pointing at OLD
        provider_selected_old = False
        for rec in evidence["contradiction_receipts"]:
            facts = (rec.get("existing_facts") or []) + (rec.get("invalidation_candidates") or [])
            idxs = set(rec.get("contradicted_facts") or [])
            for item in facts:
                if int(item.get("idx", -1)) in idxs and p5_markers["old"] in str(item.get("fact", "")):
                    provider_selected_old = True
        evidence["provider_selected_old_marker"] = provider_selected_old

        if not invalidated:
            if not provider_selected_old and not evidence["contradiction_receipts"]:
                status = "FIXTURE_FAIL"
                fid = "F-P5-B-NO-CONTRADICTION-DECISION"
            elif not provider_selected_old:
                status = "FIXTURE_FAIL"
                fid = "F-P5-B-PROVIDER-MISSED-OLD"
            else:
                status = "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL"
                fid = "F-P5-B-NOT-INVALIDATED"
            _record("P5-B", "P5-B", status, evidence, finding_id=fid)
            pytest.fail(f"{status}: OLD not invalidated after T2: {evidence}")

        # Record whether invalid_at ≈ T2 (informative; do not invent if different)
        evidence["old_invalid_at_approx_T2"] = _approx_eq(old.invalid_at, T2, tol_seconds=2.0)
        evidence["old_invalid_at_approx_new_valid_at"] = _approx_eq(
            old.invalid_at, new.valid_at, tol_seconds=2.0
        )

        _record("P5-B", "P5-B", "PASS", evidence)
    finally:
        existing = {}
        if PROVIDER_RECEIPT.exists():
            try:
                existing = json.loads(PROVIDER_RECEIPT.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
        existing["p5_b"] = client.decisions
        PROVIDER_RECEIPT.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
        await stack.aclose()


@pytest.mark.asyncio
async def test_p5_c_classify_q1_q2(p5_markers):
    """P5-C: classify current vs historical at Q1/Q2 from metadata (not search alone)."""
    _require_p5_0()
    if "old_after" not in _STATE or "new_state" not in _STATE:
        pytest.skip("P5-B did not populate shared state")

    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(
        p5_markers["db_path"], database="default_db", build_indices=True, llm_client=client
    )
    try:
        edges = await _dump_group_edges(stack.graphiti, p5_markers["group_id"])

        # Search may return both — that does NOT mean both are currently applicable
        search_old = await stack.graphiti.search(
            p5_markers["old"], group_ids=[p5_markers["group_id"]], num_results=10
        )
        search_new = await stack.graphiti.search(
            p5_markers["new"], group_ids=[p5_markers["group_id"]], num_results=10
        )
        search_lang = await stack.graphiti.search(
            "ProjectOrion RUNTIME_LANGUAGE", group_ids=[p5_markers["group_id"]], num_results=10
        )

        # Prefer driver dump; fall back to search-returned EntityEdge metadata
        if not edges:
            seen = {}
            for e in list(search_old) + list(search_new) + list(search_lang):
                seen[e.uuid] = e
            edges = list(seen.values())

        old_edges = _find_by_marker(edges, p5_markers["old"])
        new_edges = _find_by_marker(edges, p5_markers["new"])

        def pack(edge: EntityEdge) -> dict:
            return {
                "edge": _edge_public(edge),
                "at_Q1": _classify_temporal(edge, Q1),
                "at_Q2": _classify_temporal(edge, Q2),
                "retrievable_old_query": any(
                    edge.uuid == getattr(e, "uuid", None) for e in search_old
                )
                or p5_markers["old"] in (edge.fact or ""),
                "retrievable_new_query": any(
                    edge.uuid == getattr(e, "uuid", None) for e in search_new
                ),
                "retrievable_lang_query": any(
                    edge.uuid == getattr(e, "uuid", None) for e in search_lang
                ),
            }

        classifications = {
            "old": [pack(e) for e in old_edges],
            "new": [pack(e) for e in new_edges],
            "search_old_hit_count": len([e for e in search_old if p5_markers["old"] in (e.fact or "")]),
            "search_new_hit_count": len([e for e in search_new if p5_markers["new"] in (e.fact or "")]),
            "search_lang_facts": [e.fact for e in search_lang],
            "Q1": _dt_iso(Q1),
            "Q2": _dt_iso(Q2),
            "method": "metadata classification (SearchFilters reference_time not assumed)",
            "documented_reference_time_edge_search": False,
        }

        if not old_edges or not new_edges:
            _record(
                "P5-C",
                "P5-C",
                "INCONCLUSIVE",
                classifications,
                finding_id="F-P5-C-MISSING-EDGES",
            )
            pytest.fail(f"INCONCLUSIVE: missing edges for classification: {classifications}")

        old_c = classifications["old"][0]
        new_c = classifications["new"][0]

        # Expectations from metadata semantics:
        # Q1 (between T1-T2): OLD current; NEW not yet valid (valid_at=T2 > Q1)
        # Q2 (after T2): OLD expired if invalid_at set; NEW current
        expect = {
            "old_Q1_current": "TEMPORALLY_CURRENT" in old_c["at_Q1"],
            "new_Q1_not_current": "TEMPORALLY_CURRENT" not in new_c["at_Q1"],
            "old_Q2_expired": "TEMPORALLY_EXPIRED" in old_c["at_Q2"],
            "new_Q2_current": "TEMPORALLY_CURRENT" in new_c["at_Q2"],
        }
        classifications["expectations_checked"] = expect
        # Annotate RETRIEVABLE on packs
        for item in classifications["old"] + classifications["new"]:
            labels = list(item["at_Q1"])  # noqa — keep metadata labels separate
            item["note"] = "RETRIEVABLE assessed via Graphiti.search; independent of TEMPORALLY_*"

        ok = all(expect.values())
        _STATE["classifications"] = classifications

        if not ok:
            # If invalid_at missing, this is Graphiti contradiction failure already caught in B;
            # here classify as GRAPHITI or INCONCLUSIVE
            status = "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL"
            if old_edges[0].invalid_at is None:
                status = "INCONCLUSIVE"
            _record("P5-C", "P5-C", status, classifications, finding_id="F-P5-C-CLASSIFY")
            pytest.fail(f"{status}: classification matrix: {classifications}")

        _record("P5-C", "P5-C", "PASS", classifications)
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p5_d_unrelated_owner_not_invalidated(p5_markers):
    """P5-D: owner Alice edge must NOT be invalidated by language contradiction."""
    _require_p5_0()
    if "old_after" not in _STATE:
        pytest.skip("P5-B did not populate shared state")

    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(
        p5_markers["db_path"], database="default_db", build_indices=True, llm_client=client
    )
    try:
        edges = await _dump_group_edges(stack.graphiti, p5_markers["group_id"])
        if not edges:
            search_owner = await stack.graphiti.search(
                "ProjectOrion owned by Alice", group_ids=[p5_markers["group_id"]], num_results=10
            )
            edges = list(search_owner)
        owners = _find_owner(edges)
        evidence = {
            "owner_edges": [_edge_public(e) for e in owners],
            "owner_before": _STATE.get("owner_before"),
            "owner_after_state": _STATE.get("owner_after"),
            "driver_edge_count": len(edges),
        }
        if not owners and _STATE.get("owner_after"):
            # Persist observed P5-B state if driver/search miss (should not happen after clone fix)
            owners_meta = _STATE["owner_after"]
            bad_meta = [e for e in owners_meta if e.get("invalid_at") is not None]
            evidence["fallback_owner_after_state"] = owners_meta
            if bad_meta:
                _record(
                    "P5-D",
                    "P5-D",
                    "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL",
                    evidence,
                    finding_id="F-P5-D-OWNER-INVALIDATED",
                )
                pytest.fail(
                    f"GRAPHITI_TEMPORAL_CONTRADICTION_FAIL: owner invalidated: {evidence}"
                )
            _record("P5-D", "P5-D", "PASS", {**evidence, "used_p5b_state_fallback": True})
            return
        if not owners:
            _record(
                "P5-D",
                "P5-D",
                "FIXTURE_FAIL",
                evidence,
                finding_id="F-P5-D-OWNER-MISSING",
            )
            pytest.fail(f"FIXTURE_FAIL: owner Alice edge missing: {evidence}")

        bad = [e for e in owners if e.invalid_at is not None]
        evidence["invalidated_owners"] = [_edge_public(e) for e in bad]
        if bad:
            _record(
                "P5-D",
                "P5-D",
                "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL",
                evidence,
                finding_id="F-P5-D-OWNER-INVALIDATED",
            )
            pytest.fail(
                f"GRAPHITI_TEMPORAL_CONTRADICTION_FAIL: owner invalidated: {evidence}"
            )
        _record("P5-D", "P5-D", "PASS", evidence)
    finally:
        await stack.aclose()


_REOPEN_HELPER = r'''
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
'''


@pytest.mark.asyncio
async def test_p5_e_subprocess_reopen(p5_markers):
    """P5-E: subprocess reopen — temporal metadata persists on disk."""
    _require_p5_0()
    if "old_after" not in _STATE:
        pytest.skip("P5-B did not populate shared state")

    helper = ARTIFACTS / "_p5_reopen_helper.py"
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    helper.write_text(_REOPEN_HELPER, encoding="utf-8")

    env = {
        **dict(**{k: v for k, v in __import__("os").environ.items()}),
        "PYTHONPATH": str(REPO_ROOT / "src"),
    }
    # Prefer venv python
    py = REPO_ROOT / ".venv" / "bin" / "python"
    cmd = [
        str(py if py.exists() else sys.executable),
        str(helper),
        str(p5_markers["db_path"]),
        p5_markers["group_id"],
        p5_markers["old"],
        p5_markers["new"],
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    evidence = {
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
        "cmd": cmd,
    }
    try:
        # Last JSON line
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
        payload = json.loads(lines[-1]) if lines else {}
    except json.JSONDecodeError:
        payload = {}
    evidence["reopen_payload"] = payload
    _STATE["reopen"] = evidence

    if proc.returncode != 0 or not payload.get("old") or payload["old"][0].get("invalid_at") is None:
        _record(
            "P5-E",
            "P5-E",
            "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL" if payload.get("old") else "FAIL",
            evidence,
            finding_id="F-P5-E-REOPEN",
        )
        pytest.fail(f"P5-E reopen persistence failed: {evidence}")

    _record("P5-E", "P5-E", "PASS", evidence)


@pytest.mark.asyncio
async def test_p5_z_finalize_result_summary(p5_markers):
    """Write final result.json summary matrix (does not invent PASS)."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    receipt: dict = {"phases": [], "matrix": {}}
    if RECEIPT_PATH.exists():
        try:
            receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    matrix = receipt.get("matrix") or {}
    all_ids = ["P5-0", "P5-A", "P5-B", "P5-C", "P5-D", "P5-E"]
    full_pass = all(matrix.get(i) == "PASS" for i in all_ids)

    summary = {
        "suite": "P5_deterministic_temporal_contradiction",
        "graphiti": "0.29.3",
        "backend": "FalkorDBLite",
        "branch": "experiment/falkordblite-deterministic-memory",
        "matrix": {i: matrix.get(i, "MISSING") for i in all_ids},
        "full_pass": full_pass,
        "claim_if_full_pass": (
            "Graphiti 0.29.3 + FalkorDBLite passed this deterministic temporal contradiction fixture."
            if full_pass
            else None
        ),
        "old_before": _STATE.get("old_before"),
        "old_after": _STATE.get("old_after"),
        "new_state": _STATE.get("new_state"),
        "contradiction_receipt": _STATE.get("contradiction_receipt"),
        "reopen": _STATE.get("reopen"),
        "classifications": _STATE.get("classifications"),
        "markers": p5_markers,
        "T1": _dt_iso(T1),
        "T2": _dt_iso(T2),
        "Q1": _dt_iso(Q1),
        "Q2": _dt_iso(Q2),
        "p6_recommendation_only": (
            "P6 not started. If P5 full PASS, next lab step could probe search+SearchFilters "
            "temporal windows vs metadata classification; still no Fractal MemoryOps/Crystal/SVL."
        ),
        "anti_hallucination": {
            "FIXTURE_FAIL": "provider/fixture broken",
            "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL": "fixture OK, Graphiti did not invalidate as observed",
            "INCONCLUSIVE": "insufficient evidence",
        },
    }
    receipt["summary"] = summary
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    assert True  # finalize always records; matrix statuses already asserted upstream
