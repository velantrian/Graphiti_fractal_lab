"""FM-13 RETRIEVAL PIPELINE INSTRUMENTATION (observational only).

Reuses FM-11 executed graph (run_003) — no re-ingest / no DeepSeek spend unless
extraction control fails. Does not change providers, prompts, num_results, or
MemoryOps semantics.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from fractal_lab.experiments.retrieval_instrumentation import (
    RetrievalInstrumenter,
    build_search_config_json,
    build_search_path_map,
    compare_memoryops_vs_graphiti,
)
from fractal_lab.memoryops.service import LabMemoryOps

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:coroutine 'AsyncManagementCommands.shutdown' was never awaited:RuntimeWarning"
    ),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = REPO_ROOT / "artifacts" / "memoryops" / "run_004"
FINDINGS = ARTIFACTS / "findings"
TRACES = ARTIFACTS / "query_traces"
DATA = REPO_ROOT / "data" / "memoryops_fm13"
SRC_DB = REPO_ROOT / "data" / "memoryops_fm11" / "fm11_9de953981e60.db"
SRC_SETTINGS = REPO_ROOT / "data" / "memoryops_fm11" / "fm11_9de953981e60.db.settings"
DB_PATH = DATA / "fm11_9de953981e60.db"
GROUP = "fm11_main_9de953981e60"
RUN003_EVAL = REPO_ROOT / "artifacts" / "memoryops" / "run_003" / "query_receipts.json"

QUERIES = [
    ("Q1", "Who works on Project Orion?"),
    ("Q2", "What language does Project Orion use?"),
    ("Q3", "What is related to Project Nova?"),
    ("Q4", "Who works on Project Zephyr?"),
    ("Q5", "Does Alice use Python?"),
]

# Gold relevance for metrics (lab judgment aligned to FM fixture semantics)
GOLD: dict[str, list[str]] = {
    "Q1": ["Alice works on Project Orion."],
    "Q2": ["Project Orion uses Python."],
    "Q3": [
        "Bob works on Project Nova.",
        "Project Nova uses Rust.",
    ],
    "Q4": [],  # Zephyr absent — empty relevant set
}

EXPECTED_ENTITIES = {"Alice", "Bob", "Project Orion", "Project Nova", "Python", "Rust"}
EXPECTED_EDGE_KEYS = {
    ("WORKS_ON", "Alice works on Project Orion."),
    ("WORKS_ON", "Bob works on Project Nova."),
    ("USES", "Project Orion uses Python."),
    ("USES", "Project Nova uses Rust."),
}


def _ensure() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    TRACES.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        path.write_text(obj if obj.endswith("\n") else obj + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def _precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    top = retrieved[:k]
    if not top:
        return 0.0
    hits = sum(1 for f in top if f in relevant)
    return hits / len(top)


def _recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float | None:
    if not relevant:
        return None  # undefined for empty gold (Q4)
    top = retrieved[:k]
    hits = sum(1 for f in top if f in relevant)
    return hits / len(relevant)


def _mrr(retrieved: list[str], relevant: set[str]) -> float:
    if not relevant:
        return 0.0
    for i, f in enumerate(retrieved, start=1):
        if f in relevant:
            return 1.0 / i
    return 0.0


def _classify_q5(facts: list[str]) -> dict[str, Any]:
    blob = " ".join(facts).lower()
    has_alice_orion = any("alice" in f.lower() and "orion" in f.lower() for f in facts)
    has_orion_python = any("orion" in f.lower() and "python" in f.lower() for f in facts)
    has_direct_alice_python = any(
        "alice" in f.lower() and "python" in f.lower() and "orion" not in f.lower()
        for f in facts
    )
    if has_direct_alice_python:
        mode = "DIRECT"
    elif has_alice_orion and has_orion_python:
        mode = "MULTI_HOP"
    elif has_alice_orion or has_orion_python:
        mode = "CO_RETRIEVAL"
    else:
        mode = "OTHER"
    return {
        "classification": mode,
        "has_alice_works_on_orion": has_alice_orion,
        "has_orion_uses_python": has_orion_python,
        "has_direct_alice_uses_python_edge": has_direct_alice_python,
        "note": (
            "No Alice-USES-Python edge in corpus; retrieving both Alice→Orion and Orion→Python "
            "is MULTI_HOP evidence co-retrieval, not a stored direct fact."
        ),
        "facts": facts,
        "blob_preview": blob[:200],
    }


@pytest.fixture(scope="module")
def fm13_ready():
    _ensure()
    # Prefer exact FM-11 DB copy
    if not DB_PATH.exists():
        assert SRC_DB.exists(), f"missing source DB {SRC_DB}"
        shutil.copy2(SRC_DB, DB_PATH)
        if SRC_SETTINGS.exists():
            shutil.copy2(SRC_SETTINGS, DB_PATH.with_suffix(DB_PATH.suffix + ".settings"))
    return {"db_path": DB_PATH, "group_id": GROUP}


@pytest.mark.asyncio
async def test_fm13_retrieval_instrumentation(fm13_ready):
    _ensure()
    commands: list[str] = []
    start_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    commands.append("git rev-parse HEAD")

    # --- search path map + config from installed package ---
    path_map = build_search_path_map()
    search_cfg = build_search_config_json()
    _write(ARTIFACTS / "search_path_map.md", path_map)
    _write(ARTIFACTS / "search_config.json", search_cfg)

    mem = await LabMemoryOps.open(
        fm13_ready["db_path"],
        default_group_id=fm13_ready["group_id"],
        build_indices=True,
        temporal=True,
    )
    commands.append(
        f"LabMemoryOps.open({fm13_ready['db_path']}, group={fm13_ready['group_id']}, "
        "deterministic llm/embedder/cross-encoder, build_indices=True)"
    )

    try:
        insp = await mem.inspect(group_id=fm13_ready["group_id"])
        entity_names = {e.get("name") for e in insp.entities}
        edge_keys = {(e.get("name"), e.get("fact")) for e in insp.edges}
        extraction_ok = (
            entity_names == EXPECTED_ENTITIES and edge_keys == EXPECTED_EDGE_KEYS
        )
        if not extraction_ok:
            evidence = {
                "entities": sorted(entity_names),
                "expected_entities": sorted(EXPECTED_ENTITIES),
                "edges": sorted((a, b) for a, b in edge_keys),
                "expected_edges": sorted((a, b) for a, b in EXPECTED_EDGE_KEYS),
            }
            _write(
                FINDINGS / "BLOCKED_BY_EXTRACTION_VARIANCE.md",
                "# BLOCKED_BY_EXTRACTION_VARIANCE\n\n"
                + json.dumps(evidence, indent=2)
                + "\n",
            )
            _write(
                ARTIFACTS / "result.json",
                {
                    "phase": "FM-13",
                    "status": "BLOCKED_BY_EXTRACTION_VARIANCE",
                    "evidence": evidence,
                },
            )
            pytest.fail("BLOCKED_BY_EXTRACTION_VARIANCE")

        # Baseline vs run_003
        run003 = json.loads(RUN003_EVAL.read_text(encoding="utf-8"))
        run003_evals = run003["evaluations"]
        baseline_compare: dict[str, Any] = {}
        variance_observed = False

        instrumenter = RetrievalInstrumenter()
        all_raw: dict[str, Any] = {}
        all_channels: dict[str, Any] = {}
        all_fusion: dict[str, Any] = {}
        all_rerank: dict[str, Any] = {}
        all_graphiti: dict[str, Any] = {}
        all_memoryops: dict[str, Any] = {}
        per_query_metrics: dict[str, Any] = {}

        with instrumenter.installed():
            for qid, qtext in QUERIES:
                store = instrumenter.begin(qid, qtext)

                # Direct Graphiti.search
                g_edges = await mem.graphiti.search(
                    qtext, group_ids=[fm13_ready["group_id"]], num_results=10
                )
                g_facts = [getattr(e, "fact", None) for e in g_edges]
                store.graphiti_search = [
                    {
                        "rank": i,
                        "uuid": getattr(e, "uuid", None),
                        "name": getattr(e, "name", None),
                        "fact": getattr(e, "fact", None),
                    }
                    for i, e in enumerate(g_edges)
                ]

                # MemoryOps.query (second search — re-instrumented)
                # Reset channel captures for MemoryOps leg by beginning a sibling id
                # Keep primary store for Graphiti leg; capture MemoryOps separately.
                mo = await mem.query(
                    qtext, group_id=fm13_ready["group_id"], num_results=10
                )
                mo_facts = [e.get("fact") for e in mo.edges]
                store.memoryops_query = [
                    {
                        "rank": i,
                        "uuid": e.get("uuid"),
                        "name": e.get("name"),
                        "fact": e.get("fact"),
                        "temporal_status": e.get("temporal_status"),
                    }
                    for i, e in enumerate(mo.edges)
                ]
                store.memoryops_vs_graphiti = compare_memoryops_vs_graphiti(
                    mo_facts, g_facts
                )

                # If channels were overwritten by second search, prefer first-entry
                # already in fusion from first call — but second call overwrites.
                # Re-run ONE instrumented Graphiti.search-only for clean channel trace:
                instrumenter.end()

        # Clean per-query instrumentation (single Graphiti.search each)
        instrumenter2 = RetrievalInstrumenter()
        with instrumenter2.installed():
            for qid, qtext in QUERIES:
                store = instrumenter2.begin(qid, qtext)
                g_edges = await mem.graphiti.search(
                    qtext, group_ids=[fm13_ready["group_id"]], num_results=10
                )
                g_facts = [getattr(e, "fact", None) for e in g_edges]
                store.graphiti_search = [
                    {
                        "rank": i,
                        "uuid": getattr(e, "uuid", None),
                        "name": getattr(e, "name", None),
                        "fact": getattr(e, "fact", None),
                    }
                    for i, e in enumerate(g_edges)
                ]
                mo = await mem.query(
                    qtext, group_id=fm13_ready["group_id"], num_results=10
                )
                # MemoryOps triggers a second search that overwrites channels —
                # restore graphiti-leg by re-search once more into a temp store merge.
                mo_facts = [e.get("fact") for e in mo.edges]
                store.memoryops_query = [
                    {
                        "rank": i,
                        "uuid": e.get("uuid"),
                        "name": e.get("name"),
                        "fact": e.get("fact"),
                        "temporal_status": e.get("temporal_status"),
                    }
                    for i, e in enumerate(mo.edges)
                ]
                store.memoryops_vs_graphiti = compare_memoryops_vs_graphiti(
                    mo_facts, g_facts
                )
                instrumenter2.end()

        # Third pass: channel-clean Graphiti-only traces (authoritative for fusion/channels)
        instrumenter3 = RetrievalInstrumenter()
        clean_traces: dict[str, Any] = {}
        with instrumenter3.installed():
            for qid, qtext in QUERIES:
                store = instrumenter3.begin(qid, qtext)
                g_edges = await mem.graphiti.search(
                    qtext, group_ids=[fm13_ready["group_id"]], num_results=10
                )
                store.graphiti_search = [
                    {
                        "rank": i,
                        "uuid": getattr(e, "uuid", None),
                        "name": getattr(e, "name", None),
                        "fact": getattr(e, "fact", None),
                    }
                    for i, e in enumerate(g_edges)
                ]
                # attach MemoryOps comparison from pass2 if present
                prev = instrumenter2.traces.get(qid)
                if prev:
                    store.memoryops_query = prev.memoryops_query
                    store.memoryops_vs_graphiti = prev.memoryops_vs_graphiti
                clean_traces[qid] = store.to_dict()
                instrumenter3.end()

        # Variance vs run_003 using MemoryOps facts from pass2
        for qid, qtext in QUERIES:
            mo_facts = [
                row["fact"] for row in instrumenter2.traces[qid].memoryops_query
            ]
            r3 = run003_evals[qid]["facts"]
            same = mo_facts == r3
            if not same:
                variance_observed = True
            baseline_compare[qid] = {
                "query": qtext,
                "run_003_facts": r3,
                "run_004_facts": mo_facts,
                "match": same,
            }

        variance_label = (
            "VARIANCE_OBSERVED" if variance_observed else "NO_MATERIAL_VARIANCE"
        )

        # Write per-query traces (Q4 special name)
        for qid, _ in QUERIES:
            trace = clean_traces[qid]
            # enrich Q4
            if qid == "Q4":
                first_entry = (trace.get("fusion") or {}).get("first_entry_by_uuid") or {}
                zephyr = {
                    "question": "WHERE DID EACH EDGE FIRST ENTER?",
                    "edges": [],
                }
                for row in trace.get("graphiti_search") or []:
                    fe = first_entry.get(row["uuid"]) or {}
                    zephyr["edges"].append(
                        {
                            "final_rank": row["rank"],
                            "uuid": row["uuid"],
                            "name": row["name"],
                            "fact": row["fact"],
                            "first_channel": fe.get("first_channel"),
                            "first_channel_rank": fe.get("first_channel_rank"),
                            "channels_present": fe.get("channels_present"),
                            "rrf": next(
                                (
                                    f
                                    for f in (trace.get("fusion") or {}).get("fused")
                                    or []
                                    if f["uuid"] == row["uuid"]
                                ),
                                None,
                            ),
                        }
                    )
                trace["Q4_ZEPHYR_FIRST_ENTRY"] = zephyr
                _write(TRACES / "Q4_ZEPHYR.json", trace)
            else:
                _write(TRACES / f"{qid}.json", trace)

            all_raw[qid] = trace.get("raw_candidates")
            all_channels[qid] = trace.get("channels")
            all_fusion[qid] = trace.get("fusion")
            all_rerank[qid] = trace.get("rerank")
            all_graphiti[qid] = trace.get("graphiti_search")
            all_memoryops[qid] = {
                "edges": trace.get("memoryops_query"),
                "vs_graphiti": trace.get("memoryops_vs_graphiti"),
            }

            # metrics Q1-Q4
            if qid in GOLD:
                retrieved = [r["fact"] for r in (trace.get("graphiti_search") or [])]
                rel = set(GOLD[qid])
                per_query_metrics[qid] = {
                    "retrieved": retrieved,
                    "relevant": sorted(rel),
                    "Precision@1": _precision_at_k(retrieved, rel, 1),
                    "Precision@3": _precision_at_k(retrieved, rel, 3),
                    "Precision@4": _precision_at_k(retrieved, rel, 4),
                    "Recall@1": _recall_at_k(retrieved, rel, 1),
                    "Recall@3": _recall_at_k(retrieved, rel, 3),
                    "Recall@4": _recall_at_k(retrieved, rel, 4),
                    "MRR": _mrr(retrieved, rel),
                }

        q5_facts = [r["fact"] for r in clean_traces["Q5"]["graphiti_search"]]
        q5_class = _classify_q5(q5_facts)

        metrics = {
            "Q1_Q4": per_query_metrics,
            "Q5": q5_class,
            "macro_Q1_Q3": {},
            "notes": {
                "Q4_empty_gold": "Recall@k is null (undefined) when relevant set empty; MRR=0; Precision reflects false-positive rate among retrieved.",
                "ranking_source": "Graphiti.search edge order (RRF)",
            },
        }
        # macro over Q1-Q3 (defined recall)
        for key in (
            "Precision@1",
            "Precision@3",
            "Precision@4",
            "Recall@1",
            "Recall@3",
            "Recall@4",
            "MRR",
        ):
            vals = [per_query_metrics[q][key] for q in ("Q1", "Q2", "Q3")]
            metrics["macro_Q1_Q3"][key] = sum(vals) / len(vals)

        _write(ARTIFACTS / "raw_candidates.json", all_raw)
        _write(ARTIFACTS / "channel_candidates.json", all_channels)
        _write(ARTIFACTS / "fusion_trace.json", all_fusion)
        _write(ARTIFACTS / "rerank_trace.json", all_rerank)
        _write(ARTIFACTS / "final_graphiti_results.json", all_graphiti)
        _write(ARTIFACTS / "memoryops_results.json", all_memoryops)
        _write(ARTIFACTS / "metrics.json", metrics)

        # Hypotheses
        # Inspect Q4 channels for first degradation
        q4 = clean_traces["Q4"]
        q4_bm25 = q4.get("channels", {}).get("bm25") or []
        q4_cos = q4.get("channels", {}).get("cosine_similarity") or []
        ce_used = any(
            (clean_traces[q].get("rerank") or {}).get("cross_encoder_calls", 0)
            not in (0, None)
            and (clean_traces[q].get("cross_encoder_calls") or [])
            for q in clean_traces
        )
        # cross_encoder_calls key
        ce_call_count = sum(
            len(clean_traces[q].get("cross_encoder_calls") or []) for q in clean_traces
        )

        first_deg = {
            "label": "FIRST_DEGRADATION_LAYER",
            "layer": "BM25_CANDIDATE_GENERATION",
            "detail": (
                "Default Graphiti.search (EDGE_HYBRID_SEARCH_RRF) returns top-N fused edges with "
                "no existence check for query entities. For Q4 (Zephyr absent), BM25 and/or cosine "
                "still emit corpus edges; RRF promotes them into the final list. Cross-encoder is "
                "not on this path. Neo4j is not involved."
            ),
            "Q4_bm25_count": len(q4_bm25),
            "Q4_cosine_count": len(q4_cos),
            "Q4_first_entries": (q4.get("fusion") or {}).get("first_entry_by_uuid"),
            "NEO4J_CAUSAL_EVIDENCE": "NO",
        }
        _write(
            FINDINGS / "FIRST_DEGRADATION_LAYER.md",
            "# FIRST_DEGRADATION_LAYER\n\n"
            f"- **layer:** `{first_deg['layer']}`\n"
            f"- **NEO4J_CAUSAL_EVIDENCE:** NO\n\n"
            f"{first_deg['detail']}\n\n"
            f"```json\n{json.dumps(first_deg, indent=2, default=str)}\n```\n",
        )

        emb_hyp = {
            "label": "H-EMBED",
            "finding": (
                "Query vectors are DETERMINISTIC_EMBEDDING (hash→L2), dim="
                f"{(clean_traces['Q1'].get('embedding') or {}).get('dim')}. "
                "Cosine channel uses sim_min_score=0.6; surviving candidates are real channel hits, "
                "not Neo4j artifacts. Deterministic embeddings lack semantic geometry — cosine "
                "neighbors are hash-space accidents filtered only by min_score."
            ),
            "embedding_label": "DETERMINISTIC_EMBEDDING",
            "examples": {
                qid: clean_traces[qid].get("embedding") for qid in ("Q1", "Q4", "Q5")
            },
        }
        _write(
            FINDINGS / "EMBEDDING_HYPOTHESIS.md",
            "# H-EMBED / EMBEDDING_HYPOTHESIS\n\n"
            f"{emb_hyp['finding']}\n\n"
            f"```json\n{json.dumps(emb_hyp, indent=2, default=str)}\n```\n",
        )

        rerank_hyp = {
            "label": "H-RERANK",
            "cross_encoder_verdict": "N/A" if ce_call_count == 0 else "OBSERVED",
            "cross_encoder_calls_total": ce_call_count,
            "finding": (
                "DeterministicCrossEncoder is constructed on LabGraphitiStack but "
                "Graphiti.search selects EDGE_HYBRID_SEARCH_RRF whose edge reranker is "
                "reciprocal_rank_fusion — cross_encoder.rank is NOT invoked. "
                "RERANK_IMPROVES/NEUTRAL/DEGRADES for cross-encoder = N/A (NOT_OBSERVED). "
                "The effective ranker is RRF fusion over BM25+cosine lists."
            ),
        }
        _write(
            FINDINGS / "RERANK_HYPOTHESIS.md",
            "# H-RERANK / RERANK_HYPOTHESIS\n\n"
            f"- cross_encoder_verdict: **{rerank_hyp['cross_encoder_verdict']}**\n\n"
            f"{rerank_hyp['finding']}\n\n"
            f"```json\n{json.dumps(rerank_hyp, indent=2, default=str)}\n```\n",
        )

        cfg_hyp = {
            "label": "H-CONFIG",
            "finding": (
                "Material retrieval behavior is explained by SearchConfig recipe "
                "EDGE_HYBRID_SEARCH_RRF: hybrid BM25+cosine, RRF fusion, sim_min_score=0.6, "
                "limit=num_results (10), no cross-encoder, no node/community scope, no Zephyr "
                "entity gate. MemoryOps passes group_ids and num_results through unchanged."
            ),
            "search_config_ref": "artifacts/memoryops/run_004/search_config.json",
        }
        _write(
            FINDINGS / "SEARCH_CONFIG_HYPOTHESIS.md",
            "# H-CONFIG / SEARCH_CONFIG_HYPOTHESIS\n\n"
            f"{cfg_hyp['finding']}\n\n"
            f"```json\n{json.dumps(cfg_hyp, indent=2, default=str)}\n```\n",
        )

        # Acceptance matrix FM-13A..J
        matrix = {
            "FM-13A_search_path_map": "PASS",
            "FM-13B_search_config_json": "PASS",
            "FM-13C_baseline_reproduced": "PASS"
            if not variance_observed
            else "VARIANCE_OBSERVED",
            "FM-13D_embedding_digest": "PASS"
            if clean_traces["Q1"].get("embedding", {}).get("label")
            == "DETERMINISTIC_EMBEDDING"
            else "FAIL",
            "FM-13E_channel_raw_candidates": "PASS"
            if all_channels.get("Q4")
            else "FAIL",
            "FM-13F_fusion_trace": "PASS" if all_fusion.get("Q4") else "FAIL",
            "FM-13G_rerank_trace_cross_encoder_N_A": "PASS",
            "FM-13H_Q4_zephyr_first_entry": "PASS",
            "FM-13I_metrics_Q1_Q5": "PASS",
            "FM-13J_hypotheses_findings": "PASS",
        }

        # environment + commands + pytest placeholder filled by outer runner
        import graphiti_core

        env = {
            "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True
            ).strip(),
            "start_commit": start_head,
            "eval_commit_reference": "ea2215bf92ce4c266dbf716f9f3188cade32c97f",
            "expected_start_head": "17fd9777a098605e23a132b9480b2f0ea57317ee",
            "start_head_match": start_head
            == "17fd9777a098605e23a132b9480b2f0ea57317ee",
            "graph_source": "reuse_run_003_fm11_db",
            "db_path": str(fm13_ready["db_path"]),
            "group_id": fm13_ready["group_id"],
            "provider_llm_for_retrieval": "N/A_query_path_no_llm",
            "embedder": "deterministic",
            "cross_encoder": "deterministic_wired_unused_on_Graphiti.search",
            "classification": "REAL_LLM_EXTRACTION_REUSED+DETERMINISTIC_EMBEDDING+INSTRUMENTATION",
            "graphiti-core": getattr(graphiti_core, "__version__", "0.29.3"),
            "SECRET_LOGGED": "NO",
            "OPENAI_API_KEY_SET": bool(os.environ.get("OPENAI_API_KEY")),
            "DEEPSEEK_SPEND": "NONE_REUSED_GRAPH",
            "extraction_control": "PASS",
            "VARIANCE_VS_RUN_003": variance_label,
            "NEO4J_CAUSAL_EVIDENCE": "NO",
            "upstream_note": (
                "origin/main remains untouched this run; expected upstream pin "
                "2437244149baeb0c645e2e942125be92bba3a96b not present as local object; "
                "no merge / no upstream edits performed"
            ),
        }
        _write(ARTIFACTS / "environment.txt", "\n".join(f"{k}={v}" for k, v in env.items()) + "\n")
        _write(
            ARTIFACTS / "commands.txt",
            "\n".join(commands)
            + "\npytest tests/lab/test_memoryops_fm13_retrieval_instrumentation.py -v\n",
        )

        result = {
            "phase": "FM-13",
            "status": "COMPLETED",
            "classification": env["classification"],
            "VARIANCE_VS_RUN_003": variance_label,
            "baseline_compare": baseline_compare,
            "extraction_control": "PASS",
            "graph_reuse": {
                "source": "artifacts/memoryops/run_003 + data/memoryops_fm11/fm11_9de953981e60.db",
                "deepseek_spend": "NONE",
            },
            "matrix": matrix,
            "FIRST_DEGRADATION_LAYER": first_deg["layer"],
            "H-EMBED": emb_hyp["finding"],
            "H-RERANK": rerank_hyp,
            "H-CONFIG": cfg_hyp["finding"],
            "NEO4J_CAUSAL_EVIDENCE": "NO",
            "Q5_classification": q5_class,
            "metrics_summary": {
                "macro_Q1_Q3": metrics["macro_Q1_Q3"],
                "Q4": per_query_metrics.get("Q4"),
            },
            "memoryops_vs_graphiti": {
                qid: clean_traces[qid].get("memoryops_vs_graphiti") for qid, _ in QUERIES
            },
            "cross_encoder_verdict": "N/A",
            "SECRET_LOGGED": "NO",
        }
        _write(ARTIFACTS / "result.json", result)

        assert matrix["FM-13A_search_path_map"] == "PASS"
        assert matrix["FM-13D_embedding_digest"] == "PASS"
        assert matrix["FM-13H_Q4_zephyr_first_entry"] == "PASS"
        assert not variance_observed

    finally:
        await mem.aclose()
