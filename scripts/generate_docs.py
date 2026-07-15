"""Generate sanitized Wiki pages from an extracted Home Assistant backup.

The source directory must contain the selected YAML files and registry files from
Home Assistant. Registries are read to resolve relationships, but identifiers,
connections and unique IDs are never published. The script deliberately does not
read config entries, secrets, credentials, history databases or cloud data.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

from wiki_snapshot import OPAQUE_VALUE, SECRET_VALUE_PATTERNS, SHORT_PRIVATE_NUMBER


GENERATED_NOTICE = (
    "<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. "
    "Nicht direkt bearbeiten. -->\n\n"
)
ENTITY_RE = re.compile(r"\b[a-z_]+\.[a-z0-9_]+\b")
SOURCE_URL_PATTERN = re.compile(
    r"(?:"
    r"(?:(?:https?|ftp|file)\s*://|(?:javascript|data|mailto|tel)\s*:|www\.|"
    r"(?<![\w.])//)[^\s<>'\"]+"
    r"|(?<![\w@])(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s<>'\"]*)?"
    r"|(?<![\w@])(?:[a-z0-9-]+\.)+"
    r"(?:app|at|ch|cloud|com|de|dev|eu|info|io|local|me|net|org|uk|xyz)"
    r"(?::\d+)?(?:/[^\s<>'\"]*)?"
    r")",
    re.IGNORECASE,
)
SOURCE_TEMPLATE_PATTERN = re.compile(
    r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}", re.DOTALL
)
SOURCE_LABELED_SECRET = re.compile(
    r"\b(?:password|passwort|passwd|secret|token|api[ _-]?key|access[ _-]?key|"
    r"private[ _-]?key|pin|passcode|door[ _-]?code|türcode|alarmcode)\b"
    r"(?:\s*(?::|=|\b(?:ist|is|lautet)\b))?\s+"
    r"(?=[A-Za-z0-9_-]{4,16}\b)(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{4,16}\b",
    re.IGNORECASE,
)
SOURCE_EXPLICIT_SECRET = re.compile(
    r"\b(?:password|passwort|passwd|secret|token|api[ _-]?key|access[ _-]?key|"
    r"private[ _-]?key|pin|passcode|door[ _-]?code|türcode|alarmcode)\b"
    r"\s*(?::|=|\b(?:ist|is|lautet)\b)\s*[^\s,;]{4,}",
    re.IGNORECASE,
)
SOURCE_MARKDOWN_CHARACTER = re.compile(r"([\\`*_{}\[\]()#+!~-])")

STATE_LABELS = {
    "on": "eingeschaltet",
    "off": "ausgeschaltet",
    "home": "zu Hause",
    "not_home": "nicht zu Hause",
    "open": "offen",
    "closed": "geschlossen",
    "unavailable": "nicht erreichbar",
    "unknown": "unbekannt",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def read_yaml(path: Path, default: Any) -> Any:
    if not path.exists() or path.stat().st_size == 0:
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def merge_documentation_overrides(
    generated: dict[str, Any], manual: dict[str, Any]
) -> dict[str, Any]:
    """Merge generated wording with reviewed data taking precedence.

    The AI file is deliberately limited to automation wording.  Other sections
    are copied only from the manually reviewed file so a generated response can
    never move devices, change status flags or alter metadata.
    """
    result = dict(manual)
    generated_automations = generated.get("automation_overrides", {})
    manual_automations = manual.get("automation_overrides", {})
    if not isinstance(generated_automations, dict):
        generated_automations = {}
    if not isinstance(manual_automations, dict):
        manual_automations = {}

    allowed_generated_fields = {
        "description",
        "trigger_steps",
        "condition_steps",
        "action_steps",
        "manual",
        "safety_note",
    }
    merged_automations: dict[str, Any] = {}
    for alias, value in generated_automations.items():
        if not isinstance(alias, str) or not isinstance(value, dict):
            continue
        merged_automations[alias] = {
            key: item for key, item in value.items() if key in allowed_generated_fields
        }
    for alias, value in manual_automations.items():
        if not isinstance(alias, str) or not isinstance(value, dict):
            continue
        merged_automations[alias] = {
            **merged_automations.get(alias, {}),
            **value,
        }
    result["automation_overrides"] = merged_automations
    return result


def slugify(value: str) -> str:
    value = (
        value.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
    )
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "ohne-namen"


def esc(value: Any) -> str:
    return str(value if value not in (None, "") else "–").replace("|", "\\|").replace("\n", " ")


def safe_source_text(value: Any, field: str) -> str:
    """Render backup/registry text as inert Markdown without exposing secrets.

    `field` is always a fixed local label and deliberately the only source detail
    included in an error.  The rejected value must never reach logs or status
    notifications.
    """
    raw = str(value if value not in (None, "") else "–")
    text = unicodedata.normalize("NFKC", raw)
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Zl", "Zp"}
        and character not in "\r\n\t"
        for character in text
    ):
        raise RuntimeError(
            f"Ein Home-Assistant-Text enthält unzulässige Steuerzeichen ({field})."
        )
    text = re.sub(r"[\r\n\t]+", " ", text).strip() or "–"
    if (
        any(pattern.search(text) for pattern in SECRET_VALUE_PATTERNS)
        or SOURCE_LABELED_SECRET.search(text)
        or SOURCE_EXPLICIT_SECRET.search(text)
    ):
        raise RuntimeError(
            f"Ein Home-Assistant-Text enthält ein geheimnisähnliches Muster ({field})."
        )

    # Links, templates, opaque identifiers and PIN-like numbers are useful
    # neither to a family reader nor to the static site.  Replace them visibly
    # before escaping every remaining Markdown/HTML control character.
    text = SOURCE_URL_PATTERN.sub("[geschützter Link]", text)
    text = SOURCE_TEMPLATE_PATTERN.sub("[geschützte Vorlage]", text)
    text = OPAQUE_VALUE.sub("[geschützter Wert]", text)
    text = SHORT_PRIVATE_NUMBER.sub("[geschützte Zahl]", text)
    # Values are inserted as Markdown text, never as an HTML attribute.  Keeping
    # quotes literal avoids numeric HTML entities whose `#` would be escaped next.
    text = html.escape(text, quote=False)
    return SOURCE_MARKDOWN_CHARACTER.sub(r"\\\1", text)


def safe_source_scalar(value: Any, field: str) -> str:
    """Render numeric HA settings literally and textual settings as protected text."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return safe_source_text(value, field)


