"""Minimal OpenAI Responses API client for changed wiki automation wording."""

from __future__ import annotations

import json
import re
import socket
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wiki_snapshot import SECRET_VALUE_PATTERNS, redact


DEFAULT_MODEL = "gpt-5.4-nano-2026-03-17"
DEFAULT_ENDPOINT = "https://api.openai.com/v1/responses"
ALLOWED_OVERRIDE_FIELDS = {
    "description",
    "trigger_steps",
    "condition_steps",
    "action_steps",
    "manual",
    "safety_note",
}
UNSAFE_MARKUP_PATTERNS = (
    re.compile(r"[<>]"),
    re.compile(r"(?:!\s*\[|\]\s*\(|\]\s*\[)"),
    re.compile(r"(?:\{\{|\}\}|\{%|%\}|\{#|#\})"),
)
UNSAFE_URL_PATTERN = re.compile(
    r"(?:"
    r"\b(?:https?|ftp|file)\s*://"
    r"|\b(?:javascript|data|mailto|tel)\s*:"
    r"|\bwww\."
    r"|(?<![\w.])//[A-Za-z0-9]"
    r"|\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/|\b)"
    r"|\b(?:[a-z0-9-]+\.)+(?:app|at|ch|cloud|com|de|dev|eu|info|io|local|me|net|org|uk|xyz)"
    r"(?::\d+)?(?:/|\b)"
    r")",
    re.IGNORECASE,
)


class OpenAIClientError(RuntimeError):
    """A classified error suitable for status reporting and notifications."""

    def __init__(
        self,
        kind: str,
        message: str,
        *,
        retryable: bool = False,
        status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.retryable = retryable
        self.status = status


@dataclass(frozen=True)
class OpenAIResult:
    overrides: dict[str, dict[str, Any]]
    review_required: bool
    review_reason: str | None
    usage: dict[str, int]
    response_id: str | None


def output_schema(aliases: list[str]) -> dict[str, Any]:
    count = len(aliases)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["automations", "review_required", "review_reason"],
        "properties": {
            "automations": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "alias",
                        "description",
                        "trigger_steps",
                        "condition_steps",
                        "action_steps",
                        "manual",
                        "safety_note",
                        "confidence",
                        "review_required",
                    ],
                    "properties": {
                        "alias": {"type": "string", "enum": aliases},
                        "description": {"type": "string", "minLength": 1, "maxLength": 800},
                        "trigger_steps": {
                            "type": "array",
                            "items": {"type": "string", "minLength": 1, "maxLength": 500},
                            "maxItems": 12,
                        },
                        "condition_steps": {
                            "type": "array",
                            "items": {"type": "string", "minLength": 1, "maxLength": 500},
                            "maxItems": 12,
                        },
                        "action_steps": {
                            "type": "array",
                            "items": {"type": "string", "minLength": 1, "maxLength": 500},
                            "maxItems": 16,
                        },
                        "manual": {"type": "string", "minLength": 1, "maxLength": 800},
                        "safety_note": {"type": ["string", "null"], "maxLength": 800},
                        "confidence": {"type": "string", "enum": ["high", "review"]},
                        "review_required": {"type": "boolean"},
                    },
                },
            },
            "review_required": {"type": "boolean"},
            "review_reason": {"type": ["string", "null"], "maxLength": 1000},
        },
    }


def classify_http_error(status: int, payload: dict[str, Any] | None) -> OpenAIClientError:
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    if not isinstance(error, dict):
        error = {}
    code = str(error.get("code") or error.get("type") or "").casefold()
    message = str(error.get("message") or "OpenAI-Anfrage fehlgeschlagen.")
    combined = f"{code} {message}".casefold()
    if status in {400, 402, 403, 429} and any(
        marker in combined
        for marker in (
            "insufficient_quota",
            "quota",
            "billing_hard_limit",
            "credit balance",
            "credits",
        )
    ):
        return OpenAIClientError(
            "quota_exhausted",
            "Das OpenAI-API-Guthaben ist aufgebraucht oder das Abrechnungslimit wurde erreicht.",
            status=status,
        )
    if status in {401, 403}:
        return OpenAIClientError("authentication", "Der OpenAI-API-Key wurde abgelehnt.", status=status)
    if status == 429:
        return OpenAIClientError(
            "rate_limited",
            "OpenAI hat vorübergehend zu viele Anfragen erhalten.",
            retryable=True,
            status=status,
        )
    if status >= 500:
        return OpenAIClientError(
            "service_unavailable",
            "Der OpenAI-Dienst ist vorübergehend nicht erreichbar.",
            retryable=True,
            status=status,
        )
    return OpenAIClientError("request_rejected", message[:500], status=status)


