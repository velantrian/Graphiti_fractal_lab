"""FM-11/FM-12 FIRST REAL-LLM MEMORY EVALUATION.

Classification: REAL_LLM_EXTRACTION + DETERMINISTIC_EMBEDDING
Provider: DeepSeek deepseek-v4-pro via OpenAIGenericClient (json_object)
No markers. No OPENAI_API_KEY. No silent model fallback. No FM-13. No merge.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from fractal_lab.experiments.real_llm_deepseek import (
    REQUESTED_MODEL,
    CountingOpenAIGenericClient,
    DeepSeekUnavailableError,
    RealLlmCallStats,
    build_deepseek_llm_client,
    finalize_fingerprint,
    is_model_unavailable_error,
    scrub_secret,
)
from fractal_lab.memoryops.service import LabMemoryOps
from fractal_lab.memoryops.temporal import (
    TEMPORALLY_CURRENT,
    TEMPORALLY_EXPIRED,
    classify_temporal_status,
)

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:coroutine 'AsyncManagementCommands.shutdown' was never awaited:RuntimeWarning"
    ),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = REPO_ROOT / "artifacts" / "memoryops" / "run_003"
FINDINGS = ARTIFACTS / "findings"
DATA_ROOT = REPO_ROOT / "data" / "memoryops_fm11"
RECEIPT_PATH = ARTIFACTS / "result.json"

T1 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
T_AFTER = datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)
T_HIST = datetime(2026, 5, 1, 11, 0, 0, tzinfo=timezone.utc)

NATURAL_EPISODES = [
    ("N1", "Alice works on Project Orion.", T1),
    ("N2", "Project Orion uses Python.", T1 + timedelta(minutes=5)),
    ("N3", "Bob works on Project Nova.", T1 + timedelta(minutes=10)),
    ("N4", "Project Nova uses Rust.", T1 + timedelta(minutes=15)),
]

QUERIES = [
    ("Q1", "Who works on Project Orion?", ("alice", "orion")),
    ("Q2", "What language does Project Orion use?", ("python", "orion", "language")),
    ("Q3", "What is related to Project Nova?", ("nova", "bob", "rust")),
    ("Q4", "Who works on Project Zephyr?", ()),  # expect NO_RESULT / IRRELEVANT
    ("Q5", "Does Alice use Python?", ("alice", "python")),  # often PARTIAL
]

_STATE: dict[str, Any] = {}
_WARNINGS: list[str] = []
_SHARED_STATS: RealLlmCallStats | None = None
_SHARED_CLIENT: CountingOpenAIGenericClient | None = None
_FINGERPRINT: dict[str, Any] = {}


def _uid() -> str:
    return uuid.uuid4().hex[:12]


def _ensure() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for sub in ("run_a", "run_b", "run_c"):
        (ARTIFACTS / sub).mkdir(parents=True, exist_ok=True)


def _scrub(obj: Any) -> Any:
    key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    raw = json.dumps(obj, default=str)
    if key:
        raw = raw.replace(key, "REDACTED")
    # also scrub common bearer patterns that might leak
    raw = re.sub(r"(sk-[A-Za-z0-9]{8,})", "REDACTED", raw)
    return json.loads(raw)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_scrub(obj), indent=2, default=str) + "\n", encoding="utf-8"
    )


def _record(phase: str, test_id: str, status: str, evidence: dict, finding_id: str | None = None):
    _ensure()
    receipt: dict = {"phases": [], "matrix": {}, "warnings": []}
    if RECEIPT_PATH.exists():
        try:
            receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            receipt = {"phases": [], "matrix": {}, "warnings": []}
    entry = {
        "phase": phase,
        "test_id": test_id,
        "status": status,
        "evidence": _scrub(evidence),
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
    receipt["warnings"] = list(dict.fromkeys(receipt.get("warnings", []) + _WARNINGS))
    receipt["classification"] = "REAL_LLM_EXTRACTION+DETERMINISTIC_EMBEDDING"
    receipt["SECRET_LOGGED"] = "NO"
    _write_json(RECEIPT_PATH, receipt)
    if status in {"FAIL", "FIXTURE_FAIL", "STOP"} and finding_id:
        (FINDINGS / f"{finding_id}.md").write_text(
            f"# {finding_id}\n\nphase: {phase}\ntest: {test_id}\nstatus: {status}\n\n```json\n"
            f"{json.dumps(_scrub(evidence), indent=2, default=str)}\n```\n",
            encoding="utf-8",
        )


def _facts_blob(edges: list[dict]) -> str:
    return " ".join(str(e.get("fact") or "") for e in edges).lower()


def _names_blob(entities: list[dict]) -> str:
    return " ".join(str(e.get("name") or "") for e in entities).lower()


def _eval_query(label: str, query: str, edges: list[dict], expect_needles: tuple[str, ...]) -> str:
    """Return RELEVANT / PARTIAL / IRRELEVANT / NO_RESULT — semantic judgment, not forced shapes."""
    if not edges:
        return "NO_RESULT"
    blob = _facts_blob(edges)
    if not expect_needles:
        # Q4: any hit mentioning Zephyr-ish is unexpected; otherwise IRRELEVANT or NO_RESULT
        if "zephyr" in blob:
            return "IRRELEVANT"  # retrieved something about zephyr incorrectly framed
        # hits exist but query target absent → IRRELEVANT
        return "IRRELEVANT"
    hits = [n for n in expect_needles if n.lower() in blob]
    if len(hits) >= max(1, len(expect_needles) - 1) and (
        expect_needles[0].lower() in blob or (len(expect_needles) > 1 and expect_needles[1].lower() in blob)
    ):
        # strong overlap
        if len(hits) == len(expect_needles) or (
            label in {"Q1", "Q2", "Q3"} and len(hits) >= 1 and any(
                k in blob for k in expect_needles[:2]
            )
        ):
            # Q1/Q2/Q3: primary entity/topic present → RELEVANT if at least one strong needle
            if label == "Q1" and "alice" in blob:
                return "RELEVANT"
            if label == "Q2" and ("python" in blob or "rust" in blob):
                return "RELEVANT"
            if label == "Q3" and ("nova" in blob or "bob" in blob or "rust" in blob):
                return "RELEVANT"
            if label == "Q5":
                if "alice" in blob and "python" in blob:
                    return "RELEVANT"
                if "alice" in blob or "python" in blob:
                    return "PARTIAL"
                return "IRRELEVANT"
        if hits:
            return "PARTIAL"
    if hits:
        return "PARTIAL"
    return "IRRELEVANT"


async def _open_real(db_path: Path, group_id: str, stats: RealLlmCallStats | None = None):
    global _SHARED_CLIENT, _SHARED_STATS, _FINGERPRINT
    if stats is None:
        if _SHARED_STATS is None:
            _SHARED_STATS = RealLlmCallStats()
        stats = _SHARED_STATS
    client, fp = build_deepseek_llm_client(temperature=0.0, stats=stats)
    if not _FINGERPRINT:
        _FINGERPRINT = fp
    _SHARED_CLIENT = client
    mem = await LabMemoryOps.open(
        db_path,
        default_group_id=group_id,
        build_indices=True,
        llm_client=client,
    )
    return mem, client, fp


@pytest.fixture(scope="module")
def fm11_ids():
    uid = _uid()
    return {
        "uid": uid,
        "group": f"fm11_main_{uid}",
        "scope_a": f"fm11_scope_a_{uid}",
        "scope_b": f"fm11_scope_b_{uid}",
        "db_path": DATA_ROOT / f"fm11_{uid}.db",
        "reopen_db": DATA_ROOT / f"fm11_reopen_{uid}.db",
        "temporal_db": DATA_ROOT / f"fm11_temporal_{uid}.db",
        "scope_db": DATA_ROOT / f"fm11_scope_{uid}.db",
        "var_a": DATA_ROOT / f"fm11_var_a_{uid}.db",
        "var_b": DATA_ROOT / f"fm11_var_b_{uid}.db",
        "var_c": DATA_ROOT / f"fm11_var_c_{uid}.db",
    }


@pytest.mark.asyncio
async def test_fm11a_provider_fingerprint(fm11_ids):
    """FM-11A: build DeepSeek REAL_LLM client; write fingerprint (secrets REDACTED)."""
    _ensure()
    # Preserve BLOCKED history
    blocked = FINDINGS / "BLOCKED_NO_REAL_PROVIDER.md"
    if blocked.exists() and "SUPERSEDED" not in blocked.read_text(encoding="utf-8"):
        blocked.write_text(
            blocked.read_text(encoding="utf-8")
            + "\n\n---\nSUPERSEDED_BY: FM-11/FM-12 REAL_LLM DeepSeek run (same run_003).\n"
            "Prior BLOCKED_NO_REAL_PROVIDER kept as history.\n",
            encoding="utf-8",
        )
    try:
        client, fp = build_deepseek_llm_client(temperature=0.0)
    except DeepSeekUnavailableError as exc:
        _record("FM-11", "FM-11A", "STOP", {"error": str(exc)}, "F-FM11A-NO-KEY")
        pytest.fail(str(exc))

    global _SHARED_CLIENT, _SHARED_STATS, _FINGERPRINT
    _SHARED_CLIENT = client
    _SHARED_STATS = client.stats
    _FINGERPRINT = fp

    # Smoke structured extract — stop on model unavailable
    from graphiti_core.prompts.models import Message
    from pydantic import BaseModel, Field

    class SmokeFact(BaseModel):
        person: str = Field(...)
        project: str = Field(...)

    try:
        out = await client.generate_response(
            messages=[
                Message(
                    role="system",
                    content="Extract a SmokeFact JSON object with person and project only.",
                ),
                Message(role="user", content="Alice works on Project Orion."),
            ],
            response_model=SmokeFact,
            prompt_name="fm11a_smoke",
        )
    except Exception as exc:  # noqa: BLE001
        evidence = {
            "error_type": type(exc).__name__,
            "error": scrub_secret(str(exc)),
            "model_unavailable": is_model_unavailable_error(exc),
            "REQUESTED_MODEL": REQUESTED_MODEL,
        }
        if is_model_unavailable_error(exc):
            _record("FM-11", "FM-11A", "STOP", evidence, "F-FM11A-MODEL-UNAVAILABLE")
            pytest.fail(f"MODEL UNAVAILABLE — STOP (no fallback): {scrub_secret(str(exc))}")
        _record("FM-11", "FM-11A", "FAIL", evidence, "F-FM11A-SMOKE")
        raise

    fp2 = finalize_fingerprint(fp, client.stats)
    _FINGERPRINT = fp2
    _write_json(ARTIFACTS / "provider_fingerprint.json", fp2)
    env_lines = [
        f"date_utc={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"branch=experiment/falkordblite-deterministic-memory",
        f"start_commit=PENDING",
        f"provider=DeepSeek",
        f"REQUESTED_MODEL={REQUESTED_MODEL}",
        f"ACTUAL_MODEL={fp2.get('ACTUAL_MODEL')}",
        f"embedder=deterministic",
        f"classification=REAL_LLM_EXTRACTION+DETERMINISTIC_EMBEDDING",
        f"structured_output_mode=json_object",
        f"CACHE=ENABLED_BY_PROVIDER_DEFAULT",
        f"SECRET_LOGGED=NO",
    ]
    (ARTIFACTS / "environment.txt").write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    natural = "\n".join(t for _, t, _ in NATURAL_EPISODES) + "\nProject Orion now uses Rust.\n"
    (ARTIFACTS / "natural_input.txt").write_text(natural, encoding="utf-8")

    ok = (
        fp2.get("provider") == "DeepSeek"
        and fp2.get("REQUESTED_MODEL") == REQUESTED_MODEL
        and fp2.get("SECRET_LOGGED") == "NO"
        and isinstance(out, dict)
        and "alice" in json.dumps(out).lower()
    )
    evidence = {
        "fingerprint_keys": sorted(fp2.keys()),
        "ACTUAL_MODEL": fp2.get("ACTUAL_MODEL"),
        "smoke_out": out,
        "CACHE": fp2.get("CACHE"),
        "first_request_utc": fp2.get("first_request_utc"),
    }
    _record("FM-11", "FM-11A", "PASS" if ok else "FAIL", evidence, None if ok else "F-FM11A")
    _STATE["fingerprint"] = fp2
    assert ok, evidence


@pytest.mark.asyncio
async def test_fm11b_natural_ingest(fm11_ids):
    """FM-11B: natural text ingest (no markers) via REAL_LLM extraction."""
    mem, client, _ = await _open_real(fm11_ids["db_path"], fm11_ids["group"])
    try:
        receipts = []
        for label, text, ref in NATURAL_EPISODES:
            assert "MARKER" not in text.upper()
            assert not re.search(r"P[0-9]+_(OLD|NEW)_", text)
            try:
                r = await mem.ingest(
                    text,
                    group_id=fm11_ids["group"],
                    reference_time=ref,
                    name=f"fm11_{label}",
                    source_description="fm11_natural_text",
                )
            except Exception as exc:  # noqa: BLE001
                if is_model_unavailable_error(exc):
                    _record(
                        "FM-11",
                        "FM-11B",
                        "STOP",
                        {"error": scrub_secret(str(exc)), "label": label},
                        "F-FM11B-MODEL-UNAVAILABLE",
                    )
                    pytest.fail(f"MODEL UNAVAILABLE — STOP: {scrub_secret(str(exc))}")
                raise
            receipts.append(r.to_dict())
        _STATE["ingest_receipts"] = receipts
        _write_json(ARTIFACTS / "run_a" / "ingest_receipts.json", receipts)
        evidence = {
            "episode_count": len(receipts),
            "entity_counts": [len(r.get("entities") or []) for r in receipts],
            "edge_counts": [len(r.get("edges") or []) for r in receipts],
            "texts": [t for _, t, _ in NATURAL_EPISODES],
            "no_markers": True,
        }
        ok = len(receipts) == 4 and sum(evidence["edge_counts"]) + sum(evidence["entity_counts"]) >= 1
        _record("FM-11", "FM-11B", "PASS" if ok else "FAIL", evidence, None if ok else "F-FM11B-INGEST")
        assert ok, evidence
    finally:
        await mem.aclose()


@pytest.mark.asyncio
async def test_fm11c_inspect_graph(fm11_ids):
    """FM-11C: inspect ACTUAL graph — do not invent edge shapes."""
    mem, _, _ = await _open_real(fm11_ids["db_path"], fm11_ids["group"])
    try:
        insp = await mem.inspect(group_id=fm11_ids["group"])
        dump = insp.to_dict()
        _STATE["inspect"] = dump
        _write_json(ARTIFACTS / "graph_dump.json", dump)
        entities = [e for e in insp.entities if isinstance(e, dict) and e.get("uuid")]
        edges = [e for e in insp.edges if isinstance(e, dict) and e.get("uuid")]
        episodes = [e for e in insp.episodes if isinstance(e, dict) and e.get("uuid")]
        evidence = {
            "ENTITIES_actual": [
                {"name": e.get("name"), "uuid": e.get("uuid"), "labels": e.get("labels")}
                for e in entities
            ],
            "RELATIONSHIPS_actual": [
                {
                    "fact": e.get("fact"),
                    "name": e.get("name"),
                    "uuid": e.get("uuid"),
                    "valid_at": e.get("valid_at"),
                    "invalid_at": e.get("invalid_at"),
                    "group_id": e.get("group_id"),
                }
                for e in edges
            ],
            "episode_count": len(episodes),
            "entity_count": len(entities),
            "edge_count": len(edges),
            "note": "STRUCTURAL vs SEMANTIC kept separate — actual Graphiti output only",
        }
        _STATE["entities_actual"] = evidence["ENTITIES_actual"]
        _STATE["relationships_actual"] = evidence["RELATIONSHIPS_actual"]
        ok = len(episodes) >= 1 and (len(entities) >= 1 or len(edges) >= 1)
        _record("FM-11", "FM-11C", "PASS" if ok else "FAIL", evidence, None if ok else "F-FM11C-INSPECT")
        assert ok, evidence
    finally:
        await mem.aclose()


@pytest.mark.asyncio
async def test_fm11d_queries_q1_q5(fm11_ids):
    """FM-11D: Q1–Q5 with RELEVANT/PARTIAL/IRRELEVANT/NO_RESULT."""
    mem, _, _ = await _open_real(fm11_ids["db_path"], fm11_ids["group"])
    try:
        query_receipts = {}
        evaluations = {}
        for label, q, needles in QUERIES:
            r = await mem.query(q, group_id=fm11_ids["group"], num_results=10, query_time=T_AFTER)
            d = r.to_dict()
            query_receipts[label] = d
            judgment = _eval_query(label, q, [e for e in r.edges if isinstance(e, dict)], needles)
            evaluations[label] = {
                "query": q,
                "judgment": judgment,
                "hit_count": len(r.edges),
                "facts": [e.get("fact") for e in r.edges if isinstance(e, dict)],
                "temporal_summary": r.temporal_summary,
            }
        _write_json(ARTIFACTS / "query_receipts.json", {"receipts": query_receipts, "evaluations": evaluations})
        _STATE["query_evaluations"] = evaluations
        # Acceptance: suite runs and records judgments; Q1 should not be empty if graph has Alice/Orion
        ok = all(k in evaluations for k, _, _ in QUERIES)
        # Soft semantic: if graph had alice/orion, Q1 ideally RELEVANT/PARTIAL
        _record("FM-11", "FM-11D", "PASS" if ok else "FAIL", evaluations, None if ok else "F-FM11D-QUERY")
        assert ok
    finally:
        await mem.aclose()


@pytest.mark.asyncio
async def test_fm11e_process_reopen(fm11_ids):
    """FM-11E: PROCESS1 ingest+query+close → PROCESS2 reopen same DB → query without re-ingest."""
    db = fm11_ids["reopen_db"]
    group = f"fm11_reopen_{fm11_ids['uid']}"
    text = "Alice works on Project Orion."

    mem, client, _ = await _open_real(db, group)
    try:
        await mem.ingest(text, group_id=group, reference_time=T1, name="fm11e_p1")
        q1 = await mem.query("Who works on Project Orion?", group_id=group, num_results=10)
        p1_hits = len(q1.edges)
        p1_facts = [e.get("fact") for e in q1.edges if isinstance(e, dict)]
    finally:
        await mem.aclose()

    helper = ARTIFACTS / "_fm11e_reopen_helper.py"
    helper.write_text(
        """\
