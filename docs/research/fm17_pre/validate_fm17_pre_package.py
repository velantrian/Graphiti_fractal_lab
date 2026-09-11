#!/usr/bin/env python3
"""FM-17-pre v1.3 PRE-ABLATION INTEGRITY VALIDATOR.

INTEGRITY VALIDATOR ≠ RELEVANCE JUDGE.

v1.3 closes two Manus fail-open paths:
  A) empty/incomplete package → PASS
  B) declared hashes without recomputing real file bytes → PASS

Checks form, package completeness, record coverage, A/B-derived
disagreement consistency, provenance, blinding, freeze order, and
actual SHA-256 vs non-circular frozen root commitment.

Does NOT score CE/embeddings, does NOT decide DIRECT/gold/scope
substance, does NOT compute A0/A1/A2/A3 metrics.

INVALID → exit 1, GO_ALLOWED=false. No --force / --ignore / --continue-anyway.
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
VALIDATOR_VERSION = "fm17-pre-validator-v1.3"

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

# Unconditional package components for pre-ablation GO
REQUIRED_PACKAGE_KEYS = (
    "sanitized_inputs",
    "annotation_A",
    "annotation_B",
    "final_structural_package",
    "annotation_receipt",
    "frozen_integrity_manifest",
    "frozen_root_commitment",
)

# Artifact keys hashed into the integrity trust chain (minimal set)
CORE_HASH_KEYS = (
    "sanitized_inputs",
    "annotation_A",
    "annotation_B",
    "final_structural_package",
    "annotation_receipt",
)
CONDITIONAL_HASH_KEYS = (
    "disagreement_log",
    "adjudicated_annotations",
)
OPTIONAL_FILE_HASH_KEYS = (
    "query_corpus",
    "fact_corpus",
    "rulebook",
    "ontology_schema",
    "annotation_schema",
)


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def _schema_errors(schema: dict[str, Any], instance: Any) -> list[str]:
    v = Draft202012Validator(schema)
    out = []
    for e in v.iter_errors(instance):
        path = ".".join(str(p) for p in e.absolute_path) or "$"
        out.append(f"{path}: {e.message}")
    return out


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(obj: Any) -> bytes:
    """Deterministic UTF-8 JSON bytes for hashing in-memory artifacts."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


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


def record_id(rec: dict[str, Any]) -> str | None:
    pid = rec.get("pair_id")
    if isinstance(pid, str) and pid.strip():
        return pid
    qid, fid = rec.get("query_id"), rec.get("fact_id")
    if isinstance(qid, str) and isinstance(fid, str) and qid and fid:
        return f"{qid}::{fid}"
    return None


def expected_record_ids(sanitized_inputs: list[Any]) -> list[str]:
    out: list[str] = []
    for item in sanitized_inputs:
        if not isinstance(item, dict):
            continue
        qid, fid = item.get("query_id"), item.get("fact_id")
        if isinstance(qid, str) and isinstance(fid, str) and qid and fid:
            out.append(f"{qid}::{fid}")
    return out


def ids_from_records(records: list[Any]) -> list[str]:
    out: list[str] = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        rid = record_id(rec)
        if rid:
            out.append(rid)
    return out


def check_record_coverage(
    expected: list[str],
    label: str,
    records: list[Any],
) -> list[str]:
    errs: list[str] = []
    if not isinstance(records, list):
        return [f"{label} must be a nonempty list"]
    if len(records) == 0:
        errs.append(f"{label} is empty but required records exist")
        return errs
    got = ids_from_records(records)
    if len(got) != len(set(got)):
        errs.append(f"{label} contains duplicate record IDs")
    exp_set, got_set = set(expected), set(got)
    missing = sorted(exp_set - got_set)
    extra = sorted(got_set - exp_set)
    if missing:
        errs.append(f"{label} missing expected records: {missing}")
    if extra:
        errs.append(f"{label} has unexpected records: {extra}")
    if len(records) != len(got):
        errs.append(f"{label} has records without pair_id/query_id+fact_id")
    return errs


def structural_value_map(rec: dict[str, Any]) -> dict[str, Any]:
    """Field path → annotated value only (structure/integrity, not relevance)."""
    out: dict[str, Any] = {}
    for path, av in walk_annotated_fields(rec):
        out[path] = av.get("value")
    return out


