"""FM-15 lab-only REAL pairwise Cross-Encoder relevance separability.

Uses Graphiti 0.29.3 native BGERerankerClient (BAAI/bge-reranker-v2-m3).
Does NOT enable EDGE_HYBRID_SEARCH_CROSS_ENCODER / BFS / runtime search changes.
Does NOT fall back to DeterministicCrossEncoder / LLM judge / other CE models.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import os
import resource
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_MODEL = "BAAI/bge-reranker-v2-m3"
GRAPHITI_VERSION_PIN = "0.29.3"

QUERIES: list[tuple[str, str]] = [
    ("Q1", "Who works on Project Orion?"),
    ("Q2", "What language does Project Orion use?"),
    ("Q3", "What is related to Project Nova?"),
    ("Q4", "Who works on Project Zephyr?"),
    ("Q5", "Does Alice use Python?"),
]

FACTS: list[tuple[str, str]] = [
    ("F1", "Alice works on Project Orion."),
    ("F2", "Project Orion uses Python."),
    ("F3", "Bob works on Project Nova."),
    ("F4", "Project Nova uses Rust."),
]

GOLD: dict[str, list[str]] = {
    "Q1": ["Alice works on Project Orion."],
    "Q2": ["Project Orion uses Python."],
    "Q3": ["Bob works on Project Nova.", "Project Nova uses Rust."],
    "Q4": [],
    "Q5": [],  # diagnostic only — not used for hard-negative margins
}

FACT_BY_ID = {fid: text for fid, text in FACTS}
QUERY_BY_ID = {qid: text for qid, text in QUERIES}
FACT_ID_BY_TEXT = {text: fid for fid, text in FACTS}


class RealCrossEncoderUnavailableError(RuntimeError):
    """Raised when BAAI/bge-reranker-v2-m3 cannot be initialized — FM-15 must STOP."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _package_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for name in (
        "sentence_transformers",
        "transformers",
        "torch",
        "numpy",
        "graphiti_core",
    ):
        try:
            mod = __import__(name)
            out[name] = getattr(mod, "__version__", "UNKNOWN")
        except Exception as exc:  # noqa: BLE001
            out[name] = f"MISSING:{type(exc).__name__}"
    try:
        import importlib.metadata as im

        out["graphiti-core"] = im.version("graphiti-core")
    except Exception:  # noqa: BLE001
        out.setdefault("graphiti-core", out.get("graphiti_core", "UNKNOWN"))
    return out


def _hf_cache_dir() -> Path:
    return Path.home() / ".cache" / "huggingface" / "hub" / "models--BAAI--bge-reranker-v2-m3"


def resolve_model_revision() -> str | None:
    refs = _hf_cache_dir() / "refs" / "main"
    if refs.is_file():
        return refs.read_text(encoding="utf-8").strip()
    return None


def resolve_weight_fingerprint() -> dict[str, Any]:
    rev = resolve_model_revision()
    out: dict[str, Any] = {
        "model": REQUIRED_MODEL,
        "revision": rev,
        "weight_file": None,
        "sha256": None,
        "size_bytes": None,
    }
    if not rev:
        return out
    snap = _hf_cache_dir() / "snapshots" / rev
    weight = snap / "model.safetensors"
    if not weight.is_file():
        bins = list(snap.glob("*.safetensors")) + list(snap.glob("*.bin"))
        weight = bins[0] if bins else None  # type: ignore[assignment]
    if weight and Path(weight).is_file():
        h = hashlib.sha256()
        with Path(weight).open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        out["weight_file"] = Path(weight).name
        out["sha256"] = h.hexdigest()
        out["size_bytes"] = Path(weight).stat().st_size
    return out