def _response_text(response: dict[str, Any]) -> str:
    direct = response.get("output_text")
    if isinstance(direct, str) and direct:
        return direct
    pieces: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "refusal":
                raise OpenAIClientError(
                    "model_refusal",
                    "Das Modell hat die Formulierung abgelehnt; die bisherige Wiki-Version bleibt aktiv.",
                )
            text = content.get("text")
            if isinstance(text, str):
                pieces.append(text)
    if not pieces:
        raise OpenAIClientError("invalid_response", "OpenAI hat keinen auswertbaren Text geliefert.")
    return "".join(pieces)


def _contains_secret(value: Any) -> bool:
    serialised = json.dumps(value, ensure_ascii=False)
    return any(pattern.search(serialised) for pattern in SECRET_VALUE_PATTERNS)


def _without_alias_keys(value: Any) -> Any:
    """Keep real Home Assistant aliases out of the external model request."""
    if isinstance(value, dict):
        return {
            str(key): _without_alias_keys(item)
            for key, item in value.items()
            if str(key) != "alias"
        }
    if isinstance(value, list):
        return [_without_alias_keys(item) for item in value]
    return value


def _has_control_characters(value: str) -> bool:
    return any(
        unicodedata.category(character) in {"Cc", "Cf", "Zl", "Zp"}
        for character in value
    )


def _validate_plain_model_text(value: str, field: str) -> str:
    """Return a trimmed plain-text model field or reject active content."""
    if _has_control_characters(value):
        raise OpenAIClientError(
            "invalid_response",
            f"Die KI-Antwort enthält unzulässige Steuerzeichen: {field}",
        )
    text = value.strip()
    if not text:
        raise OpenAIClientError("invalid_response", f"Ungültiges Feld: {field}")
    normalised = unicodedata.normalize("NFKC", text)
    if (
        _has_control_characters(normalised)
        or UNSAFE_URL_PATTERN.search(normalised)
        or any(pattern.search(normalised) for pattern in UNSAFE_MARKUP_PATTERNS)
    ):
        raise OpenAIClientError(
            "invalid_response",
            f"Die KI-Antwort enthält unzulässiges Markup oder eine URL: {field}",
        )
    return text


def validate_ai_document(document: Any, expected_aliases: list[str]) -> OpenAIResult:
    if not isinstance(document, dict):
        raise OpenAIClientError("invalid_response", "Die KI-Antwort ist kein JSON-Objekt.")
    entries = document.get("automations")
    if not isinstance(entries, list):
        raise OpenAIClientError("invalid_response", "In der KI-Antwort fehlen Automationen.")
    expected = set(expected_aliases)
    seen: set[str] = set()
    overrides: dict[str, dict[str, Any]] = {}
    entry_review = False
    for entry in entries:
        if not isinstance(entry, dict):
            raise OpenAIClientError("invalid_response", "Ein KI-Eintrag ist ungültig.")
        alias = entry.get("alias")
        if not isinstance(alias, str) or alias not in expected or alias in seen:
            raise OpenAIClientError(
                "invalid_response", "Die KI-Antwort enthält eine unbekannte oder doppelte Automation."
            )
        seen.add(alias)
        confidence = entry.get("confidence")
        entry_review = entry_review or confidence != "high" or entry.get("review_required") is not False
        override: dict[str, Any] = {}
        for field in ALLOWED_OVERRIDE_FIELDS:
            value = entry.get(field)
            if field in {"trigger_steps", "condition_steps", "action_steps"}:
                if not isinstance(value, list) or not all(
                    isinstance(item, str) and item.strip() for item in value
                ):
                    raise OpenAIClientError("invalid_response", f"Ungültiges Feld: {field}")
                override[field] = [
                    _validate_plain_model_text(item, field) for item in value
                ]
            elif field == "safety_note" and value is None:
                continue
            elif not isinstance(value, str) or not value.strip():
                raise OpenAIClientError("invalid_response", f"Ungültiges Feld: {field}")
            else:
                override[field] = _validate_plain_model_text(value, field)
        if _contains_secret(override):
            raise OpenAIClientError(
                "secret_detected", "Die KI-Antwort enthält ein geheimnisähnliches Muster."
            )
        overrides[alias] = override
    if seen != expected:
        missing = ", ".join(sorted(expected - seen))
        raise OpenAIClientError("invalid_response", f"KI-Antwort unvollständig: {missing}")
    global_review = document.get("review_required") is not False
    reason = document.get("review_reason")
    if reason is not None and not isinstance(reason, str):
        raise OpenAIClientError("invalid_response", "Ungültiger Prüfhinweis der KI.")
    review_reason: str | None = None
    if isinstance(reason, str):
        if _has_control_characters(reason):
            raise OpenAIClientError(
                "invalid_response", "Der KI-Prüfhinweis enthält unzulässige Steuerzeichen."
            )
        if reason.strip():
            review_reason = _validate_plain_model_text(reason, "review_reason")
    return OpenAIResult(
        overrides=overrides,
        review_required=global_review or entry_review,
        review_reason=review_reason,
        usage={},
        response_id=None,
    )