def listify(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def duration(value: Any) -> str:
    if isinstance(value, dict):
        parts = []
        for key, label in (("hours", "Std."), ("minutes", "Min."), ("seconds", "Sek.")):
            if value.get(key):
                shown_value = safe_source_scalar(value[key], "Dauer")
                parts.append(f"{shown_value} {label}")
        return " ".join(parts) or "festgelegte Dauer"
    return safe_source_scalar(value, "Dauer")


def category(alias: str) -> str:
    name = alias.casefold()
    rules = [
        ("Energie & Auto", ("wallbox", "tibber", "laden", "batterie")),
        ("Garten & Wasser", ("wasser", "bewässer", "pflanze", "garten")),
        ("Haushalt", ("waschmaschine", "spülmaschine", "trockner", "müll")),
        ("System", ("system", "recorder", "reload", "timer")),
        ("Sicherheit & Zugang", ("rauch", "fenster", "tür öffnen", "benachrichtigung")),
        ("Licht & Präsenz", ("licht", "präsenz", "türkontakt")),
    ]
    return next((group for group, words in rules if any(word in name for word in words)), "Sonstiges")


def state_label(value: Any) -> str:
    raw = str(value)
    return STATE_LABELS.get(
        raw, safe_source_text(raw.replace("_", " "), "Zustandsbezeichnung")
    )


def sentence_case(value: Any) -> str:
    text = str(value).strip()
    return text[:1].upper() + text[1:] if text else text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("docs", type=Path)
    parser.add_argument(
        "--overrides",
        type=Path,
        default=Path(__file__).with_name("wiki_overrides.yaml"),
        help="Dauerhafte, geprüfte Ergänzungen zur Backup-Auswertung.",
    )
    parser.add_argument(
        "--ai-overrides",
        type=Path,
        help="Automatisch erzeugte Formulierungen; geprüfte Overrides haben Vorrang.",
    )
    parser.add_argument(
        "--inventory-source-date",
        help="Datum des automatisch gewählten Backups (nur Inventarstichtag).",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    docs = args.docs.resolve()
    if not source.is_dir() or not docs.is_dir():
        raise SystemExit("Quell- oder Dokumentationsordner fehlt.")

    manual_overrides = read_yaml(args.overrides.resolve(), {})
    generated_overrides = (
        read_yaml(args.ai_overrides.resolve(), {}) if args.ai_overrides else {}
    )
    overrides = merge_documentation_overrides(generated_overrides, manual_overrides)
    automation_overrides = overrides.get("automation_overrides", {})
    device_area_overrides = overrides.get("device_area_overrides", {})
    entity_area_overrides = overrides.get("entity_area_overrides", {})
    device_name_overrides = overrides.get("device_name_overrides", {})
    scene_overrides = overrides.get("scene_overrides", {})
    force_include_devices = set(overrides.get("force_include_devices", []))
    metadata = overrides.get("metadata", {})
    source_date = str(
        args.inventory_source_date
        or metadata.get("inventory_source_date")
        or "nicht dokumentiert"
    )
    checked_on = str(metadata.get("live_checked_date") or source_date)

    storage = source / ".storage"
    floors = read_json(storage / "core.floor_registry").get("floors", [])
    areas = read_json(storage / "core.area_registry").get("areas", [])
    labels = read_json(storage / "core.label_registry").get("labels", [])
    devices = read_json(storage / "core.device_registry").get("devices", [])
    entities = read_json(storage / "core.entity_registry").get("entities", [])
    automations = read_yaml(source / "automations.yaml", [])
    scenes = read_yaml(source / "scenes.yaml", [])

    floor_by_id = {item["floor_id"]: item for item in floors}
    area_by_id = {item["id"]: item for item in areas}
    device_by_id = {item["id"]: item for item in devices}
    entity_by_id = {item["entity_id"]: item for item in entities}
    entity_by_registry_id = {item["id"]: item for item in entities}
    device_entities: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entity in entities:
        if entity.get("device_id"):
            device_entities[entity["device_id"]].append(entity)

    everyday_entities = [
        entity for entity in entities
        if not entity.get("disabled_by")
        and entity.get("entity_category") not in ("diagnostic", "config")
    ]
    everyday_entity_registry_ids = {entity["id"] for entity in everyday_entities}

    def raw_device_name(device: dict[str, Any]) -> str:
        return device.get("name_by_user") or device.get("name") or "Unbekanntes Gerät"

    def area_id_for_device(device: dict[str, Any]) -> str | None:
        return device_area_overrides.get(raw_device_name(device)) or device.get("area_id")

    def area_id_for_entity(entity: dict[str, Any]) -> str | None:
        return (
            entity_area_overrides.get(entity.get("entity_id"))
            or entity.get("area_id")
            or area_id_for_device(device_by_id.get(entity.get("device_id"), {}))
        )

    def shown_floor_name(value: str | None) -> str:
        if value == "Ergeschoss":
            value = "Erdgeschoss"
        if value == "Draussen":
            value = "Außenbereich"
        return safe_source_text(value or "Keine Etage zugeordnet", "Etagenname")

    def area_location(area_id: str) -> str:
        area = area_by_id.get(area_id, {})
        floor = floor_by_id.get(area.get("floor_id") or "", {})
        area_name = safe_source_text(area.get("name", area_id), "Raumname")
        return f"{area_name} · {shown_floor_name(floor.get('name'))}"

    def friendly_device_name(device: dict[str, Any]) -> str:
        raw = raw_device_name(device).strip()
        raw = device_name_overrides.get(raw, raw)
        area = area_by_id.get(area_id_for_device(device) or "", {}).get("name")
        if area and raw.casefold().endswith(f" - {area}".casefold()):
            raw = raw[: -(len(area) + 3)].strip()
        combined = f"{raw} {device.get('manufacturer') or ''} {device.get('model') or ''}".casefold()
        if raw == "Büro" and "apple tv" in combined:
            return "Apple TV Büro"
        if raw == "Wohnzimmer" and "apple tv" in combined:
            return "Apple TV Wohnzimmer"
        if raw == "Büro" and ("sonos" in str(device.get("manufacturer") or "").casefold() or "era 100" in combined):
            return "Sonos Büro"
        if "tibber" in combined and ("pulse" in combined or "bridge" in combined):
            if "local" in combined:
                return "Tibber-Stromzähler (technische Verbindung)"
            return "Tibber-Stromzähler"
        if "tibber" in combined and re.search(r"\s\d+[a-z]?\s*$", raw, re.I):
            return "Tibber-Stromtarif"
        if "wallbox" in combined or "go-echarger" in combined:
            return "Wallbox (go-e)"
        if raw == "Max' Fire":
            return "Dashboard-Tablet"
        return raw

    def shown_device_name(device: dict[str, Any]) -> str:
        raw_name = raw_device_name(device).strip()
        shown_name = friendly_device_name(device)
        if raw_name in device_name_overrides:
            return shown_name
        return safe_source_text(shown_name, "Gerätename")

    def device_name(device_id: str | None) -> str:
        return shown_device_name(device_by_id.get(device_id or "", {}))

    def entity_label(entity_id: str, technical: bool = False) -> str:
        entity = entity_by_id.get(entity_id, {})
        label = entity.get("name") or entity.get("original_name")
        if not label:
            label = entity_id.split(".", 1)[-1].replace("_", " ").capitalize()
        shown_label = safe_source_text(label, "Entity-Name")
        return f"{shown_label} (`{entity_id}`)" if technical else shown_label

    def names_for(value: Any, technical: bool = False) -> str:
        result = []
        for item in listify(value):
            if isinstance(item, str) and item in entity_by_id:
                result.append(entity_label(item, technical))
            elif isinstance(item, str) and item in entity_by_registry_id:
                result.append(entity_label(entity_by_registry_id[item]["entity_id"], technical))
            elif isinstance(item, str) and item in device_by_id:
                result.append(device_name(item))
            elif isinstance(item, str) and item in area_by_id:
                result.append(safe_source_text(area_by_id[item]["name"], "Raumname"))
            elif isinstance(item, str):
                result.append(safe_source_text(item.replace("_", " "), "Bezeichnung"))
            else:
                result.append(safe_source_text(item, "Bezeichnung"))
        return ", ".join(result) or "das betroffene Gerät"

    def device_platforms(device: dict[str, Any]) -> set[str]:
        return {
            str(entity.get("platform")) for entity in device_entities.get(device.get("id"), [])
            if entity.get("platform")
        }

    def is_virtual_device(device: dict[str, Any]) -> bool:
        name = raw_device_name(device).strip()
        friendly = friendly_device_name(device)
        model = str(device.get("model") or "").casefold()
        maker = str(device.get("manufacturer") or "").casefold()
        platforms = device_platforms(device)
        if device.get("entry_type") == "service":
            return True
        if re.fullmatch(r"0x[0-9a-f]+", name.casefold()):
            return True
        if "@" in name or re.search(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", name, re.I):
            return True
        if model in {"group", "plugin", "integration", "theme", "home assistant app", "homebridge"}:
            return True
        if "speaker group" in model or "grocery shopping list" in model:
            return True
        if name.casefold().startswith("shelly") and " output " in name.casefold():
            return True
        if friendly in {"Tibber-Stromtarif", "Tibber-Stromzähler (technische Verbindung)"}:
            return True
        if name in {"Nuki Web API", "Withings", "Robotic Vacuum Cleaner"}:
            return True
        if maker == "amazon" and model == "sonos":
            return True
        if name == "Max' Echo Dot" and device.get("area_id") == "wohnzimmer" and model == "echo dot with clock":
            return True
        if device.get("via_device_id") and any(word in name.casefold() for word in ("output", "ams", "spool")):
            return True
        if name in {"Zigbee2MQTT Bridge", "HASS Bridge:21064", "NAS", "This Device", "Überall"}:
            return True
        if maker in {"home assistant", "hacs.xyz"} and platforms & {"hassio", "hacs", "homekit"}:
            return True
        if platforms and platforms <= {
            "hassio", "hacs", "sun", "met", "openweathermap", "systemmonitor",
            "ping", "backup", "bring", "openai_conversation",
            "google_generative_ai_conversation", "web_id", "smtp", "telegram_bot",
        }:
            return True
        return False

    def has_everyday_entity(device: dict[str, Any]) -> bool:
        return any(
            entity.get("id") in everyday_entity_registry_ids
            for entity in device_entities.get(device.get("id"), [])
        )

    def is_mobile_device(device: dict[str, Any]) -> bool:
        text = " ".join(str(x or "") for x in (
            friendly_device_name(device), device.get("manufacturer"), device.get("model")
        )).casefold()
        if device_platforms(device) & {"mobile_app", "icloud", "pycupra"}:
            return True
        return any(word in text for word in (
            "iphone", "ipad", "macbook", "watch", "born", "cupra", "bus", "quietcomfort", "headphone"
        ))

    def device_kind(device: dict[str, Any]) -> str:
        if friendly_device_name(device).casefold() == "pc":
            return "Computer"
        text = " ".join(
            str(x or "") for x in (
                friendly_device_name(device), device.get("manufacturer"), device.get("model")
            )
        ).casefold()
        rules = [
            ("Bedien-Tablet", ("dashboard-tablet", "dashboard tablet")),
            ("Klimaanlagen-Schalter", ("klimaanlage schalter",)),
            ("Heizgerät", ("heizstrahler",)),
            ("Kaffeemaschine", ("kaffeemaschine",)),
            ("Rauchmelder", ("rauch", "smoke")),
            ("Tür-/Fensterkontakt", ("fensterkontakt", "türkontakt", "contact sensor", "door/window")),
            ("Türschloss / Türöffner", ("nuki-türschloss", "nuki-türöffner")),
            ("Präsenzmelder", ("präsenz", "presence sensor", "human presence")),
            ("Temperatur-/Feuchtesensor", ("temperatur", "temperature", "humidity")),
            ("Stromzähler / Energiemesser", ("strommesser", "stromzähler", "power meter")),
            ("Wandschalter / Taster", ("wandschalter", "shortcut", "smart knob", "drehknopf", "switch mini")),
            ("Smarte Steckdose", ("steckdose", "smart plug")),
            ("Wasserventil", ("wasserventil", "water valve")),
            ("Wallbox", ("wallbox", "go-echarger")),
            ("Mähroboter", ("mähroboter", "mower")),
            ("Saug-/Wischgerät", ("sauron", "vacuum", "dyad", "roborock")),
            ("Fernseher / Mediaplayer", ("fernseher", "television", "apple tv", "fire tv", "65oled")),
            ("Licht", ("licht", "lichstäbchen", "light", "hue", "filament", "lampe", "laterne", "panel", "spot", "decke", "wled")),
            ("Lautsprecher / Sprachassistent", ("echo", "dot", "sonos", "alexa")),
            ("Waage", ("body+", "waage")),
            ("Luftreiniger", ("luftreiniger", "air purifier")),
            ("3D-Drucker", ("x1c", "3d drucker")),
        ]
        return next((label for label, words in rules if any(word in text for word in words)), "Smart-Home-Gerät")

    def position_hint(device: dict[str, Any]) -> str:
        text = friendly_device_name(device).casefold()
        hints = [
            (("fensterkontakt",), "am Fenster (aus Gerätename abgeleitet)"),
            (("türkontakt",), "an der Tür (aus Gerätename abgeleitet)"),
            (("fensterbank",), "auf/an der Fensterbank (aus Gerätename abgeleitet)"),
            (("esstisch",), "am Esstisch (aus Gerätename abgeleitet)"),
            (("haustür", "haustuere"), "an der Haustür (aus Gerätename abgeleitet)"),
            (("waschmaschine",), "direkt an der Waschmaschine (aus Gerätename abgeleitet)"),
            (("trockner",), "direkt am Trockner (aus Gerätename abgeleitet)"),
            (("kühlschrank",), "direkt am Kühlschrank (aus Gerätename abgeleitet)"),
            (("spülmaschine",), "direkt an der Spülmaschine (aus Gerätename abgeleitet)"),
            (("decke", "deckenlicht", "panel"), "an der Decke (aus Gerätename abgeleitet)"),
            (("sonos links",), "links beim Sonos (aus Gerätename abgeleitet)"),
            (("sonos rechts",), "rechts beim Sonos (aus Gerätename abgeleitet)"),
            (("strommesser", "tibber-stromzähler"), "am Stromzähler/Verteiler (aus Funktion abgeleitet)"),
        ]
        return next((hint for words, hint in hints if any(word in text for word in words)), "genaue Position nicht hinterlegt")

    def outage_hint(device: dict[str, Any]) -> str:
        kind = device_kind(device)
        if kind == "Licht":
            return "normalen Schalter verwenden, falls vorhanden"
        if kind == "Smarte Steckdose":
            return "Taste an der Steckdose prüfen; Gerät nicht zurücksetzen"
        if kind in {"Fernseher / Mediaplayer", "Lautsprecher / Sprachassistent", "Luftreiniger", "3D-Drucker", "Saug-/Wischgerät", "Mähroboter"}:
            return "direkt am Gerät bzw. mit Fernbedienung/App bedienen"
        if kind in {"Rauchmelder", "Tür-/Fensterkontakt", "Präsenzmelder", "Temperatur-/Feuchtesensor"}:
            return "keine Bedienung; Meldungen können ausbleiben"
        if kind == "Wallbox":
            return "Anzeige an Wallbox/Fahrzeug prüfen"
        if kind == "Wasserventil":
            return "Ventil vor Ort prüfen und sicher schließen"
        return "direkte Bedienung am Gerät prüfen; nicht zurücksetzen"

    def dedupe_devices(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for device in sorted(items, key=lambda x: friendly_device_name(x).casefold()):
            if is_virtual_device(device):
                continue
            key = friendly_device_name(device).casefold().strip()
            result.setdefault(key, device)
        return list(result.values())

    def trigger_summary(item: dict[str, Any]) -> str:
        kind = item.get("trigger") or item.get("platform") or "unbekannt"
        raw_target = item.get("entity_id") or item.get("device_id")
        if not raw_target and isinstance(item.get("target"), dict):
            raw_target = item["target"].get("entity_id") or item["target"].get("device_id") or item["target"].get("area_id")
        target = names_for(raw_target)
        if kind == "state":
            change = []
            if item.get("from") is not None:
                change.append(f"von „{state_label(item['from'])}“")
            if item.get("to") is not None:
                change.append(f"auf „{state_label(item['to'])}“")
            hold = f" und bleibt dort {duration(item['for'])}" if item.get("for") else ""
            return f"{target} wechselt {' '.join(change)}{hold}".strip()
        if kind == "numeric_state":
            limits = []
            if item.get("above") is not None:
                limits.append(
                    f"über {safe_source_scalar(item['above'], 'Grenzwertbezeichnung')}"
                )
            if item.get("below") is not None:
                limits.append(
                    f"unter {safe_source_scalar(item['below'], 'Grenzwertbezeichnung')}"
                )
            return f"der Messwert von {target} liegt {' und '.join(limits)}"
        if kind == "time":
            return f"es ist {names_for(item.get('at'))} Uhr"
        if kind == "time_pattern":
            return "das festgelegte Zeitintervall ist erreicht"
        if kind == "sun":
            return "Sonnenaufgang oder Sonnenuntergang ist erreicht"
        if kind == "device":
            event_type = safe_source_text(
                str(item.get("type", "Ereignis")).replace("_", " "),
                "Ereignisbezeichnung",
            )
            if event_type.casefold() == "action":
                return f"eine Taste am {target} wird gedrückt"
            return f"{target} meldet „{event_type}“"
        if kind == "event":
            return "Home Assistant erkennt den passenden Bedienbefehl"
        if kind == "mqtt":
            return f"{target} wird betätigt oder meldet eine Änderung"
        if kind == "template":
            return "die festgelegte interne Prüfung trifft zu"
        semantic = {
            "occupancy.detected": "Anwesenheit wird erkannt",
            "occupancy.cleared": "keine Anwesenheit wird mehr erkannt",
            "motion.detected": "Bewegung wird erkannt",
            "motion.cleared": "keine Bewegung wird mehr erkannt",
        }
        if kind in semantic:
            return f"{semantic[kind]} bei {target}"
        return f"{target} meldet das passende Ereignis"

    def condition_summary(item: dict[str, Any]) -> str:
        kind = item.get("condition", "unbekannt")
        target = names_for(item.get("entity_id") or item.get("device_id"))
        if kind == "state":
            return f"{target} ist „{state_label(item.get('state', 'festgelegt'))}“"
        if kind == "numeric_state":
            limits = []
            if item.get("above") is not None:
                limits.append(
                    f"über {safe_source_scalar(item['above'], 'Grenzwertbezeichnung')}"
                )
            if item.get("below") is not None:
                limits.append(
                    f"unter {safe_source_scalar(item['below'], 'Grenzwertbezeichnung')}"
                )
            return f"{target} liegt {' und '.join(limits)}"
        if kind == "time":
            return "der festgelegte Zeitraum ist aktiv"
        if kind == "sun":
            return "der passende Sonnenstand ist erreicht"
        if kind == "template":
            return "Home Assistant prüft zusätzliche interne Voraussetzungen"
        if kind in ("and", "or", "not"):
            return "die zusammengefassten Voraussetzungen treffen zu"
        return "die in Home Assistant hinterlegte Voraussetzung trifft zu"

    def target_summary(item: dict[str, Any]) -> str:
        target = item.get("target") or {}
        parts = []
        for key in ("entity_id", "device_id", "area_id"):
            if target.get(key):
                parts.append(names_for(target[key]))
        if item.get("entity_id"):
            parts.append(names_for(item["entity_id"]))
        if item.get("device_id"):
            parts.append(names_for(item["device_id"]))
        return ", ".join(dict.fromkeys(parts)) or "das betroffene Gerät"

    def action_summary(item: dict[str, Any]) -> str:
        service = item.get("action") or item.get("service")
        if service:
            service = str(service)
            if service.startswith("notify.mobile_app_"):
                recipient = service.removeprefix("notify.mobile_app_").replace("_", " ")
                recipient = {"max iphone": "Max' iPhone", "meikes iphone": "Meikes iPhone"}.get(recipient, recipient)
                shown_recipient = safe_source_text(recipient, "Empfängerbezeichnung")
                return f"Push-Nachricht an {shown_recipient} senden"
            exact = {
                "lock.open": "den Nuki-Öffner öffnen",
                "recorder.purge": "die Home-Assistant-Datenbank warten",
                "homeassistant.update_entity": "die zugehörigen Daten aktualisieren",
                "input_number.set_value": "einen internen Startwert speichern",
                "button.press": "die hinterlegte Gerätefunktion auslösen",
            }
            if service in exact:
                return exact[service]
            readable = {
                "turn_on": "einschalten",
                "turn_off": "ausschalten",
                "toggle": "umschalten",
                "open_cover": "öffnen",
                "close_cover": "schließen",
                "open": "öffnen",
                "notify": "benachrichtigen",
                "set_value": "auf den berechneten Wert setzen",
            }
            verb = readable.get(service.split(".")[-1], "die hinterlegte Funktion ausführen")
            addition = ""
            data = item.get("data") or {}
            if data.get("brightness_pct") is not None:
                brightness = safe_source_scalar(
                    data["brightness_pct"], "Helligkeitswert"
                )
                addition = f" mit {brightness} % Helligkeit"
            return f"{target_summary(item)} {verb}{addition}"
        if "delay" in item:
            return f"{duration(item['delay'])} warten"
        if "choose" in item:
            return "je nach aktuellem Zustand die passende Ablaufvariante wählen"
        if "if" in item:
            checks = [condition_summary(x) for x in listify(item.get("if")) if isinstance(x, dict)]
            then_steps = [action_summary(x) for x in listify(item.get("then")) if isinstance(x, dict) and x.get("enabled", True)]
            else_steps = [action_summary(x) for x in listify(item.get("else")) if isinstance(x, dict) and x.get("enabled", True)]
            text = f"wenn {checks[0].lower() if checks else 'die Voraussetzung zutrifft'}, dann {then_steps[0].lower() if then_steps else 'keinen weiteren Schritt ausführen'}"
            if else_steps:
                text += f"; andernfalls {else_steps[0].lower()}"
            return text
        if "repeat" in item:
            return "die vorgesehenen Schritte für alle betroffenen Geräte ausführen"
        if "wait_template" in item or "wait_for_trigger" in item:
            return "auf die nächste festgelegte Änderung warten"
        if "device_id" in item:
            return f"die hinterlegte Gerätefunktion bei {device_name(item.get('device_id'))} ausführen"
        return "einen internen Verarbeitungsschritt ausführen"

    def referenced_ids(value: Any) -> tuple[set[str], set[str], set[str]]:
        entity_ids: set[str] = set()
        device_ids: set[str] = set()
        area_ids: set[str] = set()

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for key, val in node.items():
                    if key == "device_id":
                        device_ids.update(str(x) for x in listify(val))
                    elif key == "entity_id":
                        entity_ids.update(str(x) for x in listify(val))
                    elif key == "area_id":
                        area_ids.update(str(x) for x in listify(val))
                    walk(val)
            elif isinstance(node, list):
                for child in node:
                    walk(child)
            elif isinstance(node, str):
                entity_ids.update(ENTITY_RE.findall(node))

        walk(value)
        translated = {
            entity_by_registry_id[x]["entity_id"] if x in entity_by_registry_id else x
            for x in entity_ids
        }
        return (
            translated.intersection(entity_by_id),
            device_ids.intersection(device_by_id),
            area_ids.intersection(area_by_id),
        )

    def automation_manual(alias: str, group: str, override: dict[str, Any]) -> str:
        if override.get("manual"):
            return str(override["manual"])
        alias_lower = alias.casefold()
        if "licht" in alias_lower:
            return "Das betroffene Licht in Home Assistant oder am vorhandenen Wandschalter direkt bedienen. Reagiert es unerwartet, nicht zurücksetzen, sondern Max informieren."
        if "batterie" in alias_lower:
            return "Das genannte Gerät aufsuchen und Batterie beziehungsweise Ladezustand direkt prüfen."
        if "müll" in alias_lower:
            return "Den Abfuhrtermin unabhängig von der Meldung prüfen."
        if "pflanzenerinnerung" in alias_lower:
            return "Die Pflanzen bei Bedarf gießen und die Erinnerung in der Handy-Meldung als erledigt bestätigen."
        if group == "Licht & Präsenz":
            return "Das betroffene Licht in Home Assistant oder am vorhandenen Wandschalter direkt bedienen. Reagiert es unerwartet, nicht zurücksetzen, sondern Max informieren."
        if group == "Sicherheit & Zugang":
            return "Zuerst die reale Situation vor Ort prüfen. Türen und Fenster von Hand sichern; eine App-Meldung ersetzt keine unmittelbare Sicherheitsmaßnahme."
        if group == "Garten & Wasser":
            return "Die betroffene Funktion in Home Assistant direkt bedienen. Bei Wasser immer vor Ort prüfen, ob das Ventil anschließend wirklich geschlossen ist."
        if group == "Haushalt":
            return "Das Haushaltsgerät selbst funktioniert weiter. Status und Programmende direkt am Gerät prüfen."
        if group == "Energie & Auto":
            return "Ladezustand und Freigabe zusätzlich am Fahrzeug beziehungsweise an der Wallbox kontrollieren."
        if group == "System":
            return "Keine Bedienung im Alltag. Diese Funktion ist ausschließlich für die technische Wartung durch Max gedacht."
        return "Die betroffene Funktion direkt am Gerät oder in Home Assistant prüfen. Nichts löschen oder auf Werkseinstellungen zurücksetzen."

    auto_dir = docs / "automationen" / "generated"
    room_dir = docs / "raeume" / "generated"
    for section in ("automationen", "raeume", "geraete"):
        (docs / section).mkdir(parents=True, exist_ok=True)
    for directory in (auto_dir, room_dir):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)

    slug_counts: Counter[str] = Counter()
    auto_meta: list[dict[str, Any]] = []
    for automation in automations:
        alias = str(automation.get("alias") or "Automation ohne Namen")
        shown_alias = safe_source_text(alias, "Automationsname")
        override = automation_overrides.get(alias, {}) or {}
        title = override.get("title") or shown_alias
        base_slug = slugify(shown_alias)
        slug_counts[base_slug] += 1
        slug = base_slug if slug_counts[base_slug] == 1 else f"{base_slug}-{slug_counts[base_slug]}"
        group = category(alias)
        enabled = override.get("enabled", True)
        technical = bool(override.get("technical", group == "System"))
        triggers = listify(automation.get("triggers") or automation.get("trigger"))
        conditions = listify(automation.get("conditions") or automation.get("condition"))
        actions = [x for x in listify(automation.get("actions") or automation.get("action")) if not isinstance(x, dict) or x.get("enabled", True)]
        entity_ids, device_ids, direct_area_ids = referenced_ids(automation)
        area_ids = set(direct_area_ids)
        area_ids.update(
            area_id for entity_id in entity_ids
            if (area_id := area_id_for_entity(entity_by_id.get(entity_id, {})))
        )
        area_ids.update(
            area_id for device_id in device_ids
            if (area_id := area_id_for_device(device_by_id.get(device_id, {})))
        )
        if "area_ids" in override:
            area_ids = {
                str(area_id) for area_id in override.get("area_ids", [])
                if str(area_id) in area_by_id
            }
        locations = [area_location(x) for x in sorted(area_ids, key=lambda x: area_location(x).casefold())]
        location_text = ", ".join(locations) if locations else "kein fester Raum – betrifft das ganze Haus"
        blueprint = automation.get("use_blueprint")
        trigger_lines = [trigger_summary(x) for x in triggers if isinstance(x, dict)]
        condition_lines = [condition_summary(x) for x in conditions if isinstance(x, dict)]
        action_lines = [action_summary(x) for x in actions if isinstance(x, dict)]
        if blueprint:
            trigger_lines = ["Home Assistant erkennt anhand des Stromverbrauchs oder Gerätezustands, dass der Ablauf beendet ist"]
            action_lines = ["die im Namen und in der Kurzbeschreibung genannte Meldung oder Aktion ausführen"]
        if "trigger_steps" in override:
            trigger_lines = [str(x) for x in override.get("trigger_steps", [])]
        if "condition_steps" in override:
            condition_lines = [str(x) for x in override.get("condition_steps", [])]
        if "action_steps" in override:
            action_lines = [str(x) for x in override.get("action_steps", [])]
        action_lines.extend(str(x) for x in override.get("result_append", []))

        description = override.get("description")
        if not description and automation.get("description"):
            description = safe_source_text(
                automation["description"], "Automationsbeschreibung"
            )
        if not description and trigger_lines and action_lines:
            description = f"Wenn {trigger_lines[0].lower()}, wird anschließend {action_lines[0].lower()}."
        if not description:
            description = "Diese Funktion führt den in Home Assistant hinterlegten Ablauf aus."

        page = []
        if technical or not enabled:
            page.append("---\nsearch:\n  exclude: true\n---\n\n")
        page.extend([GENERATED_NOTICE, f"# {title}\n\n"])
        if not enabled:
            reason = override.get("status_reason") or "Diese Automation ist derzeit ausgeschaltet."
            page.append(f"!!! info \"Status: ausgeschaltet\"\n    {reason}\n\n")
        else:
            page.append("!!! success \"Status: aktiv\"\n    Diese Automation ist in Home Assistant eingeschaltet.\n\n")
        if override.get("safety_note"):
            page.append(f"!!! warning \"Wichtig\"\n    {override['safety_note']}\n\n")
        page.append(f"**Ort:** {location_text}\n\n")
        page.append("## Das bemerkst du im Alltag\n\n")
        page.append(f"{description}\n\n")
        page.append("## Sie startet, wenn …\n\n")
        page.extend(f"{i}. {sentence_case(text)}\n" for i, text in enumerate(trigger_lines or ["Home Assistant den hinterlegten Auslöser erkennt"], 1))
        page.append("\n## Sie läuft nur weiter, wenn …\n\n")
        if condition_lines:
            page.extend(f"- {sentence_case(text)}\n" for text in condition_lines)
        else:
            page.append("Keine weitere Voraussetzung ist hinterlegt.\n")
        page.append("\n## Dann passiert …\n\n")
        page.extend(f"{i}. {sentence_case(text)}\n" for i, text in enumerate(action_lines or ["Home Assistant führt die hinterlegte Aktion aus"], 1))
        page.append("\n## So kannst du reagieren\n\n")
        page.append(automation_manual(alias, group, override) + "\n\n")
        page.append("<div data-search-exclude markdown>\n\n")
        page.append("??? info \"Technik für Max\"\n\n")
        page.append("    | Feld | Wert |\n    |---|---|\n")
        page.append(f"    | Ursprünglicher Name | {esc(shown_alias)} |\n")
        page.append(
            "    | Home-Assistant-ID | "
            f"{esc(safe_source_text(automation.get('id'), 'Automations-ID'))} |\n"
        )
        page.append(
            "    | Modus | "
            f"{esc(safe_source_text(automation.get('mode', 'single'), 'Automationsmodus'))} |\n"
        )
        page.append(f"    | Kategorie | {group} |\n")
        if entity_ids:
            technical_entities = ", ".join(entity_label(x, True) for x in sorted(entity_ids)[:30])
            page.append(f"    | Verwendete Entities | {technical_entities} |\n")
        if blueprint:
            blueprint_path = safe_source_text(
                blueprint.get("path", "nicht angegeben"), "Blueprint-Pfad"
            )
            page.append(f"    | Blueprint | {esc(blueprint_path)} |\n")
        page.append("\n</div>\n\n")
        page.append(f"<p class=\"page-status\">Definition aus Backup vom {source_date}; Status und dauerhafte Ergänzungen geprüft am {checked_on}</p>\n")
        (auto_dir / f"{slug}.md").write_text("".join(page), encoding="utf-8")
        auto_meta.append({
            "alias": alias,
            "title": title,
            "slug": slug,
            "category": group,
            "entities": entity_ids,
            "devices": device_ids,
            "areas": area_ids,
            "locations": location_text,
            "description": str(description).strip(),
            "enabled": enabled,
            "technical": technical,
            "status_reason": override.get("status_reason", ""),
        })

    categories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in auto_meta:
        if item["enabled"] and not item["technical"]:
            categories[item["category"]].append(item)
    auto_index = [GENERATED_NOTICE, "# Was passiert automatisch?\n\n"]
    auto_index.append("Hier stehen nur Funktionen, die im Alltag sichtbar oder wichtig sind. Dazu gehören automatische Abläufe **und die in Home Assistant hinterlegten Tastenbelegungen**. Interne Wartungsabläufe und ausgeschaltete Tests sind weiter unten getrennt aufgeführt.\n\n")
    auto_index.append("!!! tip \"So liest du die Seiten\"\n    Jede Seite beginnt mit Status, Ort und einer Alltagserklärung. Technische Namen sind eingeklappt und werden nur für die Wartung benötigt.\n\n")
    order = ["Sicherheit & Zugang", "Licht & Präsenz", "Haushalt", "Garten & Wasser", "Energie & Auto", "Sonstiges"]
    for group in order:
        if group not in categories:
            continue
        auto_index.append(f"## {group}\n\n")
        auto_index.append("| Funktion | Ort | Worum geht es? |\n|---|---|---|\n")
        for item in sorted(categories[group], key=lambda x: x["title"].casefold()):
            short = re.sub(r"\s+", " ", item["description"])
            if len(short) > 150:
                short = short[:147].rstrip() + "…"
            auto_index.append(f"| [{esc(item['title'])}](generated/{item['slug']}.md) | {esc(item['locations'])} | {esc(short)} |\n")
        auto_index.append("\n")

    inactive = [x for x in auto_meta if not x["enabled"]]
    technical_items = [x for x in auto_meta if x["technical"] and x["enabled"]]
    if inactive:
        auto_index.append("??? info \"Ausgeschaltete Automationen\"\n\n")
        for item in sorted(inactive, key=lambda x: x["title"].casefold()):
            reason = item["status_reason"] or "derzeit ausgeschaltet"
            auto_index.append(f"    - [{item['title']}](generated/{item['slug']}.md) – {reason}\n")
        auto_index.append("\n")
    if technical_items:
        auto_index.append("??? info \"Technische Wartungsabläufe (nicht für den Alltag)\"\n\n")
        for item in sorted(technical_items, key=lambda x: x["title"].casefold()):
            auto_index.append(f"    - [{item['title']}](generated/{item['slug']}.md)\n")
        auto_index.append("\n")

    hidden_scenes = set(scene_overrides.get("hidden", []))
    shown_scenes = [scene for scene in scenes if scene.get("name") not in hidden_scenes]
    if shown_scenes:
        auto_index.append("## Szenen\n\n")
        auto_index.append("Eine Szene stellt mehrere Geräte gemeinsam auf gespeicherte Werte.\n\n")
        for scene in shown_scenes:
            name = str(scene.get("name") or "Szene ohne Namen")
            shown_name = safe_source_text(name, "Szenenname")
            count = scene_overrides.get("entity_counts", {}).get(name, len(scene.get("entities") or {}))
            description = scene_overrides.get("descriptions", {}).get(name, f"Verändert {count} gespeicherte Zustände.")
            auto_index.append(f"- **{shown_name}:** {description}\n")
        auto_index.append("\n")
    auto_index.append(f"<p class=\"page-status\">Definitionen aus Backup vom {source_date}; Status und dauerhafte Ergänzungen geprüft am {checked_on}</p>\n")
    (docs / "automationen" / "index.md").write_text("".join(auto_index), encoding="utf-8")

    daily_automation_device_ids = {
        device_id
        for item in auto_meta if item["enabled"] and not item["technical"]
        for device_id in item["devices"]
    }
    area_all_devices: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for device in devices:
        if not is_mobile_device(device) and (
            has_everyday_entity(device)
            or device.get("id") in daily_automation_device_ids
            or raw_device_name(device) in force_include_devices
        ):
            area_all_devices[area_id_for_device(device)].append(device)
    area_devices = {
        area_id: dedupe_devices(items)
        for area_id, items in area_all_devices.items()
    }
    area_entities: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for entity in everyday_entities:
        area_entities[area_id_for_entity(entity)].append(entity)

    room_slug: dict[str, str] = {
        area["id"]: slugify(safe_source_text(area["name"], "Raumname"))
        for area in areas
    }
    for area in areas:
        area_id = area["id"]
        shown_area_name = safe_source_text(area["name"], "Raumname")
        floor = shown_floor_name(floor_by_id.get(area.get("floor_id") or "", {}).get("name"))
        room_devices = area_devices.get(area_id, [])
        related = [x for x in auto_meta if x["enabled"] and not x["technical"] and area_id in x["areas"]]
        page = [GENERATED_NOTICE, f"# {shown_area_name}\n\n"]
        page.append(f"**Standort:** {floor}\n\n**Alltagsrelevante Geräte:** {len(room_devices)}\n\n")
        if area["name"] == "Gästeklo":
            page.append("!!! note \"Abweichender Gerätename\"\n    Das sichtbare Licht trägt in Home Assistant „Gästebad“ im Namen. Gemeint ist nach aktueller Raumzuordnung das Gästeklo.\n\n")

        page.append("## Geräte an diesem Standort\n\n")
        if room_devices:
            page.append("| Gerät | Aufgabe | Raumzuordnung | Position / Standortshinweis | Bei Home-Assistant-Ausfall |\n|---|---|---|---|---|\n")
            for device in room_devices:
                assignment = "in Home Assistant bestätigt" if device.get("area_id") else "aus Name/Funktion abgeleitet"
                page.append(
                    f"| {esc(shown_device_name(device))} | {device_kind(device)} | {assignment} | "
                    f"{position_hint(device)} | {outage_hint(device)} |\n"
                )
        else:
            page.append("Für diesen Raum ist derzeit kein eigenständiges physisches Gerät eingetragen.\n")

        page.append("\n## Das passiert hier automatisch\n\n")
        if related:
            for item in sorted(related, key=lambda x: x["title"].casefold()):
                page.append(f"- [{item['title']}](../../automationen/generated/{item['slug']}.md)\n")
        else:
            page.append("Für diesen Raum ist keine aktive, alltagsrelevante Automation eindeutig zugeordnet.\n")

        page.append("\n## Bedienung und Störung\n\n")
        kinds = {device_kind(device) for device in room_devices}
        if "Licht" in kinds or "Wandschalter / Taster" in kinds:
            page.append("- Licht zuerst am vorhandenen Wandschalter oder direkt in Home Assistant bedienen.\n")
        if kinds & {"Rauchmelder", "Tür-/Fensterkontakt", "Präsenzmelder", "Temperatur-/Feuchtesensor"}:
            page.append("- Sensoren brauchen normalerweise keine Bedienung. Bei einem Ausfall können automatische Meldungen oder Schaltungen fehlen.\n")
        if "Smarte Steckdose" in kinds:
            page.append("- Smarte Steckdosen nicht auf Werkseinstellungen zurücksetzen. Bei Haushaltsgeräten das Programm direkt am Gerät prüfen.\n")
        page.append("- Wenn etwas unerwartet reagiert: Gerät nicht löschen oder zurücksetzen, Beobachtung notieren und Max informieren.\n")
        page.append(f"\n<p class=\"page-status\">Inventar aus Backup vom {source_date}; gekennzeichnete Ergänzungen geprüft am {checked_on}</p>\n")
        (room_dir / f"{room_slug[area_id]}.md").write_text("".join(page), encoding="utf-8")

    floor_areas: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for area in areas:
        floor_areas[area.get("floor_id")].append(area)
    room_index = [GENERATED_NOTICE, "# Räume und Standorte\n\n"]
    room_index.append("Die Raumseiten zeigen nur physische beziehungsweise im Alltag erkennbare Geräte. Interne Dienste, Plugins, Diagnosewerte und virtuelle Lichtgruppen werden ausgeblendet.\n\n")
    room_index.append("!!! info \"Was bedeutet Standort?\"\n    Räume und Etagen stammen aus Home Assistant. Einzelne Gerätezuordnungen sind als geprüfte oder aus Name/Funktion abgeleitete Ergänzung gekennzeichnet. Eine genauere Position wird nur genannt, wenn sie aus dem Gerätenamen sicher erkennbar ist; sonst steht ausdrücklich „nicht hinterlegt“.\n\n")
    for floor in sorted(floors, key=lambda x: (x.get("level") is None, x.get("level") or 0)):
        shown_name = shown_floor_name(floor.get("name"))
        room_index.append(f"## {shown_name}\n\n")
        for area in sorted(floor_areas[floor["floor_id"]], key=lambda x: x["name"].casefold()):
            count = len(area_devices.get(area["id"], []))
            area_name = safe_source_text(area["name"], "Raumname")
            room_index.append(f"- [{area_name}](generated/{room_slug[area['id']]}.md) – {count} alltagsrelevante Geräte\n")
        room_index.append("\n")
    room_index.append(f"<p class=\"page-status\">Inventar aus Backup vom {source_date}; gekennzeichnete Ergänzungen geprüft am {checked_on}</p>\n")
    (docs / "raeume" / "index.md").write_text("".join(room_index), encoding="utf-8")

    device_index = [GENERATED_NOTICE, "# Geräte und ihre Standorte\n\n"]
    shown_count = sum(len(area_devices.get(area["id"], [])) for area in areas)
    device_index.append(f"Hier stehen **{shown_count} alltagsrelevante Geräte**. Home Assistant kennt zusätzlich technische Dienste, Plugins, virtuelle Gruppen und Diagnoseeinträge; diese erscheinen bewusst nicht in der Familienansicht.\n\n")
    device_index.append("## Nach Raum\n\n")
    device_index.append("| Gerät | Art | Standort | Standortstatus |\n|---|---|---|---|\n")
    for area in sorted(areas, key=lambda x: area_location(x["id"]).casefold()):
        for device in area_devices.get(area["id"], []):
            status = "in Home Assistant bestätigt" if device.get("area_id") else "aus Name/Funktion abgeleitet"
            device_index.append(
                f"| {esc(shown_device_name(device))} | {device_kind(device)} | "
                f"[{area_location(area['id'])}](../raeume/generated/{room_slug[area['id']]}.md) | {status} |\n"
            )

    physical_platforms = {
        "alexa_devices", "alexa_media", "zigbee2mqtt", "nuki_ng", "matter", "sonos",
        "mobile_app", "icloud", "pycupra", "tibber", "apple_tv", "philips_js",
        "roborock", "wled", "shelly", "mqtt", "withings", "spotify",
    }
    unassigned_candidates = [
        device for device in devices
        if not area_id_for_device(device)
        and not is_virtual_device(device)
        and has_everyday_entity(device)
        and device_platforms(device) & physical_platforms
    ]
    unassigned_candidates = dedupe_devices(unassigned_candidates)
    stationary_candidates = []
    for device in unassigned_candidates:
        if is_mobile_device(device):
            continue
        stationary_candidates.append(device)
    unassigned_candidates = stationary_candidates
    if unassigned_candidates:
        device_index.append("\n??? question \"Geräte ohne bestätigten festen Raum\"\n\n")
        device_index.append("    Diese Geräte wirken stationär, haben aber noch keinen verlässlichen festen Raum. Es wird bewusst kein Standort erfunden.\n\n")
        device_index.append("    | Gerät | Art | Standort |\n    |---|---|---|\n")
        for device in unassigned_candidates:
            device_index.append(
                f"    | {esc(shown_device_name(device))} | {device_kind(device)} | noch offen |\n"
            )

    device_index.append(f"\n<p class=\"page-status\">Inventar aus Backup vom {source_date}; gekennzeichnete Ergänzungen geprüft am {checked_on}</p>\n")
    (docs / "geraete" / "index.md").write_text("".join(device_index), encoding="utf-8")

    summary = {
        "floors": len(floors),
        "areas": len(areas),
        "labels": len(labels),
        "registry_devices": len(devices),
        "shown_devices": shown_count,
        "registry_entities": len(entities),
        "everyday_entities": len(everyday_entities),
        "automations": len(automations),
        "scenes": len(shown_scenes),
        "source_date": source_date,
        "checked_on": checked_on,
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
