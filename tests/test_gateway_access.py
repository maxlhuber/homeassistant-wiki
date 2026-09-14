"""Security regressions for the v3 Ingress/password boundary."""
import sys
import time
import unittest
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "homewiki_gateway")]
from app.server import Handler


def request(address="172.30.32.2", **headers):
    handler = object.__new__(Handler)
    handler.client_address = (address, 123)
    handler.headers = Message()
    for key, value in headers.items():
        handler.headers[key] = value
    return handler


class AccessTests(unittest.TestCase):
    def test_display_name_resolves_original_max_button_problem(self):
        settings = SimpleNamespace(admin_password="", admin_users={"Max"})
        handler = request(**{"X-Remote-User-Name": "maxlh", "X-Remote-User-Display-Name": "Max"})
        with patch("app.server.load_settings", return_value=settings):
            self.assertTrue(handler._admin())
            self.assertFalse(request()._admin())
            self.assertFalse(request(**{"X-Remote-User-Name": "other"})._admin())

    def test_forged_headers_from_non_ingress_are_denied(self):
        settings = SimpleNamespace(admin_password="", admin_users={"Max"})
        with patch("app.server.load_settings", return_value=settings):
            self.assertFalse(request("172.30.33.8", **{"X-Remote-User-Name": "Max"})._admin())

    def test_password_cookie_expires_and_is_bound_to_user_and_password(self):
        settings = SimpleNamespace(admin_password="test-only-password", admin_users={"Max"})
        handler = request(**{"X-Remote-User-Id": "person-1", "X-Remote-User-Display-Name": "Max"})
        with patch("app.server.load_settings", return_value=settings):
            self.assertFalse(handler._admin())
            expiry = str(int(time.time()) + 300)
            handler.headers["Cookie"] = f"hauswiki_admin={expiry}.{handler._signature(expiry, settings.admin_password)}"
            self.assertTrue(handler._admin())
            settings.admin_password = "changed-password"
            self.assertFalse(handler._admin())
            settings.admin_password = "test-only-password"
            handler.headers.replace_header("X-Remote-User-Id", "person-2")
            self.assertFalse(handler._admin())
            handler.headers.replace_header("X-Remote-User-Id", "person-1")
            with patch("app.server.time.time", return_value=float(expiry) + 1):
                self.assertFalse(handler._admin())

    def test_unsafe_ingress_path_is_not_inserted_into_html_or_cookie(self):
        self.assertEqual(request(**{"X-Ingress-Path": '//evil.example/"'})._base(), "/")
        self.assertEqual(request(**{"X-Ingress-Path": "/api/hassio_ingress/abc_123"})._base(), "/api/hassio_ingress/abc_123/")


if __name__ == "__main__":
    unittest.main()