def compute_disagreement_set(
    annotation_A: list[Any], annotation_B: list[Any]
) -> list[dict[str, Any]]:
    """Derive disagreements from A/B structural field values (not receipt count)."""
    by_a = {record_id(r): r for r in annotation_A if isinstance(r, dict) and record_id(r)}
    by_b = {record_id(r): r for r in annotation_B if isinstance(r, dict) and record_id(r)}
    disagreements: list[dict[str, Any]] = []
    for rid in sorted(set(by_a) | set(by_b)):
        if rid not in by_a or rid not in by_b:
            disagreements.append(
                {
                    "pair_id": rid,
                    "field_path": "__record_presence__",
                    "reason": "record present in only one annotator set",
                }
            )
            continue
        va = structural_value_map(by_a[rid])
        vb = structural_value_map(by_b[rid])
        for path in sorted(set(va) | set(vb)):
            if path not in va or path not in vb or va[path] != vb[path]:
                disagreements.append(
                    {
                        "pair_id": rid,
                        "field_path": path,
                        "reason": "structural_value_mismatch",
                    }
                )
    return disagreements


def compute_artifact_digest(package: dict[str, Any], key: str) -> str | None:
    """SHA-256 of real file bytes when artifact_paths set; else canonical JSON bytes."""
    paths = package.get("artifact_paths") or {}
    if isinstance(paths, dict) and key in paths and paths[key]:
        p = Path(str(paths[key]))
        if not p.is_file():
            return None
        return sha256_file(p)
    if key not in package:
        return None
    return sha256_bytes(canonical_json_bytes(package[key]))


def compute_artifact_sha256_map(package: dict[str, Any], require_conditional: bool) -> dict[str, str]:
    digests: dict[str, str] = {}
    for key in CORE_HASH_KEYS:
        d = compute_artifact_digest(package, key)
        if d is None:
            continue
        digests[key] = d
    if require_conditional:
        for key in CONDITIONAL_HASH_KEYS:
            d = compute_artifact_digest(package, key)
            if d is not None:
                digests[key] = d
    paths = package.get("artifact_paths") or {}
    if isinstance(paths, dict):
        for key in OPTIONAL_FILE_HASH_KEYS:
            if key in paths and paths[key]:
                p = Path(str(paths[key]))
                if p.is_file():
                    digests[key] = sha256_file(p)
    return digests


def frozen_root_from_digests(artifact_sha256: dict[str, str]) -> str:
    return sha256_bytes(canonical_json_bytes(artifact_sha256))