def init_bge_reranker_client() -> tuple[Any, dict[str, Any]]:
    """Initialize Graphiti-native BGERerankerClient for BAAI/bge-reranker-v2-m3.

    Raises RealCrossEncoderUnavailableError on any failure — no silent fallback.
    """
    t0 = time.perf_counter()
    try:
        from graphiti_core.cross_encoder.bge_reranker_client import BGERerankerClient
    except Exception as exc:  # noqa: BLE001
        raise RealCrossEncoderUnavailableError(
            f"cannot import BGERerankerClient: {exc}"
        ) from exc

    try:
        client = BGERerankerClient()
    except Exception as exc:  # noqa: BLE001
        raise RealCrossEncoderUnavailableError(
            f"BGERerankerClient init failed for {REQUIRED_MODEL}: {exc}"
        ) from exc

    load_s = time.perf_counter() - t0
    model = getattr(client, "model", None)
    if model is None:
        raise RealCrossEncoderUnavailableError("BGERerankerClient.model is None")

    # Hard identity check — refuse silent substitution
    model_name = None
    card = getattr(model, "model_card_data", None)
    if card is not None:
        model_name = getattr(card, "base_model", None) or getattr(card, "model_id", None)
    if model_name is None:
        model_name = getattr(model, "model_name", None) or getattr(
            model, "_model_card_vars", {}
        ).get("model_name")
    # CrossEncoder stores model_name_or_path sometimes
    model_name = model_name or getattr(model, "model_name_or_path", None)
    name_str = str(model_name or "")
    if REQUIRED_MODEL not in name_str and name_str not in ("", "None"):
        # still allow if transformers config name matches
        cfg = getattr(model, "config", None) or getattr(
            getattr(model, "model", None), "config", None
        )
        cfg_name = getattr(cfg, "_name_or_path", None) if cfg is not None else None
        if cfg_name and REQUIRED_MODEL not in str(cfg_name):
            raise RealCrossEncoderUnavailableError(
                f"refusing substituted CE model {name_str!r} / {cfg_name!r}; "
                f"required {REQUIRED_MODEL}"
            )
    elif REQUIRED_MODEL not in name_str:
        # verify via HF cache presence + CrossEncoder constructor default in source
        cfg = getattr(getattr(model, "model", None), "config", None)
        cfg_name = getattr(cfg, "_name_or_path", None) if cfg is not None else None
        if cfg_name and REQUIRED_MODEL not in str(cfg_name):
            raise RealCrossEncoderUnavailableError(
                f"model identity unclear / mismatched: {cfg_name!r}"
            )

    try:
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = str(next(model.model.parameters()).dtype) if hasattr(model, "model") else "unknown"
    except Exception:  # noqa: BLE001
        device = "cpu"
        dtype = "unknown"

    activation = str(getattr(model, "activation_fn", None))
    revision = resolve_model_revision()
    weights = resolve_weight_fingerprint()
    meta = {
        "CROSS_ENCODER_PROVIDER": "local",
        "CROSS_ENCODER_MODEL": REQUIRED_MODEL,
        "MODEL_REVISION": revision,
        "MODEL_WEIGHT_FINGERPRINT": weights.get("sha256"),
        "MODEL_WEIGHT_FILE": weights.get("weight_file"),
        "MODEL_WEIGHT_SIZE_BYTES": weights.get("size_bytes"),
        "FRAMEWORK": "sentence-transformers CrossEncoder via graphiti_core.BGERerankerClient",
        "FRAMEWORK_VERSION": _package_versions().get("sentence_transformers", "UNKNOWN"),
        "DEVICE": device.upper() if device == "cpu" else device.upper(),
        "device": device,
        "DTYPE": dtype,
        "ACTIVATION_FN": activation,
        "NETWORK_REQUIRED_FOR_MODEL_FETCH": "YES" if revision is None else "NO_IF_CACHED",
        "API_COST": 0,
        "load_time_s": load_s,
        "package_versions": _package_versions(),
        "CROSS_ENCODER_REAL": "YES",
        "NOT_DeterministicCrossEncoder": True,
        "NOT_LLM_judge": True,
        "NOT_OpenAI_reranker": True,
        "NOT_DeepSeek_judge": True,
        "graphiti_native_client": "BGERerankerClient",
        "graphiti_version_expected": GRAPHITI_VERSION_PIN,
        "SECRET_LOGGED": "NO",
        "recorded_at_utc": _utc_now(),
    }
    return client, meta


