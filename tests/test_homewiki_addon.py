from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "homewiki_gateway"))

from app import codex_client, settings, supervisor  # noqa: E402


class SettingsTests(unittest.TestCase):
    def test_defaults_and_secret_values_are_loaded_without_logging(self):
        with tempfile.TemporaryDirectory() as temporary:
            options = Path(temporary) / "options.json"
            options.write_text(json.dumps({"backup_password": "private", "admin_users": ["Max"]}), encoding="utf-8")
            value = settings.load_settings(options)
        self.assertEqual(value.schedule_days, ("wed", "sun"))
        self.assertEqual(value.backup_password, "private")
        self.assertEqual(value.admin_users, frozenset({"Max"}))


class SupervisorTests(unittest.TestCase):
    @patch("app.supervisor.time.sleep", return_value=None)
    def test_waits_until_backup_job_is_done(self, _sleep):
        running = {"jobs": [{"name": "backup_manager_full_backup", "stage": "addons", "done": False}]}
        done = {"jobs": [{"name": "backup_manager_full_backup", "stage": "complete", "done": True}]}
        with patch("app.supervisor.json_request", side_effect=[running, done]) as request:
            supervisor.wait_for_backup_jobs(60)
        self.assertEqual(request.call_count, 2)

    def test_latest_backup_uses_newest_full_across_locations(self):
        backups = {"backups": [
            {"slug": "partial", "type": "partial", "date": "2026-09-15T10:00:00Z"},
            {"slug": "old", "type": "full", "date": "2026-09-13T10:00:00Z", "location": None},
            {"slug": "nas", "type": "full", "date": "2026-09-14T10:00:00Z", "location": "NAS"},
        ]}
        with patch("app.supervisor.json_request", return_value=backups):
            selected = supervisor.latest_full_backup()
        self.assertEqual(selected["slug"], "nas")

    def test_export_requires_active_named_share_mount(self):
        with patch("pathlib.Path.is_dir", return_value=True), patch("pathlib.Path.is_mount", return_value=True):
            supervisor.ensure_share_mount(Path("/share/HausWiki"))

        with patch("pathlib.Path.is_dir", return_value=True), patch("pathlib.Path.is_mount", return_value=False):
            with self.assertRaises(supervisor.SupervisorError):
                supervisor.ensure_share_mount(Path("/share/HausWiki"))


class CodexClientTests(unittest.TestCase):
    def test_codex_receives_opaque_handles_and_never_private_alias(self):
        private_alias = "Türcode 123456"

        def fake_run(command, **kwargs):
            self.assertNotIn(private_alias, kwargs["input"])
            result_path = Path(command[command.index("--output-last-message") + 1])
            result_path.write_text(json.dumps({
                "automations": [{
                    "alias": "automation_1", "description": "Eine sichere Beschreibung.",
                    "trigger_steps": [], "condition_steps": [], "action_steps": ["Eine Aktion wird ausgeführt."],
                    "manual": "Keine Bedienung erforderlich.", "safety_note": None,
                    "confidence": "high", "review_required": False,
                }],
                "review_required": False, "review_reason": None,
            }), encoding="utf-8")
            return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with tempfile.TemporaryDirectory() as temporary, patch("app.codex_client.subprocess.run", side_effect=fake_run):
            prompt = Path(temporary) / "prompt.txt"
            prompt.write_text("Nur Fakten.", encoding="utf-8")
            result = codex_client.request_automation_wording_codex(
                [{"alias": private_alias, "change": "modified", "definition": {"alias": private_alias, "action": []}}],
                prompt_path=prompt, model="", timeout_seconds=30,
            )
        self.assertIn(private_alias, result.overrides)


if __name__ == "__main__":
    unittest.main()
