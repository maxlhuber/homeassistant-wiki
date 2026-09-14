from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from wiki_openai import OpenAIClientError, OpenAIResult, validate_ai_document
from wiki_snapshot import redact


QUOTA_PATTERN = re.compile(r"(?:usage limit|rate limit|quota|429|overloaded|spend limit|try again|reset)", re.I)
AUTH_PATTERN = re.compile(r"(?:not logged in|authentication required|sign in|login required|unauthori[sz]ed)", re.I)


def _text_from_json(value: Any) -> str:
    """Extract Claude's response across CLI JSON format revisions."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("result", "text", "message"):
            if isinstance(value.get(key), str):
                return value[key]
        content = value.get("content")
        if isinstance(content, list):
            parts = [item.get("text", "") for item in content if isinstance(item, dict)]
            return "".join(part for part in parts if isinstance(part, str))
    return ""


def _parse_document(stdout: str) -> Any:
    try:
        payload = json.loads(stdout)
    except ValueError:
        payload = None
    text = _text_from_json(payload) if payload is not None else stdout
    if isinstance(text, str):
        try:
            return json.loads(text.strip())
        except ValueError:
            # Claude occasionally wraps JSON in a markdown fence. The prompt
            # asks for plain JSON, but accepting a fence makes upgrades safer.
            match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S | re.I)
            if match:
                try:
                    return json.loads(match.group(1))
                except ValueError:
                    pass
    return None


def request_automation_wording_claude(
    candidates: list[dict[str, Any]], *, prompt_path: Path, model: str,
    timeout_seconds: int, api_key: str = ""
) -> OpenAIResult:
    handles = [f"automation_{index}" for index in range(1, len(candidates) + 1)]
    aliases = {handle: str(item["alias"]) for handle, item in zip(handles, candidates)}
    payload = [
        {
            "handle": handle,
            "change": item.get("change"),
            "definition": redact({key: value for key, value in item.get("definition", {}).items() if key != "alias"}),
        }
        for handle, item in zip(handles, candidates)
    ]
    prompt = (
        prompt_path.read_text(encoding="utf-8")
        + "\n\nAntworte ausschließlich mit einem JSON-Objekt, ohne Markdown-Codeblock.\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    command = ["claude", "-p", "--output-format", "json", "--max-turns", "1", "--permission-mode", "plan"]
    if model:
        command.extend(["--model", model])
    environment = os.environ.copy()
    environment["CLAUDE_CONFIG_DIR"] = "/data/claude-home"
    if api_key:
        environment["ANTHROPIC_API_KEY"] = api_key
    try:
        completed = subprocess.run(
            command, input=prompt, text=True, capture_output=True,
            timeout=timeout_seconds, env=environment, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError as error:
        raise OpenAIClientError("service_unavailable", "Die Claude-Code-CLI ist im Add-on nicht verfügbar.") from error
    except subprocess.TimeoutExpired as error:
        raise OpenAIClientError("timeout", "Der Claude-Lauf hat das Zeitlimit überschritten.", retryable=True) from error
    diagnostic = (completed.stderr + "\n" + completed.stdout)[-6000:]
    if completed.returncode != 0:
        if AUTH_PATTERN.search(diagnostic):
            raise OpenAIClientError("authentication", "Die Claude-Anmeldung ist abgelaufen oder fehlt.")
        if QUOTA_PATTERN.search(diagnostic):
            # Subscription limits and API rate limits are both retried by the
            # existing scheduler; no partial wiki is published meanwhile.
            kind = "quota_exhausted" if re.search(r"usage limit|spend limit|quota|weekly|monthly", diagnostic, re.I) else "rate_limited"
            raise OpenAIClientError(kind, "Das Claude-Nutzungslimit ist derzeit ausgeschöpft.", retryable=True)
        raise OpenAIClientError("service_unavailable", "Der Claude-Lauf ist fehlgeschlagen.", retryable=True)
    document = _parse_document(completed.stdout)
    if document is None:
        raise OpenAIClientError("invalid_response", "Claude lieferte keine gültige strukturierte Antwort.")
    checked = validate_ai_document(document, handles)
    return OpenAIResult(
        overrides={aliases[handle]: value for handle, value in checked.overrides.items()},
        review_required=checked.review_required,
        review_reason=checked.review_reason,
        usage=checked.usage,
        response_id=checked.response_id,
    )