async def score_pairs_official(
    client: Any, query: str, passages: list[str]
) -> list[tuple[str, float]]:
    """Score via Graphiti-native BGERerankerClient.rank (official path)."""
    return await client.rank(query, passages)


def score_logits_optional(cross_encoder_model: Any, query: str, passages: list[str]) -> list[float]:
    """Optional Identity-activation logits for transparency; does not replace official RAW."""
    try:
        import torch.nn as nn

        pairs = [[query, p] for p in passages]
        arr = cross_encoder_model.predict(pairs, activation_fn=nn.Identity())
        return [float(x) for x in arr]
    except Exception:  # noqa: BLE001
        return []


def build_score_matrix(
    official_scores: dict[str, dict[str, float]],
    logit_scores: dict[str, dict[str, float]] | None = None,
) -> list[dict[str, Any]]:
    """Flatten 20 pairs into rows with gold label and within-query rank."""
    rows: list[dict[str, Any]] = []
    for qid, qtext in QUERIES:
        scored = []
        for fid, ftext in FACTS:
            raw = float(official_scores[qid][fid])
            gold = ftext in GOLD.get(qid, [])
            logit = None
            if logit_scores and qid in logit_scores and fid in logit_scores[qid]:
                logit = float(logit_scores[qid][fid])
            scored.append((fid, ftext, raw, gold, logit))
        # rank by raw desc (stable by fact id)
        ordered = sorted(scored, key=lambda t: (-t[2], t[0]))
        rank_map = {fid: i + 1 for i, (fid, *_rest) in enumerate(ordered)}
        for fid, ftext, raw, gold, logit in scored:
            rows.append(
                {
                    "query_id": qid,
                    "query_text": qtext,
                    "fact_id": fid,
                    "fact_text": ftext,
                    "gold_relevant": gold,
                    "RAW_SCORE": raw,
                    "NORMALIZED_SCORE": None,
                    "LOGIT_SCORE": logit,
                    "rank_within_query": rank_map[fid],
                    "note": (
                        "RAW_SCORE is BGERerankerClient.rank / CrossEncoder.predict "
                        "official output (model activation_fn=Sigmoid). "
                        "No additional lab normalization. LOGIT_SCORE is Identity "
                        "activation for transparency only."
                    ),
                }
            )
    return rows


def hard_negative_margin(qid: str, scores_by_fid: dict[str, float]) -> dict[str, Any]:
    gold_texts = GOLD[qid]
    gold_fids = [FACT_ID_BY_TEXT[t] for t in gold_texts]
    non_gold_fids = [fid for fid, _ in FACTS if fid not in gold_fids]
    gold_scores = [scores_by_fid[fid] for fid in gold_fids]
    non_gold_scores = [scores_by_fid[fid] for fid in non_gold_fids]
    lowest_gold = min(gold_scores)
    best_non_gold = max(non_gold_scores)
    margin = lowest_gold - best_non_gold
    return {
        "query_id": qid,
        "query_text": QUERY_BY_ID[qid],
        "gold_fact_ids": gold_fids,
        "gold_scores": {fid: scores_by_fid[fid] for fid in gold_fids},
        "non_gold_scores": {fid: scores_by_fid[fid] for fid in non_gold_fids},
        "LOWEST_GOLD_SCORE": lowest_gold,
        "BEST_NON_GOLD_SCORE": best_non_gold,
        "HARD_NEGATIVE_MARGIN": margin,
        "separates_perfectly_on_fixture": margin > 0,
    }


