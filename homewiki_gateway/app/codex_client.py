from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from wiki_openai import OpenAIClientError, OpenAIResult, output_schema, validate_ai_document
from wiki_snapshot import redact


QUOTA_PATTERN = re.compile(r"(?:usage limit|rate limit|quota|try again|reset)", re.I)
AUTH_PATTERN = re.compile(r"(?:not logged in|authentication|sign in|login required)", re.I)


def request_automation_wording_codex(
    candidates: list[dict[str, Any]], *, prompt_path: Path, model: str, timeout_seconds: int
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
    prompt = prompt_path.read_text(encoding="utf-8") + "\n\n" + json.dumps(payload, ensure_ascii=False)
    with tempfile.TemporaryDirectory(prefix="haus-wiki-codex-") as temporary:
        root = Path(temporary)
        schema = root / "schema.json"
        result_file = root / "result.json"
        schema.write_text(json.dumps(output_schema(handles), ensure_ascii=False), encoding="utf-8")
        command = [
            "codex", "exec", "-", "--skip-git-repo-check", "--sandbox", "read-only",
            "--output-schema", str(schema), "--output-last-message", str(result_file),
            "-c", 'approval_policy="never"', "-C", str(root),
        ]
        if model:
            command.extend(["--model", model])
        environment = os.environ.copy()
        environment["CODEX_HOME"] = "/data/codex-home"
        try:
            completed = subprocess.run(
                command, input=prompt, text=True, capture_output=True, timeout=timeout_seconds,
                env=environment, encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired as error:
            raise OpenAIClientError("timeout", "Der Codex-Lauf hat das Zeitlimit überschritten.", retryable=True) from error
        diagnostic = (completed.stderr + "\n" + completed.stdout)[-4000:]
        if completed.returncode != 0:
            if AUTH_PATTERN.search(diagnostic):
                raise OpenAIClientError("authentication", "Die ChatGPT-Anmeldung ist abgelaufen oder fehlt.")
            if QUOTA_PATTERN.search(diagnostic):
                raise OpenAIClientError("quota_exhausted", "Das Codex-Nutzungslimit ist derzeit ausgeschöpft.", retryable=True)
            raise OpenAIClientError("service_unavailable", "Der Codex-Lauf ist fehlgeschlagen.", retryable=True)
        try:
            document = json.loads(result_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise OpenAIClientError("invalid_response", "Codex lieferte keine gültige strukturierte Antwort.") from error
    checked = validate_ai_document(document, handles)
    return OpenAIResult(
        overrides={aliases[handle]: value for handle, value in checked.overrides.items()},
        review_required=checked.review_required,
        review_reason=checked.review_reason,
        usage=checked.usage,
        response_id=checked.response_id,
    )