def request_automation_wording(
    candidates: list[dict[str, Any]],
    *,
    api_key: str | None,
    prompt_path: Path,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: int = 90,
) -> OpenAIResult:
    if not candidates:
        return OpenAIResult({}, False, None, {}, None)
    if not api_key:
        raise OpenAIClientError(
            "missing_key", "Für geänderte Automationen ist kein OpenAI-API-Key hinterlegt."
        )
    try:
        prompt = prompt_path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise OpenAIClientError("prompt_missing", "Die feste Wiki-Anweisung fehlt.") from error
    original_aliases = [str(item["alias"]) for item in candidates]
    if len(set(original_aliases)) != len(original_aliases):
        raise OpenAIClientError(
            "ambiguous_alias", "Geänderte Automationen haben doppelte Namen und brauchen eine Prüfung."
        )
    model_aliases = [f"automation_{index}" for index in range(1, len(candidates) + 1)]
    model_candidates = [
        {
            "change": item.get("change"),
            "alias": model_alias,
            "definition": _without_alias_keys(item.get("definition")),
        }
        for model_alias, item in zip(model_aliases, candidates, strict=True)
    ]
    user_payload = {
        "task": "Formuliere nur die folgenden geänderten Automationen.",
        "automations": redact(model_candidates),
    }
    body = {
        "model": model,
        "store": False,
        "reasoning": {"effort": "none"},
        "max_output_tokens": min(6000, 800 + 850 * len(candidates)),
        "input": [
            {"role": "developer", "content": prompt},
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "homeassistant_wiki_delta",
                "strict": True,
                "schema": output_schema(model_aliases),
            }
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "homeassistant-wiki-weekly/1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        raise classify_http_error(error.code, payload) from error
    except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
        raise OpenAIClientError(
            "network", "Die OpenAI-API ist vom Raspberry Pi aus nicht erreichbar.", retryable=True
        ) from error
    try:
        response_document = json.loads(raw.decode("utf-8"))
        output_document = json.loads(_response_text(response_document))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OpenAIClientError("invalid_response", "OpenAI hat ungültiges JSON geliefert.") from error
    result = validate_ai_document(output_document, model_aliases)
    mapped_overrides = {
        original_alias: result.overrides[model_alias]
        for original_alias, model_alias in zip(
            original_aliases, model_aliases, strict=True
        )
    }
    usage_raw = response_document.get("usage", {})
    usage = {
        key: int(value)
        for key, value in usage_raw.items()
        if key in {"input_tokens", "output_tokens", "total_tokens"}
        and isinstance(value, int)
    }
    return OpenAIResult(
        overrides=mapped_overrides,
        review_required=result.review_required,
        review_reason=result.review_reason,
        usage=usage,
        response_id=(
            str(response_document["id"]) if isinstance(response_document.get("id"), str) else None
        ),
    )


def probe_api_credit(
    *,
    api_key: str | None,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: int = 30,
) -> OpenAIResult:
    """Make the smallest practical weekly Responses call to expose quota errors."""
    if not api_key:
        raise OpenAIClientError(
            "missing_key", "Für die wöchentliche Guthabenprüfung fehlt der OpenAI-API-Key."
        )
    body = {
        "model": model,
        "store": False,
        "reasoning": {"effort": "none"},
        "max_output_tokens": 32,
        "input": "Antworte exakt mit OK.",
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "homeassistant-wiki-weekly/1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        raise classify_http_error(error.code, payload) from error
    except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
        raise OpenAIClientError(
            "network", "Die OpenAI-API ist vom Raspberry Pi aus nicht erreichbar.", retryable=True
        ) from error
    try:
        response_document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OpenAIClientError("invalid_response", "OpenAI hat ungültiges JSON geliefert.") from error
    usage_raw = response_document.get("usage", {})
    usage = {
        key: int(value)
        for key, value in usage_raw.items()
        if key in {"input_tokens", "output_tokens", "total_tokens"}
        and isinstance(value, int)
    }
    return OpenAIResult(
        overrides={},
        review_required=False,
        review_reason=None,
        usage=usage,
        response_id=(
            str(response_document["id"]) if isinstance(response_document.get("id"), str) else None
        ),
    )
