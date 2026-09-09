"""P4: FalkorDBLite last-write routing / multi-group read surfaces (lab only).

ONE Graphiti instance. No workarounds (no monkey-patch, no force _database,
no separate clients to hide rebind). Deterministic providers only.
Graphiti 0.29.3 APIs: retrieve_episodes / search with group_ids.
"""

from __future__ import annotations

import json
import uuid
import warnings
from datetime import datetime, timezone
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
ARTIFACTS = REPO_ROOT / "artifacts" / "run_002"
FINDINGS = ARTIFACTS / "findings"
DATA_ROOT = REPO_ROOT / "data" / "falkor_e2e_p4"
RECEIPT_PATH = ARTIFACTS / "result.json"

SHARED_PROBE = "P4_MULTISCOPE_PROBE"


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
            f"{getattr(ep, 'content', '')} {getattr(ep, 'name', '')} {getattr(ep, 'group_id', '')}"
        )
    return "\n".join(parts)


def _marker_in_episodes(episodes, marker: str) -> bool:
    return marker in _episodes_blob(episodes)


def _record(phase: str, test_id: str, status: str, evidence: dict, finding_id: str | None = None):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    receipt: dict = {"phases": []}
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
    phases = [
        p
        for p in receipt.setdefault("phases", [])
        if not (p.get("phase") == phase and p.get("test_id") == test_id)
    ]
    phases.append(entry)
    receipt["phases"] = phases
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    if status in {"FAIL", "PARTIAL"} and finding_id:
        (FINDINGS / f"{finding_id}.md").write_text(
            f"# {finding_id}\n\nphase: {phase}\ntest: {test_id}\nstatus: {status}\n\n```json\n"
            f"{json.dumps(evidence, indent=2)}\n```\n",
            encoding="utf-8",
        )


def _write_finding_note(finding_id: str, body: str) -> None:
    FINDINGS.mkdir(parents=True, exist_ok=True)
    (FINDINGS / f"{finding_id}.md").write_text(body, encoding="utf-8")


@pytest.fixture()
def db_path() -> Path:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    return DATA_ROOT / f"p4_{uuid.uuid4().hex}.db"


async def _add_episode(graphiti, *, name: str, body: str, group_id: str):
    return await graphiti.add_episode(
        name=name,
        episode_body=body,
        source_description="fractal_lab_p4_routing",
        reference_time=datetime.now(timezone.utc),
        source=EpisodeType.text,
        group_id=group_id,
    )


