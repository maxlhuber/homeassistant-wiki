from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import threading
import time
import uuid
import subprocess
from zoneinfo import ZoneInfo
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import weekly_update
from wiki_openai import OpenAIResult

from .codex_client import request_automation_wording_codex
from .settings import load_settings
from .operation_log import OperationLog
from .supervisor import download_backup, ensure_share_mount, homeassistant_timezone, latest_automatic_backup_file, latest_full_backup, notify, wait_for_backup_jobs


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
        self.login_generation = 0
        self.login_cancel = threading.Event()
        self.login_state: dict[str, Any] = {"state": "idle", "code": None, "url": None, "expires_at": None, "retry_at": None, "attempts": 0}
        self.auth_cache: tuple[float, dict[str, Any]] = (0, {})
        for path in (DATA, MANUAL, RELEASES, WORK, DATA / "codex-home"):
            path.mkdir(parents=True, exist_ok=True)
        self.operation_log = OperationLog(DATA / "logs")
        if not APP_STATUS.exists():
            self._set_app_status(state="idle", message="Bereit für die erste Aktualisierung.")

    def logs(self, limit: int = 200) -> dict[str, Any]:
        return self.operation_log.read(limit)

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
            "backup": app.get("backup"),
            "backup_date": app.get("backup_date"),
            "version": runtime_version(),
            "warning_kind": "llm_incomplete" if app.get("warning_kind") else None,
            "warning_message": "LLM-Ergänzungen sind noch nicht vollständig." if app.get("warning_kind") else None,
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
        ensure_share_mount(export_path)
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
        started = time.monotonic()
        run_id = uuid.uuid4().hex[:12]
        self.operation_log.emit("run_started", "Wiki-Aktualisierung gestartet.", run_id=run_id, reason=reason, version=runtime_version())
        self._set_app_status(state="running", phase="backup_wait", run_id=run_id, message="Backup wird ausgewählt.", started_at=_now(), retry_at=None)
        backup_path = WORK / "selected.backup"
        previous = None
        try:
            settings = load_settings()
            self.operation_log.emit("phase", "Netzwerkspeicher und laufende Backups werden geprüft.", run_id=run_id, phase="backup_wait")
            ensure_share_mount(settings.export_path)
            wait_for_backup_jobs(settings.llm_timeout_minutes * 60)
            local_backup = latest_automatic_backup_file(settings.export_path)
            if local_backup is not None:
                backup = {"name": local_backup.name, "date": local_backup.name, "source": "network_share"}
                self._set_app_status(state="running", message="Neuestes automatisches NAS-Vollbackup wird sicher eingelesen.", backup=backup["name"], backup_date=backup["date"])
                shutil.copyfile(local_backup, backup_path)
            else:
                backup = latest_full_backup()
                self._set_app_status(state="running", message="Vollbackup wird sicher eingelesen.", backup=backup.get("name"), backup_date=backup.get("date"))
                backup_id = backup.get("slug") or backup.get("backup_id") or backup.get("id")
                if not backup_id:
                    raise RuntimeError("Das ausgewählte Backup besitzt keine gültige Supervisor-ID.")
                download_backup(str(backup_id), backup_path)
            self.operation_log.emit("phase", "Backup ausgewählt; Wiki wird erzeugt und geprüft.", run_id=run_id, phase="build", source=backup.get("source", "supervisor"))
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
            self._set_app_status(state="running", phase="build", message="Wiki wird erzeugt und validiert.")
            code = weekly_update.run(args)
            result = _read_json(STATUS, {})
            outcome = result.get("outcome", "failed")
            if code != 0:
                if result.get("reason_kind") == "quota_exhausted":
                    retry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=settings.quota_retry_minutes)
                    self._set_app_status(state="waiting_quota", phase="waiting_quota", message="Codex-Kontingent erschöpft; der Lauf wird automatisch fortgesetzt.", retry_at=retry.isoformat(timespec="seconds"))
                    notify("Haus-Wiki wartet", "Das Codex-Kontingent ist erschöpft. Die bestehende Wiki-Version bleibt aktiv; der Lauf wird automatisch wiederholt.")
                else:
                    self._set_app_status(state="failed", phase="failed", message="Die Aktualisierung ist fehlgeschlagen. Bitte Backup, Verbindung und Anmeldung prüfen.")
                    notify("Haus-Wiki: Fehler", "Die Aktualisierung ist fehlgeschlagen. Bitte Backup, Verbindung und Anmeldung prüfen.")
                self._record({"reason": reason, "outcome": outcome, "message": "Aktualisierung konnte nicht abgeschlossen werden."})
                self.operation_log.emit("run_blocked", "Aktualisierung konnte nicht abgeschlossen werden.", level="warning", run_id=run_id, outcome=outcome, duration_seconds=round(time.monotonic() - started, 2))
                return
            if outcome != "ready_unchanged":
                try:
                    self.operation_log.emit("phase", "Geprüftes Wiki wird auf das NAS exportiert.", run_id=run_id, phase="export")
                    self._set_app_status(phase="export", message="Das geprüfte Wiki wird auf das NAS exportiert.")
                    self._export(settings.export_path)
                except Exception:
                    REBUILD_REQUIRED.touch()
                    if previous is not None and previous.is_dir():
                        _replace_tree(previous, DATA / "publish-site")
                    raise
                self._retain_previous(previous, settings.release_retention)
                message = "Das Wiki wurde erfolgreich aktualisiert und auf das NAS exportiert."
                notification_title = "Haus-Wiki aktualisiert"
            else:
                message = "Das neueste Backup enthält keine wiki-relevanten Änderungen."
                notification_title = "Haus-Wiki unverändert"
            prior = _read_json(APP_STATUS, {})
            warning_kind = result.get("warning_kind")
            warning_message = result.get("warning_message")
            # A metadata-only rebuild cannot prove that missing LLM wording was
            # recovered. Keep the visible warning until an actual LLM run succeeds.
            if not warning_kind and not result.get("openai_called"):
                warning_kind = prior.get("warning_kind")
                warning_message = prior.get("warning_message")
            if warning_kind:
                warning_message = "Das Wiki ist verfügbar. LLM-Ergänzungen fehlen noch; Details stehen im Laufstatus."
                message += " LLM-Ergänzungen sind noch nicht vollständig."
            if result.get("warning_kind"):
                notify("Haus-Wiki: LLM-Hinweis", "Der automatisch erzeugte Wiki-Stand wurde ohne vollständige LLM-Ergänzung veröffentlicht. Bitte Anmeldung und Kontingent prüfen.", "haus_wiki_llm")
            notify(notification_title, message)
            self._set_app_status(state="idle", phase="complete", message=message, completed_at=_now(), retry_at=None, warning_kind=warning_kind, warning_message=warning_message, backup_date=result.get("backup_date") or backup.get("date"), duration_seconds=round(time.monotonic() - started, 2))
            self.operation_log.emit("run_completed", "Wiki-Lauf abgeschlossen; LLM-Ergänzungen fehlen noch." if warning_kind else "Wiki-Lauf erfolgreich abgeschlossen.", level="warning" if warning_kind else "info", run_id=run_id, outcome=outcome, backup_date=result.get("backup_date"), duration_seconds=round(time.monotonic() - started, 2))
            BUILT_VERSION.write_text(runtime_version() + "\n", encoding="utf-8")
            MANUAL_DIRTY.unlink(missing_ok=True)
            REBUILD_REQUIRED.unlink(missing_ok=True)
            self._record({"reason": reason, "outcome": outcome, "backup": backup.get("name"), "warning": result.get("warning_kind")})
        except Exception as error:
            self.operation_log.emit("run_failed", "Wiki-Aktualisierung fehlgeschlagen. Bestehenden Stand prüfen.", level="error", run_id=run_id, error_type=type(error).__name__, duration_seconds=round(time.monotonic() - started, 2))
            message = "Die Aktualisierung ist fehlgeschlagen. Bitte Backup, NAS-Verbindung und Anmeldung prüfen."
            self._set_app_status(state="failed", phase="failed", message=message)
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
        with self.lock:
            if self.thread and self.thread.is_alive():
                raise ValueError("Während einer Aktualisierung ist keine Wiederherstellung möglich.")
            self._rollback(release)

    def _rollback(self, release: str) -> None:
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
        self.operation_log.emit("rollback_completed", "Gesicherter Wiki-Stand wiederhergestellt.", outcome="rolled_back")
        notify("Haus-Wiki zurückgesetzt", f"Der Versionsstand {release} ist wieder aktiv.")

    def auth_status(self) -> dict[str, Any]:
        if time.monotonic() - self.auth_cache[0] < 15:
            return dict(self.auth_cache[1])
        try:
            result = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, timeout=15, env={**os.environ, "CODEX_HOME": str(DATA / "codex-home")})
            status = {"logged_in": result.returncode == 0, "message": "Angemeldet" if result.returncode == 0 else "Nicht angemeldet"}
        except Exception:
            status = {"logged_in": False, "message": "Status nicht verfügbar"}
        self.auth_cache = (time.monotonic(), status)
        return dict(status)

    def start_device_login(self) -> bool:
        with self.login_lock:
            if self.login_state["state"] in {"starting", "pending", "retrying"}:
                return False
            self.login_generation += 1
            generation = self.login_generation
            self.login_cancel = threading.Event()
            self.login_output = []
            self.login_state = {"state": "starting", "code": None, "url": None, "expires_at": None, "retry_at": None, "attempts": 0}
            threading.Thread(target=self._login_flow, args=(generation, self.login_cancel), daemon=True).start()
        self.operation_log.emit("login_started", "ChatGPT-Anmeldung gestartet.")
        return True

    def stop_device_login(self) -> None:
        with self.login_lock:
            self.login_generation += 1
            self.login_cancel.set()
            process = self.login_process
            self.login_process = None
            self.login_output = []
            self.login_state.update(state="cancelled", code=None, url=None, expires_at=None, retry_at=None)
            self.auth_cache = (0, {})
        if process and process.poll() is None:
            process.terminate()
        self.operation_log.emit("login_cancelled", "ChatGPT-Anmeldung abgebrochen.")

    def _collect_login(self, process, generation: int) -> None:
        if process.stdout:
            for line in process.stdout:
                with self.login_lock:
                    if generation != self.login_generation or process is not self.login_process:
                        return
                    clean = re.sub(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))", "", line).rstrip()
                    clean = "".join(character for character in clean if character >= " " or character == "\t")
                    self.login_output = (self.login_output + [clean[:1000]])[-30:]
                    code = re.search(r"\b[A-Z0-9]{4,5}-[A-Z0-9]{4,5}\b", clean)
                    if "https://auth.openai.com/codex/device" in clean:
                        self.login_state["url"] = "https://auth.openai.com/codex/device"
                    if code and not self.login_state.get("code"):
                        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15)
                        self.login_state.update(state="pending", code=code.group(), url="https://auth.openai.com/codex/device", expires_at=expires.isoformat(timespec="seconds"))

    def _login_flow(self, generation: int, cancel: threading.Event) -> None:
        failures = 0
        while not cancel.is_set():
            with self.login_lock:
                if generation != self.login_generation:
                    return
                self.login_state.update(state="starting", code=None, expires_at=None, retry_at=None, attempts=self.login_state["attempts"] + 1)
                self.login_output = []
                try:
                    process = subprocess.Popen(["codex", "login", "--device-auth"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env={**os.environ, "CODEX_HOME": str(DATA / "codex-home"), "NO_COLOR": "1", "TERM": "dumb"}, bufsize=1)
                    self.login_process = process
                except OSError:
                    self.login_state.update(state="failed")
                    self.operation_log.emit("login_failed", "Anmeldeprozess konnte nicht gestartet werden.", level="error")
                    return
            collector = threading.Thread(target=self._collect_login, args=(process, generation), daemon=True)
            collector.start()
            started = time.monotonic()
            expired = False
            while process.poll() is None and not cancel.wait(0.5):
                with self.login_lock:
                    if generation != self.login_generation:
                        return
                    expiry = self.login_state.get("expires_at")
                expired = bool(expiry and dt.datetime.fromisoformat(expiry) <= dt.datetime.now(dt.timezone.utc))
                if expired or (not expiry and time.monotonic() - started > 90):
                    process.terminate()
                    break
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            collector.join(timeout=2)
            if cancel.is_set():
                return
            self.auth_cache = (0, {})
            authenticated = self.auth_status().get("logged_in", False)
            with self.login_lock:
                if generation != self.login_generation:
                    return
                expiry = self.login_state.get("expires_at")
                expired = expired or bool(expiry and dt.datetime.fromisoformat(expiry) <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=5))
                self.login_state.update(code=None, expires_at=None)
                self.login_output = []
                if authenticated:
                    self.login_state.update(state="authenticated", retry_at=None)
                    self.operation_log.emit("login_completed", "ChatGPT-Anmeldung erfolgreich.")
                    return
                failures = 0 if expired else failures + 1
                if failures >= 3:
                    self.login_state.update(state="failed", retry_at=None)
                    self.operation_log.emit("login_failed", "Anmeldung nach drei Fehlern gestoppt. Erneut starten.", level="error")
                    return
                delay = 1 if expired else min(30, 5 * 2 ** (failures - 1))
                self.login_state.update(state="retrying", retry_at=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=delay)).isoformat(timespec="seconds"))
            self.operation_log.emit("login_renewed" if expired else "login_retry", "Abgelaufener Anmeldecode wird erneuert." if expired else "Anmeldung wird nach einer kurzen Pause wiederholt.", level="info" if expired else "warning")
            if cancel.wait(delay):
                return

    def device_login_status(self) -> dict[str, Any]:
        with self.login_lock:
            running = self.login_state["state"] in {"starting", "pending", "retrying"}
            code = None if running or not self.login_process else self.login_process.returncode
            return {"running": running, "exit_code": code, "output": "\n".join(self.login_output[-30:]), **self.login_state}


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
