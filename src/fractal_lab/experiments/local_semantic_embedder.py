"""Lab-only REAL semantic embedder adapter for Graphiti EmbedderClient (FM-14).

Uses a small local pretrained ONNX model via fastembed — NOT hash/random/lexical
stubs and NOT DeepSeek / OpenAI / Voyage / Cohere API keys.

API_COST=$0 (local). LOCAL_COMPUTE_COST=NOT_MEASURED.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from graphiti_core.embedder.client import EmbedderClient, EmbedderConfig

# Preferred small English semantic model (fastembed / ONNX quantized packaging).
DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"
DEFAULT_HF_SOURCE = "qdrant/bge-small-en-v1.5-onnx-q"
# Snapshot resolved from local fastembed cache after first download (refs/main).
DEFAULT_MODEL_REVISION = "52398278842ec682c6f32300af41344b1c0b0bb2"
DEFAULT_DIM = 384

_MODEL_LOCK = threading.Lock()
_MODEL_SINGLETON: Any = None
_MODEL_META: dict[str, Any] = {}


class RealEmbedderUnavailableError(RuntimeError):
    """Raised when no genuine pretrained local semantic embedder can be loaded."""


def _package_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for name in ("fastembed", "onnxruntime", "numpy"):
        try:
            mod = __import__(name)
            out[name] = getattr(mod, "__version__", "UNKNOWN")
        except Exception as exc:  # noqa: BLE001
            out[name] = f"MISSING:{type(exc).__name__}"
    return out


def _resolve_revision(cache_hint: str | None = None) -> str:
    """Best-effort read of HF-style refs/main under fastembed cache."""
    candidates = [
        Path("/tmp/fastembed_cache") / f"models--{DEFAULT_HF_SOURCE.replace('/', '--')}",
        Path.home() / ".cache" / "fastembed" / f"models--{DEFAULT_HF_SOURCE.replace('/', '--')}",
    ]
    if cache_hint:
        candidates.insert(0, Path(cache_hint))
    for base in candidates:
        ref = base / "refs" / "main"
        if ref.is_file():
            return ref.read_text(encoding="utf-8").strip()
    return DEFAULT_MODEL_REVISION


def load_fastembed_model(model_name: str = DEFAULT_MODEL_NAME) -> tuple[Any, dict[str, Any]]:
    """Load (or reuse) the local TextEmbedding model; return (model, meta)."""
    global _MODEL_SINGLETON, _MODEL_META
    with _MODEL_LOCK:
        if _MODEL_SINGLETON is not None and _MODEL_META.get("model_name") == model_name:
            return _MODEL_SINGLETON, dict(_MODEL_META)
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RealEmbedderUnavailableError(
                "fastembed not installed — cannot run REAL semantic embedder"
            ) from exc

        try:
            model = TextEmbedding(model_name=model_name)
        except Exception as exc:  # noqa: BLE001
            raise RealEmbedderUnavailableError(
                f"failed to load local semantic model {model_name!r}: {exc}"
            ) from exc

        # Probe dim + normalization on a fixed string
        probe = list(model.embed(["fm14_probe"]))[0]
        dim = len(probe)
        l2 = float(sum(x * x for x in probe)) ** 0.5
        revision = _resolve_revision()
        meta = {
            "provider": "local_fastembed",
            "framework": "fastembed+onnxruntime",
            "model_name": model_name,
            "hf_source_repo": DEFAULT_HF_SOURCE if model_name == DEFAULT_MODEL_NAME else model_name,
            "model_revision": revision,
            "model_file": "model_optimized.onnx",
            "embedding_dim": dim,
            "normalization": "L2_unit_norm_from_model" if abs(l2 - 1.0) < 1e-3 else f"raw_l2={l2:.6f}",
            "device": "cpu",
            "dtype": "float32",
            "package_versions": _package_versions(),
            "API_COST_USD": 0,
            "LOCAL_COMPUTE_COST": "NOT_MEASURED",
            "embedding_label": "REAL_SEMANTIC_EMBEDDING",
            "NOT_hash_random_lexical_fixture": True,
        }
        _MODEL_SINGLETON = model
        _MODEL_META = meta
        return model, dict(meta)


class LocalSemanticEmbedder(EmbedderClient):
    """Graphiti EmbedderClient backed by a small local pretrained semantic model."""

    embedding_label = "REAL_SEMANTIC_EMBEDDING"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        *,
        embedding_dim: int | None = None,
    ) -> None:
        self.model_name = model_name
        self._model, self.meta = load_fastembed_model(model_name)
        dim = embedding_dim if embedding_dim is not None else int(self.meta["embedding_dim"])
        self.config = EmbedderConfig(embedding_dim=dim)
        self.embedding_dim = dim

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        # fastembed returns generators of numpy arrays / lists
        vectors = list(self._model.embed(texts))
        out: list[list[float]] = []
        for v in vectors:
            arr = [float(x) for x in v]
            if len(arr) != self.embedding_dim:
                # Truncate or refuse — do not pad with zeros (would break semantics)
                if len(arr) > self.embedding_dim:
                    arr = arr[: self.embedding_dim]
                else:
                    raise RuntimeError(
                        f"embed dim {len(arr)} < configured {self.embedding_dim}"
                    )
            out.append(arr)
        return out

    def _coerce_text(
        self, input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]]
    ) -> str:
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, list) and input_data and isinstance(input_data[0], str):
            # Match Graphiti call sites that pass [text]; OpenAI path embeds list and
            # returns data[0]. For a single-element list return that string.
            if len(input_data) == 1:
                return str(input_data[0])
            return " ".join(str(x) for x in input_data)
        return str(input_data)

    async def create(
        self, input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]]
    ) -> list[float]:
        text = self._coerce_text(input_data)
        return self._embed_texts([text])[0]

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        if not input_data_list:
            return []
        return self._embed_texts(list(input_data_list))

    def fingerprint(self) -> dict[str, Any]:
        """Stable artifact for embedding_fingerprint.json (no secrets)."""
        probe_texts = [
            "Alice works on Project Orion.",
            "Who works on Project Orion?",
            "Who works on Project Zephyr?",
        ]
        vecs = self._embed_texts(probe_texts)
        digests = []
        for t, v in zip(probe_texts, vecs, strict=True):
            raw = ",".join(f"{x:.8f}" for x in v).encode("utf-8")
            digests.append(
                {
                    "text": t,
                    "dim": len(v),
                    "sha256_hex": hashlib.sha256(raw).hexdigest(),
                    "l2_norm": float(sum(x * x for x in v)) ** 0.5,
                    "head8": v[:8],
                }
            )
        return {
            **self.meta,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "smoke_probes": digests,
            "SECRET_LOGGED": "NO",
            "DEEPSEEK_KEY_USED_FOR_EMBEDDINGS": False,
        }


def cosine_similarity(a: list[float], b: list[float]) -> float:
    import math

    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return float(dot / (na * nb))


def probe_deepseek_embeddings_endpoint(api_key: str | None) -> dict[str, Any]:
    """Record that DeepSeek /embeddings is unavailable — do not misuse the key elsewhere."""
    import urllib.error
    import urllib.request

    result: dict[str, Any] = {
        "probed": True,
        "base_url": "https://api.deepseek.com",
        "paths": [],
        "usable": False,
        "SECRET_LOGGED": "NO",
        "DEEPSEEK_KEY_MISUSED_FOR_OTHER_PROVIDER": False,
        "decision": "USE_LOCAL_FASTEMBED",
    }
    if not api_key:
        result["error"] = "NO_DEEPSEEK_API_KEY"
        result["decision"] = "USE_LOCAL_FASTEMBED"
        return result

    for path, model in (
        ("/embeddings", "deepseek-embedding"),
        ("/v1/embeddings", "text-embedding-3-small"),
    ):
        entry: dict[str, Any] = {"path": path, "model_attempted": model}
        req = urllib.request.Request(
            f"https://api.deepseek.com{path}",
            data=json.dumps({"model": model, "input": "ping"}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                entry["status"] = resp.status
                entry["body_preview"] = resp.read()[:200].decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            entry["status"] = exc.code
            try:
                entry["body_preview"] = exc.read()[:200].decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                entry["body_preview"] = ""
            entry["error"] = f"HTTPError {exc.code}"
        except Exception as exc:  # noqa: BLE001
            entry["status"] = None
            entry["error"] = type(exc).__name__
            entry["message"] = str(exc)[:200]
        result["paths"].append(entry)

    statuses = [p.get("status") for p in result["paths"]]
    result["usable"] = any(s == 200 for s in statuses)
    if not result["usable"]:
        result["decision"] = "USE_LOCAL_FASTEMBED"
        result["note"] = (
            "DeepSeek /embeddings returned non-200 (typically 404). "
            "Do not put DEEPSEEK_API_KEY into another provider embedding endpoint."
        )
    return result
