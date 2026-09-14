from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


OPTIONS = Path("/data/options.json")


# Keep older installations readable while exposing clear, user-facing values
# in the Home Assistant configuration form.
PROVIDER_ALIASES = {
    "codex": "openai_subscription",
    "openai abo": "openai_subscription",
    "openai_subscription": "openai_subscription",
    "openai subscription": "openai_subscription",
    "chatgpt": "openai_subscription",
    "claude": "claude_subscription",
    "claude abo": "claude_subscription",
    "claude_subscription": "claude_subscription",
    "claude subscription": "claude_subscription",
    "api": "openai_api",
    "openai api": "openai_api",
    "openai_api": "openai_api",
    "claude api": "claude_api",
    "claude_api": "claude_api",
    "disabled": "disabled",
    "ohne ki": "disabled",
}


@dataclass(frozen=True)
class Settings:
    schedule_days: tuple[str, ...]
    schedule_time: str
    catch_up: bool
    backup_password: str
    llm_provider: str
    openai_api_key: str
    anthropic_api_key: str
    model: str
    llm_timeout_minutes: int
    quota_retry_minutes: int
    release_retention: int
    export_path: Path
    admin_users: frozenset[str]
    admin_password: str = ""


def load_settings(path: Path = OPTIONS) -> Settings:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raw = {}
    days = raw.get("schedule_days", ["wed", "sun"])
    if not isinstance(days, list):
        days = ["wed", "sun"]
    admins = raw.get("admin_users", ["Max"])
    if not isinstance(admins, list):
        admins = ["Max"]
    provider = str(raw.get("llm_provider") or "OpenAI Abo").strip().lower()
    provider = PROVIDER_ALIASES.get(provider, "openai_subscription")
    return Settings(
        schedule_days=tuple(str(day).lower() for day in days),
        schedule_time=str(raw.get("schedule_time", "02:00")),
        catch_up=bool(raw.get("catch_up", True)),
        backup_password=str(raw.get("backup_password") or ""),
        llm_provider=provider,
        openai_api_key=str(raw.get("openai_api_key") or ""),
        anthropic_api_key=str(raw.get("anthropic_api_key") or ""),
        model=str(raw.get("model") or ""),
        llm_timeout_minutes=max(5, min(240, int(raw.get("llm_timeout_minutes", 90)))),
        quota_retry_minutes=max(5, min(360, int(raw.get("quota_retry_minutes", 30)))),
        release_retention=max(1, min(20, int(raw.get("release_retention", 3)))),
        export_path=Path(str(raw.get("export_path") or "/share/HausWiki")),
        admin_users=frozenset(str(item) for item in admins if str(item).strip()),
        admin_password=str(raw.get("admin_password") or ""),
    )
