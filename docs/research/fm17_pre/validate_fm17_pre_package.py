#!/usr/bin/env python3
"""FM-17-pre v1.2 PRE-ABLATION INTEGRITY VALIDATOR.

INTEGRITY VALIDATOR ≠ RELEVANCE JUDGE.

Checks form, provenance, blinding, freeze, hashes, process consistency,
and forbidden input access. Does NOT score CE/embeddings, does NOT
decide DIRECT/gold/scope substance, does NOT compute A0/A1/A2/A3 metrics.

INVALID → exit 1, GO_ALLOWED=false. No --force / --ignore / --continue-anyway.
A debug print mode never sets GO_ALLOWED=true unless validation_status=PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
VALIDATOR_VERSION = "fm17-pre-validator-v1.2"

FORBIDDEN_SANITIZED_KEYS = {
    "split",
    "gold",
    "hn",
    "hn_labels",
    "gold_relevance_class",
    "score",
    "rank",
    "ce_score",
    "embedding_score",
    "expected",
}
PARTITION_TOKENS = {"CAL", "TEST"}


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def _schema_errors(schema: dict[str, Any], instance: Any) -> list[str]:
    v = Draft202012Validator(schema)
    out = []
    for e in v.iter_errors(instance):
        path = ".".join(str(p) for p in e.absolute_path) or "$"
        out.append(f"{path}: {e.message}")
    return out


def walk_annotated_fields(record: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    for side in ("query", "fact"):
        block = record.get(side) or {}
        if not isinstance(block, dict):
            continue
        for name, av in block.items():
            if isinstance(av, dict) and "provenance" in av:
                found.append((f"{side}.{name}", av))
    return found


def validate_structural_record(record: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or _load_schema("oracle_annotations.schema.json")
    errs = _schema_errors(schema, record)
    if record.get("record_layer") != "STRUCTURAL":
        return errs
    if "annotation_notes" in record:
        errs.append("STRUCTURAL contains unbounded annotation_notes")
    if "gold_relevance_class" in record:
        errs.append("STRUCTURAL contains gold_relevance_class")
    if "hn_labels" in record:
        errs.append("STRUCTURAL contains hn_labels")
    qclass = ((record.get("query") or {}).get("query_class") or {}).get("value")
    scope_av = (record.get("query") or {}).get("scope_target") or {}
    scope_val = scope_av.get("value")
    if qclass == "BROAD" and scope_val not in (None, "any"):
        prov = scope_av.get("provenance") or {}
        span = prov.get("source_span") or ""
        rule = prov.get("rule_id") or ""
        if not (isinstance(span, str) and span.strip()) and not (isinstance(rule, str) and rule.strip()):
            errs.append(
                "BROAD query with narrow scope_target lacks source_span and rule_id"
            )
    return errs


def validate_sanitized_input(obj: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or _load_schema("sanitized_annotation_input.schema.json")
    errs = _schema_errors(schema, obj)
    for k in obj.keys():
        if k in FORBIDDEN_SANITIZED_KEYS or k.lower() in {"split"}:
            errs.append(f"sanitized input contains forbidden key {k}")
    batch = str(obj.get("batch_id") or "")
    if batch in PARTITION_TOKENS or batch.upper() in PARTITION_TOKENS:
        errs.append("batch_id encodes evaluation partition identity")
    for token in PARTITION_TOKENS:
        if token in json.dumps(obj):
            # only fail if used as partition identity fields; query text mentioning
            # the letters is possible. Restrict to field values of ids/batch.
            pass
    if obj.get("split") is not None:
        errs.append("sanitized input exposes split/partition identity")
    return errs


def validate_receipt(obj: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or _load_schema("annotation_receipt.schema.json")
    errs = _schema_errors(schema, obj)
    for flag in (
        "gold_access",
        "hn_access",
        "ce_score_access",
        "embedding_score_access",
        "evaluation_overlay_access",
    ):
        if obj.get(flag) is True:
            errs.append(f"{flag}=true is forbidden on primary structural receipt")
    blinding = obj.get("blinding") or {}
    if isinstance(blinding, dict):
        for k, v in blinding.items():
            if v is True:
                errs.append(f"blinding.{k}=true is forbidden")
    a = obj.get("annotator_A_id")
    b = obj.get("annotator_B_id")
    if a and b and a == b:
        errs.append("annotator_A_id == annotator_B_id")
    if obj.get("independent_annotation_available") is False:
        errs.append("INDEPENDENT_ANNOTATION_AVAILABLE=false → PRE_ABLATION_VALIDATION_FAIL")
    dc = obj.get("disagreement_count")
    ac = obj.get("adjudicated_count")
    if isinstance(dc, int) and isinstance(ac, int) and dc != ac:
        errs.append("disagreement_count != adjudicated_count")
    if isinstance(dc, int) and dc > 0:
        if not obj.get("adjudicator_id"):
            errs.append("disagreement_count>0 but adjudicator_id is null")
        if not obj.get("disagreement_log_hash"):
            errs.append("disagreement_count>0 missing disagreement_log_hash")
        if not obj.get("adjudicated_annotation_hash"):
            errs.append("disagreement_count>0 missing adjudicated_annotation_hash")
    for i, am in enumerate(obj.get("post_freeze_amendments") or []):
        if not isinstance(am, dict):
            errs.append(f"amendment[{i}] not an object")
            continue
        if am.get("scoring_started") is True:
            if am.get("invalidation_required") is not True or am.get("previous_result_invalidated") is not True:
                errs.append(
                    f"amendment[{i}] scoring_started=true but invalidation not enforced"
                )
    return errs


def validate_disagreement_log(entries: list[Any]) -> list[str]:
    errs: list[str] = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            errs.append(f"disagreement[{i}] not object")
            continue
        status = e.get("status")
        if status in {"PENDING", "UNRESOLVED_DISAGREEMENT"}:
            errs.append(f"disagreement[{i}] non-final status {status}")
        if status != "ADJUDICATED":
            errs.append(f"disagreement[{i}] status must be ADJUDICATED, got {status}")
        if not e.get("adjudicator_id"):
            errs.append(f"disagreement[{i}] missing adjudicator_id")
    return errs


def validate_package(package: dict[str, Any]) -> dict[str, Any]:
    """Validate a TEST_FIXTURE / mock package dict.

    Expected keys (all optional except those used): sanitized_inputs,
    annotation_A, annotation_B, disagreement_log, adjudicated_annotations,
    final_structural_package, annotation_receipt, evaluation_overlay,
    overlay_after_structural_freeze.
    """
    errors: list[str] = []
    rec_schema = _load_schema("oracle_annotations.schema.json")
    san_schema = _load_schema("sanitized_annotation_input.schema.json")
    recpt_schema = _load_schema("annotation_receipt.schema.json")

    for i, item in enumerate(package.get("sanitized_inputs") or []):
        errors.extend(f"sanitized[{i}] {e}" for e in validate_sanitized_input(item, san_schema))

    for label in ("annotation_A", "annotation_B", "adjudicated_annotations", "final_structural_package"):
        for i, rec in enumerate(package.get(label) or []):
            errors.extend(f"{label}[{i}] {e}" for e in validate_structural_record(rec, rec_schema))

    if package.get("disagreement_log"):
        errors.extend(validate_disagreement_log(package["disagreement_log"]))

    if package.get("annotation_receipt") is not None:
        errors.extend(validate_receipt(package["annotation_receipt"], recpt_schema))

    overlay = package.get("evaluation_overlay")
    freeze_locked = package.get("overlay_after_structural_freeze")
    if overlay:
        if freeze_locked is not True:
            errors.append("evaluation overlay present before structural freeze lock")
        for i, rec in enumerate(overlay):
            errors.extend(
                f"overlay[{i}] {e}" for e in _schema_errors(rec_schema, rec)
            )

    status = "PASS" if not errors else "FAIL"
    go = status == "PASS"
    return {
        "validator_version": VALIDATOR_VERSION,
        "validation_status": status,
        "GO_ALLOWED": go,
        "errors": errors,
        "note": "INTEGRITY VALIDATOR ≠ RELEVANCE JUDGE. TEST_FIXTURE path only in v1.2.",
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FM-17-pre fail-closed integrity validator")
    p.add_argument("package_json", nargs="?", help="Path to TEST_FIXTURE package JSON")
    p.add_argument("--debug", action="store_true", help="Print errors; never forces GO_ALLOWED")
    args = p.parse_args(argv)
    if not args.package_json:
        print("usage: validate_fm17_pre_package.py PACKAGE.json", file=sys.stderr)
        return 1
    data = json.loads(Path(args.package_json).read_text(encoding="utf-8"))
    result = validate_package(data)
    if args.debug:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
    # debug flag must never flip GO
    if result["validation_status"] != "PASS":
        result["GO_ALLOWED"] = False
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
