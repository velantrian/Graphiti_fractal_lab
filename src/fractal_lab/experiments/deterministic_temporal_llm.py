"""Deterministic temporal LLM stub for P5 contradiction / EdgeTimestamps labs.

Dedicated client — do NOT use DeterministicLLMClient for P5 conclusions:
that stub returns contradicted_facts=[] and EdgeTimestamps valid_at/invalid_at None.

Parses Graphiti 0.29.3 EdgeDuplicate context (EXISTING FACTS + FACT INVALIDATION
CANDIDATES) and selects the OLD marker index from context rather than hardcoding.
"""

from __future__ import annotations

import ast
import json
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.prompts.models import Message

from fractal_lab.experiments.deterministic_providers import (
    MARKER_RE,
    NAME_RE,
    _entity_names_from_text,
    _extract_episode_blob,
    _messages_text,
    _parse_json_list_block,
)

# P5 + P6 temporal markers (P6 reuses this client; keep P5 aliases)
P5_OLD_RE = re.compile(r"P5_OLD_[A-Za-z0-9_-]+")
P5_NEW_RE = re.compile(r"P5_NEW_[A-Za-z0-9_-]+")
P5_ANY_RE = re.compile(r"P5_(?:OLD|NEW)_[A-Za-z0-9_-]+")
TEMPORAL_OLD_RE = re.compile(r"P[56]_OLD_[A-Za-z0-9_-]+")
TEMPORAL_NEW_RE = re.compile(r"P[56]_NEW_[A-Za-z0-9_-]+")
TEMPORAL_LATE_OLD_RE = re.compile(r"P6_LATE_OLD_[A-Za-z0-9_-]+")
TEMPORAL_ANY_RE = re.compile(r"P[56]_(?:OLD|NEW|LATE_OLD)_[A-Za-z0-9_-]+")

# Extend marker recognition used by shared helpers when blob scraping
_EXTENDED_MARKER_RE = re.compile(
    r"(?:VELANTRIM_FALKOR_E2E_|A_ONLY_|B_ONLY_|P5_OLD_|P5_NEW_|P6_OLD_|P6_NEW_|P6_LATE_OLD_)[A-Za-z0-9_-]+"
)


def _tag_inner(text: str, start_tag: str, end_tag: str) -> str:
    if start_tag not in text:
        return ""
    i = text.index(start_tag) + len(start_tag)
    j = text.find(end_tag, i)
    if j == -1:
        return text[i:].strip()
    return text[i:j].strip()


def _parse_idx_fact_list(block: str) -> list[dict[str, Any]]:
    """Parse list of {idx, fact} from prompt (JSON or Python repr)."""
    block = (block or "").strip()
    if not block or block in {"[]", "null", "None"}:
        return []
    # Prefer JSON
    try:
        data = json.loads(block)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict) and "idx" in x]
    except json.JSONDecodeError:
        pass
    # Python repr from f-string interpolation of list[dict]
    try:
        data = ast.literal_eval(block)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict) and "idx" in x]
    except (SyntaxError, ValueError):
        pass
    # Regex fallback: idx + nearby fact
    out: list[dict[str, Any]] = []
    for m in re.finditer(
        r"['\"]?idx['\"]?\s*[:=]\s*(\d+).*?['\"]?fact['\"]?\s*[:=]\s*['\"](.+?)['\"]",
        block,
        flags=re.DOTALL,
    ):
        out.append({"idx": int(m.group(1)), "fact": m.group(2)})
    return out


