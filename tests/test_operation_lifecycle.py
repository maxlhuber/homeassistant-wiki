from __future__ import annotations

import datetime as dt
import io
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "homewiki_gateway"))
from app.engine import WikiEngine
from app.operation_log import OperationLog


def login_engine():
    engine = WikiEngine.__new__(WikiEngine)
    engine.login_lock = threading.Lock()
    engine.login_generation = 1
    engine.login_cancel = threading.Event()
    engine.login_process = None
    engine.login_output = []
    engine.login_state = {"state": "starting", "attempts": 0}
    engine.operation_log = Mock()
    engine.auth_cache = (0, {})
    return engine


class LoginLifecycleTests(unittest.TestCase):
    def test_extracts_clean_code_and_expiration_and_rejects_stale_process(self):
        engine = login_engine()
        process = Mock(stdout=io.StringIO("\x1b[94mhttps://auth.openai.com/codex/device\x1b[0m\n\x1b[94mABCD-EFGHI\x1b[0m\n"))
        engine.login_process = process
        engine._collect_login(process, 1)
        self.assertEqual(engine.login_state["code"], "ABCD-EFGHI")
        self.assertNotIn("\x1b", "".join(engine.login_output))
        self.assertGreater(dt.datetime.fromisoformat(engine.login_state["expires_at"]), dt.datetime.now(dt.timezone.utc))
        stale = Mock(stdout=io.StringIO("XXXX-YYYYY\n"))
        engine._collect_login(stale, 1)
        self.assertEqual(engine.login_state["code"], "ABCD-EFGHI")

    def test_cancel_invalidates_collectors_and_clears_code(self):
        engine = login_engine()
        process = Mock()
        process.poll.return_value = None
        engine.login_process = process
        engine.login_state.update(code="ABCD-EFGHI", state="pending")
        engine.stop_device_login()
        self.assertTrue(engine.login_cancel.is_set())
        self.assertEqual(engine.login_generation, 2)
        self.assertIsNone(engine.device_login_status()["code"])
        process.terminate.assert_called_once()

    def test_repeated_errors_stop_after_three_attempts(self):
        engine = login_engine()
        process = Mock(stdout=io.StringIO(""), returncode=1)
        process.poll.return_value = 1
        cancel = Mock()
        cancel.is_set.return_value = False
        cancel.wait.return_value = False
        with patch("app.engine.subprocess.Popen", return_value=process) as popen, patch.object(engine, "auth_status", return_value={"logged_in": False}):
            engine._login_flow(1, cancel)
        self.assertEqual(popen.call_count, 3)
        self.assertEqual(engine.login_state["state"], "failed")
        self.assertEqual([call.args[0] for call in cancel.wait.call_args_list], [5, 10])

    def test_success_does_not_restart(self):
        engine = login_engine()
        process = Mock(stdout=io.StringIO(""), returncode=0)
        process.poll.return_value = 0
        with patch("app.engine.subprocess.Popen", return_value=process) as popen, patch.object(engine, "auth_status", return_value={"logged_in": True}):
            engine._login_flow(1, engine.login_cancel)
        popen.assert_called_once()
        self.assertEqual(engine.login_state["state"], "authenticated")

    def test_expired_code_renews_without_treating_expiration_as_failure(self):
        engine = login_engine()
        process = Mock(stdout=None, returncode=1)
        process.poll.return_value = 1
        def collect(_process, _generation):
            engine.login_state["expires_at"] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
        with patch("app.engine.subprocess.Popen", return_value=process) as popen, patch.object(engine, "_collect_login", side_effect=collect), patch.object(engine, "auth_status", side_effect=[{"logged_in": False}, {"logged_in": True}]), patch.object(engine.login_cancel, "wait", return_value=False):
            engine._login_flow(1, engine.login_cancel)
        self.assertEqual(popen.call_count, 2)
        self.assertEqual(engine.login_state["state"], "authenticated")


class OperationLogTests(unittest.TestCase):
    def test_rotation_is_bounded_and_unknown_payloads_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            log = OperationLog(Path(directory), max_bytes=250, backups=2)
            for index in range(15):
                log.emit("test", "Fester sicherer Text", run_id=str(index), password="do-not-log", raw_output="sensitive")
            result = log.read()
            self.assertEqual(result["entries"][-1]["run_id"], "14")
            self.assertLessEqual(len(list(Path(directory).iterdir())), 3)
            self.assertNotIn("sensitive", str(result))
            self.assertNotIn("do-not-log", str(result))
            for handler in log.logger.handlers:
                handler.close()


if __name__ == "__main__":
    unittest.main()
