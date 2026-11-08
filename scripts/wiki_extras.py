"""Additional reader sections: emergency, maintenance, energy and technology.

The functions here receive the already parsed registries and the display helpers
of ``generate_docs`` so names are protected exactly like on every other page.
Identifiers, unique IDs, connections and config entries are never published;
integration domains are derived from registry platforms and identifier
*domains* only.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from wiki_batteries import BatteryInfo, battery_info, shopping_list


GENERATED_NOTICE = (
    "<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. "
    "Nicht direkt bearbeiten. -->\n\n"
)

# domain: (display name, needs internet: nein | ja | teilweise)
INTEGRATIONS: dict[str, tuple[str, str]] = {
    "adguard": ("AdGuard Home", "nein"),
    "alexa_devices": ("Alexa-Geräte", "ja"),
    "alexa_media": ("Alexa Media Player", "ja"),
    "apple_tv": ("Apple TV", "nein"),
    "backup": ("Home-Assistant-Backup", "nein"),
    "bambu_lab": ("Bambu Lab 3D-Drucker", "teilweise"),
    "bring": ("Bring! Einkaufslisten", "ja"),
    "cast": ("Google Cast", "nein"),
    "cloud": ("Home Assistant Cloud", "ja"),
    "dreame_mower": ("Dreame Mähroboter", "ja"),
    "dreame_vacuum": ("Dreame Saugroboter", "ja"),
    "esphome": ("ESPHome", "nein"),
    "goecharger": ("go-e Wallbox", "nein"),
    "goecharger_api2": ("go-e Wallbox (API v2)", "nein"),
    "goecharger_mqtt": ("go-e Wallbox (MQTT)", "nein"),
    "google_generative_ai_conversation": ("Google Gemini", "ja"),
    "hacs": ("HACS", "ja"),
    "hassio": ("Supervisor und Apps", "nein"),
    "homekit": ("HomeKit-Brücke", "nein"),
    "homekit_controller": ("HomeKit-Geräte", "nein"),
    "hue": ("Philips Hue Bridge", "nein"),
    "icloud": ("Apple iCloud", "ja"),
    "ipp": ("Drucker", "nein"),
    "matter": ("Matter", "nein"),
    "met": ("Wetter (Met.no)", "ja"),
    "mobile_app": ("Home-Assistant-App auf Handys", "teilweise"),
    "mqtt": ("MQTT", "nein"),
    "narwal": ("Narwal Saugroboter", "ja"),
    "nuki": ("Nuki", "nein"),
    "nuki_ng": ("Nuki (erweitert)", "teilweise"),
    "openai_conversation": ("OpenAI", "ja"),
    "openweathermap": ("OpenWeatherMap", "ja"),
    "philips_js": ("Philips Fernseher", "nein"),
    "ping": ("Erreichbarkeitsprüfung (Ping)", "nein"),
    "pycupra": ("Cupra Connect", "ja"),
    "roborock": ("Roborock", "teilweise"),
    "shelly": ("Shelly", "nein"),
    "smtp": ("E-Mail-Versand", "ja"),
    "sonos": ("Sonos", "nein"),
    "speedport": ("Telekom Speedport", "nein"),
    "spotify": ("Spotify", "ja"),
    "sun": ("Sonnenstand", "nein"),
    "systemmonitor": ("Systemmonitor", "nein"),
    "telegram_bot": ("Telegram", "ja"),
    "tibber": ("Tibber", "ja"),
    "tibber_local": ("Tibber Pulse (lokal)", "nein"),
    "tibber_prices": ("Tibber Preise & Planung", "ja"),
    "tplink": ("TP-Link Kasa/Tapo", "nein"),
    "volkswagencarnet": ("Volkswagen Connect", "ja"),
    "waste_collection_schedule": ("Abfuhrkalender", "ja"),
    "withings": ("Withings", "ja"),
    "wiz": ("WiZ", "nein"),
    "wled": ("WLED", "nein"),
    "wyoming": ("Sprachdienste (Whisper/Piper)", "nein"),
    "zha": ("Zigbee (ZHA)", "nein"),
    "zigbee2mqtt": ("Zigbee2MQTT", "nein"),
}
INTERNET_LABEL = {
    "nein": "nein, läuft lokal",
    "ja": "ja",
    "teilweise": "teilweise",
    "unbekannt": "nicht hinterlegt",
}
HELPER_PLATFORMS: dict[str, str] = {
    "input_boolean": "Schalter",
    "input_button": "Taste",
    "input_datetime": "Datum / Uhrzeit",
    "input_number": "Zahl",
    "input_select": "Auswahl",
    "input_text": "Text",
    "counter": "Zähler",
    "timer": "Timer",
    "schedule": "Zeitplan",
    "template": "Vorlage",
    "group": "Gruppe",
    "utility_meter": "Verbrauchszähler",
    "derivative": "Änderungsrate",
    "integration": "Integralsensor",
    "min_max": "Kombinationssensor",
    "statistics": "Statistik",
    "threshold": "Schwellenwert",
    "trend": "Trend",
    "history_stats": "Verlaufsstatistik",
    "tod": "Tageszeit",
    "switch_as_x": "Gerätetyp ändern",
}
INTERNAL_PLATFORMS = {
    "homeassistant", "person", "zone", "sun", "conversation", "assist_pipeline",
    "tts", "stt", "wake_word", "ai_task", "update", "backup", "hassio",
    "persistent_notification", "automation", "script", "scene", "device_tracker",
    "image_upload", "go2rtc", "camera", "weather",
} | set(HELPER_PLATFORMS)
WIRELESS_LAN_PLATFORMS = {
    "shelly", "wled", "tplink", "wiz", "sonos", "apple_tv", "philips_js", "esphome",
    "bambu_lab", "goecharger_mqtt", "goecharger", "goecharger_api2", "roborock",
    "narwal", "speedport", "cast", "nuki", "nuki_ng", "tibber_local", "dreame_vacuum",
    "dreame_mower", "alexa_media", "alexa_devices", "ipp", "hue",
}
ROBOT_KINDS = {"Saug-/Wischgerät", "Mähroboter"}
BATTERY_ENTITY = re.compile(r"_batter(?:y|ie)(?:_level|_state|_percentage)?$")


@dataclass
class ExtraContext:
    docs: Path
    source: Path
    source_note: str
    devices: list[dict[str, Any]]
    entities: list[dict[str, Any]]
    areas: list[dict[str, Any]]
    area_by_id: dict[str, dict[str, Any]]
    entity_by_id: dict[str, dict[str, Any]]
    device_entities: dict[str, list[dict[str, Any]]]
    auto_meta: list[dict[str, Any]]
    room_slug: dict[str, str]
    shown_device_name: Callable[[dict[str, Any]], str]
    device_kind: Callable[[dict[str, Any]], str]
    area_location: Callable[[str], str]
    area_id_for_device: Callable[[dict[str, Any]], str | None]
    is_virtual_device: Callable[[dict[str, Any]], bool]
    is_mobile_device: Callable[[dict[str, Any]], bool]
    entity_label: Callable[..., str]
    safe_text: Callable[[Any, str], str]
    esc: Callable[[Any], str]
    hidden_devices: set[str] = field(default_factory=set)
    battery_overrides: dict[str, str] = field(default_factory=dict)


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    import yaml

    if not path.exists() or path.stat().st_size == 0:
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _read_storage(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    data = document.get("data") if isinstance(document, dict) else None
    return data if isinstance(data, dict) else {}


def _read_inventory(source: Path) -> dict[str, Any]:
    path = source / ".wiki_backup_metadata.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _footer(note: str) -> str:
    return f"\n<p class=\"page-status\">Backup-Stand: {note}. Aktuelle Werte zeigt die Haus-Wiki-App unter Live.</p>\n"


def _integration(domain: str, safe_text: Callable[[Any, str], str]) -> tuple[str, str]:
    if domain in INTEGRATIONS:
        return INTEGRATIONS[domain]
    return safe_text(domain.replace("_", " ").title(), "Integrationsname"), "unbekannt"


class Inventory:
    """Derived, publishable facts shared by the extra pages."""

    def __init__(self, ctx: ExtraContext) -> None:
        self.ctx = ctx
        self.physical = [
            device for device in ctx.devices
            if not ctx.is_virtual_device(device)
            and not device.get("disabled_by")
            and not ctx.is_mobile_device(device)
            and ctx.shown_device_name(device) not in ctx.hidden_devices
        ]
        self.physical.sort(key=lambda device: ctx.shown_device_name(device).casefold())
        self.kinds: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for device in self.physical:
            self.kinds[ctx.device_kind(device)].append(device)

    # Device classification -------------------------------------------------
    def device_domains(self, device: dict[str, Any]) -> set[str]:
        domains: set[str] = set()
        for item in device.get("identifiers") or []:
            if isinstance(item, (list, tuple)) and item and isinstance(item[0], str):
                domain = item[0]
                value = str(item[1]) if len(item) > 1 else ""
                if domain == "mqtt" and value.startswith("zigbee2mqtt_"):
                    domain = "zigbee2mqtt"
                domains.add(domain)
        for entity in self.ctx.device_entities.get(device.get("id"), []):
            if entity.get("platform"):
                domains.add(str(entity["platform"]))
        return domains

    def is_zigbee(self, device: dict[str, Any]) -> bool:
        return bool(self.device_domains(device) & {"zigbee2mqtt", "zha"})

    def zigbee_coordinator(self) -> dict[str, Any] | None:
        for device in self.ctx.devices:
            name = str(device.get("name") or "").casefold()
            model = str(device.get("model") or "").casefold()
            if "zigbee2mqtt bridge" in name or (model == "bridge" and "zigbee" in str(device.get("manufacturer") or "").casefold()):
                return device
            for item in device.get("identifiers") or []:
                if isinstance(item, (list, tuple)) and len(item) > 1 and str(item[1]).startswith("zigbee2mqtt_bridge"):
                    return device
        return None

    def battery_entities(self, device: dict[str, Any]) -> list[dict[str, Any]]:
        result = []
        for entity in self.ctx.device_entities.get(device.get("id"), []):
            if entity.get("disabled_by"):
                continue
            device_class = entity.get("device_class") or entity.get("original_device_class")
            if device_class == "battery" or (
                str(entity.get("entity_id", "")).startswith(("sensor.", "binary_sensor."))
                and BATTERY_ENTITY.search(str(entity.get("entity_id")))
            ):
                result.append(entity)
        return result

    def battery_devices(self) -> list[tuple[dict[str, Any], BatteryInfo]]:
        result = []
        seen: set[str] = set()
        for device in self.physical:
            if not self.battery_entities(device):
                continue
            name = self.ctx.shown_device_name(device).casefold()
            if name in seen:
                continue
            seen.add(name)
            if self.ctx.device_kind(device) in ROBOT_KINDS:
                info = BatteryInfo("eingebauter Akku", "hersteller", "lädt in der Station")
            else:
                info = battery_info(
                    device.get("id"), device.get("manufacturer"), device.get("model"),
                    self.ctx.battery_overrides,
                )
            result.append((device, info))
        return result

    # Locations -------------------------------------------------------------
    def location(self, device: dict[str, Any], prefix: str = "..") -> str:
        area_id = self.ctx.area_id_for_device(device)
        if not area_id or area_id not in self.ctx.area_by_id:
            return "kein Raum hinterlegt"
        slug = self.ctx.room_slug.get(area_id)
        label = self.ctx.area_location(area_id)
        return f"[{label}]({prefix}/raeume/generated/{slug}.md)" if slug else label

    def room_sort(self, device: dict[str, Any]) -> tuple[str, str]:
        area_id = self.ctx.area_id_for_device(device)
        label = self.ctx.area_location(area_id) if area_id in self.ctx.area_by_id else "~"
        return label.casefold(), self.ctx.shown_device_name(device).casefold()

    # Integrations ----------------------------------------------------------
    def integrations(self) -> list[dict[str, Any]]:
        device_counts: Counter[str] = Counter()
        entity_counts: Counter[str] = Counter()
        for device in self.ctx.devices:
            if device.get("disabled_by"):
                continue
            for domain in {
                ("zigbee2mqtt" if item[0] == "mqtt" and len(item) > 1 and str(item[1]).startswith("zigbee2mqtt_") else item[0])
                for item in device.get("identifiers") or []
                if isinstance(item, (list, tuple)) and item and isinstance(item[0], str)
            }:
                device_counts[domain] += 1
        zigbee_ids = {d.get("id") for d in self.ctx.devices if self.is_zigbee(d)}
        for entity in self.ctx.entities:
            platform = entity.get("platform")
            if platform and not entity.get("disabled_by"):
                # Zigbee2MQTT publishes its entities through MQTT; count them
                # where a reader expects them.
                if platform == "mqtt" and entity.get("device_id") in zigbee_ids:
                    platform = "zigbee2mqtt"
                entity_counts[str(platform)] += 1
        domains = {
            domain for domain in set(device_counts) | set(entity_counts)
            if domain not in INTERNAL_PLATFORMS or domain in {"hassio", "backup"}
        }
        rows = []
        for domain in domains:
            name, internet = _integration(domain, self.ctx.safe_text)
            rows.append({
                "domain": domain,
                "name": name,
                "internet": internet,
                "devices": device_counts.get(domain, 0),
                "entities": entity_counts.get(domain, 0),
            })
        return sorted(rows, key=lambda row: (row["name"].casefold(), row["domain"]))


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def _battery_section(inv: Inventory, prefix: str = "..") -> list[str]:
    ctx = inv.ctx
    rows = sorted(inv.battery_devices(), key=lambda item: inv.room_sort(item[0]))
    out: list[str] = []
    if not rows:
        out.append("Im Backup ist kein Gerät mit Batterie- oder Akkuanzeige hinterlegt.\n\n")
        return out
    known = [info for _, info in rows if info.certainty != "unbekannt"]
    out.append(
        f"**{len(rows)} Geräte** melden einen Batterie- oder Akkustand. "
        f"Für **{len(known)}** ist der Typ bekannt. Den aktuellen Ladestand zeigt die "
        "Haus-Wiki-App unter **Live**; dort kannst du fehlende Typen auch eintragen.\n\n"
    )
    stock = shopping_list([info.type for _, info in rows if info.certainty in {"hersteller", "eingetragen", "typisch"}])
    if stock:
        out.append("!!! tip \"Batterievorrat für einen kompletten Wechsel\"\n")
        out.append("    " + ", ".join(f"**{count}× {cell}**" for cell, count in stock) + "\n\n")
        out.append("    Typische Angaben sind mitgezählt; vor dem Kauf an einem Gerät prüfen.\n\n")
    out.append("| Gerät | Standort | Batterie / Akku | Angabe |\n|---|---|---|---|\n")
    for device, info in rows:
        kind = ctx.esc(info.type) if info.type else "*noch eintragen*"
        if info.note:
            kind += f" <small>({ctx.esc(info.note)})</small>"
        out.append(
            f"| {ctx.esc(ctx.shown_device_name(device))} | {inv.location(device, prefix)} | {kind} | {info.label} |\n"
        )
    out.append("\n")
    return out


def write_maintenance(ctx: ExtraContext, inv: Inventory, inventory: dict[str, Any]) -> int:
    out = [GENERATED_NOTICE, "# Wartung & Pflege\n\n"]
    out.append(
        "Was regelmäßig Aufmerksamkeit braucht: Batterien, Pflegearbeiten an Geräten und "
        "Hinweise, wo die Einrichtung noch lückenhaft ist.\n\n"
    )
    out.append("## Batterien und Akkus\n\n")
    out.extend(_battery_section(inv))

    tasks: list[tuple[str, str]] = []
    kinds = set(inv.kinds)
    if "Rauchmelder" in kinds:
        tasks.append(("Rauchmelder", "Einmal im Monat den Prüfknopf drücken. Piept ein Melder kurz und regelmäßig, ist die Batterie schwach."))
    if "Luftreiniger" in kinds:
        tasks.append(("Luftreiniger", "Filter nach Herstellerangabe wechseln (meist etwa alle sechs Monate). Den Vorfilter zwischendurch absaugen."))
    if "Saug-/Wischgerät" in kinds:
        tasks.append(("Saug- und Wischroboter", "Bürsten von Haaren befreien, Filter ausklopfen, Schmutzwasser und Beutel der Station regelmäßig leeren."))
    if "Mähroboter" in kinds:
        tasks.append(("Mähroboter", "Messer prüfen und vor dem Winter reinigen, laden und frostfrei lagern."))
    if "Wasserventil" in kinds:
        tasks.append(("Wasserventil im Garten", "Vor dem ersten Frost abbauen oder entleeren. Im Frühjahr Dichtung und Batterie prüfen."))
    if "Klimaanlagen-Schalter" in kinds or any("klima" in ctx.shown_device_name(d).casefold() for d in inv.physical):
        tasks.append(("Klimaanlage", "Luftfilter zu Beginn und Ende der Saison reinigen."))
    if "3D-Drucker" in kinds:
        tasks.append(("3D-Drucker", "Druckplatte reinigen, Filamentreste entfernen; Wartungshinweise des Herstellers in dessen App beachten."))
    if "Tür-/Fensterkontakt" in kinds or "Wandschalter / Taster" in kinds:
        tasks.append(("Funkschalter und Kontakte", "Reagiert ein Schalter verzögert oder gar nicht, zuerst die Batterie prüfen. Gerät nicht zurücksetzen."))
    if tasks:
        out.append("## Regelmäßige Pflege\n\n| Gerät | Was ist zu tun? |\n|---|---|\n")
        for name, text in tasks:
            out.append(f"| {name} | {text} |\n")
        out.append("\n")

    unnamed = [d for d in ctx.devices if re.fullmatch(r"0x[0-9a-f]+", str(d.get("name_by_user") or d.get("name") or "").strip().casefold())]
    without_room = [d for d in inv.physical if not ctx.area_id_for_device(d)]
    out.append("## Offene Punkte in der Einrichtung\n\n")
    if not unnamed and not without_room:
        out.append("Alle erkannten Geräte haben einen Namen und einen Raum.\n\n")
    else:
        if unnamed:
            out.append(f"- **{len(unnamed)} Gerät(e) ohne Namen**: Zigbee-Geräte, die nur mit ihrer Funkadresse angemeldet sind. Sie sollten benannt oder entfernt werden; Details unter [Zigbee-Netz](../technik/zigbee.md).\n")
        if without_room:
            out.append(f"- **{len(without_room)} Gerät(e) ohne Raum**: Sie erscheinen auf keiner Raumseite. Liste unter [Geräte](../geraete/index.md).\n")
        out.append("\n")

    firmware = [d for d in inv.physical if d.get("sw_version")]
    if firmware:
        out.append("??? info \"Firmware- und Softwarestände laut Backup\"\n\n")
        out.append("    | Gerät | Hersteller / Modell | Version |\n    |---|---|---|\n")
        for device in sorted(firmware, key=lambda d: ctx.shown_device_name(d).casefold()):
            maker = ctx.safe_text(device.get("manufacturer"), "Hersteller")
            model = ctx.safe_text(device.get("model"), "Modell")
            version = ctx.safe_text(device.get("sw_version"), "Firmwareversion")
            out.append(f"    | {ctx.esc(ctx.shown_device_name(device))} | {ctx.esc(maker)} / {ctx.esc(model)} | {ctx.esc(version)} |\n")
        out.append("\n    Verfügbare Updates zeigt die Haus-Wiki-App unter **Live** beziehungsweise Home Assistant unter Einstellungen.\n\n")

    version = inventory.get("homeassistant_version")
    out.append("## Sicherungen\n\n")
    out.append(
        "Das Wiki entsteht aus dem neuesten vollständigen Home-Assistant-Backup. "
        + (f"Dieser Stand wurde mit Home Assistant **{ctx.safe_text(version, 'HA-Version')}** erstellt. " if version else "")
        + "Wann das letzte Backup lief, zeigt die App unter **Live**. Ein Backup älter als eine Woche ist ein Grund, nachzusehen.\n"
    )
    out.append(_footer(ctx.source_note))
    (ctx.docs / "wartung").mkdir(parents=True, exist_ok=True)
    (ctx.docs / "wartung" / "index.md").write_text("".join(out), encoding="utf-8")
    return len(inv.battery_devices())


def _energy_label(ctx: ExtraContext, stat: Any) -> str:
    value = str(stat or "")
    if value in ctx.entity_by_id:
        entity = ctx.entity_by_id[value]
        device = next((d for d in ctx.devices if d.get("id") == entity.get("device_id")), None)
        label = ctx.entity_label(value)
        if device is not None:
            return f"{ctx.shown_device_name(device)} – {label}"
        return label
    if ":" in value:
        return ctx.safe_text(value.split(":", 1)[0].replace("_", " ").title() + "-Statistik", "Statistikname")
    return ctx.safe_text(value.replace("_", " "), "Statistikname")


def write_energy(ctx: ExtraContext, inv: Inventory) -> None:
    energy = _read_storage(ctx.source / ".storage/energy")
    out = [GENERATED_NOTICE, "# Haushalt & Energie\n\n"]
    out.append(
        "Strom, Auto, Haushaltsgeräte und Garten auf einen Blick: welche Geräte dazugehören und "
        "was automatisch passiert.\n\n"
    )
    sources = energy.get("energy_sources") if isinstance(energy.get("energy_sources"), list) else []
    consumers = energy.get("device_consumption") if isinstance(energy.get("device_consumption"), list) else []
    out.append("## Strom im Überblick\n\n")
    if sources or consumers:
        names = {"grid": "Stromnetz", "solar": "Solaranlage", "battery": "Hausspeicher", "gas": "Gas", "water": "Wasser"}
        rows: list[tuple[str, str]] = []
        for item in sources:
            if not isinstance(item, dict):
                continue
            kind = names.get(str(item.get("type")), ctx.safe_text(item.get("type"), "Energiequelle"))
            stats: list[Any] = []
            for flow in ("flow_from", "flow_to"):
                for part in item.get(flow) or []:
                    if isinstance(part, dict):
                        stats.append(part.get("stat_energy_from") or part.get("stat_energy_to"))
            for key in ("stat_energy_from", "stat_energy_to", "stat_rate"):
                if item.get(key):
                    stats.append(item.get(key))
            measured = ", ".join(dict.fromkeys(_energy_label(ctx, stat) for stat in stats if stat)) or "–"
            rows.append((kind, measured))
        if rows:
            out.append("| Quelle | Gemessen über |\n|---|---|\n")
            for kind, measured in rows:
                out.append(f"| {kind} | {ctx.esc(measured)} |\n")
            out.append("\n")
        if consumers:
            out.append(f"Einzeln erfasst werden **{len(consumers)} Verbraucher**:\n\n")
            for item in consumers:
                if isinstance(item, dict) and item.get("stat_consumption"):
                    label = ctx.safe_text(item["name"], "Verbrauchername") if item.get("name") else _energy_label(ctx, item.get("stat_consumption"))
                    out.append(f"- {label}\n")
            out.append("\n")
        out.append("Verläufe und Kosten zeigt Home Assistant im Energie-Dashboard.\n\n")
    else:
        out.append("Im Backup ist kein Energie-Dashboard eingerichtet.\n\n")

    groups = [
        ("Auto und Wallbox", {"Wallbox"}, ("cupra", "born", "wallbox", "auto")),
        ("Haushaltsgeräte", {"Kaffeemaschine"}, ("waschmaschine", "trockner", "spülmaschine", "kühlschrank", "gefrier", "backofen", "herd")),
        ("Heizen, Kühlen und Luft", {"Heizgerät", "Klimaanlagen-Schalter", "Luftreiniger"}, ("klima", "heiz", "lüft")),
        ("Garten und Wasser", {"Wasserventil", "Mähroboter"}, ("garten", "bewässer", "pumpe", "wasser")),
        ("Reinigung", {"Saug-/Wischgerät"}, ()),
    ]
    automation_groups = {
        "Auto und Wallbox": {"Energie & Auto"},
        "Haushaltsgeräte": {"Haushalt"},
        "Garten und Wasser": {"Garten & Wasser"},
    }
    used: set[str] = set()
    for title, kinds, words in groups:
        members = []
        for device in inv.physical:
            name = ctx.shown_device_name(device)
            if name in used:
                continue
            kind = ctx.device_kind(device)
            if kind in kinds or (words and any(w in name.casefold() for w in words) and kind not in {"Licht", "Wandschalter / Taster", "Temperatur-/Feuchtesensor", "Lautsprecher / Sprachassistent"}):
                members.append(device)
                used.add(name)
        related = [
            item for item in ctx.auto_meta
            if item["enabled"] and not item["technical"] and item["category"] in automation_groups.get(title, set())
        ]
        if not members and not related:
            continue
        out.append(f"## {title}\n\n")
        if members:
            out.append("| Gerät | Art | Standort |\n|---|---|---|\n")
            for device in sorted(members, key=inv.room_sort):
                out.append(f"| {ctx.esc(ctx.shown_device_name(device))} | {ctx.device_kind(device)} | {inv.location(device)} |\n")
            out.append("\n")
        if title == "Haushaltsgeräte" and any(ctx.device_kind(d) == "Smarte Steckdose" for d in members):
            out.append("Die smarten Steckdosen messen den Stromverbrauch. Daran erkennt Home Assistant zum Beispiel, wann ein Programm fertig ist. Bitte nicht ausschalten, solange das Gerät läuft.\n\n")
        if related:
            out.append("**Das passiert automatisch:**\n\n")
            for item in sorted(related, key=lambda x: x["title"].casefold()):
                out.append(f"- [{item['title']}](../automationen/generated/{item['slug']}.md)\n")
            out.append("\n")
    out.append(_footer(ctx.source_note))
    (ctx.docs / "energie").mkdir(parents=True, exist_ok=True)
    (ctx.docs / "energie" / "index.md").write_text("".join(out), encoding="utf-8")


def write_emergency(ctx: ExtraContext, inv: Inventory, integrations: list[dict[str, Any]], manual_pages: set[str]) -> None:
    kinds = set(inv.kinds)
    names = " ".join(ctx.shown_device_name(d).casefold() for d in inv.physical)
    out = ["---\nhide:\n  - toc\n---\n\n", GENERATED_NOTICE, "# Notfall & Ausfälle\n\n"]
    out.append(
        "<div class=\"emergency-lead\" markdown>\n\n"
        "**Bei Feuer, Rauch, Wasser oder Gas zuerst Menschen in Sicherheit bringen und den Notruf 112 wählen.** "
        "Das Smart Home ist dabei unwichtig.\n\n</div>\n\n"
    )
    if "notfall" in manual_pages:
        out.append("!!! danger \"Eigene Notfallhinweise\"\n    Kontakte und Hinweise der Familie stehen unter [Notfallhinweise](../manuell/notfall.md).\n\n")
    else:
        out.append("!!! note \"Kontakte ergänzen\"\n    Lege in der Haus-Wiki-App unter **Verwalten → Eigene Anleitungen** eine Seite mit dem Namen `notfall` an. Sie erscheint dann hier ganz oben, zum Beispiel mit Telefonnummern von Elektriker, Vermieter oder Nachbarn.\n\n")

    out.append("## Was ist los?\n\n<div class=\"grid cards\" markdown>\n\n")
    out.append("-   :material-home-alert:{ .lg .sign-red } **Home Assistant reagiert nicht**\n\n    App lädt nicht, Automationen laufen nicht.\n\n    [Weiter](#home-assistant-reagiert-nicht)\n\n")
    out.append("-   :material-wifi-off:{ .lg .sign-red } **Das Internet ist weg**\n\n    Router blinkt rot, Handy hat kein WLAN-Internet.\n\n    [Weiter](#das-internet-ist-weg)\n\n")
    out.append("-   :material-flash-off:{ .lg .sign-red } **Der Strom war weg**\n\n    Nach einem Stromausfall oder einer ausgelösten Sicherung.\n\n    [Weiter](#der-strom-war-weg)\n\n")
    if kinds & {"Türschloss / Türöffner"} or "nuki" in names:
        out.append("-   :material-door-closed-lock:{ .lg .sign-red } **Ich komme nicht ins Haus**\n\n    Schloss oder Türöffner reagiert nicht.\n\n    [Weiter](#haustur-und-schloss)\n\n")
    out.append("</div>\n\n")

    out.append("## Home Assistant reagiert nicht\n\n")
    out.append("1. Ruhe bewahren: Das Haus funktioniert auch ohne Home Assistant, nur die Automatik fehlt.\n")
    out.append("2. Licht über die Wandschalter bedienen. Funkschalter, die nur an Home Assistant gekoppelt sind, können dabei ausfallen; dann die Lampe in der jeweiligen Hersteller-App schalten.\n")
    out.append("3. Nichts zurücksetzen und keine Geräte neu anlernen.\n")
    out.append("4. Die Administration informieren. Hilft das nicht, den Home-Assistant-Rechner einmal vom Strom trennen, 10 Sekunden warten und wieder einstecken. Der Start dauert einige Minuten.\n\n")
    still = []
    if kinds & {"Türschloss / Türöffner"} or "nuki" in names:
        still.append("Haustür: mit dem Schlüssel oder der Nuki-App (Bluetooth, ohne Home Assistant)")
    if "Rauchmelder" in kinds:
        still.append("Rauchmelder: piepen weiter vor Ort, nur die Handy-Meldung fehlt")
    if "Smarte Steckdose" in kinds:
        still.append("Haushaltsgeräte an smarten Steckdosen: laufen weiter, die Taste an der Steckdose schaltet von Hand")
    if "Wallbox" in kinds:
        still.append("Wallbox: lädt mit ihren eigenen Einstellungen; Steuerung über die Hersteller-App")
    if "Saug-/Wischgerät" in kinds:
        still.append("Saugroboter: über seine eigene App starten")
    if still:
        out.append("**Funktioniert weiterhin:**\n\n" + "".join(f"- {line}\n" for line in still) + "\n")

    out.append("## Das Internet ist weg\n\n")
    out.append("Home Assistant arbeitet zu Hause ohne Internet weiter. Ausfallen können Dienste, die über einen Server des Herstellers laufen, und der Zugriff von unterwegs.\n\n")
    technical = {"hassio", "backup", "mqtt", "systemmonitor", "ping", "hacs", "homekit", "wyoming"}
    relevant = [row for row in integrations if row["devices"] and row["domain"] not in technical]
    local = [row for row in relevant if row["internet"] == "nein"]
    cloud = [row for row in relevant if row["internet"] in {"ja", "teilweise"}]
    if local or cloud:
        out.append("<div class=\"split\" markdown>\n\n<div markdown>\n\n**Läuft weiter**\n\n")
        out.extend(f"- {row['name']}\n" for row in local)
        out.append("\n</div>\n\n<div markdown>\n\n**Braucht Internet**\n\n")
        out.extend(f"- {row['name']}{' (teilweise)' if row['internet'] == 'teilweise' else ''}\n" for row in cloud)
        out.append("\n</div>\n\n</div>\n\n")
    router = [d for d in ctx.devices if "speedport" in str(d.get("model") or d.get("name") or "").casefold() or ctx.device_kind(d) == "Router"]
    out.append("**Was hilft:** Router für 30 Sekunden vom Strom trennen und wieder einstecken. ")
    if router:
        out.append(f"Der Router ist ein {ctx.esc(ctx.safe_text(router[0].get('model') or router[0].get('name'), 'Routermodell'))}. ")
    out.append("Leuchtet er danach weiter rot, liegt die Störung meist beim Anbieter.\n\n")

    out.append("## Der Strom war weg\n\n")
    out.append("- Home Assistant startet von selbst wieder. Das dauert einige Minuten.\n")
    if any(inv.is_zigbee(d) for d in inv.physical):
        out.append("- Funkgeräte (Zigbee) melden sich danach nach und nach zurück. Bis zu 15 Minuten sind normal.\n")
    out.append("- Lampen können nach dem Stromausfall eingeschaltet sein. Einfach normal ausschalten.\n")
    if "Smarte Steckdose" in kinds:
        out.append("- Prüfen, ob Kühlschrank und Gefriergerät wieder Strom haben.\n")
    out.append("\n")

    device_sections = []
    if kinds & {"Türschloss / Türöffner"} or "nuki" in names:
        device_sections.append(("Haustür und Schloss", [
            "Das Schloss lässt sich jederzeit mit dem normalen Schlüssel öffnen, von innen auch per Drehknauf.",
            "Die Nuki-App funktioniert per Bluetooth direkt am Schloss, auch ohne Internet und ohne Home Assistant.",
            "Blinkt das Schloss rot oder meldet die App einen schwachen Akku, das Schloss laden beziehungsweise die Batterien tauschen (siehe [Wartung](../wartung/index.md)).",
        ]))
    if "Wasserventil" in kinds:
        device_sections.append(("Wasser im Garten läuft und hört nicht auf", [
            "Das Wasserventil im Garten vor Ort schließen: am Ventil die Taste drücken oder es vom Wasserhahn abschrauben.",
            "Zur Sicherheit den Wasserhahn davor zudrehen.",
        ]))
    if "Rauchmelder" in kinds:
        device_sections.append(("Ein Rauchmelder piept", [
            "Dauerton: Ernstfall annehmen, Haus verlassen, 112.",
            "Kurzes Piepen etwa jede Minute: Die Batterie ist schwach. Batterie tauschen.",
        ]))
    if "Heizgerät" in kinds:
        device_sections.append(("Heizstrahler geht nicht aus", [
            "Den Heizstrahler am eigenen Schalter oder an der Sicherung ausschalten.",
        ]))
    if "Wallbox" in kinds:
        device_sections.append(("Das Auto lädt nicht", [
            "Anzeige an Wallbox und Auto prüfen. Die Wallbox lässt sich auch über die Hersteller-App steuern.",
            "Ist im Auto ein Ladeziel oder Zeitplan gesetzt, startet das Laden eventuell später.",
        ]))
    for title, lines in device_sections:
        out.append(f"## {title}\n\n" + "".join(f"- {line}\n" for line in lines) + "\n")

    out.append("## Was du nicht tun solltest\n\n")
    out.append("- Geräte nicht auf Werkseinstellungen zurücksetzen oder aus Apps löschen.\n")
    out.append("- Keine Zugangsdaten oder Codes an Fremde weitergeben, auch nicht am Telefon.\n")
    out.append("- Bei Wasser und Strom im Zweifel die Hauptsicherung beziehungsweise den Haupthahn nutzen und Fachleute rufen.\n")
    out.append(_footer(ctx.source_note))
    (ctx.docs / "notfall").mkdir(parents=True, exist_ok=True)
    (ctx.docs / "notfall" / "index.md").write_text("".join(out), encoding="utf-8")


def write_technology(ctx: ExtraContext, inv: Inventory, integrations: list[dict[str, Any]], inventory: dict[str, Any]) -> dict[str, int]:
    tech = ctx.docs / "technik"
    tech.mkdir(parents=True, exist_ok=True)
    apps = [app for app in inventory.get("apps") or [] if isinstance(app, dict)]
    scripts = _read_yaml_mapping(ctx.source / "scripts.yaml")
    helpers = [
        entity for entity in ctx.entities
        if entity.get("platform") in HELPER_PLATFORMS
        and not entity.get("disabled_by")
        and str(entity.get("entity_id", "")).split(".", 1)[0] != "update"
    ]
    zigbee = [d for d in inv.physical if inv.is_zigbee(d)]
    lan = [d for d in inv.physical if inv.device_domains(d) & WIRELESS_LAN_PLATFORMS and not inv.is_zigbee(d)]
    version = inventory.get("homeassistant_version")

    # Overview ------------------------------------------------------------
    out = [GENERATED_NOTICE, "# Technik\n\n"]
    out.append("Dieser Bereich ist für alle, die das System betreuen. Im Alltag wird er nicht gebraucht.\n\n")
    out.append("<div class=\"stat-grid\" markdown>\n\n")
    stats = [
        ("Home Assistant", ctx.safe_text(version, "HA-Version") if version else "–"),
        ("Integrationen", str(len(integrations))),
        ("Apps", str(len(apps)) if apps else "–"),
        ("Zigbee-Geräte", str(len(zigbee))),
        ("Automationen", str(len(ctx.auto_meta))),
        ("Skripte", str(len(scripts))),
        ("Helfer", str(len(helpers))),
    ]
    for label, value in stats:
        out.append(f"<div class=\"stat\"><span>{label}</span><strong>{value}</strong></div>\n")
    out.append("\n</div>\n\n")
    out.append("<div class=\"grid cards\" markdown>\n\n")
    for icon, title, text, link in (
        ("puzzle", "Integrationen", "Woran Home Assistant angebunden ist und was davon Internet braucht.", "integrationen.md"),
        ("apps", "Apps", "Zusatzprogramme auf dem Home-Assistant-Server.", "apps.md"),
        ("zigbee", "Zigbee-Netz", "Funkgeräte, Stromversorgung und unbenannte Geräte.", "zigbee.md"),
        ("lan", "Netzwerk", "Router und Geräte im WLAN oder LAN.", "netzwerk.md"),
        ("script-text-outline", "Skripte & Helfer", "Wiederverwendbare Abläufe und Hilfswerte.", "skripte-helfer.md"),
        ("clipboard-check-outline", "Wiki & Datenqualität", "Kennzahlen, Grenzen der Auswertung, Wiki-Betrieb.", "../admin/index.md"),
    ):
        out.append(f"-   :material-{icon}:{{ .lg }} **{title}**\n\n    {text}\n\n    [Öffnen]({link})\n\n")
    out.append("</div>\n")
    out.append(_footer(ctx.source_note))
    (tech / "index.md").write_text("".join(out), encoding="utf-8")

    # Integrations --------------------------------------------------------
    out = [GENERATED_NOTICE, "# Integrationen\n\n"]
    out.append(
        f"Home Assistant nutzt **{len(integrations)} Integrationen**. Die Spalte *Internet nötig* beruht auf dem "
        "üblichen Verhalten der Integration, nicht auf einer Messung.\n\n"
    )
    out.append("| Integration | Geräte | Entitäten | Internet nötig? |\n|---|---:|---:|---|\n")
    for row in integrations:
        out.append(f"| {row['name']} | {row['devices']} | {row['entities']} | {INTERNET_LABEL[row['internet']]} |\n")
    out.append("\n??? info \"Technische Namen\"\n\n")
    out.append("    " + ", ".join(f"`{row['domain']}`" for row in integrations) + "\n")
    out.append(_footer(ctx.source_note))
    (tech / "integrationen.md").write_text("".join(out), encoding="utf-8")

    # Apps ----------------------------------------------------------------
    out = [GENERATED_NOTICE, "# Apps auf dem Home-Assistant-Server\n\n"]
    if apps:
        out.append(f"Das Backup enthält **{len(apps)} Apps** (früher „Add-ons“). Sie laufen neben Home Assistant auf demselben Rechner.\n\n")
        out.append("| App | Version |\n|---|---|\n")
        for app in apps:
            name = ctx.safe_text(app.get("name") or app.get("slug"), "App-Name")
            shown_version = ctx.safe_text(app.get("version"), "App-Version") if app.get("version") else "–"
            out.append(f"| {ctx.esc(name)} | {ctx.esc(shown_version)} |\n")
        out.append("\nOb eine App gerade läuft und ob Updates bereitstehen, zeigt Home Assistant unter **Einstellungen → Apps**.\n")
    else:
        out.append("Das verwendete Backup enthält keine App-Liste.\n")
    out.append(_footer(ctx.source_note))
    (tech / "apps.md").write_text("".join(out), encoding="utf-8")

    # Zigbee --------------------------------------------------------------
    coordinator = inv.zigbee_coordinator()
    out = [GENERATED_NOTICE, "# Zigbee-Netz\n\n"]
    if zigbee:
        battery_ids = {d.get("id") for d, _ in inv.battery_devices()}
        mains = [d for d in zigbee if d.get("id") not in battery_ids]
        out.append(
            f"**{len(zigbee)} Zigbee-Geräte** funken über "
            + (f"die Zentrale *{ctx.esc(ctx.safe_text(coordinator.get('name_by_user') or coordinator.get('name'), 'Gerätename'))}*" if coordinator else "eine Zigbee-Zentrale")
            + f". **{len(zigbee) - len(mains)}** laufen mit Batterie. Die übrigen **{len(mains)}** melden "
            "keinen Batteriestand, hängen also in der Regel am Strom und leiten Funksignale weiter.\n\n"
        )
        out.append("!!! tip \"Gute Funkverbindung\"\n    Geräte am Strom verstärken das Netz. Wird eine Lampe dauerhaft hart ausgeschaltet (Wandschalter aus), fehlt sie als Zwischenstation. Batteriegeräte, die oft ausfallen, profitieren von einem Steckdosen-Gerät in der Nähe.\n\n")
        out.append("| Gerät | Art | Standort | Strom |\n|---|---|---|---|\n")
        for device in sorted(zigbee, key=inv.room_sort):
            power = "Batterie" if device.get("id") in battery_ids else "Netz"
            out.append(f"| {ctx.esc(ctx.shown_device_name(device))} | {ctx.device_kind(device)} | {inv.location(device)} | {power} |\n")
        out.append("\n")
    else:
        out.append("Im Backup sind keine Zigbee-Geräte hinterlegt.\n\n")
    unnamed = [
        d for d in ctx.devices
        if re.fullmatch(r"0x[0-9a-f]+", str(d.get("name_by_user") or d.get("name") or "").strip().casefold())
    ]
    if unnamed:
        out.append("## Unbenannte Geräte\n\n")
        out.append(f"{len(unnamed)} Gerät(e) sind nur mit ihrer Funkadresse angemeldet. Typisch sind neu angelernte oder nicht erkannte Geräte. In Zigbee2MQTT benennen und einem Raum zuordnen oder entfernen.\n\n")
        out.append("| Hersteller / Modell | Raum |\n|---|---|\n")
        for device in unnamed:
            maker = ctx.safe_text(device.get("manufacturer") or "unbekannt", "Hersteller")
            model = ctx.safe_text(device.get("model") or "unbekannt", "Modell")
            out.append(f"| {ctx.esc(maker)} / {ctx.esc(model)} | {inv.location(device)} |\n")
        out.append("\n")
    out.append(_footer(ctx.source_note))
    (tech / "zigbee.md").write_text("".join(out), encoding="utf-8")

    # Network -------------------------------------------------------------
    out = [GENERATED_NOTICE, "# Netzwerk\n\n"]
    routers = [d for d in ctx.devices if "speedport" in str(d.get("model") or d.get("name") or "").casefold() or ctx.device_kind(d) == "Router"]
    if routers:
        router = routers[0]
        out.append("## Router\n\n")
        model = ctx.safe_text(router.get("model") or router.get("name"), "Routermodell")
        maker = ctx.safe_text(router.get("manufacturer") or "–", "Hersteller")
        firmware = ctx.safe_text(router.get("sw_version"), "Firmwareversion") if router.get("sw_version") else "–"
        out.append(f"| Modell | Hersteller | Firmware |\n|---|---|---|\n| {ctx.esc(model)} | {ctx.esc(maker)} | {ctx.esc(firmware)} |\n\n")
    domains = {row["domain"] for row in integrations}
    services = []
    if "adguard" in domains:
        services.append("**AdGuard Home** filtert Werbung und Tracker für alle Geräte im Netz. Fällt er aus, kann die Namensauflösung im ganzen Haus stocken.")
    if "matter" in domains:
        services.append("**Matter** ist eingerichtet. Matter-Geräte sprechen per WLAN oder Thread direkt mit Home Assistant.")
    if "ping" in domains:
        services.append("**Erreichbarkeitsprüfungen** (Ping) überwachen die Internetverbindung.")
    if services:
        out.append("## Netzwerkdienste\n\n" + "".join(f"- {line}\n" for line in services) + "\n")
    if lan:
        out.append(f"## Geräte im WLAN oder LAN ({len(lan)})\n\n")
        out.append("Diese Geräte sind direkt mit dem Heimnetz verbunden. Bei WLAN-Problemen sind sie als Erstes betroffen.\n\n")
        out.append("| Gerät | Art | Standort | Anbindung |\n|---|---|---|---|\n")
        for device in sorted(lan, key=inv.room_sort):
            domain = sorted(inv.device_domains(device) & WIRELESS_LAN_PLATFORMS)[0]
            name, _ = _integration(domain, ctx.safe_text)
            out.append(f"| {ctx.esc(ctx.shown_device_name(device))} | {ctx.device_kind(device)} | {inv.location(device)} | {name} |\n")
        out.append("\n")
    out.append("IP-Adressen, WLAN-Namen und Zugangsdaten stehen bewusst nicht im Wiki.\n")
    out.append(_footer(ctx.source_note))
    (tech / "netzwerk.md").write_text("".join(out), encoding="utf-8")

    # Scripts and helpers ------------------------------------------------
    out = [GENERATED_NOTICE, "# Skripte & Helfer\n\n"]
    out.append("## Skripte\n\n")
    if scripts:
        out.append("Skripte sind gespeicherte Abläufe, die per Knopf, Sprachbefehl oder aus Automationen gestartet werden.\n\n")
        out.append("| Skript | Was es tut |\n|---|---|\n")
        for key in sorted(scripts, key=lambda k: str((scripts[k] or {}).get("alias") or k).casefold() if isinstance(scripts[k], dict) else str(k)):
            script = scripts[key]
            if not isinstance(script, dict):
                continue
            alias = ctx.safe_text(script.get("alias") or key, "Skriptname")
            description = ctx.safe_text(script.get("description"), "Skriptbeschreibung") if script.get("description") else "Keine Beschreibung hinterlegt."
            out.append(f"| {ctx.esc(alias)} | {ctx.esc(description)} |\n")
        out.append("\n")
    else:
        out.append("Im Backup sind keine Skripte hinterlegt.\n\n")
    out.append("## Helfer\n\n")
    if helpers:
        out.append("Helfer speichern Werte oder Schalter, die Automationen nutzen, etwa einen Urlaubsmodus oder einen Zeitplan.\n\n")
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for entity in helpers:
            grouped[HELPER_PLATFORMS[str(entity["platform"])]].append(entity)
        for label in sorted(grouped):
            items = sorted(grouped[label], key=lambda e: ctx.entity_label(e["entity_id"]).casefold())
            out.append(f"**{label}** ({len(items)}): " + ", ".join(ctx.entity_label(e["entity_id"]) for e in items) + "\n\n")
        out.append("??? info \"Technische Namen der Helfer\"\n\n")
        for entity in sorted(helpers, key=lambda e: e["entity_id"]):
            out.append(f"    - {ctx.entity_label(entity['entity_id'], True)}\n")
        out.append("\n")
    else:
        out.append("Im Backup sind keine Helfer hinterlegt.\n\n")
    out.append(_footer(ctx.source_note))
    (tech / "skripte-helfer.md").write_text("".join(out), encoding="utf-8")
    return {
        "integrations": len(integrations),
        "apps": len(apps),
        "zigbee_devices": len(zigbee),
        "scripts": len(scripts),
        "helpers": len(helpers),
    }


def write_extra_pages(ctx: ExtraContext) -> dict[str, Any]:
    inventory = _read_inventory(ctx.source)
    inv = Inventory(ctx)
    integrations = inv.integrations()
    manual_pages = {path.stem for path in (ctx.docs / "manuell").glob("*.md")} if (ctx.docs / "manuell").is_dir() else set()
    batteries = write_maintenance(ctx, inv, inventory)
    write_energy(ctx, inv)
    write_emergency(ctx, inv, integrations, manual_pages)
    counts = write_technology(ctx, inv, integrations, inventory)
    return {
        "battery_devices": batteries,
        "homeassistant_version": inventory.get("homeassistant_version"),
        **counts,
    }
