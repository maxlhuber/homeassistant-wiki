"""Build a secret-free semantic snapshot and calculate weekly changes."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import yaml

from wiki_dashboards import DashboardInventoryError, build_dashboard_snapshot


SNAPSHOT_VERSION = 1
SENSITIVE_KEY = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|"
    r"authorization|credential|webhook[_-]?id|encryption[_-]?key|pin|passcode|"
    r"passphrase|alarm[_-]?code|door[_-]?code|unlock[_-]?code)",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9]{4}(?:-[A-Z0-9]{4}){6}\b"),
)
URL_VALUE = re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)
OPAQUE_VALUE = re.compile(
    r"\b(?=[A-Za-z0-9_-]{28,}\b)(?=[A-Za-z0-9_-]*[A-Za-z])"
    r"(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]+\b"
)
REGISTRY_FIELDS = {
    "floors": ("floor_id", "name", "level"),
    "areas": ("id", "name", "floor_id", "aliases"),
    "devices": (
        "id",
        "name",
        "name_by_user",
        "manufacturer",
        "model",
        "area_id",
        "disabled_by",
        "entry_type",
        "via_device_id",
    ),
    "entities": (
        "id",
        "entity_id",
        "name",
        "original_name",
        "device_id",
        "area_id",
        "platform",
        "disabled_by",
        "entity_category",
    ),
    "labels": ("label_id", "name"),
}
PRIVATE_TEXT_KEYS = {
    "message",
    "title",
    "text",
    "payload",
    "payload_template",
    "value_template",
    "wait_template",
    "variables",
    "event_data",
    "event_data_template",
}
LLM_ALLOWED_KEYS = {
    "description",
    "mode",
    "max",
    "trigger",
    "triggers",
    "condition",
    "conditions",
    "action",
    "actions",
    "service",
    "target",
    "entity_id",
    "device_id",
    "area_id",
    "platform",
    "domain",
    "type",
    "subtype",
    "state",
    "from",
    "to",
    "for",
    "above",
    "below",
    "at",
    "before",
    "after",
    "weekday",
    "event_type",
    "zone",
    "offset",
    "id",
    "enabled",
    "attribute",
    "match",
    "choose",
    "sequence",
    "then",
    "else",
    "if",
    "repeat",
    "while",
    "until",
    "count",
    "parallel",
    "delay",
    "wait_for_trigger",
    "timeout",
    "continue_on_timeout",
    "continue_on_error",
    "stop",
    "error",
    "data",
}
SAFE_SERVICE_DATA_KEYS = {
    "entity_id",
    "area_id",
    "device_id",
    "brightness",
    "brightness_pct",
    "color_temp_kelvin",
    "transition",
    "temperature",
    "hvac_mode",
    "duration",
    "position",
    "tilt_position",
    "percentage",
    "volume_level",
    "source",
    "option",
    "preset_mode",
    "fan_mode",
    "speed",
    "rgb_color",
    "xy_color",
    "color_name",
    "flash",
}
SHORT_PRIVATE_NUMBER = re.compile(r"(?<![\w.])\d{4,8}(?![\w.])")


class SnapshotError(RuntimeError):
    """Raised when the whitelisted data cannot form a valid snapshot."""


@dataclass(frozen=True)
class SnapshotDelta:
    sections: dict[str, dict[str, list[str]]]
    automation_candidates: list[dict[str, Any]]

    @property
    def has_changes(self) -> bool:
        return any(
            values[change]
            for values in self.sections.values()
            for change in ("added", "removed", "modified")
        )

    def summary(self) -> dict[str, dict[str, int]]:
        return {
            section: {kind: len(keys) for kind, keys in values.items()}
            for section, values in self.sections.items()
        }


def canonical(value: Any) -> Any:
    """Normalise mappings without changing the meaningful order of lists."""
    if isinstance(value, dict):
        return {str(key): canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, tuple):
        return [canonical(item) for item in value]
    return value


def semantic_hash(value: Any) -> str:
    raw = json.dumps(
        canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _clean_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return value
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    safe_path = "/" if parsed.path in {"", "/"} else "/<geschützter-pfad>"
    return urlunsplit((parsed.scheme, host, safe_path, "", ""))


def _clean_scalar(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    clean = URL_VALUE.sub(lambda match: _clean_url(match.group(0)), value)
    for pattern in SECRET_VALUE_PATTERNS:
        clean = pattern.sub("<geschützt>", clean)
    clean = OPAQUE_VALUE.sub("<geschützt>", clean)
    if len(clean) > 3000:
        return clean[:3000] + "…"
    return clean


def redact(value: Any) -> Any:
    """Remove credential values while preserving enough structure for wording."""
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            shown_key = str(key)
            if SENSITIVE_KEY.search(shown_key):
                result[shown_key] = "<geschützt>"
            else:
                result[shown_key] = redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    return _clean_scalar(value)


def _read_registry(source: Path, filename: str, key: str) -> list[dict[str, Any]]:
    path = source / ".storage" / filename
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        items = document["data"][key]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise SnapshotError(f"Ungültiges Home-Assistant-Register: {filename}") from error
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise SnapshotError(f"Ungültiges Home-Assistant-Register: {filename}")
    return items


def _read_yaml_list(path: Path) -> list[dict[str, Any]]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise SnapshotError(f"Ungültige YAML-Datei: {path.name}") from error
    if not isinstance(document, list) or not all(isinstance(item, dict) for item in document):
        raise SnapshotError(f"{path.name} muss eine Liste von Einträgen enthalten.")
    return document


def _selected_record(item: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return canonical({field: item.get(field) for field in fields if item.get(field) is not None})


def _registry_map(
    items: list[dict[str, Any]], section: str, primary: str
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        key = item.get(primary)
        if not isinstance(key, str) or not key:
            key = f"missing:{index}"
        records[key] = _selected_record(item, REGISTRY_FIELDS[section])
    return {key: records[key] for key in sorted(records)}


def _humanise_definition(
    value: Any,
    devices: dict[str, dict[str, Any]],
    areas: dict[str, dict[str, Any]],
    entities: dict[str, dict[str, Any]],
) -> Any:
    if isinstance(value, list):
        return [_humanise_definition(item, devices, areas, entities) for item in value]
    if not isinstance(value, dict):
        return redact(value)
    result: dict[str, Any] = {}
    for key, item in value.items():
        shown_key = str(key)
        if SENSITIVE_KEY.search(shown_key) or shown_key in PRIVATE_TEXT_KEYS:
            result[shown_key] = "<geschützt>"
            continue
        if shown_key not in LLM_ALLOWED_KEYS:
            continue
        if shown_key in {"device_id", "area_id", "entity_id"}:
            lookup = devices if shown_key == "device_id" else areas if shown_key == "area_id" else entities

            def shown(identifier: Any) -> Any:
                if not isinstance(identifier, str):
                    return redact(identifier)
                record = lookup.get(identifier, {})
                if shown_key == "device_id":
                    return record.get("name_by_user") or record.get("name") or "Unbenanntes Gerät"
                if shown_key == "area_id":
                    return record.get("name") or identifier
                label = record.get("name") or record.get("original_name")
                return f"{label} [{identifier}]" if label else identifier

            result[shown_key.removesuffix("_id")] = (
                [shown(part) for part in item] if isinstance(item, list) else shown(item)
            )
            continue
        if shown_key == "data" and isinstance(item, dict):
            safe_data: dict[str, Any] = {}
            hidden = 0
            for data_key, data_value in item.items():
                data_name = str(data_key)
                if (
                    SENSITIVE_KEY.search(data_name)
                    or data_name in PRIVATE_TEXT_KEYS
                    or data_name not in SAFE_SERVICE_DATA_KEYS
                ):
                    hidden += 1
                    continue
                if data_name in {"entity_id", "device_id", "area_id"}:
                    safe_data[data_name] = _humanise_definition(
                        {data_name: data_value}, devices, areas, entities
                    ).get(data_name.removesuffix("_id"))
                else:
                    safe_data[data_name] = redact(data_value)
            if hidden:
                safe_data["geschützte_felder"] = hidden
            result[shown_key] = safe_data
            continue
        cleaned = _humanise_definition(item, devices, areas, entities)
        if shown_key in {"alias", "description", "stop", "error"} and isinstance(
            cleaned, str
        ):
            cleaned = SHORT_PRIVATE_NUMBER.sub("<geschützt>", cleaned)
        result[shown_key] = cleaned
    return result


def build_snapshot(source: Path) -> dict[str, Any]:
    source = source.resolve()
    floors_raw = _read_registry(source, "core.floor_registry", "floors")
    areas_raw = _read_registry(source, "core.area_registry", "areas")
    labels_raw = _read_registry(source, "core.label_registry", "labels")
    devices_raw = _read_registry(source, "core.device_registry", "devices")
    entities_raw = _read_registry(source, "core.entity_registry", "entities")
    automations_raw = _read_yaml_list(source / "automations.yaml")
    scenes_raw = _read_yaml_list(source / "scenes.yaml")
    try:
        dashboards = build_dashboard_snapshot(source)
    except DashboardInventoryError as error:
        raise SnapshotError(str(error)) from error

    floors = _registry_map(floors_raw, "floors", "floor_id")
    areas = _registry_map(areas_raw, "areas", "id")
    devices = _registry_map(devices_raw, "devices", "id")
    entities = _registry_map(entities_raw, "entities", "entity_id")
    labels = _registry_map(labels_raw, "labels", "label_id")

    automations: dict[str, dict[str, Any]] = {}
    key_counts: dict[str, int] = {}
    for index, automation in enumerate(automations_raw):
        alias = str(automation.get("alias") or "Automation ohne Namen")
        base_key = str(automation.get("id") or f"alias:{alias}")
        key_counts[base_key] = key_counts.get(base_key, 0) + 1
        key = base_key if key_counts[base_key] == 1 else f"{base_key}#{key_counts[base_key]}"
        automations[key] = {
            "alias": alias,
            "source_hash": semantic_hash(automation),
            "definition": _humanise_definition(automation, devices, areas, entities),
        }

    scenes: dict[str, dict[str, Any]] = {}
    for index, scene in enumerate(scenes_raw):
        key = str(scene.get("id") or scene.get("name") or f"scene:{index}")
        scenes[key] = {
            "name": str(scene.get("name") or "Szene ohne Namen"),
            "source_hash": semantic_hash(scene),
        }

    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "floors": floors,
        "areas": areas,
        "labels": labels,
        "devices": devices,
        "entities": entities,
        "automations": {key: automations[key] for key in sorted(automations)},
        "scenes": {key: scenes[key] for key in sorted(scenes)},
        "dashboards": dashboards,
    }


def _record_changed(section: str, old: dict[str, Any], new: dict[str, Any]) -> bool:
    if section in {"automations", "scenes"}:
        return old.get("source_hash") != new.get("source_hash")
    return canonical(old) != canonical(new)


def calculate_delta(old: dict[str, Any] | None, new: dict[str, Any]) -> SnapshotDelta:
    sections: dict[str, dict[str, list[str]]] = {}
    automation_candidates: list[dict[str, Any]] = []
    for section in (
        "floors",
        "areas",
        "labels",
        "devices",
        "entities",
        "automations",
        "scenes",
        "dashboards",
    ):
        old_items = (old or {}).get(section, {})
        new_items = new.get(section, {})
        if not isinstance(old_items, dict) or not isinstance(new_items, dict):
            raise SnapshotError(f"Snapshot-Abschnitt {section} ist ungültig.")
        old_keys = set(old_items)
        new_keys = set(new_items)
        added = sorted(new_keys - old_keys)
        removed = sorted(old_keys - new_keys)
        modified = sorted(
            key
            for key in old_keys & new_keys
            if _record_changed(section, old_items[key], new_items[key])
        )
        sections[section] = {"added": added, "removed": removed, "modified": modified}
        if section == "automations":
            for key in added + modified:
                record = new_items[key]
                automation_candidates.append(
                    {
                        "change": "added" if key in added else "modified",
                        "alias": record["alias"],
                        "definition": record["definition"],
                    }
                )
    return SnapshotDelta(sections=sections, automation_candidates=automation_candidates)


def load_snapshot(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SnapshotError("Der vorherige Wiki-Snapshot ist beschädigt.") from error
    if not isinstance(document, dict) or document.get("snapshot_version") != SNAPSHOT_VERSION:
        raise SnapshotError("Der vorherige Wiki-Snapshot hat eine unbekannte Version.")
    return document


def write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_text(
        json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