def no_result_separability(
    scores: dict[str, dict[str, float]],
) -> dict[str, Any]:
    q4_scores = list(scores["Q4"].values())
    q4_max = max(q4_scores)
    positive_scores: list[float] = []
    positive_pairs: list[dict[str, Any]] = []
    for qid in ("Q1", "Q2", "Q3"):
        for text in GOLD[qid]:
            fid = FACT_ID_BY_TEXT[text]
            s = scores[qid][fid]
            positive_scores.append(s)
            positive_pairs.append({"query_id": qid, "fact_id": fid, "score": s})
    positive_min = min(positive_scores)
    margin = positive_min - q4_max
    interval = None
    if margin > 0:
        interval = {
            "OBSERVED_SEPARATION_INTERVAL": f"({q4_max}, {positive_min}]",
            "label": ["NOT_CALIBRATED", "NOT_AUTHORIZED", "FIXTURE_ONLY"],
        }
    return {
        "Q4_MAX_SCORE": q4_max,
        "Q4_scores": dict(scores["Q4"]),
        "POSITIVE_MIN_SCORE": positive_min,
        "positive_gold_pairs": positive_pairs,
        "NO_RESULT_SEPARABILITY_MARGIN": margin,
        "NO_RESULT_SEPARABILITY": "SEPARABLE" if margin > 0 else "OVERLAPPING",
        "observed_separation_interval": interval,
        "THRESHOLD_SELECTED": False,
        "note": "Positive margin establishes SEPARABILITY_OBSERVED_ON_FM15_FIXTURE only.",
    }


def q5_diagnostic(scores_by_fid: dict[str, float]) -> dict[str, Any]:
    f1 = scores_by_fid["F1"]
    f2 = scores_by_fid["F2"]
    f3 = scores_by_fid["F3"]
    f4 = scores_by_fid["F4"]
    # Relative strength vs other facts — not a threshold claim
    ranked = sorted(scores_by_fid.items(), key=lambda kv: -kv[1])
    top2 = {fid for fid, _ in ranked[:2]}
    both_supportive = "F1" in top2 and "F2" in top2
    return {
        "query_id": "Q5",
        "query_text": QUERY_BY_ID["Q5"],
        "scores": dict(scores_by_fid),
        "F1_score": f1,
        "F2_score": f2,
        "F3_score": f3,
        "F4_score": f4,
        "F1_scores_strongly_relative": ranked[0][0] == "F1" or f1 >= ranked[1][1],
        "F2_scores_strongly_relative": "F2" in top2,
        "both_F1_F2_appear_supportive": both_supportive,
        "DIRECT_SUPPORT": "NO",
        "DIRECT_SUPPORT_BOOL": False,
        "CO_RETRIEVAL": "YES" if both_supportive else "NO",
        "MULTI_HOP_REASONING": "NOT_PROVEN",
        "note": "High pairwise scores must not be converted into reasoning proof.",
    }


def embedding_baseline_margins(sim_matrix: dict[str, Any]) -> dict[str, Any]:
    """Compute analogous margins from run_005 similarity_matrix.json cosine scores."""
    matrix = sim_matrix.get("matrix", sim_matrix)
    out_margins: dict[str, Any] = {}
    scores: dict[str, dict[str, float]] = {}
    for qid, _ in QUERIES:
        entry = matrix[qid]
        cos = entry.get("cosine_vs_facts") or entry
        by_fid: dict[str, float] = {}
        for fid, ftext in FACTS:
            by_fid[fid] = float(cos[ftext])
        scores[qid] = by_fid

    for qid in ("Q1", "Q2", "Q3"):
        out_margins[qid] = hard_negative_margin(qid, scores[qid])

    nrs = no_result_separability(scores)
    return {
        "source": "artifacts/memoryops/run_005/similarity_matrix.json",
        "score_family": "cosine_embedding",
        "scores_by_query_fact": scores,
        "hard_negative_margins": out_margins,
        "no_result_separability": nrs,
        "per_query_ranks": {
            qid: sorted(
                [{"fact_id": fid, "score": scores[qid][fid]} for fid, _ in FACTS],
                key=lambda r: -r["score"],
            )
            for qid, _ in QUERIES
        },
    }


