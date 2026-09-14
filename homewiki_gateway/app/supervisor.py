from __future__ import annotations

import json
import os
import time
import datetime as dt
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


BASE = "http://supervisor"


class SupervisorError(RuntimeError):
    pass


def _request(path: str, *, method: str = "GET", body: dict[str, Any] | None = None, timeout: int = 60):
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        raise SupervisorError(f"Supervisor-Anfrage wurde abgelehnt (HTTP {error.code}).") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise SupervisorError("Home Assistant Supervisor ist nicht erreichbar.") from error


def json_request(path: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    with _request(path, method=method, body=body) as response:
        document = json.loads(response.read().decode("utf-8"))
    if document.get("result") != "ok":
        raise SupervisorError(str(document.get("message") or "Supervisor-Anfrage fehlgeschlagen."))
    return document.get("data")


def core_json_request(path: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    """Call Home Assistant Core through the Supervisor proxy.

    Unlike Supervisor endpoints, Core endpoints return their payload directly
    and do not wrap it in a ``result/data`` envelope.
    """
    with _request("/core/api" + path, method=method, body=body) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")) if raw else None


def wait_for_backup_jobs(timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    while True:
        data = json_request("/jobs/info") or {}
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        running = any(
            isinstance(job, dict)
            and not bool(job.get("done"))
            and "backup" in str(job.get("name") or "").casefold()
            for job in jobs
        )
        if not running:
            return
        if time.monotonic() >= deadline:
            raise SupervisorError("Ein Home-Assistant-Backup läuft länger als das konfigurierte Zeitlimit.")
        time.sleep(30)


def latest_full_backup() -> dict[str, Any]:
    data = json_request("/backups") or {}
    backups = data.get("backups", []) if isinstance(data, dict) else []
    # Supervisor versions differ slightly: some expose ``type=full`` while
    # older ones only expose that Home Assistant is included.  Never fall
    # back to an arbitrary old archive when the explicit type is absent.
    full = [
        item for item in backups
        if isinstance(item, dict)
        and (item.get("type") == "full" or ("type" not in item and item.get("homeassistant_included") is True))
    ]
    if not full:
        raise SupervisorError("Es wurde kein vollständiges Home-Assistant-Backup gefunden.")
    def sort_key(item: dict[str, Any]) -> tuple[float, str]:
        raw = str(item.get("date") or "")
        try:
            timestamp = dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError, OverflowError):
            timestamp = float("-inf")
        return timestamp, raw

    return max(full, key=sort_key)


def ensure_share_mount(export_path: Path) -> None:
    try:
        relative = export_path.resolve().relative_to(Path("/share").resolve())
        mount_name = relative.parts[0]
    except (ValueError, IndexError):
        raise SupervisorError("Der Exportpfad muss auf eine Netzwerkfreigabe unter /share/<Name> zeigen.")
    mountpoint = Path("/share") / mount_name
    if not mountpoint.is_dir() or not mountpoint.is_mount():
        raise SupervisorError(f"Die Home-Assistant-Netzwerkfreigabe {mount_name} ist nicht aktiv.")


def download_backup(slug: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".new")
    try:
        with _request(f"/backups/{slug}/download", timeout=900) as response, temporary.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        if temporary.stat().st_size <= 0:
            raise SupervisorError("Das ausgewählte Backup ist leer.")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def notify(title: str, message: str, notification_id: str = "haus_wiki") -> None:
    try:
        core_json_request(
            "/services/persistent_notification/create",
            method="POST",
            body={"title": title[:100], "message": message[:1000], "notification_id": notification_id},
        )
    except SupervisorError:
        pass


def homeassistant_timezone() -> str:
    try:
        data = core_json_request("/config") or {}
        return str(data.get("time_zone") or "UTC")
    except SupervisorError:
        return "UTC"
