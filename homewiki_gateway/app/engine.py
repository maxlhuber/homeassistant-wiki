from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import threading
import time
from zoneinfo import ZoneInfo
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import weekly_update
from wiki_openai import OpenAIResult

from .codex_client import request_automation_wording_codex
from .settings import load_settings
from .supervisor import download_backup, ensure_share_mount, homeassistant_timezone, latest_full_backup, notify, wait_for_backup_jobs


DATA = Path("/data")
PROJECT = Path("/app/project")
STATUS = DATA / "last_status.json"
APP_STATUS = DATA / "app_status.json"
HISTORY = DATA / "history.json"
MANUAL = DATA / "manual"
RELEASES = DATA / "releases"
WORK = DATA / "work"
MANUAL_DIRTY = DATA / "manual-dirty"
BUILT_VERSION = DATA / "built-version"
REBUILD_REQUIRED = DATA / "rebuild-required"
VERSION_CONFIG = Path("/app/homewiki-config.yaml")
ORIGINAL_REQUEST_AUTOMATION_WORDING = weekly_update.request_automation_wording
ORIGINAL_PROBE_API_CREDIT = weekly_update.probe_api_credit


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def runtime_version() -> str:
    """Read the packaged app version without relying on the s6 environment."""
    try:
        for line in VERSION_CONFIG.read_text(encoding="utf-8").splitlines():
            if line.startswith("version:"):
                return line.partition(":")[2].strip().strip('"\'') or "dev"
    except OSError:
        pass
    return os.environ.get("HOMEWIKI_VERSION", "dev")


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _replace_tree(source: Path, destination: Path) -> None:
    incoming = destination.with_name(destination.name + ".new")
    previous = destination.with_name(destination.name + ".old")
    shutil.rmtree(incoming, ignore_errors=True)
    shutil.rmtree(previous, ignore_errors=True)
    shutil.copytree(source, incoming)
    if destination.exists():
        destination.replace(previous)
    try:
        incoming.replace(destination)
    except Exception:
        if previous.exists():
            previous.replace(destination)
        raise
    shutil.rmtree(previous, ignore_errors=True)


