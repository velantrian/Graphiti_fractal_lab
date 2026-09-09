"""Deterministic LLM / embedder / cross-encoder stubs for offline Graphiti labs.

No network LLM calls. Responses are shaped to match Graphiti 0.29.3
prompt response_models so add_episode → search can pass with real evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.embedder.client import EMBEDDING_DIM, EmbedderClient, EmbedderConfig
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.prompts.models import Message

MARKER_RE = re.compile(r"VELANTRIM_FALKOR_E2E_[A-Za-z0-9_-]+")
# Proper-noun-ish tokens for synthetic fixtures (Alice, Bob, AcmeCorp, …)
NAME_RE = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:'[A-Za-z]+)?)\b")


def _messages_text(messages: list[Message]) -> str:
    return "\n".join(m.content for m in messages)


def _extract_episode_blob(messages: list[Message]) -> str:
    text = _messages_text(messages)
    # Graphiti extract_text uses <TEXT>; extract_message uses <CURRENT MESSAGE>
    for tag in (
        ("<TEXT>", "</TEXT>"),
        ("<CURRENT MESSAGE>", "</CURRENT MESSAGE>"),
        ("<CURRENT_MESSAGE>", "</CURRENT_MESSAGE>"),
        ("<MESSAGES>", "</MESSAGES>"),
        ("<NEW ENTITY>", "</NEW ENTITY>"),
        ("<NEW FACT>", "</NEW FACT>"),
    ):
        start, end = tag
        if start in text:
            i = text.index(start) + len(start)
            j = text.find(end, i)
            if j != -1:
                return text[i:j].strip()
    # Last resort: only lines that look like fixture content containing our marker
    markers = MARKER_RE.findall(text)
    if markers:
        # Return a synthetic minimal blob so entity extraction stays tight
        return " ".join(dict.fromkeys(markers))
    return ""


def _entity_names_from_text(blob: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        key = name.strip()
        if not key or key.lower() in seen:
            return
        # Skip common prompt words that look capitalized
        # Drop prompt junk / English function words
        if key.lower() in {
            "current", "message", "entity", "entities", "existing", "previous",
            "task", "important", "never", "respond", "json", "text", "guidelines",
            "example", "the", "a", "an", "and", "or", "for", "with", "from", "this",
            "that", "those", "these", "when", "if", "do", "be", "not", "only",
            "must", "always", "include", "could", "good", "bad", "types", "extract",
            "token", "unique", "retrieval", "lab", "confirmed", "mentions",
            "extractedentities", "extractededges", "noderesolutions",
            "summarizedentities", "edgeduplicate", "person", "location",
            "organization", "topic", "object", "dr",
        }:
            return
        if len(key) <= 2:
            return
        seen.add(key.lower())
        names.append(key)

    for m in MARKER_RE.findall(blob):
        add(m)
    for m in NAME_RE.findall(blob):
        add(m)

    # Always ensure at least two distinct entities so edges can form
    if len(names) == 0:
        add("LabSubject")
        add("LabObject")
    elif len(names) == 1:
        add("LabContext")

    return names


def _parse_json_list_block(text: str, key_hints: tuple[str, ...]) -> list[dict[str, Any]]:
    """Best-effort scrape of list-like JSON embedded in prompts."""
    for hint in key_hints:
        # Look for "hint": [ ... ] patterns that are already JSON in the prompt
        pass
    # Parse ENTITIES / extracted_nodes blocks printed via to_prompt_json
    for label in ("<ENTITIES>", "<EXISTING ENTITIES>", "<NEW ENTITY>"):
        if label not in text:
            continue
    try:
        # Find first JSON array of objects in the text
        match = re.search(r"\[\s*\{.*?\}\s*\]", text, flags=re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
    except json.JSONDecodeError:
        pass
    return []


def _entities_listed_in_prompt(messages: list[Message]) -> list[str]:
    text = _messages_text(messages)
    names: list[str] = []
    for obj in _parse_json_list_block(text, ("name",)):
        n = obj.get("name")
        if isinstance(n, str) and n.strip():
            names.append(n.strip())
    # Also pull from simple "name": "..." occurrences near ENTITIES
    if not names:
        for m in re.findall(r'"name"\s*:\s*"([^"]+)"', text):
            if m not in names:
                names.append(m)
    return names


class DeterministicLLMClient(LLMClient):
    """Schema-aware stub that returns valid Graphiti extraction structures."""

    def __init__(self) -> None:
        super().__init__(config=LLMConfig(api_key="deterministic-lab-key", model="deterministic"), cache=False)

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, Any]:
        if response_model is None:
            return {"content": "deterministic-noop"}

        name = response_model.__name__
        blob = _extract_episode_blob(messages)
        text_all = _messages_text(messages)

        if name == "ExtractedEntities":
            entities = _entity_names_from_text(blob)
            return {
                "extracted_entities": [
                    {"name": n, "entity_type_id": 0, "episode_indices": [0]} for n in entities
                ]
            }

        if name == "ExtractedEdges":
            names = _entities_listed_in_prompt(messages) or _entity_names_from_text(blob)
            # Deduplicate while preserving order
            uniq: list[str] = []
            seen: set[str] = set()
            for n in names:
                if n.lower() not in seen:
                    seen.add(n.lower())
                    uniq.append(n)
            if len(uniq) < 2:
                uniq = list(dict.fromkeys(uniq + ["LabSubject", "LabObject"]))
            markers = MARKER_RE.findall(blob) or MARKER_RE.findall(text_all)
            marker_bit = markers[0] if markers else "NO_MARKER"
            edges = []
            # Chain consecutive entities; put marker into every fact for BM25 recall
            for i in range(len(uniq) - 1):
                src, tgt = uniq[i], uniq[i + 1]
                edges.append(
                    {
                        "source_entity_name": src,
                        "target_entity_name": tgt,
                        "relation_type": "RELATED_TO",
                        "fact": (
                            f"{src} is related to {tgt} in lab fixture mentioning {marker_bit}. "
                            f"Episode excerpt: {blob[:400]}"
                        ),
                        "valid_at": None,
                        "invalid_at": None,
                        "episode_indices": [0],
                    }
                )
            # Also connect first→last if only one edge would omit a marker entity mid-list
            if len(uniq) >= 3:
                edges.append(
                    {
                        "source_entity_name": uniq[0],
                        "target_entity_name": uniq[-1],
                        "relation_type": "MENTIONS_MARKER",
                        "fact": f"{uniq[0]} shares context with {uniq[-1]} about {marker_bit}",
                        "valid_at": None,
                        "invalid_at": None,
                        "episode_indices": [0],
                    }
                )
            return {"edges": edges}

        if name == "NodeResolutions":
            # IDs are 0..N-1 relative indices of unresolved extracted nodes
            extracted = []
            # Prefer ENTITIES block ids
            for obj in _parse_json_list_block(text_all, ("id", "name")):
                if "id" in obj and "name" in obj:
                    extracted.append(obj)
            if not extracted:
                # Fall back: count '"id": <int>' near extracted nodes
                ids = [int(x) for x in re.findall(r'"id"\s*:\s*(\d+)', text_all)]
                names = re.findall(r'"name"\s*:\s*"([^"]+)"', text_all)
                for i, nid in enumerate(sorted(set(ids))):
                    nm = names[i] if i < len(names) else f"Entity_{nid}"
                    extracted.append({"id": nid, "name": nm})
            resolutions = []
            for obj in extracted:
                resolutions.append(
                    {
                        "id": int(obj["id"]),
                        "name": str(obj["name"]),
                        "duplicate_candidate_id": -1,
                    }
                )
            # If still empty, return empty list (resolve path may no-op)
            return {"entity_resolutions": resolutions}

        if name == "EdgeDuplicate":
            return {"duplicate_facts": [], "contradicted_facts": []}

        if name == "SummarizedEntities":
            names = _entities_listed_in_prompt(messages) or _entity_names_from_text(blob)
            return {
                "summaries": [
                    {"name": n, "summary": f"Deterministic summary for {n}."} for n in names
                ]
            }

        if name in {"Summary", "EntitySummary"}:
            return {"summary": f"Deterministic summary. {blob[:180]}".strip()}

        if name == "SummaryDescription":
            return {"description": "Deterministic one-sentence summary description."}

        if name == "EdgeTimestamps":
            return {"valid_at": None, "invalid_at": None}

        if name == "BatchEdgeTimestamps":
            # Count facts if possible; default one
            n = max(1, text_all.count('"fact"'))
            return {"timestamps": [{"valid_at": None, "invalid_at": None} for _ in range(min(n, 32))]}

        if name == "SagaSummary":
            return {"summary": "Deterministic saga summary."}

        # Attribute extraction / custom entity models: return empty/nullish fields
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
                    # string or unknown — prefer null when nullable
                    out[key] = None
            # Required string fields need something non-null
            for req in schema.get("required") or []:
                if out.get(req) is None:
                    out[req] = ""
            return out
        except Exception as exc:  # noqa: BLE001 — surface unknown models honestly
            raise RuntimeError(
                f"DeterministicLLMClient cannot synthesize response for {name}: {exc}"
            ) from exc


class DeterministicEmbedder(EmbedderClient):
    """Hash-based fixed-dimension embeddings; same text → same vector."""

    def __init__(self, embedding_dim: int | None = None) -> None:
        dim = embedding_dim if embedding_dim is not None else EMBEDDING_DIM
        self.config = EmbedderConfig(embedding_dim=dim)
        self.embedding_dim = dim

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Expand digest stream to fill dim
        values: list[float] = []
        block = digest
        while len(values) < self.embedding_dim:
            for i in range(len(block)):
                # Map byte to [-1, 1]
                values.append((block[i] / 127.5) - 1.0)
                if len(values) >= self.embedding_dim:
                    break
            block = hashlib.sha256(block).digest()
        # L2 normalize for stable cosine behavior
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    async def create(
        self, input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]]
    ) -> list[float]:
        if isinstance(input_data, str):
            text = input_data
        elif isinstance(input_data, list) and input_data and isinstance(input_data[0], str):
            text = " ".join(input_data)  # type: ignore[arg-type]
        else:
            text = str(input_data)
        return self._embed_one(text)

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in input_data_list]


class DeterministicCrossEncoder(CrossEncoderClient):
    """Stable lexical overlap ranks (no network)."""

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        q_tokens = set(query.lower().split())
        scored: list[tuple[str, float]] = []
        for i, p in enumerate(passages):
            p_tokens = set(p.lower().split())
            overlap = len(q_tokens & p_tokens)
            # Stable tie-break by index so order is deterministic
            score = float(overlap) + (1.0 / (i + 1000))
            scored.append((p, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
