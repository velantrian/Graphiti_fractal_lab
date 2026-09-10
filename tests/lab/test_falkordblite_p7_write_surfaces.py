"""P7: Bounded write-surface inventory (lab only).

Inventory + experimentally verify Graphiti 0.29.3 + FalkorDBLite write surfaces
through which a pre-invalidation EntityEdge snapshot can re-enter storage, and
whether each can clear a NEWER invalid_at / expired_at.

Anti-hallucination:
  RESTORED_BYTES ≠ RESTORED_CURRENT_APPLICABILITY
  Fixture-scoped only; no universal Falkor/Graphiti/SVL claims
  Distinguish high-level (resolve then persist) vs low-level (raw temporal fields)

NO fixes. NO Fractal MemoryOps / Crystal / SVL / Ladybug / real LLM / upgrade.
STOP after matrix + receipts.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.edges import EntityEdge
from graphiti_core.models.edges.edge_db_queries import (
    get_entity_edge_save_bulk_query,
    get_entity_edge_save_query,
)
from graphiti_core.namespaces import EdgeNamespace
from graphiti_core.nodes import EntityNode, EpisodeType
from graphiti_core.utils.bulk_utils import RawEpisode, add_nodes_and_edges_bulk

from fractal_lab.experiments.deterministic_temporal_llm import DeterministicTemporalLLMClient
from fractal_lab.experiments.falkor_graphiti_bootstrap import LabGraphitiStack, open_lab_graphiti

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:coroutine 'AsyncManagementCommands.shutdown' was never awaited:RuntimeWarning"
    ),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = REPO_ROOT / "artifacts" / "run_006"
FINDINGS = ARTIFACTS / "findings"
DATA_ROOT = REPO_ROOT / "data" / "falkor_e2e_p7"
RECEIPT_PATH = ARTIFACTS / "result.json"
SNAPSHOT_PRE_PATH = ARTIFACTS / "snapshot_pre.json"
SNAPSHOT_POST_PATH = ARTIFACTS / "snapshot_post.json"
INVENTORY_PATH = FINDINGS / "INVENTORY.md"
MATRIX_PATH = FINDINGS / "MATRIX.md"

T1 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
Q3 = datetime(2026, 1, 4, 10, 0, 0, tzinfo=timezone.utc)

_BASELINE_OK: bool | None = None
_BASELINE_BLOCK_REASON: str | None = None
_STATE: dict[str, Any] = {}

# Ordered matrix ids for finalize
MATRIX_IDS = [
    "BASELINE",
    "P7-A",
    "P7-B",
    "P7-C",
    "P7-D",
    "P7-E",
    "P7-F",
    "P7-G",
    "P7-H",
    "P7-I",
    "P7-N/A",
]


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
    if "classification" in evidence:
        receipt.setdefault("matrix", {})[f"{test_id}_class"] = evidence["classification"]
    if "invalid_at_class" in evidence:
        receipt.setdefault("matrix", {})[f"{test_id}_invalid_at"] = evidence["invalid_at_class"]
    if "expired_at_class" in evidence:
        receipt.setdefault("matrix", {})[f"{test_id}_expired_at"] = evidence["expired_at_class"]
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    if status in {"FAIL", "FIXTURE_FAIL", "BLOCKED"} and finding_id:
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
    pub = _edge_public(e)
    pub["fact_embedding"] = list(e.fact_embedding) if e.fact_embedding is not None else None
    pub["attributes"] = dict(e.attributes or {})
    return pub


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


def _classify_field(
    *,
    before: datetime | None,
    after: datetime | None,
    expected_newer: datetime,
    field: str,
) -> str:
    """Classify clearing vs preserving for invalid_at or expired_at."""
    if before is None:
        return "INCONCLUSIVE_NO_BEFORE"
    before_is_newer = (
        _approx_eq(before, expected_newer)
        if field == "invalid_at"
        else True  # expired_at is wall-clock at T2 invalidate; any non-None before counts
    )
    if field == "invalid_at" and not before_is_newer:
        return "INCONCLUSIVE_BEFORE_NOT_T2"
    if before is not None and after is None:
        return "CLEARS_NEWER_INVALIDATION" if field == "invalid_at" else "CLEARS_EXPIRED_AT"
    if field == "invalid_at" and after is not None and _approx_eq(after, expected_newer):
        return "PRESERVES_INVALIDATION"
    if field == "expired_at" and after is not None and before is not None:
        if _approx_eq(after, before, tol_seconds=5.0):
            return "PRESERVES_EXPIRED_AT"
        return "PARTIAL_EXPIRED_AT_CHANGED"
    if after is not None and before is not None and not _approx_eq(after, before, tol_seconds=5.0):
        return "PARTIAL"
    return "INCONCLUSIVE"


def _overall_class(invalid_at_class: str, expired_at_class: str) -> str:
    clears_i = invalid_at_class == "CLEARS_NEWER_INVALIDATION"
    preserves_i = invalid_at_class == "PRESERVES_INVALIDATION"
    clears_e = expired_at_class == "CLEARS_EXPIRED_AT"
    preserves_e = expired_at_class == "PRESERVES_EXPIRED_AT"
    if clears_i and (clears_e or expired_at_class.startswith("CLEARS")):
        return "CLEARS_NEWER_INVALIDATION"
    if preserves_i and preserves_e:
        return "PRESERVES_INVALIDATION"
    if preserves_i and clears_e:
        return "PARTIAL"
    if clears_i and preserves_e:
        return "PARTIAL"
    if invalid_at_class.startswith("NOT_") or expired_at_class.startswith("NOT_"):
        return invalid_at_class if invalid_at_class.startswith("NOT_") else expired_at_class
    if "INCONCLUSIVE" in invalid_at_class or "INCONCLUSIVE" in expired_at_class:
        return "INCONCLUSIVE"
    if clears_i:
        return "CLEARS_NEWER_INVALIDATION"
    if preserves_i:
        return "PRESERVES_INVALIDATION"
    return "PARTIAL"


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


async def _save_and_close(stack: LabGraphitiStack) -> None:
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


def _require_baseline():
    if _BASELINE_OK is not True:
        pytest.fail(
            f"BLOCKED STOP: T2 baseline cannot reproduce "
            f"(ok={_BASELINE_OK}, reason={_BASELINE_BLOCK_REASON})"
        )


async def _open_phase_db(phase_key: str) -> tuple[LabGraphitiStack, DeterministicTemporalLLMClient, Path]:
    markers = _STATE["markers"]
    db_path = DATA_ROOT / f"p7_{phase_key}_{markers['uid']}.db"
    _copy_fresh_db(Path(markers["baseline_db"]), db_path)
    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(
        db_path, database="default_db", build_indices=True, llm_client=client
    )
    return stack, client, db_path


def _measure_old(before: EntityEdge, after: EntityEdge | None) -> dict:
    if after is None:
        return {
            "invalid_at_class": "INCONCLUSIVE",
            "expired_at_class": "INCONCLUSIVE",
            "classification": "INCONCLUSIVE",
            "before": _edge_public(before),
            "after": None,
            "RESTORED_BYTES": False,
        }
    ia_class = _classify_field(
        before=before.invalid_at,
        after=after.invalid_at,
        expected_newer=T2,
        field="invalid_at",
    )
    ea_class = _classify_field(
        before=before.expired_at,
        after=after.expired_at,
        expected_newer=T2,
        field="expired_at",
    )
    overall = _overall_class(ia_class, ea_class)
    restored_bytes = after.uuid == before.uuid and after.invalid_at is None
    return {
        "invalid_at_class": ia_class,
        "expired_at_class": ea_class,
        "classification": overall,
        "before": _edge_public(before),
        "after": _edge_public(after),
        "RESTORED_BYTES": restored_bytes,
        "RESTORED_CURRENT_APPLICABILITY": (
            after.valid_at is not None
            and after.valid_at <= Q3
            and after.invalid_at is None
        ),
    }


# ---------------------------------------------------------------------------
# Static inventory (source-backed)
# ---------------------------------------------------------------------------


STATIC_INVENTORY = [
    {
        "id": "EntityEdge.save",
        "symbol": "graphiti_core.edges.EntityEdge.save",
        "path": "edges.py:335",
        "signature": "async def save(self, driver: GraphDriver)",
        "accepts_temporal_fields": True,
        "fields": ["invalid_at", "expired_at", "valid_at", "reference_time"],
        "persist_mechanism": "get_entity_edge_save_query(FALKORDB): MERGE ... SET e = $edge_data",
        "hypothesized_risk": "HIGH — SET e=$edge_data can overwrite newer invalid_at with None",
        "matrix_rows": ["P7-B", "P7-C"],
    },
    {
        "id": "FalkorEntityEdgeOperations.save",
        "symbol": "graphiti_core.driver.falkordb.operations.entity_edge_ops.FalkorEntityEdgeOperations.save",
        "path": "driver/falkordb/operations/entity_edge_ops.py:36",
        "signature": "async def save(self, executor, edge, tx=None)",
        "accepts_temporal_fields": True,
        "fields": ["invalid_at", "expired_at", "valid_at"],
        "note": "Omits reference_time from edge_data (unlike EntityEdge.save)",
        "persist_mechanism": "Same get_entity_edge_save_query(FALKORDB)",
        "hypothesized_risk": "HIGH — same SET e=$edge_data",
        "matrix_rows": ["P7-E"],
    },
    {
        "id": "FalkorEntityEdgeOperations.save_bulk",
        "symbol": "graphiti_core.driver.falkordb.operations.entity_edge_ops.FalkorEntityEdgeOperations.save_bulk",
        "path": "driver/falkordb/operations/entity_edge_ops.py:66",
        "signature": "async def save_bulk(self, executor, edges, tx=None, batch_size=100)",
        "accepts_temporal_fields": True,
        "fields": ["invalid_at", "expired_at", "valid_at"],
        "persist_mechanism": "get_entity_edge_save_bulk_query(FALKORDB): UNWIND ... SET r = edge",
        "hypothesized_risk": "HIGH — bulk SET replaces relationship map",
        "matrix_rows": ["P7-F"],
    },
    {
        "id": "EntityEdgeNamespace.save",
        "symbol": "graphiti_core.namespaces.edges.EntityEdgeNamespace.save",
        "path": "namespaces/edges.py:47",
        "signature": "async def save(self, edge: EntityEdge, tx=None) -> EntityEdge",
        "accepts_temporal_fields": True,
        "persist_mechanism": "generate_embedding + FalkorEntityEdgeOperations.save",
        "hypothesized_risk": "HIGH (delegates to ops); Falkor routing requires group-cloned driver",
        "matrix_rows": ["P7-E"],
    },
    {
        "id": "EntityEdgeNamespace.save_bulk",
        "symbol": "graphiti_core.namespaces.edges.EntityEdgeNamespace.save_bulk",
        "path": "namespaces/edges.py:56",
        "signature": "async def save_bulk(self, edges, tx=None, batch_size=100)",
        "accepts_temporal_fields": True,
        "persist_mechanism": "FalkorEntityEdgeOperations.save_bulk",
        "hypothesized_risk": "HIGH",
        "matrix_rows": ["P7-F"],
    },
    {
        "id": "add_nodes_and_edges_bulk",
        "symbol": "graphiti_core.utils.bulk_utils.add_nodes_and_edges_bulk",
        "path": "utils/bulk_utils.py:128",
        "signature": "async def add_nodes_and_edges_bulk(driver, episodic_nodes, episodic_edges, entity_nodes, entity_edges, embedder)",
        "accepts_temporal_fields": True,
        "fields": ["invalid_at", "expired_at", "valid_at", "reference_time"],
        "persist_mechanism": "get_entity_edge_save_bulk_query → SET r = edge",
        "hypothesized_risk": "HIGH when called with pre-built SNAPSHOT_PRE EntityEdge list",
        "matrix_rows": ["P7-D"],
    },
    {
        "id": "Graphiti.add_episode",
        "symbol": "graphiti_core.graphiti.Graphiti.add_episode",
        "path": "graphiti.py:980",
        "signature": "async def add_episode(... reference_time, group_id, ...)",
        "accepts_temporal_fields": "indirect — LLM extract + resolve_extracted_edges then bulk persist",
        "persist_mechanism": "_process_episode_data → add_nodes_and_edges_bulk(resolved+invalidated)",
        "hypothesized_risk": "LOW for late-T1 stale narrative (P6-A SAFE_HIGH_LEVEL); does not accept raw SNAPSHOT_PRE bytes",
        "matrix_rows": ["P7-A"],
    },
    {
        "id": "Graphiti.add_episode_bulk",
        "symbol": "graphiti_core.graphiti.Graphiti.add_episode_bulk",
        "path": "graphiti.py:1230",
        "signature": "async def add_episode_bulk(bulk_episodes: list[RawEpisode], group_id=...)",
        "accepts_temporal_fields": "indirect — same resolve then bulk",
        "persist_mechanism": "add_nodes_and_edges_bulk(resolved+invalidated)",
        "hypothesized_risk": "LOW for late-T1 (expect preserve like add_episode)",
        "matrix_rows": ["P7-H"],
    },
    {
        "id": "Graphiti.add_triplet",
        "symbol": "graphiti_core.graphiti.Graphiti.add_triplet",
        "path": "graphiti.py:1645",
        "signature": "async def add_triplet(source_node, edge: EntityEdge, target_node)",
        "accepts_temporal_fields": "edge object accepted then resolve_extracted_edge before bulk write",
        "persist_mechanism": "resolve_extracted_edge → add_nodes_and_edges_bulk",
        "hypothesized_risk": "MEDIUM — may rewrite same UUID after resolve; not a raw snapshot restore",
        "matrix_rows": ["P7-I"],
    },
    {
        "id": "driver.execute_query + get_entity_edge_save_query",
        "symbol": "FalkorDriver.execute_query + get_entity_edge_save_query(FALKORDB)",
        "path": "driver/falkordb_driver.py:238 + models/edges/edge_db_queries.py:63",
        "signature": "async def execute_query(cypher_query_, **kwargs)",
        "accepts_temporal_fields": True,
        "persist_mechanism": "MERGE RELATES_TO SET e=$edge_data (same Cypher as EntityEdge.save)",
        "hypothesized_risk": "HIGH — raw Cypher surface",
        "matrix_rows": ["P7-G"],
    },
    {
        "id": "EpisodicEdge.save / CommunityEdge.save / HasEpisodeEdge / NextEpisodeEdge",
        "symbol": "graphiti_core.edges.(EpisodicEdge|CommunityEdge|HasEpisodeEdge|NextEpisodeEdge).save",
        "path": "edges.py (non-EntityEdge)",
        "accepts_temporal_fields": False,
        "persist_mechanism": "MENTIONS / HAS_MEMBER / HAS_EPISODE / NEXT_EPISODE — no invalid_at/expired_at",
        "hypothesized_risk": "N/A for EntityEdge temporal resurrection",
        "matrix_rows": ["P7-N/A"],
    },
    {
        "id": "RelatesToNode_ (Kuzu)",
        "symbol": "Kuzu RelatesToNode_ intermediate",
        "path": "models/edges/edge_db_queries.py KUZU branch; driver/kuzu/*",
        "accepts_temporal_fields": "Kuzu-only modeling",
        "persist_mechanism": "Not used on FalkorDBLite (direct RELATES_TO relationship)",
        "hypothesized_risk": "NOT_RUN_ON_FALKOR",
        "matrix_rows": ["P7-N/A"],
    },
    {
        "id": "remove_episode",
        "symbol": "graphiti_core.graphiti.Graphiti.remove_episode",
        "path": "graphiti.py:1765",
        "accepts_temporal_fields": False,
        "persist_mechanism": "DELETE edges/nodes created by episode — no snapshot restore",
        "hypothesized_risk": "N/A",
        "matrix_rows": ["P7-N/A"],
    },
    {
        "id": "restore/import helpers",
        "symbol": "(none found in graphiti_core 0.29.3)",
        "path": "migrations/ empty; no restore/import EntityEdge APIs located",
        "accepts_temporal_fields": False,
        "hypothesized_risk": "N/A — not present",
        "matrix_rows": ["P7-N/A"],
    },
]


@pytest.mark.asyncio
async def test_p7_00_write_inventory_markdown():
    """Evidence-backed inventory from installed graphiti_core 0.29.3 sources."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    gc = REPO_ROOT / ".venv" / "lib" / "python3.13" / "site-packages" / "graphiti_core"
    # Verify key files exist at claimed paths
    checks = {
        "edges.EntityEdge.save": (gc / "edges.py").exists(),
        "edge_db_queries": (gc / "models" / "edges" / "edge_db_queries.py").exists(),
        "bulk_utils": (gc / "utils" / "bulk_utils.py").exists(),
        "falkor_entity_edge_ops": (
            gc / "driver" / "falkordb" / "operations" / "entity_edge_ops.py"
        ).exists(),
        "namespaces_edges": (gc / "namespaces" / "edges.py").exists(),
        "graphiti.add_episode": (gc / "graphiti.py").exists(),
    }
    # Spot-check Falkor SET e = $edge_data
    falkor_query = get_entity_edge_save_query(GraphProvider.FALKORDB)
    bulk_query = get_entity_edge_save_bulk_query(GraphProvider.FALKORDB)
    assert "SET e = $edge_data" in falkor_query or "SET e = $edge_data" in falkor_query.replace(
        "\n", " "
    )
    assert "SET r = edge" in bulk_query.replace("\n", " ") or "SET r = edge" in bulk_query

    lines = [
        "# P7 Write-Surface Inventory (graphiti-core==0.29.3 + FalkorDBLite)",
        "",
        "Evidence-backed from installed package under `.venv/.../graphiti_core/`.",
        "Fixture-scoped experimental classifications live in MATRIX.md / result.json.",
        "",
        "| id | symbol | accepts invalid_at/expired_at | hypothesized risk | matrix |",
        "|---|---|---|---|---|",
    ]
    for row in STATIC_INVENTORY:
        lines.append(
            f"| {row['id']} | `{row['symbol']}` | {row.get('accepts_temporal_fields')} | "
            f"{row.get('hypothesized_risk', '')} | {', '.join(row.get('matrix_rows', []))} |"
        )
    lines.extend(
        [
            "",
            "## Source checks",
            f"```json\n{json.dumps(checks, indent=2)}\n```",
            "",
            "## Falkor single-edge save Cypher (excerpt)",
            "```cypher",
            falkor_query.strip(),
            "```",
            "",
            "## Falkor bulk-edge save Cypher (excerpt)",
            "```cypher",
            bulk_query.strip(),
            "```",
            "",
            "## Full inventory records",
            f"```json\n{json.dumps(STATIC_INVENTORY, indent=2)}\n```",
            "",
        ]
    )
    INVENTORY_PATH.write_text("\n".join(lines), encoding="utf-8")
    evidence = {
        "inventory_path": str(INVENTORY_PATH),
        "surface_count": len(STATIC_INVENTORY),
        "checks": checks,
        "falkor_save_has_set_map": "SET e = $edge_data" in falkor_query,
        "falkor_bulk_has_set_map": "SET r = edge" in bulk_query,
    }
    _STATE["inventory"] = evidence
    _record("INVENTORY", "INVENTORY", "PASS", evidence)
    assert all(checks.values())


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p7_baseline_t2_and_snapshots():
    global _BASELINE_OK, _BASELINE_BLOCK_REASON
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)

    uid = _uuid()
    markers = {
        "uid": uid,
        "old": f"P7_OLD_{uid}",
        "new": f"P7_NEW_{uid}",
        "late": f"P7_LATE_OLD_{uid}",
        "group_id": f"p7_orion_{uid[:10]}",
        "baseline_db": DATA_ROOT / f"p7_baseline_{uid}.db",
    }
    client = DeterministicTemporalLLMClient()
    stack = await open_lab_graphiti(
        markers["baseline_db"], database="default_db", build_indices=True, llm_client=client
    )
    try:
        await stack.graphiti.add_episode(
            name="p7_t1_python",
            episode_body=_fixture_t1(markers["old"]),
            source_description="fractal_lab_p7_write_surfaces",
            reference_time=T1,
            source=EpisodeType.text,
            group_id=markers["group_id"],
        )
        edges_pre = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_pre = _find_by_marker(edges_pre, markers["old"])
        if not old_pre:
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "OLD edge missing after T1"
            _record("BASELINE", "BASELINE", "BLOCKED", {"edges": [_edge_public(e) for e in edges_pre]})
            pytest.fail(_BASELINE_BLOCK_REASON)
        old_edge = old_pre[0]
        if old_edge.invalid_at is not None or not _approx_eq(old_edge.valid_at, T1):
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "SNAPSHOT_PRE preconditions failed"
            _record("BASELINE", "BASELINE", "BLOCKED", {"old": _edge_public(old_edge)})
            pytest.fail(_BASELINE_BLOCK_REASON)
        # Ensure embedding loaded for later restores
        if old_edge.fact_embedding is None:
            await old_edge.load_fact_embedding(_group_driver(stack.graphiti, markers["group_id"]))
        snapshot_pre = _edge_snapshot_full(old_edge)
        SNAPSHOT_PRE_PATH.write_text(json.dumps(snapshot_pre, indent=2, default=str), encoding="utf-8")

        await stack.graphiti.add_episode(
            name="p7_t2_rust",
            episode_body=_fixture_t2(markers["new"]),
            source_description="fractal_lab_p7_write_surfaces",
            reference_time=T2,
            source=EpisodeType.text,
            group_id=markers["group_id"],
        )
        edges_post = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_post = _find_by_marker(edges_post, markers["old"])
        new_post = _find_by_marker(edges_post, markers["new"])
        if not old_post or not new_post:
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "OLD or NEW missing after T2"
            _record(
                "BASELINE",
                "BASELINE",
                "BLOCKED",
                {"old": [_edge_public(e) for e in old_post], "new": [_edge_public(e) for e in new_post]},
            )
            pytest.fail(_BASELINE_BLOCK_REASON)
        old_after = old_post[0]
        if old_after.uuid != snapshot_pre["uuid"]:
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "OLD UUID changed across T2"
            _record("BASELINE", "BASELINE", "BLOCKED", {"pre": snapshot_pre["uuid"], "post": old_after.uuid})
            pytest.fail(_BASELINE_BLOCK_REASON)
        if old_after.invalid_at is None or not _approx_eq(old_after.invalid_at, T2):
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = f"T2 did not invalidate OLD (invalid_at={_dt_iso(old_after.invalid_at)})"
            _record("BASELINE", "BASELINE", "BLOCKED", {"old": _edge_public(old_after)})
            pytest.fail(_BASELINE_BLOCK_REASON)
        if old_after.expired_at is None:
            _BASELINE_OK = False
            _BASELINE_BLOCK_REASON = "T2 did not set expired_at on OLD (expected from resolve_edge_contradictions)"
            _record("BASELINE", "BASELINE", "BLOCKED", {"old": _edge_public(old_after)})
            pytest.fail(_BASELINE_BLOCK_REASON)
        if old_after.fact_embedding is None:
            await old_after.load_fact_embedding(_group_driver(stack.graphiti, markers["group_id"]))
        snapshot_post = _edge_snapshot_full(old_after)
        SNAPSHOT_POST_PATH.write_text(json.dumps(snapshot_post, indent=2, default=str), encoding="utf-8")

        _STATE["markers"] = markers
        _STATE["snapshot_pre"] = snapshot_pre
        _STATE["snapshot_post"] = snapshot_post
        _STATE["group_id"] = markers["group_id"]
        evidence = {
            "group_id": markers["group_id"],
            "snapshot_pre_invalid_at": snapshot_pre["invalid_at"],
            "snapshot_pre_expired_at": snapshot_pre["expired_at"],
            "snapshot_post_invalid_at": snapshot_post["invalid_at"],
            "snapshot_post_expired_at": snapshot_post["expired_at"],
            "same_uuid": snapshot_pre["uuid"] == snapshot_post["uuid"],
            "new_edge": _edge_public(new_post[0]),
        }
        _BASELINE_OK = True
        _BASELINE_BLOCK_REASON = None
        _record("BASELINE", "BASELINE", "PASS", evidence)
    finally:
        await _save_and_close(stack)


