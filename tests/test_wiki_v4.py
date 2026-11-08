"""Version 4: new reader sections, battery types, inventory and live status."""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "homewiki_gateway")]

from test_weekly_pipeline import _registry  # noqa: E402
from generate_docs import main as generate_docs  # noqa: E402
from wiki_backup import ALLOWED_MEMBERS, backup_inventory  # noqa: E402
from wiki_batteries import battery_info, clean_type, load_overrides, save_overrides, shopping_list  # noqa: E402
from wiki_snapshot import SnapshotError, build_snapshot, calculate_delta, load_snapshot  # noqa: E402
from app.live import build_live  # noqa: E402
from app.server import Handler  # noqa: E402


SECRET_IDENTIFIER = "0xa4c1deadbeef0001"


def _write_house(root: Path) -> None:
    storage = root / ".storage"
    storage.mkdir(parents=True)
    files = {
        "core.floor_registry": _registry("floors", [{"floor_id": "eg", "name": "Erdgeschoss"}]),
        "core.area_registry": _registry("areas", [
            {"id": "flur", "name": "Flur", "floor_id": "eg"},
            {"id": "garten", "name": "Garten", "floor_id": "eg"},
        ]),
        "core.label_registry": _registry("labels", []),
        "core.device_registry": _registry("devices", [
            {"id": "bridge", "name": "Zigbee2MQTT Bridge", "manufacturer": "Zigbee2MQTT", "model": "Bridge",
             "identifiers": [["mqtt", "zigbee2mqtt_bridge_0x00124b"]]},
            {"id": "switch-1", "name": "Wandschalter Flur", "manufacturer": "Philips",
             "model": "Hue wall switch module", "area_id": "flur", "sw_version": "2.85.5",
             "identifiers": [["mqtt", f"zigbee2mqtt_{SECRET_IDENTIFIER}"]], "via_device_id": "bridge"},
            {"id": "valve-1", "name": "Wasserventil Garten", "manufacturer": "SONOFF",
             "model": "Zigbee smart water valve", "area_id": "garten",
             "identifiers": [["mqtt", "zigbee2mqtt_0xa4c1000000000002"]], "via_device_id": "bridge"},
            {"id": "smoke-1", "name": "Rauchmelder Flur", "manufacturer": "Tuya", "model": "Smoke sensor",
             "area_id": "flur", "identifiers": [["mqtt", "zigbee2mqtt_0xa4c1000000000003"]]},
            {"id": "lock-1", "name": "Nuki", "manufacturer": "Nuki Home Solutions GmbH",
             "model": "Nuki smart lock 3.0 (pro)", "area_id": "flur", "identifiers": [["nuki", "SECRETNUKI"]]},
            {"id": "lamp-1", "name": "Flur Decke", "manufacturer": "Innr", "model": "GU10 spot",
             "area_id": "flur", "identifiers": [["mqtt", "zigbee2mqtt_0xa4c1000000000004"]]},
            {"id": "phone-1", "name": "Max iPhone", "manufacturer": "Apple", "model": "iPhone18,1",
             "identifiers": [["mobile_app", "x"]]},
            {"id": "router-1", "name": "Speedport Smart 4R Typ A", "manufacturer": "Deutsche Telekom",
             "model": "Speedport Smart 4R Typ A", "identifiers": [["speedport", "x"]]},
        ]),
        "core.entity_registry": _registry("entities", [
            {"id": "e1", "entity_id": "event.wandschalter_flur", "original_name": "Aktion", "device_id": "switch-1", "platform": "mqtt"},
            {"id": "e2", "entity_id": "sensor.wandschalter_flur_battery", "original_name": "Batterie", "device_id": "switch-1", "platform": "mqtt", "original_device_class": "battery"},
            {"id": "e3", "entity_id": "switch.wasserventil_garten", "original_name": "Ventil", "device_id": "valve-1", "platform": "mqtt"},
            {"id": "e4", "entity_id": "sensor.wasserventil_garten_battery", "original_name": "Batterie", "device_id": "valve-1", "platform": "mqtt", "original_device_class": "battery"},
            {"id": "e5", "entity_id": "binary_sensor.rauchmelder_flur_smoke", "original_name": "Rauch", "device_id": "smoke-1", "platform": "mqtt"},
            {"id": "e6", "entity_id": "sensor.rauchmelder_flur_battery_state", "original_name": "Batterie", "device_id": "smoke-1", "platform": "mqtt"},
            {"id": "e7", "entity_id": "lock.nuki", "original_name": "Schloss", "device_id": "lock-1", "platform": "nuki"},
            {"id": "e8", "entity_id": "sensor.nuki_batterie", "original_name": "Batterie", "device_id": "lock-1", "platform": "nuki", "original_device_class": "battery"},
            {"id": "e9", "entity_id": "light.flur_decke", "original_name": "Licht", "device_id": "lamp-1", "platform": "mqtt"},
            {"id": "e10", "entity_id": "sensor.max_iphone_battery_level", "original_name": "Battery", "device_id": "phone-1", "platform": "mobile_app", "original_device_class": "battery"},
            {"id": "e11", "entity_id": "sensor.speedport_status", "original_name": "Status", "device_id": "router-1", "platform": "speedport"},
            {"id": "e12", "entity_id": "input_boolean.urlaubsmodus", "original_name": "Urlaubsmodus", "platform": "input_boolean"},
        ]),
        "energy": json.dumps({"data": {"energy_sources": [{"type": "grid", "flow_from": [{"stat_energy_from": "sensor.nuki_batterie"}]}], "device_consumption": []}}),
    }
    for name, content in files.items():
        (storage / name).write_text(content, encoding="utf-8")
    (root / "automations.yaml").write_text(yaml.safe_dump([{
        "id": "1", "alias": "Garten bewässern",
        "triggers": [{"trigger": "sun", "event": "sunset"}],
        "actions": [{"action": "switch.turn_on", "target": {"entity_id": "switch.wasserventil_garten"}}],
    }], allow_unicode=True), encoding="utf-8")
    (root / "scenes.yaml").write_text("[]\n", encoding="utf-8")
    (root / "scripts.yaml").write_text(yaml.safe_dump({"alles_aus": {"alias": "Alles aus", "description": "Schaltet alle Lichter aus.", "sequence": []}}, allow_unicode=True), encoding="utf-8")
    (root / ".wiki_backup_metadata.json").write_text(json.dumps({
        "homeassistant_version": "2026.11.0",
        "apps": [{"name": "Zigbee2MQTT", "slug": "45df7312_zigbee2mqtt", "version": "2.14.3"}],
    }), encoding="utf-8")


