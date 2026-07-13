"""Generate sanitized Wiki pages from an extracted Home Assistant backup.

The source directory must contain the selected YAML files and registry files from
Home Assistant. The script deliberately does not read config entries, secrets,
credentials, history databases, cloud data, or device identifiers.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


GENERATED_NOTICE = (
    "<!-- Automatisch aus einem lokalen Home-Assistant-Backup erzeugt. "
    "Nicht direkt bearbeiten. -->\n\n"
)
ENTITY_RE = re.compile(r"\b[a-z_]+\.[a-z0-9_]+\b")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def read_yaml(path: Path, default: Any) -> Any:
    if not path.exists() or path.stat().st_size == 0:
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


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


def listify(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def duration(value: Any) -> str:
    if isinstance(value, dict):
        parts = []
        for key, label in (("hours", "Std."), ("minutes", "Min."), ("seconds", "Sek.")):
            if value.get(key):
                parts.append(f"{value[key]} {label}")
        return " ".join(parts) or "festgelegte Dauer"
    return str(value)


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("docs", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    docs = args.docs.resolve()
    if not source.is_dir() or not docs.is_dir():
        raise SystemExit("Quell- oder Dokumentationsordner fehlt.")

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

    def area_id_for_device(device: dict[str, Any]) -> str | None:
        return device.get("area_id")

    def area_id_for_entity(entity: dict[str, Any]) -> str | None:
        return entity.get("area_id") or area_id_for_device(device_by_id.get(entity.get("device_id"), {}))

    def device_name(device_id: str | None) -> str:
        device = device_by_id.get(device_id or "", {})
        return device.get("name_by_user") or device.get("name") or "unbekanntes Gerät"

    def entity_name(entity_id: str) -> str:
        entity = entity_by_id.get(entity_id, {})
        label = entity.get("name") or entity.get("original_name")
        return f"{label} (`{entity_id}`)" if label else f"`{entity_id}`"

    def names_for(value: Any) -> str:
        values = listify(value)
        result = []
        for item in values:
            if isinstance(item, str) and item in entity_by_id:
                result.append(entity_name(item))
            elif isinstance(item, str) and item in entity_by_registry_id:
                result.append(entity_name(entity_by_registry_id[item]["entity_id"]))
            elif isinstance(item, str) and item in device_by_id:
                result.append(device_name(item))
            elif isinstance(item, str) and item in area_by_id:
                result.append(area_by_id[item]["name"])
            else:
                result.append(f"`{item}`" if isinstance(item, str) else str(item))
        return ", ".join(result) or "nicht näher angegeben"

    def trigger_summary(item: dict[str, Any]) -> str:
        kind = item.get("trigger") or item.get("platform") or "unbekannt"
        raw_target = item.get("entity_id") or item.get("device_id")
        if not raw_target and isinstance(item.get("target"), dict):
            raw_target = item["target"].get("entity_id") or item["target"].get("device_id") or item["target"].get("area_id")
        target = names_for(raw_target)
        if kind == "state":
            change = []
            if item.get("from") is not None:
                change.append(f"von `{item['from']}`")
            if item.get("to") is not None:
                change.append(f"auf `{item['to']}`")
            hold = f" für {duration(item['for'])}" if item.get("for") else ""
            return f"Status von {target} ändert sich {' '.join(change)}{hold}".strip()
        if kind == "numeric_state":
            limits = []
            if item.get("above") is not None:
                limits.append(f"über {item['above']}")
            if item.get("below") is not None:
                limits.append(f"unter {item['below']}")
            return f"Messwert von {target} liegt {' und '.join(limits)}"
        if kind == "time":
            return f"Zeitpunkt {names_for(item.get('at'))} ist erreicht"
        if kind == "time_pattern":
            return "regelmäßiges Zeitmuster ist erreicht"
        if kind == "sun":
            return f"{item.get('event', 'Sonnenstand')} ist erreicht"
        if kind == "device":
            return f"Geräteereignis „{item.get('type', 'Ereignis')}“ von {target}"
        if kind == "event":
            return f"Ereignis `{item.get('event_type', 'unbekannt')}` tritt ein"
        if kind == "mqtt":
            return f"MQTT-Nachricht am Thema `{item.get('topic', 'nicht angegeben')}`"
        if kind == "template":
            return "eine festgelegte Vorlagenbedingung wird wahr"
        semantic = {
            "occupancy.detected": "Anwesenheit wird erkannt",
            "occupancy.cleared": "keine Anwesenheit wird mehr erkannt",
            "motion.detected": "Bewegung wird erkannt",
            "motion.cleared": "keine Bewegung wird mehr erkannt",
        }
        if kind in semantic:
            return f"{semantic[kind]} bei {target}"
        return f"Auslöser `{kind}` bei {target}"

    def condition_summary(item: dict[str, Any]) -> str:
        kind = item.get("condition", "unbekannt")
        target = names_for(item.get("entity_id") or item.get("device_id"))
        if kind == "state":
            return f"{target} hat den Status `{item.get('state', 'festgelegt')}`"
        if kind == "numeric_state":
            limits = []
            if item.get("above") is not None:
                limits.append(f"über {item['above']}")
            if item.get("below") is not None:
                limits.append(f"unter {item['below']}")
            return f"{target} liegt {' und '.join(limits)}"
        if kind == "time":
            return "der festgelegte Zeitraum ist aktiv"
        if kind == "sun":
            return "der festgelegte Sonnenstand ist erreicht"
        if kind == "template":
            return "eine interne Vorlagenprüfung ist erfüllt"
        if kind in ("and", "or", "not"):
            return f"logische Bedingungsgruppe `{kind}` ist erfüllt"
        return f"Bedingung `{kind}` ist erfüllt"

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
        return ", ".join(parts) or "festgelegtes Ziel"

    def action_summary(item: dict[str, Any]) -> str:
        service = item.get("action") or item.get("service")
        if service:
            if str(service).startswith("notify.mobile_app_"):
                recipient = str(service).removeprefix("notify.mobile_app_").replace("_", " ")
                recipient = {"max iphone": "Max' iPhone", "meikes iphone": "Meikes iPhone"}.get(recipient, recipient)
                return f"Push-Nachricht an {recipient} senden"
            readable = {
                "turn_on": "einschalten",
                "turn_off": "ausschalten",
                "toggle": "umschalten",
                "open_cover": "öffnen",
                "close_cover": "schließen",
                "open": "öffnen",
                "notify": "benachrichtigen",
            }
            verb = readable.get(str(service).split(".")[-1], f"Dienst `{service}` ausführen")
            addition = ""
            data = item.get("data") or {}
            if data.get("brightness_pct") is not None:
                addition = f" mit {data['brightness_pct']} % Helligkeit"
            return f"{target_summary(item)} {verb}{addition}"
        if "delay" in item:
            return f"{duration(item['delay'])} warten"
        if "choose" in item:
            return f"zwischen {len(item.get('choose') or [])} Ablaufvarianten wählen"
        if "if" in item:
            checks = [condition_summary(x) for x in listify(item.get("if")) if isinstance(x, dict)]
            then_steps = [action_summary(x) for x in listify(item.get("then")) if isinstance(x, dict) and x.get("enabled", True)]
            else_all = [x for x in listify(item.get("else")) if isinstance(x, dict)]
            else_steps = [action_summary(x) for x in else_all if x.get("enabled", True)]
            text = f"wenn {checks[0].lower() if checks else 'die interne Bedingung erfüllt ist'}, dann {then_steps[0].lower() if then_steps else 'keinen aktiven Schritt ausführen'}"
            if else_steps:
                text += f"; andernfalls {else_steps[0].lower()}"
            elif else_all:
                text += "; der andernfalls vorgesehene Schritt ist derzeit deaktiviert"
            return text
        if "repeat" in item:
            return "eine festgelegte Schrittfolge wiederholen"
        if "wait_template" in item or "wait_for_trigger" in item:
            return "auf eine festgelegte Bedingung warten"
        if "device_id" in item:
            return f"Geräteaktion „{item.get('type', 'festgelegt')}“ bei {device_name(item.get('device_id'))}"
        return "einen internen Verarbeitungsschritt ausführen"

    def referenced_ids(value: Any) -> tuple[set[str], set[str]]:
        entity_ids: set[str] = set()
        device_ids: set[str] = set()
        def walk(node: Any) -> None:
            if isinstance(node, dict):
                for key, val in node.items():
                    if key == "device_id":
                        device_ids.update(str(x) for x in listify(val))
                    if key == "entity_id":
                        entity_ids.update(str(x) for x in listify(val))
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
        return translated.intersection(entity_by_id), device_ids.intersection(device_by_id)

    auto_dir = docs / "automationen" / "generated"
    room_dir = docs / "raeume" / "generated"
    for directory in (auto_dir, room_dir):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)

    slug_counts: Counter[str] = Counter()
    auto_meta: list[dict[str, Any]] = []
    for automation in automations:
        alias = automation.get("alias") or "Automation ohne Namen"
        base_slug = slugify(alias)
        slug_counts[base_slug] += 1
        slug = base_slug if slug_counts[base_slug] == 1 else f"{base_slug}-{slug_counts[base_slug]}"
        triggers = listify(automation.get("triggers") or automation.get("trigger"))
        conditions = listify(automation.get("conditions") or automation.get("condition"))
        actions = listify(automation.get("actions") or automation.get("action"))
        entity_ids, device_ids = referenced_ids(automation)
        blueprint = automation.get("use_blueprint")
        trigger_lines = [trigger_summary(x) for x in triggers if isinstance(x, dict)]
        condition_lines = [condition_summary(x) for x in conditions if isinstance(x, dict)]
        action_lines = [action_summary(x) for x in actions if isinstance(x, dict)]
        if blueprint:
            trigger_lines = ["Die Auslöser werden durch einen Blueprint festgelegt."]
            action_lines = ["Der Ablauf wird durch einen Blueprint festgelegt."]

        page = [GENERATED_NOTICE, f"# {alias}\n"]
        page.append("## Kurz erklärt\n")
        if automation.get("description"):
            page.append(f"{automation['description']}\n")
        elif trigger_lines and action_lines:
            page.append(f"Wenn {trigger_lines[0].lower()}, wird anschließend {action_lines[0].lower()}.\n")
        else:
            page.append("Diese Automation führt einen festgelegten Smart-Home-Ablauf aus.\n")
        page.append("## Auslöser\n")
        page.extend(f"{i}. {text}\n" for i, text in enumerate(trigger_lines or ["Noch nicht automatisch lesbar"], 1))
        page.append("\n## Bedingungen\n")
        if condition_lines:
            page.extend(f"- {text}\n" for text in condition_lines)
        else:
            page.append("Keine zusätzlichen Bedingungen in der Automation hinterlegt.\n")
        page.append("\n## Ablauf\n")
        page.extend(f"{i}. {text}\n" for i, text in enumerate(action_lines or ["Noch nicht automatisch lesbar"], 1))
        page.append("\n## Manuelle Bedienung\n")
        page.append("Noch zu ergänzen: Wie lässt sich diese Funktion von Hand auslösen oder übersteuern?\n")
        if blueprint:
            page.append("\n## Blueprint\n")
            page.append(f"Technische Vorlage: `{blueprint.get('path', 'nicht angegeben')}`\n")
        page.append("\n## Technische Angaben\n")
        page.append("| Feld | Wert |\n|---|---|\n")
        page.append(f"| Home-Assistant-ID | `{esc(automation.get('id'))}` |\n")
        page.append(f"| Modus | `{esc(automation.get('mode', 'single'))}` |\n")
        page.append(f"| Kategorie | {category(alias)} |\n")
        if entity_ids:
            page.append(f"| Verwendete Entities | {', '.join(entity_name(x) for x in sorted(entity_ids)[:30])} |\n")
        page.append("\n<p class=\"page-status\">Automatisch erfasst: 12. Juli 2026 · Manuelle Erklärung noch zu prüfen</p>\n")
        (auto_dir / f"{slug}.md").write_text("".join(page), encoding="utf-8")
        auto_meta.append({"alias": alias, "slug": slug, "category": category(alias), "entities": entity_ids, "devices": device_ids})

    categories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in auto_meta:
        categories[item["category"]].append(item)
    auto_index = [GENERATED_NOTICE, "# Automationen\n\n"]
    auto_index.append(f"Aktuell sind **{len(automations)} Automationen** dokumentiert. Die Seiten wurden aus der Sicherung vom 12. Juli 2026 erzeugt.\n\n")
    auto_index.append("!!! info \"Automatisch erfasst\"\n    Auslöser, Bedingungen und Aktionen stammen aus Home Assistant. Die alltagstaugliche Erklärung und die manuelle Alternative werden anschließend gemeinsam geprüft.\n\n")
    order = ["Licht & Präsenz", "Sicherheit & Zugang", "Garten & Wasser", "Energie & Auto", "Haushalt", "System", "Sonstiges"]
    for group in order:
        if group not in categories:
            continue
        auto_index.append(f"## {group}\n\n")
        for item in sorted(categories[group], key=lambda x: x["alias"].casefold()):
            auto_index.append(f"- [{item['alias']}](generated/{item['slug']}.md)\n")
        auto_index.append("\n")
    auto_index.append("## Szenen\n\n")
    if scenes:
        auto_index.append("| Szene | Enthaltene Zustände |\n|---|---:|\n")
        for scene in scenes:
            auto_index.append(f"| {esc(scene.get('name'))} | {len(scene.get('entities') or {})} |\n")
    else:
        auto_index.append("Keine Szenen vorhanden.\n")
    auto_index.append("\n<p class=\"page-status\">Zuletzt aus Home Assistant übernommen: 12. Juli 2026</p>\n")
    (docs / "automationen" / "index.md").write_text("".join(auto_index), encoding="utf-8")

    area_devices: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for device in devices:
        area_devices[area_id_for_device(device)].append(device)
    area_entities: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for entity in entities:
        area_entities[area_id_for_entity(entity)].append(entity)

    room_slug: dict[str, str] = {area["id"]: slugify(area["name"]) for area in areas}
    for area in areas:
        area_id = area["id"]
        floor = floor_by_id.get(area.get("floor_id") or "", {}).get("name") or "Keine Etage zugeordnet"
        if floor == "Ergeschoss":
            floor = "Erdgeschoss"
        room_devices = sorted(area_devices[area_id], key=lambda x: device_name(x.get("id")).casefold())
        room_entities = area_entities[area_id]
        related = []
        room_entity_ids = {x["entity_id"] for x in room_entities}
        room_device_ids = {x["id"] for x in room_devices}
        for item in auto_meta:
            if item["entities"] & room_entity_ids or item["devices"] & room_device_ids:
                related.append(item)
        domains = Counter(x["entity_id"].split(".", 1)[0] for x in room_entities)
        page = [GENERATED_NOTICE, f"# {area['name']}\n\n"]
        page.append(f"**Etage:** {floor}  \n**Erfasste Geräte:** {len(room_devices)}  \n**Erfasste Entities:** {len(room_entities)}\n\n")
        page.append("## Geräte\n\n")
        if room_devices:
            page.append("| Gerät | Hersteller / Modell | Anbindung |\n|---|---|---|\n")
            for device in room_devices:
                platforms = sorted({e.get("platform") for e in device_entities[device["id"]] if e.get("platform")})
                maker = " / ".join(x for x in (device.get("manufacturer"), device.get("model")) if x) or "–"
                page.append(f"| {esc(device_name(device['id']))} | {esc(maker)} | {esc(', '.join(platforms))} |\n")
        else:
            page.append("Keine Geräte direkt diesem Raum zugeordnet.\n")
        page.append("\n## Wichtige Funktionen\n\n")
        if domains:
            page.append(", ".join(f"**{domain}:** {count}" for domain, count in domains.most_common(12)) + "\n")
        else:
            page.append("Noch keine Funktionen erfasst.\n")
        page.append("\n## Zugehörige Automationen\n\n")
        if related:
            for item in sorted(related, key=lambda x: x["alias"].casefold()):
                page.append(f"- [{item['alias']}](../../automationen/generated/{item['slug']}.md)\n")
        else:
            page.append("Keine Automation konnte diesem Raum automatisch zugeordnet werden.\n")
        page.append("\n## Manuelle Bedienung\n\nNoch zu ergänzen: wichtigste Schalter, Bedienelemente und Verhalten bei einem Ausfall.\n")
        page.append("\n<p class=\"page-status\">Automatisch erfasst: 12. Juli 2026 · Manuelle Angaben noch zu ergänzen</p>\n")
        (room_dir / f"{room_slug[area_id]}.md").write_text("".join(page), encoding="utf-8")

    floor_areas: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for area in areas:
        floor_areas[area.get("floor_id")].append(area)
    room_index = [GENERATED_NOTICE, "# Räume\n\n"]
    room_index.append(f"Home Assistant enthält **{len(floors)} Etagen** und **{len(areas)} Räume beziehungsweise Bereiche**.\n\n")
    for floor in sorted(floors, key=lambda x: (x.get("level") is None, x.get("level") or 0)):
        shown_name = "Erdgeschoss" if floor.get("name") == "Ergeschoss" else floor.get("name")
        room_index.append(f"## {shown_name}\n\n")
        if floor.get("name") == "Ergeschoss":
            room_index.append("!!! note \"Bezeichnung in Home Assistant\"\n    Die Etage heißt dort derzeit „Ergeschoss“. Im Wiki wird die vermutlich gemeinte Schreibweise „Erdgeschoss“ verwendet.\n\n")
        for area in sorted(floor_areas[floor["floor_id"]], key=lambda x: x["name"].casefold()):
            room_index.append(f"- [{area['name']}](generated/{room_slug[area['id']]}.md) – {len(area_devices[area['id']])} Geräte\n")
        room_index.append("\n")
    if floor_areas[None]:
        room_index.append("## Ohne Etage\n\n")
        for area in sorted(floor_areas[None], key=lambda x: x["name"].casefold()):
            room_index.append(f"- [{area['name']}](generated/{room_slug[area['id']]}.md) – {len(area_devices[area['id']])} Geräte\n")
    room_index.append("\n<p class=\"page-status\">Zuletzt aus Home Assistant übernommen: 12. Juli 2026</p>\n")
    (docs / "raeume" / "index.md").write_text("".join(room_index), encoding="utf-8")

    manufacturers = Counter((d.get("manufacturer") or "Unbekannt") for d in devices)
    unassigned = area_devices[None]
    device_index = [GENERATED_NOTICE, "# Geräte\n\n"]
    device_index.append(f"In Home Assistant sind **{len(devices)} Geräte** und **{len(entities)} Entities** registriert. Davon sind **{len(unassigned)} Geräte keinem Raum zugeordnet**.\n\n")
    device_index.append("## Häufigste Hersteller\n\n| Hersteller | Geräte |\n|---|---:|\n")
    for maker, count in manufacturers.most_common(20):
        device_index.append(f"| {esc(maker)} | {count} |\n")
    device_index.append("\n## Nicht zugeordnete Geräte\n\n")
    device_index.append("Diese Liste sollte geprüft werden. Virtuelle Dienste benötigen nicht zwingend einen Raum; physische Geräte sollten nach Möglichkeit zugeordnet werden.\n\n")
    device_index.append("| Gerät | Hersteller / Modell |\n|---|---|\n")
    for device in sorted(unassigned, key=lambda x: device_name(x["id"]).casefold()):
        maker = " / ".join(x for x in (device.get("manufacturer"), device.get("model")) if x) or "–"
        device_index.append(f"| {esc(device_name(device['id']))} | {esc(maker)} |\n")
    device_index.append("\n<p class=\"page-status\">Zuletzt aus Home Assistant übernommen: 12. Juli 2026</p>\n")
    (docs / "geraete" / "index.md").write_text("".join(device_index), encoding="utf-8")

    summary = {
        "floors": len(floors), "areas": len(areas), "labels": len(labels),
        "devices": len(devices), "entities": len(entities),
        "automations": len(automations), "scenes": len(scenes),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
