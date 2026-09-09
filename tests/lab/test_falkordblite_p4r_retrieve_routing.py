"""P4R: Corrected retrieve_episodes routing with temporal control (lab only).

Graphiti 0.29.3 retrieve_episodes filters ``e.valid_at <= reference_time``.
Prior P4 fixtures captured reference_time BEFORE add_episode (which sets
valid_at from a later datetime.now()), producing empty retrieve results that
were mis-attributed to Falkor last-write affinity / multi-scope routing.

This suite:
  1) Proves the temporal filter (Control1 / Control2) on a single group.
  2) Re-runs single- and multi-group retrieve with query_time AFTER writes.
No monkey-patches. Deterministic providers only. Does not start P5.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from graphiti_core.nodes import EpisodeType

from fractal_lab.experiments.falkor_graphiti_bootstrap import open_lab_graphiti

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:coroutine 'AsyncManagementCommands.shutdown' was never awaited:RuntimeWarning"
    ),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = REPO_ROOT / "artifacts" / "run_003"
FINDINGS = ARTIFACTS / "findings"
DATA_ROOT = REPO_ROOT / "data" / "falkor_e2e_p4r"
RECEIPT_PATH = ARTIFACTS / "result.json"

SHARED_PROBE = "P4R_MULTISCOPE_PROBE"

# Module gate: Control2 must pass before multi-group attribution.
_CONTROL2_OK: bool | None = None
_CONTROL2_EVIDENCE: dict | None = None


def _uuid() -> str:
    return uuid.uuid4().hex


def _driver_db(graphiti) -> str | None:
    driver = getattr(graphiti, "driver", None)
    if driver is None:
        return None
    return getattr(driver, "_database", None)


def _fixture(marker: str, who: str, other: str) -> str:
    return (
        f"{who} collaborated with {other} at MarkerCorp on a synthetic lab project. "
        f"The unique retrieval token is {marker}. "
        f"Shared probe token {SHARED_PROBE} is present for multi-group recall. "
        f"{who} confirmed the token {marker} must remain searchable via Graphiti.search."
    )


def _edges_blob(edges) -> str:
    parts = []
    for e in edges:
        parts.append(f"{getattr(e, 'fact', '')} {getattr(e, 'name', '')}")
    return "\n".join(parts)


def _marker_in_edges(edges, marker: str) -> bool:
    return marker in _edges_blob(edges)


def _episodes_blob(episodes) -> str:
    parts = []
    for ep in episodes:
        parts.append(
            f"{getattr(ep, 'content', '')} {getattr(ep, 'name', '')} "
            f"{getattr(ep, 'group_id', '')}"
        )
    return "\n".join(parts)


def _marker_in_episodes(episodes, marker: str) -> bool:
    return marker in _episodes_blob(episodes)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _episode_meta(episodes) -> list[dict]:
    rows = []
    for ep in episodes:
        rows.append(
            {
                "name": getattr(ep, "name", None),
                "group_id": getattr(ep, "group_id", None),
                "valid_at": _iso(getattr(ep, "valid_at", None)),
                "uuid": getattr(ep, "uuid", None),
            }
        )
    return rows


def _record(phase: str, test_id: str, status: str, evidence: dict, finding_id: str | None = None):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    receipt: dict = {"phases": [], "notes": []}
    if RECEIPT_PATH.exists():
        try:
            receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = {"phases": [], "notes": []}
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
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    if status in {"FAIL", "PARTIAL", "STOP"} and finding_id:
        (FINDINGS / f"{finding_id}.md").write_text(
            f"# {finding_id}\n\nphase: {phase}\ntest: {test_id}\nstatus: {status}\n\n```json\n"
            f"{json.dumps(evidence, indent=2)}\n```\n",
            encoding="utf-8",
        )


def _write_finding(finding_id: str, body: str) -> None:
    FINDINGS.mkdir(parents=True, exist_ok=True)
    (FINDINGS / f"{finding_id}.md").write_text(body, encoding="utf-8")


def _require_control2():
    if _CONTROL2_OK is not True:
        pytest.fail(
            "STOP: temporal Control2 failed or did not run — "
            "do not attribute multi-group retrieve failures. "
            f"evidence={json.dumps(_CONTROL2_EVIDENCE)[:1500]}"
        )


@pytest.fixture()
def db_path() -> Path:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    return DATA_ROOT / f"p4r_{uuid.uuid4().hex}.db"


async def _add_episode(graphiti, *, name: str, body: str, group_id: str):
    return await graphiti.add_episode(
        name=name,
        episode_body=body,
        source_description="fractal_lab_p4r_retrieve_routing",
        reference_time=datetime.now(timezone.utc),
        source=EpisodeType.text,
        group_id=group_id,
    )


async def _read_surface(
    graphiti,
    *,
    surface: str,
    group_ids: list[str],
    query_time: datetime,
    search_query: str | None = None,
    last_n: int = 10,
) -> dict:
    before = _driver_db(graphiti)
    if surface == "retrieve_episodes":
        eps = await graphiti.retrieve_episodes(
            query_time, last_n=last_n, group_ids=group_ids
        )
        after = _driver_db(graphiti)
        return {
            "surface": surface,
            "requested_group_ids": list(group_ids),
            "driver_database_before": before,
            "driver_database_after": after,
            "query_reference_time": _iso(query_time),
            "result_count": len(eps),
            "episode_names": [getattr(e, "name", None) for e in eps],
            "episode_group_ids": [getattr(e, "group_id", None) for e in eps],
            "episodes": _episode_meta(eps),
            "_episodes": eps,
        }
    assert search_query is not None
    edges = await graphiti.search(
        search_query, group_ids=group_ids, num_results=20
    )
    after = _driver_db(graphiti)
    return {
        "surface": surface,
        "requested_group_ids": list(group_ids),
        "driver_database_before": before,
        "driver_database_after": after,
        "query_reference_time": None,
        "search_query": search_query,
        "result_count": len(edges),
        "facts": [getattr(e, "fact", "") for e in edges],
        "_edges": edges,
    }


@pytest.mark.asyncio
async def test_p4r_00_temporal_control(db_path: Path):
    """Mandatory first: Control1 early ref → empty; Control2 late ref → hit."""
    global _CONTROL2_OK, _CONTROL2_EVIDENCE

    uid = _uuid()
    marker = f"TEMP_{uid}"
    group_a = f"p4r_ctrl_A_{uid[:10]}"

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        g = stack.graphiti
        result = await _add_episode(
            g,
            name=f"p4r_ctrl_{uid[:8]}",
            body=_fixture(marker, "Alice", "Alpha"),
            group_id=group_a,
        )
        episode = result.episode
        valid_at = episode.valid_at
        assert valid_at is not None, "episode.valid_at must be set by add_episode"

        # Control1: reference_time strictly before valid_at → must NOT return
        early = valid_at - timedelta(seconds=1)
        if early.tzinfo is None:
            early = early.replace(tzinfo=timezone.utc)
        c1 = await _read_surface(
            g,
            surface="retrieve_episodes",
            group_ids=[group_a],
            query_time=early,
        )
        c1_found = _marker_in_episodes(c1.pop("_episodes"), marker)
        c1["episode_valid_at"] = _iso(valid_at)
        c1["marker"] = marker
        c1["marker_found"] = c1_found
        c1["expectation"] = "NOT_RETURNED"

        # Control2: query_time AFTER write (preferred pattern)
        query_time = datetime.now(timezone.utc)
        used_plus_one = False
        c2 = await _read_surface(
            g,
            surface="retrieve_episodes",
            group_ids=[group_a],
            query_time=query_time,
        )
        c2_eps = c2.pop("_episodes")
        c2_found = _marker_in_episodes(c2_eps, marker)
        if not c2_found:
            # +1s only if needed — document why
            query_time = datetime.now(timezone.utc) + timedelta(seconds=1)
            used_plus_one = True
            c2 = await _read_surface(
                g,
                surface="retrieve_episodes",
                group_ids=[group_a],
                query_time=query_time,
            )
            c2_eps = c2.pop("_episodes")
            c2_found = _marker_in_episodes(c2_eps, marker)

        c2["episode_valid_at"] = _iso(valid_at)
        c2["marker"] = marker
        c2["marker_found"] = c2_found
        c2["expectation"] = "RETURNED"
        c2["used_plus_one_second"] = used_plus_one
        c2["plus_one_reason"] = (
            "datetime.now() immediately after write still missed valid_at <= filter; "
            "added +1s cushion"
            if used_plus_one
            else None
        )

        evidence = {
            "group_a": group_a,
            "marker": marker,
            "episode_valid_at": _iso(valid_at),
            "episode_name": getattr(episode, "name", None),
            "driver_database_after_write": _driver_db(g),
            "control1": c1,
            "control2": c2,
            "graphiti_filter": "e.valid_at <= reference_time (graphiti_core 0.29.3)",
        }

        control1_ok = not c1_found
        control2_ok = c2_found
        _CONTROL2_OK = control2_ok
        _CONTROL2_EVIDENCE = evidence

        if not control1_ok and not control2_ok:
            _record(
                "P4R_TEMPORAL",
                "temporal_control",
                "FAIL",
                evidence,
                finding_id="F-P4R-TEMPORAL-BOTH-FAIL",
            )
            pytest.fail("Temporal Control1 and Control2 both failed")
        if not control1_ok:
            _record(
                "P4R_TEMPORAL",
                "temporal_control",
                "FAIL",
                evidence,
                finding_id="F-P4R-TEMPORAL-CONTROL1",
            )
            pytest.fail(
                "Control1 FAIL: early reference_time still returned episode "
                "(temporal filter not behaving as documented)"
            )
        if not control2_ok:
            _record(
                "P4R_TEMPORAL",
                "temporal_control",
                "STOP",
                evidence,
                finding_id="F-P4R-TEMPORAL-CONTROL2-STOP",
            )
            pytest.fail(
                "STOP: Control2 failed — single-group retrieve with late "
                "query_time did not return episode. Do not attribute multi-group."
            )

        _record("P4R_TEMPORAL", "temporal_control", "PASS", evidence)
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p4r_a_single_group_retrieve_after_write(db_path: Path):
    """P4R-A: single-group retrieve with query_time AFTER write must find marker."""
    _require_control2()
    uid = _uuid()
    marker = f"A_ONLY_{uid}"
    group_a = f"p4r_a_A_{uid[:10]}"

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        g = stack.graphiti
        result = await _add_episode(
            g,
            name=f"p4r_a_{uid[:8]}",
            body=_fixture(marker, "Alice", "Alpha"),
            group_id=group_a,
        )
        valid_at = result.episode.valid_at
        query_time = datetime.now(timezone.utc)
        read = await _read_surface(
            g,
            surface="retrieve_episodes",
            group_ids=[group_a],
            query_time=query_time,
        )
        eps = read.pop("_episodes")
        found = _marker_in_episodes(eps, marker)
        evidence = {
            "marker": marker,
            "group_a": group_a,
            "episode_valid_at": _iso(valid_at),
            "query_reference_time": _iso(query_time),
            "driver_database_after_write": _driver_db(g),
            "read": read,
            "expected_marker_found": found,
        }
        if found:
            _record("P4R_A", "single_group_retrieve_after_write", "PASS", evidence)
        else:
            _record(
                "P4R_A",
                "single_group_retrieve_after_write",
                "FAIL",
                evidence,
                finding_id="F-P4R-A-RETRIEVE-MISS",
            )
            pytest.fail("P4R-A: late query_time single-group retrieve missed marker")
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p4r_b_a_then_b_read_a(db_path: Path):
    """P4R-B: A→B then search(A)+retrieve([A]) with query_time AFTER both writes."""
    _require_control2()
    uid = _uuid()
    marker_a = f"A_ONLY_{uid}"
    marker_b = f"B_ONLY_{uid}"
    group_a = f"p4r_b_A_{uid[:10]}"
    group_b = f"p4r_b_B_{uid[:10]}"

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        g = stack.graphiti
        ra = await _add_episode(
            g, name=f"p4r_b_a_{uid[:8]}", body=_fixture(marker_a, "Alice", "Alpha"), group_id=group_a
        )
        rb = await _add_episode(
            g, name=f"p4r_b_b_{uid[:8]}", body=_fixture(marker_b, "Bob", "Beta"), group_id=group_b
        )
        driver_after = _driver_db(g)
        query_time = datetime.now(timezone.utc)

        search_a = await _read_surface(
            g,
            surface="search",
            group_ids=[group_a],
            query_time=query_time,
            search_query=marker_a,
        )
        edges = search_a.pop("_edges")
        search_found = _marker_in_edges(edges, marker_a)
        search_foreign = _marker_in_edges(edges, marker_b)

        retrieve_a = await _read_surface(
            g,
            surface="retrieve_episodes",
            group_ids=[group_a],
            query_time=query_time,
        )
        eps = retrieve_a.pop("_episodes")
        retrieve_found = _marker_in_episodes(eps, marker_a)
        retrieve_foreign = _marker_in_episodes(eps, marker_b)

        evidence = {
            "sequence": "A_then_B_read_A",
            "marker_a": marker_a,
            "marker_b": marker_b,
            "group_a": group_a,
            "group_b": group_b,
            "episode_a_valid_at": _iso(ra.episode.valid_at),
            "episode_b_valid_at": _iso(rb.episode.valid_at),
            "driver_database_after_writes": driver_after,
            "query_reference_time": _iso(query_time),
            "search": {
                **search_a,
                "expected_marker_found": search_found,
                "foreign_marker_found": search_foreign,
            },
            "retrieve_episodes": {
                **retrieve_a,
                "expected_marker_found": retrieve_found,
                "foreign_marker_found": retrieve_foreign,
            },
            "last_write_group_observed": driver_after == group_b,
        }

        if search_foreign or retrieve_foreign:
            _record(
                "P4R_B",
                "a_then_b_read_a",
                "FAIL",
                evidence,
                finding_id="F-P4R-CROSS-GROUP-LEAKAGE",
            )
            pytest.fail("P4R-B cross-group leakage")
        if not search_found or not retrieve_found:
            _record(
                "P4R_B",
                "a_then_b_read_a",
                "FAIL",
                evidence,
                finding_id="F-P4R-B-LAST-WRITE-READ-A",
            )
            pytest.fail(
                f"P4R-B miss after A→B (search={search_found}, retrieve={retrieve_found})"
            )
        _record("P4R_B", "a_then_b_read_a", "PASS", evidence)
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p4r_c_b_then_a_read_b(db_path: Path):
    """P4R-C: fresh DB B→A then search(B)+retrieve([B]) with late query_time."""
    _require_control2()
    uid = _uuid()
    marker_a = f"A_ONLY_{uid}"
    marker_b = f"B_ONLY_{uid}"
    group_a = f"p4r_c_A_{uid[:10]}"
    group_b = f"p4r_c_B_{uid[:10]}"

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        g = stack.graphiti
        rb = await _add_episode(
            g, name=f"p4r_c_b_{uid[:8]}", body=_fixture(marker_b, "Bob", "Beta"), group_id=group_b
        )
        ra = await _add_episode(
            g, name=f"p4r_c_a_{uid[:8]}", body=_fixture(marker_a, "Alice", "Alpha"), group_id=group_a
        )
        driver_after = _driver_db(g)
        query_time = datetime.now(timezone.utc)

        search_b = await _read_surface(
            g,
            surface="search",
            group_ids=[group_b],
            query_time=query_time,
            search_query=marker_b,
        )
        edges = search_b.pop("_edges")
        search_found = _marker_in_edges(edges, marker_b)
        search_foreign = _marker_in_edges(edges, marker_a)

        retrieve_b = await _read_surface(
            g,
            surface="retrieve_episodes",
            group_ids=[group_b],
            query_time=query_time,
        )
        eps = retrieve_b.pop("_episodes")
        retrieve_found = _marker_in_episodes(eps, marker_b)
        retrieve_foreign = _marker_in_episodes(eps, marker_a)

        evidence = {
            "sequence": "B_then_A_read_B",
            "marker_a": marker_a,
            "marker_b": marker_b,
            "group_a": group_a,
            "group_b": group_b,
            "episode_b_valid_at": _iso(rb.episode.valid_at),
            "episode_a_valid_at": _iso(ra.episode.valid_at),
            "driver_database_after_writes": driver_after,
            "query_reference_time": _iso(query_time),
            "search": {
                **search_b,
                "expected_marker_found": search_found,
                "foreign_marker_found": search_foreign,
            },
            "retrieve_episodes": {
                **retrieve_b,
                "expected_marker_found": retrieve_found,
                "foreign_marker_found": retrieve_foreign,
            },
            "last_write_group_observed": driver_after == group_a,
            "run_002_discrepancy_note": (
                "run_002 result.json P4D B_then_A_read_B retrieve expected_marker_found=false "
                "(receipt wins over any prose claiming PASS); likely INVALID_REFERENCE_TIME_IN_FIXTURE"
            ),
        }

        if search_foreign or retrieve_foreign:
            _record(
                "P4R_C",
                "b_then_a_read_b",
                "FAIL",
                evidence,
                finding_id="F-P4R-CROSS-GROUP-LEAKAGE",
            )
            pytest.fail("P4R-C cross-group leakage")
        if not search_found or not retrieve_found:
            _record(
                "P4R_C",
                "b_then_a_read_b",
                "FAIL",
                evidence,
                finding_id="F-P4R-C-LAST-WRITE-READ-B",
            )
            pytest.fail(
                f"P4R-C miss after B→A (search={search_found}, retrieve={retrieve_found})"
            )
        _record("P4R_C", "b_then_a_read_b", "PASS", evidence)
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p4r_d_multi_group_retrieve_both(db_path: Path):
    """P4R-D: retrieve_episodes(group_ids=[A,B]) PASS only if BOTH markers found."""
    _require_control2()
    uid = _uuid()
    marker_a = f"A_ONLY_{uid}"
    marker_b = f"B_ONLY_{uid}"
    group_a = f"p4r_d_A_{uid[:10]}"
    group_b = f"p4r_d_B_{uid[:10]}"

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        g = stack.graphiti
        ra = await _add_episode(
            g, name=f"p4r_d_a_{uid[:8]}", body=_fixture(marker_a, "Carol", "Gamma"), group_id=group_a
        )
        rb = await _add_episode(
            g, name=f"p4r_d_b_{uid[:8]}", body=_fixture(marker_b, "Dave", "Delta"), group_id=group_b
        )
        driver_after = _driver_db(g)
        query_time = datetime.now(timezone.utc)

        # Also record multi-group search for comparison (P4B already PASS historically)
        search_both = await _read_surface(
            g,
            surface="search",
            group_ids=[group_a, group_b],
            query_time=query_time,
            search_query=SHARED_PROBE,
        )
        search_edges = search_both.pop("_edges")
        search_a = _marker_in_edges(search_edges, marker_a)
        search_b = _marker_in_edges(search_edges, marker_b)

        retrieve_both = await _read_surface(
            g,
            surface="retrieve_episodes",
            group_ids=[group_a, group_b],
            query_time=query_time,
            last_n=10,
        )
        eps = retrieve_both.pop("_episodes")
        found_a = _marker_in_episodes(eps, marker_a)
        found_b = _marker_in_episodes(eps, marker_b)

        evidence = {
            "marker_a": marker_a,
            "marker_b": marker_b,
            "group_a": group_a,
            "group_b": group_b,
            "episode_a_valid_at": _iso(ra.episode.valid_at),
            "episode_b_valid_at": _iso(rb.episode.valid_at),
            "driver_database_after_writes": driver_after,
            "query_reference_time": _iso(query_time),
            "search_multi": {
                **search_both,
                "found_a": search_a,
                "found_b": search_b,
            },
            "retrieve_multi": {
                **retrieve_both,
                "found_a": found_a,
                "found_b": found_b,
            },
        }

        if found_a and found_b:
            _record("P4R_D", "multi_group_retrieve_both", "PASS", evidence)
        elif found_a or found_b:
            _record(
                "P4R_D",
                "multi_group_retrieve_both",
                "FAIL",
                evidence,
                finding_id="F-P4R-D-MULTISCOPE-PARTIAL",
            )
            pytest.fail(
                f"P4R-D multi-group retrieve partial (a={found_a}, b={found_b})"
            )
        else:
            _record(
                "P4R_D",
                "multi_group_retrieve_both",
                "FAIL",
                evidence,
                finding_id="F-P4R-D-MULTISCOPE-EMPTY",
            )
            pytest.fail("P4R-D multi-group retrieve found neither marker")
    finally:
        await stack.aclose()
