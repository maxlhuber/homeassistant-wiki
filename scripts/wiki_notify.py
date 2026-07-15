"""Send fixed, non-sensitive wiki status codes to Home Assistant.

The webhook payload deliberately contains only an allow-listed event kind.  If
Home Assistant is unavailable, the event is retained locally and retried by a
separate systemd timer.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ALLOWED_KINDS = frozenset(
    {
        "update_success",
        "openai_quota",
        "openai_auth",
        "openai_rate_limit",
        "openai_unavailable",
        "backup_invalid",
        "validation_failed",
        "github_failed",
        "review_required",
        "deploy_rolled_back",
    }
)
WARNING_KIND_MAP = {
    "quota_exhausted": "openai_quota",
    "authentication": "openai_auth",
    "missing_key": "openai_auth",
    "rate_limited": "openai_rate_limit",
    "network": "openai_unavailable",
    "service_unavailable": "openai_unavailable",
    "request_rejected": "openai_unavailable",
    "invalid_response": "openai_unavailable",
    "model_refusal": "review_required",
    "secret_detected": "review_required",
    "ambiguous_alias": "review_required",
    "prompt_missing": "validation_failed",
    "ai_disabled": "openai_auth",
}
BACKUP_REASON_PREFIXES = (
    "backup_",
    "core_archive_",
    "required_member_",
    "invalid_member",
    "unsafe_member",
    "mixed_backup_",
    "duplicate_member",
    "truncated_member",
)


class NotificationConfigurationError(RuntimeError):
    """Raised when the local root-owned webhook credential is malformed."""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _read_webhook(path: Path) -> str:
    try:
        if path.stat().st_size > 512:
            raise NotificationConfigurationError("Webhook-Datei ist unplausibel groß.")
        value = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise NotificationConfigurationError("Webhook-Datei ist nicht lesbar.") from error
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname
        not in {"homeassistant.local", "homeassistant", "192.168.1.100"}
        or parsed.port not in {None, 8123}
        or not parsed.path.startswith("/api/webhook/")
        or len(parsed.path.removeprefix("/api/webhook/")) < 32
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise NotificationConfigurationError("Webhook-Adresse ist nicht freigegeben.")
    return value


def _post(webhook: str, kind: str, timeout: int = 10) -> bool:
    if kind not in ALLOWED_KINDS:
        raise ValueError("Unbekannter Benachrichtigungstyp")
    request = urllib.request.Request(
        webhook,
        data=json.dumps({"kind": kind}, separators=(",", ":")).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "homeassistant-wiki/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(1024)
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _load_queue(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(value, list):
        return []
    return [
        {"kind": item["kind"], "created_at": item.get("created_at", "")}
        for item in value
        if isinstance(item, dict) and item.get("kind") in ALLOWED_KINDS
    ][:100]


def _write_queue(path: Path, items: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".wiki-notify-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(items[-100:], output, ensure_ascii=False, indent=2)
            output.write("\n")
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def send_or_queue(webhook: str, queue: Path, kind: str) -> bool:
    if _post(webhook, kind):
        pending = _load_queue(queue)
        remaining = [item for item in pending if item["kind"] != kind]
        if len(remaining) != len(pending):
            _write_queue(queue, remaining)
        return True
    pending = _load_queue(queue)
    if not any(item["kind"] == kind for item in pending):
        pending.append({"kind": kind, "created_at": _now()})
    _write_queue(queue, pending)
    return False


def flush(webhook: str, queue: Path) -> tuple[int, int]:
    pending = _load_queue(queue)
    remaining: list[dict[str, str]] = []
    sent = 0
    for index, item in enumerate(pending):
        if _post(webhook, item["kind"]):
            sent += 1
        else:
            remaining.extend(pending[index:])
            break
    _write_queue(queue, remaining)
    return sent, len(remaining)


def kinds_from_status(path: Path) -> list[str]:
    try:
        document: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ["validation_failed"]
    if not isinstance(document, dict):
        return ["validation_failed"]
    warning = document.get("warning_kind")
    kinds: list[str] = []
    if isinstance(warning, str):
        kinds.append(WARNING_KIND_MAP.get(warning, "openai_unavailable"))
    outcome = document.get("outcome")
    if outcome in {"blocked", "failed"}:
        reason = str(document.get("reason_kind") or "")
        if reason in {"review_required", "model_review_required"}:
            kinds.append("review_required")
        elif reason.startswith(BACKUP_REASON_PREFIXES):
            kinds.append("backup_invalid")
        elif reason in WARNING_KIND_MAP:
            kinds.append(WARNING_KIND_MAP[reason])
        else:
            kinds.append("validation_failed")
    return list(dict.fromkeys(kinds))


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--webhook-file", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--kind", choices=sorted(ALLOWED_KINDS))
    mode.add_argument("--status", type=Path)
    mode.add_argument("--flush", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    try:
        webhook = _read_webhook(args.webhook_file)
    except NotificationConfigurationError:
        # There is nowhere safe to send a notification if the local endpoint
        # credential itself is missing.  Avoid printing the credential value.
        raise SystemExit(2)
    if args.flush:
        _, remaining = flush(webhook, args.queue)
        raise SystemExit(0 if remaining == 0 else 1)
    kinds = [args.kind] if args.kind else kinds_from_status(args.status)
    for kind in kinds:
        send_or_queue(webhook, args.queue, kind)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
