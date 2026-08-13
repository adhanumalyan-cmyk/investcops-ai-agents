"""
LLM provider abstraction.

Initial provider: Gemini (google-genai). Future providers: OpenAI, local.
All provider code lives behind this interface so agents never touch SDKs
directly. When no provider/key is configured, `llm_enabled()` is False and
agents run fully deterministically.
"""

import json
import re
from typing import Any, Optional

from core.config import load_config
from core.errors import LLMError
from core.logging import get_logger

logger = get_logger("investcops.llm")

_SAFE_SYSTEM = (
    "You are a digital investigation assistant. Use ONLY the evidence provided. "
    "Never fabricate evidence, identities, citations or conclusions. "
    "Do not make legal determinations. State uncertainty explicitly. "
    "If evidence is insufficient, say so."
)


def llm_enabled() -> bool:
    return load_config().llm_enabled


def complete(
    prompt: str,
    *,
    system: str = _SAFE_SYSTEM,
    max_context_chars: Optional[int] = None,
) -> str:
    """Single LLM completion. Returns plain text. Raises LLMError on failure."""
    cfg = load_config()
    if not cfg.llm_enabled:
        raise LLMError("LLM not configured; set LLM_PROVIDER and the matching API key.")
    budget = max_context_chars or cfg.LLM_MAX_CONTEXT_CHARS
    prompt = _trim(prompt, budget)
    try:
        if cfg.LLM_PROVIDER == "gemini":
            return _gemini_complete(cfg, system, prompt)
        if cfg.LLM_PROVIDER == "openai":
            return _openai_complete(cfg, system, prompt)
        if cfg.LLM_PROVIDER == "local":
            return _local_complete(cfg, system, prompt)
    except LLMError:
        raise
    except Exception as exc:
        raise LLMError(f"{cfg.LLM_PROVIDER} call failed: {exc}") from exc
    raise LLMError(f"Unsupported LLM_PROVIDER: {cfg.LLM_PROVIDER}")


def _trim(prompt: str, max_chars: int) -> str:
    if len(prompt) <= max_chars:
        return prompt
    return prompt[:max_chars] + "\n...[context truncated]"


def _gemini_complete(cfg: Any, system: str, prompt: str) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise LLMError("Gemini support requires 'pip install google-genai'") from exc
    client = genai.Client(api_key=cfg.GEMINI_API_KEY)
    resp = client.models.generate_content(
        model=cfg.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    text = getattr(resp, "text", None)
    if not text:
        raise LLMError("Gemini returned empty response")
    return text


def _openai_complete(cfg: Any, system: str, prompt: str) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise LLMError("OpenAI support requires httpx") from exc
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {cfg.OPENAI_API_KEY}"},
        json={
            "model": cfg.OPENAI_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        },
        timeout=cfg.LLM_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _local_complete(cfg: Any, system: str, prompt: str) -> str:
    try:
        import httpx
    except ImportError as exc:
        raise LLMError("Local LLM support requires httpx") from exc
    resp = httpx.post(
        f"{cfg.LOCAL_LLM_URL.rstrip('/')}/v1/chat/completions",
        json={
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=cfg.LLM_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def extract_json(text: str) -> Optional[dict]:
    """Best-effort extraction of a JSON object from an LLM reply."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None