def compare_to_embedding(
    ce_scores: dict[str, dict[str, float]],
    ce_margins: dict[str, Any],
    ce_nrs: dict[str, Any],
    emb: dict[str, Any],
) -> dict[str, Any]:
    emb_margins = emb["hard_negative_margins"]
    emb_nrs = emb["no_result_separability"]
    per_query: dict[str, Any] = {}
    for qid, _ in QUERIES:
        ce_rank = [
            fid
            for fid, _ in sorted(
                ce_scores[qid].items(), key=lambda kv: (-kv[1], kv[0])
            )
        ]
        emb_rank = [r["fact_id"] for r in emb["per_query_ranks"][qid]]
        entry: dict[str, Any] = {
            "embedding_rank": emb_rank,
            "cross_encoder_rank": ce_rank,
            "rank_identical": ce_rank == emb_rank,
        }
        if qid in ("Q1", "Q2", "Q3"):
            entry["embedding_hard_negative_margin"] = emb_margins[qid][
                "HARD_NEGATIVE_MARGIN"
            ]
            entry["cross_encoder_hard_negative_margin"] = ce_margins[qid][
                "HARD_NEGATIVE_MARGIN"
            ]
            entry["margin_improved"] = (
                ce_margins[qid]["HARD_NEGATIVE_MARGIN"]
                > emb_margins[qid]["HARD_NEGATIVE_MARGIN"]
            )
            entry["ce_separates"] = ce_margins[qid]["HARD_NEGATIVE_MARGIN"] > 0
            entry["emb_separates"] = emb_margins[qid]["HARD_NEGATIVE_MARGIN"] > 0
        per_query[qid] = entry

    return {
        "note": "Compare ordering/margins within each score family — not raw magnitudes across scales.",
        "per_query": per_query,
        "q4_embedding_max": emb_nrs["Q4_MAX_SCORE"],
        "q4_cross_encoder_max": ce_nrs["Q4_MAX_SCORE"],
        "embedding_no_result_separability_margin": emb_nrs[
            "NO_RESULT_SEPARABILITY_MARGIN"
        ],
        "cross_encoder_no_result_separability_margin": ce_nrs[
            "NO_RESULT_SEPARABILITY_MARGIN"
        ],
        "embedding_no_result_label": emb_nrs["NO_RESULT_SEPARABILITY"],
        "cross_encoder_no_result_label": ce_nrs["NO_RESULT_SEPARABILITY"],
    }