class InventoryTests(unittest.TestCase):
    def test_backup_inventory_keeps_only_app_names_and_versions(self):
        result = backup_inventory({
            "homeassistant": {"version": "2026.11.0", "size": 3.2},
            "addons": [
                {"name": "Zigbee2MQTT", "slug": "z2m", "version": "2.14.3", "size": 99, "options": {"password": "x"}},
                {"slug": "core_mosquitto", "version": "7.1.3"},
                "garbage",
            ],
            "repositories": ["https://example.invalid/private"],
            "extra": {"secret": "x"},
        })
        self.assertEqual(result["homeassistant_version"], "2026.11.0")
        self.assertEqual(result["apps"], [
            {"name": "core_mosquitto", "slug": "core_mosquitto", "version": "7.1.3"},
            {"name": "Zigbee2MQTT", "slug": "z2m", "version": "2.14.3"},
        ])
        self.assertNotIn("repositories", json.dumps(result))
        self.assertEqual(backup_inventory(None), {"homeassistant_version": None, "apps": []})

    def test_whitelist_adds_scripts_and_energy_but_no_config_entries(self):
        self.assertIn("scripts.yaml", ALLOWED_MEMBERS)
        self.assertIn(".storage/energy", ALLOWED_MEMBERS)
        self.assertNotIn(".storage/core.config_entries", ALLOWED_MEMBERS)
        self.assertNotIn("secrets.yaml", ALLOWED_MEMBERS)

    def test_snapshot_tracks_scripts_apps_and_rebuilds_from_version_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            _write_house(source)
            first = build_snapshot(source)
            (source / "scripts.yaml").write_text(yaml.safe_dump({"alles_aus": {"alias": "Alles aus", "sequence": [{"delay": 1}]}}), encoding="utf-8")
            delta = calculate_delta(first, build_snapshot(source))
            self.assertEqual(delta.sections["scripts"]["modified"], ["alles_aus"])
            self.assertTrue(delta.has_changes)
            self.assertIn("45df7312_zigbee2mqtt", first["apps"])
            old = Path(temporary) / "snapshot.json"
            old.write_text(json.dumps({"snapshot_version": 1}), encoding="utf-8")
            self.assertIsNone(load_snapshot(old))
            old.write_text(json.dumps({"snapshot_version": 99}), encoding="utf-8")
            with self.assertRaises(SnapshotError):
                load_snapshot(old)


