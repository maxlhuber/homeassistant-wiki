"""PC-independent weekly Home Assistant wiki update orchestrator.

This command prepares and validates updated documentation.  Publishing is kept
outside this module so a failed or review-required run cannot replace the live
site accidentally.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from wiki_backup import (
    BackupExtractionError,
    discover_latest_backup,
    extract_home_assistant_backup,
)
from wiki_openai import (
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    OpenAIClientError,
    OpenAIResult,
    probe_api_credit,
    request_automation_wording,
)
from wiki_snapshot import (
    SECRET_VALUE_PATTERNS,
    SnapshotDelta,
    SnapshotError,
    build_snapshot,
    calculate_delta,
    destructive_change_reason,
    load_snapshot,
    semantic_hash,
    write_snapshot,
)


BLOCKED_EXIT = 20
FAILED_EXIT = 30
CRITICAL_AUTOMATION = re.compile(
    r"(?:rauch|feuer|alarm|tür|tuer|schloss|nuki|wasser|ventil|wallbox|laden|lade)",
    re.IGNORECASE,
)
GENERATED_FIELDS = {
    "description",
    "trigger_steps",
    "condition_steps",
    "action_steps",
    "manual",
    "safety_note",
}
GERMAN_MONTHS = (
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_status(path: Path, **values: Any) -> None:
    document = {"updated_at": _now_iso(), **values}
    _write_json_atomic(path, document)


def _review_is_approved(path: Path, fingerprint: str) -> bool:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(document, dict)
        and document.get("snapshot_fingerprint") == fingerprint
        and document.get("approved") is True
    )


def _backup_date_label(raw: str | None, fallback: Path) -> str:
    parsed: dt.datetime | None = None
    if raw:
        try:
            parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
    if parsed is None:
        marker = fallback / "backup.json" if fallback.is_dir() else fallback
        parsed = dt.datetime.fromtimestamp(marker.stat().st_mtime)
    return f"{parsed.day}. {GERMAN_MONTHS[parsed.month - 1]} {parsed.year}"


def _backup_time(raw: str | None, fallback: Path) -> dt.datetime:
    parsed: dt.datetime | None = None
    if raw:
        try:
            parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
    if parsed is None:
        marker = fallback / "backup.json" if fallback.is_dir() else fallback
        parsed = dt.datetime.fromtimestamp(marker.stat().st_mtime).astimezone()
    elif parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
    return parsed.astimezone(dt.timezone.utc)


def _assert_backup_fresh(raw: str | None, fallback: Path, max_age_seconds: int) -> None:
    if max_age_seconds <= 0:
        return
    parsed = _backup_time(raw, fallback)
    age = dt.datetime.now(dt.timezone.utc) - parsed
    if age.total_seconds() < -86400:
        raise BackupExtractionError(
            "backup_date_invalid", "Das neueste Backup trägt ein unplausibles Datum in der Zukunft."
        )
    if age.total_seconds() > max_age_seconds:
        days = max(1, int(age.total_seconds() // 86400))
        raise BackupExtractionError(
            "backup_stale", f"Das neueste gültige Home-Assistant-Backup ist bereits {days} Tage alt."
        )


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise RuntimeError(f"Ungültige Override-Datei: {path.name}") from error
    if not isinstance(document, dict):
        raise RuntimeError(f"Ungültige Override-Datei: {path.name}")
    return document


def _read_secret_file(path: Path | None, label: str) -> str | None:
    """Read a small systemd credential without ever logging its value."""
    if path is None:
        return None
    try:
        if path.stat().st_size > 8192:
            raise RuntimeError(f"Die Zugangsdaten-Datei für {label} ist unplausibel groß.")
        value = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise RuntimeError(f"Die Zugangsdaten-Datei für {label} ist nicht lesbar.") from error
    return value or None


def merge_ai_overrides(
    existing: dict[str, Any],
    result: OpenAIResult,
    current_aliases: set[str],
    drop_aliases: set[str] | None = None,
) -> dict[str, Any]:
    """Update only the machine-owned wording file and discard orphaned aliases."""
    current = existing.get("automation_overrides", {})
    if not isinstance(current, dict):
        current = {}
    automations: dict[str, dict[str, Any]] = {}
    dropped = drop_aliases or set()
    for alias, value in current.items():
        if alias not in current_aliases or alias in dropped or not isinstance(value, dict):
            continue
        automations[str(alias)] = {
            key: item for key, item in value.items() if key in GENERATED_FIELDS
        }
    for alias, value in result.overrides.items():
        automations[alias] = {
            key: item for key, item in value.items() if key in GENERATED_FIELDS
        }
    return {
        "metadata": {
            "purpose": "Automatisch erzeugte Formulierungen; manuelle Overrides haben immer Vorrang.",
            "generated_at": _now_iso(),
        },
        "automation_overrides": {
            alias: automations[alias] for alias in sorted(automations, key=str.casefold)
        },
    }


def _write_yaml_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    header = (
        "# Automatisch erzeugt. Nicht manuell bearbeiten.\n"
        "# scripts/wiki_overrides.yaml hat für jedes Feld Vorrang.\n\n"
    )
    temporary.write_text(
        header + yaml.safe_dump(value, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _run_generator(
    repo: Path,
    source: Path,
    docs: Path,
    manual_overrides: Path,
    ai_overrides: Path,
    source_date: str,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).with_name("generate_docs.py")),
        str(source),
        str(docs),
        "--overrides",
        str(manual_overrides),
        "--ai-overrides",
        str(ai_overrides),
        "--inventory-source-date",
        source_date,
    ]
    completed = subprocess.run(
        command,
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Der Wiki-Generator hat keine Zusammenfassung geliefert.")
    summary = json.loads(lines[-1])
    if not isinstance(summary, dict):
        raise RuntimeError("Ungültige Generator-Zusammenfassung.")
    return summary


def _secret_scan(root: Path, literal_secrets: list[str]) -> None:
    hits: list[str] = []
    exact = [secret for secret in literal_secrets if len(secret) >= 6]
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(secret in text for secret in exact) or any(
            pattern.search(text) for pattern in SECRET_VALUE_PATTERNS
        ):
            hits.append(path.relative_to(root).as_posix())
    if hits:
        raise RuntimeError(
            "Die Veröffentlichung wurde wegen eines geheimnisähnlichen Inhalts gestoppt: "
            + ", ".join(hits[:10])
        )


def _strict_build(repo: Path, project: Path) -> None:
    site = project / "site"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "mkdocs",
            "build",
            "--clean",
            "--strict",
            "--config-file",
            str(project / "mkdocs.yml"),
            "--site-dir",
            str(site),
        ],
        cwd=project,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-2000:]
        raise RuntimeError(f"Der strenge Wiki-Build ist fehlgeschlagen: {detail}")
    required_pages = (site / "index.html", site / "automationen" / "index.html", site / "geraete" / "index.html")
    if not all(path.is_file() and path.stat().st_size > 200 for path in required_pages):
        raise RuntimeError("Der Wiki-Build enthält nicht alle erforderlichen Startseiten.")


def _validate_and_stage_docs(
    repo: Path,
    state_dir: Path,
    source: Path,
    manual_overrides: Path,
    ai_overrides: Path,
    source_date: str,
    literal_secrets: list[str],
) -> tuple[Path, dict[str, Any]]:
    project = Path(tempfile.mkdtemp(prefix="wiki-candidate-", dir=state_dir / "work"))
    try:
        docs = project / "docs"
        shutil.copytree(repo / "docs", docs)
        shutil.copy2(repo / "mkdocs.yml", project / "mkdocs.yml")
        summary = _run_generator(
            repo, source, docs, manual_overrides, ai_overrides, source_date
        )
        first_hash = _tree_hash(docs)
        second_summary = _run_generator(
            repo, source, docs, manual_overrides, ai_overrides, source_date
        )
        if first_hash != _tree_hash(docs) or summary != second_summary:
            raise RuntimeError("Der Wiki-Generator liefert bei gleicher Eingabe unterschiedliche Ergebnisse.")
        if int(summary.get("areas", 0)) <= 0 or int(summary.get("automations", 0)) <= 0:
            raise RuntimeError("Die Inventarprüfung meldet unplausibel wenige Inhalte.")
        _secret_scan(docs, literal_secrets)
        _strict_build(repo, project)
        return project, summary
    except Exception:
        shutil.rmtree(project, ignore_errors=True)
        raise


def _replace_docs(repo: Path, staged_docs: Path) -> None:
    destination = repo / "docs"
    incoming = repo / ".docs-weekly-new"
    previous = repo / ".docs-weekly-old"
    shutil.rmtree(incoming, ignore_errors=True)
    shutil.rmtree(previous, ignore_errors=True)
    shutil.copytree(staged_docs, incoming)
    destination.replace(previous)
    try:
        incoming.replace(destination)
    except Exception:
        previous.replace(destination)
        raise
    shutil.rmtree(previous)


def _replace_publish_site(state_dir: Path, staged_site: Path) -> None:
    """Prepare static, already validated files for the privileged publisher."""
    destination = state_dir / "publish-site"
    incoming = state_dir / ".publish-site-new"
    previous = state_dir / ".publish-site-old"
    shutil.rmtree(incoming, ignore_errors=True)
    shutil.rmtree(previous, ignore_errors=True)
    shutil.copytree(staged_site, incoming, symlinks=False)
    if destination.exists():
        destination.replace(previous)
    try:
        incoming.replace(destination)
    except Exception:
        if previous.exists():
            previous.replace(destination)
        raise
    shutil.rmtree(previous, ignore_errors=True)


def _changed_aliases(
    delta: SnapshotDelta, old: dict[str, Any] | None, new: dict[str, Any]
) -> tuple[set[str], set[str]]:
    new_aliases = {
        new["automations"][key]["alias"]
        for key in delta.sections["automations"]["added"]
        + delta.sections["automations"]["modified"]
    }
    old_aliases = {
        old["automations"][key]["alias"]
        for key in delta.sections["automations"]["removed"]
        + delta.sections["automations"]["modified"]
        if old and key in old.get("automations", {})
    }
    return new_aliases, old_aliases


def _review_reason(
    delta: SnapshotDelta,
    old: dict[str, Any] | None,
    new: dict[str, Any],
    manual_aliases: set[str],
) -> str | None:
    reasons: list[str] = []
    destructive = destructive_change_reason(old, delta)
    if destructive:
        reasons.append(destructive)
    if old is None:
        return " ".join(reasons) or None
    dashboard_changes = delta.sections.get("dashboards", {})
    new_dashboards = new.get("dashboards", {})
    dashboard_migration_needs_review = (
        "dashboards" not in old
        and isinstance(new_dashboards, dict)
        and (
            not new_dashboards
            or any(str(key).startswith("unbekannt-") for key in new_dashboards)
        )
    )
    dashboard_changed = "dashboards" in old and any(
        dashboard_changes.get(kind) for kind in ("added", "removed", "modified")
    )
    if dashboard_migration_needs_review or dashboard_changed:
        reasons.append(
            "Mindestens ein Home-Assistant-Dashboard wurde geändert. "
            "Die bebilderten Wiki-Anleitungen müssen vor der Veröffentlichung "
            "auf Aktualität geprüft werden."
        )
    new_aliases, old_aliases = _changed_aliases(delta, old, new)
    manual_changed = sorted((new_aliases | old_aliases) & manual_aliases, key=str.casefold)
    if manual_changed:
        reasons.append(
            "Mindestens eine geänderte Automation besitzt eine bewusst geprüfte manuelle "
            "Beschreibung: " + ", ".join(manual_changed)
        )
    critical = sorted(
        (alias for alias in new_aliases | old_aliases if CRITICAL_AUTOMATION.search(alias)),
        key=str.casefold,
    )
    if critical:
        reasons.append(
            "Eine sicherheits- oder versorgungsrelevante Automation wurde geändert: "
            + ", ".join(critical)
        )
    return " ".join(reasons) or None


def _review_credit_probe_required(no_ai: bool, delta: SnapshotDelta) -> bool:
    """Avoid an API call when a local-only dashboard review already blocks the run."""
    return not no_ai and bool(delta.automation_candidates)


def _arguments() -> argparse.Namespace:
    repo_default = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=repo_default)
    parser.add_argument(
        "--backup-root",
        type=Path,
        default=Path(os.environ.get("WIKI_BACKUP_DIR", "/mnt/homeassistant-backups")),
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path(os.environ.get("WIKI_STATE_DIR", "/var/lib/homeassistant-wiki")),
    )
    parser.add_argument("--min-backup-age", type=int, default=300)
    parser.add_argument(
        "--max-backup-age",
        type=int,
        default=int(os.environ.get("WIKI_MAX_BACKUP_AGE", 8 * 24 * 60 * 60)),
    )
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--endpoint", default=os.environ.get("OPENAI_RESPONSES_URL", DEFAULT_ENDPOINT))
    parser.add_argument("--backup-key-file", type=Path)
    parser.add_argument("--openai-key-file", type=Path)
    parser.add_argument("--no-ai", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    repo = args.repo.resolve()
    state_dir = args.state_dir.resolve()
    work_dir = state_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    status_path = state_dir / "last_status.json"
    snapshot_path = state_dir / "last_snapshot.json"
    last_backup_path = state_dir / "last_backup.json"
    ai_overrides_path = state_dir / "wiki_ai_overrides.yaml"
    review_approval_path = state_dir / "review-approval.json"
    manual_overrides_path = repo / "scripts" / "wiki_overrides.yaml"
    prompt_path = Path(__file__).with_name("wiki_ai_prompt.txt")
    backup_key = _read_secret_file(args.backup_key_file, "Home Assistant")
    if backup_key is None:
        backup_key = os.environ.get("HA_BACKUP_KEY")
    api_key = _read_secret_file(args.openai_key_file, "OpenAI")
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
    literal_secrets = [
        value
        for value in (
            backup_key,
            api_key,
            os.environ.get("WIKI_NAS_PASSWORD"),
            os.environ.get("HA_TOKEN"),
        )
        if value
    ]
    backup: Path | None = None
    try:
        backup = discover_latest_backup(args.backup_root, args.min_backup_age)
        extracted = extract_home_assistant_backup(
            backup, work_dir / "extracted", backup_key
        )
        _assert_backup_fresh(extracted.backup_date, backup, args.max_backup_age)
        backup_time = _backup_time(extracted.backup_date, backup)
        source_date = _backup_date_label(extracted.backup_date, backup)
        new_snapshot = build_snapshot(extracted.destination)
        snapshot_fingerprint = semantic_hash(new_snapshot)
        review_approved = _review_is_approved(
            review_approval_path, snapshot_fingerprint
        )
        old_snapshot = load_snapshot(snapshot_path)
        delta = calculate_delta(old_snapshot, new_snapshot)
        manual = _load_yaml_mapping(manual_overrides_path)
        manual_automations = manual.get("automation_overrides", {})
        manual_aliases = set(manual_automations) if isinstance(manual_automations, dict) else set()
        rollback_reason: str | None = None
        if last_backup_path.exists():
            try:
                last_backup = json.loads(last_backup_path.read_text(encoding="utf-8"))
                previous_raw = last_backup.get("backup_time")
                previous_time = dt.datetime.fromisoformat(str(previous_raw))
                if previous_time.tzinfo is None:
                    previous_time = previous_time.replace(tzinfo=dt.timezone.utc)
                if backup_time < previous_time.astimezone(dt.timezone.utc):
                    rollback_reason = (
                        "Das ausgewählte Backup ist älter als der zuletzt veröffentlichte "
                        "Wiki-Stand und braucht eine bewusste Freigabe."
                    )
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                rollback_reason = "Der gespeicherte Backup-Zeitpunkt ist unlesbar und muss geprüft werden."
        review_reasons = [
            reason
            for reason in (
                rollback_reason,
                _review_reason(delta, old_snapshot, new_snapshot, manual_aliases),
            )
            if reason
        ]
        review_reason = " ".join(review_reasons) or None
        if review_reason and not review_approved:
            review_probe = OpenAIResult({}, False, None, {}, None)
            review_warning: OpenAIClientError | None = None
            review_probe_attempted = _review_credit_probe_required(
                args.no_ai, delta
            )
            if review_probe_attempted:
                try:
                    review_probe = probe_api_credit(
                        api_key=api_key,
                        model=args.model,
                        endpoint=args.endpoint,
                    )
                except OpenAIClientError as error:
                    review_warning = error
            _write_status(
                status_path,
                outcome="blocked",
                reason_kind="review_required",
                message=review_reason,
                backup=backup.name,
                backup_date=source_date,
                delta=delta.summary(),
                snapshot_fingerprint=snapshot_fingerprint,
                warning_kind=review_warning.kind if review_warning else None,
                warning_message=str(review_warning) if review_warning else None,
                warning_retryable=(review_warning.retryable if review_warning else None),
                warning_http_status=(review_warning.status if review_warning else None),
                openai_credit_probe=review_probe_attempted,
                openai_model=args.model if review_probe_attempted else None,
                openai_usage=review_probe.usage,
                openai_response_id=review_probe.response_id,
            )
            return BLOCKED_EXIT

        ai_result = OpenAIResult({}, False, None, {}, None)
        warning: OpenAIClientError | None = None
        regular_ai_attempted = False
        credit_probe_attempted = False
        candidates = [
            item
            for item in delta.automation_candidates
            if item["alias"] not in manual_aliases
        ]
        if old_snapshot is not None and candidates:
            regular_ai_attempted = True
            try:
                if args.no_ai:
                    raise OpenAIClientError(
                        "ai_disabled",
                        "KI-Formulierungen sind deaktiviert, obwohl Automationen geändert wurden.",
                    )
                ai_result = request_automation_wording(
                    candidates,
                    api_key=api_key,
                    prompt_path=prompt_path,
                    model=args.model,
                    endpoint=args.endpoint,
                )
            except OpenAIClientError as error:
                warning = error
            if ai_result.review_required:
                _write_status(
                    status_path,
                    outcome="blocked",
                    reason_kind="model_review_required",
                    message=ai_result.review_reason or "Die KI hat eine manuelle Prüfung angefordert.",
                    backup=backup.name,
                    backup_date=source_date,
                    delta=delta.summary(),
                    snapshot_fingerprint=snapshot_fingerprint,
                    openai_usage=ai_result.usage,
                    openai_response_id=ai_result.response_id,
                )
                return BLOCKED_EXIT
        elif not args.no_ai and not review_approved:
            credit_probe_attempted = True
            try:
                ai_result = probe_api_credit(
                    api_key=api_key,
                    model=args.model,
                    endpoint=args.endpoint,
                )
            except OpenAIClientError as error:
                warning = error

        existing_ai = _load_yaml_mapping(ai_overrides_path)
        current_aliases = {
            record["alias"] for record in new_snapshot["automations"].values()
        }
        next_ai = merge_ai_overrides(
            existing_ai,
            ai_result,
            current_aliases,
            drop_aliases=(
                {str(item["alias"]) for item in candidates}
                if warning and regular_ai_attempted
                else set()
            ),
        )
        pending_ai = work_dir / "wiki_ai_overrides.yaml"
        _write_yaml_atomic(pending_ai, next_ai)
        staged_project, summary = _validate_and_stage_docs(
            repo,
            state_dir,
            extracted.destination,
            manual_overrides_path,
            pending_ai,
            source_date,
            literal_secrets,
        )
        try:
            _replace_publish_site(state_dir, staged_project / "site")
            _replace_docs(repo, staged_project / "docs")
        finally:
            shutil.rmtree(staged_project, ignore_errors=True)
        _write_yaml_atomic(ai_overrides_path, next_ai)
        write_snapshot(snapshot_path, new_snapshot)
        _write_json_atomic(
            last_backup_path,
            {"backup_time": backup_time.isoformat(), "backup_name": backup.name},
        )
        if review_approved:
            review_approval_path.unlink(missing_ok=True)
        if old_snapshot is None:
            outcome = "ready_baseline"
        elif delta.has_changes:
            outcome = "ready_changed"
        else:
            outcome = "ready_metadata_only"
        _write_status(
            status_path,
            outcome=outcome,
            backup=backup.name,
            backup_date=source_date,
            delta=delta.summary(),
            generator=summary,
            warning_kind=warning.kind if warning else None,
            warning_message=str(warning) if warning else None,
            warning_retryable=warning.retryable if warning else None,
            warning_http_status=warning.status if warning else None,
            openai_called=regular_ai_attempted,
            openai_credit_probe=credit_probe_attempted,
            openai_model=args.model if regular_ai_attempted or credit_probe_attempted else None,
            openai_usage=ai_result.usage,
            openai_response_id=ai_result.response_id,
            review_approved=review_approved,
        )
        return 0
    except OpenAIClientError as error:
        _write_status(
            status_path,
            outcome="blocked",
            reason_kind=error.kind,
            message=str(error),
            retryable=error.retryable,
            http_status=error.status,
            backup=backup.name if backup else None,
        )
        return BLOCKED_EXIT
    except (BackupExtractionError, SnapshotError) as error:
        _write_status(
            status_path,
            outcome="failed",
            reason_kind=getattr(error, "kind", "source_invalid"),
            message=str(error),
            backup=backup.name if backup else None,
        )
        return FAILED_EXIT
    except (OSError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        _write_status(
            status_path,
            outcome="failed",
            reason_kind="pipeline_error",
            message=str(error)[:2000],
            backup=backup.name if backup else None,
        )
        return FAILED_EXIT


def main() -> None:
    raise SystemExit(run(_arguments()))


if __name__ == "__main__":
    main()
