"""P6: Stale restore / resurrection boundary (lab only).

Anti-hallucination:
  RESTORED_BYTES ≠ RESTORED_CURRENT_APPLICABILITY
  searchable ≠ temporally current
  Distinguish A (add_episode late-T1) vs B (EntityEdge.save of SNAPSHOT_PRE)

Uses DeterministicTemporalLLMClient from P5; Falkor bootstrap with llm_client
override; group clone for edge dumps.

Does NOT start P7 / Fractal MemoryOps / OpenAI/Grok / Ladybug / Graphiti upgrade.
Does NOT import/copy SVL model into Graphiti — comparison discussion in findings only.
Allowed claims: this fixture only.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodeType

from fractal_lab.experiments.deterministic_temporal_llm import DeterministicTemporalLLMClient
from fractal_lab.experiments.falkor_graphiti_bootstrap import LabGraphitiStack, open_lab_graphiti

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:coroutine 'AsyncManagementCommands.shutdown' was never awaited:RuntimeWarning"
    ),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = REPO_ROOT / "artifacts" / "run_005"
FINDINGS = ARTIFACTS / "findings"
DATA_ROOT = REPO_ROOT / "data" / "falkor_e2e_p6"
RECEIPT_PATH = ARTIFACTS / "result.json"
PROVIDER_RECEIPT = ARTIFACTS / "provider_decisions.json"
SNAPSHOT_PRE_PATH = ARTIFACTS / "snapshot_pre.json"
SNAPSHOT_POST_PATH = ARTIFACTS / "snapshot_post.json"
BEFORE_RESTORE = ARTIFACTS / "before_restore_edges.json"
AFTER_RESTORE = ARTIFACTS / "after_restore_edges.json"
REOPEN_AFTER_RESTORE = ARTIFACTS / "reopen_after_restore.json"

T1 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
Q3 = datetime(2026, 1, 4, 10, 0, 0, tzinfo=timezone.utc)  # Q3 > T2

_BASELINE_OK: bool | None = None
_BASELINE_BLOCK_REASON: str | None = None
_STATE: dict[str, Any] = {}


def _uuid() -> str:
    return uuid.uuid4().hex


def _dt_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _approx_eq(a: datetime | None, b: datetime | None, *, tol_seconds: float = 2.0) -> bool:
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
    if status in {
        "FAIL",
        "FIXTURE_FAIL",
        "BLOCKED",
        "GRAPHITI_TEMPORAL_CONTRADICTION_FAIL",
    } and finding_id:
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
        "created_at": _dt_iso(e.created_at),
        "source_node_uuid": e.source_node_uuid,
        "target_node_uuid": e.target_node_uuid,
        "episodes": list(e.episodes or []),
    }


def _edge_snapshot_full(e: EntityEdge) -> dict:
    """Faithful restore payload for EntityEdge.save (includes embedding)."""
    pub = _edge_public(e)
    pub["fact_embedding"] = list(e.fact_embedding) if e.fact_embedding is not None else None
    pub["attributes"] = dict(e.attributes or {})
    return pub


def _classify_temporal(edge: EntityEdge, query_time: datetime) -> list[str]:
    labels = ["STORED"]
    va = edge.valid_at
    ia = edge.invalid_at
    if va is not None and va.tzinfo is None:
        va = va.replace(tzinfo=timezone.utc)
    if ia is not None and ia.tzinfo is None:
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


def _fixture_late_t1(late_marker: str) -> str:
    return (
        f"ProjectOrion uses Python as its RUNTIME_LANGUAGE. "
        f"The unique retrieval marker is {late_marker}."
    )


async def _dump_group_edges(graphiti, group_id: str) -> list[EntityEdge]:
    driver = graphiti.driver
    try:
        if getattr(driver, "provider", None) == GraphProvider.FALKORDB:
            if group_id != getattr(driver, "_database", None):
                driver = driver.clone(database=group_id)
        return await EntityEdge.get_by_group_ids(driver, [group_id])
    except Exception:
        return []


def _group_driver(graphiti, group_id: str):
    driver = graphiti.driver
    if getattr(driver, "provider", None) == GraphProvider.FALKORDB:
        if group_id != getattr(driver, "_database", None):
            driver = driver.clone(database=group_id)
    return driver


def _find_by_marker(edges: list[EntityEdge], marker: str) -> list[EntityEdge]:
    return [e for e in edges if marker in (e.fact or "")]


def _find_owner(edges: list[EntityEdge]) -> list[EntityEdge]:
    out = []
    for e in edges:
        blob = f"{e.name} {e.fact}"
        if "OWNED_BY" in blob or "owned by Alice" in blob.lower():
            out.append(e)
    return out


def _find_language(edges: list[EntityEdge]) -> list[EntityEdge]:
    return [
        e
        for e in edges
        if "RUNTIME_LANGUAGE" in f"{e.name} {e.fact}"
        or ("Python" in (e.fact or "") or "Rust" in (e.fact or ""))
        and "owned by" not in (e.fact or "").lower()
    ]


async def _save_and_close(stack: LabGraphitiStack) -> None:
    """Persist RDB to disk and shut down redislite so copies / subprocess reopen work."""
    try:
        client = stack.falkor_db.client
        await client.execute_command("SAVE")
    except Exception as exc:  # noqa: BLE001
        _STATE.setdefault("save_warnings", []).append(repr(exc))
    settings_path = Path(str(stack.db_path) + ".settings")
    pid = None
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            pidfile = settings.get("pidfile")
            if pidfile and Path(pidfile).exists():
                pid = int(Path(pidfile).read_text(encoding="utf-8").strip())
        except Exception:
            pid = None
    await stack.aclose()
    if pid is not None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.kill(pid, sig)
                time.sleep(0.2)
            except ProcessLookupError:
                break


def _copy_fresh_db(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    settings = Path(str(dst) + ".settings")
    if settings.exists():
        settings.unlink()
    if not src.exists():
        raise FileNotFoundError(f"baseline RDB missing: {src}")
    shutil.copy2(src, dst)


def _entity_edge_from_snapshot(snap: dict) -> EntityEdge:
    return EntityEdge(
        uuid=snap["uuid"],
        group_id=snap["group_id"],
        source_node_uuid=snap["source_node_uuid"],
        target_node_uuid=snap["target_node_uuid"],
        created_at=_parse_dt(snap.get("created_at")) or datetime.now(timezone.utc),
        name=snap["name"],
        fact=snap["fact"],
        fact_embedding=snap.get("fact_embedding"),
        episodes=list(snap.get("episodes") or []),
        expired_at=_parse_dt(snap.get("expired_at")),
        valid_at=_parse_dt(snap.get("valid_at")),
        invalid_at=_parse_dt(snap.get("invalid_at")),
        reference_time=_parse_dt(snap.get("reference_time")),
        attributes=dict(snap.get("attributes") or {}),
    )


def _require_baseline():
    if _BASELINE_OK is not True:
        pytest.fail(
            f"BLOCKED STOP: T2 baseline cannot reproduce "
            f"(ok={_BASELINE_OK}, reason={_BASELINE_BLOCK_REASON})"
        )


# ---------------------------------------------------------------------------
# Baseline: T1 Python → SNAPSHOT_PRE; T2 Rust → SNAPSHOT_POST
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p6_baseline_t2_and_snapshots():
    """Build T2 contradiction baseline; persist SNAPSHOT_PRE/POST. BLOCKED STOP if fail."""
    global _BASELINE_OK, _BASELINE_BLOCK_REASON
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)

    uid = _uuid()
    markers = {
        "uid": uid,
        "old": f"P6_OLD_{uid}",
        "new": f"P6_NEW_{uid}",
        "late": f"P6_LATE_OLD_{uid}",
        "group_id": f"p6_orion_{uid[:10]}",
        "baseline_db": DATA_ROOT / f"p6_baseline_{uid}.db",
    }
    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(
        markers["baseline_db"], database="default_db", build_indices=True, llm_client=client
    )
    try:
        # --- T1 ---
        r1 = await stack.graphiti.add_episode(
            name="p6_t1_python",
            episode_body=_fixture_t1(markers["old"]),
            source_description="fractal_lab_p6_stale_restore",
            reference_time=T1,
            source=EpisodeType.text,
            group_id=markers["group_id"],
        )
        edges_pre = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_pre = _find_by_marker(edges_pre, markers["old"])
        owner_pre = _find_owner(edges_pre)

        if not old_pre:
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "OLD edge missing after T1"
            evidence = {
                "edges": [_edge_public(e) for e in edges_pre],
                "episode_edges": [_edge_public(e) for e in (r1.edges or [])],
            }
            _record(
                "BASELINE",
                "BASELINE",
                "BLOCKED",
                evidence,
                finding_id="F-P6-BASELINE-T1-OLD-MISSING",
            )
            pytest.fail(f"BLOCKED STOP: {_BASELINE_BLOCK_REASON}: {evidence}")

        old_edge = old_pre[0]
        if old_edge.invalid_at is not None or not _approx_eq(old_edge.valid_at, T1):
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "SNAPSHOT_PRE preconditions failed (valid_at/invalid_at)"
            evidence = {"old": _edge_public(old_edge)}
            _record(
                "BASELINE",
                "BASELINE",
                "BLOCKED",
                evidence,
                finding_id="F-P6-BASELINE-SNAPSHOT-PRE",
            )
            pytest.fail(f"BLOCKED STOP: {_BASELINE_BLOCK_REASON}: {evidence}")

        snapshot_pre = _edge_snapshot_full(old_edge)
        SNAPSHOT_PRE_PATH.write_text(
            json.dumps(snapshot_pre, indent=2, default=str), encoding="utf-8"
        )

        # --- T2 contradiction ---
        r2 = await stack.graphiti.add_episode(
            name="p6_t2_rust",
            episode_body=_fixture_t2(markers["new"]),
            source_description="fractal_lab_p6_stale_restore",
            reference_time=T2,
            source=EpisodeType.text,
            group_id=markers["group_id"],
        )
        edges_post = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_post = _find_by_marker(edges_post, markers["old"])
        new_post = _find_by_marker(edges_post, markers["new"])
        owner_post = _find_owner(edges_post)

        if not old_post or not new_post:
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "OLD or NEW missing after T2"
            evidence = {
                "old": [_edge_public(e) for e in old_post],
                "new": [_edge_public(e) for e in new_post],
                "all": [_edge_public(e) for e in edges_post],
            }
            _record(
                "BASELINE",
                "BASELINE",
                "BLOCKED",
                evidence,
                finding_id="F-P6-BASELINE-T2-MISSING",
            )
            pytest.fail(f"BLOCKED STOP: {_BASELINE_BLOCK_REASON}: {evidence}")

        old_after = old_post[0]
        new_edge = new_post[0]
        if old_after.uuid != snapshot_pre["uuid"]:
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "OLD UUID changed across T2 (cannot snapshot same UUID)"
            evidence = {"pre_uuid": snapshot_pre["uuid"], "post_uuid": old_after.uuid}
            _record(
                "BASELINE",
                "BASELINE",
                "BLOCKED",
                evidence,
                finding_id="F-P6-BASELINE-UUID-DRIFT",
            )
            pytest.fail(f"BLOCKED STOP: {_BASELINE_BLOCK_REASON}: {evidence}")

        if old_after.invalid_at is None or not _approx_eq(old_after.invalid_at, T2):
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = (
                f"T2 did not invalidate OLD at T2 (invalid_at={_dt_iso(old_after.invalid_at)})"
            )
            evidence = {
                "old_after": _edge_public(old_after),
                "new": _edge_public(new_edge),
                "provider_decisions": list(client.decisions),
            }
            _record(
                "BASELINE",
                "BASELINE",
                "BLOCKED",
                evidence,
                finding_id="F-P6-BASELINE-T2-NOT-INVALIDATED",
            )
            pytest.fail(f"BLOCKED STOP: {_BASELINE_BLOCK_REASON}: {evidence}")

        if new_edge.invalid_at is not None:
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "NEW edge unexpectedly invalidated at baseline"
            _record(
                "BASELINE",
                "BASELINE",
                "BLOCKED",
                {"new": _edge_public(new_edge)},
                finding_id="F-P6-BASELINE-NEW-INVALID",
            )
            pytest.fail(f"BLOCKED STOP: {_BASELINE_BLOCK_REASON}")

        snapshot_post = _edge_snapshot_full(old_after)
        SNAPSHOT_POST_PATH.write_text(
            json.dumps(snapshot_post, indent=2, default=str), encoding="utf-8"
        )

        _STATE["markers"] = markers
        _STATE["snapshot_pre"] = snapshot_pre
        _STATE["snapshot_post"] = snapshot_post
        _STATE["new_edge"] = _edge_public(new_edge)
        _STATE["owner_post"] = [_edge_public(e) for e in owner_post]
        _STATE["baseline_edges"] = [_edge_public(e) for e in edges_post]
        _STATE["baseline_db"] = str(markers["baseline_db"])
        _STATE["group_id"] = markers["group_id"]
        _STATE["baseline_provider_decisions"] = list(client.decisions)

        evidence = {
            "group_id": markers["group_id"],
            "old_marker": markers["old"],
            "new_marker": markers["new"],
            "snapshot_pre_uuid": snapshot_pre["uuid"],
            "snapshot_pre_invalid_at": snapshot_pre["invalid_at"],
            "snapshot_post_uuid": snapshot_post["uuid"],
            "snapshot_post_invalid_at": snapshot_post["invalid_at"],
            "same_uuid": snapshot_pre["uuid"] == snapshot_post["uuid"],
            "new_edge": _edge_public(new_edge),
            "owner_count": len(owner_post),
            "artifact_pre": str(SNAPSHOT_PRE_PATH),
            "artifact_post": str(SNAPSHOT_POST_PATH),
        }
        _BASELINE_OK = True
        _BASELINE_BLOCK_REASON = None
        _record("BASELINE", "BASELINE", "PASS", evidence)
    finally:
        PROVIDER_RECEIPT.write_text(
            json.dumps(
                {"baseline": client.decisions, "note": "P6 provider decisions accumulate per phase"},
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        await _save_and_close(stack)


# ---------------------------------------------------------------------------
# P6-0: close/reopen — OLD.invalid_at=T2, NEW/OWNER None
# ---------------------------------------------------------------------------


_REOPEN_HELPER = r'''
import asyncio, json, sys
from fractal_lab.experiments.deterministic_temporal_llm import DeterministicTemporalLLMClient
from fractal_lab.experiments.falkor_graphiti_bootstrap import open_lab_graphiti
from graphiti_core.edges import EntityEdge

async def main(db_path: str, group_id: str, old_m: str, new_m: str) -> int:
    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(db_path, database="default_db", build_indices=True, llm_client=client)
    try:
        driver = stack.graphiti.driver.clone(database=group_id)
        edges = await EntityEdge.get_by_group_ids(driver, [group_id])
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
        owner = [
            pub(e)
            for e in edges
            if "owned by Alice" in (e.fact or "").lower() or e.name == "OWNED_BY"
        ]
        print(json.dumps({"old": old, "new": new, "owner": owner, "count": len(edges)}))
        if not old or not new or not owner:
            return 2
        if old[0].get("invalid_at") is None:
            return 4
        if new[0].get("invalid_at") is not None:
            return 5
        if owner[0].get("invalid_at") is not None:
            return 6
        return 0
    finally:
        await stack.aclose()

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])))
'''


@pytest.mark.asyncio
async def test_p6_0_reopen_after_t2():
    _require_baseline()
    markers = _STATE["markers"]
    helper = ARTIFACTS / "_p6_reopen_helper.py"
    helper.write_text(_REOPEN_HELPER, encoding="utf-8")
    py = REPO_ROOT / ".venv" / "bin" / "python"
    cmd = [
        str(py if py.exists() else sys.executable),
        str(helper),
        str(markers["baseline_db"]),
        markers["group_id"],
        markers["old"],
        markers["new"],
    ]
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, env=env, timeout=180)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    payload = json.loads(lines[-1]) if lines else {}
    evidence = {
        "returncode": proc.returncode,
        "payload": payload,
        "stderr_tail": proc.stderr[-2000:],
    }
    old = (payload.get("old") or [None])[0]
    new = (payload.get("new") or [None])[0]
    owner = (payload.get("owner") or [None])[0]
    ok = (
        proc.returncode == 0
        and old
        and new
        and owner
        and old.get("invalid_at") is not None
        and _approx_eq(_parse_dt(old.get("invalid_at")), T2)
        and new.get("invalid_at") is None
        and owner.get("invalid_at") is None
    )
    evidence["asserts"] = {
        "old_invalid_at_T2": bool(old and _approx_eq(_parse_dt(old.get("invalid_at")), T2)),
        "new_invalid_at_none": bool(new and new.get("invalid_at") is None),
        "owner_invalid_at_none": bool(owner and owner.get("invalid_at") is None),
    }
    if not ok:
        _record("P6-0", "P6-0", "FAIL", evidence, finding_id="F-P6-0-REOPEN")
        pytest.fail(f"P6-0 reopen assert failed: {evidence}")
    _record("P6-0", "P6-0", "PASS", evidence)


# ---------------------------------------------------------------------------
# P6-A: late add_episode reference_time=T1 (high-level path)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p6_a_late_add_episode_t1():
    """P6-A high-level: late Python episode at T1. Never mix with EntityEdge.save."""
    _require_baseline()
    markers = _STATE["markers"]
    db_a = DATA_ROOT / f"p6_a_{markers['uid']}.db"
    _copy_fresh_db(Path(markers["baseline_db"]), db_a)

    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(db_a, database="default_db", build_indices=True, llm_client=client)
    try:
        before = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before, markers["old"])
        result = await stack.graphiti.add_episode(
            name="p6_late_t1_python",
            episode_body=_fixture_late_t1(markers["late"]),
            source_description="fractal_lab_p6_a_late_episode",
            reference_time=T1,  # NOT T3
            source=EpisodeType.text,
            group_id=markers["group_id"],
        )
        after = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after, markers["old"])
        new_after = _find_by_marker(after, markers["new"])
        late_after = _find_by_marker(after, markers["late"])

        # Provider must identify Rust T2 as contradiction candidate
        rust_selected = False
        dup_receipts = [d for d in client.decisions if d.get("model") == "EdgeDuplicate"]
        for rec in dup_receipts:
            facts = (rec.get("existing_facts") or []) + (rec.get("invalidation_candidates") or [])
            idxs = set(rec.get("contradicted_facts") or [])
            for item in facts:
                if int(item.get("idx", -1)) not in idxs:
                    continue
                fact = str(item.get("fact", ""))
                if markers["new"] in fact:
                    rust_selected = True
                elif "Rust" in fact and (
                    "RUNTIME_LANGUAGE" in fact
                    or "runtime_language" in fact.lower()
                    or "language" in fact.lower()
                ):
                    rust_selected = True

        # Classify from temporal metadata on the ORIGINAL OLD uuid
        classification = "INCONCLUSIVE"
        old_meta = None
        if old_after:
            old_e = old_after[0]
            old_meta = _edge_public(old_e)
            ia = old_e.invalid_at
            if ia is None:
                # Same UUID lost invalidation via high-level path
                classification = "RESURRECTION_HIGH_LEVEL"
            elif _approx_eq(ia, T2):
                classification = "SAFE_HIGH_LEVEL"
            else:
                classification = "INCONCLUSIVE"
        elif old_before and not old_after:
            classification = "INCONCLUSIVE"

        evidence = {
            "path": "A_add_episode_late_T1",
            "reference_time": _dt_iso(T1),
            "late_marker": markers["late"],
            "provider_selected_rust_t2": rust_selected,
            "dup_receipts": dup_receipts,
            "old_before": [_edge_public(e) for e in old_before],
            "old_after": [_edge_public(e) for e in old_after],
            "new_after": [_edge_public(e) for e in new_after],
            "late_after": [_edge_public(e) for e in late_after],
            "episode_edges": [_edge_public(e) for e in (result.edges or [])],
            "classification": classification,
            "anti_hallucination": {
                "RESTORED_BYTES": "not claimed for path A (no snapshot save)",
                "RESTORED_CURRENT_APPLICABILITY": (
                    "true iff OLD uuid TEMPORALLY_CURRENT at Q3 after late episode"
                    if old_after
                    else "n/a"
                ),
                "note": "searchable ≠ temporally current; classify from invalid_at/valid_at",
            },
            "old_at_Q3": (
                _classify_temporal(old_after[0], Q3) if old_after else None
            ),
        }
        _STATE["p6_a"] = evidence
        _STATE["p6_a_db"] = str(db_a)

        # Persist provider decisions
        existing = {}
        if PROVIDER_RECEIPT.exists():
            try:
                existing = json.loads(PROVIDER_RECEIPT.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
        existing["p6_a"] = client.decisions
        PROVIDER_RECEIPT.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")

        if not rust_selected:
            _record(
                "P6-A",
                "P6-A",
                "FIXTURE_FAIL",
                evidence,
                finding_id="F-P6-A-PROVIDER-MISSED-RUST",
            )
            pytest.fail(f"FIXTURE_FAIL: provider did not select Rust T2: {evidence}")

        status = "PASS" if classification in {"SAFE_HIGH_LEVEL", "RESURRECTION_HIGH_LEVEL"} else "INCONCLUSIVE"
        # Observation statuses are still recorded; INCONCLUSIVE fails soft via status label
        if classification == "INCONCLUSIVE":
            _record("P6-A", "P6-A", "INCONCLUSIVE", evidence, finding_id="F-P6-A-INCONCLUSIVE")
            pytest.fail(f"INCONCLUSIVE P6-A classification: {evidence}")
        _record("P6-A", "P6-A", "PASS", {**evidence, "observed_class": classification})
        # Also stamp matrix with observed class for the summary matrix
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        receipt.setdefault("matrix", {})["P6-A_class"] = classification
        RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    finally:
        await _save_and_close(stack)


# ---------------------------------------------------------------------------
# P6-B: low-level EntityEdge.save(SNAPSHOT_PRE) on fresh T2 baseline copy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p6_b_low_level_snapshot_pre_save():
    """P6-B low-level path — NEVER mix with A. Hypothesis until executed."""
    _require_baseline()
    markers = _STATE["markers"]
    snap_pre = json.loads(SNAPSHOT_PRE_PATH.read_text(encoding="utf-8"))
    assert snap_pre.get("invalid_at") is None, "SNAPSHOT_PRE must have invalid_at None"

    db_b = DATA_ROOT / f"p6_b_{markers['uid']}.db"
    _copy_fresh_db(Path(markers["baseline_db"]), db_b)

    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(db_b, database="default_db", build_indices=True, llm_client=client)
    try:
        before = await _dump_group_edges(stack.graphiti, markers["group_id"])
        BEFORE_RESTORE.write_text(
            json.dumps(
                {
                    "phase": "P6-B_before",
                    "edges": [_edge_public(e) for e in before],
                    "hypothesis": (
                        "EntityEdge.save of SNAPSHOT_PRE on same UUID may overwrite "
                        "invalid_at T2→None (stale resurrection of bytes)."
                    ),
                    "anti_hallucination": (
                        "RESTORED_BYTES ≠ RESTORED_CURRENT_APPLICABILITY; "
                        "observation only after save executes."
                    ),
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        old_before = _find_by_marker(before, markers["old"])
        if not old_before:
            evidence = {"before": [_edge_public(e) for e in before]}
            _record("P6-B", "P6-B", "INCONCLUSIVE", evidence, finding_id="F-P6-B-OLD-MISSING")
            pytest.fail(f"INCONCLUSIVE: OLD missing before restore: {evidence}")

        before_ia = old_before[0].invalid_at
        before_pub = _edge_public(old_before[0])

        # Ensure embedding present for Falkor SET e = $edge_data
        edge = _entity_edge_from_snapshot(snap_pre)
        if edge.fact_embedding is None:
            await edge.generate_embedding(stack.graphiti.embedder)

        driver = _group_driver(stack.graphiti, markers["group_id"])
        await edge.save(driver)

        after = await _dump_group_edges(stack.graphiti, markers["group_id"])
        AFTER_RESTORE.write_text(
            json.dumps(
                {
                    "phase": "P6-B_after",
                    "edges": [_edge_public(e) for e in after],
                    "saved_snapshot_pre": {k: v for k, v in snap_pre.items() if k != "fact_embedding"},
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        old_after = _find_by_marker(after, markers["old"])
        new_after = _find_by_marker(after, markers["new"])
        classification = "INCONCLUSIVE"
        restored_bytes = False
        restored_current_applicability = False

        if not old_after:
            classification = "INCONCLUSIVE"
        else:
            oa = old_after[0]
            restored_bytes = oa.uuid == snap_pre["uuid"] and oa.invalid_at is None
            # Temporally current at Q3 iff valid_at<=Q3 and invalid_at is None
            labels_q3 = _classify_temporal(oa, Q3)
            restored_current_applicability = "TEMPORALLY_CURRENT" in labels_q3
            if before_ia is not None and oa.invalid_at is None:
                classification = "STALE_RESURRECTION_OBSERVED"
            elif before_ia is not None and oa.invalid_at is not None and _approx_eq(
                oa.invalid_at, before_ia
            ):
                classification = "NOT_OBSERVED"
            else:
                classification = "INCONCLUSIVE"

        evidence = {
            "path": "B_EntityEdge_save_SNAPSHOT_PRE",
            "distinct_from": "A_add_episode_late_T1",
            "before_old": before_pub,
            "after_old": [_edge_public(e) for e in old_after],
            "after_new": [_edge_public(e) for e in new_after],
            "classification": classification,
            "RESTORED_BYTES": restored_bytes,
            "RESTORED_CURRENT_APPLICABILITY": restored_current_applicability,
            "note": (
                "RESTORED_BYTES means SNAPSHOT_PRE fields written (invalid_at None). "
                "RESTORED_CURRENT_APPLICABILITY means metadata classifies TEMPORALLY_CURRENT at Q3. "
                "These are not the same claim."
            ),
            "artifacts": {
                "before": str(BEFORE_RESTORE),
                "after": str(AFTER_RESTORE),
            },
        }
        _STATE["p6_b"] = evidence
        _STATE["p6_b_db"] = str(db_b)

        if classification == "INCONCLUSIVE":
            _record("P6-B", "P6-B", "INCONCLUSIVE", evidence, finding_id="F-P6-B-INCONCLUSIVE")
            pytest.fail(f"INCONCLUSIVE P6-B: {evidence}")

        _record("P6-B", "P6-B", "PASS", evidence)
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        receipt.setdefault("matrix", {})["P6-B_class"] = classification
        receipt.setdefault("matrix", {})["P6-B_RESTORED_BYTES"] = restored_bytes
        receipt.setdefault("matrix", {})["P6-B_RESTORED_CURRENT_APPLICABILITY"] = (
            restored_current_applicability
        )
        RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    finally:
        await _save_and_close(stack)


# ---------------------------------------------------------------------------
# P6-C: replay SNAPSHOT_POST on fresh T2 baseline — OLD stays historical
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p6_c_replay_snapshot_post():
    _require_baseline()
    markers = _STATE["markers"]
    snap_post = json.loads(SNAPSHOT_POST_PATH.read_text(encoding="utf-8"))
    assert snap_post.get("invalid_at") is not None, "SNAPSHOT_POST must keep invalid_at=T2"

    db_c = DATA_ROOT / f"p6_c_{markers['uid']}.db"
    _copy_fresh_db(Path(markers["baseline_db"]), db_c)

    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(db_c, database="default_db", build_indices=True, llm_client=client)
    try:
        before = await _dump_group_edges(stack.graphiti, markers["group_id"])
        edge = _entity_edge_from_snapshot(snap_post)
        if edge.fact_embedding is None:
            await edge.generate_embedding(stack.graphiti.embedder)
        driver = _group_driver(stack.graphiti, markers["group_id"])
        await edge.save(driver)
        after = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after, markers["old"])

        ok = bool(
            old_after
            and old_after[0].invalid_at is not None
            and _approx_eq(old_after[0].invalid_at, T2)
            and "TEMPORALLY_EXPIRED" in _classify_temporal(old_after[0], Q3)
        )
        evidence = {
            "path": "C_EntityEdge_save_SNAPSHOT_POST",
            "before_old": [_edge_public(e) for e in _find_by_marker(before, markers["old"])],
            "after_old": [_edge_public(e) for e in old_after],
            "expect": "OLD remains historical (invalid_at≈T2)",
            "ok": ok,
            "at_Q3": _classify_temporal(old_after[0], Q3) if old_after else None,
        }
        _STATE["p6_c"] = evidence
        if not ok:
            _record("P6-C", "P6-C", "FAIL", evidence, finding_id="F-P6-C-NOT-HISTORICAL")
            pytest.fail(f"P6-C OLD not historical after SNAPSHOT_POST replay: {evidence}")
        _record("P6-C", "P6-C", "PASS", evidence)
    finally:
        await _save_and_close(stack)


# ---------------------------------------------------------------------------
# P6-D: reopen after P6-B state — persistence of restore outcome
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p6_d_reopen_after_p6_b():
    _require_baseline()
    if "p6_b_db" not in _STATE or "p6_b" not in _STATE:
        pytest.skip("P6-B did not populate state")

    markers = _STATE["markers"]
    helper = ARTIFACTS / "_p6_reopen_helper.py"
    if not helper.exists():
        helper.write_text(_REOPEN_HELPER, encoding="utf-8")
    py = REPO_ROOT / ".venv" / "bin" / "python"
    cmd = [
        str(py if py.exists() else sys.executable),
        str(helper),
        _STATE["p6_b_db"],
        markers["group_id"],
        markers["old"],
        markers["new"],
    ]
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, env=env, timeout=180)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    payload = json.loads(lines[-1]) if lines else {}
    REOPEN_AFTER_RESTORE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    expected_class = _STATE["p6_b"]["classification"]
    old = (payload.get("old") or [None])[0]
    persisted = False
    if expected_class == "STALE_RESURRECTION_OBSERVED":
        persisted = bool(old and old.get("invalid_at") is None)
    elif expected_class == "NOT_OBSERVED":
        persisted = bool(old and old.get("invalid_at") is not None)
    else:
        persisted = bool(old)

    evidence = {
        "returncode": proc.returncode,
        "payload": payload,
        "expected_class_from_B": expected_class,
        "persisted_consistent_with_B": persisted,
        "artifact": str(REOPEN_AFTER_RESTORE),
    }
    _STATE["p6_d"] = evidence
    if not persisted or not old:
        _record("P6-D", "P6-D", "FAIL", evidence, finding_id="F-P6-D-PERSIST")
        pytest.fail(f"P6-D reopen persistence mismatch: {evidence}")
    _record("P6-D", "P6-D", "PASS", evidence)


# ---------------------------------------------------------------------------
# P6-E: Q3>T2 classify language edges; concurrent contradictory current?
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p6_e_q3_concurrent_current_edges():
    _require_baseline()
    if "p6_b_db" not in _STATE:
        pytest.skip("P6-B db missing")

    markers = _STATE["markers"]
    # Use post-B state (where resurrection may have occurred)
    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(
        _STATE["p6_b_db"], database="default_db", build_indices=True, llm_client=client
    )
    try:
        edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        lang_edges = []
        for e in edges:
            fact = e.fact or ""
            if "owned by" in fact.lower():
                continue
            if "RUNTIME_LANGUAGE" in f"{e.name} {fact}" or "Python" in fact or "Rust" in fact:
                lang_edges.append(e)

        packs = []
        current_python = []
        current_rust = []
        for e in lang_edges:
            labels = _classify_temporal(e, Q3)
            pack = {"edge": _edge_public(e), "at_Q3": labels}
            packs.append(pack)
            if "TEMPORALLY_CURRENT" in labels:
                if "Python" in (e.fact or ""):
                    current_python.append(e.uuid)
                if "Rust" in (e.fact or ""):
                    current_rust.append(e.uuid)

        observation = None
        if current_python and current_rust:
            observation = "CONCURRENT_CONTRADICTORY_CURRENT_EDGES"

        evidence = {
            "Q3": _dt_iso(Q3),
            "language_edges": packs,
            "current_python_uuids": current_python,
            "current_rust_uuids": current_rust,
            "observation": observation,
            "note": (
                "Observation scoped to this fixture/post-P6-B state only. "
                "searchable ≠ temporally current; labels from valid_at/invalid_at."
            ),
        }
        _STATE["p6_e"] = evidence
        _record("P6-E", "P6-E", "PASS", evidence)
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        receipt.setdefault("matrix", {})["P6-E_observation"] = observation or "NONE"
        RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    finally:
        await stack.aclose()


# ---------------------------------------------------------------------------
# Finalize + SVL comparison discussion (no import/copy)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p6_z_finalize_result_and_svl_discussion():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    receipt: dict = {"phases": [], "matrix": {}}
    if RECEIPT_PATH.exists():
        try:
            receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    matrix = receipt.get("matrix") or {}
    ids = ["BASELINE", "P6-0", "P6-A", "P6-B", "P6-C", "P6-D", "P6-E"]
    full_pass = all(matrix.get(i) == "PASS" for i in ids)

    # Comparison discussion vs SVL model.py (read-only; not imported into Graphiti)
    svl_discussion = {
        "source": "velantrian/-Velantrim-State-Validation-Lab-/src/state_validation_lab/model.py",
        "read_only": True,
        "imported_into_graphiti": False,
        "svl_invariant": (
            "SVL ResearchStateModel.restore() writes RESTORED_STALE_CANDIDATE with "
            "applicable=False into a quarantined candidate store; it never overwrites "
            "current disposition. reconcile() cannot clear later revoke/erase/supersede."
        ),
        "graphiti_p6_b_contrast_this_fixture_only": (
            "P6-B EntityEdge.save(SNAPSHOT_PRE) on Falkor MERGE SET e=$edge_data can "
            "overwrite the live edge's invalid_at when classification is "
            "STALE_RESURRECTION_OBSERVED. That is RESTORED_BYTES onto the live graph row, "
            "not an SVL-style quarantined candidate. This does NOT imply "
            "'Falkor unsafe' universally nor 'SVL must integrate'."
        ),
        "graphiti_p6_a_contrast": (
            "P6-A uses add_episode (high-level). Classification SAFE_HIGH_LEVEL vs "
            "RESURRECTION_HIGH_LEVEL is separate from B's low-level save path."
        ),
        "forbidden_claims_not_made": [
            "Graphiti prevents resurrection universally",
            "Falkor unsafe",
            "SVL must integrate",
        ],
    }
    (FINDINGS / "SVL_COMPARISON_DISCUSSION.md").write_text(
        "# SVL comparison discussion (P6)\n\n"
        "Read-only comparison against SVL `model.py`. "
        "**Not imported/copied into Graphiti.**\n\n"
        f"```json\n{json.dumps(svl_discussion, indent=2)}\n```\n",
        encoding="utf-8",
    )

    p7_recommendation = {
        "start_p7": False,
        "bounded_recommendation_only": (
            "If P6 full PASS: a bounded P7 could inventory which Graphiti write surfaces "
            "(add_episode vs EntityEdge.save vs bulk load) accept pre-invalidation snapshots "
            "on FalkorDBLite for this fixture family — still lab-only, still no Fractal "
            "MemoryOps / Crystal / SVL integration / Ladybug / real LLM. Do not start P7 here."
        ),
    }

    summary = {
        "suite": "P6_stale_restore_resurrection_boundary",
        "graphiti": "0.29.3",
        "backend": "FalkorDBLite",
        "branch": "experiment/falkordblite-deterministic-memory",
        "start_commit": "cc0e864",
        "matrix": {i: matrix.get(i, "MISSING") for i in ids},
        "class_observations": {
            "P6-A_class": matrix.get("P6-A_class"),
            "P6-B_class": matrix.get("P6-B_class"),
            "P6-B_RESTORED_BYTES": matrix.get("P6-B_RESTORED_BYTES"),
            "P6-B_RESTORED_CURRENT_APPLICABILITY": matrix.get(
                "P6-B_RESTORED_CURRENT_APPLICABILITY"
            ),
            "P6-E_observation": matrix.get("P6-E_observation"),
        },
        "full_pass": full_pass,
        "claim_if_full_pass": (
            "Graphiti 0.29.3 + FalkorDBLite exercised this deterministic stale-restore "
            "fixture (A high-level late episode vs B low-level SNAPSHOT_PRE save) with "
            "recorded classifications. Fixture-scoped only."
            if full_pass
            else None
        ),
        "markers": _STATE.get("markers"),
        "p6_a": _STATE.get("p6_a"),
        "p6_b": _STATE.get("p6_b"),
        "p6_c": _STATE.get("p6_c"),
        "p6_d": _STATE.get("p6_d"),
        "p6_e": _STATE.get("p6_e"),
        "T1": _dt_iso(T1),
        "T2": _dt_iso(T2),
        "Q3": _dt_iso(Q3),
        "svl_comparison_discussion": svl_discussion,
        "p7_recommendation_only": p7_recommendation,
        "anti_hallucination": {
            "RESTORED_BYTES": "snapshot fields written back to store",
            "RESTORED_CURRENT_APPLICABILITY": "metadata says TEMPORALLY_CURRENT at query time",
            "searchable_ne_temporally_current": True,
            "A_ne_B": "add_episode late-T1 ≠ EntityEdge.save(SNAPSHOT_PRE)",
        },
    }
    receipt["summary"] = summary
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    assert True