class BatteryTests(unittest.TestCase):
    def test_library_marks_certainty_and_override_wins(self):
        exact = battery_info("d1", "Philips", "Hue wall switch module", {})
        self.assertEqual((exact.type, exact.certainty), ("1× CR2450", "hersteller"))
        typical = battery_info("d2", "Tuya", "Temperature & humidity LCD sensor", {})
        self.assertEqual(typical.certainty, "typisch")
        self.assertEqual(battery_info("d3", "Tuya", "Smoke sensor", {}).certainty, "unbekannt")
        own = battery_info("d1", "Philips", "Hue wall switch module", {"d1": "1× CR2032"})
        self.assertEqual((own.type, own.certainty, own.label), ("1× CR2032", "eingetragen", "selbst eingetragen"))

    def test_entries_are_validated_and_counted(self):
        self.assertEqual(clean_type(" 2x  AAA "), "2× AAA")
        self.assertIsNone(clean_type("  "))
        for value in ("<script>", "a" * 41, "1× CR2032; rm -rf"):
            with self.assertRaises(ValueError):
                clean_type(value)
        self.assertEqual(shopping_list(["2× AAA", "1× CR2450", "2× AAA", "Nuki Power Pack (Akku)"]), [("AAA", 4), ("CR2450", 1)])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "battery_types.json"
            save_overrides(path, {"dev-1": "2× AA"})
            self.assertEqual(load_overrides(path), {"dev-1": "2× AA"})
            path.write_text(json.dumps({"devices": {"../bad": "1× AA", "ok-2": "<b>"}}), encoding="utf-8")
            self.assertEqual(load_overrides(path), {})


