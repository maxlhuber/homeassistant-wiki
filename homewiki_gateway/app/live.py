"""Live household status for the app: batteries, silent devices, updates, backup.

The wiki itself stays backup-based.  This module asks Home Assistant for the
current state through the Supervisor proxy and returns a small, display-ready
summary.  It never returns attributes beyond the fields selected here.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import threading
import time
from pathlib import Path
from typing import Any

try:
    from .wiki_batteries import battery_info, clean_type, load_overrides, save_overrides
except ImportError:  # pragma: no cover - packaged fallback
    from wiki_batteries import battery_info, clean_type, load_overrides, save_overrides
from .supervisor import SupervisorError, core_json_request, json_request


BATTERY_TYPES = Path("/data/battery_types.json")
CACHE_SECONDS = 60
LOW_PERCENT = 20
WARN_PERCENT = 35
MOBILE_DOMAINS = {"mobile_app", "icloud", "pycupra", "volkswagencarnet"}
SKIP_OFFLINE_DOMAINS = MOBILE_DOMAINS | {
    "hassio", "hacs", "openai_conversation", "google_generative_ai_conversation",
    "telegram_bot", "smtp", "bring", "backup", "sun", "met", "openweathermap",
}
ROBOT_WORDS = ("vacuum", "saug", "narwal", "roborock", "dreame", "mower", "mäh")
DEVICE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# One template call collects everything; Home Assistant resolves device, area
# and integration for each entity.  Only plain values are emitted.
TEMPLATE = r"""
{%- set ns = namespace(b=[], o=[], u=[], seen=[]) -%}
{%- for s in states.sensor | list + states.binary_sensor | list -%}
  {%- set dc = s.attributes.get('device_class', '') -%}
  {%- if dc == 'battery' or (s.entity_id is search('_batter(y|ie)(_level|_state|_percentage)?$') and dc != 'voltage') -%}
    {%- set did = device_id(s.entity_id) -%}
    {%- if did -%}
      {%- set ns2 = namespace(dom=[]) -%}
      {%- for i in device_attr(did, 'identifiers') or [] -%}{%- set ns2.dom = ns2.dom + [i[0] ~ ''] -%}{%- endfor -%}
      {%- set ns.b = ns.b + [{
        'device': did,
        'name': device_attr(did, 'name_by_user') or device_attr(did, 'name') or s.name,
        'area': area_name(did) or area_name(s.entity_id) or '',
        'manufacturer': device_attr(did, 'manufacturer') or '',
        'model': device_attr(did, 'model') or '',
        'domains': ns2.dom,
        'domain': s.domain,
        'state': s.state,
        'unit': s.attributes.get('unit_of_measurement', ''),
        'changed': s.last_changed.isoformat()
      }] -%}
    {%- endif -%}
  {%- endif -%}
{%- endfor -%}
{%- for s in states | selectattr('state', 'eq', 'unavailable') -%}
  {%- set did = device_id(s.entity_id) -%}
  {%- if did and did not in ns.seen -%}
    {%- set ns.seen = ns.seen + [did] -%}
    {%- set ents = device_entities(did) -%}
    {%- set alive = ents | map('states') | reject('in', ['unavailable', 'unknown', None, '']) | list -%}
    {%- if ents | length > 0 and alive | length == 0 and device_attr(did, 'entry_type') != 'service' -%}
      {%- set ns2 = namespace(dom=[]) -%}
      {%- for i in device_attr(did, 'identifiers') or [] -%}{%- set ns2.dom = ns2.dom + [i[0] ~ ''] -%}{%- endfor -%}
      {%- set ns.o = ns.o + [{
        'device': did,
        'name': device_attr(did, 'name_by_user') or device_attr(did, 'name') or s.name,
        'area': area_name(did) or '',
        'domains': ns2.dom,
        'changed': s.last_changed.isoformat()
      }] -%}
    {%- endif -%}
  {%- endif -%}
{%- endfor -%}
{%- for s in states.update | selectattr('state', 'eq', 'on') -%}
  {%- set ns.u = ns.u + [{
    'name': s.attributes.get('title') or s.name,
    'installed': s.attributes.get('installed_version') or '',
    'latest': s.attributes.get('latest_version') or ''
  }] -%}
{%- endfor -%}
{{ {'batteries': ns.b, 'offline': ns.o, 'updates': ns.u} | tojson }}
"""


def _text(value: Any, limit: int = 120) -> str:
    return " ".join(str(value or "").split())[:limit]


def _level(state: str, domain: str) -> tuple[float | None, str]:
    """Return percentage (if numeric) and one of ok | warn | low | unknown."""
    value = (state or "").strip().casefold()
    if domain == "binary_sensor":
        return None, "low" if value == "on" else "ok" if value == "off" else "unknown"
    try:
        number = float(value)
    except ValueError:
        return None, {"low": "low", "medium": "warn", "high": "ok", "full": "ok", "charging": "ok"}.get(value, "unknown")
    number = max(0.0, min(100.0, number))
    return number, "low" if number <= LOW_PERCENT else "warn" if number <= WARN_PERCENT else "ok"


def _is_robot(name: str, model: str) -> bool:
    text = f"{name} {model}".casefold()
    return any(word in text for word in ROBOT_WORDS)


def build_live(raw: dict[str, Any], overrides: dict[str, str], backup: dict[str, Any] | None, core_version: str | None, now: dt.datetime | None = None) -> dict[str, Any]:
    now = now or dt.datetime.now(dt.timezone.utc)
    batteries: dict[str, dict[str, Any]] = {}
    for item in raw.get("batteries") or []:
        if not isinstance(item, dict) or not DEVICE_ID.fullmatch(str(item.get("device") or "")):
            continue
        if set(item.get("domains") or []) & MOBILE_DOMAINS:
            continue
        percent, level = _level(str(item.get("state")), str(item.get("domain")))
        device_id = str(item["device"])
        name = _text(item.get("name"))
        model = _text(item.get("model"))
        if _is_robot(name, model):
            info = {"type": "eingebauter Akku", "certainty": "hersteller", "label": "Herstellerangabe", "note": "lädt in der Station"}
        else:
            found = battery_info(device_id, item.get("manufacturer"), item.get("model"), overrides)
            info = {"type": found.type, "certainty": found.certainty, "label": found.label, "note": found.note}
        entry = {
            "device": device_id,
            "name": name,
            "area": _text(item.get("area")),
            "percent": percent,
            "state": _text(item.get("state"), 20),
            "level": level,
            "changed": _text(item.get("changed"), 40),
            **info,
        }
        previous = batteries.get(device_id)
        # Prefer the numeric percentage over a text state for the same device.
        if previous is None or (previous["percent"] is None and percent is not None):
            batteries[device_id] = entry
    order = {"low": 0, "warn": 1, "unknown": 2, "ok": 3}
    battery_list = sorted(
        batteries.values(),
        key=lambda e: (order.get(e["level"], 9), e["percent"] if e["percent"] is not None else 101, e["name"].casefold()),
    )

    offline = []
    for item in raw.get("offline") or []:
        if not isinstance(item, dict) or not DEVICE_ID.fullmatch(str(item.get("device") or "")):
            continue
        if set(item.get("domains") or []) & SKIP_OFFLINE_DOMAINS:
            continue
        offline.append({
            "device": str(item["device"]),
            "name": _text(item.get("name")),
            "area": _text(item.get("area")),
            "since": _text(item.get("changed"), 40),
        })
    offline.sort(key=lambda e: (e["area"].casefold() or "~", e["name"].casefold()))

    updates = [
        {"name": _text(u.get("name")), "installed": _text(u.get("installed"), 40), "latest": _text(u.get("latest"), 40)}
        for u in raw.get("updates") or [] if isinstance(u, dict)
    ]
    updates.sort(key=lambda u: u["name"].casefold())

    backup_info = None
    if backup and backup.get("date"):
        try:
            stamp = dt.datetime.fromisoformat(str(backup["date"]).replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=dt.timezone.utc)
            hours = max(0, round((now - stamp).total_seconds() / 3600))
            backup_info = {"date": stamp.isoformat(), "age_hours": hours, "level": "ok" if hours <= 48 else "warn" if hours <= 24 * 8 else "low"}
        except (TypeError, ValueError):
            backup_info = None

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "core_version": _text(core_version, 40) or None,
        "batteries": battery_list,
        "offline": offline,
        "updates": updates,
        "backup": backup_info,
        "summary": {
            "batteries_low": sum(1 for b in battery_list if b["level"] == "low"),
            "batteries_warn": sum(1 for b in battery_list if b["level"] == "warn"),
            "batteries_untyped": sum(1 for b in battery_list if b["certainty"] == "unbekannt"),
            "offline": len(offline),
            "updates": len(updates),
        },
    }


def _latest_backup() -> dict[str, Any] | None:
    data = json_request("/backups") or {}
    items = [item for item in (data.get("backups") or []) if isinstance(item, dict) and item.get("date")]
    if not items:
        return None

    def stamp(item: dict[str, Any]) -> float:
        try:
            return dt.datetime.fromisoformat(str(item["date"]).replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            return float("-inf")

    return max(items, key=stamp)


class LiveStatus:
    def __init__(self, battery_file: Path = BATTERY_TYPES) -> None:
        self.battery_file = battery_file
        self.lock = threading.Lock()
        self.cache: tuple[float, dict[str, Any]] | None = None

    def invalidate(self) -> None:
        with self.lock:
            self.cache = None

    def get(self) -> dict[str, Any]:
        with self.lock:
            if self.cache and time.monotonic() - self.cache[0] < CACHE_SECONDS:
                return self.cache[1]
        try:
            rendered = core_json_request("/template", method="POST", body={"template": TEMPLATE})
            raw = json.loads(rendered) if isinstance(rendered, str) else rendered
            if not isinstance(raw, dict):
                raise SupervisorError("Unerwartete Antwort von Home Assistant.")
        except (SupervisorError, ValueError) as error:
            return {"error": "Home Assistant liefert gerade keine Live-Werte. Bitte gleich noch einmal versuchen.", "detail": type(error).__name__}
        try:
            backup = _latest_backup()
        except SupervisorError:
            backup = None
        try:
            core_version = (core_json_request("/config") or {}).get("version")
        except SupervisorError:
            core_version = None
        value = build_live(raw, load_overrides(self.battery_file), backup, core_version)
        with self.lock:
            self.cache = (time.monotonic(), value)
        return value

    def set_battery_type(self, device_id: str, value: Any) -> str | None:
        if not DEVICE_ID.fullmatch(device_id or ""):
            raise ValueError("Unbekanntes Gerät.")
        cleaned = clean_type(value)
        devices = load_overrides(self.battery_file)
        if cleaned:
            devices[device_id] = cleaned
        else:
            devices.pop(device_id, None)
        save_overrides(self.battery_file, devices)
        self.invalidate()
        return cleaned