class WikiEngine:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.thread: threading.Thread | None = None
        self.login_process = None
        self.login_output: list[str] = []
        self.login_lock = threading.Lock()
        for path in (DATA, MANUAL, RELEASES, WORK, DATA / "codex-home"):
            path.mkdir(parents=True, exist_ok=True)
        if not APP_STATUS.exists():
            self._set_app_status(state="idle", message="Bereit für die erste Aktualisierung.")

    def _set_app_status(self, **values: Any) -> None:
        current = _read_json(APP_STATUS, {})
        current.update({"updated_at": _now(), **values})
        _write_json(APP_STATUS, current)

    def status(self) -> dict[str, Any]:
        app = _read_json(APP_STATUS, {})
        pipeline = _read_json(STATUS, {})
        app["pipeline"] = pipeline
        app["running"] = bool(self.thread and self.thread.is_alive())
        app["releases"] = self.releases()
        app["auth"] = self.auth_status()
        return app

    def health_status(self) -> dict[str, Any]:
        """Return a cheap, secret-free status for Supervisor health checks."""
        app = _read_json(APP_STATUS, {})
        return {
            "status": "ok",
            "state": app.get("state", "unknown"),
            "message": app.get("message", ""),
            "running": bool(self.thread and self.thread.is_alive()),
            "updated_at": app.get("updated_at"),
            "completed_at": app.get("completed_at"),
            "version": runtime_version(),
        }

    def history(self) -> list[dict[str, Any]]:
        value = _read_json(HISTORY, [])
        return value[-100:] if isinstance(value, list) else []

    def _record(self, entry: dict[str, Any]) -> None:
        history = self.history()
        history.append({"at": _now(), **entry})
        _write_json(HISTORY, history[-100:])

    def trigger(self, reason: str = "manual") -> bool:
        with self.lock:
            if self.thread and self.thread.is_alive():
                return False
            self.thread = threading.Thread(target=self._run, args=(reason,), daemon=True)
            self.thread.start()
            return True

    def _backup_current(self) -> Path | None:
        current = DATA / "publish-site"
        if not current.is_dir():
            return None
        destination = WORK / "previous-site"
        shutil.rmtree(destination, ignore_errors=True)
        shutil.copytree(current, destination)
        return destination

    def _retain_previous(self, previous: Path | None, retention: int) -> None:
        if previous is None or not previous.is_dir():
            return
        release = RELEASES / dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        shutil.copytree(previous, release)
        for stale in sorted((path for path in RELEASES.iterdir() if path.is_dir()), reverse=True)[retention:]:
            shutil.rmtree(stale, ignore_errors=True)

    def _export(self, export_path: Path) -> None:
        current = DATA / "publish-site"
        resolved = export_path.resolve()
        share = Path("/share").resolve()
        if resolved != share and share not in resolved.parents:
            raise RuntimeError("Der Exportpfad muss innerhalb von /share liegen.")
        _replace_tree(current, resolved)

    def _configure_llm(self, settings) -> bool:
        weekly_update.request_automation_wording = ORIGINAL_REQUEST_AUTOMATION_WORDING
        weekly_update.probe_api_credit = ORIGINAL_PROBE_API_CREDIT
        if settings.llm_provider == "chatgpt":
            weekly_update.request_automation_wording = lambda candidates, **kwargs: request_automation_wording_codex(
                candidates,
                prompt_path=kwargs["prompt_path"],
                model=settings.model,
                timeout_seconds=settings.llm_timeout_minutes * 60,
            )
            weekly_update.probe_api_credit = lambda **kwargs: OpenAIResult({}, False, None, {}, None)
            return False
        return settings.llm_provider == "disabled"

    def _run(self, reason: str) -> None:
        settings = load_settings()
        self._set_app_status(state="running", message="Backup wird ausgewählt.", started_at=_now(), retry_at=None)
        backup_path = WORK / "selected.backup"
        previous = None
        try:
            ensure_share_mount(settings.export_path)
            wait_for_backup_jobs(settings.llm_timeout_minutes * 60)
            backup = latest_full_backup()
            self._set_app_status(state="running", message="Vollbackup wird sicher eingelesen.", backup=backup.get("name"), backup_date=backup.get("date"))
            download_backup(str(backup["slug"]), backup_path)
            previous = self._backup_current()
            secret_file = WORK / ".backup-password"
            secret_file.write_text(settings.backup_password, encoding="utf-8")
            os.chmod(secret_file, 0o600)
            api_file = WORK / ".openai-key"
            api_file.write_text(settings.openai_api_key, encoding="utf-8")
            os.chmod(api_file, 0o600)
            os.environ["WIKI_MANUAL_DOCS_DIR"] = str(MANUAL)
            no_ai = self._configure_llm(settings)
            args = SimpleNamespace(
                repo=PROJECT,
                backup_root=backup_path,
                state_dir=DATA,
                min_backup_age=0,
                max_backup_age=0,
                model=settings.model or weekly_update.DEFAULT_MODEL,
                endpoint=weekly_update.DEFAULT_ENDPOINT,
                backup_key_file=secret_file,
                openai_key_file=api_file,
                no_ai=no_ai,
                force_rebuild=(
                    reason == "manual_edit"
                    or MANUAL_DIRTY.exists()
                    or REBUILD_REQUIRED.exists()
                    or BUILT_VERSION.read_text(encoding="utf-8").strip() != runtime_version()
                    if BUILT_VERSION.exists()
                    else True
                ),
            )
            self._set_app_status(state="running", message="Wiki wird erzeugt und validiert.")
            code = weekly_update.run(args)
            result = _read_json(STATUS, {})
            outcome = result.get("outcome", "failed")
            if code != 0:
                if result.get("reason_kind") == "quota_exhausted":
                    retry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=settings.quota_retry_minutes)
                    self._set_app_status(state="waiting_quota", message="Codex-Kontingent erschöpft; der Lauf wird automatisch fortgesetzt.", retry_at=retry.isoformat(timespec="seconds"))
                    notify("Haus-Wiki wartet", "Das Codex-Kontingent ist erschöpft. Die bestehende Wiki-Version bleibt aktiv; der Lauf wird automatisch wiederholt.")
                else:
                    self._set_app_status(state="failed", message=str(result.get("message") or "Aktualisierung fehlgeschlagen."))
                    notify("Haus-Wiki: Fehler", str(result.get("message") or "Die Aktualisierung ist fehlgeschlagen."))
                self._record({"reason": reason, "outcome": outcome, "message": result.get("message")})
                return
            if outcome != "ready_unchanged":
                try:
                    self._export(settings.export_path)
                except Exception:
                    REBUILD_REQUIRED.touch()
                    if previous is not None and previous.is_dir():
                        _replace_tree(previous, DATA / "publish-site")
                    raise
                self._retain_previous(previous, settings.release_retention)
                message = "Das Wiki wurde erfolgreich aktualisiert und auf das NAS exportiert."
                notify("Haus-Wiki aktualisiert", message)
            else:
                message = "Das neueste Backup enthält keine wiki-relevanten Änderungen."
                notify("Haus-Wiki unverändert", message)
            if result.get("warning_kind"):
                notify("Haus-Wiki: LLM-Hinweis", str(result.get("warning_message") or "Der deterministische Wiki-Stand wurde ohne LLM-Ergänzung veröffentlicht."), "haus_wiki_llm")
            self._set_app_status(state="idle", message=message, completed_at=_now(), retry_at=None)
            BUILT_VERSION.write_text(runtime_version() + "\n", encoding="utf-8")
            MANUAL_DIRTY.unlink(missing_ok=True)
            REBUILD_REQUIRED.unlink(missing_ok=True)
            self._record({"reason": reason, "outcome": outcome, "backup": backup.get("name"), "warning": result.get("warning_kind")})
        except Exception as error:
            message = str(error)[:1000]
            self._set_app_status(state="failed", message=message)
            self._record({"reason": reason, "outcome": "failed", "message": message})
            notify("Haus-Wiki: Fehler", message)
        finally:
            backup_path.unlink(missing_ok=True)
            (WORK / ".backup-password").unlink(missing_ok=True)
            (WORK / ".openai-key").unlink(missing_ok=True)
            shutil.rmtree(WORK / "previous-site", ignore_errors=True)

    def releases(self) -> list[str]:
        return sorted((path.name for path in RELEASES.iterdir() if path.is_dir()), reverse=True)

    def rollback(self, release: str) -> None:
        if release not in self.releases():
            raise ValueError("Unbekannter Versionsstand.")
        settings = load_settings()
        current = DATA / "publish-site"
        previous = self._backup_current()
        _replace_tree(RELEASES / release, current)
        self._retain_previous(previous, settings.release_retention)
        self._export(settings.export_path)
        self._set_app_status(state="idle", message=f"Rollback auf {release} abgeschlossen.")
        self._record({"reason": "rollback", "outcome": "rolled_back", "release": release})
        notify("Haus-Wiki zurückgesetzt", f"Der Versionsstand {release} ist wieder aktiv.")

    def auth_status(self) -> dict[str, Any]:
        try:
            result = __import__("subprocess").run(["codex", "login", "status"], capture_output=True, text=True, timeout=15, env={**os.environ, "CODEX_HOME": str(DATA / "codex-home")})
            return {"logged_in": result.returncode == 0, "message": (result.stdout or result.stderr).strip()[-300:]}
        except Exception:
            return {"logged_in": False, "message": "Status nicht verfügbar"}

    def start_device_login(self) -> bool:
        import subprocess
        with self.login_lock:
            if self.login_process and self.login_process.poll() is None:
                return False
            self.login_output = []
            self.login_process = subprocess.Popen(
                ["codex", "login", "--device-auth"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, env={**os.environ, "CODEX_HOME": str(DATA / "codex-home")}, bufsize=1,
            )
            threading.Thread(target=self._collect_login, daemon=True).start()
            return True

    def _collect_login(self) -> None:
        process = self.login_process
        if process and process.stdout:
            for line in process.stdout:
                with self.login_lock:
                    self.login_output.append(line.rstrip())

    def device_login_status(self) -> dict[str, Any]:
        with self.login_lock:
            running = bool(self.login_process and self.login_process.poll() is None)
            code = None if running or not self.login_process else self.login_process.returncode
            return {"running": running, "exit_code": code, "output": "\n".join(self.login_output[-30:])}


def scheduler(engine: WikiEngine) -> None:
    weekdays = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    while True:
        try:
            settings = load_settings()
            now = dt.datetime.now(ZoneInfo(homeassistant_timezone()))
            hour, minute = (int(value) for value in settings.schedule_time.split(":"))
            scheduled_today = weekdays and now.weekday() in {weekdays.get(day, -1) for day in settings.schedule_days}
            last = _read_json(APP_STATUS, {}).get("last_schedule_date")
            inside_window = (now.hour, now.minute) >= (hour, minute) if settings.catch_up else (now.hour, now.minute) == (hour, minute)
            if scheduled_today and inside_window and last != now.date().isoformat():
                if engine.trigger("schedule"):
                    engine._set_app_status(last_schedule_date=now.date().isoformat())
            retry_at = _read_json(APP_STATUS, {}).get("retry_at")
            if retry_at and dt.datetime.fromisoformat(retry_at) <= dt.datetime.now(dt.timezone.utc):
                engine.trigger("quota_retry")
            if MANUAL_DIRTY.exists():
                engine.trigger("manual_edit")
        except Exception:
            pass
        time.sleep(30)
