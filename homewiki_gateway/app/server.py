from __future__ import annotations

import hashlib
import hmac
import html
import json
import mimetypes
import os
import re
import secrets
import shutil
import subprocess
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

try:
    from .wiki_snapshot import SECRET_VALUE_PATTERNS
except ImportError:
    from wiki_snapshot import SECRET_VALUE_PATTERNS
from .engine import BUILT_VERSION, DATA, MANUAL, MANUAL_DIRTY, WikiEngine, runtime_version, scheduler
from .settings import load_settings

UI_FILE = Path(__file__).with_name("ui.html")
SESSION_KEY = secrets.token_bytes(32)
SESSION_SECONDS = 3600
ACCESS_LOCK = threading.Lock()
LOGIN_ATTEMPTS: dict[str, list[float]] = {}


class Handler(BaseHTTPRequestHandler):
    engine: WikiEngine
    server_version = "HausWiki/3"

    def log_message(self, fmt, *args):
        # URLs can contain session IDs or authentication material. Operational
        # events are logged by the engine; do not duplicate raw HTTP requests.
        pass

    @property
    def path_only(self):
        return unquote(urlsplit(self.path).path).lstrip("/")

    def _allowed(self):
        # HA's documented Ingress proxy. Header assertions from another
        # container are not an authenticated Home Assistant session.
        return self.client_address[0] == "172.30.32.2" or (
            os.environ.get("HOMEWIKI_DEV_MODE") == "1"
            and self.client_address[0] in {"127.0.0.1", "::1"}
        )

    def _user(self):
        return self.headers.get("X-Remote-User-Id", "")

    def _signature(self, expiry, password):
        payload = f"{expiry}:{self._user()}:{hashlib.sha256(password.encode()).hexdigest()}"
        return hmac.new(SESSION_KEY, payload.encode(), hashlib.sha256).hexdigest()

    def _admin(self):
        if not self._allowed():
            return False
        settings = load_settings()
        if settings.admin_password:
            try:
                cookie = SimpleCookie(self.headers.get("Cookie", ""))
                expiry, signature = cookie["hauswiki_admin"].value.split(".", 1)
                return time.time() < int(expiry) <= time.time() + SESSION_SECONDS + 5 and hmac.compare_digest(
                    signature, self._signature(expiry, settings.admin_password)
                )
            except (KeyError, ValueError):
                return False
        permitted = {value.strip().casefold() for value in settings.admin_users}
        return any(self.headers.get(key, "").strip().casefold() in permitted for key in (
            "X-Remote-User-Id", "X-Remote-User-Name", "X-Remote-User-Display-Name"
        ) if self.headers.get(key, "").strip())

    def _base(self):
        base = self.headers.get("X-Ingress-Path", "").rstrip("/")
        return base + "/" if re.fullmatch(r"(?:/api/hassio_ingress/[A-Za-z0-9_-]+)?", base) else "/"

    def _send(self, data, mime, status=200, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, value, status=200, headers=None):
        self._send(json.dumps(value, ensure_ascii=False).encode(), "application/json; charset=utf-8", status, headers)

    def _error(self, message, status=400):
        self._json({"error": message}, status)

    def _body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size < 0 or size > 200_000:
            raise ValueError("Die Anfrage ist zu groß.")
        value = json.loads(self.rfile.read(size).decode() or "{}")
        if not isinstance(value, dict):
            raise ValueError("Ein JSON-Objekt wird erwartet.")
        return value

    def _file(self, root, relative):
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root.resolve()):
            return self._error("Ungültiger Pfad.", 404)
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.is_file():
            return self._error("Diese Seite ist noch nicht vorhanden.", 404)
        mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self._send(candidate.read_bytes(), mime)

    def do_GET(self):
        path = self.path_only
        if path == "_gateway_health":
            return self._json(self.engine.health_status())
        if not self._allowed():
            return self._error("Bitte Haus-Wiki über Home Assistant öffnen.", 403)
        if path in {"", "index.html"}:
            content = UI_FILE.read_text(encoding="utf-8").replace("__BASE__", html.escape(self._base(), quote=True))
            return self._send(content.encode(), "text/html; charset=utf-8")
        if path == "api/status":
            value = self.engine.status()
            settings = load_settings()
            value.update(admin=self._admin(), password_required=bool(settings.admin_password), version=runtime_version(),
                         schedule={"days": settings.schedule_days, "time": settings.schedule_time, "catch_up": settings.catch_up},
                         llm_provider=settings.llm_provider)
            return self._json(value)
        if path == "wiki" or path.startswith("wiki/"):
            return self._file(DATA / "publish-site", path.removeprefix("wiki").lstrip("/"))
        if not self._admin():
            return self._error("Bitte zuerst die Verwaltung freischalten.", 403)
        if path == "api/history":
            return self._json(self.engine.history())
        if path == "api/logs":
            value = self.engine.logs()
            level = parse_qs(urlsplit(self.path).query).get("level", [""])[0].upper()
            if level:
                levels = {"WARNING", "ERROR"} if level == "WARNING" else {level}
                value["entries"] = [entry for entry in value["entries"] if entry.get("level", "").upper() in levels]
            return self._json(value)
        if path == "api/auth/device/status":
            return self._json(self.engine.device_login_status())
        if path == "api/manual":
            return self._json({"pages": sorted(p.stem for p in MANUAL.glob("*.md") if p.is_file() and not p.is_symlink())})
        if path.startswith("api/manual/"):
            name = path.removeprefix("api/manual/")
            if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", name):
                return self._error("Ungültiger Seitenname.")
            page = MANUAL / f"{name}.md"
            if not page.is_file() or page.is_symlink():
                return self._error("Seite nicht gefunden.", 404)
            return self._json({"name": name, "content": page.read_text(encoding="utf-8")})
        return self._error("Nicht gefunden.", 404)

    def _write_allowed(self):
        if not self._allowed():
            self._error("Bitte Haus-Wiki über Home Assistant öffnen.", 403)
            return False
        # Browser actions deliberately use a custom header. Cross-site forms
        # cannot send it and no cross-origin CORS permission is granted.
        if self.headers.get("X-Haus-Wiki") != "1":
            self._error("Bitte die Haus-Wiki-Oberfläche neu laden.", 403)
            return False
        return True

    def _unlock(self):
        password = load_settings().admin_password
        if not password:
            return self._json({"admin": self._admin()})
        key = self._user() or self.client_address[0]
        now = time.monotonic()
        with ACCESS_LOCK:
            attempts = [stamp for stamp in LOGIN_ATTEMPTS.get(key, []) if now - stamp < 60]
            if len(attempts) >= 5:
                return self._error("Zu viele Versuche. Bitte in einer Minute erneut versuchen.", 429)
            attempts.append(now)
            LOGIN_ATTEMPTS[key] = attempts
        if not hmac.compare_digest(str(self._body().get("password", "")).encode(), password.encode()):
            return self._error("Das Verwaltungspasswort stimmt nicht.", 403)
        with ACCESS_LOCK:
            LOGIN_ATTEMPTS.pop(key, None)
        expiry = str(int(time.time()) + SESSION_SECONDS)
        cookie = f"hauswiki_admin={expiry}.{self._signature(expiry, password)}; Path={self._base()}; HttpOnly; SameSite=Strict; Max-Age={SESSION_SECONDS}"
        if self.headers.get("X-Forwarded-Proto") == "https":
            cookie += "; Secure"
        return self._json({"admin": True}, headers={"Set-Cookie": cookie})

    def do_POST(self):
        if not self._write_allowed():
            return
        path = self.path_only
        try:
            if path == "api/unlock":
                return self._unlock()
            if not self._admin():
                return self._error("Bitte zuerst die Verwaltung freischalten.", 403)
            if path == "api/lock":
                return self._json({"ok": True}, headers={"Set-Cookie": f"hauswiki_admin=; Path={self._base()}; HttpOnly; SameSite=Strict; Max-Age=0"})
            if path == "api/run":
                started = self.engine.trigger("manual")
                return self._json({"started": started, "message": "Aktualisierung gestartet." if started else "Eine Aktualisierung läuft bereits. Ihr Fortschritt wird hier angezeigt."}, 202)
            if path == "api/rollback":
                if self.engine.thread and self.engine.thread.is_alive():
                    return self._error("Bitte die laufende Aktualisierung vor einer Wiederherstellung abwarten.", 409)
                self.engine.rollback(str(self._body().get("release") or ""))
                return self._json({"ok": True})
            if path == "api/auth/device":
                started = self.engine.start_device_login()
                return self._json({"started": started, "message": "Anmeldung gestartet." if started else "Die Anmeldung ist bereits geöffnet."}, 202)
            if path == "api/auth/device/cancel":
                self.engine.stop_device_login()
                return self._json({"ok": True})
            if path == "api/auth/device/code":
                self.engine.submit_login_code(str(self._body().get("code") or ""))
                return self._json({"ok": True})
            if path == "api/auth/logout":
                self.engine.stop_device_login()
                settings = load_settings()
                if settings.llm_provider.startswith("claude"):
                    subprocess.run(["claude", "auth", "logout"], timeout=20, capture_output=True, env={**os.environ, "CLAUDE_CONFIG_DIR": str(DATA / "claude-home")})
                else:
                    subprocess.run(["codex", "logout"], timeout=20, capture_output=True, env={**os.environ, "CODEX_HOME": str(DATA / "codex-home")})
                self.engine.auth_cache = (0, {})
                return self._json({"ok": True})
        except (ValueError, UnicodeError):
            return self._error("Die Eingabe konnte nicht verarbeitet werden.")
        except Exception:
            return self._error("Die Aktion konnte nicht abgeschlossen werden. Bitte das Betriebsprotokoll prüfen.", 500)
        return self._error("Nicht gefunden.", 404)

    def do_PUT(self):
        if not self._write_allowed():
            return
        if not self._admin():
            return self._error("Bitte zuerst die Verwaltung freischalten.", 403)
        if not self.path_only.startswith("api/manual/"):
            return self._error("Nicht gefunden.", 404)
        name = self.path_only.removeprefix("api/manual/")
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", name) or name == "index":
            return self._error("Bitte einen Seitennamen mit Buchstaben, Zahlen oder Bindestrichen verwenden (nicht index).")
        try:
            content = str(self._body().get("content") or "")
            if not content.strip() or len(content.encode()) > 100_000:
                return self._error("Die Seite ist leer oder zu groß.")
            if any(pattern.search(content) for pattern in SECRET_VALUE_PATTERNS):
                return self._error("Bitte geheimnisähnliche Inhalte aus der Seite entfernen.")
            temporary = MANUAL / f"{name}.md.new"
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(MANUAL / f"{name}.md")
            MANUAL_DIRTY.touch()
            started = self.engine.trigger("manual_edit")
            return self._json({"saved": True, "update_started": started})
        except (ValueError, UnicodeError):
            return self._error("Die Eingabe konnte nicht verarbeitet werden.")
        except Exception:
            return self._error("Die Seite konnte nicht gespeichert werden.", 500)


def main():
    engine = WikiEngine()
    Handler.engine = engine
    if not (DATA / "publish-site").is_dir():
        bootstrap = Path("/app/bootstrap-site")
        if bootstrap.is_dir():
            shutil.copytree(bootstrap, DATA / "publish-site")
    threading.Thread(target=scheduler, args=(engine,), daemon=True).start()
    built = BUILT_VERSION.read_text(encoding="utf-8").strip() if BUILT_VERSION.exists() else ""
    if built != runtime_version():
        engine.trigger("version_update")
    print("[haus-wiki] Dienst bereit auf Port 8099", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8099), Handler).serve_forever()
