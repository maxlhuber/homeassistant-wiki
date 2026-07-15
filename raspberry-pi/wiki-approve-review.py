#!/usr/bin/python3
"""Approve exactly the blocked, secret-free wiki snapshot shown to the operator."""

from __future__ import annotations

import json
import os
import pwd
import re
import subprocess
import tempfile
from pathlib import Path


STATUS = Path("/var/lib/homeassistant-wiki/last_status.json")
APPROVAL = Path("/var/lib/homeassistant-wiki/review-approval.json")


def main() -> None:
    if os.geteuid() != 0:
        raise SystemExit("Bitte mit sudo ausführen.")
    try:
        status = json.loads(STATUS.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SystemExit("Es liegt kein lesbarer Prüfauftrag vor.") from error
    if not isinstance(status, dict) or status.get("outcome") != "blocked":
        raise SystemExit("Aktuell wartet keine Wiki-Aktualisierung auf Freigabe.")
    if status.get("reason_kind") not in {"review_required", "model_review_required"}:
        raise SystemExit("Dieser Fehler kann nicht per Freigabe übersprungen werden.")
    fingerprint = status.get("snapshot_fingerprint")
    if not isinstance(fingerprint, str) or not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
        raise SystemExit("Der Prüfauftrag besitzt keinen gültigen Fingerabdruck.")
    reason = str(status.get("message") or "Manuelle Prüfung erforderlich.")
    print("\nPrüfgrund:\n" + reason + "\n")
    answer = input("Genau diesen Stand freigeben und erneut ausführen? Tippe JA: ")
    if answer != "JA":
        raise SystemExit("Keine Freigabe erteilt.")

    APPROVAL.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".review-approval-", dir=APPROVAL.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(
                {"approved": True, "snapshot_fingerprint": fingerprint},
                output,
                indent=2,
            )
            output.write("\n")
        user = pwd.getpwnam("wikiadmin")
        os.chown(temporary, user.pw_uid, user.pw_gid)
        temporary.replace(APPROVAL)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    subprocess.run(
        ["systemctl", "start", "--no-block", "wiki-weekly.service"], check=True
    )
    print("Freigabe gespeichert. Die geprüfte Aktualisierung startet jetzt erneut.")


if __name__ == "__main__":
    main()
