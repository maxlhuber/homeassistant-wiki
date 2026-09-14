from __future__ import annotations

import json
import os
import time
import datetime as dt
import tarfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from wiki_backup import BackupExtractionError, discover_latest_backup


BASE = "http://supervisor"
SHARE_ROOT = Path("/share")


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
    # Automatic NAS snapshots are the authoritative source for the wiki.
    # Supervisor also exposes legacy/manual full archives (including old
    # 2024 snapshots); never let those win while an automatic snapshot exists.
    automatic = [item for item in full if item.get("with_automatic_settings") is True]
    if automatic:
        full = automatic
    def sort_key(item: dict[str, Any]) -> tuple[float, str]:
        raw = str(item.get("date") or "")
        try:
            timestamp = dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError, OverflowError):
            timestamp = float("-inf")
        return timestamp, raw

    return max(full, key=sort_key)


def latest_automatic_backup_file(export_path: Path) -> Path | None:
    """Select a validated automatic full backup only from the configured share.

    Dates and completeness come from backup.json, never from a filename. The
    existing archive validator only inspects outer headers, without decrypting
    or extracting the large Home Assistant payload.
    """
    root = _export_mount(export_path)
    candidates: list[tuple[float, Path]] = []
    try:
        # Automatic archives may be stored directly in the share or below a
        # ``Backup``/date directory.  Search recursively, but only accept
        # structurally validated full archives and never arbitrary tar files.
        files = list(root.rglob("automatic_backup_*.tar"))
        for path in files:
            try:
                validated = discover_latest_backup(path, min_age_seconds=0)
                with tarfile.open(validated, mode="r:") as archive:
                    metadata_member = next(member for member in archive if member.name.removeprefix("./") == "backup.json")
                    if metadata_member.size > 1_000_000:
                        continue
                    document = json.loads(archive.extractfile(metadata_member).read())
                if document.get("type") != "full":
                    continue
                stamp = dt.datetime.fromisoformat(document["date"].replace("Z", "+00:00")).timestamp()
                candidates.append((stamp, validated))
            except (BackupExtractionError, OSError, tarfile.TarError, ValueError, KeyError, StopIteration):
                continue
    except OSError as error:
        raise SupervisorError("Der konfigurierte NAS-Backupordner konnte nicht gelesen werden.") from error
    if files and not candidates:
        raise SupervisorError("Die automatischen NAS-Backups sind noch nicht vollständig oder ungültig. Es wird kein alter Ersatzstand verwendet.")
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def _export_mount(export_path: Path) -> Path:
    try:
        relative = export_path.resolve().relative_to(SHARE_ROOT.resolve())
        # A share itself (``/share/HausWiki``) is supported for backwards
        # compatibility with existing installations.  For a shared backup
        # location prefer a child such as ``/share/NASWiki/HausWiki``; the
        # safety checks below still refuse to replace a directory containing
        # backup archives.
        if not relative.parts:
            raise ValueError("Export requires a named share")
        mount_name = relative.parts[0]
    except (ValueError, IndexError):
        raise SupervisorError("Der Exportpfad muss unter /share/<Freigabe> liegen.")
    return SHARE_ROOT / mount_name


def ensure_share_mount(export_path: Path) -> None:
    mountpoint = _export_mount(export_path)
    if not mountpoint.is_dir() or not mountpoint.is_mount():
        raise SupervisorError("Die konfigurierte Home-Assistant-Netzwerkfreigabe ist nicht aktiv.")
    for target in (export_path, export_path.with_name(export_path.name + ".new"), export_path.with_name(export_path.name + ".old")):
        if target.is_symlink():
            raise SupervisorError("Der Wiki-Export darf keine symbolischen Links ersetzen.")
        if target.exists() and any(path.is_file() and path.name.casefold().endswith((".tar", ".tar.gz", ".backup")) for path in target.rglob("*")):
            raise SupervisorError("Der Exportordner enthält Backup-Archive und darf nicht ersetzt werden. Bitte einen eigenen Wiki-Ordner verwenden.")


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