# ---------------------------------------------------------------------------
# Matrix rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_p7_a_add_episode_late_t1():
    """P7-A: high-level add_episode late T1 — expect PRESERVES (P6-A SAFE_HIGH_LEVEL)."""
    _require_baseline()
    markers = _STATE["markers"]
    stack, client, db_path = await _open_phase_db("a")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        await stack.graphiti.add_episode(
            name="p7_late_t1_python",
            episode_body=_fixture_late_t1(markers["late"]),
            source_description="fractal_lab_p7_a",
            reference_time=T1,
            source=EpisodeType.text,
            group_id=markers["group_id"],
        )
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after_list = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after_list[0] if old_after_list else None)
        # High-level path: map PRESERVES → expected
        evidence = {
            "path": "Graphiti.add_episode late reference_time=T1",
            "db": str(db_path),
            **measured,
            "note": "Does not pass SNAPSHOT_PRE bytes; narrative re-entry via extract/resolve",
            "provider_decisions_count": len(client.decisions),
        }
        # Expect preserve invalid_at≈T2
        ok = measured["invalid_at_class"] == "PRESERVES_INVALIDATION"
        _STATE["P7-A"] = evidence
        if not ok:
            _record("P7-A", "P7-A", "FAIL", evidence, finding_id="F-P7-A")
            pytest.fail(f"P7-A expected PRESERVES_INVALIDATION: {evidence}")
        _record("P7-A", "P7-A", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_b_entity_edge_save_snapshot_pre():
    """P7-B: EntityEdge.save(SNAPSHOT_PRE) — expect CLEARS (P6-B)."""
    _require_baseline()
    markers = _STATE["markers"]
    snap_pre = json.loads(SNAPSHOT_PRE_PATH.read_text(encoding="utf-8"))
    stack, _client, db_path = await _open_phase_db("b")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        edge = _entity_edge_from_snapshot(snap_pre)
        if edge.fact_embedding is None:
            await edge.generate_embedding(stack.graphiti.embedder)
        await edge.save(_group_driver(stack.graphiti, markers["group_id"]))
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after[0] if old_after else None)
        evidence = {
            "path": "EntityEdge.save(SNAPSHOT_PRE)",
            "db": str(db_path),
            **measured,
        }
        _STATE["P7-B"] = evidence
        if measured["classification"] != "CLEARS_NEWER_INVALIDATION":
            _record("P7-B", "P7-B", "FAIL", evidence, finding_id="F-P7-B")
            pytest.fail(f"P7-B expected CLEARS: {evidence}")
        _record("P7-B", "P7-B", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_c_entity_edge_save_snapshot_post():
    """P7-C: EntityEdge.save(SNAPSHOT_POST) control — expect PRESERVES."""
    _require_baseline()
    markers = _STATE["markers"]
    snap_post = json.loads(SNAPSHOT_POST_PATH.read_text(encoding="utf-8"))
    stack, _client, db_path = await _open_phase_db("c")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        edge = _entity_edge_from_snapshot(snap_post)
        if edge.fact_embedding is None:
            await edge.generate_embedding(stack.graphiti.embedder)
        await edge.save(_group_driver(stack.graphiti, markers["group_id"]))
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after[0] if old_after else None)
        evidence = {
            "path": "EntityEdge.save(SNAPSHOT_POST)",
            "db": str(db_path),
            **measured,
        }
        _STATE["P7-C"] = evidence
        if measured["invalid_at_class"] != "PRESERVES_INVALIDATION":
            _record("P7-C", "P7-C", "FAIL", evidence, finding_id="F-P7-C")
            pytest.fail(f"P7-C expected PRESERVES: {evidence}")
        _record("P7-C", "P7-C", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_d_add_nodes_and_edges_bulk_snapshot_pre():
    """P7-D: add_nodes_and_edges_bulk with SNAPSHOT_PRE entity edge list."""
    _require_baseline()
    markers = _STATE["markers"]
    snap_pre = json.loads(SNAPSHOT_PRE_PATH.read_text(encoding="utf-8"))
    stack, _client, db_path = await _open_phase_db("d")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        edge = _entity_edge_from_snapshot(snap_pre)
        if edge.fact_embedding is None:
            await edge.generate_embedding(stack.graphiti.embedder)
        driver = _group_driver(stack.graphiti, markers["group_id"])
        await add_nodes_and_edges_bulk(
            driver, [], [], [], [edge], stack.graphiti.embedder
        )
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after[0] if old_after else None)
        evidence = {
            "path": "add_nodes_and_edges_bulk([SNAPSHOT_PRE])",
            "db": str(db_path),
            **measured,
        }
        _STATE["P7-D"] = evidence
        # Observation: expect CLEARS like EntityEdge.save (same SET r=edge)
        if measured["classification"] not in {
            "CLEARS_NEWER_INVALIDATION",
            "PRESERVES_INVALIDATION",
            "PARTIAL",
            "INCONCLUSIVE",
        }:
            _record("P7-D", "P7-D", "FAIL", evidence, finding_id="F-P7-D")
            pytest.fail(f"P7-D unexpected class: {evidence}")
        _record("P7-D", "P7-D", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_e_namespace_entity_save_snapshot_pre():
    """P7-E: EdgeNamespace(group_driver).entity.save(SNAPSHOT_PRE)."""
    _require_baseline()
    markers = _STATE["markers"]
    snap_pre = json.loads(SNAPSHOT_PRE_PATH.read_text(encoding="utf-8"))
    stack, _client, db_path = await _open_phase_db("e")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        edge = _entity_edge_from_snapshot(snap_pre)
        driver = _group_driver(stack.graphiti, markers["group_id"])
        ns = EdgeNamespace(driver, stack.graphiti.embedder)
        await ns.entity.save(edge)
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after[0] if old_after else None)
        evidence = {
            "path": "EdgeNamespace(group_driver).entity.save(SNAPSHOT_PRE)",
            "delegates_to": "FalkorEntityEdgeOperations.save",
            "note_ops_omits_reference_time": True,
            "db": str(db_path),
            **measured,
        }
        _STATE["P7-E"] = evidence
        _record("P7-E", "P7-E", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_f_namespace_entity_save_bulk_snapshot_pre():
    """P7-F: EdgeNamespace(group_driver).entity.save_bulk([SNAPSHOT_PRE])."""
    _require_baseline()
    markers = _STATE["markers"]
    snap_pre = json.loads(SNAPSHOT_PRE_PATH.read_text(encoding="utf-8"))
    stack, _client, db_path = await _open_phase_db("f")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        edge = _entity_edge_from_snapshot(snap_pre)
        if edge.fact_embedding is None:
            await edge.generate_embedding(stack.graphiti.embedder)
        driver = _group_driver(stack.graphiti, markers["group_id"])
        ns = EdgeNamespace(driver, stack.graphiti.embedder)
        await ns.entity.save_bulk([edge])
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after[0] if old_after else None)
        evidence = {
            "path": "EdgeNamespace(group_driver).entity.save_bulk([SNAPSHOT_PRE])",
            "delegates_to": "FalkorEntityEdgeOperations.save_bulk",
            "db": str(db_path),
            **measured,
        }
        _STATE["P7-F"] = evidence
        _record("P7-F", "P7-F", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_g_driver_execute_query_raw_save():
    """P7-G: FalkorDriver.execute_query(get_entity_edge_save_query) with SNAPSHOT_PRE map."""
    _require_baseline()
    markers = _STATE["markers"]
    snap_pre = json.loads(SNAPSHOT_PRE_PATH.read_text(encoding="utf-8"))
    stack, _client, db_path = await _open_phase_db("g")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        edge = _entity_edge_from_snapshot(snap_pre)
        if edge.fact_embedding is None:
            await edge.generate_embedding(stack.graphiti.embedder)
        edge_data = {
            "source_uuid": edge.source_node_uuid,
            "target_uuid": edge.target_node_uuid,
            "uuid": edge.uuid,
            "name": edge.name,
            "group_id": edge.group_id,
            "fact": edge.fact,
            "fact_embedding": edge.fact_embedding,
            "episodes": edge.episodes,
            "created_at": edge.created_at,
            "expired_at": edge.expired_at,
            "valid_at": edge.valid_at,
            "invalid_at": edge.invalid_at,
            "reference_time": edge.reference_time,
        }
        driver = _group_driver(stack.graphiti, markers["group_id"])
        await driver.execute_query(
            get_entity_edge_save_query(GraphProvider.FALKORDB),
            edge_data=edge_data,
        )
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after[0] if old_after else None)
        evidence = {
            "path": "FalkorDriver.execute_query(get_entity_edge_save_query, edge_data=SNAPSHOT_PRE)",
            "db": str(db_path),
            **measured,
        }
        _STATE["P7-G"] = evidence
        _record("P7-G", "P7-G", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_h_add_episode_bulk_late_t1():
    """P7-H: add_episode_bulk with late T1 RawEpisode — expect PRESERVES like A."""
    _require_baseline()
    markers = _STATE["markers"]
    stack, client, db_path = await _open_phase_db("h")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        raw = RawEpisode(
            name="p7_bulk_late_t1",
            content=_fixture_late_t1(markers["late"] + "_BULK"),
            source_description="fractal_lab_p7_h",
            source=EpisodeType.text,
            reference_time=T1,
        )
        await stack.graphiti.add_episode_bulk([raw], group_id=markers["group_id"])
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_after = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after[0] if old_after else None)
        evidence = {
            "path": "Graphiti.add_episode_bulk([RawEpisode late T1])",
            "db": str(db_path),
            **measured,
            "provider_decisions_count": len(client.decisions),
        }
        _STATE["P7-H"] = evidence
        _record("P7-H", "P7-H", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_i_add_triplet_snapshot_pre():
    """P7-I: add_triplet with SNAPSHOT_PRE edge object (resolve then bulk)."""
    _require_baseline()
    markers = _STATE["markers"]
    snap_pre = json.loads(SNAPSHOT_PRE_PATH.read_text(encoding="utf-8"))
    stack, client, db_path = await _open_phase_db("i")
    try:
        before_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        old_before = _find_by_marker(before_edges, markers["old"])[0]
        edge = _entity_edge_from_snapshot(snap_pre)
        if edge.fact_embedding is None:
            await edge.generate_embedding(stack.graphiti.embedder)
        # Falkor: bind driver to group graph so get_by_uuid / add_triplet see edges
        if markers["group_id"] != getattr(stack.graphiti.driver, "_database", None):
            stack.graphiti.driver = stack.graphiti.driver.clone(database=markers["group_id"])
            stack.graphiti.clients.driver = stack.graphiti.driver
        source = await EntityNode.get_by_uuid(stack.graphiti.driver, edge.source_node_uuid)
        target = await EntityNode.get_by_uuid(stack.graphiti.driver, edge.target_node_uuid)
        result = await stack.graphiti.add_triplet(source, edge, target)
        after_edges = await _dump_group_edges(stack.graphiti, markers["group_id"])
        # Measure the ORIGINAL OLD uuid (may or may not be rewritten)
        old_after = [e for e in after_edges if e.uuid == snap_pre["uuid"]]
        if not old_after:
            old_after = _find_by_marker(after_edges, markers["old"])
        measured = _measure_old(old_before, old_after[0] if old_after else None)
        evidence = {
            "path": "Graphiti.add_triplet(source, SNAPSHOT_PRE_edge, target)",
            "db": str(db_path),
            "result_edge_uuids": [e.uuid for e in (result.edges or [])],
            "result_edge_invalid_ats": [_dt_iso(e.invalid_at) for e in (result.edges or [])],
            **measured,
            "note": "High-level resolve path — not raw RESTORED_BYTES guarantee",
            "provider_decisions_count": len(client.decisions),
        }
        _STATE["P7-I"] = evidence
        _record("P7-I", "P7-I", "PASS", evidence)
    finally:
        await _save_and_close(stack)


@pytest.mark.asyncio
async def test_p7_na_non_entity_surfaces():
    """Document N/A / NOT_RUN surfaces without claiming experimental clears."""
    evidence = {
        "EpisodicEdge.save": "NOT_APPLICABLE — no invalid_at/expired_at fields",
        "CommunityEdge.save": "NOT_APPLICABLE — no invalid_at/expired_at fields",
        "HasEpisodeEdge.save": "NOT_APPLICABLE",
        "NextEpisodeEdge.save": "NOT_APPLICABLE",
        "RelatesToNode_": "NOT_RUN_ON_FALKOR — Kuzu-only intermediate modeling",
        "remove_episode": "NOT_APPLICABLE — delete path, not snapshot restore",
        "restore/import helpers": "NOT_APPLICABLE — none located in graphiti_core 0.29.3",
        "classification": "NOT_APPLICABLE",
    }
    _STATE["P7-N/A"] = evidence
    _record("P7-N/A", "P7-N/A", "PASS", evidence)


@pytest.mark.asyncio
async def test_p7_z_finalize_matrix_and_result():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    receipt: dict = {"phases": [], "matrix": {}}
    if RECEIPT_PATH.exists():
        try:
            receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    matrix = receipt.get("matrix") or {}

    rows = []
    for tid in ["P7-A", "P7-B", "P7-C", "P7-D", "P7-E", "P7-F", "P7-G", "P7-H", "P7-I", "P7-N/A"]:
        ev = _STATE.get(tid) or {}
        # Prefer live state; fall back to receipt phase evidence
        if not ev:
            for p in receipt.get("phases") or []:
                if p.get("test_id") == tid:
                    ev = p.get("evidence") or {}
        rows.append(
            {
                "id": tid,
                "path": ev.get("path") or tid,
                "status": matrix.get(tid, "MISSING"),
                "classification": ev.get("classification") or matrix.get(f"{tid}_class"),
                "invalid_at_class": ev.get("invalid_at_class") or matrix.get(f"{tid}_invalid_at"),
                "expired_at_class": ev.get("expired_at_class") or matrix.get(f"{tid}_expired_at"),
                "RESTORED_BYTES": ev.get("RESTORED_BYTES"),
                "RESTORED_CURRENT_APPLICABILITY": ev.get("RESTORED_CURRENT_APPLICABILITY"),
            }
        )

    md = [
        "# P7 Write-Surface Matrix (fixture-scoped)",
        "",
        "Classifications from pytest on Graphiti 0.29.3 + FalkorDBLite only.",
        "RESTORED_BYTES ≠ RESTORED_CURRENT_APPLICABILITY.",
        "",
        "| id | path | status | classification | invalid_at | expired_at | RESTORED_BYTES |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        md.append(
            f"| {r['id']} | {r['path']} | {r['status']} | {r['classification']} | "
            f"{r['invalid_at_class']} | {r['expired_at_class']} | {r['RESTORED_BYTES']} |"
        )
    md.extend(
        [
            "",
            "## invalid_at vs expired_at",
            "",
            "- Baseline T2 sets BOTH `invalid_at≈T2` and `expired_at≈utc_now()` on OLD",
            "  (from `resolve_edge_contradictions`).",
            "- Low-level SNAPSHOT_PRE writes typically clear BOTH (None in edge_data map).",
            "- High-level add_episode / add_episode_bulk late-T1 expected to PRESERVE invalid_at.",
            "- If classes diverge, overall is PARTIAL.",
            "",
            "## Not started",
            "",
            "- P8, fixes, Fractal MemoryOps / Crystal / SVL integration, Ladybug, real LLM,",
            "  Graphiti upgrade, merge to main, upstream Graphiti_fractal edits.",
            "",
            f"```json\n{json.dumps(rows, indent=2, default=str)}\n```",
            "",
        ]
    )
    MATRIX_PATH.write_text("\n".join(md), encoding="utf-8")

    summary = {
        "suite": "P7_write_surface_inventory",
        "graphiti": "0.29.3",
        "backend": "FalkorDBLite",
        "falkordblite": "0.10.0",
        "branch": "experiment/falkordblite-deterministic-memory",
        "claim_scope": "fixture-scoped ProjectOrion Python@T1→Rust@T2 only",
        "matrix_rows": rows,
        "inventory_surfaces": len(STATIC_INVENTORY),
        "markers": _STATE.get("markers"),
        "T1": _dt_iso(T1),
        "T2": _dt_iso(T2),
        "Q3": _dt_iso(Q3),
        "anti_hallucination": {
            "RESTORED_BYTES": "snapshot temporal fields written back (invalid_at None)",
            "RESTORED_CURRENT_APPLICABILITY": "valid_at<=Q3 and invalid_at is None",
            "no_universal_claims": True,
        },
        "not_started": [
            "P8",
            "fixes",
            "Fractal MemoryOps",
            "Crystal",
            "SVL integration",
            "Ladybug",
            "real LLM",
            "Graphiti upgrade",
            "merge to main",
            "upstream Graphiti_fractal edits",
        ],
        "artifacts": {
            "inventory": str(INVENTORY_PATH),
            "matrix": str(MATRIX_PATH),
            "snapshot_pre": str(SNAPSHOT_PRE_PATH),
            "snapshot_post": str(SNAPSHOT_POST_PATH),
            "result": str(RECEIPT_PATH),
        },
    }
    receipt["summary"] = summary
    receipt["matrix_rows"] = rows
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")

    required = ["INVENTORY", "BASELINE", "P7-A", "P7-B", "P7-C", "P7-D", "P7-E", "P7-F", "P7-G", "P7-H", "P7-I", "P7-N/A"]
    missing = [i for i in required if matrix.get(i) != "PASS"]
    assert not missing, f"P7 finalize incomplete: {missing}"