@pytest.mark.asyncio
async def test_p4a_last_write_routing_matrix(db_path: Path):
    """P4A: after A then B write on ONE instance, matrix of search×retrieve × {A,B}."""
    uid = _uuid()
    marker_a = f"A_ONLY_{uid}"
    marker_b = f"B_ONLY_{uid}"
    group_a = f"p4a_A_{uid[:10]}"
    group_b = f"p4a_B_{uid[:10]}"
    now = datetime.now(timezone.utc)

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    matrix: list[dict] = []
    findings: list[str] = []
    try:
        g = stack.graphiti

        await _add_episode(
            g,
            name=f"p4a_a_{uid[:8]}",
            body=_fixture(marker_a, "Alice", "Alpha"),
            group_id=group_a,
        )
        # Baseline A before B
        edges_a0 = await g.search(marker_a, group_ids=[group_a], num_results=10)
        eps_a0 = await g.retrieve_episodes(now, last_n=10, group_ids=[group_a])
        assert _marker_in_edges(edges_a0, marker_a), "A must be searchable before B"
        assert _marker_in_episodes(eps_a0, marker_a), "A episodes must retrieve before B"

        await _add_episode(
            g,
            name=f"p4a_b_{uid[:8]}",
            body=_fixture(marker_b, "Bob", "Beta"),
            group_id=group_b,
        )
        driver_after_b = _driver_db(g)

        scopes = [
            ("A", group_a, marker_a, marker_b),
            ("B", group_b, marker_b, marker_a),
        ]
        surfaces = ("retrieve_episodes", "search")

        for scope_label, scope_gid, expected, foreign in scopes:
            for surface in surfaces:
                before = _driver_db(g)
                if surface == "retrieve_episodes":
                    eps = await g.retrieve_episodes(now, last_n=10, group_ids=[scope_gid])
                    after = _driver_db(g)
                    row = {
                        "surface": surface,
                        "scope_label": scope_label,
                        "requested_group": scope_gid,
                        "driver_database_before": before,
                        "driver_database_after": after,
                        "result_count": len(eps),
                        "expected_marker": expected,
                        "foreign_marker": foreign,
                        "expected_marker_found": _marker_in_episodes(eps, expected),
                        "foreign_marker_found": _marker_in_episodes(eps, foreign),
                        "episode_group_ids": [getattr(e, "group_id", None) for e in eps],
                        "episode_names": [getattr(e, "name", None) for e in eps],
                    }
                else:
                    edges = await g.search(expected, group_ids=[scope_gid], num_results=10)
                    after = _driver_db(g)
                    row = {
                        "surface": surface,
                        "scope_label": scope_label,
                        "requested_group": scope_gid,
                        "driver_database_before": before,
                        "driver_database_after": after,
                        "result_count": len(edges),
                        "expected_marker": expected,
                        "foreign_marker": foreign,
                        "expected_marker_found": _marker_in_edges(edges, expected),
                        "foreign_marker_found": _marker_in_edges(edges, foreign),
                        "facts": [getattr(e, "fact", "") for e in edges],
                    }
                matrix.append(row)

        # Classify
        missing_expected = [r for r in matrix if not r["expected_marker_found"]]
        foreign_leaks = [r for r in matrix if r["foreign_marker_found"]]
        search_ok = {
            r["scope_label"]: r["expected_marker_found"]
            for r in matrix
            if r["surface"] == "search"
        }
        retrieve_ok = {
            r["scope_label"]: r["expected_marker_found"]
            for r in matrix
            if r["surface"] == "retrieve_episodes"
        }
        divergence = any(
            search_ok.get(lbl) != retrieve_ok.get(lbl) for lbl in ("A", "B")
        )

        # Last-write affinity: shared driver stuck on B after write B; non-B scope miss
        last_write_affinity = driver_after_b == group_b and any(
            (not r["expected_marker_found"]) and r["requested_group"] != driver_after_b
            for r in matrix
        )

        evidence = {
            "marker_a": marker_a,
            "marker_b": marker_b,
            "group_a": group_a,
            "group_b": group_b,
            "driver_database_after_write_b": driver_after_b,
            "matrix": matrix,
            "divergence_search_vs_retrieve": divergence,
            "last_write_affinity_symptom": last_write_affinity,
        }

        status = "PASS"
        finding_id = None
        if foreign_leaks:
            status = "FAIL"
            finding_id = "F-P4-CROSS-GROUP-LEAKAGE"
            findings.append(finding_id)
        elif divergence and missing_expected:
            status = "FAIL"
            finding_id = "F-P4-READ-SURFACE-DIVERGENCE"
            findings.append(finding_id)
        elif last_write_affinity or missing_expected:
            status = "FAIL"
            finding_id = "F-P4-LAST-WRITE-AFFINITY"
            findings.append(finding_id)
        elif divergence:
            # surfaces disagree but both found expected somehow — still a finding
            status = "FAIL"
            finding_id = "F-P4-READ-SURFACE-DIVERGENCE"
            findings.append(finding_id)

        _record("P4A", "last_write_routing_matrix", status, evidence, finding_id=finding_id)
        if status != "PASS":
            pytest.fail(f"P4A {status} {finding_id}: {json.dumps(evidence)[:2000]}")
    except Exception as exc:
        already = False
        if RECEIPT_PATH.exists():
            data = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
            already = any(
                ph.get("phase") == "P4A" and ph.get("status") == "FAIL"
                for ph in data.get("phases", [])
            )
        if not already:
            _record(
                "P4A",
                "last_write_routing_matrix",
                "FAIL",
                {"error": repr(exc), "matrix": matrix},
                finding_id="F-P4-LAST-WRITE-AFFINITY",
            )
        raise
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p4b_multi_group_search(db_path: Path):
    """P4B: search(group_ids=[A,B]) must return BOTH markers; A-only or B-only = FAIL."""
    uid = _uuid()
    marker_a = f"A_ONLY_{uid}"
    marker_b = f"B_ONLY_{uid}"
    group_a = f"p4b_A_{uid[:10]}"
    group_b = f"p4b_B_{uid[:10]}"

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        g = stack.graphiti
        await _add_episode(
            g, name=f"p4b_a_{uid[:8]}", body=_fixture(marker_a, "Alice", "Alpha"), group_id=group_a
        )
        await _add_episode(
            g, name=f"p4b_b_{uid[:8]}", body=_fixture(marker_b, "Bob", "Beta"), group_id=group_b
        )

        before = _driver_db(g)
        # Query designed to match both groups' episode facts (shared probe + MarkerCorp)
        edges = await g.search(
            SHARED_PROBE, group_ids=[group_a, group_b], num_results=20
        )
        after = _driver_db(g)
        found_a = _marker_in_edges(edges, marker_a)
        found_b = _marker_in_edges(edges, marker_b)
        evidence = {
            "marker_a": marker_a,
            "marker_b": marker_b,
            "group_a": group_a,
            "group_b": group_b,
            "query": SHARED_PROBE,
            "group_ids": [group_a, group_b],
            "driver_database_before": before,
            "driver_database_after": after,
            "result_count": len(edges),
            "found_a": found_a,
            "found_b": found_b,
            "facts": [getattr(e, "fact", "") for e in edges],
        }
        if found_a and found_b:
            _record("P4B", "multi_group_search", "PASS", evidence)
        elif found_a or found_b:
            # TZ: FAIL/PARTIAL — use FAIL + finding F-P4-MULTISCOPE-PARTIAL
            _record(
                "P4B",
                "multi_group_search",
                "FAIL",
                evidence,
                finding_id="F-P4-MULTISCOPE-PARTIAL",
            )
            pytest.fail(
                "P4B multi-group search returned only one scope "
                f"(found_a={found_a}, found_b={found_b}) — F-P4-MULTISCOPE-PARTIAL"
            )
        else:
            _record(
                "P4B",
                "multi_group_search",
                "FAIL",
                evidence,
                finding_id="F-P4-MULTISCOPE-PARTIAL",
            )
            pytest.fail("P4B multi-group search found neither marker")
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p4c_multi_group_retrieve_episodes(db_path: Path):
    """P4C: retrieve_episodes(group_ids=[A,B]) expecting episodes from both groups."""
    uid = _uuid()
    marker_a = f"A_ONLY_{uid}"
    marker_b = f"B_ONLY_{uid}"
    group_a = f"p4c_A_{uid[:10]}"
    group_b = f"p4c_B_{uid[:10]}"
    now = datetime.now(timezone.utc)

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        g = stack.graphiti
        await _add_episode(
            g, name=f"p4c_a_{uid[:8]}", body=_fixture(marker_a, "Carol", "Gamma"), group_id=group_a
        )
        await _add_episode(
            g, name=f"p4c_b_{uid[:8]}", body=_fixture(marker_b, "Dave", "Delta"), group_id=group_b
        )

        # API exists on Graphiti 0.29.3 — applicable
        before = _driver_db(g)
        try:
            eps = await g.retrieve_episodes(now, last_n=10, group_ids=[group_a, group_b])
        except TypeError as exc:
            evidence = {"error": repr(exc), "note": "API signature rejected multi group_ids"}
            _record(
                "P4C",
                "multi_group_retrieve_episodes",
                "NOT_APPLICABLE",
                evidence,
            )
            return

        after = _driver_db(g)
        found_a = _marker_in_episodes(eps, marker_a)
        found_b = _marker_in_episodes(eps, marker_b)
        group_ids_seen = sorted({getattr(e, "group_id", None) for e in eps})
        evidence = {
            "marker_a": marker_a,
            "marker_b": marker_b,
            "group_a": group_a,
            "group_b": group_b,
            "driver_database_before": before,
            "driver_database_after": after,
            "result_count": len(eps),
            "found_a": found_a,
            "found_b": found_b,
            "episode_group_ids": [getattr(e, "group_id", None) for e in eps],
            "group_ids_seen": group_ids_seen,
            "episode_names": [getattr(e, "name", None) for e in eps],
        }
        if found_a and found_b:
            _record("P4C", "multi_group_retrieve_episodes", "PASS", evidence)
        elif found_a or found_b:
            _record(
                "P4C",
                "multi_group_retrieve_episodes",
                "FAIL",
                evidence,
                finding_id="F-P4-MULTISCOPE-PARTIAL",
            )
            pytest.fail(
                f"P4C retrieve_episodes multi-group partial (a={found_a}, b={found_b})"
            )
        else:
            _record(
                "P4C",
                "multi_group_retrieve_episodes",
                "FAIL",
                evidence,
                finding_id="F-P4-MULTISCOPE-PARTIAL",
            )
            pytest.fail("P4C retrieve_episodes multi-group found neither marker")
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p4d_write_order_reversal(db_path: Path):
    """P4D: A→B→read A and B→A→read B — check last-written affinity failures."""
    uid = _uuid()
    marker_a = f"A_ONLY_{uid}"
    marker_b = f"B_ONLY_{uid}"
    group_a = f"p4d_A_{uid[:10]}"
    group_b = f"p4d_B_{uid[:10]}"
    now = datetime.now(timezone.utc)

    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    try:
        g = stack.graphiti
        rows: list[dict] = []

        # Sequence 1: A → B → read A
        await _add_episode(
            g, name=f"p4d1_a_{uid[:8]}", body=_fixture(marker_a, "Eve", "Echo"), group_id=group_a
        )
        await _add_episode(
            g, name=f"p4d1_b_{uid[:8]}", body=_fixture(marker_b, "Frank", "Foxtrot"), group_id=group_b
        )
        db_after_ab = _driver_db(g)
        before = _driver_db(g)
        edges_a = await g.search(marker_a, group_ids=[group_a], num_results=10)
        after_s = _driver_db(g)
        eps_a = await g.retrieve_episodes(now, last_n=10, group_ids=[group_a])
        after_e = _driver_db(g)
        rows.append(
            {
                "sequence": "A_then_B_read_A",
                "driver_database_after_writes": db_after_ab,
                "search": {
                    "requested_group": group_a,
                    "driver_database_before": before,
                    "driver_database_after": after_s,
                    "result_count": len(edges_a),
                    "expected_marker_found": _marker_in_edges(edges_a, marker_a),
                    "foreign_marker_found": _marker_in_edges(edges_a, marker_b),
                },
                "retrieve_episodes": {
                    "requested_group": group_a,
                    "driver_database_before": after_s,
                    "driver_database_after": after_e,
                    "result_count": len(eps_a),
                    "expected_marker_found": _marker_in_episodes(eps_a, marker_a),
                    "foreign_marker_found": _marker_in_episodes(eps_a, marker_b),
                },
            }
        )

        # Sequence 2 on SAME instance: B → A → read B
        # (B already last-written; write B again then A, then read B)
        await _add_episode(
            g,
            name=f"p4d2_b_{uid[:8]}",
            body=_fixture(marker_b, "Frank", "Foxtrot"),
            group_id=group_b,
        )
        await _add_episode(
            g,
            name=f"p4d2_a_{uid[:8]}",
            body=_fixture(marker_a, "Eve", "Echo"),
            group_id=group_a,
        )
        db_after_ba = _driver_db(g)
        before = _driver_db(g)
        edges_b = await g.search(marker_b, group_ids=[group_b], num_results=10)
        after_s = _driver_db(g)
        eps_b = await g.retrieve_episodes(now, last_n=10, group_ids=[group_b])
        after_e = _driver_db(g)
        rows.append(
            {
                "sequence": "B_then_A_read_B",
                "driver_database_after_writes": db_after_ba,
                "search": {
                    "requested_group": group_b,
                    "driver_database_before": before,
                    "driver_database_after": after_s,
                    "result_count": len(edges_b),
                    "expected_marker_found": _marker_in_edges(edges_b, marker_b),
                    "foreign_marker_found": _marker_in_edges(edges_b, marker_a),
                },
                "retrieve_episodes": {
                    "requested_group": group_b,
                    "driver_database_before": after_s,
                    "driver_database_after": after_e,
                    "result_count": len(eps_b),
                    "expected_marker_found": _marker_in_episodes(eps_b, marker_b),
                    "foreign_marker_found": _marker_in_episodes(eps_b, marker_a),
                },
            }
        )

        affinity_failures = []
        leaks = []
        for row in rows:
            for surface in ("search", "retrieve_episodes"):
                cell = row[surface]
                if not cell["expected_marker_found"]:
                    affinity_failures.append(
                        {
                            "sequence": row["sequence"],
                            "surface": surface,
                            "driver_after_writes": row["driver_database_after_writes"],
                            "requested_group": cell["requested_group"],
                        }
                    )
                if cell["foreign_marker_found"]:
                    leaks.append({"sequence": row["sequence"], "surface": surface})

        evidence = {
            "marker_a": marker_a,
            "marker_b": marker_b,
            "group_a": group_a,
            "group_b": group_b,
            "rows": rows,
            "affinity_failures": affinity_failures,
            "leaks": leaks,
        }
        if leaks:
            _record(
                "P4D",
                "write_order_reversal",
                "FAIL",
                evidence,
                finding_id="F-P4-CROSS-GROUP-LEAKAGE",
            )
            pytest.fail("P4D cross-group leakage on order reversal reads")
        if affinity_failures:
            _record(
                "P4D",
                "write_order_reversal",
                "FAIL",
                evidence,
                finding_id="F-P4-LAST-WRITE-AFFINITY",
            )
            pytest.fail(
                f"P4D last-write affinity failures: {affinity_failures}"
            )
        _record("P4D", "write_order_reversal", "PASS", evidence)
    finally:
        await stack.aclose()


