from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from securetar import SecureTarArchive


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_docs import (  # noqa: E402
    main as generate_docs_main,
    merge_documentation_overrides,
    safe_source_text,
)
from weekly_update import (  # noqa: E402
    _review_credit_probe_required,
    _review_reason,
    merge_ai_overrides,
)
from wiki_backup import (  # noqa: E402
    ALLOWED_MEMBERS,
    BackupExtractionError,
    REQUIRED_MEMBER_NAMES,
    discover_latest_backup,
    extract_home_assistant_backup,
)
from wiki_openai import (  # noqa: E402
    OpenAIClientError,
    OpenAIResult,
    classify_http_error,
    request_automation_wording,
    validate_ai_document,
)
from wiki_snapshot import build_snapshot, calculate_delta  # noqa: E402
from wiki_dashboards import (  # noqa: E402
    build_dashboard_snapshot,
    write_dashboard_inventory,
)


def _registry(items_key: str, items: list[dict]) -> str:
    return json.dumps({"version": 1, "data": {items_key: items}})


def _write_source(root: Path, automations: list[dict]) -> None:
    storage = root / ".storage"
    storage.mkdir(parents=True)
    files = {
        "core.floor_registry": _registry("floors", [{"floor_id": "eg", "name": "Erdgeschoss"}]),
        "core.area_registry": _registry(
            "areas", [{"id": "flur", "name": "Flur", "floor_id": "eg"}]
        ),
        "core.label_registry": _registry("labels", []),
        "core.device_registry": _registry(
            "devices",
            [{"id": "device-secret-id", "name": "Flurlicht", "area_id": "flur"}],
        ),
        "core.entity_registry": _registry(
            "entities",
            [
                {
                    "id": "entity-registry-id",
                    "entity_id": "light.flur",
                    "original_name": "Flurlicht",
                    "device_id": "device-secret-id",
                    "platform": "mqtt",
                }
            ],
        ),
    }
    for filename, content in files.items():
        (storage / filename).write_text(content, encoding="utf-8")
    (root / "automations.yaml").write_text(
        yaml.safe_dump(automations, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (root / "scenes.yaml").write_text("[]\n", encoding="utf-8")


class BackupExtractionTests(unittest.TestCase):
    @staticmethod
    def _metadata(
        *,
        protected: bool,
        compressed: bool,
        date: str = "2026-07-15T01:00:00+00:00",
        name: str = "Wiki-Testbackup",
    ) -> bytes:
        return json.dumps(
            {
                "slug": "wiki-test",
                "version": 2,
                "name": name,
                "date": date,
                "type": "partial",
                "protected": protected,
                "compressed": compressed,
                "homeassistant": {"version": "2026.7.1", "size": 1.0},
            }
        ).encode("utf-8")

    @staticmethod
    def _add_bytes(archive: tarfile.TarFile, name: str, payload: bytes) -> None:
        info = tarfile.TarInfo(name)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    def _add_allowed_members(self, archive: tarfile.TarFile) -> None:
        for member in ALLOWED_MEMBERS:
            payload = b"[]\n" if member.endswith(".yaml") else b'{"data": {}}\n'
            self._add_bytes(archive, "data/" + member, payload)

    def _add_required_members(self, archive: tarfile.TarFile) -> None:
        for member in REQUIRED_MEMBER_NAMES:
            payload = b"[]\n" if member.endswith(".yaml") else b'{"data": {}}\n'
            self._add_bytes(archive, "data/" + member, payload)

    def _official_backup(
        self,
        path: Path,
        *,
        protected: bool,
        password: str | None = None,
        version: int = 3,
        compressed: bool = True,
        date: str = "2026-07-15T01:00:00+00:00",
    ) -> None:
        with SecureTarArchive(
            path,
            mode="w",
            password=password if protected else None,
            create_version=version,
        ) as outer:
            self._add_bytes(
                outer.tar,
                "./backup.json",
                self._metadata(
                    protected=protected, compressed=compressed, date=date
                ),
            )
            inner_name = "./homeassistant.tar.gz" if compressed else "./homeassistant.tar"
            with outer.create_tar(inner_name, gzip=compressed) as inner:
                self._add_allowed_members(inner)

    def _archive(self, path: Path, symlink_allowed_member: bool = False) -> None:
        with tarfile.open(path, "w:gz") as archive:
            for member in ALLOWED_MEMBERS:
                tar_name = "data/" + member
                if symlink_allowed_member and member == "automations.yaml":
                    info = tarfile.TarInfo(tar_name)
                    info.type = tarfile.SYMTYPE
                    info.linkname = "data/secrets.yaml"
                    archive.addfile(info)
                    continue
                payload = b"[]\n" if member.endswith(".yaml") else b'{"data": {}}\n'
                info = tarfile.TarInfo(tar_name)
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            secret = b"should-never-be-copied"
            info = tarfile.TarInfo("data/secrets.yaml")
            info.size = len(secret)
            archive.addfile(info, io.BytesIO(secret))
            traversal = b"also-not-copied"
            info = tarfile.TarInfo("data/../outside.txt")
            info.size = len(traversal)
            archive.addfile(info, io.BytesIO(traversal))

    def test_extracts_only_whitelist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "backup.tar.gz"
            self._archive(archive)
            destination = root / "output"
            extract_home_assistant_backup(archive, destination)
            extracted = {
                path.relative_to(destination).as_posix()
                for path in destination.rglob("*")
                if path.is_file() and path.name != ".wiki_backup_metadata.json"
            }
            self.assertEqual(extracted, set(ALLOWED_MEMBERS))

    def test_optional_dashboard_files_may_be_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "minimal.tar"
            with tarfile.open(archive, "w:") as handle:
                self._add_required_members(handle)
            destination = root / "output"

            extract_home_assistant_backup(archive, destination)

            extracted = {
                path.relative_to(destination).as_posix()
                for path in destination.rglob("*")
                if path.is_file() and path.name != ".wiki_backup_metadata.json"
            }
            self.assertEqual(extracted, set(REQUIRED_MEMBER_NAMES))
            self.assertFalse((root / "outside.txt").exists())
            self.assertFalse((destination / "secrets.yaml").exists())

    def test_rejects_symlink_for_whitelisted_member(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "backup.tar.gz"
            self._archive(archive, symlink_allowed_member=True)
            with self.assertRaises(BackupExtractionError) as caught:
                extract_home_assistant_backup(archive, root / "output")
            self.assertEqual(caught.exception.kind, "unsafe_member")

    def test_reads_securetar_v2_and_v3_and_classifies_wrong_key(self) -> None:
        for version in (2, 3):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive_path = root / f"home-assistant-v{version}.tar"
                self._official_backup(
                    archive_path,
                    protected=True,
                    password="test-backup-key",
                    version=version,
                )
                with self.assertRaises(BackupExtractionError) as caught:
                    extract_home_assistant_backup(
                        archive_path, root / "wrong-output", password="wrong-key"
                    )
                self.assertEqual(caught.exception.kind, "backup_key_invalid")
                result = extract_home_assistant_backup(
                    archive_path, root / "output", password="test-backup-key"
                )
                self.assertTrue((result.destination / "automations.yaml").is_file())

    def test_streams_inner_archive_without_complete_temporary_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "large-home-assistant.tar"
            with SecureTarArchive(
                archive_path,
                mode="w",
                password="test-backup-key",
                create_version=3,
            ) as outer:
                self._add_bytes(
                    outer.tar,
                    "./backup.json",
                    self._metadata(protected=True, compressed=True),
                )
                with outer.create_tar("./homeassistant.tar.gz", gzip=True) as inner:
                    self._add_allowed_members(inner)
                    self._add_bytes(inner, "data/unrelated.bin", os.urandom(3 * 1024 * 1024))

            with patch(
                "wiki_backup.tempfile.NamedTemporaryFile",
                side_effect=AssertionError("inner archive must be streamed"),
                create=True,
            ):
                result = extract_home_assistant_backup(
                    archive_path, root / "output", password="test-backup-key"
                )
            self.assertTrue((result.destination / "automations.yaml").is_file())

    def test_rejects_v3_corruption_after_tar_end_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw_inner = root / "inner.tar"
            with tarfile.open(raw_inner, "w:") as inner:
                self._add_allowed_members(inner)
            # Force the SecureTar final tag into chunks the tar parser does not need.
            with raw_inner.open("ab") as handle:
                handle.write(b"x" * (3 * 1024 * 1024))

            archive_path = root / "corrupt-home-assistant.tar"
            with SecureTarArchive(
                archive_path,
                mode="w",
                password="test-backup-key",
                create_version=3,
            ) as outer:
                self._add_bytes(
                    outer.tar,
                    "./backup.json",
                    self._metadata(protected=True, compressed=False),
                )
                info = tarfile.TarInfo("./homeassistant.tar")
                info.size = raw_inner.stat().st_size
                with raw_inner.open("rb") as source:
                    outer.import_tar(source, info)

            with tarfile.open(archive_path, "r:") as outer:
                member = next(
                    item for item in outer if item.name.endswith("homeassistant.tar")
                )
            with archive_path.open("r+b") as handle:
                handle.seek(member.offset_data + member.size - 100)
                original = handle.read(1)
                handle.seek(-1, io.SEEK_CUR)
                handle.write(bytes([original[0] ^ 1]))

            with self.assertRaises(BackupExtractionError) as caught:
                extract_home_assistant_backup(
                    archive_path, root / "output", password="test-backup-key"
                )
            self.assertEqual(caught.exception.kind, "backup_invalid")

    def test_rejects_mixed_outer_and_direct_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "mixed.tar"
            with SecureTarArchive(
                archive_path,
                mode="w",
                password="test-backup-key",
                create_version=3,
            ) as outer:
                self._add_bytes(
                    outer.tar,
                    "./backup.json",
                    self._metadata(protected=True, compressed=True),
                )
                with outer.create_tar("./homeassistant.tar.gz", gzip=True) as inner:
                    self._add_allowed_members(inner)
                self._add_bytes(outer.tar, "data/automations.yaml", b"[]\n")

            with self.assertRaises(BackupExtractionError) as caught:
                extract_home_assistant_backup(
                    archive_path, root / "output", password="test-backup-key"
                )
            self.assertEqual(caught.exception.kind, "mixed_backup_layout")

    def test_discovery_ignores_newer_foreign_tar_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid = root / "valid-ha-backup.tar"
            self._official_backup(valid, protected=False)
            foreign = root / "newer-foreign.tar"
            with tarfile.open(foreign, "w:") as archive:
                self._add_bytes(archive, "unrelated.txt", b"not a HA backup")
            newer = valid.stat().st_mtime + 60
            os.utime(foreign, (newer, newer))

            self.assertEqual(discover_latest_backup(root, min_age_seconds=0), valid)


class SnapshotTests(unittest.TestCase):
    @staticmethod
    def _write_dashboard(source: Path, entity_id: str) -> None:
        storage = source / ".storage"
        document = {
            "version": 1,
            "key": "lovelace.lovelace",
            "data": {
                "config": {
                    "title": "Übersicht",
                    "views": [
                        {
                            "title": "Start",
                            "path": "home",
                            "type": "sections",
                            "sections": [
                                {
                                    "type": "grid",
                                    "cards": [{"type": "tile", "entity": entity_id}],
                                }
                            ],
                        }
                    ],
                }
            },
        }
        (storage / "lovelace.lovelace").write_text(
            json.dumps(document), encoding="utf-8"
        )

    @staticmethod
    def _write_dashboard_registry(source: Path, item: dict) -> None:
        storage = source / ".storage"
        (storage / "lovelace_dashboards").write_text(
            json.dumps({"version": 1, "data": {"items": [item]}}),
            encoding="utf-8",
        )

    def test_dashboard_change_is_local_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            _write_source(first, [])
            _write_source(second, [])
            self._write_dashboard(first, "light.flur")
            self._write_dashboard(second, "light.private_room")

            old = build_snapshot(first)
            new = build_snapshot(second)
            delta = calculate_delta(old, new)

            self.assertEqual(delta.sections["dashboards"]["modified"], ["uebersicht"])
            self.assertEqual(delta.automation_candidates, [])
            self.assertFalse(_review_credit_probe_required(False, delta))
            serialised = json.dumps(new["dashboards"], ensure_ascii=False)
            self.assertNotIn("light.private_room", serialised)

    def test_dashboard_registry_change_is_detected_without_leaking_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            _write_source(first, [])
            _write_source(second, [])
            self._write_dashboard(first, "light.flur")
            self._write_dashboard(second, "light.flur")
            self._write_dashboard_registry(
                first,
                {
                    "id": "main",
                    "url_path": "lovelace",
                    "title": "Privat 123456 https://unsafe.example",
                    "show_in_sidebar": True,
                    "mode": "storage",
                },
            )
            self._write_dashboard_registry(
                second,
                {
                    "id": "main",
                    "url_path": "lovelace",
                    "title": "<script>privat</script>",
                    "show_in_sidebar": False,
                    "mode": "storage",
                },
            )

            old = build_snapshot(first)
            new = build_snapshot(second)
            delta = calculate_delta(old, new)
            serialised = json.dumps(new["dashboards"], ensure_ascii=False)

            self.assertEqual(delta.sections["dashboards"]["modified"], ["uebersicht"])
            self.assertFalse(new["dashboards"]["uebersicht"]["visible"])
            for private_text in ("123456", "unsafe.example", "<script>", "privat"):
                self.assertNotIn(private_text, serialised.lower())

    def test_dashboard_inventory_with_no_sources_replaces_stale_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "docs" / "automatisch.md"
            source.mkdir()
            destination.parent.mkdir()
            destination.write_text("VERALTETER INHALT", encoding="utf-8")

            count = write_dashboard_inventory(source, destination, "18. Juli 2026")
            rendered = destination.read_text(encoding="utf-8")

            self.assertEqual(count, 0)
            self.assertNotIn("VERALTETER INHALT", rendered)
            self.assertIn("keine Dashboard-Dateien erkannt", rendered)
            self.assertIn("exclude: true", rendered)

    def test_unknown_dashboard_metadata_is_generic_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / ".storage").mkdir()
            self._write_dashboard_registry(
                source,
                {
                    "id": "secret-id",
                    "url_path": "private-123456",
                    "title": "[Intern](https://unsafe.example)",
                    "show_in_sidebar": True,
                    "mode": "storage",
                },
            )

            snapshot = build_dashboard_snapshot(source)
            serialised = json.dumps(snapshot, ensure_ascii=False)

            self.assertEqual(len(snapshot), 1)
            self.assertIn("Neues Dashboard", serialised)
            for private_text in (
                "secret-id",
                "private-123456",
                "unsafe.example",
                "[Intern]",
            ):
                self.assertNotIn(private_text, serialised)

    def test_dashboard_migration_blocks_unknown_or_empty_inventory(self) -> None:
        for with_unknown in (False, True):
            with self.subTest(
                with_unknown=with_unknown
            ), tempfile.TemporaryDirectory() as temporary:
                source = Path(temporary)
                _write_source(source, [])
                if with_unknown:
                    self._write_dashboard_registry(
                        source,
                        {
                            "id": "new-private-dashboard",
                            "url_path": "new-private-dashboard",
                            "show_in_sidebar": True,
                            "mode": "storage",
                        },
                    )
                new = build_snapshot(source)
                old = json.loads(json.dumps(new))
                old.pop("dashboards")
                delta = calculate_delta(old, new)

                reason = _review_reason(delta, old, new, set())

                self.assertIsNotNone(reason)
                self.assertIn("Dashboard", reason)

    def test_dashboard_migration_accepts_known_inventory_as_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            _write_source(source, [])
            self._write_dashboard(source, "light.flur")
            new = build_snapshot(source)
            old = json.loads(json.dumps(new))
            old.pop("dashboards")
            delta = calculate_delta(old, new)

            self.assertIsNone(_review_reason(delta, old, new, set()))

    def test_review_reason_aggregates_dashboard_manual_and_critical_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            alias = "Haustür öffnen"
            old_automation = {
                "id": "door",
                "alias": alias,
                "trigger": [{"platform": "time", "at": "10:00:00"}],
                "action": [{"service": "notify.mobile_app"}],
            }
            new_automation = json.loads(json.dumps(old_automation))
            new_automation["trigger"][0]["at"] = "10:05:00"
            _write_source(first, [old_automation])
            _write_source(second, [new_automation])
            self._write_dashboard(first, "light.flur")
            self._write_dashboard(second, "light.kueche")

            old = build_snapshot(first)
            new = build_snapshot(second)
            delta = calculate_delta(old, new)
            reason = _review_reason(delta, old, new, {alias})

            self.assertIsNotNone(reason)
            self.assertIn("Dashboard", reason)
            self.assertIn("manuelle Beschreibung", reason)
            self.assertIn("sicherheits-", reason)
            self.assertTrue(_review_credit_probe_required(False, delta))
            self.assertFalse(_review_credit_probe_required(True, delta))

    def test_mapping_order_and_comments_are_not_semantic_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            _write_source(
                first,
                [
                    {
                        "id": "1",
                        "alias": "Flurlicht",
                        "trigger": [{"platform": "state", "entity_id": "light.flur", "to": "on"}],
                        "action": [{"service": "light.turn_off", "target": {"entity_id": "light.flur"}}],
                    }
                ],
            )
            _write_source(
                second,
                [
                    {
                        "action": [{"target": {"entity_id": "light.flur"}, "service": "light.turn_off"}],
                        "trigger": [{"to": "on", "entity_id": "light.flur", "platform": "state"}],
                        "alias": "Flurlicht",
                        "id": "1",
                    }
                ],
            )
            delta = calculate_delta(build_snapshot(first), build_snapshot(second))
            self.assertFalse(delta.has_changes)
            self.assertEqual(delta.automation_candidates, [])

    def test_secret_is_redacted_but_its_change_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            base = {
                "id": "1",
                "alias": "Test",
                "trigger": [{"platform": "time", "at": "10:00:00"}],
                "action": [{"service": "rest_command.call", "data": {"password": "first-secret"}}],
            }
            _write_source(first, [base])
            changed = json.loads(json.dumps(base))
            changed["action"][0]["data"]["password"] = "second-secret"
            _write_source(second, [changed])
            old = build_snapshot(first)
            new = build_snapshot(second)
            delta = calculate_delta(old, new)
            self.assertTrue(delta.has_changes)
            definition = delta.automation_candidates[0]["definition"]
            serialised = json.dumps(definition, ensure_ascii=False)
            self.assertEqual(
                definition["action"][0]["data"]["geschützte_felder"], 1
            )
            self.assertNotIn("first-secret", serialised)
            self.assertNotIn("second-secret", serialised)
            self.assertNotIn("device-secret-id", serialised)

    def test_llm_definition_hides_messages_templates_and_short_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            _write_source(
                source,
                [
                    {
                        "id": "private",
                        "alias": "Türcode 123456",
                        "trigger": [
                            {"platform": "template", "value_template": "{{ 654321 }}"}
                        ],
                        "action": [
                            {
                                "service": "notify.mobile_app",
                                "data": {
                                    "title": "Privat",
                                    "message": "PIN 654321 für die Tür",
                                    "alarm_code": "7654321",
                                },
                            }
                        ],
                    }
                ],
            )
            delta = calculate_delta(None, build_snapshot(source))
            serialised = json.dumps(
                delta.automation_candidates[0]["definition"], ensure_ascii=False
            )
            self.assertIn("notify.mobile_app", serialised)
            self.assertNotIn("Türcode", serialised)
            self.assertNotIn("123456", serialised)
            self.assertNotIn("654321", serialised)
            self.assertNotIn("7654321", serialised)
            self.assertNotIn("PIN", serialised)


class OpenAITests(unittest.TestCase):
    def test_quota_is_distinct_from_short_rate_limit(self) -> None:
        quota = classify_http_error(
            429, {"error": {"code": "insufficient_quota", "message": "No credits"}}
        )
        rate = classify_http_error(
            429, {"error": {"code": "rate_limit_exceeded", "message": "Slow down"}}
        )
        hard_limit = classify_http_error(
            400, {"error": {"code": "billing_hard_limit_reached", "message": "Limit"}}
        )
        self.assertEqual(quota.kind, "quota_exhausted")
        self.assertFalse(quota.retryable)
        self.assertEqual(hard_limit.kind, "quota_exhausted")
        self.assertEqual(rate.kind, "rate_limited")
        self.assertTrue(rate.retryable)

    def test_structured_response_must_cover_each_alias_once(self) -> None:
        valid = {
            "automations": [
                {
                    "alias": "Licht",
                    "description": "Schaltet das Licht aus.",
                    "trigger_steps": ["Es ist 22 Uhr."],
                    "condition_steps": [],
                    "action_steps": ["Das Licht wird ausgeschaltet."],
                    "manual": "Das Licht am Schalter bedienen.",
                    "safety_note": None,
                    "confidence": "high",
                    "review_required": False,
                }
            ],
            "review_required": False,
            "review_reason": None,
        }
        result = validate_ai_document(valid, ["Licht"])
        self.assertFalse(result.review_required)
        self.assertIn("Licht", result.overrides)
        invalid = json.loads(json.dumps(valid))
        invalid["automations"][0]["alias"] = "Erfunden"
        with self.assertRaises(OpenAIClientError):
            validate_ai_document(invalid, ["Licht"])

    def test_model_wording_rejects_markup_urls_jinja_and_controls(self) -> None:
        valid = {
            "automations": [
                {
                    "alias": "Licht",
                    "description": "Schaltet das Licht aus.",
                    "trigger_steps": ["Es ist 22 Uhr."],
                    "condition_steps": [],
                    "action_steps": ["Das Licht wird ausgeschaltet."],
                    "manual": "Das Licht am Schalter bedienen.",
                    "safety_note": None,
                    "confidence": "high",
                    "review_required": False,
                }
            ],
            "review_required": False,
            "review_reason": None,
        }
        unsafe_values = (
            "<script>alert(1)</script>",
            "[Hilfe](relative-seite)",
            "![Bild](relative-bild.png)",
            "Mehr unter https://example.com/hilfe",
            "Mehr unter www.example.de",
            "javascript:alert(1)",
            "data:text/html,Alarm",
            "{{ states('alarm_control_panel.haus') }}",
            "{% if true %}Alarm{% endif %}",
            "Erste Zeile\nZweite Zeile",
            "Normaler Text\u202emit Richtungswechsel",
        )
        for unsafe in unsafe_values:
            with self.subTest(unsafe=repr(unsafe)):
                document = json.loads(json.dumps(valid))
                document["automations"][0]["description"] = unsafe
                with self.assertRaises(OpenAIClientError) as caught:
                    validate_ai_document(document, ["Licht"])
                self.assertEqual(caught.exception.kind, "invalid_response")

    def test_plain_text_validation_covers_every_free_model_field(self) -> None:
        valid = {
            "automations": [
                {
                    "alias": "Licht",
                    "description": "Schaltet das Licht aus.",
                    "trigger_steps": ["Es ist 22 Uhr."],
                    "condition_steps": ["Jemand ist zuhause."],
                    "action_steps": ["Das Licht wird ausgeschaltet."],
                    "manual": "Das Licht am Schalter bedienen.",
                    "safety_note": "Keine besondere Gefahr.",
                    "confidence": "high",
                    "review_required": False,
                }
            ],
            "review_required": False,
            "review_reason": "Keine manuelle Prüfung nötig.",
        }
        scalar_fields = ("description", "manual", "safety_note")
        list_fields = ("trigger_steps", "condition_steps", "action_steps")
        for field in scalar_fields:
            with self.subTest(field=field):
                document = json.loads(json.dumps(valid))
                document["automations"][0][field] = "<b>Nicht erlaubt</b>"
                with self.assertRaises(OpenAIClientError):
                    validate_ai_document(document, ["Licht"])
        for field in list_fields:
            with self.subTest(field=field):
                document = json.loads(json.dumps(valid))
                document["automations"][0][field] = ["<b>Nicht erlaubt</b>"]
                with self.assertRaises(OpenAIClientError):
                    validate_ai_document(document, ["Licht"])
        document = json.loads(json.dumps(valid))
        document["review_reason"] = "[Prüfen](relative-seite)"
        with self.assertRaises(OpenAIClientError):
            validate_ai_document(document, ["Licht"])

    def test_request_uses_opaque_handle_instead_of_private_alias(self) -> None:
        output = {
            "automations": [
                {
                    "alias": "automation_1",
                    "description": "Eine geprüfte Beschreibung.",
                    "trigger_steps": [],
                    "condition_steps": [],
                    "action_steps": ["Eine Nachricht wird gesendet."],
                    "manual": "Keine Bedienung nötig.",
                    "safety_note": None,
                    "confidence": "high",
                    "review_required": False,
                }
            ],
            "review_required": False,
            "review_reason": None,
        }
        response = json.dumps(
            {"id": "response_test", "output_text": json.dumps(output), "usage": {}}
        ).encode()
        captured: dict[str, bytes] = {}

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self) -> bytes:
                return response

        def fake_open(request, timeout):
            captured["body"] = request.data
            return FakeResponse()

        with tempfile.TemporaryDirectory() as temporary:
            prompt = Path(temporary) / "prompt.txt"
            prompt.write_text("Nur Fakten.", encoding="utf-8")
            with patch("wiki_openai.urllib.request.urlopen", side_effect=fake_open):
                result = request_automation_wording(
                    [
                        {
                            "change": "modified",
                            "alias": "Türcode 123456",
                            "definition": {
                                "alias": "Türcode <geschützt>",
                                "action": [{"service": "notify.mobile_app"}],
                            },
                        }
                    ],
                    api_key="sk-test_abcdefghijklmnopqrstuvwxyz",
                    prompt_path=prompt,
                )
        body = captured["body"].decode("utf-8")
        self.assertNotIn("Türcode 123456", body)
        self.assertNotIn("Türcode", body)
        self.assertNotIn("123456", body)
        self.assertIn("automation_1", body)
        self.assertIn("Türcode 123456", result.overrides)


class SourceTextTests(unittest.TestCase):
    def test_generator_neutralizes_active_backup_and_registry_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            docs = root / "docs"
            source.mkdir()
            docs.mkdir()
            alias = "Licht <script> {{ code }} 123456"
            _write_source(
                source,
                [
                    {
                        "id": "test-automation",
                        "alias": alias,
                        "description": "[Details](https://unsafe.example/private) 654321",
                        "trigger": [
                            {
                                "platform": "state",
                                "entity_id": "light.flur",
                                "to": "on",
                            }
                        ],
                        "action": [
                            {
                                "service": "light.turn_on",
                                "target": {"entity_id": "light.flur"},
                            }
                        ],
                    }
                ],
            )
            storage = source / ".storage"
            replacements = {
                "core.floor_registry": ("floors", "name", "{{ floor }}"),
                "core.area_registry": (
                    "areas",
                    "name",
                    "[Raum](https://unsafe.example/room)",
                ),
                "core.device_registry": (
                    "devices",
                    "name",
                    "<img src=x onerror=alert(1)>",
                ),
                "core.entity_registry": (
                    "entities",
                    "original_name",
                    "Sensor 456789",
                ),
            }
            for filename, (section, field, value) in replacements.items():
                path = storage / filename
                document = json.loads(path.read_text(encoding="utf-8"))
                document["data"][section][0][field] = value
                path.write_text(json.dumps(document), encoding="utf-8")

            overrides = root / "overrides.yaml"
            overrides.write_text("{}\n", encoding="utf-8")
            output = io.StringIO()
            arguments = [
                "generate_docs.py",
                str(source),
                str(docs),
                "--overrides",
                str(overrides),
            ]
            with patch.object(sys, "argv", arguments), contextlib.redirect_stdout(output):
                generate_docs_main()

            rendered = "\n".join(
                path.read_text(encoding="utf-8") for path in docs.rglob("*.md")
            )
            for private_or_active in (
                "<script>",
                "<img ",
                "https://unsafe.example",
                "{{ code }}",
                "{{ floor }}",
                "123456",
                "654321",
                "456789",
            ):
                self.assertNotIn(private_or_active, rendered)
            self.assertIn("geschütz", rendered)
            self.assertFalse(
                any("123456" in path.name for path in docs.rglob("*.md"))
            )

    def test_secret_like_source_text_fails_without_echoing_value(self) -> None:
        cases = (
            "sk-proj-test_abcdefghijklmnopqrstuvwxyz",
            "Passwort: dummy-secret-value",
        )
        for secret_text in cases:
            with self.subTest(secret_text=secret_text.split(":", 1)[0]):
                with self.assertRaises(RuntimeError) as caught:
                    safe_source_text(secret_text, "Testfeld")
                self.assertNotIn(secret_text, str(caught.exception))


class OverrideTests(unittest.TestCase):
    def test_manual_values_always_override_ai_and_ai_cannot_move_devices(self) -> None:
        ai = {
            "device_area_overrides": {"Lampe": "falsch"},
            "automation_overrides": {
                "Licht": {
                    "description": "KI",
                    "action_steps": ["KI-Aktion"],
                    "enabled": False,
                    "area_ids": ["falsch"],
                }
            },
        }
        manual = {
            "device_area_overrides": {"Lampe": "flur"},
            "automation_overrides": {
                "Licht": {"description": "**Geprüft** [interne Hilfe](hilfe.md)"}
            },
        }
        merged = merge_documentation_overrides(ai, manual)
        self.assertEqual(merged["device_area_overrides"]["Lampe"], "flur")
        self.assertEqual(
            merged["automation_overrides"]["Licht"]["description"],
            "**Geprüft** [interne Hilfe](hilfe.md)",
        )
        self.assertEqual(merged["automation_overrides"]["Licht"]["action_steps"], ["KI-Aktion"])
        self.assertNotIn("enabled", merged["automation_overrides"]["Licht"])
        self.assertNotIn("area_ids", merged["automation_overrides"]["Licht"])

    def test_machine_override_file_drops_orphans(self) -> None:
        existing = {
            "automation_overrides": {
                "Alt": {"description": "alt"},
                "Bleibt": {"description": "bleibt"},
            }
        }
        result = OpenAIResult(
            overrides={"Neu": {"description": "neu"}},
            review_required=False,
            review_reason=None,
            usage={},
            response_id=None,
        )
        merged = merge_ai_overrides(
            existing, result, {"Bleibt", "Neu"}, drop_aliases={"Bleibt"}
        )
        self.assertEqual(set(merged["automation_overrides"]), {"Neu"})


class PiInstallationTests(unittest.TestCase):
    def test_installer_copies_every_python_runner(self) -> None:
        installer = (ROOT / "raspberry-pi" / "wiki-weekly-install.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("wiki_dashboards.py", installer)

    def test_weekly_runner_only_fast_forwards_remote_main(self) -> None:
        runner = (ROOT / "raspberry-pi" / "wiki-weekly-update.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("refs/heads/main:refs/remotes/origin/main", runner)
        self.assertIn("git merge-base --is-ancestor", runner)
        self.assertIn('git merge --ff-only "${REMOTE_HEAD}"', runner)


if __name__ == "__main__":
    unittest.main()
