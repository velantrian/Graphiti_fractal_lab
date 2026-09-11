"""FM-17-pre v1.3 fail-closed schema + package integrity enforcement.

TEST_FIXTURE / EXAMPLE_NOT_GOLD only. Does not annotate CAL/TEST.
Does not compute relevance / A0–A3 metrics.
Adds T19–T26 / P5–P6 (v1.3) and T27–T29 / P7 external freeze anchor (v1.3.1).
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/research/fm17_pre"
sys.path.insert(0, str(DOC))

spec = importlib.util.spec_from_file_location(
    "validate_fm17_pre_package", DOC / "validate_fm17_pre_package.py"
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

HEX64 = "a" * 64


def P(
    source_type="RAW_QUERY_TEXT",
    span="Project Nimbus",
    rule=None,
    annotator="annotator_A",
    blind="BLINDED_TO_GOLD_AND_HN",
    adj="AGREED",
    adjudicator=None,
):
    d = {
        "source_type": source_type,
        "source_span": span,
        "rule_id": rule,
        "annotator_id": annotator,
        "adjudicator_id": adjudicator,
        "blinding_status": blind,
        "adjudication_status": adj,
    }
    return d


def AV(value, **kw):
    return {"value": value, "provenance": P(**kw)}


def valid_structural_p1() -> dict:
    """P1 — blinded raw-text STRUCTURAL record."""
    return {
        "pair_id": "EX_Q_NARROW::EX_F_WORKS",
        "query_id": "EX_Q_NARROW",
        "fact_id": "EX_F_WORKS",
        "record_layer": "STRUCTURAL",
        "query": {
            "entity_targets": AV(["Project Nimbus"], span="Project Nimbus"),
            "predicate_target": AV(
                "works_on", span="Who works on", rule="RB_PRED_WORKS_ON", source_type="FIXED_RULE"
            ),
            "scope_target": AV("any", source_type="FIXED_RULE", span=None, rule="RB_SCOPE_UNSPECIFIED_TO_ANY"),
            "temporal_target": AV("any", source_type="FIXED_RULE", span=None, rule="RB_TEMPORAL_UNSPECIFIED_TO_ANY"),
            "polarity_target": AV("affirmative", span="Who works on"),
            "condition_target": AV(None, source_type="FIXED_RULE", span=None, rule="RB_CONDITION_UNSPECIFIED"),
            "attribution_target": AV(None, source_type="FIXED_RULE", span=None, rule="RB_ATTRIB_UNSPECIFIED"),
            "query_class": AV("NARROW", span="Who works on Project Nimbus?"),
            "role_target": AV({"subject": None, "object": "Project Nimbus"}, span="Who works on Project Nimbus?"),
        },
        "fact": {
            "entities": AV(
                ["Sofia", "Project Nimbus"],
                source_type="RAW_FACT_TEXT",
                span="Sofia works on Project Nimbus.",
            ),
            "predicate": AV("works_on", source_type="RAW_FACT_TEXT", span="works on"),
            "scope": AV("default", source_type="FIXED_RULE", span=None, rule="RB_SCOPE_NO_MARKER_DEFAULT"),
            "polarity": AV("affirmative", source_type="RAW_FACT_TEXT", span="works on"),
            "condition": AV(None, source_type="FIXED_RULE", span=None, rule="RB_CONDITION_UNSPECIFIED"),
            "attribution": AV(None, source_type="FIXED_RULE", span=None, rule="RB_ATTRIB_UNSPECIFIED"),
            "temporal_state": AV("current", source_type="FIXED_RULE", span=None, rule="RB_TEMPORAL_NO_MARKER_CURRENT"),
            "role": AV(
                {"subject": "Sofia", "object": "Project Nimbus"},
                source_type="RAW_FACT_TEXT",
                span="Sofia works on Project Nimbus.",
            ),
        },
        "annotation_comment": {"reason_code": "OTHER_NON_OUTCOME_REASON", "comment": "EXAMPLE_NOT_GOLD"},
    }


def valid_fixed_rule_p2() -> dict:
    rec = valid_structural_p1()
    rec["query"]["scope_target"] = AV(
        "any", source_type="FIXED_RULE", span=None, rule="RB_SCOPE_UNSPECIFIED_TO_ANY"
    )
    return rec


def valid_receipt(**over) -> dict:
    base = {
        "annotation_schema_version": "1.2",
        "rulebook_version": "v1.2",
        "sanitized_input_hash": HEX64,
        "ontology_schema_hash": HEX64,
        "annotation_schema_hash": HEX64,
        "rulebook_hash": HEX64,
        "query_corpus_hash": HEX64,
        "fact_corpus_hash": HEX64,
        "annotation_A_hash": HEX64,
        "annotation_B_hash": HEX64,
        "disagreement_log_hash": None,
        "adjudicated_annotation_hash": None,
        "final_structural_package_hash": HEX64,
        "annotator_A_id": "annotator_A",
        "annotator_B_id": "annotator_B",
        "adjudicator_id": None,
        "blinding": {
            "gold_access": False,
            "hn_access": False,
            "ce_score_access": False,
            "ce_rank_access": False,
            "embedding_score_access": False,
            "embedding_rank_access": False,
            "other_annotator_access_before_submission": False,
            "evaluation_split_identity_access": False,
        },
        "gold_access": False,
        "hn_access": False,
        "ce_score_access": False,
        "embedding_score_access": False,
        "evaluation_overlay_access": False,
        "independent_annotation_available": True,
        "annotation_started_at": "2026-09-11T00:00:00Z",
        "annotation_frozen_at": "2026-09-11T00:00:01Z",
        "disagreement_count": 0,
        "adjudicated_count": 0,
        "post_freeze_amendments": [],
    }
    base.update(over)
    return base


def valid_adjudicated_receipt() -> dict:
    return valid_receipt(
        disagreement_count=1,
        adjudicated_count=1,
        adjudicator_id="adjudicator_1",
        disagreement_log_hash=HEX64,
        adjudicated_annotation_hash=HEX64,
    )


def expect_fail(errs: list[str], code: str) -> None:
    assert errs, f"{code}: expected FAIL, got PASS"
    return None


def expect_pass(errs: list[str], code: str) -> None:
    assert not errs, f"{code}: expected PASS, got {errs}"


# ----- T1–T18 -----


def test_T1_structural_not_blinded_fails():
    rec = valid_structural_p1()
    rec["query"]["entity_targets"]["provenance"]["blinding_status"] = "NOT_BLINDED"
    expect_fail(mod.validate_structural_record(rec), "T1")


def test_T2_structural_unknown_blinding_fails():
    rec = valid_structural_p1()
    rec["query"]["entity_targets"]["provenance"]["blinding_status"] = "UNKNOWN"
    expect_fail(mod.validate_structural_record(rec), "T2")


def test_T3_fixed_rule_without_rule_id_fails():
    rec = valid_structural_p1()
    rec["query"]["scope_target"]["provenance"]["source_type"] = "FIXED_RULE"
    rec["query"]["scope_target"]["provenance"]["rule_id"] = None
    rec["query"]["scope_target"]["provenance"]["source_span"] = None
    expect_fail(mod.validate_structural_record(rec), "T3")


def test_T4_raw_fact_text_without_source_span_fails():
    rec = valid_structural_p1()
    rec["fact"]["entities"]["provenance"]["source_type"] = "RAW_FACT_TEXT"
    rec["fact"]["entities"]["provenance"]["source_span"] = ""
    expect_fail(mod.validate_structural_record(rec), "T4")


def test_T5_human_annotation_without_annotator_id_fails():
    rec = valid_structural_p1()
    rec["query"]["query_class"]["provenance"]["source_type"] = "HUMAN_ANNOTATION"
    rec["query"]["query_class"]["provenance"]["annotator_id"] = None
    rec["query"]["query_class"]["provenance"]["source_span"] = "Who works"
    expect_fail(mod.validate_structural_record(rec), "T5")


def test_T6_adjudicated_without_adjudicator_fails():
    rec = valid_structural_p1()
    rec["query"]["predicate_target"]["provenance"]["source_type"] = "ADJUDICATED"
    rec["query"]["predicate_target"]["provenance"]["adjudication_status"] = "ADJUDICATED"
    rec["query"]["predicate_target"]["provenance"]["annotator_id"] = "annotator_A"
    rec["query"]["predicate_target"]["provenance"]["adjudicator_id"] = None
    rec["query"]["predicate_target"]["provenance"]["rule_id"] = "RB_PRED_WORKS_ON"
    expect_fail(mod.validate_structural_record(rec), "T6")


def test_T7_gold_access_true_fails():
    r = valid_receipt(gold_access=True)
    expect_fail(mod.validate_receipt(r), "T7")


def test_T8_hn_access_true_fails():
    r = valid_receipt(hn_access=True)
    expect_fail(mod.validate_receipt(r), "T8")


def test_T9_ce_score_access_true_fails():
    r = valid_receipt(ce_score_access=True)
    expect_fail(mod.validate_receipt(r), "T9")


def test_T10_embedding_score_access_true_fails():
    r = valid_receipt(embedding_score_access=True)
    expect_fail(mod.validate_receipt(r), "T10")


def test_T11_sanitized_split_test_fails():
    obj = {
        "query_id": "EX_Q",
        "fact_id": "EX_F",
        "query_text": "Who works on Project Nimbus?",
        "fact_text": "Sofia works on Project Nimbus.",
        "split": "TEST",
    }
    expect_fail(mod.validate_sanitized_input(obj), "T11")


def test_T12_structural_gold_relevance_class_fails():
    rec = valid_structural_p1()
    rec["gold_relevance_class"] = "DIRECT"
    expect_fail(mod.validate_structural_record(rec), "T12")


def test_T13_structural_hn_labels_fails():
    rec = valid_structural_p1()
    rec["hn_labels"] = ["HN9"]
    expect_fail(mod.validate_structural_record(rec), "T13")


def test_T14_disagreement_without_adjudicator_fails():
    r = valid_receipt(disagreement_count=1, adjudicated_count=1, adjudicator_id=None)
    expect_fail(mod.validate_receipt(r), "T14")


def test_T15_disagreement_count_mismatch_fails():
    r = valid_adjudicated_receipt()
    r["adjudicated_count"] = 0
    expect_fail(mod.validate_receipt(r), "T15")


def test_T16_amendment_after_scoring_not_invalidated_fails():
    am = {
        "amendment_id": "am1",
        "timestamp": "2026-09-11T01:00:00Z",
        "previous_package_hash": HEX64,
        "new_package_hash": "b" * 64,
        "reason_code": "TRANSCRIPTION_ERROR",
        "reason_text": "typo",
        "changed_fields": ["fact.scope"],
        "affected_record_ids": ["EX_Q_NARROW::EX_F_WORKS"],
        "authorized_by": "adjudicator_1",
        "scoring_started": True,
        "invalidation_required": False,
        "previous_result_invalidated": False,
        "new_version": "1.2.1",
    }
    r = valid_receipt(post_freeze_amendments=[am])
    expect_fail(mod.validate_receipt(r), "T16")


def test_T17_same_annotator_a_and_b_fails():
    r = valid_receipt(annotator_A_id="annotator_A", annotator_B_id="annotator_A")
    expect_fail(mod.validate_receipt(r), "T17")


def test_T18_broad_narrow_scope_without_span_or_rule_fails():
    rec = valid_structural_p1()
    rec["query"]["query_class"] = AV("BROAD", span="What components are associated with")
    rec["query"]["scope_target"] = AV(
        "prod", source_type="HUMAN_ANNOTATION", span="", rule=None, annotator="annotator_A"
    )
    # empty span + no rule
    rec["query"]["scope_target"]["provenance"]["source_span"] = ""
    rec["query"]["scope_target"]["provenance"]["rule_id"] = None
    expect_fail(mod.validate_structural_record(rec), "T18")


def test_P1_valid_blinded_raw_text_passes():
    expect_pass(mod.validate_structural_record(valid_structural_p1()), "P1")


def test_P2_valid_fixed_rule_with_rule_id_passes():
    expect_pass(mod.validate_structural_record(valid_fixed_rule_p2()), "P2")


def test_P3_valid_fully_adjudicated_receipt_passes():
    expect_pass(mod.validate_receipt(valid_adjudicated_receipt()), "P3")


def test_P4_valid_no_disagreement_receipt_passes():
    expect_pass(mod.validate_receipt(valid_receipt()), "P4")


import hashlib
import json
import tempfile
from pathlib import Path as _Path


def _sanitized_one():
    return {
        "query_id": "EX_Q_NARROW",
        "fact_id": "EX_F_WORKS",
        "query_text": "Who works on Project Nimbus?",
        "fact_text": "Sofia works on Project Nimbus.",
    }


def _ann_a():
    return valid_structural_p1()


def _ann_b_agree():
    rec = valid_structural_p1()
    # force annotator_B identity on fields that carry annotator_id
    for path, av in mod.walk_annotated_fields(rec):
        av["provenance"]["annotator_id"] = "annotator_B"
    return rec


def _ann_b_disagree():
    rec = _ann_b_agree()
    # structural value mismatch (integrity compare, not relevance)
    rec["query"]["predicate_target"]["value"] = "owns"
    return rec


def _adjudicated_from_a():
    rec = valid_structural_p1()
    for path, av in mod.walk_annotated_fields(rec):
        av["provenance"]["adjudication_status"] = "ADJUDICATED"
        av["provenance"]["adjudicator_id"] = "adjudicator_1"
        av["provenance"]["source_type"] = "ADJUDICATED"
    return rec


def _disagreement_log_one():
    return [
        {
            "pair_id": "EX_Q_NARROW::EX_F_WORKS",
            "field_path": "query.predicate_target",
            "status": "ADJUDICATED",
            "adjudicator_id": "adjudicator_1",
            "resolution": "keep_A",
        }
    ]


def _apply_hashes_to_receipt(receipt: dict, digests: dict, require_conditional: bool = False) -> dict:
    receipt = copy.deepcopy(receipt)
    receipt["sanitized_input_hash"] = digests["sanitized_inputs"]
    receipt["annotation_A_hash"] = digests["annotation_A"]
    receipt["annotation_B_hash"] = digests["annotation_B"]
    receipt["final_structural_package_hash"] = digests["final_structural_package"]
    # schema/corpus/rulebook: bind to same digests only when files absent — use digest of empty marker
    marker = hashlib.sha256(b"TEST_FIXTURE_NO_EXTERNAL_CORPUS_v1.3").hexdigest()
    for k in (
        "ontology_schema_hash",
        "annotation_schema_hash",
        "rulebook_hash",
        "query_corpus_hash",
        "fact_corpus_hash",
    ):
        receipt[k] = marker
    if require_conditional:
        receipt["disagreement_log_hash"] = digests["disagreement_log"]
        receipt["adjudicated_annotation_hash"] = digests["adjudicated_annotations"]
    else:
        receipt["disagreement_log_hash"] = None
        receipt["adjudicated_annotation_hash"] = None
    return receipt


def build_complete_no_disagreement_package(write_files: bool = False, tmpdir: str | None = None) -> dict:
    """P5 positive control package."""
    pkg: dict = {
        "sanitized_inputs": [_sanitized_one()],
        "annotation_A": [_ann_a()],
        "annotation_B": [_ann_b_agree()],
        "final_structural_package": [_ann_a()],
        "overlay_after_structural_freeze": False,
    }
    if write_files:
        assert tmpdir is not None
        tdir = _Path(tmpdir)
        paths = {}
        for key in ("sanitized_inputs", "annotation_A", "annotation_B", "final_structural_package"):
            fp = tdir / f"{key}.json"
            fp.write_text(json.dumps(pkg[key], sort_keys=True, separators=(",", ":")), encoding="utf-8")
            paths[key] = str(fp)
        pkg["artifact_paths"] = paths

    # provisional receipt for hashing annotation_receipt itself
    provisional = valid_receipt()
    pkg["annotation_receipt"] = provisional
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    # rebuild receipt with real digests then re-hash receipt into manifest
    receipt = _apply_hashes_to_receipt(provisional, materials["artifact_sha256"], False)
    pkg["annotation_receipt"] = receipt
    if write_files:
        rp = _Path(tmpdir) / "annotation_receipt.json"
        rp.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        pkg["artifact_paths"]["annotation_receipt"] = str(rp)
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
    pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    # sync receipt hashes again to final digests (receipt content change changes its own hash)
    receipt = _apply_hashes_to_receipt(provisional, materials["artifact_sha256"], False)
    pkg["annotation_receipt"] = receipt
    if write_files:
        _Path(pkg["artifact_paths"]["annotation_receipt"]).write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
    pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    # final receipt must match final digests of A/B/sanitized/final (not circular on receipt body)
    receipt = _apply_hashes_to_receipt(provisional, materials["artifact_sha256"], False)
    pkg["annotation_receipt"] = receipt
    if write_files:
        _Path(pkg["artifact_paths"]["annotation_receipt"]).write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )
        # receipt file bytes changed → recompute manifest/root once more with updated receipt file
        materials = mod.build_frozen_materials(pkg, require_conditional=False)
        pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
        pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    else:
        materials = mod.build_frozen_materials(pkg, require_conditional=False)
        pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
        pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    return pkg


def build_complete_disagreement_package() -> dict:
    """P6 positive control with real A/B disagreement + adjudication."""
    pkg: dict = {
        "sanitized_inputs": [_sanitized_one()],
        "annotation_A": [_ann_a()],
        "annotation_B": [_ann_b_disagree()],
        "final_structural_package": [_adjudicated_from_a()],
        "adjudicated_annotations": [_adjudicated_from_a()],
        "disagreement_log": _disagreement_log_one(),
        "overlay_after_structural_freeze": False,
    }
    provisional = valid_adjudicated_receipt()
    pkg["annotation_receipt"] = provisional
    materials = mod.build_frozen_materials(pkg, require_conditional=True)
    receipt = _apply_hashes_to_receipt(provisional, materials["artifact_sha256"], True)
    receipt["disagreement_count"] = 1  # will be corrected to computed
    # compute actual disagreement count from A/B
    computed = mod.compute_disagreement_set(pkg["annotation_A"], pkg["annotation_B"])
    receipt["disagreement_count"] = len(computed)
    receipt["adjudicated_count"] = len(computed)
    pkg["annotation_receipt"] = receipt
    materials = mod.build_frozen_materials(pkg, require_conditional=True)
    receipt = _apply_hashes_to_receipt(provisional, materials["artifact_sha256"], True)
    receipt["disagreement_count"] = len(computed)
    receipt["adjudicated_count"] = len(computed)
    pkg["annotation_receipt"] = receipt
    materials = mod.build_frozen_materials(pkg, require_conditional=True)
    pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
    pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    return pkg




def external_root_of(pkg: dict) -> str:
    """Capture package root as EXTERNAL R0 — must be held outside the package for validation."""
    return pkg["frozen_root_commitment"]["root_sha256"]


def validate_anchored(pkg: dict, expected_frozen_root: str | None = None):
    """Production path: expected root is an external argument, never package-defaulted."""
    if expected_frozen_root is None and isinstance(pkg.get("frozen_root_commitment"), dict):
        # Only for convenience when caller forgot — tests that need absent-anchor must pass None explicitly via validate_package
        expected_frozen_root = external_root_of(pkg)
    return mod.validate_package(pkg, expected_frozen_root=expected_frozen_root)

def test_independent_annotation_false_fails_package():
    """Must fail for independent_annotation=false on a otherwise-complete package."""
    pkg = build_complete_no_disagreement_package()
    pkg["annotation_receipt"]["independent_annotation_available"] = False
    # receipt mutation changes digest → rebuild freeze materials after intentional flag set
    # For this test we want the FAIL reason to include independent_annotation, so rebuild hashes
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["annotation_receipt"] = _apply_hashes_to_receipt(
        pkg["annotation_receipt"], materials["artifact_sha256"], False
    )
    pkg["annotation_receipt"]["independent_annotation_available"] = False
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
    pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    R0 = external_root_of(pkg)
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["validation_status"] == "FAIL"
    assert result["GO_ALLOWED"] is False
    assert any("INDEPENDENT_ANNOTATION" in e for e in result["errors"]), result["errors"]


def test_validator_debug_cannot_force_go():
    pkg = build_complete_no_disagreement_package()
    pkg["annotation_receipt"]["gold_access"] = True
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["annotation_receipt"] = _apply_hashes_to_receipt(
        pkg["annotation_receipt"], materials["artifact_sha256"], False
    )
    pkg["annotation_receipt"]["gold_access"] = True
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
    pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    R0 = external_root_of(pkg)
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["GO_ALLOWED"] is False
    assert result["validation_status"] == "FAIL"
    assert any("gold_access" in e for e in result["errors"]), result["errors"]


def test_positive_package_go_allowed():
    """Regression: complete legitimate package reaches GO via production validate_package."""
    pkg = build_complete_no_disagreement_package()
    R0 = external_root_of(pkg)
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["errors"] == [], result["errors"]
    assert result["validation_status"] == "PASS"
    assert result["GO_ALLOWED"] is True


# ----- T19–T26 adversarial completeness / hash -----


def test_T19_completely_empty_package_fails():
    # No external root AND empty package — both fail-closed
    result = mod.validate_package({})
    assert result["validation_status"] == "FAIL"
    assert result["GO_ALLOWED"] is False
    assert any(
        "EMPTY_PACKAGE" in e or "MISSING_REQUIRED" in e or "MISSING_EXTERNAL_EXPECTED_ROOT" in e
        for e in result["errors"]
    ), result["errors"]


def test_T20_keys_present_content_empty_fails():
    pkg = {
        "sanitized_inputs": [
            {
                "query_id": "EX_Q_NARROW",
                "fact_id": "EX_F_WORKS",
                "query_text": "Who works on Project Nimbus?",
                "fact_text": "Sofia works on Project Nimbus.",
            }
        ],
        "annotation_A": [],
        "annotation_B": [],
        "final_structural_package": [],
        "annotation_receipt": valid_receipt(),
        "frozen_integrity_manifest": {
            "protocol_version": "fm17-pre-v1.3",
            "created_before_evaluation_overlay": True,
            "artifact_sha256": {},
        },
        "frozen_root_commitment": {
            "root_sha256": "a" * 64,
            "freeze_declared_before_overlay": True,
        },
    }
    # Incomplete package: still FAIL even if a dummy external root is supplied
    result = mod.validate_package(pkg, expected_frozen_root="a" * 64)
    assert result["validation_status"] == "FAIL"
    assert result["GO_ALLOWED"] is False
    assert any("EMPTY_REQUIRED_RECORD_SET" in e for e in result["errors"]), result["errors"]


def test_T21_record_coverage_gap_fails():
    pkg = build_complete_no_disagreement_package()
    R0 = external_root_of(pkg)
    # drop the only record from annotation_B
    pkg["annotation_B"] = []
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["validation_status"] == "FAIL"
    assert any(
        "EMPTY_REQUIRED_RECORD_SET:annotation_B" in e or "missing expected records" in e
        for e in result["errors"]
    ), result["errors"]


def test_T22_false_zero_disagreement_declaration_fails():
    pkg = build_complete_no_disagreement_package()
    pkg["annotation_B"] = [_ann_b_disagree()]
    # receipt still claims 0 disagreements; no adjudication evidence
    pkg["annotation_receipt"]["disagreement_count"] = 0
    pkg["annotation_receipt"]["adjudicated_count"] = 0
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["annotation_receipt"] = _apply_hashes_to_receipt(
        pkg["annotation_receipt"], materials["artifact_sha256"], False
    )
    pkg["annotation_receipt"]["disagreement_count"] = 0
    pkg["annotation_receipt"]["adjudicated_count"] = 0
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
    pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    R0 = external_root_of(pkg)
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["validation_status"] == "FAIL"
    assert result["computed_disagreement_count"] > 0
    assert any("DISAGREEMENT_COUNT_MISMATCH" in e for e in result["errors"]), result["errors"]


def test_T23_valid_looking_but_wrong_sha256_fails():
    pkg = build_complete_no_disagreement_package()
    R0 = external_root_of(pkg)
    # syntactically valid 64-hex that does not match bytes
    wrong = "b" * 64
    pkg["frozen_integrity_manifest"]["artifact_sha256"]["annotation_A"] = wrong
    # keep frozen root as original (also ensure receipt hash wrong path is hit)
    pkg["annotation_receipt"]["annotation_A_hash"] = wrong
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["validation_status"] == "FAIL"
    assert any("HASH_MISMATCH:annotation_A" in e or "FROZEN_ROOT_MISMATCH" in e for e in result["errors"]), result["errors"]


def test_T24_post_hash_artifact_modification_fails():
    with tempfile.TemporaryDirectory() as td:
        pkg = build_complete_no_disagreement_package(write_files=True, tmpdir=td)
        R0 = external_root_of(pkg)
        # freeze done; now tamper file bytes
        ap = _Path(pkg["artifact_paths"]["annotation_A"])
        data = json.loads(ap.read_text())
        data[0]["annotation_comment"]["comment"] = "TAMPERED_AFTER_FREEZE"
        ap.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        # keep in-memory annotation_A matching old (validator prefers artifact_paths)
        result = mod.validate_package(pkg, expected_frozen_root=R0)
        assert result["validation_status"] == "FAIL"
        assert any(
            "HASH_MISMATCH:annotation_A" in e or "FROZEN_ROOT_MISMATCH" in e or "EXTERNAL_VS_ACTUAL" in e
            for e in result["errors"]
        ), result["errors"]


def test_T25_file_plus_local_manifest_replaced_frozen_root_holds():
    with tempfile.TemporaryDirectory() as td:
        pkg = build_complete_no_disagreement_package(write_files=True, tmpdir=td)
        R0 = external_root_of(pkg)
        original_root = R0
        # tamper file
        ap = _Path(pkg["artifact_paths"]["annotation_A"])
        data = json.loads(ap.read_text())
        data[0]["annotation_comment"]["comment"] = "COLLUDING_TAMPER"
        ap.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        # rewrite local manifest + receipt to match new bytes (internal consistency)
        new_digest = mod.sha256_file(ap)
        pkg["frozen_integrity_manifest"]["artifact_sha256"]["annotation_A"] = new_digest
        pkg["annotation_receipt"]["annotation_A_hash"] = new_digest
        # also rewrite receipt file if present
        if "annotation_receipt" in pkg["artifact_paths"]:
            rp = _Path(pkg["artifact_paths"]["annotation_receipt"])
            rp.write_text(json.dumps(pkg["annotation_receipt"], sort_keys=True, separators=(",", ":")), encoding="utf-8")
            pkg["frozen_integrity_manifest"]["artifact_sha256"]["annotation_receipt"] = mod.sha256_file(rp)
        # package-local frozen root commitment UNCHANGED; EXTERNAL R0 held separately
        assert pkg["frozen_root_commitment"]["root_sha256"] == original_root
        result = mod.validate_package(pkg, expected_frozen_root=R0)
        assert result["validation_status"] == "FAIL"
        assert any(
            "FROZEN_ROOT_MISMATCH" in e or "EXTERNAL_VS_ACTUAL" in e for e in result["errors"]
        ), result["errors"]


def test_T26_required_frozen_root_missing_fails():
    pkg = build_complete_no_disagreement_package()
    R0 = external_root_of(pkg)
    del pkg["frozen_root_commitment"]
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["validation_status"] == "FAIL"
    assert any(
        "MISSING_REQUIRED_COMPONENT:frozen_root_commitment" in e or "MISSING_FROZEN_ROOT" in e
        for e in result["errors"]
    ), result["errors"]


def test_P5_complete_no_disagreement_package_passes():
    pkg = build_complete_no_disagreement_package()
    R0 = external_root_of(pkg)
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["validation_status"] == "PASS", result["errors"]
    assert result["GO_ALLOWED"] is True
    assert result["computed_disagreement_count"] == 0


def test_P6_complete_real_disagreement_package_passes():
    pkg = build_complete_disagreement_package()
    R0 = external_root_of(pkg)
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["validation_status"] == "PASS", result["errors"]
    assert result["GO_ALLOWED"] is True
    assert result["computed_disagreement_count"] > 0




# ----- T27–T29 / P7 external freeze anchor (v1.3.1) -----


def test_T27_full_package_plus_root_replacement_fails():
    """Manus bypass: mutate artifact + recompute ALL package-local roots; EXTERNAL R0 unchanged."""
    pkg = build_complete_no_disagreement_package()
    R0 = external_root_of(pkg)

    # 1) mutate hash-bound artifact
    pkg["annotation_A"][0]["annotation_comment"]["comment"] = "FULL_PACKAGE_REPLACEMENT"

    # 2–5) recompute hashes, receipt, local manifest, AND package-local root = R1
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["annotation_receipt"] = _apply_hashes_to_receipt(
        pkg["annotation_receipt"], materials["artifact_sha256"], False
    )
    materials = mod.build_frozen_materials(pkg, require_conditional=False)
    pkg["frozen_integrity_manifest"] = materials["frozen_integrity_manifest"]
    pkg["frozen_root_commitment"] = materials["frozen_root_commitment"]
    R1 = pkg["frozen_root_commitment"]["root_sha256"]
    assert R1 != R0

    # 6) EXTERNAL expected root remains R0
    result = mod.validate_package(pkg, expected_frozen_root=R0)

    assert result["validation_status"] == "FAIL"
    assert result["GO_ALLOWED"] is False
    assert result["package_local_root"] == R1
    assert result["actual_root"] == R1
    assert result["external_expected_root"] == R0
    assert any("EXTERNAL_VS_ACTUAL_ROOT_MISMATCH" in e for e in result["errors"]), result["errors"]
    assert any("EXTERNAL_VS_PACKAGE_ROOT_MISMATCH" in e for e in result["errors"]), result["errors"]


def test_T28_external_expected_anchor_absent_fails():
    pkg = build_complete_no_disagreement_package()
    # Explicitly omit external expected root — must NOT default from package
    result = mod.validate_package(pkg, expected_frozen_root=None)
    assert result["validation_status"] == "FAIL"
    assert result["GO_ALLOWED"] is False
    assert any("MISSING_EXTERNAL_EXPECTED_ROOT" in e for e in result["errors"]), result["errors"]


def test_T29_package_valid_but_local_root_ne_external_fails():
    pkg = build_complete_no_disagreement_package()
    R0 = external_root_of(pkg)
    wrong_external = "d" * 64
    assert wrong_external != R0
    result = mod.validate_package(pkg, expected_frozen_root=wrong_external)
    assert result["validation_status"] == "FAIL"
    assert result["GO_ALLOWED"] is False
    assert any("EXTERNAL_VS_PACKAGE_ROOT_MISMATCH" in e or "EXTERNAL_VS_ACTUAL_ROOT_MISMATCH" in e for e in result["errors"]), result["errors"]


def test_P7_valid_externally_anchored_package_passes():
    pkg = build_complete_no_disagreement_package()
    R0 = external_root_of(pkg)
    result = mod.validate_package(pkg, expected_frozen_root=R0)
    assert result["validation_status"] == "PASS", result["errors"]
    assert result["GO_ALLOWED"] is True
    assert result["external_expected_root"] == R0
    assert result["package_local_root"] == R0
    assert result["actual_root"] == R0


def test_template_rows_structural_pass_overlay_schema_pass():
    import json
    from pathlib import Path
    doc = Path(__file__).resolve().parents[2] / "docs/research/fm17_pre"
    schema = mod._load_schema("oracle_annotations.schema.json")
    for line in (doc / "oracle_annotations.template.jsonl").read_text().splitlines():
        rec = json.loads(line)
        if rec["record_layer"] == "STRUCTURAL":
            expect_pass(mod.validate_structural_record(rec, schema), "TEMPLATE")
        else:
            expect_pass(mod._schema_errors(schema, rec), "TEMPLATE_OVERLAY")