def _normalize_iso_z(value: str | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return dt.astimezone(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = str(value).strip()
    # Strip trailing comments like "# ISO 8601..."
    if "#" in s:
        s = s.split("#", 1)[0].strip()
    if not s or s.lower() in {"none", "null"}:
        return None
    # Tolerate "2026-01-01 10:00:00+00:00"
    s = s.replace(" ", "T") if "T" not in s and " " in s else s
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.astimezone(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        # Last-ditch: already looks like ISO
        if re.match(r"\d{4}-\d{2}-\d{2}T", s):
            if s.endswith("Z"):
                return s
            return s.replace("+00:00", "Z")
        return None


def _reference_time_from_text(text: str) -> str | None:
    for start, end in (
        ("<REFERENCE_TIME>", "</REFERENCE_TIME>"),
        ("<REFERENCE TIME>", "</REFERENCE TIME>"),
    ):
        inner = _tag_inner(text, start, end)
        if inner:
            return _normalize_iso_z(inner)
    # Fallback: ISO-looking token near "reference"
    m = re.search(
        r"reference[_\s]?time[^0-9]*(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return _normalize_iso_z(m.group(1))
    return None


def _p5_entities_from_blob(blob: str) -> list[str]:
    """Ordered entity names for ProjectOrion temporal fixture."""
    names: list[str] = []
    seen: set[str] = set()

    def add(n: str) -> None:
        key = n.strip()
        if not key or key.lower() in seen:
            return
        # Skip markers / prompt junk as entity names
        if TEMPORAL_ANY_RE.fullmatch(key) or P5_ANY_RE.fullmatch(key) or MARKER_RE.fullmatch(key):
            return
        if key.lower() in {
            "current", "message", "entity", "entities", "runtime_language",
            "owned_by", "has_owner", "project", "uses", "language", "marker",
            "token", "lab", "episode", "fact", "json",
        }:
            return
        seen.add(key.lower())
        names.append(key)

    # Prefer known fixture nouns in stable order
    for preferred in ("ProjectOrion", "Python", "Rust", "Alice", "Bob"):
        if re.search(rf"\b{re.escape(preferred)}\b", blob):
            add(preferred)

    for m in NAME_RE.findall(blob):
        add(m)

    if "ProjectOrion" not in seen and "projectorion" not in seen:
        # Still try case-insensitive
        if re.search(r"project\s*orion", blob, flags=re.IGNORECASE):
            add("ProjectOrion")

    if len(names) < 2:
        # Ensure extractable pair
        if "ProjectOrion" not in {n for n in names}:
            names.insert(0, "ProjectOrion")
        if len(names) < 2:
            names.append("LabObject")
    return names


class DeterministicTemporalLLMClient(LLMClient):
    """Schema-aware stub for temporal contradiction + EdgeTimestamps (P5/P6)."""

    def __init__(self) -> None:
        super().__init__(
            config=LLMConfig(api_key="deterministic-temporal-lab-key", model="deterministic-temporal"),
            cache=False,
        )
        # Decision receipts for artifacts (EdgeDuplicate / timestamps)
        self.decisions: list[dict[str, Any]] = []

    def clear_decisions(self) -> None:
        self.decisions.clear()

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, Any]:
        if response_model is None:
            return {"content": "deterministic-temporal-noop"}

        name = response_model.__name__
        text_all = _messages_text(messages)
        blob = _extract_episode_blob(messages)
        # Prefer episode text that includes P5 markers even if tag scrape missed
        if not TEMPORAL_ANY_RE.search(blob):
            markers = _EXTENDED_MARKER_RE.findall(text_all)
            if markers and ("ProjectOrion" in text_all or "Python" in text_all or "Rust" in text_all):
                # Reconstruct a minimal blob from CURRENT_MESSAGE / TEXT if present
                for start, end in (
                    ("<CURRENT_MESSAGE>", "</CURRENT_MESSAGE>"),
                    ("<CURRENT MESSAGE>", "</CURRENT MESSAGE>"),
                    ("<TEXT>", "</TEXT>"),
                ):
                    inner = _tag_inner(text_all, start, end)
                    if inner and (TEMPORAL_ANY_RE.search(inner) or "ProjectOrion" in inner):
                        blob = inner
                        break

        if name == "ExtractedEntities":
            entities = _p5_entities_from_blob(blob or text_all)
            return {
                "extracted_entities": [
                    {"name": n, "entity_type_id": 0, "episode_indices": [0]} for n in entities
                ]
            }

        if name == "ExtractedEdges":
            return self._extracted_edges(messages, blob, text_all)

        if name == "NodeResolutions":
            return self._node_resolutions(text_all)

        if name == "EdgeDuplicate":
            return self._edge_duplicate(text_all)

        if name == "EdgeTimestamps":
            return self._edge_timestamps(text_all)

        if name == "BatchEdgeTimestamps":
            ref = _reference_time_from_text(text_all)
            # Count facts roughly
            n = max(1, text_all.count('"fact"') + text_all.count("'fact'"))
            n = min(n, 32)
            stamps = [{"valid_at": ref, "invalid_at": None} for _ in range(n)]
            self.decisions.append(
                {
                    "model": "BatchEdgeTimestamps",
                    "reference_time": ref,
                    "count": n,
                }
            )
            return {"timestamps": stamps}

        if name == "SummarizedEntities":
            names = _p5_entities_from_blob(blob or text_all)
            return {
                "summaries": [
                    {"name": n, "summary": f"Deterministic temporal summary for {n}."} for n in names
                ]
            }

        if name in {"Summary", "EntitySummary"}:
            return {"summary": f"Deterministic temporal summary. {(blob or '')[:180]}".strip()}

        if name == "SummaryDescription":
            return {"description": "Deterministic temporal one-sentence summary description."}

        if name == "SagaSummary":
            return {"summary": "Deterministic temporal saga summary."}

        # Attribute / unknown models: empty-safe schema fill
        try:
            schema = response_model.model_json_schema()
            props = schema.get("properties") or {}
            out: dict[str, Any] = {}
            for key, prop in props.items():
                t = prop.get("type")
                if t == "array":
                    out[key] = []
                elif t == "object":
                    out[key] = {}
                elif t == "integer":
                    out[key] = 0
                elif t == "number":
                    out[key] = 0.0
                elif t == "boolean":
                    out[key] = False
                else:
                    out[key] = None
            for req in schema.get("required") or []:
                if out.get(req) is None:
                    out[req] = ""
            return out
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"DeterministicTemporalLLMClient cannot synthesize response for {name}: {exc}"
            ) from exc

    def _extracted_edges(
        self, messages: list[Message], blob: str, text_all: str
    ) -> dict[str, Any]:
        # Entity names from ENTITIES block in prompt
        entity_names: list[str] = []
        entities_block = _tag_inner(text_all, "<ENTITIES>", "</ENTITIES>")
        if entities_block:
            try:
                data = json.loads(entities_block)
                if isinstance(data, list):
                    for obj in data:
                        if isinstance(obj, dict) and isinstance(obj.get("name"), str):
                            entity_names.append(obj["name"])
            except json.JSONDecodeError:
                for m in re.findall(r'"name"\s*:\s*"([^"]+)"', entities_block):
                    entity_names.append(m)
        if not entity_names:
            entity_names = _p5_entities_from_blob(blob or text_all)

        # Dedup preserve order
        uniq: list[str] = []
        seen: set[str] = set()
        for n in entity_names:
            if n.lower() not in seen:
                seen.add(n.lower())
                uniq.append(n)

        def has(name: str) -> bool:
            return name.lower() in seen

        def pick(*candidates: str) -> str | None:
            for c in candidates:
                if has(c):
                    for u in uniq:
                        if u.lower() == c.lower():
                            return u
            return None

        subject = pick("ProjectOrion") or (uniq[0] if uniq else "ProjectOrion")
        ref = _reference_time_from_text(text_all)

        # Prefer episode blob markers — text_all may contain EXISTING FACTS / prior
        # markers from Graphiti context and must not pollute extraction (P6-A late).
        source_blob = blob or ""
        late_markers = TEMPORAL_LATE_OLD_RE.findall(source_blob)
        old_markers = TEMPORAL_OLD_RE.findall(source_blob)
        new_markers = TEMPORAL_NEW_RE.findall(source_blob)
        if not (late_markers or old_markers or new_markers):
            late_markers = TEMPORAL_LATE_OLD_RE.findall(text_all)
            old_markers = TEMPORAL_OLD_RE.findall(text_all)
            new_markers = TEMPORAL_NEW_RE.findall(text_all)

        edges: list[dict[str, Any]] = []

        # Language fact: decide language from episode blob first (not marker pollution)
        lang = None
        marker_bit = None
        if re.search(r"\bRust\b", source_blob):
            lang = pick("Rust") or "Rust"
            marker_bit = new_markers[0] if new_markers else "P5_NEW_MISSING"
        elif re.search(r"\bPython\b", source_blob):
            lang = pick("Python") or "Python"
            marker_bit = (
                late_markers[0]
                if late_markers
                else (old_markers[0] if old_markers else "P5_OLD_MISSING")
            )
        elif new_markers:
            lang = pick("Rust") or "Rust"
            marker_bit = new_markers[0]
        elif late_markers or old_markers:
            lang = pick("Python") or "Python"
            marker_bit = late_markers[0] if late_markers else old_markers[0]

        if lang is not None:
            # Ensure lang is in entity list for Graphiti validation — use listed name
            if not has(lang):
                # Still emit; Graphiti may reject if not in ENTITIES — prefer listed
                for u in uniq:
                    if u.lower() in {"python", "rust"}:
                        lang = u
                        break
            edges.append(
                {
                    "source_entity_name": subject,
                    "target_entity_name": lang if has(lang) else (pick("Python", "Rust") or lang),
                    "relation_type": "RUNTIME_LANGUAGE",
                    "fact": (
                        f"{subject} uses {lang} as its RUNTIME_LANGUAGE. "
                        f"Retrieval marker {marker_bit}."
                    ),
                    "valid_at": ref,
                    "invalid_at": None,
                    "episode_indices": [0],
                }
            )

        # Owner / unrelated fact
        alice = pick("Alice")
        if alice and re.search(r"\bAlice\b", source_blob) and re.search(
            r"\b(owner|owned|owns)\b", source_blob, flags=re.IGNORECASE
        ):
            edges.append(
                {
                    "source_entity_name": subject,
                    "target_entity_name": alice,
                    "relation_type": "OWNED_BY",
                    "fact": f"{subject} is owned by {alice}.",
                    "valid_at": ref,
                    "invalid_at": None,
                    "episode_indices": [0],
                }
            )

        if not edges:
            # Fallback minimal edge so extraction does not no-op
            tgt = uniq[1] if len(uniq) > 1 else "LabObject"
            marker = (old_markers or new_markers or ["NO_MARKER"])[0]
            edges.append(
                {
                    "source_entity_name": subject,
                    "target_entity_name": tgt,
                    "relation_type": "RELATED_TO",
                    "fact": f"{subject} is related to {tgt} mentioning {marker}.",
                    "valid_at": ref,
                    "invalid_at": None,
                    "episode_indices": [0],
                }
            )

        self.decisions.append(
            {
                "model": "ExtractedEdges",
                "reference_time": ref,
                "edges": [
                    {
                        "relation_type": e["relation_type"],
                        "fact": e["fact"],
                        "valid_at": e["valid_at"],
                    }
                    for e in edges
                ],
            }
        )
        return {"edges": edges}

    def _node_resolutions(self, text_all: str) -> dict[str, Any]:
        extracted: list[dict[str, Any]] = []
        entities_block = _tag_inner(text_all, "<ENTITIES>", "</ENTITIES>")
        if entities_block:
            try:
                data = json.loads(entities_block)
                if isinstance(data, list):
                    extracted = [x for x in data if isinstance(x, dict) and "id" in x and "name" in x]
            except json.JSONDecodeError:
                pass
        if not extracted:
            for obj in _parse_json_list_block(text_all, ("id", "name")):
                if "id" in obj and "name" in obj:
                    extracted.append(obj)

        existing_block = _tag_inner(text_all, "<EXISTING ENTITIES>", "</EXISTING ENTITIES>")
        existing: list[dict[str, Any]] = []
        if existing_block:
            try:
                data = json.loads(existing_block)
                if isinstance(data, list):
                    existing = [x for x in data if isinstance(x, dict)]
            except json.JSONDecodeError:
                try:
                    data = ast.literal_eval(existing_block)
                    if isinstance(data, list):
                        existing = [x for x in data if isinstance(x, dict)]
                except (SyntaxError, ValueError):
                    pass

        name_to_candidate: dict[str, int] = {}
        for obj in existing:
            nm = obj.get("name")
            cid = obj.get("candidate_id", obj.get("id"))
            if isinstance(nm, str) and isinstance(cid, int):
                name_to_candidate[nm.lower()] = cid

        resolutions = []
        for obj in extracted:
            nm = str(obj["name"])
            dup = name_to_candidate.get(nm.lower(), -1)
            resolutions.append(
                {
                    "id": int(obj["id"]),
                    "name": nm,
                    "duplicate_candidate_id": dup,
                }
            )
        self.decisions.append(
            {
                "model": "NodeResolutions",
                "resolutions": resolutions,
                "existing_count": len(existing),
            }
        )
        return {"entity_resolutions": resolutions}

    def _edge_duplicate(self, text_all: str) -> dict[str, Any]:
        existing_block = _tag_inner(text_all, "<EXISTING FACTS>", "</EXISTING FACTS>")
        invalidation_block = _tag_inner(
            text_all, "<FACT INVALIDATION CANDIDATES>", "</FACT INVALIDATION CANDIDATES>"
        )
        new_fact = _tag_inner(text_all, "<NEW FACT>", "</NEW FACT>")

        existing_items = _parse_idx_fact_list(existing_block)
        invalidation_items = _parse_idx_fact_list(invalidation_block)
        all_items = existing_items + invalidation_items

        contradicted: list[int] = []
        duplicate_facts: list[int] = []

        new_has_new_marker = bool(TEMPORAL_NEW_RE.search(new_fact))
        new_has_late_old = bool(TEMPORAL_LATE_OLD_RE.search(new_fact))
        new_is_language = bool(
            re.search(r"RUNTIME_LANGUAGE", new_fact, flags=re.IGNORECASE)
            or re.search(r"\b(uses|runtime)\b.*\b(Python|Rust)\b", new_fact, flags=re.IGNORECASE)
            or re.search(r"\b(Python|Rust)\b.*\b(runtime|language)\b", new_fact, flags=re.IGNORECASE)
        )
        new_lang = None
        if re.search(r"\bRust\b", new_fact):
            new_lang = "Rust"
        elif re.search(r"\bPython\b", new_fact):
            new_lang = "Python"

        def _is_owner_fact(fact: str) -> bool:
            return bool(re.search(r"\bOWNED_BY\b|\bowned by\b", fact, flags=re.IGNORECASE))

        # P5 / baseline T2: Rust (NEW) contradicts Python (OLD) — select OLD idx from context
        if new_has_new_marker or (new_is_language and new_lang == "Rust"):
            for item in all_items:
                fact = str(item.get("fact", ""))
                idx = int(item["idx"])
                if _is_owner_fact(fact):
                    continue
                if TEMPORAL_OLD_RE.search(fact):
                    contradicted.append(idx)
                    break
            if not contradicted:
                for item in all_items:
                    fact = str(item.get("fact", ""))
                    idx = int(item["idx"])
                    if _is_owner_fact(fact):
                        continue
                    if new_lang == "Rust" and re.search(r"\bPython\b", fact) and (
                        re.search(r"RUNTIME_LANGUAGE", fact, flags=re.IGNORECASE)
                        or re.search(r"language", fact, flags=re.IGNORECASE)
                    ):
                        contradicted.append(idx)
                        break

        # P6-A late add_episode (reference_time=T1, Python + P6_LATE_OLD): identify Rust T2
        # as contradiction candidate by parsing context (not hardcoded idx).
        elif new_has_late_old or (new_is_language and new_lang == "Python" and TEMPORAL_LATE_OLD_RE.search(new_fact + text_all)):
            for item in all_items:
                fact = str(item.get("fact", ""))
                idx = int(item["idx"])
                if _is_owner_fact(fact):
                    continue
                if TEMPORAL_NEW_RE.search(fact):
                    contradicted.append(idx)
                    break
            if not contradicted:
                for item in all_items:
                    fact = str(item.get("fact", ""))
                    idx = int(item["idx"])
                    if _is_owner_fact(fact):
                        continue
                    if re.search(r"\bRust\b", fact) and (
                        re.search(r"RUNTIME_LANGUAGE", fact, flags=re.IGNORECASE)
                        or re.search(r"language", fact, flags=re.IGNORECASE)
                    ):
                        contradicted.append(idx)
                        break

        # Exact duplicate (same marker) — rare in P5 path
        if not contradicted:
            for item in existing_items:
                fact = str(item.get("fact", ""))
                idx = int(item["idx"])
                if new_fact.strip() and fact.strip() == new_fact.strip():
                    duplicate_facts.append(idx)
                    break

        receipt = {
            "model": "EdgeDuplicate",
            "new_fact": new_fact,
            "existing_facts": existing_items,
            "invalidation_candidates": invalidation_items,
            "duplicate_facts": duplicate_facts,
            "contradicted_facts": contradicted,
            "selection_rule": (
                "P6_LATE_OLD→contradict Rust/P6_NEW from context"
                if (new_has_late_old or TEMPORAL_LATE_OLD_RE.search(new_fact))
                else "P5/P6_OLD marker index from context (else Python RUNTIME_LANGUAGE)"
            ),
        }
        self.decisions.append(receipt)
        return {"duplicate_facts": duplicate_facts, "contradicted_facts": contradicted}

    def _edge_timestamps(self, text_all: str) -> dict[str, Any]:
        ref = _reference_time_from_text(text_all)
        fact = _tag_inner(text_all, "<FACT>", "</FACT>")
        receipt = {
            "model": "EdgeTimestamps",
            "fact": fact[:200],
            "valid_at": ref,
            "invalid_at": None,
        }
        self.decisions.append(receipt)
        return {"valid_at": ref, "invalid_at": None}
