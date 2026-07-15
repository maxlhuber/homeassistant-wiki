from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wiki_notify import (  # noqa: E402
    NotificationConfigurationError,
    _read_webhook,
    flush,
    kinds_from_status,
    send_or_queue,
)


class NotificationTests(unittest.TestCase):
    def test_webhook_is_restricted_to_local_home_assistant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "webhook"
            path.write_text(
                "http://homeassistant.local:8123/api/webhook/" + "a" * 64,
                encoding="utf-8",
            )
            self.assertEqual(_read_webhook(path), path.read_text(encoding="utf-8"))
            path.write_text(
                "https://example.com/api/webhook/" + "a" * 64,
                encoding="utf-8",
            )
            with self.assertRaises(NotificationConfigurationError):
                _read_webhook(path)

    def test_failed_notification_is_deduplicated_and_later_flushed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            queue = Path(temporary) / "queue.json"
            with patch("wiki_notify._post", return_value=False):
                self.assertFalse(send_or_queue("unused", queue, "openai_quota"))
                self.assertFalse(send_or_queue("unused", queue, "openai_quota"))
            self.assertEqual(len(json.loads(queue.read_text(encoding="utf-8"))), 1)
            with patch("wiki_notify._post", return_value=True):
                self.assertEqual(flush("unused", queue), (1, 0))

    def test_flush_stops_at_first_failure_and_preserves_remaining_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            queue = Path(temporary) / "queue.json"
            original = [
                {"kind": "openai_quota", "created_at": "first"},
                {"kind": "backup_invalid", "created_at": "second"},
                {"kind": "github_failed", "created_at": "third"},
            ]
            queue.write_text(json.dumps(original), encoding="utf-8")
            with patch("wiki_notify._post", side_effect=[True, False]) as post:
                self.assertEqual(flush("unused", queue), (1, 2))
            self.assertEqual(post.call_count, 2)
            self.assertEqual(json.loads(queue.read_text(encoding="utf-8")), original[1:])

    def test_successful_send_removes_stale_entries_of_same_kind(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            queue = Path(temporary) / "queue.json"
            queue.write_text(
                json.dumps(
                    [
                        {"kind": "openai_quota", "created_at": "old"},
                        {"kind": "backup_invalid", "created_at": "keep"},
                        {"kind": "openai_quota", "created_at": "older"},
                    ]
                ),
                encoding="utf-8",
            )
            with patch("wiki_notify._post", return_value=True):
                self.assertTrue(send_or_queue("unused", queue, "openai_quota"))
            self.assertEqual(
                json.loads(queue.read_text(encoding="utf-8")),
                [{"kind": "backup_invalid", "created_at": "keep"}],
            )

    def test_status_maps_quota_and_backup_failures_to_fixed_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status = Path(temporary) / "status.json"
            status.write_text(
                json.dumps(
                    {
                        "outcome": "failed",
                        "warning_kind": "quota_exhausted",
                        "reason_kind": "backup_invalid",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                kinds_from_status(status), ["openai_quota", "backup_invalid"]
            )

    def test_review_status_also_reports_openai_credit_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status = Path(temporary) / "status.json"
            status.write_text(
                json.dumps(
                    {
                        "outcome": "blocked",
                        "reason_kind": "review_required",
                        "warning_kind": "quota_exhausted",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                kinds_from_status(status), ["openai_quota", "review_required"]
            )


if __name__ == "__main__":
    unittest.main()
