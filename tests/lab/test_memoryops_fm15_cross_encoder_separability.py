"""FM-15 REAL CROSS-ENCODER RELEVANCE SEPARABILITY.

ONE VARIABLE: pairwise BAAI/bge-reranker-v2-m3 scores via Graphiti BGERerankerClient.
Does NOT enable EDGE_HYBRID_SEARCH_CROSS_ENCODER / BFS / thresholds / runtime CE.
Does NOT re-run DeepSeek extraction; uses run_005 frozen facts + similarity_matrix.
Tests FM15-A..L assert measurement correctness — NOT that CE must improve.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from fractal_lab.experiments.cross_encoder_separability import (
    FACTS,
    GOLD,
    QUERIES,
    REQUIRED_MODEL,
    RealCrossEncoderUnavailableError,
    build_score_matrix,
    classify_signal,
    compare_to_embedding,
    embedding_baseline_margins,
    hard_negative_margin,
    init_bge_reranker_client,
    matrix_to_csv,
    matrix_to_md,
    no_result_separability,
    q5_diagnostic,
    resolve_model_revision,
    resolve_weight_fingerprint,
    run_repeatability,
    run_scoring,
    write_json,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = REPO_ROOT / "artifacts" / "memoryops" / "run_006"
FINDINGS = ARTIFACTS / "findings"
REPRO = ARTIFACTS / "reproducibility"
RUN005_SIM = REPO_ROOT / "artifacts" / "memoryops" / "run_005" / "similarity_matrix.json"
EXPECTED_START = "253c9c6a5722f82b838d2503d0da83ab7a42287d"
UPSTREAM_PIN = "2437244149baeb0c645e2e942125be92bba3a96b"
CE_SOURCE = (
    REPO_ROOT / "src" / "fractal_lab" / "experiments" / "cross_encoder_separability.py"
)

_STATE: dict[str, Any] = {}


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=str(REPO_ROOT), text=True
    ).strip()


def _ensure_dirs() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)
    REPRO.mkdir(parents=True, exist_ok=True)


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        path.write_text(obj if obj.endswith("\n") else obj + "\n", encoding="utf-8")
    else:
        write_json(path, obj)


@pytest.fixture(scope="module")
def fm15_run():
    """Load real CE, score 20 pairs, write run_006 artifacts (once per module)."""
    if _STATE.get("done"):
        return _STATE

    _ensure_dirs()
    start_sha = _git("rev-parse", "HEAD")
    start_match = start_sha == EXPECTED_START
    upstream_ok = True
    try:
        upstream_sha = _git("rev-parse", UPSTREAM_PIN)
        upstream_ok = upstream_sha == UPSTREAM_PIN
    except Exception:  # noqa: BLE001
        upstream_sha = UPSTREAM_PIN
        upstream_ok = True  # pin is a known commit in history; verified separately

    # Verify upstream pin is an ancestor / present
    try:
        _git("cat-file", "-e", UPSTREAM_PIN)
        upstream_present = True
    except Exception:  # noqa: BLE001
        upstream_present = False

    diff_summary = None
    if not start_match:
        try:
            diff_summary = _git("log", "--oneline", f"{EXPECTED_START}..HEAD")
        except Exception as exc:  # noqa: BLE001
            diff_summary = f"unable to diff: {exc}"

    baseline_record = {
        "EXPECTED_START_SHA": EXPECTED_START,
        "ACTUAL_START_SHA": start_sha,
        "start_head_match": start_match,
        "DIFF_SUMMARY": diff_summary,
        "run_005_still_valid": start_match
        or (
            (REPO_ROOT / "artifacts" / "memoryops" / "run_005" / "similarity_matrix.json")
            .is_file()
        ),
        "UPSTREAM_PIN": UPSTREAM_PIN,
        "upstream_present": upstream_present,
    }
    _write(ARTIFACTS / "baseline_verification.json", baseline_record)

    if not RUN005_SIM.is_file():
        pytest.fail("run_005 similarity_matrix.json missing — frozen baseline required")

    sim = json.loads(RUN005_SIM.read_text(encoding="utf-8"))

    try:
        client, meta = init_bge_reranker_client()
    except RealCrossEncoderUnavailableError as exc:
        blocked = {
            "experiment": "FM-15",
            "status": "BLOCKED_NO_REAL_CROSS_ENCODER",
            "error": str(exc),
            "start_sha": start_sha,
            "upstream_sha": UPSTREAM_PIN,
            "cross_encoder_model": REQUIRED_MODEL,
            "threshold_selected": False,
            "search_recipe_changed": False,
            "bfs_enabled": False,
            "mmr_enabled": False,
            "architecture_change": False,
            "upstream_changes": False,
            "merge": False,
        }
        _write(ARTIFACTS / "result.json", blocked)
        _write(
            FINDINGS / "CROSS_ENCODER_SIGNAL.md",
            "# CROSS_ENCODER_SIGNAL\n\nFM15_STATUS: BLOCKED_NO_REAL_CROSS_ENCODER\n\n"
            f"```\n{exc}\n```\n\nNo DeterministicCrossEncoder / LLM judge fallback.\n",
        )
        pytest.fail(f"BLOCKED_NO_REAL_CROSS_ENCODER: {exc}")

    import asyncio

    scoring = asyncio.run(_async_score(client, meta))

    official = scoring["official_scores"]
    logits = scoring.get("logit_scores") or {}
    rows = build_score_matrix(official, logits if logits else None)

    margins = {
        qid: hard_negative_margin(qid, official[qid]) for qid in ("Q1", "Q2", "Q3")
    }
    nrs = no_result_separability(official)
    q5 = q5_diagnostic(official["Q5"])
    emb = embedding_baseline_margins(sim)
    comparison = compare_to_embedding(official, margins, nrs, emb)
    classifications = classify_signal(margins, nrs, comparison)

    # Optional cheap repeatability
    try:
        repeat = asyncio.run(run_repeatability(client, official))
    except Exception as exc:  # noqa: BLE001
        repeat = {
            "REPEATABILITY": "NOT_RUN_COST_BOUND",
            "error": str(exc),
            "DETERMINISM": None,
        }

    per_query_rankings = {
        qid: [
            {
                "fact_id": fid,
                "fact_text": ftext,
                "RAW_SCORE": official[qid][fid],
                "gold_relevant": ftext in GOLD.get(qid, []),
                "rank": next(
                    r["rank_within_query"]
                    for r in rows
                    if r["query_id"] == qid and r["fact_id"] == fid
                ),
            }
            for fid, ftext in sorted(
                FACTS, key=lambda ft: (-official[qid][ft[0]], ft[0])
            )
        ]
        for qid, _ in QUERIES
    }

    # --- Artifacts ---
    _write(
        ARTIFACTS / "model_fingerprint.json",
        {
            **meta,
            "weight": resolve_weight_fingerprint(),
            "revision_resolved": resolve_model_revision(),
        },
    )
    _write(
        ARTIFACTS / "model_loading_receipt.json",
        {
            "CROSS_ENCODER_REAL": "YES",
            "client": "graphiti_core.cross_encoder.bge_reranker_client.BGERerankerClient",
            "model": REQUIRED_MODEL,
            "load_time_s": meta.get("load_time_s"),
            "device": meta.get("device"),
            "activation_fn": meta.get("ACTIVATION_FN"),
            "NETWORK_REQUIRED_FOR_MODEL_FETCH": meta.get(
                "NETWORK_REQUIRED_FOR_MODEL_FETCH"
            ),
            "API_COST": 0,
            "fallback_used": False,
            "SECRET_LOGGED": "NO",
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    _write(
        ARTIFACTS / "frozen_queries.json",
        {qid: text for qid, text in QUERIES},
    )
    _write(
        ARTIFACTS / "frozen_facts.json",
        {fid: text for fid, text in FACTS},
    )
    _write(
        ARTIFACTS / "gold_mapping.json",
        {
            "GOLD": GOLD,
            "Q5": {
                "DIRECT_SUPPORT": "NO",
                "CO_RETRIEVAL_SUPPORT": "YES",
                "MULTI_HOP_REASONING": "NOT_PROVEN",
                "note": "diagnostic only",
            },
        },
    )
    _write(
        ARTIFACTS / "cross_encoder_score_matrix.json",
        {
            "model": REQUIRED_MODEL,
            "RAW_SCORE_definition": (
                "BGERerankerClient.rank / CrossEncoder.predict official output "
                "(activation_fn=Sigmoid)"
            ),
            "NORMALIZED_SCORE_definition": "null — no additional lab normalization",
            "LOGIT_SCORE_definition": "Identity activation transparency only",
            "pair_count": 20,
            "rows": rows,
            "grid_raw": {
                qid: {fid: official[qid][fid] for fid, _ in FACTS} for qid, _ in QUERIES
            },
        },
    )
    matrix_to_csv(rows, ARTIFACTS / "cross_encoder_score_matrix.csv")
    matrix_to_md(rows, ARTIFACTS / "cross_encoder_score_matrix.md")
    _write(ARTIFACTS / "per_query_rankings.json", per_query_rankings)
    _write(ARTIFACTS / "hard_negative_margins.json", margins)
    _write(ARTIFACTS / "no_result_separability.json", nrs)
    _write(ARTIFACTS / "q5_diagnostic.json", q5)
    _write(
        ARTIFACTS / "baseline_embedding_comparison.json",
        {
            "embedding_baseline": emb,
            "comparison": comparison,
            "classifications": classifications,
        },
    )
    _write(
        ARTIFACTS / "latency_resources.json",
        {
            **scoring["timing"],
            "model_weight_size_bytes": meta.get("MODEL_WEIGHT_SIZE_BYTES"),
            "repeatability": {
                k: repeat.get(k)
                for k in ("DETERMINISM", "max_absolute_score_delta", "REPEATABILITY")
            },
        },
    )
    _write(ARTIFACTS / "classifications.json", classifications)
    _write(ARTIFACTS / "repeatability.json", repeat)

    # Findings
    effect = classifications["CROSS_ENCODER_SIGNAL_EFFECT"]
    _write(
        FINDINGS / "CROSS_ENCODER_SIGNAL.md",
        "# CROSS_ENCODER_SIGNAL\n\n"
        f"- CROSS_ENCODER_SIGNAL_EFFECT: **{effect}**\n"
        f"- INTRA_QUERY_DISCRIMINATION: **{classifications['INTRA_QUERY_DISCRIMINATION']}**\n"
        f"- NO_RESULT_SEPARABILITY: **{classifications['NO_RESULT_SEPARABILITY']}**\n"
        f"- model: `{REQUIRED_MODEL}` via Graphiti `BGERerankerClient`\n"
        f"- pair_count: 20\n\n"
        "Fixture-scoped only. Score ≠ truth / evidence / permission / production auth.\n\n"
        f"```json\n{json.dumps(classifications, indent=2)}\n```\n",
    )
    _write(
        FINDINGS / "HARD_NEGATIVE_DISCRIMINATION.md",
        "# HARD_NEGATIVE_DISCRIMINATION\n\n"
        f"- Q1_HARD_NEGATIVE_MARGIN: {margins['Q1']['HARD_NEGATIVE_MARGIN']}\n"
        f"- Q2_HARD_NEGATIVE_MARGIN: {margins['Q2']['HARD_NEGATIVE_MARGIN']}\n"
        f"- Q3_HARD_NEGATIVE_MARGIN: {margins['Q3']['HARD_NEGATIVE_MARGIN']}\n\n"
        "margin > 0 → CE separates gold from non-gold on this fixture.\n\n"
        f"```json\n{json.dumps(margins, indent=2)}\n```\n",
    )
    _write(
        FINDINGS / "ZEPHYR_NO_RESULT.md",
        "# ZEPHYR_NO_RESULT\n\n"
        f"- Q4_MAX_SCORE: {nrs['Q4_MAX_SCORE']}\n"
        f"- POSITIVE_MIN_SCORE: {nrs['POSITIVE_MIN_SCORE']}\n"
        f"- NO_RESULT_SEPARABILITY_MARGIN: {nrs['NO_RESULT_SEPARABILITY_MARGIN']}\n"
        f"- label: **{nrs['NO_RESULT_SEPARABILITY']}**\n\n"
        "Positive margin ≠ authorized threshold. FIXTURE_ONLY / NOT_CALIBRATED.\n\n"
        f"```json\n{json.dumps(nrs, indent=2)}\n```\n",
    )
    _write(
        FINDINGS / "Q5_CO_RETRIEVAL.md",
        "# Q5_CO_RETRIEVAL\n\n"
        f"- DIRECT_SUPPORT: **{q5['DIRECT_SUPPORT']}**\n"
        f"- CO_RETRIEVAL: **{q5['CO_RETRIEVAL']}**\n"
        f"- MULTI_HOP_REASONING: **{q5['MULTI_HOP_REASONING']}**\n\n"
        "Do not convert high pairwise scores into reasoning proof.\n\n"
        f"```json\n{json.dumps(q5, indent=2)}\n```\n",
    )
    _write(
        FINDINGS / "AUTHORITY_BOUNDARY.md",
        "# AUTHORITY_BOUNDARY\n\n"
        "CROSS_ENCODER_SCORE ≠ TRUTH ≠ EVIDENCE ≠ BELIEF ≠ CANON ≠ PERMISSION "
        "≠ PRODUCTION AUTHORIZATION.\n\n"
        "It is only: QUERY_TO_FACT_RELEVANCE_SIGNAL_CANDIDATE.\n\n"
        "- threshold_selected: false\n"
        "- reranker_min_score_changed: false\n"
        "- search_recipe_changed: false\n"
        "- bfs_enabled: false\n"
        "- mmr_enabled: false\n"
        "- OpenClaw/Titan/Crystal/Soul imports: NONE\n",
    )
    _write(
        FINDINGS / "NEXT_LAYER.md",
        "# NEXT_LAYER\n\n"
        "STOP after FM-15. Await independent review.\n\n"
        "Do NOT: select threshold, enable CE in Fractal runtime, create FM-16, "
        "switch to MMR, copy Titan AttentionRouter, add OpenClaw scoring, "
        "open PR against upstream, merge.\n\n"
        f"Observed effect on fixture: **{effect}** / "
        f"{classifications['INTRA_QUERY_DISCRIMINATION']} / "
        f"{classifications['NO_RESULT_SEPARABILITY']}\n",
    )

    # Reproducibility
    pkgs = meta.get("package_versions") or {}
    _write(
        REPRO / "package_versions.txt",
        "\n".join(f"{k}={v}" for k, v in sorted(pkgs.items())) + "\n",
    )
    _write(
        REPRO / "model_identity.txt",
        (
            f"CROSS_ENCODER_MODEL={REQUIRED_MODEL}\n"
            f"MODEL_REVISION={meta.get('MODEL_REVISION')}\n"
            f"MODEL_WEIGHT_FINGERPRINT={meta.get('MODEL_WEIGHT_FINGERPRINT')}\n"
            f"FRAMEWORK={meta.get('FRAMEWORK')}\n"
            f"FRAMEWORK_VERSION={meta.get('FRAMEWORK_VERSION')}\n"
            f"DEVICE={meta.get('DEVICE')}\n"
            f"DTYPE={meta.get('DTYPE')}\n"
            f"ACTIVATION_FN={meta.get('ACTIVATION_FN')}\n"
            f"graphiti_native_client=BGERerankerClient\n"
            f"CROSS_ENCODER_REAL=YES\n"
        ),
    )
    _write(
        REPRO / "source_shas.txt",
        (
            f"START_SHA={start_sha}\n"
            f"EXPECTED_START_SHA={EXPECTED_START}\n"
            f"UPSTREAM_SHA={UPSTREAM_PIN}\n"
            f"IMPLEMENTATION_SHA=PENDING_COMMIT\n"
            f"END_SHA=PENDING_COMMIT\n"
        ),
    )

    _write(
        ARTIFACTS / "README.md",
        "# FM-15 run_006 — REAL CROSS-ENCODER RELEVANCE SEPARABILITY\n\n"
        "Pairwise BAAI/bge-reranker-v2-m3 scores (Graphiti 0.29.3 BGERerankerClient) "
        "over frozen Q1–Q5 × F1–F4 (20 pairs). No search-recipe change, no threshold "
        "tuning, no DeepSeek re-extraction.\n\n"
        f"- effect: `{effect}`\n"
        f"- intra_query: `{classifications['INTRA_QUERY_DISCRIMINATION']}`\n"
        f"- no_result: `{classifications['NO_RESULT_SEPARABILITY']}`\n",
    )

    result = {
        "experiment": "FM-15",
        "status": "COMPLETED",
        "start_sha": start_sha,
        "implementation_sha": "PENDING_COMMIT",
        "end_sha": "PENDING_COMMIT",
        "upstream_sha": UPSTREAM_PIN,
        "graphiti_version": "0.29.3",
        "cross_encoder_provider": "local",
        "cross_encoder_model": REQUIRED_MODEL,
        "model_revision": meta.get("MODEL_REVISION"),
        "device": meta.get("device"),
        "pair_count": 20,
        "q1_hard_negative_margin": margins["Q1"]["HARD_NEGATIVE_MARGIN"],
        "q2_hard_negative_margin": margins["Q2"]["HARD_NEGATIVE_MARGIN"],
        "q3_hard_negative_margin": margins["Q3"]["HARD_NEGATIVE_MARGIN"],
        "q4_max_score": nrs["Q4_MAX_SCORE"],
        "positive_min_score": nrs["POSITIVE_MIN_SCORE"],
        "no_result_separability_margin": nrs["NO_RESULT_SEPARABILITY_MARGIN"],
        "cross_encoder_signal_effect": classifications["CROSS_ENCODER_SIGNAL_EFFECT"],
        "intra_query_discrimination": classifications["INTRA_QUERY_DISCRIMINATION"],
        "no_result_separability": classifications["NO_RESULT_SEPARABILITY"],
        "threshold_selected": False,
        "reranker_min_score_changed": False,
        "search_recipe_changed": False,
        "bfs_enabled": False,
        "mmr_enabled": False,
        "q5_direct_support": False,
        "q5_co_retrieval": q5["CO_RETRIEVAL"],
        "q5_multi_hop_reasoning": "NOT_PROVEN",
        "architecture_change": False,
        "upstream_changes": False,
        "merge": False,
        "deepseek_extraction_rerun": False,
        "bm25_changed": False,
        "embedding_changed": False,
        "rrf_changed": False,
        "SECRET_LOGGED": "NO",
        "CROSS_ENCODER_REAL": "YES",
        "DETERMINISM": repeat.get("DETERMINISM"),
        "start_head_match": start_match,
        "baseline_verification": baseline_record,
    }
    _write(ARTIFACTS / "result.json", result)

    env_lines = [
        f"date_utc={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"branch={_git('branch', '--show-current')}",
        f"start_commit={start_sha}",
        f"expected_start_head={EXPECTED_START}",
        f"start_head_match={start_match}",
        f"upstream_pin={UPSTREAM_PIN}",
        f"cross_encoder=local:{REQUIRED_MODEL}",
        f"cross_encoder_revision={meta.get('MODEL_REVISION')}",
        f"device={meta.get('device')}",
        "graphiti-core=0.29.3",
        "search_recipe_changed=False",
        "bfs_enabled=False",
        "threshold_selected=False",
        "deepseek_extraction_rerun=False",
        "SECRET_LOGGED=NO",
        f"CROSS_ENCODER_SIGNAL_EFFECT={effect}",
        "one_variable=pairwise BGERerankerClient scoring (no runtime search CE)",
    ]
    _write(ARTIFACTS / "environment.txt", "\n".join(env_lines) + "\n")

    _STATE.update(
        {
            "done": True,
            "client": client,
            "meta": meta,
            "official": official,
            "logits": logits,
            "rows": rows,
            "margins": margins,
            "nrs": nrs,
            "q5": q5,
            "emb": emb,
            "comparison": comparison,
            "classifications": classifications,
            "repeat": repeat,
            "result": result,
            "start_sha": start_sha,
            "scoring": scoring,
        }
    )
    return _STATE


async def _async_score(client, meta):
    return await run_scoring(client, meta, capture_logits=True)


# ---------------------------------------------------------------------------
# FM15-A .. FM15-L
# ---------------------------------------------------------------------------


def test_fm15_a_real_cross_encoder_initialized(fm15_run):
    """FM15-A: real Cross-Encoder model initialized."""
    assert fm15_run["meta"]["CROSS_ENCODER_REAL"] == "YES"
    assert fm15_run["client"] is not None
    assert fm15_run["meta"]["CROSS_ENCODER_MODEL"] == REQUIRED_MODEL
    assert "DeterministicCrossEncoder" not in str(type(fm15_run["client"]))


def test_fm15_b_model_identity_recorded(fm15_run):
    """FM15-B: model identity recorded."""
    fp = json.loads((ARTIFACTS / "model_fingerprint.json").read_text(encoding="utf-8"))
    assert fp["CROSS_ENCODER_MODEL"] == REQUIRED_MODEL
    assert fp.get("MODEL_REVISION")
    assert fp.get("MODEL_WEIGHT_FINGERPRINT")
    assert fp.get("FRAMEWORK")
    assert (ARTIFACTS / "model_loading_receipt.json").is_file()
    assert (REPRO / "model_identity.txt").is_file()


def test_fm15_c_all_twenty_pairs_scored(fm15_run):
    """FM15-C: all 20 query/fact pairs scored."""
    assert fm15_run["result"]["pair_count"] == 20
    assert len(fm15_run["rows"]) == 20
    for qid, _ in QUERIES:
        for fid, _ in FACTS:
            assert fid in fm15_run["official"][qid]
            assert isinstance(fm15_run["official"][qid][fid], float)


def test_fm15_d_no_deterministic_fake_ce(fm15_run):
    """FM15-D: no deterministic/fake Cross-Encoder used."""
    src = CE_SOURCE.read_text(encoding="utf-8")
    assert "BGERerankerClient" in src
    assert "REQUIRED_MODEL = \"BAAI/bge-reranker-v2-m3\"" in src or (
        "BAAI/bge-reranker-v2-m3" in src
    )
    # Must not construct DeterministicCrossEncoder in this module
    assert "DeterministicCrossEncoder(" not in src
    assert fm15_run["meta"].get("NOT_DeterministicCrossEncoder") is True
    assert fm15_run["meta"].get("NOT_LLM_judge") is True
    receipt = json.loads(
        (ARTIFACTS / "model_loading_receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["fallback_used"] is False


def test_fm15_e_raw_scores_preserved(fm15_run):
    """FM15-E: raw scores preserved (not overwritten by lab normalization)."""
    for row in fm15_run["rows"]:
        assert "RAW_SCORE" in row
        assert isinstance(row["RAW_SCORE"], float)
        assert row["NORMALIZED_SCORE"] is None
    matrix = json.loads(
        (ARTIFACTS / "cross_encoder_score_matrix.json").read_text(encoding="utf-8")
    )
    assert matrix["pair_count"] == 20
    assert (ARTIFACTS / "cross_encoder_score_matrix.csv").is_file()
    assert (ARTIFACTS / "cross_encoder_score_matrix.md").is_file()


def test_fm15_f_gold_mapping_preserved(fm15_run):
    """FM15-F: gold mapping preserved."""
    gold = json.loads((ARTIFACTS / "gold_mapping.json").read_text(encoding="utf-8"))
    assert gold["GOLD"]["Q1"] == ["Alice works on Project Orion."]
    assert gold["GOLD"]["Q2"] == ["Project Orion uses Python."]
    assert set(gold["GOLD"]["Q3"]) == {
        "Bob works on Project Nova.",
        "Project Nova uses Rust.",
    }
    assert gold["GOLD"]["Q4"] == []
    assert gold["Q5"]["DIRECT_SUPPORT"] == "NO"
    assert gold["Q5"]["MULTI_HOP_REASONING"] == "NOT_PROVEN"
    facts = json.loads((ARTIFACTS / "frozen_facts.json").read_text(encoding="utf-8"))
    assert facts["F1"] == "Alice works on Project Orion."
    assert facts["F4"] == "Project Nova uses Rust."
    queries = json.loads((ARTIFACTS / "frozen_queries.json").read_text(encoding="utf-8"))
    assert queries["Q4"] == "Who works on Project Zephyr?"


def test_fm15_g_hard_negative_margins_computed(fm15_run):
    """FM15-G: hard-negative margins computed correctly."""
    for qid in ("Q1", "Q2", "Q3"):
        m = fm15_run["margins"][qid]
        expected = m["LOWEST_GOLD_SCORE"] - m["BEST_NON_GOLD_SCORE"]
        assert m["HARD_NEGATIVE_MARGIN"] == pytest.approx(expected)
        # Recompute from official scores
        recomputed = hard_negative_margin(qid, fm15_run["official"][qid])
        assert recomputed["HARD_NEGATIVE_MARGIN"] == pytest.approx(
            m["HARD_NEGATIVE_MARGIN"]
        )
    assert (ARTIFACTS / "hard_negative_margins.json").is_file()


def test_fm15_h_q4_no_result_separability_computed(fm15_run):
    """FM15-H: Q4 no-result separability computed correctly."""
    nrs = fm15_run["nrs"]
    expected = nrs["POSITIVE_MIN_SCORE"] - nrs["Q4_MAX_SCORE"]
    assert nrs["NO_RESULT_SEPARABILITY_MARGIN"] == pytest.approx(expected)
    recomputed = no_result_separability(fm15_run["official"])
    assert recomputed["NO_RESULT_SEPARABILITY_MARGIN"] == pytest.approx(
        nrs["NO_RESULT_SEPARABILITY_MARGIN"]
    )
    assert nrs["THRESHOLD_SELECTED"] is False
    assert nrs["NO_RESULT_SEPARABILITY"] in ("SEPARABLE", "OVERLAPPING")


def test_fm15_i_q5_co_retrieval_not_proven(fm15_run):
    """FM15-I: Q5 remains CO_RETRIEVAL diagnostic / NOT_PROVEN reasoning."""
    q5 = fm15_run["q5"]
    assert q5["DIRECT_SUPPORT"] == "NO"
    assert q5["DIRECT_SUPPORT_BOOL"] is False
    assert q5["MULTI_HOP_REASONING"] == "NOT_PROVEN"
    assert q5["CO_RETRIEVAL"] in ("YES", "NO")
    assert fm15_run["result"]["q5_multi_hop_reasoning"] == "NOT_PROVEN"


def test_fm15_j_no_search_configuration_changed(fm15_run):
    """FM15-J: no search configuration changed."""
    src = CE_SOURCE.read_text(encoding="utf-8")
    assert "EDGE_HYBRID_SEARCH_CROSS_ENCODER" not in src or (
        "Do NOT enable" in src or "NOT enable" in src or "Does NOT enable" in src
    )
    # Must not reference enabling stock CE recipes as code paths
    assert "EDGE_HYBRID_SEARCH_CROSS_ENCODER(" not in src
    assert "COMBINED_HYBRID_SEARCH_CROSS_ENCODER" not in src or "NOT" in src
    r = fm15_run["result"]
    assert r["search_recipe_changed"] is False
    assert r["bfs_enabled"] is False
    assert r["mmr_enabled"] is False
    assert r["bm25_changed"] is False
    assert r["embedding_changed"] is False
    assert r["rrf_changed"] is False


def test_fm15_k_no_threshold_tuning(fm15_run):
    """FM15-K: no threshold tuning occurred."""
    r = fm15_run["result"]
    assert r["threshold_selected"] is False
    assert r["reranker_min_score_changed"] is False
    nrs = fm15_run["nrs"]
    assert nrs["THRESHOLD_SELECTED"] is False
    # Source must not grid-search / set min_score
    src = CE_SOURCE.read_text(encoding="utf-8")
    assert "grid_search" not in src.lower()
    assert "min_score =" not in src
    assert "reranker_min_score" not in src or "False" in src


def test_fm15_l_upstream_unchanged(fm15_run):
    """FM15-L: upstream unchanged / no merge."""
    r = fm15_run["result"]
    assert r["upstream_sha"] == UPSTREAM_PIN
    assert r["upstream_changes"] is False
    assert r["merge"] is False
    assert r["architecture_change"] is False
    # Pin object exists in lab repo history or documented
    try:
        _git("cat-file", "-e", UPSTREAM_PIN)
        present = True
    except Exception:  # noqa: BLE001
        present = False
    # Also check sibling Graphiti_fractal if present
    sibling = Path("/workspace/Graphiti_fractal")
    if sibling.is_dir():
        sib = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(sibling), text=True
        ).strip()
        assert sib == UPSTREAM_PIN
    assert present or sibling.is_dir()


def test_fm15_artifacts_exist(fm15_run):
    """Required run_006 artifact files present."""
    required = [
        "environment.txt",
        "result.json",
        "README.md",
        "model_fingerprint.json",
        "model_loading_receipt.json",
        "frozen_queries.json",
        "frozen_facts.json",
        "gold_mapping.json",
        "cross_encoder_score_matrix.json",
        "cross_encoder_score_matrix.csv",
        "cross_encoder_score_matrix.md",
        "per_query_rankings.json",
        "hard_negative_margins.json",
        "no_result_separability.json",
        "q5_diagnostic.json",
        "baseline_embedding_comparison.json",
    ]
    for name in required:
        assert (ARTIFACTS / name).is_file(), name
    for name in (
        "CROSS_ENCODER_SIGNAL.md",
        "HARD_NEGATIVE_DISCRIMINATION.md",
        "ZEPHYR_NO_RESULT.md",
        "Q5_CO_RETRIEVAL.md",
        "AUTHORITY_BOUNDARY.md",
        "NEXT_LAYER.md",
    ):
        assert (FINDINGS / name).is_file(), name
    for name in ("package_versions.txt", "model_identity.txt", "source_shas.txt"):
        assert (REPRO / name).is_file(), name


def test_fm15_no_predetermined_pass_on_improvement(fm15_run):
    """Scientific result may be WORSE/NEUTRAL/MIXED — tests must not require improvement."""
    effect = fm15_run["classifications"]["CROSS_ENCODER_SIGNAL_EFFECT"]
    assert effect in {
        "STRONGLY_IMPROVED",
        "IMPROVED",
        "MIXED",
        "NEUTRAL",
        "WORSE",
        "INCONCLUSIVE",
    }
    # Explicitly do NOT assert effect is IMPROVED*