class ReaderSectionTests(unittest.TestCase):
    def test_new_sections_are_generated_secret_free_deterministic_and_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            source = project / "source"
            _write_house(source)
            docs = project / "docs"
            shutil.copytree(ROOT / "homewiki_gateway/runtime/docs", docs)
            (docs / "manuell" / "notfall.md").write_text("# Notfallhinweise\n\nNachbar fragen.\n", encoding="utf-8")
            shutil.copy2(ROOT / "homewiki_gateway/runtime/mkdocs.yml", project / "mkdocs.yml")
            overrides = project / "overrides.yaml"
            overrides.write_text("{}\n", encoding="utf-8")
            battery_file = project / "battery_types.json"
            save_overrides(battery_file, {"smoke-1": "1× CR123A"})
            args = ["generate_docs.py", str(source), str(docs), "--overrides", str(overrides), "--inventory-source-date", "08.11.2026"]
            with patch.dict(os.environ, {"WIKI_BATTERY_TYPES_FILE": str(battery_file)}), patch.object(sys, "argv", args):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    generate_docs()
                first = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()}
                with contextlib.redirect_stdout(io.StringIO()):
                    generate_docs()
            self.assertEqual(first, {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()})
            summary = json.loads(output.getvalue().strip().splitlines()[-1])
            self.assertEqual(summary["battery_devices"], 4)
            self.assertEqual(summary["scripts"], 1)
            self.assertEqual(summary["apps"], 1)
            self.assertEqual(summary["homeassistant_version"], "2026.11.0")

            maintenance = (docs / "wartung/index.md").read_text(encoding="utf-8")
            self.assertIn("1× CR2450", maintenance)
            self.assertIn("Herstellerangabe", maintenance)
            self.assertIn("1× CR123A", maintenance)
            self.assertIn("selbst eingetragen", maintenance)
            self.assertNotIn("Max iPhone", maintenance)
            self.assertIn("Rauchmelder", maintenance)

            emergency = (docs / "notfall/index.md").read_text(encoding="utf-8")
            self.assertIn("112", emergency)
            self.assertIn("../manuell/notfall.md", emergency)
            self.assertIn("Nuki-App", emergency)
            self.assertIn("Wasserventil", emergency)

            integrations = (docs / "technik/integrationen.md").read_text(encoding="utf-8")
            self.assertIn("Zigbee2MQTT", integrations)
            self.assertIn("Telekom Speedport", integrations)
            self.assertIn("Alles aus", (docs / "technik/skripte-helfer.md").read_text(encoding="utf-8"))
            self.assertIn("Urlaubsmodus", (docs / "technik/skripte-helfer.md").read_text(encoding="utf-8"))
            self.assertIn("Garten bewässern", (docs / "energie/index.md").read_text(encoding="utf-8"))
            self.assertIn("notfall/index.md", (docs / "index.md").read_text(encoding="utf-8"))

            published = "\n".join(p.read_text(encoding="utf-8") for p in docs.rglob("*.md"))
            for private in (SECRET_IDENTIFIER, "SECRETNUKI", "zigbee2mqtt_bridge", "smoke-1", "switch-1"):
                self.assertNotIn(private, published)

            result = subprocess.run([sys.executable, "-m", "mkdocs", "build", "--strict", "--config-file", str(project / "mkdocs.yml")], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            for page in ("notfall", "wartung", "energie", "technik"):
                self.assertTrue((project / "site" / page / "index.html").is_file())


class LiveTests(unittest.TestCase):
    def test_live_summary_filters_mobile_prefers_percent_and_rates_backup(self):
        now = dt.datetime(2026, 11, 8, 12, tzinfo=dt.timezone.utc)
        raw = {
            "batteries": [
                {"device": "d1", "name": "Wandschalter", "area": "Flur", "manufacturer": "Philips", "model": "Hue wall switch module", "domains": ["mqtt"], "domain": "sensor", "state": "high"},
                {"device": "d1", "name": "Wandschalter", "area": "Flur", "manufacturer": "Philips", "model": "Hue wall switch module", "domains": ["mqtt"], "domain": "sensor", "state": "12"},
                {"device": "d2", "name": "iPhone", "domains": ["mobile_app"], "domain": "sensor", "state": "5"},
                {"device": "d3", "name": "Narwal Flow 2", "model": "Flow 2", "domains": ["narwal"], "domain": "sensor", "state": "90"},
                {"device": "d4", "name": "Rauchmelder", "domains": ["mqtt"], "domain": "sensor", "state": "medium"},
                {"device": "../x", "name": "Kaputt", "domains": [], "domain": "sensor", "state": "1"},
            ],
            "offline": [
                {"device": "o1", "name": "Sensor", "area": "Bad", "domains": ["mqtt"], "changed": "2026-11-07T10:00:00+00:00"},
                {"device": "o2", "name": "Handy", "area": "", "domains": ["mobile_app"]},
            ],
            "updates": [{"name": "Zigbee2MQTT", "installed": "2.14", "latest": "2.15"}],
        }
        result = build_live(raw, {"d4": "1× CR123A"}, {"date": "2026-11-01T12:00:00+00:00"}, "2026.11.0", now=now)
        names = [b["name"] for b in result["batteries"]]
        self.assertEqual(names, ["Wandschalter", "Rauchmelder", "Narwal Flow 2"])
        self.assertEqual(result["batteries"][0]["percent"], 12.0)
        self.assertEqual(result["batteries"][0]["level"], "low")
        self.assertEqual(result["batteries"][1]["type"], "1× CR123A")
        self.assertEqual(result["batteries"][2]["type"], "eingebauter Akku")
        self.assertEqual([o["name"] for o in result["offline"]], ["Sensor"])
        self.assertEqual(result["backup"]["age_hours"], 168)
        self.assertEqual(result["backup"]["level"], "warn")
        self.assertEqual(result["summary"], {"batteries_low": 1, "batteries_warn": 1, "batteries_untyped": 0, "offline": 1, "updates": 1})


def _request(address="172.30.32.2", path="/api/battery-types/dev-1", **headers):
    handler = object.__new__(Handler)
    handler.client_address = (address, 123)
    handler.headers = Message()
    for key, value in headers.items():
        handler.headers[key] = value
    handler.path = path
    handler.sent = []
    handler._json = lambda value, status=200, headers=None: handler.sent.append((status, value))
    handler._error = lambda message, status=400: handler.sent.append((status, {"error": message}))
    return handler


class BatteryEndpointTests(unittest.TestCase):
    def test_battery_type_requires_ingress_header_and_admin(self):
        settings = SimpleNamespace(admin_password="", admin_users={"Max"})
        live = SimpleNamespace(set_battery_type=lambda device, value: value)
        with patch("app.server.load_settings", return_value=settings):
            handler = _request(**{"X-Remote-User-Name": "Max"})
            Handler.live = live
            handler.do_PUT()
            self.assertEqual(handler.sent[0][0], 403)
            handler = _request(**{"X-Remote-User-Name": "Gast", "X-Haus-Wiki": "1"})
            handler.do_PUT()
            self.assertEqual(handler.sent[0][0], 403)
            handler = _request("172.30.33.9", **{"X-Remote-User-Name": "Max", "X-Haus-Wiki": "1"})
            handler.do_PUT()
            self.assertEqual(handler.sent[0][0], 403)


if __name__ == "__main__":
    unittest.main()