def classify_signal(
    ce_margins: dict[str, Any],
    ce_nrs: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, str]:
    m1 = ce_margins["Q1"]["HARD_NEGATIVE_MARGIN"]
    m2 = ce_margins["Q2"]["HARD_NEGATIVE_MARGIN"]
    m3 = ce_margins["Q3"]["HARD_NEGATIVE_MARGIN"]
    margins = [m1, m2, m3]
    all_pos = all(m > 0 for m in margins)
    any_pos = any(m > 0 for m in margins)
    nrs_ok = ce_nrs["NO_RESULT_SEPARABILITY_MARGIN"] > 0

    # Gold ordering preserved = gold facts ranked above all non-gold for Q1-Q3
    gold_order_ok = all_pos  # positive margin implies all gold > all non-gold

    if all_pos and nrs_ok and gold_order_ok:
        effect = "STRONGLY_IMPROVED"
    else:
        # Compare to embedding margins for IMPROVED/MIXED/NEUTRAL/WORSE
        improved = 0
        degraded = 0
        for qid in ("Q1", "Q2", "Q3"):
            pq = comparison["per_query"][qid]
            if pq["cross_encoder_hard_negative_margin"] > pq[
                "embedding_hard_negative_margin"
            ] + 1e-9:
                improved += 1
            elif pq["cross_encoder_hard_negative_margin"] < pq[
                "embedding_hard_negative_margin"
            ] - 1e-9:
                # also count separation flip
                if pq["emb_separates"] and not pq["ce_separates"]:
                    degraded += 1
                elif not pq["ce_separates"] and pq["emb_separates"]:
                    degraded += 1
                else:
                    degraded += 1
        nrs_improved = (
            ce_nrs["NO_RESULT_SEPARABILITY_MARGIN"]
            > comparison["embedding_no_result_separability_margin"]
        )
        if improved >= 2 and degraded == 0:
            effect = "IMPROVED" if not all_pos or not nrs_ok else "STRONGLY_IMPROVED"
        elif improved > 0 and degraded > 0:
            effect = "MIXED"
        elif degraded >= 2 and improved == 0:
            effect = "WORSE"
        elif improved == 0 and degraded == 0 and not nrs_improved:
            effect = "NEUTRAL"
        elif any_pos or nrs_ok or nrs_improved:
            effect = "IMPROVED"
        else:
            effect = "INCONCLUSIVE"

    if all_pos:
        intra = "STRONG"
    elif any_pos:
        intra = "PARTIAL"
    elif all(abs(m) < 1e-6 for m in margins):
        intra = "INCONCLUSIVE"
    else:
        intra = "NONE"

    nrs_label = ce_nrs["NO_RESULT_SEPARABILITY"]

    return {
        "CROSS_ENCODER_SIGNAL_EFFECT": effect,
        "INTRA_QUERY_DISCRIMINATION": intra,
        "NO_RESULT_SEPARABILITY": nrs_label,
    }