def validate_package_completeness(package: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(package, dict) or len(package) == 0:
        return ["EMPTY_PACKAGE: minimally required pre-ablation package is missing"]

    for key in REQUIRED_PACKAGE_KEYS:
        if key not in package:
            errs.append(f"MISSING_REQUIRED_COMPONENT:{key}")
        elif package[key] is None:
            errs.append(f"REQUIRED_COMPONENT_NULL:{key}")

    # Nonempty list components when present
    for key in (
        "sanitized_inputs",
        "annotation_A",
        "annotation_B",
        "final_structural_package",
    ):
        if key not in package:
            continue
        val = package[key]
        if not isinstance(val, list):
            errs.append(f"{key} must be a list")
        elif len(val) == 0:
            errs.append(f"EMPTY_REQUIRED_RECORD_SET:{key}")

    receipt = package.get("annotation_receipt")
    if receipt is not None and not isinstance(receipt, dict):
        errs.append("annotation_receipt must be an object")
    elif isinstance(receipt, dict) and len(receipt) == 0:
        errs.append("EMPTY_REQUIRED_COMPONENT:annotation_receipt")

    fim = package.get("frozen_integrity_manifest")
    if fim is not None and not isinstance(fim, dict):
        errs.append("frozen_integrity_manifest must be an object")
    elif isinstance(fim, dict):
        if not fim.get("artifact_sha256") or not isinstance(fim.get("artifact_sha256"), dict):
            errs.append("frozen_integrity_manifest.artifact_sha256 missing or invalid")
        if fim.get("created_before_evaluation_overlay") is not True:
            errs.append("frozen_integrity_manifest.created_before_evaluation_overlay must be true")

    frc = package.get("frozen_root_commitment")
    if frc is not None and not isinstance(frc, dict):
        errs.append("frozen_root_commitment must be an object")
    elif isinstance(frc, dict):
        root = frc.get("root_sha256")
        if not (isinstance(root, str) and len(root) == 64 and all(c in "0123456789abcdef" for c in root)):
            errs.append("frozen_root_commitment.root_sha256 missing or not 64-hex")
        if frc.get("freeze_declared_before_overlay") is not True:
            errs.append("frozen_root_commitment.freeze_declared_before_overlay must be true")

    return errs


def validate_hash_integrity(package: dict[str, Any], computed_dc: int) -> list[str]:
    """Recompute real digests; compare to local manifest + non-circular frozen root."""
    errs: list[str] = []
    fim = package.get("frozen_integrity_manifest")
    frc = package.get("frozen_root_commitment")
    if not isinstance(fim, dict) or not isinstance(frc, dict):
        return ["HASH_GATE: frozen integrity materials missing"]

    declared = fim.get("artifact_sha256")
    if not isinstance(declared, dict):
        return ["HASH_GATE: artifact_sha256 missing"]

    require_conditional = computed_dc > 0
    actual = compute_artifact_sha256_map(package, require_conditional=require_conditional)

    for key in CORE_HASH_KEYS:
        if key not in actual:
            errs.append(f"HASH_GATE: unable to hash required artifact {key}")
            continue
        if key not in declared:
            errs.append(f"HASH_GATE: local manifest missing declared hash for {key}")
            continue
        exp = declared[key]
        if not (isinstance(exp, str) and len(exp) == 64 and all(c in "0123456789abcdef" for c in exp)):
            errs.append(f"HASH_GATE: declared hash for {key} is not valid 64-hex")
            continue
        if actual[key] != exp:
            errs.append(
                f"HASH_MISMATCH:{key}: declared={exp} actual={actual[key]}"
            )

    if require_conditional:
        for key in CONDITIONAL_HASH_KEYS:
            if key not in package and key not in (package.get("artifact_paths") or {}):
                errs.append(f"HASH_GATE: conditional artifact {key} required but absent")
                continue
            if key not in actual:
                errs.append(f"HASH_GATE: unable to hash conditional artifact {key}")
                continue
            if key not in declared:
                errs.append(f"HASH_GATE: local manifest missing declared hash for {key}")
                continue
            if actual[key] != declared[key]:
                errs.append(
                    f"HASH_MISMATCH:{key}: declared={declared[key]} actual={actual[key]}"
                )

    # Receipt declared content hashes must match recomputed core artifact digests
    receipt = package.get("annotation_receipt")
    if isinstance(receipt, dict):
        receipt_map = {
            "sanitized_inputs": "sanitized_input_hash",
            "annotation_A": "annotation_A_hash",
            "annotation_B": "annotation_B_hash",
            "final_structural_package": "final_structural_package_hash",
        }
        for art_key, receipt_field in receipt_map.items():
            rh = receipt.get(receipt_field)
            if art_key in actual and isinstance(rh, str) and rh != actual[art_key]:
                errs.append(
                    f"RECEIPT_HASH_MISMATCH:{receipt_field}: declared={rh} actual={actual[art_key]}"
                )
        if require_conditional:
            for art_key, receipt_field in (
                ("disagreement_log", "disagreement_log_hash"),
                ("adjudicated_annotations", "adjudicated_annotation_hash"),
            ):
                rh = receipt.get(receipt_field)
                if art_key in actual and isinstance(rh, str) and rh != actual[art_key]:
                    errs.append(
                        f"RECEIPT_HASH_MISMATCH:{receipt_field}: declared={rh} actual={actual[art_key]}"
                    )

    # Non-circular frozen root: compare recomputed root to immutable commitment
    # Root is over the LOCAL MANIFEST's artifact_sha256 map as frozen at freeze time,
    # but we recompute root from ACTUAL digests — both must equal frozen_root_commitment.
    expected_root = frc.get("root_sha256")
    actual_root = frozen_root_from_digests(actual)
    # Also require that declared map's root matches commitment (attacker updating
    # file+local manifest but not root fails because actual_root != expected_root)
    declared_root = frozen_root_from_digests({k: declared[k] for k in sorted(declared) if isinstance(declared.get(k), str)})
    if actual_root != expected_root:
        errs.append(
            f"FROZEN_ROOT_MISMATCH: expected={expected_root} actual={actual_root}"
        )
    # If local manifest was rewritten to match tampered files, declared_root == actual_root
    # but still != expected_root → caught above. If only local manifest wrong:
    if declared_root != expected_root and actual_root == expected_root:
        errs.append(
            f"LOCAL_MANIFEST_ROOT_DRIFT: declared_root={declared_root} frozen={expected_root}"
        )

    # Optional: bind pre_ablation_validation_receipt schema fields when supplied
    pav = package.get("pre_ablation_validation_receipt")
    if pav is not None:
        pav_schema = _load_schema("pre_ablation_validation_receipt.schema.json")
        errs.extend(f"pre_ablation_receipt {e}" for e in _schema_errors(pav_schema, pav))
        if isinstance(pav, dict):
            if pav.get("sanitized_input_hash") and "sanitized_inputs" in actual:
                if pav["sanitized_input_hash"] != actual["sanitized_inputs"]:
                    errs.append("pre_ablation_receipt sanitized_input_hash mismatch")
            if pav.get("validated_package_hash") and pav["validated_package_hash"] != actual_root:
                # validated_package_hash should bind the frozen root of hashed artifacts
                errs.append("pre_ablation_receipt validated_package_hash != frozen root")

    return errs


def validate_package(package: dict[str, Any]) -> dict[str, Any]:
    """Validate a TEST_FIXTURE / mock package dict (fail-closed).

    Required keys (v1.3): sanitized_inputs, annotation_A, annotation_B,
    final_structural_package, annotation_receipt, frozen_integrity_manifest,
    frozen_root_commitment.

    Optional: disagreement_log, adjudicated_annotations (required when A/B disagree),
    artifact_paths (map to real files for sha256_file), evaluation_overlay,
    overlay_after_structural_freeze, pre_ablation_validation_receipt.
    """
    errors: list[str] = []
    rec_schema = _load_schema("oracle_annotations.schema.json")
    san_schema = _load_schema("sanitized_annotation_input.schema.json")
    recpt_schema = _load_schema("annotation_receipt.schema.json")

    # --- FIX A: completeness first (empty package must not PASS) ---
    errors.extend(validate_package_completeness(package))

    # Schema / structural checks only when components exist
    for i, item in enumerate(package.get("sanitized_inputs") or []):
        if isinstance(item, dict):
            errors.extend(f"sanitized[{i}] {e}" for e in validate_sanitized_input(item, san_schema))

    for label in ("annotation_A", "annotation_B", "adjudicated_annotations", "final_structural_package"):
        for i, rec in enumerate(package.get(label) or []):
            if isinstance(rec, dict):
                errors.extend(f"{label}[{i}] {e}" for e in validate_structural_record(rec, rec_schema))

    # Record coverage: EXPECTED == A == B == final (and adjudicated when required)
    san = package.get("sanitized_inputs")
    if isinstance(san, list) and len(san) > 0:
        expected = expected_record_ids(san)
        if not expected:
            errors.append("sanitized_inputs produced no expected record IDs")
        else:
            for label in ("annotation_A", "annotation_B", "final_structural_package"):
                if isinstance(package.get(label), list):
                    errors.extend(check_record_coverage(expected, label, package[label]))

    # Derive disagreement from A/B (do not trust receipt.disagreement_count alone)
    computed_disagreements: list[dict[str, Any]] = []
    computed_dc = 0
    ann_a = package.get("annotation_A")
    ann_b = package.get("annotation_B")
    if isinstance(ann_a, list) and isinstance(ann_b, list) and len(ann_a) > 0 and len(ann_b) > 0:
        computed_disagreements = compute_disagreement_set(ann_a, ann_b)
        computed_dc = len(computed_disagreements)

    if package.get("annotation_receipt") is not None and isinstance(package.get("annotation_receipt"), dict):
        errors.extend(validate_receipt(package["annotation_receipt"], recpt_schema))
        receipt = package["annotation_receipt"]
        declared_dc = receipt.get("disagreement_count")
        if isinstance(declared_dc, int) and (
            isinstance(ann_a, list) and isinstance(ann_b, list) and len(ann_a) > 0 and len(ann_b) > 0
        ):
            if declared_dc != computed_dc:
                errors.append(
                    f"DISAGREEMENT_COUNT_MISMATCH: receipt={declared_dc} computed_from_A_B={computed_dc}"
                )

    if computed_dc > 0:
        if not package.get("disagreement_log"):
            errors.append("computed_disagreement_count>0 but disagreement_log missing")
        else:
            errors.extend(validate_disagreement_log(package["disagreement_log"]))
        if not package.get("adjudicated_annotations"):
            errors.append("computed_disagreement_count>0 but adjudicated_annotations missing")
        elif isinstance(san, list) and len(san) > 0:
            expected = expected_record_ids(san)
            if isinstance(package.get("adjudicated_annotations"), list):
                errors.extend(
                    check_record_coverage(
                        expected, "adjudicated_annotations", package["adjudicated_annotations"]
                    )
                )
        receipt = package.get("annotation_receipt") if isinstance(package.get("annotation_receipt"), dict) else {}
        if not (receipt or {}).get("adjudicator_id"):
            errors.append("computed_disagreement_count>0 but receipt.adjudicator_id missing")
        if not (receipt or {}).get("disagreement_log_hash"):
            errors.append("computed_disagreement_count>0 but receipt.disagreement_log_hash missing")
        if not (receipt or {}).get("adjudicated_annotation_hash"):
            errors.append("computed_disagreement_count>0 but receipt.adjudicated_annotation_hash missing")
    elif package.get("disagreement_log"):
        # optional when zero disagreements; if present still must be well-formed
        errors.extend(validate_disagreement_log(package["disagreement_log"]))

    overlay = package.get("evaluation_overlay")
    freeze_locked = package.get("overlay_after_structural_freeze")
    if overlay:
        if freeze_locked is not True:
            errors.append("evaluation overlay present before structural freeze lock")
        for i, rec in enumerate(overlay):
            if isinstance(rec, dict):
                errors.extend(f"overlay[{i}] {e}" for e in _schema_errors(rec_schema, rec))

    # --- FIX B: real hash verification + non-circular frozen root ---
    # Only run full hash gate when completeness scaffolding is present enough
    # to avoid drowning empty-package failures in hash noise — but empty still FAIL.
    has_hash_scaffold = (
        isinstance(package.get("frozen_integrity_manifest"), dict)
        and isinstance(package.get("frozen_root_commitment"), dict)
        and isinstance(package.get("annotation_receipt"), dict)
        and isinstance(package.get("sanitized_inputs"), list)
        and isinstance(package.get("annotation_A"), list)
        and isinstance(package.get("annotation_B"), list)
        and isinstance(package.get("final_structural_package"), list)
    )
    if has_hash_scaffold:
        errors.extend(validate_hash_integrity(package, computed_dc))
    elif package:  # non-empty but missing scaffold → completeness already erred;
        # additionally reject missing frozen root explicitly when other materials exist
        if "frozen_root_commitment" not in package:
            if "MISSING_REQUIRED_COMPONENT:frozen_root_commitment" not in errors:
                errors.append("MISSING_FROZEN_ROOT_COMMITMENT")

    status = "PASS" if not errors else "FAIL"
    go = status == "PASS"
    return {
        "validator_version": VALIDATOR_VERSION,
        "validation_status": status,
        "GO_ALLOWED": go,
        "errors": errors,
        "computed_disagreement_count": computed_dc,
        "computed_disagreements": computed_disagreements if computed_dc else [],
        "note": (
            "INTEGRITY VALIDATOR ≠ RELEVANCE JUDGE. "
            "v1.3: completeness + A/B-derived disagreement + real SHA-256 + frozen root."
        ),
    }


def build_frozen_materials(package: dict[str, Any], require_conditional: bool = False) -> dict[str, Any]:
    """Helper for fixtures: compute digests + frozen root from package artifacts."""
    digests = compute_artifact_sha256_map(package, require_conditional=require_conditional)
    root = frozen_root_from_digests(digests)
    return {
        "artifact_sha256": digests,
        "frozen_integrity_manifest": {
            "protocol_version": "fm17-pre-v1.3",
            "created_before_evaluation_overlay": True,
            "artifact_sha256": dict(digests),
        },
        "frozen_root_commitment": {
            "root_sha256": root,
            "freeze_declared_before_overlay": True,
            "anchor_class": "detached_frozen_manifest_digest",
        },
        "root_sha256": root,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FM-17-pre fail-closed integrity validator v1.3")
    p.add_argument("package_json", nargs="?", help="Path to TEST_FIXTURE package JSON")
    p.add_argument("--debug", action="store_true", help="Print errors; never forces GO_ALLOWED")
    args = p.parse_args(argv)
    if not args.package_json:
        print("usage: validate_fm17_pre_package.py PACKAGE.json", file=sys.stderr)
        return 1
    data = json.loads(Path(args.package_json).read_text(encoding="utf-8"))
    result = validate_package(data)
    print(json.dumps(result, indent=2))
    if result["validation_status"] != "PASS":
        result["GO_ALLOWED"] = False
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
