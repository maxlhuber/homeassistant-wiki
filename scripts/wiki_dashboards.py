"""Create a deterministic dashboard inventory without publishing HA contents."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

import yaml


REGISTRY_MEMBER = ".storage/lovelace_dashboards"

DASHBOARD_SOURCES: dict[str, dict[str, Any]] = {
    ".storage/lovelace.lovelace": {
        "key": "uebersicht",
        "title": "Übersicht",
        "visible": True,
        "mode": "Speicher",
        "registry_ids": (),
        "registry_paths": ("lovelace",),
    },
    ".storage/lovelace.dashboard_test": {
        "key": "dashboard-test",
        "title": "Dashboard (Test)",
        "visible": False,
        "mode": "Speicher",
        "registry_ids": ("dashboard_test",),
        "registry_paths": ("dashboard-test",),
    },
    ".storage/lovelace.map": {
        "key": "karte-alt",
        "title": "Karte (alte Variante)",
        "visible": True,
        "mode": "Speicher",
        "registry_ids": ("map",),
        "registry_paths": ("map",),
    },
    ".storage/lovelace.familien_karte": {
        "key": "karte",
        "title": "Karte",
        "visible": True,
        "mode": "Speicher",
        "registry_ids": ("familien_karte",),
        "registry_paths": ("familien-karte",),
    },
    ".storage/lovelace.system_status": {
        "key": "systemstatus",
        "title": "Systemstatus",
        "visible": True,
        "mode": "Speicher",
        "registry_ids": ("system_status",),
        "registry_paths": ("system-status",),
    },
    "dashboards/cupra_laden.yaml": {
        "key": "cupra-laden",
        "title": "Cupra Laden",
        "visible": True,
        "mode": "YAML",
        "registry_ids": (),
        "registry_paths": ("cupra-laden",),
    },
}

DASHBOARD_MEMBER_NAMES = (REGISTRY_MEMBER, *DASHBOARD_SOURCES)

PURPOSES = {
    "uebersicht": "Alltag, Räume, Wetter, Hausgeräte, Strom und Wallbox",
    "cupra-laden": "Ladevorgänge, Energieanteile und Ladekosten des Cupra",
    "karte": "Standorte von Max und Meike",
    "karte-alt": "Frühere Kartenvariante; Prüfung und Entfernung empfohlen",
    "systemstatus": "Technischer Zustand und Diagnose für Max",
    "dashboard-test": "Versteckte Testfläche; nicht für den Alltag",
}

LAYOUT_LABELS = {
    "masonry": "Kacheln",
    "panel": "Vollbild",
    "sections": "Abschnitte",
    "sidebar": "Seitenleiste",
}


class DashboardInventoryError(RuntimeError):
    """Raised when an optional dashboard file is present but invalid."""


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    return value


def _semantic_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DashboardInventoryError(
            f"Ungültige Dashboard-Datei: {path.name}"
        ) from error
    if not isinstance(document, dict):
        raise DashboardInventoryError(f"Ungültige Dashboard-Datei: {path.name}")
    return document


def _read_storage_dashboard(path: Path) -> dict[str, Any]:
    document = _read_json(path)
    try:
        config = document["data"]["config"]
    except (KeyError, TypeError) as error:
        raise DashboardInventoryError(
            f"Ungültige Dashboard-Datei: {path.name}"
        ) from error
    if not isinstance(config, dict):
        raise DashboardInventoryError(f"Ungültige Dashboard-Datei: {path.name}")
    return config


def _read_yaml_dashboard(path: Path) -> dict[str, Any]:
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise DashboardInventoryError(
            f"Ungültige Dashboard-Datei: {path.name}"
        ) from error
    if not isinstance(config, dict):
        raise DashboardInventoryError(f"Ungültige Dashboard-Datei: {path.name}")
    return config


def _read_registry(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.is_symlink() or not path.is_file():
        raise DashboardInventoryError(
            "Dashboard-Verzeichnis ist keine reguläre Datei."
        )
    document = _read_json(path)
    try:
        items = document["data"]["items"]
    except (KeyError, TypeError) as error:
        raise DashboardInventoryError(
            "Das Dashboard-Verzeichnis besitzt nicht die erwartete Struktur."
        ) from error
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise DashboardInventoryError(
            "Das Dashboard-Verzeichnis besitzt nicht die erwartete Struktur."
        )
    return items


def _structure_count(value: Any) -> int:
    if isinstance(value, list):
        return sum(_structure_count(item) for item in value)
    if not isinstance(value, dict):
        return 0
    own = 1 if isinstance(value.get("type"), str) and value.get("type") else 0
    return own + sum(
        _structure_count(child)
        for child in value.values()
        if isinstance(child, (dict, list))
    )


def _summarise_config(config: dict[str, Any]) -> dict[str, Any]:
    views = config.get("views") or []
    if not isinstance(views, list):
        raise DashboardInventoryError(
            "Ein Dashboard besitzt keine gültige Ansichtsliste."
        )
    summaries: list[dict[str, Any]] = []
    for index, view in enumerate(views):
        if not isinstance(view, dict):
            raise DashboardInventoryError("Eine Dashboard-Ansicht ist ungültig.")
        layout = view.get("type")
        summaries.append(
            {
                "title": f"Ansicht {index + 1}",
                "layout": LAYOUT_LABELS.get(layout, "Standard"),
                "structure_count": _structure_count(view),
            }
        )
    return {
        "view_count": len(summaries),
        "views": summaries,
        "strategy": isinstance(config.get("strategy"), dict),
    }


def _known_source_for_registry(item: dict[str, Any]) -> str | None:
    item_id = item.get("id")
    item_path = item.get("url_path")
    for relative, metadata in DASHBOARD_SOURCES.items():
        if isinstance(item_id, str) and item_id in metadata["registry_ids"]:
            return relative
        if isinstance(item_path, str) and item_path in metadata["registry_paths"]:
            return relative
    return None


def _safe_mode(value: Any, fallback: str) -> str:
    if value == "yaml":
        return "YAML"
    if value == "storage":
        return "Speicher"
    return fallback


def _metadata_record(
    metadata: dict[str, Any],
    registry_item: dict[str, Any] | None,
) -> dict[str, Any]:
    record = {
        "title": str(metadata["title"]),
        "visible": bool(metadata["visible"]),
        "mode": str(metadata["mode"]),
        "metadata_hash": _semantic_hash(registry_item) if registry_item else None,
    }
    if registry_item:
        shown = registry_item.get("show_in_sidebar")
        if isinstance(shown, bool):
            record["visible"] = shown
        record["mode"] = _safe_mode(registry_item.get("mode"), record["mode"])
    return record


def build_dashboard_snapshot(source: Path) -> dict[str, dict[str, Any]]:
    """Return structural data and hashes, never titles, paths, entities or card text."""
    dashboards: dict[str, dict[str, Any]] = {}
    source = source.resolve()
    registry_items = _read_registry(source / REGISTRY_MEMBER)
    registry_by_source: dict[str, dict[str, Any]] = {}
    unknown_items: list[dict[str, Any]] = []
    for item in registry_items:
        relative = _known_source_for_registry(item)
        if relative is None:
            unknown_items.append(item)
            continue
        if relative in registry_by_source:
            raise DashboardInventoryError(
                "Ein bekanntes Dashboard ist im Verzeichnis doppelt vorhanden."
            )
        registry_by_source[relative] = item

    for relative, metadata in DASHBOARD_SOURCES.items():
        path = source / Path(relative)
        registry_item = registry_by_source.get(relative)
        if not path.exists() and registry_item is None:
            continue
        if path.exists():
            if path.is_symlink() or not path.is_file():
                raise DashboardInventoryError(
                    f"Dashboard-Quelle ist keine reguläre Datei: {path.name}"
                )
            config = (
                _read_yaml_dashboard(path)
                if path.suffix == ".yaml"
                else _read_storage_dashboard(path)
            )
            summary = _summarise_config(config)
            source_hash = _semantic_hash(config)
        else:
            summary = {"view_count": 0, "views": [], "strategy": False}
            source_hash = _semantic_hash({"registry_only": True})
        key = str(metadata["key"])
        if key in dashboards:
            raise DashboardInventoryError(
                f"Dashboard {key} ist in mehreren Quellen gleichzeitig vorhanden."
            )
        dashboards[key] = {
            **_metadata_record(metadata, registry_item),
            "source_hash": source_hash,
            **summary,
        }

    for item in unknown_items:
        digest = _semantic_hash(item)
        key = f"unbekannt-{digest[:12]}"
        dashboards[key] = {
            "title": "Neues Dashboard (Prüfung nötig)",
            "visible": (
                item["show_in_sidebar"]
                if isinstance(item.get("show_in_sidebar"), bool)
                else False
            ),
            "mode": _safe_mode(item.get("mode"), "unbekannt"),
            "metadata_hash": digest,
            "source_hash": digest,
            "view_count": 0,
            "views": [],
            "strategy": False,
        }

    return {key: dashboards[key] for key in sorted(dashboards)}


def write_dashboard_inventory(
    source: Path, destination: Path, source_date: str
) -> int:
    dashboards = build_dashboard_snapshot(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---\n",
        "search:\n",
        "  exclude: true\n",
        "---\n\n",
        "<!-- Automatisch erzeugt. Änderungen werden beim nächsten Wochenlauf ersetzt. -->\n\n",
        "# Automatisch erkannte Dashboard-Struktur\n\n",
        "Diese technische Kontrollseite für Max zeigt nur den groben Aufbau und den "
        "bekannten Zweck. Inhalte, technische Kennungen und interne Pfade werden "
        "nicht veröffentlicht.\n\n",
    ]
    if not dashboards:
        lines.extend(
            [
                "Es wurden im ausgewählten Backup keine Dashboard-Dateien erkannt. "
                "Der Wochenlauf hält bei einem unerwarteten Wechsel zu diesem Zustand "
                "zur Prüfung an.\n\n",
            ]
        )
    else:
        lines.extend(
            [
                "| Dashboard | Aufgabe | Sichtbar | Ansichten | Modus |\n",
                "|---|---|---:|---:|---|\n",
            ]
        )
        for key, dashboard in dashboards.items():
            purpose = PURPOSES.get(key, "Unbekanntes Dashboard; manuelle Prüfung nötig")
            lines.append(
                f"| {dashboard['title']} | {purpose} "
                f"| {'ja' if dashboard['visible'] else 'nein'} "
                f"| {dashboard['view_count']} | {dashboard['mode']} |\n"
            )
        lines.extend(
            [
                "\n## Erkannte Ansichten\n\n",
                "Ändert sich diese Struktur, stoppt der Wochenlauf vor der Veröffentlichung. "
                "So können die bebilderten Anleitungen geprüft und bei Bedarf neu "
                "aufgenommen werden.\n\n",
            ]
        )
        for key, dashboard in dashboards.items():
            lines.append(f"### {dashboard['title']}\n\n")
            if dashboard["strategy"]:
                lines.append("- Die Oberfläche wird automatisch erzeugt.\n")
            if not dashboard["views"]:
                lines.append("- Keine feste Ansicht ausgelesen.\n")
            for view in dashboard["views"]:
                lines.append(
                    f"- **{view['title']}** – Layout: {view['layout']}; "
                    f"Strukturelemente: {view['structure_count']}\n"
                )
            lines.append("\n")
    lines.append(
        f'<p class="page-status">Dashboard-Struktur aus Backup vom '
        f"{html.escape(str(source_date)[:80])}</p>\n"
    )
    temporary = destination.with_suffix(destination.suffix + ".new")
    temporary.write_text("".join(lines), encoding="utf-8")
    temporary.replace(destination)
    return len(dashboards)
