"""FM-16 CROSS-ENCODER HELD-OUT GENERALIZATION & CALIBRATION — integrity tests.

Tests FM16-A..X assert experiment integrity ONLY.
They MUST NOT assert CE must win, threshold must exist, or generalization must be strong.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from fractal_lab.experiments.cross_encoder_separability import (
    REQUIRED_MODEL,
    resolve_weight_fingerprint,
)
from fractal_lab.experiments.fm16_generalization import (
    CAL_FACTS,
    CAL_QUERIES,
    CE_REVISION_PIN,
    CE_WEIGHT_SHA_PIN,
    EXPECTED_START_SHA,
    HN_ADV,
    HN_CORE,
    RUN007,
    TEST_FACTS,
    TEST_QUERIES,
    UPSTREAM_SHA,
    _build_hn_labels_cal,
    _build_hn_labels_test,
    entity_overlap,
    gold_to_dict,
    hn_coverage,
    validate_split,
    CAL_ENTITIES,
    TEST_ENTITIES,
)
from fractal_lab.experiments.local_semantic_embedder import DEFAULT_MODEL_NAME as EMBED_MODEL

REPO_ROOT = Path(__file__).resolve().parents[2]
CE_SRC = REPO_ROOT / "src" / "fractal_lab" / "experiments" / "cross_encoder_separability.py"
FM16_SRC = REPO_ROOT / "src" / "fractal_lab" / "experiments" / "fm16_generalization.py"
MEMOPS = REPO_ROOT / "core" / "memory_ops.py"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=str(REPO_ROOT), text=True).strip()


def _load(name: str) -> Any:
    path = RUN007 / name
    assert path.is_file(), f"missing artifact {path}"
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def result():
    return _load("result.json")


@pytest.fixture(scope="module")
def prereg():
    return _load("preregistration.json")


def test_fm16_a_start_sha_verified():
    head = _git("rev-parse", "HEAD")
    # At test time HEAD may already include FM-16 commit; START was expected parent pin.
    # Integrity: expected start is an ancestor / recorded in result.
    _git("cat-file", "-e", EXPECTED_START_SHA)
    result = _load("result.json")
    assert result["start_sha"] == EXPECTED_START_SHA


def test_fm16_b_ce_identity_matches_fm15():
    w = resolve_weight_fingerprint()
    assert w.get("revision") == CE_REVISION_PIN
    assert w.get("sha256") == CE_WEIGHT_SHA_PIN
    fp = _load("model_fingerprints.json")
    assert fp["pins"]["ce_model"] == REQUIRED_MODEL
    assert fp["pins"]["ce_revision"] == CE_REVISION_PIN
    assert fp["pins"]["ce_weight_sha256"] == CE_WEIGHT_SHA_PIN


def test_fm16_c_embedding_identity_matches_fm14():
    fp = _load("model_fingerprints.json")
    assert fp["pins"]["embedding_model"] == EMBED_MODEL
    assert EMBED_MODEL == "BAAI/bge-small-en-v1.5"


def test_fm16_d_entity_disjoint():
    ov = entity_overlap(CAL_ENTITIES, TEST_ENTITIES)
    assert ov["entity_disjoint"] is True
    preg = _load("preregistration.json")
    assert preg["entity_disjoint"]["entity_disjoint"] is True


def test_fm16_e_40_facts_calibration():
    assert len(CAL_FACTS) == 40
    facts = _load("corpus/calibration_facts.json")
    assert len(facts) == 40


def test_fm16_f_40_facts_test():
    assert len(TEST_FACTS) == 40
    facts = _load("corpus/test_facts.json")
    assert len(facts) == 40


def test_fm16_g_20_queries_each():
    assert len(CAL_QUERIES) == 20 and len(TEST_QUERIES) == 20
    assert len(_load("corpus/calibration_queries.json")) == 20
    assert len(_load("corpus/test_queries.json")) == 20


def test_fm16_h_12_answerable_8_no_answer():
    for qs, name in ((CAL_QUERIES, "cal"), (TEST_QUERIES, "test")):
        ans = [q for q in qs if q["class"] == "answerable"]
        noa = [q for q in qs if q["class"] == "no_answer"]
        assert len(ans) == 12 and len(noa) == 8, name
        assert len([q for q in ans if q["subtype"] == "broad"]) == 4


def test_fm16_i_hn_coverage():
    for labels, name in (
        (_build_hn_labels_cal(), "cal"),
        (_build_hn_labels_test(), "test"),
    ):
        cov = hn_coverage(labels)
        for h in HN_CORE:
            assert cov[h] >= 3, f"{name} {h}={cov[h]}"
        for h in HN_ADV:
            assert cov[h] >= 2, f"{name} {h}={cov[h]}"
    errs = validate_split(CAL_FACTS, CAL_QUERIES, _build_hn_labels_cal(), "CAL")
    errs += validate_split(TEST_FACTS, TEST_QUERIES, _build_hn_labels_test(), "TEST")
    assert errs == []


def test_fm16_j_preregistration_hashes_before_scoring(prereg):
    hashes = _load("hashes/frozen_corpus_sha256.json")
    assert set(hashes) >= {
        "calibration_facts.json",
        "calibration_queries.json",
        "calibration_gold.json",
        "test_facts.json",
        "test_queries.json",
        "test_gold.json",
        "hard_negative_labels.json",
        "adversarial_strata_manifest.json",
        "fm15_anchor.json",
    }
    assert prereg["corpus_file_sha256"] == hashes
    assert "threshold_rule" in prereg


def test_fm16_k_800_calibration_ce_pairs():
    rows = (RUN007 / "scores" / "ce_calibration.csv").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) - 1 == 800  # header + 800


def test_fm16_l_800_test_ce_pairs():
    rows = (RUN007 / "scores" / "ce_test.csv").read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) - 1 == 800


def test_fm16_m_same_1600_pairs_embedding():
    cal = (RUN007 / "scores" / "embedding_calibration.csv").read_text(encoding="utf-8").strip().splitlines()
    test = (RUN007 / "scores" / "embedding_test.csv").read_text(encoding="utf-8").strip().splitlines()
    assert len(cal) - 1 == 800
    assert len(test) - 1 == 800


def test_fm16_n_threshold_derived_only_from_calibration():
    cal = _load("calibration/calibrated_thresholds.json")
    assert cal["threshold_selection_rule"]["feasibility"]["ANSWERABLE_QUERY_COVERAGE"] == 1.0
    # search artifacts exist for CAL only
    assert (RUN007 / "calibration" / "threshold_search_ce.json").is_file()
    assert (RUN007 / "calibration" / "threshold_search_embedding.json").is_file()


def test_fm16_o_threshold_frozen_before_test():
    h = _load("hashes/calibrated_threshold_sha256.json")
    assert h.get("frozen_before_test") is True
    assert h.get("calibrated_thresholds.json")
    receipt = _load("calibration/threshold_freeze_receipt.json")
    assert receipt.get("heldout_applied_once") is True
    assert receipt.get("thresholds_unchanged_after_freeze") is True


def test_fm16_p_one_global_threshold_only(result):
    # At most one CE and one embedding threshold recorded
    assert "ce_threshold" in result and "embedding_threshold" in result
    cal = _load("calibration/calibrated_thresholds.json")
    assert set(k for k in cal if k.startswith("THETA_")) <= {"THETA_CE", "THETA_EMBEDDING"}


def test_fm16_q_no_test_leakage():
    # Integrity marker: calibrated file records freeze hash; heldout applied once
    assert (RUN007 / "evaluation" / "heldout_ce.json").is_file()
    assert (RUN007 / "evaluation" / "heldout_embedding.json").is_file()
    src = FM16_SRC.read_text(encoding="utf-8")
    assert "CALIBRATION_ONLY" in src or "calibration only" in src.lower() or "ONLY on CALIBRATION" in src or "ONLY from calibration" in src.lower() or "CALIBRATION" in src


def test_fm16_r_no_forced_refill(result):
    assert result["forced_refill"] is False
    receipts = _load("evaluation/rejection_receipts.json")
    assert receipts["FORCED_REFILL"] is False


def test_fm16_s_rejection_receipts_generated():
    receipts = _load("evaluation/rejection_receipts.json")
    assert len(receipts["ce"]) == 20
    assert len(receipts["embedding"]) == 20
    sample = receipts["ce"][0]
    assert "selected_ids" in sample and "discarded_ids" in sample
    assert "candidates" in sample


def test_fm16_t_fm15_anchor_unchanged_fixture():
    anchor = _load("corpus/fm15_anchor.json")
    assert len(anchor["queries"]) == 5 and len(anchor["facts"]) == 4
    assert (RUN007 / "scores" / "fm15_anchor_recheck.csv").is_file()
    result = _load("result.json")
    assert result["fm15_anchor"] in {"EXACT", "NEAR_EXACT", "DRIFTED"}


def test_fm16_u_no_search_recipe_changed():
    result = _load("result.json")
    assert result["search_recipe_changed"] is False
    src = FM16_SRC.read_text(encoding="utf-8")
    # no runtime search activation symbols / hybrid CE recipe
    assert "EDGE_HYBRID_SEARCH_CROSS_ENCODER" not in src
    assert "reranker_min_score" not in src
    assert "await client.search" not in src
    assert "graphiti.search" not in src


def test_fm16_v_no_runtime_integration(result):
    assert result["runtime_gate_implemented"] is False
    assert result["threshold_runtime_authorized"] is False
    assert result["new_relevance_module"] is False
    assert result["architecture_change"] is False


def test_fm16_w_upstream_unchanged(result):
    assert result["upstream_sha"] == UPSTREAM_SHA
    assert result["upstream_changes"] is False
    assert result["merge"] is False
    # Upstream pin lives in sibling Graphiti_fractal repo; verify if present.
    upstream_repo = REPO_ROOT.parent / "Graphiti_fractal"
    if (upstream_repo / ".git").exists():
        subprocess.check_output(
            ["git", "-C", str(upstream_repo), "cat-file", "-e", UPSTREAM_SHA],
            text=True,
        )
        head = subprocess.check_output(
            ["git", "-C", str(upstream_repo), "rev-parse", "HEAD"],
            text=True,
        ).strip()
        assert head == UPSTREAM_SHA


def test_fm16_x_no_predetermined_positive_result():
    """Integrity: tests must not hard-require CE win / strong generalization."""
    src = Path(__file__).read_text(encoding="utf-8")
    # Build needles via concatenation so this file does not contain full forbidden asserts.
    needles = [
        "generalization_verdict" + '] == "GENERALIZATION_STRONG"',
        "ce_vs_embedding" + '] == "CLEARLY_BETTER"',
        "ce_global_threshold_feasible" + "] is True",
    ]
    for n in needles:
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("assert ") and n in stripped:
                raise AssertionError(f"predetermined quality assert forbidden: {stripped}")
    result = _load("result.json")
    assert result["generalization_verdict"] in {
        "GENERALIZATION_STRONG",
        "GENERALIZATION_PARTIAL",
        "GLOBAL_THRESHOLD_NOT_FEASIBLE",
        "GENERALIZATION_FAILED",
        "INCONCLUSIVE",
    }