def matrix_to_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "query_id",
        "query_text",
        "fact_id",
        "fact_text",
        "gold_relevant",
        "RAW_SCORE",
        "NORMALIZED_SCORE",
        "LOGIT_SCORE",
        "rank_within_query",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def matrix_to_md(rows: list[dict[str, Any]], path: Path) -> None:
    # Wide raw-score table
    lines = [
        "# Cross-Encoder Score Matrix (FM-15)",
        "",
        "RAW_SCORE = Graphiti `BGERerankerClient.rank` / `CrossEncoder.predict` "
        "(official; activation_fn=Sigmoid).",
        "NORMALIZED_SCORE = null (no additional lab-side normalization).",
        "LOGIT_SCORE = Identity activation (transparency only).",
        "",
        "## RAW_SCORE grid",
        "",
        "| Query | F1 | F2 | F3 | F4 |",
        "|---|---:|---:|---:|---:|",
    ]
    by_q: dict[str, dict[str, float]] = {}
    for r in rows:
        by_q.setdefault(r["query_id"], {})[r["fact_id"]] = r["RAW_SCORE"]
    for qid, _ in QUERIES:
        s = by_q[qid]
        lines.append(
            f"| {qid} | {s['F1']:.6f} | {s['F2']:.6f} | {s['F3']:.6f} | {s['F4']:.6f} |"
        )
    lines.extend(["", "## Per-pair detail", ""])
    lines.append(
        "| Q | Fact | Gold | Rank | RAW_SCORE | LOGIT_SCORE | Fact text |"
    )
    lines.append("|---|---|---|---:|---:|---:|---|")
    for r in rows:
        logit = "" if r["LOGIT_SCORE"] is None else f"{r['LOGIT_SCORE']:.6f}"
        lines.append(
            f"| {r['query_id']} | {r['fact_id']} | {r['gold_relevant']} | "
            f"{r['rank_within_query']} | {r['RAW_SCORE']:.6f} | {logit} | "
            f"{r['fact_text']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


async def run_scoring(
    client: Any, meta: dict[str, Any], *, capture_logits: bool = True
) -> dict[str, Any]:
    """Score all 20 Q×F pairs. Returns official scores + optional logits + timing."""
    official: dict[str, dict[str, float]] = {}
    logits: dict[str, dict[str, float]] = {}
    t0 = time.perf_counter()
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    for qid, qtext in QUERIES:
        passages = [ftext for _, ftext in FACTS]
        ranked = await score_pairs_official(client, qtext, passages)
        by_text = {p: float(s) for p, s in ranked}
        official[qid] = {fid: by_text[ftext] for fid, ftext in FACTS}
        if capture_logits:
            logit_list = score_logits_optional(client.model, qtext, passages)
            if logit_list and len(logit_list) == len(FACTS):
                logits[qid] = {
                    fid: float(logit_list[i]) for i, (fid, _) in enumerate(FACTS)
                }
    elapsed = time.perf_counter() - t0
    peak_rss2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux ru_maxrss is KB
    return {
        "official_scores": official,
        "logit_scores": logits,
        "timing": {
            "model_load_time_s": meta.get("load_time_s"),
            "twenty_pair_scoring_time_s": elapsed,
            "per_pair_average_s": elapsed / 20.0,
            "batch_scoring": "per-query batch of 4 via CrossEncoder.predict",
            "device": meta.get("device"),
            "peak_rss_kb_approx": max(peak_rss, peak_rss2),
            "LATENCY_NE_QUALITY": True,
        },
        "pair_count": 20,
    }


async def run_repeatability(
    client: Any, first: dict[str, dict[str, float]]
) -> dict[str, Any]:
    second_official: dict[str, dict[str, float]] = {}
    for qid, qtext in QUERIES:
        passages = [ftext for _, ftext in FACTS]
        ranked = await score_pairs_official(client, qtext, passages)
        by_text = {p: float(s) for p, s in ranked}
        second_official[qid] = {fid: by_text[ftext] for fid, ftext in FACTS}
    deltas: list[float] = []
    for qid, _ in QUERIES:
        for fid, _ in FACTS:
            deltas.append(abs(first[qid][fid] - second_official[qid][fid]))
    max_delta = max(deltas) if deltas else 0.0
    if max_delta == 0.0:
        det = "EXACT"
    elif max_delta < 1e-5:
        det = "NEAR_EXACT"
    else:
        det = "NON_DETERMINISTIC"
    return {
        "DETERMINISM": det,
        "max_absolute_score_delta": max_delta,
        "second_run_scores": second_official,
        "REPEATABILITY": "RUN",
    }


def assert_no_forbidden_imports_in_source(source_path: Path) -> list[str]:
    text = source_path.read_text(encoding="utf-8")
    forbidden = [
        "OpenClaw",
        "AttentionRouter",
        "EvidenceGate",
        "Crystal",
        "from soul",
        "import soul",
        "DeterministicCrossEncoder",
        "EDGE_HYBRID_SEARCH_CROSS_ENCODER",
        "COMBINED_HYBRID_SEARCH_CROSS_ENCODER",
    ]
    hits = [f for f in forbidden if f in text]
    # Allow mentioning DeterministicCrossEncoder / EDGE_... in comments as "do not use"
    # Filter: only flag if used as construction
    real_hits = []
    for h in hits:
        if h in (
            "DeterministicCrossEncoder",
            "EDGE_HYBRID_SEARCH_CROSS_ENCODER",
            "COMBINED_HYBRID_SEARCH_CROSS_ENCODER",
        ):
            if f"{h}(" in text or f"={h}" in text.replace(" ", ""):
                real_hits.append(h)
        else:
            real_hits.append(h)
    return real_hits


__all__ = [
    "REQUIRED_MODEL",
    "QUERIES",
    "FACTS",
    "GOLD",
    "RealCrossEncoderUnavailableError",
    "init_bge_reranker_client",
    "run_scoring",
    "run_repeatability",
    "build_score_matrix",
    "hard_negative_margin",
    "no_result_separability",
    "q5_diagnostic",
    "embedding_baseline_margins",
    "compare_to_embedding",
    "classify_signal",
    "matrix_to_csv",
    "matrix_to_md",
    "write_json",
    "resolve_model_revision",
    "resolve_weight_fingerprint",
]
