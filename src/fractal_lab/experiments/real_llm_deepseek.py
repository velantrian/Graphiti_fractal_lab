"""REAL_LLM DeepSeek provider wiring for lab MemoryOps (FM-11/FM-12).

Classification: REAL_LLM_EXTRACTION + DETERMINISTIC_EMBEDDING.

- REQUESTED_MODEL = deepseek-v4-pro exactly (no flash/chat fallback)
- Expected version label: DeepSeek-V4-Pro-0813 (API may only return model id)
- Context Caching is provider-automatic — do NOT implement custom KV cache
- Never sets or uses OPENAI_API_KEY; never logs the raw DEEPSEEK_API_KEY
- Embedder remains DeterministicEmbedder (via open_lab_graphiti)
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import openai
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.llm_client.errors import EmptyResponseError, RateLimitError
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.prompts.models import Message

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
REQUESTED_MODEL = "deepseek-v4-pro"
EXPECTED_VERSION_LABEL = "DeepSeek-V4-Pro-0813"
STRUCTURED_OUTPUT_MODE = "json_object"
BOX_SECRETS_PATH = Path("/home/box/agent-data/box-secrets.json")

# Official DeepSeek pricing used ONLY for optional ESTIMATED_COST (≠ ACTUAL_BILLED_COST).
# Amounts are USD per 1M tokens; update if DeepSeek publishes new rates.
# Cache hit tokens billed at cache-hit input rate when known; else treated as miss.
# Official DeepSeek docs (api-docs.deepseek.com) as of 2026-09-10:
# deepseek-v4-pro / MODEL VERSION DeepSeek-V4-Pro-0813
# Off-peak used as default estimate basis; peak is 2x.
ESTIMATED_PRICING_USD_PER_1M = {
    "input_cache_hit_offpeak": 0.022,
    "input_cache_miss_offpeak": 0.66,
    "output_offpeak": 1.98,
    "input_cache_hit_peak": 0.044,
    "input_cache_miss_peak": 1.32,
    "output_peak": 3.96,
    # Convenience aliases used by estimate_cost_usd (off-peak default)
    "input_cache_hit": 0.022,
    "input_cache_miss": 0.66,
    "output": 1.98,
    "source": "https://api-docs.deepseek.com/quick_start/pricing (fetched 2026-09-10)",
    "model_version_label": "DeepSeek-V4-Pro-0813",
    "label": "ESTIMATED_COST ≠ ACTUAL_BILLED_COST",
    "note": "From 2026-09-14 12:00 Beijing, deepseek-v4-pro routes to V4.1 Flash pricing",
}


class DeepSeekUnavailableError(RuntimeError):
    """Raised when deepseek-v4-pro is unavailable — do NOT silently fall back."""


def load_deepseek_api_key() -> tuple[str, str]:
    """Return (api_key, source) from process env or box-secrets. Never print the key."""
    env = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if env:
        return env, "env:DEEPSEEK_API_KEY"
    if BOX_SECRETS_PATH.is_file():
        data = json.loads(BOX_SECRETS_PATH.read_text(encoding="utf-8"))
        secrets = data.get("secrets") if isinstance(data, dict) else None
        if isinstance(secrets, dict):
            key = (secrets.get("DEEPSEEK_API_KEY") or "").strip()
            if key:
                os.environ["DEEPSEEK_API_KEY"] = key
                return key, "box-secrets:secrets.DEEPSEEK_API_KEY"
    raise DeepSeekUnavailableError(
        "DEEPSEEK_API_KEY missing from process env and box-secrets.json"
    )


def scrub_secret(text: str, api_key: str | None = None) -> str:
    """Redact API key substrings from error/log text."""
    out = str(text)
    key = api_key
    if not key:
        key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip() or None
    if key and key in out:
        out = out.replace(key, "REDACTED")
    return out


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def extract_usage_fields(usage: Any) -> dict[str, Any]:
    """Pull token + cache counters from an OpenAI-compatible usage object."""
    if usage is None:
        return {
            "prompt_tokens": "UNKNOWN",
            "completion_tokens": "UNKNOWN",
            "total_tokens": "UNKNOWN",
            "prompt_cache_hit_tokens": "UNKNOWN",
            "prompt_cache_miss_tokens": "UNKNOWN",
            "cached_tokens_detail": "UNKNOWN",
            "CACHE_USAGE": "UNKNOWN",
        }

    dump: dict[str, Any] = {}
    if hasattr(usage, "model_dump"):
        dump = usage.model_dump()
    elif isinstance(usage, dict):
        dump = dict(usage)

    prompt_tokens = _as_int(dump.get("prompt_tokens"))
    completion_tokens = _as_int(dump.get("completion_tokens"))
    total_tokens = _as_int(dump.get("total_tokens"))

    hit = dump.get("prompt_cache_hit_tokens")
    miss = dump.get("prompt_cache_miss_tokens")
    # Fallbacks some SDKs nest under prompt_tokens_details.cached_tokens
    details = dump.get("prompt_tokens_details") or {}
    if not isinstance(details, dict) and hasattr(details, "model_dump"):
        details = details.model_dump()
    cached_detail = None
    if isinstance(details, dict):
        cached_detail = details.get("cached_tokens")

    hit_i = _as_int(hit)
    miss_i = _as_int(miss)
    if hit_i is None and cached_detail is not None:
        hit_i = _as_int(cached_detail)
    if miss_i is None and prompt_tokens is not None and hit_i is not None:
        miss_i = max(prompt_tokens - hit_i, 0)

    cache_usage = "OBSERVED" if (hit_i is not None or miss_i is not None) else "UNKNOWN"
    hit_miss = "UNKNOWN"
    if hit_i is not None and miss_i is not None:
        if hit_i > 0 and miss_i == 0:
            hit_miss = "CACHE_HIT"
        elif hit_i > 0:
            hit_miss = "PARTIAL_CACHE_HIT"
        else:
            hit_miss = "CACHE_MISS"

    return {
        "prompt_tokens": prompt_tokens if prompt_tokens is not None else "UNKNOWN",
        "completion_tokens": completion_tokens if completion_tokens is not None else "UNKNOWN",
        "total_tokens": total_tokens if total_tokens is not None else "UNKNOWN",
        "prompt_cache_hit_tokens": hit_i if hit_i is not None else "UNKNOWN",
        "prompt_cache_miss_tokens": miss_i if miss_i is not None else "UNKNOWN",
        "cached_tokens_detail": cached_detail if cached_detail is not None else "UNKNOWN",
        "CACHE_USAGE": cache_usage,
        "hit_miss": hit_miss,
        "reasoning_tokens": _as_int(
            ((dump.get("completion_tokens_details") or {}) or {}).get("reasoning_tokens")
            if isinstance(dump.get("completion_tokens_details"), dict)
            else getattr(dump.get("completion_tokens_details"), "reasoning_tokens", None)
        ),
    }


def estimate_cost_usd(hit: int, miss: int, completion: int) -> dict[str, Any]:
    """Optional estimate only — never claim ACTUAL billed cost."""
    p = ESTIMATED_PRICING_USD_PER_1M
    cost = (
        (miss / 1_000_000.0) * float(p["input_cache_miss"])
        + (hit / 1_000_000.0) * float(p["input_cache_hit"])
        + (completion / 1_000_000.0) * float(p["output"])
    )
    return {
        "ESTIMATED_COST_USD": round(cost, 8),
        "label": "ESTIMATED_COST ≠ ACTUAL_BILLED_COST",
        "pricing_table": p,
        "ACTUAL_BILLED_COST": "NOT_RETURNED_BY_API",
    }


@dataclass
class PerRequestUsage:
    request_index: int
    requested_model: str
    actual_model: str
    request_utc_start: str
    request_utc_end: str
    latency_ms: float
    prompt_tokens: int | str
    completion_tokens: int | str
    total_tokens: int | str
    cache_hit_tokens: int | str
    cache_miss_tokens: int | str
    hit_miss: str
    system_fingerprint: str | None = None
    prompt_name: str | None = None
    cold_or_warm: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_index": self.request_index,
            "REQUESTED_MODEL": self.requested_model,
            "ACTUAL_MODEL": self.actual_model,
            "request_utc_start": self.request_utc_start,
            "request_utc_end": self.request_utc_end,
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cache_hit_tokens": self.cache_hit_tokens,
            "cache_miss_tokens": self.cache_miss_tokens,
            "hit_miss": self.hit_miss,
            "cold_or_warm": self.cold_or_warm,
            "system_fingerprint": self.system_fingerprint,
            "prompt_name": self.prompt_name,
            "note": "CACHE_HIT ≠ better semantic result; cache is cost/latency only",
        }


@dataclass
class RealLlmCallStats:
    """Aggregated + per-request usage/cache counters from live API responses."""

    generate_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    usage_observed: bool = False
    cache_fields_observed: bool = False
    actual_models_seen: list[str] = field(default_factory=list)
    system_fingerprints: list[str] = field(default_factory=list)
    per_request: list[PerRequestUsage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    billed_cost_actual: Any = "NOT_RETURNED_BY_API"

    def record_request(self, req: PerRequestUsage) -> None:
        self.per_request.append(req)
        if isinstance(req.prompt_tokens, int):
            self.prompt_tokens += req.prompt_tokens
            self.usage_observed = True
        if isinstance(req.completion_tokens, int):
            self.completion_tokens += req.completion_tokens
            self.usage_observed = True
        if isinstance(req.total_tokens, int):
            self.total_tokens += req.total_tokens
        if isinstance(req.cache_hit_tokens, int):
            self.cache_hit_tokens += req.cache_hit_tokens
            self.cache_fields_observed = True
        if isinstance(req.cache_miss_tokens, int):
            self.cache_miss_tokens += req.cache_miss_tokens
            self.cache_fields_observed = True
        if req.actual_model and req.actual_model not in self.actual_models_seen:
            self.actual_models_seen.append(req.actual_model)
        if req.system_fingerprint and req.system_fingerprint not in self.system_fingerprints:
            self.system_fingerprints.append(req.system_fingerprint)

    def cache_effect(self) -> str:
        if not self.cache_fields_observed:
            return "unknown"
        if self.cache_hit_tokens > 0:
            return "observed"
        return "not_observed"

    def to_dict(self) -> dict[str, Any]:
        est = None
        if self.usage_observed:
            est = estimate_cost_usd(
                self.cache_hit_tokens,
                self.cache_miss_tokens if self.cache_fields_observed else self.prompt_tokens,
                self.completion_tokens,
            )
        return {
            "generate_calls": self.generate_calls,
            "TOKEN_USAGE": {
                "prompt_tokens": self.prompt_tokens if self.usage_observed else "UNKNOWN",
                "completion_tokens": self.completion_tokens if self.usage_observed else "UNKNOWN",
                "total_tokens": self.total_tokens if self.usage_observed else "UNKNOWN",
                "observed": self.usage_observed,
            },
            "CACHE_HIT_TOKENS": {
                "total": self.cache_hit_tokens if self.cache_fields_observed else "UNKNOWN",
                "per_request": [
                    r.cache_hit_tokens for r in self.per_request
                ],
            },
            "CACHE_MISS_TOKENS": {
                "total": self.cache_miss_tokens if self.cache_fields_observed else "UNKNOWN",
                "per_request": [
                    r.cache_miss_tokens for r in self.per_request
                ],
            },
            "CACHE_EFFECT": self.cache_effect(),
            "CACHE": "ENABLED_BY_PROVIDER_DEFAULT",
            "ACTUAL_MODELS_SEEN": list(self.actual_models_seen) or ["UNKNOWN"],
            "system_fingerprints": list(self.system_fingerprints),
            "COST": {
                "ACTUAL_BILLED_COST": self.billed_cost_actual,
                "ESTIMATED_COST": est,
            },
            "per_request": [r.to_dict() for r in self.per_request],
            "errors": [scrub_secret(e) for e in self.errors],
            "SECRET_LOGGED": "NO",
        }


class CountingOpenAIGenericClient(OpenAIGenericClient):
    """OpenAIGenericClient that records live model id, usage, and cache counters.

    Overrides _generate_response so usage fields are not discarded by the base client.
    Does NOT implement custom KV cache — DeepSeek Context Caching is automatic.
    """

    def __init__(self, *args: Any, stats: RealLlmCallStats | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.stats = stats if stats is not None else RealLlmCallStats()
        self._last_prompt_name: str | None = None

    async def generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int | None = None,
        model_size: ModelSize | None = None,
        group_id: str | None = None,
        prompt_name: str | None = None,
        *,
        attribute_extraction: bool = False,
    ) -> dict[str, Any]:
        self._last_prompt_name = prompt_name
        self.stats.generate_calls += 1
        try:
            return await super().generate_response(
                messages,
                response_model=response_model,
                max_tokens=max_tokens,
                model_size=model_size if model_size is not None else ModelSize.medium,
                group_id=group_id,
                prompt_name=prompt_name,
                attribute_extraction=attribute_extraction,
            )
        except Exception as exc:  # noqa: BLE001
            self.stats.errors.append(scrub_secret(f"{type(exc).__name__}: {exc}"))
            raise

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, Any]:
        openai_messages: list[ChatCompletionMessageParam] = []
        for m in messages:
            m.content = self._clean_input(m.content)
            if m.role == "user":
                openai_messages.append({"role": "user", "content": m.content})
            elif m.role == "system":
                openai_messages.append({"role": "system", "content": m.content})

        requested = self.model or REQUESTED_MODEL
        t0 = time.perf_counter()
        utc_start = _utc_now_iso()
        try:
            response = await self.client.chat.completions.create(
                model=requested,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                response_format=self._build_response_format(response_model),  # type: ignore[arg-type]
            )
        except openai.RateLimitError as e:
            raise RateLimitError from e
        except Exception as e:
            scrubbed = scrub_secret(str(e))
            logger.error("Error in generating LLM response: %s", scrubbed)
            # Re-raise original but ensure logs are scrubbed
            raise

        utc_end = _utc_now_iso()
        latency_ms = (time.perf_counter() - t0) * 1000.0

        actual_model = getattr(response, "model", None) or "UNKNOWN"
        fingerprint = getattr(response, "system_fingerprint", None)
        usage_fields = extract_usage_fields(getattr(response, "usage", None))

        hit = usage_fields["prompt_cache_hit_tokens"]
        miss = usage_fields["prompt_cache_miss_tokens"]
        cold_or_warm = "UNKNOWN"
        if isinstance(hit, int) and isinstance(miss, int):
            cold_or_warm = "WARM/CACHE_HIT" if hit > 0 else "COLD/CACHE_MISS"

        self.stats.record_request(
            PerRequestUsage(
                request_index=len(self.stats.per_request),
                requested_model=requested,
                actual_model=str(actual_model),
                request_utc_start=utc_start,
                request_utc_end=utc_end,
                latency_ms=round(latency_ms, 2),
                prompt_tokens=usage_fields["prompt_tokens"],
                completion_tokens=usage_fields["completion_tokens"],
                total_tokens=usage_fields["total_tokens"],
                cache_hit_tokens=hit,
                cache_miss_tokens=miss,
                hit_miss=str(usage_fields.get("hit_miss") or "UNKNOWN"),
                system_fingerprint=str(fingerprint) if fingerprint else None,
                prompt_name=self._last_prompt_name,
                cold_or_warm=cold_or_warm,
            )
        )

        result = response.choices[0].message.content or ""
        if not result:
            raise EmptyResponseError("LLM returned an empty response")
        return json.loads(self._strip_code_fences(result))


def build_deepseek_llm_client(
    *,
    temperature: float = 0.0,
    stats: RealLlmCallStats | None = None,
) -> tuple[CountingOpenAIGenericClient, dict[str, Any]]:
    """Build DeepSeek client + redacted fingerprint. No silent model fallback."""
    api_key, key_source = load_deepseek_api_key()
    # Guard: never use OPENAI_API_KEY for this path
    cfg = LLMConfig(
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
        model=REQUESTED_MODEL,
        temperature=temperature,
    )
    client = CountingOpenAIGenericClient(
        config=cfg,
        structured_output_mode=STRUCTURED_OUTPUT_MODE,
        stats=stats if stats is not None else RealLlmCallStats(),
    )
    fingerprint = {
        "provider": "DeepSeek",
        "REQUESTED_MODEL": REQUESTED_MODEL,
        "EXPECTED_VERSION_LABEL": EXPECTED_VERSION_LABEL,
        "ACTUAL_MODEL": "PENDING_LIVE_RESPONSE",
        "model": REQUESTED_MODEL,
        "client": "OpenAIGenericClient",
        "client_wrapper": "CountingOpenAIGenericClient",
        "structured_output_mode": STRUCTURED_OUTPUT_MODE,
        "base_url": DEEPSEEK_BASE_URL,
        "temperature": temperature,
        "embedder": "deterministic",
        "cross_encoder": "deterministic",
        "classification": "REAL_LLM_EXTRACTION+DETERMINISTIC_EMBEDDING",
        "CACHE": "ENABLED_BY_PROVIDER_DEFAULT",
        "custom_kv_cache": False,
        "api_key_source": key_source,
        "api_key": "REDACTED",
        "SECRET_LOGGED": "NO",
        "openai_api_key_set": bool(os.environ.get("OPENAI_API_KEY")),
        "note": (
            "OPENAI_API_KEY must remain unset/unused. "
            "deepseek-v4-pro may route to V4.1 Flash from 2026-09-14 12:00 Beijing — "
            "record UTC timestamps for reproducibility; still request deepseek-v4-pro."
        ),
    }
    if fingerprint["openai_api_key_set"]:
        fingerprint["warning"] = "OPENAI_API_KEY is present in env but must NOT be used"
    return client, fingerprint


def finalize_fingerprint(fingerprint: dict[str, Any], stats: RealLlmCallStats) -> dict[str, Any]:
    """Update fingerprint with live ACTUAL_MODEL + cache/usage aggregates."""
    out = dict(fingerprint)
    models = stats.actual_models_seen
    out["ACTUAL_MODEL"] = models[0] if len(models) == 1 else (models or ["UNKNOWN"])
    if isinstance(out["ACTUAL_MODEL"], list) and len(out["ACTUAL_MODEL"]) == 1:
        out["ACTUAL_MODEL"] = out["ACTUAL_MODEL"][0]
    if not models:
        out["ACTUAL_MODEL"] = "UNKNOWN"
    out["ACTUAL_MODELS_SEEN"] = list(models) or ["UNKNOWN"]
    out["system_fingerprints"] = list(stats.system_fingerprints)
    out["CACHE"] = "ENABLED_BY_PROVIDER_DEFAULT"
    out["CACHE_HIT_TOKENS"] = (
        stats.cache_hit_tokens if stats.cache_fields_observed else "UNKNOWN"
    )
    out["CACHE_MISS_TOKENS"] = (
        stats.cache_miss_tokens if stats.cache_fields_observed else "UNKNOWN"
    )
    out["CACHE_EFFECT"] = stats.cache_effect()
    out["TOKEN_USAGE"] = {
        "prompt_tokens": stats.prompt_tokens if stats.usage_observed else "UNKNOWN",
        "completion_tokens": stats.completion_tokens if stats.usage_observed else "UNKNOWN",
        "total_tokens": stats.total_tokens if stats.usage_observed else "UNKNOWN",
    }
    out["COST"] = stats.to_dict().get("COST")
    out["request_count"] = stats.generate_calls
    out["first_request_utc"] = (
        stats.per_request[0].request_utc_start if stats.per_request else None
    )
    out["last_request_utc"] = (
        stats.per_request[-1].request_utc_end if stats.per_request else None
    )
    out["SECRET_LOGGED"] = "NO"
    out["secrets"] = "REDACTED"
    return out


def is_model_unavailable_error(exc: BaseException) -> bool:
    msg = scrub_secret(str(exc)).lower()
    name = type(exc).__name__.lower()
    needles = (
        "model not found",
        "model-unavailable",
        "model_unavailable",
        "does not exist",
        "invalid model",
        "not available",
        "unknown model",
    )
    if "404" in msg or "notfound" in name.replace("_", ""):
        return True
    return any(n in msg for n in needles)
