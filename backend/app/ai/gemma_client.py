"""Gemma client with the plan's fallback ladder (Section 3).

    try AMD vLLM endpoint (GEMMA_URL, OpenAI-compatible)
     -> on error: Fireworks Gemma API
     -> on error: cached response (data/cache/*.json keyed by request hash)
     -> on cache miss: caller-supplied template (f-string) fallback

The demo must NEVER show a spinner that never resolves; every public function
here returns a value plus the `source` that produced it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Callable, Optional

import httpx

from app.config import get_settings

_JSON_BLOCK = re.compile(r"\{.*\}|\[.*\]", re.DOTALL)


@dataclass
class LLMResult:
    text: str
    source: str  # amd-vllm | fireworks | cache | template


def _cache_key(system: str, user: str, tag: str) -> str:
    h = hashlib.sha256(f"{tag}\n{system}\n{user}".encode()).hexdigest()[:20]
    return f"{tag}_{h}"


def _cache_path(key: str):
    settings = get_settings()
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings.cache_dir / f"{key}.json"


def _read_cache(key: str) -> Optional[str]:
    path = _cache_path(key)
    if path.exists():
        try:
            return json.loads(path.read_text())["text"]
        except (json.JSONDecodeError, KeyError, OSError):
            return None
    return None


def _write_cache(key: str, text: str, source: str) -> None:
    try:
        _cache_path(key).write_text(json.dumps({"text": text, "source": source}))
    except OSError:
        pass


def _chat(base_url: str, api_key: str, model: str, system: str, user: str,
          temperature: float) -> str:
    settings = get_settings()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    url = base_url.rstrip("/") + "/chat/completions"
    resp = httpx.post(url, json=payload, headers=headers, timeout=settings.llm_timeout_s)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def active_backend() -> str:
    """Best-effort report of which backend /health should advertise."""
    settings = get_settings()
    if settings.gemma_url:
        return "amd-vllm"
    if settings.fireworks_api_key:
        return "fireworks"
    if settings.use_cache:
        return "cache"
    return "template"


def complete(
    system: str,
    user: str,
    *,
    tag: str,
    temperature: float = 0.4,
    template_fn: Optional[Callable[[], str]] = None,
) -> LLMResult:
    """Run the fallback ladder. `template_fn` is the always-succeeds last resort."""
    settings = get_settings()
    key = _cache_key(system, user, tag)

    # 1. AMD vLLM (ROCm) OpenAI-compatible endpoint.
    if settings.gemma_url:
        try:
            text = _chat(settings.gemma_url, "", settings.gemma_model, system, user, temperature)
            if settings.use_cache:
                _write_cache(key, text, "amd-vllm")
            return LLMResult(text, "amd-vllm")
        except (httpx.HTTPError, KeyError, IndexError):
            pass

    # 2. Fireworks Gemma API.
    if settings.fireworks_api_key:
        try:
            text = _chat(settings.fireworks_base_url, settings.fireworks_api_key,
                         settings.fireworks_model, system, user, temperature)
            if settings.use_cache:
                _write_cache(key, text, "fireworks")
            return LLMResult(text, "fireworks")
        except (httpx.HTTPError, KeyError, IndexError):
            pass

    # 3. Cached response.
    if settings.use_cache:
        cached = _read_cache(key)
        if cached is not None:
            return LLMResult(cached, "cache")

    # 4. Template fallback (never fails).
    if template_fn is not None:
        return LLMResult(template_fn(), "template")

    return LLMResult("", "template")


def complete_json(system: str, user: str, *, tag: str, temperature: float = 0.2,
                  template_fn: Optional[Callable[[], str]] = None) -> tuple[dict | list | None, str]:
    """Like `complete` but parses a JSON object/array out of the response.

    Retries the JSON extraction once by regex; returns (None, source) if the
    model produced unparseable output and there was no template.
    """
    result = complete(system, user, tag=tag, temperature=temperature, template_fn=template_fn)
    parsed = _extract_json(result.text)
    return parsed, result.source


def _extract_json(text: str) -> dict | list | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK.search(text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None