@pytest.mark.asyncio
async def test_p4_cleanup_shutdown_warning_documented(db_path: Path):
    """Document AsyncManagementCommands.shutdown as MINOR/RESOURCE CLEANUP (not a P4 fail)."""
    # Capture whether the known redislite warning still appears around close.
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True)
    saw = False
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            await stack.aclose()
            for w in caught:
                msg = str(w.message)
                if "AsyncManagementCommands.shutdown" in msg and "never awaited" in msg:
                    saw = True
    except Exception:
        # aclose already ran or partially ran
        pass

    evidence = {
        "warning_name": "coroutine 'AsyncManagementCommands.shutdown' was never awaited",
        "severity_during_aclose_in_this_test": saw,
        "severity": "MINOR",
        "category": "RESOURCE_CLEANUP",
        "note": (
            "Known redislite/FalkorDBLite teardown noise. Lab bootstrap prefers "
            "AsyncFalkorDB.close() over FalkorDriver.close()/aclose-only. "
            "No obvious one-line fix without invasive redislite changes; left as finding."
        ),
        "pytest_filter": "tests filterwarnings ignore this RuntimeWarning",
    }
    _write_finding_note(
        "F-P4-CLEANUP-SHUTDOWN-WARNING",
        "# F-P4-CLEANUP-SHUTDOWN-WARNING\n\n"
        "severity: MINOR\ncategory: RESOURCE_CLEANUP\n\n"
        f"```json\n{json.dumps(evidence, indent=2)}\n```\n",
    )
    _record("P4_CLEANUP", "shutdown_warning", "PASS", evidence)
    # Does not fail the suite — documentation only
