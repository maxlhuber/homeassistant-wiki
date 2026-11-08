"""Battery types for common smart-home devices.

The wiki and the live view share this table.  Each entry is matched against the
manufacturer and model reported by Home Assistant.  ``certainty`` is shown to
readers so a typical value is never presented as a confirmed specification:

* ``hersteller`` – the model has exactly one documented battery type.
* ``typisch`` – the type is common for this model family but variants exist;
  the reader is asked to check before buying.

Values entered by the administrator in the app always win.  They are stored in
``/data/battery_types.json`` keyed by the Home Assistant device ID.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAX_TYPE_LENGTH = 40
ALLOWED_TYPE = re.compile(r"^[\w ×x+.,/()\-–]{1,40}$", re.UNICODE)
COUNT_AND_CELL = re.compile(r"^\s*(\d{1,2})\s*[×x]\s*([A-Za-z0-9-]+)\s*$")


@dataclass(frozen=True)
class BatteryInfo:
    type: str
    certainty: str  # hersteller | typisch | eingetragen | unbekannt
    note: str = ""

    @property
    def label(self) -> str:
        return {
            "hersteller": "Herstellerangabe",
            "typisch": "typisch – bitte prüfen",
            "eingetragen": "selbst eingetragen",
        }.get(self.certainty, "noch nicht bekannt")


# (manufacturer contains, model contains, type, certainty, note)
LIBRARY: tuple[tuple[str, str, str, str, str], ...] = (
    ("philips", "wall switch module", "1× CR2450", "hersteller", ""),
    ("philips", "dimmer switch", "1× CR2032", "typisch", "ältere Modelle: CR2450"),
    ("philips", "smart button", "1× CR2032", "hersteller", ""),
    ("philips", "tap dial", "1× CR2032", "hersteller", ""),
    ("philips", "motion sensor", "2× AAA", "hersteller", ""),
    ("ikea", "shortcut button", "1× CR2032", "hersteller", ""),
    ("ikea", "styrbar", "2× AAA", "hersteller", ""),
    ("ikea", "rodret", "1× AAA", "hersteller", ""),
    ("ikea", "remote control", "1× CR2032", "hersteller", ""),
    ("ikea", "on/off switch", "1× CR2032", "hersteller", ""),
    ("ikea", "motion sensor", "2× CR2032", "typisch", ""),
    ("osram", "switch mini", "1× CR2450", "hersteller", ""),
    ("ledvance", "switch mini", "1× CR2450", "hersteller", ""),
    ("sonoff", "water valve", "2× AA", "hersteller", ""),
    ("sonoff", "snzb-02", "1× CR2450", "typisch", ""),
    ("sonoff", "snzb-03", "1× CR2450", "typisch", ""),
    ("sonoff", "snzb-04", "1× CR2032", "typisch", ""),
    ("sonoff", "contact sensor", "1× CR2032", "typisch", ""),
    ("ewelink", "contact sensor", "1× CR2032", "typisch", ""),
    ("tuya", "smart knob", "1× CR2032", "typisch", ""),
    ("tuya", "fingerbot", "eingebauter Akku", "typisch", "per USB-C laden"),
    ("tuya", "door/window sensor", "1× CR2032", "typisch", "manche Varianten: 2× AAA"),
    ("tuya", "lcd sensor", "2× AAA", "typisch", "manche Varianten: CR2032"),
    ("tuya", "temperature and humidity sensor", "1× CR2032", "typisch", ""),
    ("tuya", "temperature & humidity sensor", "1× CR2032", "typisch", ""),
    ("aqara", "wireless mini switch", "1× CR2032", "hersteller", ""),
    ("aqara", "door and window sensor", "1× CR1632", "hersteller", ""),
    ("aqara", "temperature and humidity sensor", "1× CR2032", "hersteller", ""),
    ("aqara", "motion sensor", "1× CR2450", "hersteller", ""),
    ("nuki", "smart lock 3.0 (pro)", "Nuki Power Pack (Akku)", "hersteller", "per USB-C laden"),
    ("nuki", "smart lock 4", "Nuki Power Pack oder 4× AA", "typisch", ""),
    ("nuki", "smart lock", "4× AA oder Nuki Power Pack", "typisch", ""),
    ("nuki", "opener", "4× AAA", "typisch", "alternativ per USB-Netzteil"),
    ("withings", "body", "4× AAA", "hersteller", ""),
)


def _matches(manufacturer: str, model: str, maker_part: str, model_part: str) -> bool:
    return maker_part in manufacturer and model_part in model


def library_type(manufacturer: Any, model: Any) -> BatteryInfo | None:
    maker = str(manufacturer or "").casefold()
    shown_model = str(model or "").casefold()
    for maker_part, model_part, kind, certainty, note in LIBRARY:
        if _matches(maker, shown_model, maker_part, model_part):
            return BatteryInfo(kind, certainty, note)
    return None


def clean_type(value: Any) -> str | None:
    """Validate an administrator entry; ``None`` removes it."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    text = re.sub(r"(?<=\d)\s*[xX]\s*", "× ", text)
    if len(text) > MAX_TYPE_LENGTH or not ALLOWED_TYPE.fullmatch(text):
        raise ValueError(
            "Bitte nur einen kurzen Batterietyp eintragen, z. B. „2× AAA“ oder „1× CR2032“."
        )
    return text


def load_overrides(path: Path | None) -> dict[str, str]:
    if path is None or not path.is_file() or path.is_symlink():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    devices = document.get("devices") if isinstance(document, dict) else None
    if not isinstance(devices, dict):
        return {}
    result: dict[str, str] = {}
    for device_id, value in devices.items():
        if not isinstance(device_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", device_id):
            continue
        try:
            cleaned = clean_type(value)
        except ValueError:
            continue
        if cleaned:
            result[device_id] = cleaned
    return result


def save_overrides(path: Path, devices: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    document = {"devices": {key: devices[key] for key in sorted(devices)}}
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def battery_info(
    device_id: str | None,
    manufacturer: Any,
    model: Any,
    overrides: dict[str, str],
) -> BatteryInfo:
    if device_id and device_id in overrides:
        return BatteryInfo(overrides[device_id], "eingetragen")
    return library_type(manufacturer, model) or BatteryInfo("", "unbekannt")


def shopping_list(types: list[str]) -> list[tuple[str, int]]:
    """Sum simple ``n× CELL`` entries into a stock list; other values count once."""
    totals: dict[str, int] = {}
    for value in types:
        match = COUNT_AND_CELL.match(value or "")
        if match:
            cell = match.group(2).upper()
            totals[cell] = totals.get(cell, 0) + int(match.group(1))
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))