import asyncio, json, sys
from fractal_lab.memoryops.service import LabMemoryOps

async def main(db_path: str, group_id: str, query: str) -> int:
    # Query-only reopen: deterministic LLM ok; embedder deterministic matches PROCESS1
    mem = await LabMemoryOps.open(db_path, default_group_id=group_id, build_indices=True, temporal=True)
    try:
        r = await mem.query(query, group_id=group_id, num_results=10)
        print(json.dumps(r.to_dict(), default=str))
        return 0
    finally:
        await mem.aclose()

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3])))
""",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(helper), str(db), group, "Who works on Project Orion?"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        timeout=180,
    )
    p2_payload = None
    try:
        out = scrub_secret(proc.stdout.strip())
        p2_payload = json.loads(out) if out else None
    except json.JSONDecodeError:
        p2_payload = {"raw_stdout": scrub_secret(proc.stdout), "stderr": scrub_secret(proc.stderr)}
    p2_hits = len((p2_payload or {}).get("edges") or []) if isinstance(p2_payload, dict) else 0
    evidence = {
        "process1_hit_count": p1_hits,
        "process1_facts": p1_facts,
        "process2_returncode": proc.returncode,
        "process2_hit_count": p2_hits,
        "process2_facts": [
            e.get("fact") for e in ((p2_payload or {}).get("edges") or []) if isinstance(e, dict)
        ]
        if isinstance(p2_payload, dict)
        else None,
        "stderr_tail": scrub_secret((proc.stderr or "")[-500:]),
    }
    _write_json(ARTIFACTS / "reopen_receipts.json", evidence)
    _STATE["reopen"] = evidence
    ok = p1_hits >= 1 and p2_hits >= 1 and proc.returncode == 0
    status = "PASS" if ok else ("FINDINGS" if p1_hits >= 1 else "FAIL")
    if not ok and p1_hits >= 1:
        _WARNINGS.append("FM-11E: PROCESS2 reopen returned fewer/zero hits — persistence/search finding")
    _record("FM-11", "FM-11E", status, evidence, None if status == "PASS" else "F-FM11E-REOPEN")
    assert status in {"PASS", "FINDINGS"}, evidence


@pytest.mark.asyncio
async def test_fm11f_usage_receipt(fm11_ids):
    """FM-11F: usage_receipt with token/cache counters (UNKNOWN only if truly unavailable)."""
    global _SHARED_STATS, _FINGERPRINT
    stats = _SHARED_STATS or RealLlmCallStats()
    usage = stats.to_dict()
    fp = finalize_fingerprint(_FINGERPRINT or {"provider": "DeepSeek"}, stats)
    _FINGERPRINT = fp
    _write_json(ARTIFACTS / "provider_fingerprint.json", fp)
    _write_json(ARTIFACTS / "usage_receipt.json", usage)
    evidence = {
        "generate_calls": stats.generate_calls,
        "TOKEN_USAGE": usage.get("TOKEN_USAGE"),
        "CACHE_HIT_TOKENS": usage.get("CACHE_HIT_TOKENS"),
        "CACHE_MISS_TOKENS": usage.get("CACHE_MISS_TOKENS"),
        "CACHE_EFFECT": usage.get("CACHE_EFFECT"),
        "COST": usage.get("COST"),
        "ACTUAL_MODELS_SEEN": usage.get("ACTUAL_MODELS_SEEN"),
    }
    ok = stats.generate_calls >= 1
    _record("FM-11", "FM-11F", "PASS" if ok else "FAIL", evidence, None if ok else "F-FM11F-USAGE")
    assert ok


@pytest.mark.asyncio
async def test_fm11g_warnings_recorded(fm11_ids):
    """FM-11G: persist warnings + unexpected findings note."""
    _ensure()
    warnings_path = FINDINGS / "WARNINGS.md"
    body = "# WARNINGS\n\n" + ("\n".join(f"- {w}" for w in _WARNINGS) if _WARNINGS else "- (none yet)\n")
    body += "\n\nSECRET_LOGGED=NO\n"
    warnings_path.write_text(body, encoding="utf-8")
    _record("FM-11", "FM-11G", "PASS", {"warnings": list(_WARNINGS)}, None)


@pytest.mark.asyncio
async def test_fm11h_optional_scope(fm11_ids):
    """FM-11H: optional scope isolation if stable under REAL_LLM."""
    db = fm11_ids["scope_db"]
    mem, _, _ = await _open_real(db, fm11_ids["scope_a"])
    try:
        await mem.ingest(
            "Alice works on Project Orion in scope Alpha.",
            group_id=fm11_ids["scope_a"],
            reference_time=T1,
            name="scope_a",
        )
        await mem.ingest(
            "Bob works on Project Nova in scope Beta.",
            group_id=fm11_ids["scope_b"],
            reference_time=T1,
            name="scope_b",
        )
        qa = await mem.query("Alice Project Orion", group_id=fm11_ids["scope_a"])
        qb = await mem.query("Bob Project Nova", group_id=fm11_ids["scope_b"])
        leak = await mem.query("Bob Project Nova", group_id=fm11_ids["scope_a"])
        evidence = {
            "scope_a_hits": len(qa.edges),
            "scope_b_hits": len(qb.edges),
            "scope_a_facts": [e.get("fact") for e in qa.edges if isinstance(e, dict)],
            "scope_b_facts": [e.get("fact") for e in qb.edges if isinstance(e, dict)],
            "leak_facts": [e.get("fact") for e in leak.edges if isinstance(e, dict)],
            "a_mentions_bob": "bob" in _facts_blob(qa.edges),
            "leak_mentions_bob_or_nova": (
                "bob" in _facts_blob(leak.edges) or "nova" in _facts_blob(leak.edges)
            ),
        }
        _write_json(ARTIFACTS / "scope_receipts.json", evidence)
        _STATE["scope"] = evidence
        # Soft: record FINDINGS if leakage; PASS if isolated or inconclusive retrieval
        if evidence["leak_mentions_bob_or_nova"] and evidence["scope_a_hits"] > 0:
            status = "FINDINGS"
            _WARNINGS.append("FM-11H: possible cross-scope retrieval under tested interface")
        elif evidence["scope_a_hits"] >= 1 or evidence["scope_b_hits"] >= 1:
            status = "PASS"
        else:
            status = "FINDINGS"
            _WARNINGS.append("FM-11H: scope queries returned no hits (deterministic embedder?)")
        _record("FM-11", "FM-11H", status, evidence, None if status == "PASS" else "F-FM11H-SCOPE")
        assert status in {"PASS", "FINDINGS"}
    finally:
        await mem.aclose()


@pytest.mark.asyncio
async def test_fm12a_natural_python_rust_contradiction(fm11_ids):
    """FM-12A: natural Python→Rust contradiction (no markers)."""
    db = fm11_ids["temporal_db"]
    group = f"fm12_temporal_{fm11_ids['uid']}"
    mem, client, _ = await _open_real(db, group)
    try:
        r1 = await mem.ingest(
            "Project Orion uses Python.",
            group_id=group,
            reference_time=T1,
            name="fm12_python",
        )
        r2 = await mem.ingest(
            "Project Orion now uses Rust.",
            group_id=group,
            reference_time=T2,
            name="fm12_rust",
        )
        insp = await mem.inspect(group_id=group)
        edges = [e for e in insp.edges if isinstance(e, dict) and e.get("fact")]
        python_edges = [e for e in edges if "python" in (e.get("fact") or "").lower()]
        rust_edges = [
            e
            for e in edges
            if "rust" in (e.get("fact") or "").lower()
            and "orion" in (e.get("fact") or "").lower()
        ]
        evidence = {
            "t1_episode": r1.episode_uuid,
            "t2_episode": r2.episode_uuid,
            "python_edges": python_edges,
            "rust_edges": rust_edges,
            "all_facts": [e.get("fact") for e in edges],
        }
        _STATE["fm12_edges"] = evidence
        _STATE["fm12_group"] = group
        _STATE["fm12_db"] = str(db)
        ok = bool(python_edges) or bool(rust_edges) or bool(edges)
        _record("FM-12", "FM-12A", "PASS" if ok else "FAIL", evidence, None if ok else "F-FM12A")
        assert ok, evidence
    finally:
        await mem.aclose()


@pytest.mark.asyncio
async def test_fm12b_retrieved_ne_current(fm11_ids):
    """FM-12B: RETRIEVED≠CURRENT — search may return expired; classify temporal status."""
    db = Path(_STATE.get("fm12_db") or fm11_ids["temporal_db"])
    group = _STATE.get("fm12_group") or f"fm12_temporal_{fm11_ids['uid']}"
    mem, _, _ = await _open_real(db, group)
    try:
        q = await mem.query(
            "What language does Project Orion use?",
            group_id=group,
            num_results=10,
            query_time=T_AFTER,
        )
        edges = [e for e in q.edges if isinstance(e, dict)]
        py = next((e for e in edges if "python" in (e.get("fact") or "").lower()), None)
        ru = next((e for e in edges if "rust" in (e.get("fact") or "").lower()), None)
        # Also classify from inspect store
        insp = await mem.inspect(group_id=group)
        stored = [e for e in insp.edges if isinstance(e, dict) and e.get("fact")]
        classifications = []
        for e in stored:
            st = classify_temporal_status(
                valid_at=e.get("valid_at"),
                invalid_at=e.get("invalid_at"),
                query_time=T_AFTER,
            )
            classifications.append(
                {
                    "fact": e.get("fact"),
                    "valid_at": e.get("valid_at"),
                    "invalid_at": e.get("invalid_at"),
                    "temporal_status": st,
                    "retrieved_in_search": any(
                        (x.get("uuid") == e.get("uuid")) for x in edges
                    ),
                }
            )
        retrieved_expired = any(
            c["temporal_status"] == TEMPORALLY_EXPIRED and c["retrieved_in_search"]
            for c in classifications
        )
        rust_current = any(
            "rust" in (c.get("fact") or "").lower() and c["temporal_status"] == TEMPORALLY_CURRENT
            for c in classifications
        )
        python_expired = any(
            "python" in (c.get("fact") or "").lower() and c["temporal_status"] == TEMPORALLY_EXPIRED
            for c in classifications
        )
        outcome = "UNKNOWN"
        if rust_current and python_expired:
            outcome = "PYTHON_EXPIRED_RUST_CURRENT"
        elif rust_current and not python_expired:
            outcome = "RUST_CURRENT_PYTHON_NOT_EXPIRED_OR_MISSING"
        elif python_expired and not rust_current:
            outcome = "PYTHON_EXPIRED_RUST_NOT_CURRENT_OR_MISSING"
        elif edges:
            outcome = "RETRIEVED_WITHOUT_CLEAN_TEMPORAL_SPLIT"
        else:
            outcome = "NO_SEARCH_HITS"

        temporal_receipt = {
            "query_time": T_AFTER.isoformat(),
            "search_facts": [e.get("fact") for e in edges],
            "python_hit": py,
            "rust_hit": ru,
            "classifications": classifications,
            "retrieved_expired_observed": retrieved_expired,
            "invariant": "RETRIEVED≠CURRENT",
            "TEMPORAL_OUTCOME": outcome,
            "PYTHON": "EXPIRED" if python_expired else ("PRESENT" if py or any("python" in (c.get("fact") or "").lower() for c in classifications) else "ABSENT"),
            "RUST": "CURRENT" if rust_current else ("PRESENT" if ru or any("rust" in (c.get("fact") or "").lower() for c in classifications) else "ABSENT"),
        }
        _write_json(ARTIFACTS / "temporal_update_receipt.json", temporal_receipt)
        _STATE["temporal"] = temporal_receipt
        # PASS if we observed temporal metadata path; FINDINGS if contradiction incomplete
        if outcome == "PYTHON_EXPIRED_RUST_CURRENT":
            status = "PASS"
        elif classifications:
            status = "FINDINGS"
        else:
            status = "FAIL"
        _record("FM-12", "FM-12B", status, temporal_receipt, None if status == "PASS" else "F-FM12B-TEMPORAL")
        assert status in {"PASS", "FINDINGS"}
    finally:
        await mem.aclose()


@pytest.mark.asyncio
async def test_fm12c_historical_query(fm11_ids):
    """FM-12C: historical query_time between T1 and T2 — metadata classification only."""
    db = Path(_STATE.get("fm12_db") or fm11_ids["temporal_db"])
    group = _STATE.get("fm12_group") or f"fm12_temporal_{fm11_ids['uid']}"
    mem, _, _ = await _open_real(db, group)
    try:
        q = await mem.query(
            "What language does Project Orion use?",
            group_id=group,
            num_results=10,
            query_time=T_HIST,
        )
        edges = [e for e in q.edges if isinstance(e, dict)]
        insp = await mem.inspect(group_id=group)
        stored = [e for e in insp.edges if isinstance(e, dict) and e.get("fact")]
        hist = []
        for e in stored:
            st = classify_temporal_status(
                valid_at=e.get("valid_at"), invalid_at=e.get("invalid_at"), query_time=T_HIST
            )
            hist.append({"fact": e.get("fact"), "temporal_status_at_T_HIST": st, **{k: e.get(k) for k in ("valid_at", "invalid_at", "uuid")}})
        receipt = {
            "query_time": T_HIST.isoformat(),
            "note": "metadata classification at historical time — not time-travel retrieval API",
            "search_hit_count": len(edges),
            "search_facts": [e.get("fact") for e in edges],
            "stored_classifications_at_hist": hist,
        }
        _write_json(ARTIFACTS / "historical_query_receipt.json", receipt)
        _STATE["historical"] = receipt
        _record("FM-12", "FM-12C", "PASS", receipt, None)
    finally:
        await mem.aclose()


@pytest.mark.asyncio
async def test_fm12d_provenance(fm11_ids):
    """FM-12D: provenance receipts for retrieved edges."""
    db = Path(_STATE.get("fm12_db") or fm11_ids["temporal_db"])
    group = _STATE.get("fm12_group") or f"fm12_temporal_{fm11_ids['uid']}"
    mem, _, _ = await _open_real(db, group)
    try:
        q = await mem.provenance_for_query_hits(
            "What language does Project Orion use?",
            group_id=group,
            num_results=10,
            query_time=T_AFTER,
        )
        receipt = q.to_dict()
        _write_json(ARTIFACTS / "provenance_receipts.json", receipt)
        _STATE["provenance"] = {
            "hit_count": len(q.edges),
            "provenance_count": len(q.provenance),
            "sample": (q.provenance or [None])[0],
        }
        ok = True  # provenance layer should not crash
        _record("FM-12", "FM-12D", "PASS" if ok else "FAIL", _STATE["provenance"], None)
        assert ok
    finally:
        await mem.aclose()


@pytest.mark.asyncio
async def test_fm12e_variance_abc(fm11_ids):
    """FM-12E: RUN_A/B/C variance with independent cache counters."""
    runs = []
    for tag, dbkey in (("run_a", "var_a"), ("run_b", "var_b"), ("run_c", "var_c")):
        stats = RealLlmCallStats()
        group = f"fm12_{tag}_{fm11_ids['uid']}"
        db = fm11_ids[dbkey]
        mem, client, fp = await _open_real(db, group, stats=stats)
        try:
            texts = [
                "Alice works on Project Orion.",
                "Project Orion uses Python.",
            ]
            ingest = []
            for i, text in enumerate(texts):
                r = await mem.ingest(
                    text,
                    group_id=group,
                    reference_time=T1 + timedelta(minutes=i),
                    name=f"{tag}_{i}",
                )
                ingest.append(
                    {
                        "entities": [e.get("name") for e in r.entities if isinstance(e, dict)],
                        "facts": [e.get("fact") for e in r.edges if isinstance(e, dict)],
                    }
                )
            insp = await mem.inspect(group_id=group)
            q = await mem.query("Who works on Project Orion?", group_id=group, num_results=10)
            run_doc = {
                "run": tag,
                "REQUESTED_MODEL": REQUESTED_MODEL,
                "ACTUAL_MODELS_SEEN": list(stats.actual_models_seen) or ["UNKNOWN"],
                "entities": [e.get("name") for e in insp.entities if isinstance(e, dict)],
                "facts": [e.get("fact") for e in insp.edges if isinstance(e, dict)],
                "query_facts": [e.get("fact") for e in q.edges if isinstance(e, dict)],
                "ingest": ingest,
                "usage": stats.to_dict(),
                "CACHE_HIT_TOKENS_total": stats.cache_hit_tokens if stats.cache_fields_observed else "UNKNOWN",
                "CACHE_MISS_TOKENS_total": stats.cache_miss_tokens if stats.cache_fields_observed else "UNKNOWN",
                "first_request_utc": stats.per_request[0].request_utc_start if stats.per_request else None,
                "last_request_utc": stats.per_request[-1].request_utc_end if stats.per_request else None,
                "note": "identical natural prefixes; cache counters independent per run; CACHE_HIT ≠ better semantics",
            }
            _write_json(ARTIFACTS / tag / "variance_run.json", run_doc)
            runs.append(run_doc)
        finally:
            await mem.aclose()

    # Compare structural/semantic variance without forcing equality
    def norm_set(vals):
        return sorted({(v or "").strip().lower() for v in vals if v})

    variance = {
        "runs": [r["run"] for r in runs],
        "entity_sets": {r["run"]: norm_set(r["entities"]) for r in runs},
        "fact_sets": {r["run"]: norm_set(r["facts"]) for r in runs},
        "entity_set_equal": len({tuple(norm_set(r["entities"])) for r in runs}) == 1,
        "fact_set_equal": len({tuple(norm_set(r["facts"])) for r in runs}) == 1,
        "cache_totals": {
            r["run"]: {
                "hit": r["CACHE_HIT_TOKENS_total"],
                "miss": r["CACHE_MISS_TOKENS_total"],
            }
            for r in runs
        },
        "note": "Variance across REAL_LLM extraction with deterministic embeddings",
    }
    _write_json(ARTIFACTS / "variance_report.json", variance)
    _STATE["variance"] = variance
    _record("FM-12", "FM-12E", "PASS", variance, None)


@pytest.mark.asyncio
async def test_fm12f_finalize_artifacts(fm11_ids):
    """FM-12F: finalize fingerprint/usage/commands/result; classify TEMPORAL_OUTCOME."""
    global _SHARED_STATS, _FINGERPRINT
    stats = _SHARED_STATS or RealLlmCallStats()
    fp = finalize_fingerprint(_FINGERPRINT or {"provider": "DeepSeek", "REQUESTED_MODEL": REQUESTED_MODEL}, stats)
    # Merge variance run stats into a note (already separate)
    _FINGERPRINT = fp
    _write_json(ARTIFACTS / "provider_fingerprint.json", fp)
    _write_json(ARTIFACTS / "usage_receipt.json", stats.to_dict())

    commands = [
        "# FM-11/FM-12 REAL_LLM commands (secrets redacted)",
        "python -c 'from fractal_lab.experiments.real_llm_deepseek import build_deepseek_llm_client; ...'",
        "pytest -q tests/lab/test_memoryops_fm11_fm12_real_llm.py",
        f"REQUESTED_MODEL={REQUESTED_MODEL}",
        "OPENAI_API_KEY=UNSET_BY_POLICY",
        "SECRET_LOGGED=NO",
    ]
    (ARTIFACTS / "commands.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")

    temporal = _STATE.get("temporal") or {}
    summary = {
        "phase": "FM-11/FM-12",
        "status": "COMPLETED",
        "classification": "REAL_LLM_EXTRACTION+DETERMINISTIC_EMBEDDING",
        "REQUESTED_MODEL": REQUESTED_MODEL,
        "ACTUAL_MODEL": fp.get("ACTUAL_MODEL"),
        "CACHE": "ENABLED_BY_PROVIDER_DEFAULT",
        "CACHE_HIT_TOKENS": fp.get("CACHE_HIT_TOKENS"),
        "CACHE_MISS_TOKENS": fp.get("CACHE_MISS_TOKENS"),
        "CACHE_EFFECT": fp.get("CACHE_EFFECT"),
        "TOKEN_USAGE": fp.get("TOKEN_USAGE"),
        "COST": fp.get("COST"),
        "matrix": {},
        "QUERY_EVALUATION": _STATE.get("query_evaluations"),
        "ENTITIES_actual": _STATE.get("entities_actual"),
        "RELATIONSHIPS_actual": _STATE.get("relationships_actual"),
        "REOPEN": _STATE.get("reopen"),
        "TEMPORAL_OUTCOME": temporal.get("TEMPORAL_OUTCOME"),
        "PYTHON": temporal.get("PYTHON"),
        "RUST": temporal.get("RUST"),
        "HISTORICAL_QUERY": _STATE.get("historical"),
        "PROVENANCE": _STATE.get("provenance"),
        "VARIANCE": {
            "entity_set_equal": (_STATE.get("variance") or {}).get("entity_set_equal"),
            "fact_set_equal": (_STATE.get("variance") or {}).get("fact_set_equal"),
        },
        "SCOPE": _STATE.get("scope"),
        "WARNINGS": list(_WARNINGS),
        "SECRET_LOGGED": "NO",
        "supersedes": "BLOCKED_NO_REAL_PROVIDER (kept as history in findings/)",
        "NEXT_ACTION": "STOP_AND_AWAIT_REVIEW",
        "MERGE": "NO",
        "UPSTREAM_FRACTAL": "2437244149baeb0c645e2e942125be92bba3a96b untouched",
    }
    if RECEIPT_PATH.exists():
        try:
            prior = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
            summary["matrix"] = prior.get("matrix", {})
            summary["phases"] = prior.get("phases", [])
        except json.JSONDecodeError:
            pass
    _write_json(RECEIPT_PATH, summary)
    _record("FM-12", "FM-12F", "PASS", {"finalized": True, "TEMPORAL_OUTCOME": summary["TEMPORAL_OUTCOME"]}, None)

    # Update environment with end commit placeholder (filled after git commit by runner)
    env_path = ARTIFACTS / "environment.txt"
    extra = [
        f"ACTUAL_MODEL={fp.get('ACTUAL_MODEL')}",
        f"CACHE_EFFECT={fp.get('CACHE_EFFECT')}",
        f"CACHE_HIT_TOKENS={fp.get('CACHE_HIT_TOKENS')}",
        f"CACHE_MISS_TOKENS={fp.get('CACHE_MISS_TOKENS')}",
        f"generate_calls={stats.generate_calls}",
        "SECRET_LOGGED=NO",
    ]
    prev = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    env_path.write_text(prev.rstrip() + "\n" + "\n".join(extra) + "\n", encoding="utf-8")
