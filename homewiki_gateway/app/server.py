from __future__ import annotations

import json
import mimetypes
import re
import shutil
import subprocess
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .wiki_snapshot import SECRET_VALUE_PATTERNS

from .engine import BUILT_VERSION, DATA, MANUAL, MANUAL_DIRTY, PROJECT, WikiEngine, runtime_version, scheduler
from .settings import load_settings


UI = r'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><base href="__BASE__"><title>Haus-Wiki</title><style>
:root{color-scheme:dark;--bg:#111827;--card:#1f2937;--line:#374151;--text:#f3f4f6;--muted:#9ca3af;--accent:#14b8a6;--danger:#f87171}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px system-ui,sans-serif}header{position:sticky;top:0;z-index:2;display:flex;gap:8px;align-items:center;padding:12px 18px;background:#0b1220;border-bottom:1px solid var(--line)}header h1{font-size:19px;margin:0 auto 0 0}button{border:0;border-radius:7px;padding:9px 13px;background:#334155;color:white;cursor:pointer}button.primary{background:#0f766e}button.danger{background:#991b1b}button:disabled{opacity:.45;cursor:default}main{max-width:1200px;margin:auto;padding:16px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}.card h2{font-size:14px;color:var(--muted);margin:0 0 8px}.value{font-size:18px}.ok{color:#5eead4}.bad{color:var(--danger)}nav{display:flex;gap:8px;margin:14px 0}nav button.active{background:#0f766e}.panel{display:none}.panel.active{display:block}iframe{width:100%;height:calc(100vh - 170px);border:1px solid var(--line);border-radius:10px;background:white}pre,textarea{width:100%;white-space:pre-wrap;background:#0b1220;border:1px solid var(--line);border-radius:8px;padding:12px;color:var(--text)}textarea{min-height:45vh;font:14px ui-monospace,monospace}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:8px;border-bottom:1px solid var(--line)}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}select,input{background:#0b1220;color:white;border:1px solid var(--line);border-radius:7px;padding:9px}.muted{color:var(--muted)}@media(max-width:650px){header{flex-wrap:wrap}iframe{height:70vh}}
</style></head><body><header><h1>Haus-Wiki</h1><button id="run" class="primary">Jetzt aktualisieren</button><button id="login">ChatGPT anmelden</button></header><main><div class="cards"><section class="card"><h2>Status</h2><div id="state" class="value">Lädt…</div><div id="message" class="muted"></div></section><section class="card"><h2>Letztes Backup</h2><div id="backup">–</div></section><section class="card"><h2>ChatGPT/Codex</h2><div id="auth">–</div></section><section class="card"><h2>Letzter Abschluss</h2><div id="completed">–</div></section></div><nav><button data-tab="wiki" class="active">Wiki</button><button data-tab="status">Status & Logs</button><button data-tab="manual">Manuelle Seiten</button><button data-tab="rollback">Rollback</button></nav><section id="wiki" class="panel active"><iframe src="wiki/"></iframe></section><section id="status" class="panel"><pre id="history">Noch keine Läufe.</pre><h3>ChatGPT-Anmeldung</h3><pre id="loginOutput">Nicht gestartet.</pre></section><section id="manual" class="panel"><div class="row"><select id="pages"></select><input id="newName" placeholder="neue-seite"><button id="newPage">Neu</button><button id="savePage" class="primary">Speichern & aktualisieren</button></div><textarea id="editor" placeholder="# Seitentitel"></textarea></section><section id="rollback" class="panel"><table><thead><tr><th>Versionsstand</th><th></th></tr></thead><tbody id="releases"></tbody></table></section></main><script>
const api=p=>`api/${p}`;let isAdmin=false;async function req(p,opt){const r=await fetch(api(p),opt);const j=await r.json();if(!r.ok)throw Error(j.error||'Fehler');return j}function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}async function refresh(){try{const s=await req('status');isAdmin=s.admin;document.getElementById('state').textContent=s.running?'Aktualisierung läuft':s.state||'Bereit';document.getElementById('message').textContent=s.message||'';document.getElementById('backup').textContent=s.backup||s.pipeline?.backup||'–';document.getElementById('auth').textContent=s.auth?.logged_in?'Angemeldet':'Nicht angemeldet';document.getElementById('completed').textContent=s.completed_at||'–';document.getElementById('run').disabled=!isAdmin||s.running;document.getElementById('login').disabled=!isAdmin;document.getElementById('savePage').disabled=!isAdmin;document.getElementById('newPage').disabled=!isAdmin;document.getElementById('history').textContent=JSON.stringify(await req('history'),null,2);document.getElementById('releases').innerHTML=(s.releases||[]).map(x=>`<tr><td>${esc(x)}</td><td><button ${isAdmin?'':'disabled'} onclick="rollback('${x}')">Wiederherstellen</button></td></tr>`).join('');}catch(e){document.getElementById('state').textContent='Nicht erreichbar';document.getElementById('message').textContent=e.message}}async function loadPages(){const p=await req('manual');pages.innerHTML=p.pages.map(x=>`<option>${esc(x)}</option>`).join('');if(p.pages.length)await loadPage()}async function loadPage(){if(!pages.value)return;const p=await req(`manual/${encodeURIComponent(pages.value)}`);editor.value=p.content}async function rollback(x){if(confirm(`Versionsstand ${x} wiederherstellen?`)){await req('rollback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({release:x})});refresh()}}document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('nav button,.panel').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active');if(b.dataset.tab==='manual')loadPages()});run.onclick=async()=>{await req('run',{method:'POST'});refresh()};login.onclick=async()=>{await req('auth/device',{method:'POST'});document.querySelector('[data-tab=status]').click()};pages.onchange=loadPage;newPage.onclick=()=>{let n=newName.value.trim();if(!n)return;pages.insertAdjacentHTML('beforeend',`<option>${esc(n)}</option>`);pages.value=n;editor.value=`# ${n.replaceAll('-',' ')}\n\n`;};savePage.onclick=async()=>{await req(`manual/${encodeURIComponent(pages.value)}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:editor.value})});alert('Gespeichert. Die Aktualisierung wurde gestartet.')};setInterval(async()=>{refresh();try{const l=await req('auth/device/status');loginOutput.textContent=l.output||'Warte auf Anmeldung…'}catch{}},5000);refresh();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    engine: WikiEngine
    server_version = "HausWiki/2"

    def log_message(self, fmt, *args):
        print(f"[http] {self.client_address[0]} {fmt % args}")

    @property
    def path_only(self) -> str:
        return unquote(urlsplit(self.path).path).lstrip("/")

    def _admin(self) -> bool:
        # Ingress versions expose the authenticated HA user under different
        # headers.  Prefer an explicit identity when available; when HA omits
        # it entirely, the request has already passed the authenticated
        # Supervisor ingress proxy, so treat it as the configured single-admin
        # installation rather than disabling all controls.
        identity = next((self.headers.get(name, "").strip() for name in (
            "X-Remote-User-Name", "X-Remote-User", "X-Hass-User",
        ) if self.headers.get(name, "").strip()), "")
        if identity:
            return identity in load_settings().admin_users
        return True

    def _allowed(self) -> bool:
        # Ingress may proxy from either of the Supervisor bridge addresses
        # (172.30.32.1/.2) depending on HA version and connection reuse.
        # Restrict direct access to the private Supervisor bridge, while
        # allowing both addresses so the UI API is reachable reliably.
        address = self.client_address[0]
        return address.startswith("172.30.") or __import__("os").environ.get("HOMEWIKI_ALLOW_ANY") == "1"

    def _json(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(data)

    def _error(self, message, status=400):
        self._json({"error": message}, status)

    def _body(self):
        size = min(int(self.headers.get("Content-Length", "0")), 200_000)
        return json.loads(self.rfile.read(size).decode("utf-8") or "{}")

    def _file(self, root: Path, relative: str):
        candidate = (root / relative).resolve()
        if root.resolve() not in candidate.parents and candidate != root.resolve():
            return self._error("Ungültiger Pfad.", 404)
        if candidate.is_dir(): candidate = candidate / "index.html"
        if not candidate.is_file(): return self._error("Nicht gefunden.", 404)
        data = candidate.read_bytes(); mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(200); self.send_header("Content-Type", mime); self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-cache, must-revalidate"); self.send_header("X-Content-Type-Options", "nosniff"); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        path = self.path_only
        # This endpoint is only exposed on the Supervisor's private app network.
        # Keep it available to the watchdog and HA MCP without requiring an
        # Ingress user header; it deliberately contains no backup names,
        # configuration values, authentication output, or other private data.
        if path == "_gateway_health": return self._json(self.engine.health_status())
        if not self._allowed(): return self._error("Zugriff nur über Home Assistant Ingress.",403)
        if path in {"", "index.html"}:
            base=self.headers.get("X-Ingress-Path","/").rstrip("/")+"/"
            data=UI.replace("__BASE__",base).encode(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(data))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(data); return
        if path == "api/status":
            value=self.engine.status(); value["admin"]=self._admin(); return self._json(value)
        if path == "api/history": return self._json(self.engine.history())
        if path == "api/auth/device/status": return self._json(self.engine.device_login_status())
        if path == "api/manual": return self._json({"pages": sorted(p.stem for p in MANUAL.glob("*.md") if p.is_file())})
        if path.startswith("api/manual/"):
            name=path.removeprefix("api/manual/")
            if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}",name): return self._error("Ungültiger Seitenname.")
            page=MANUAL/f"{name}.md"
            if not page.is_file(): return self._error("Seite nicht gefunden.",404)
            return self._json({"name":name,"content":page.read_text(encoding="utf-8")})
        if path == "wiki" or path.startswith("wiki/"):
            relative=path.removeprefix("wiki").lstrip("/")
            return self._file(DATA/"publish-site",relative)
        return self._error("Nicht gefunden.",404)

    def do_POST(self):
        if not self._allowed(): return self._error("Zugriff nur über Home Assistant Ingress.",403)
        if not self._admin(): return self._error("Nur konfigurierte Wiki-Administratoren dürfen diese Aktion ausführen.",403)
        path=self.path_only
        try:
            if path == "api/run":
                return self._json({"started":self.engine.trigger("manual")},202)
            if path == "api/rollback":
                self.engine.rollback(str(self._body().get("release") or "")); return self._json({"ok":True})
            if path == "api/auth/device":
                return self._json({"started":self.engine.start_device_login()},202)
            if path == "api/auth/logout":
                subprocess.run(["codex","logout"],timeout=20,env={**__import__('os').environ,"CODEX_HOME":str(DATA/"codex-home")}); return self._json({"ok":True})
        except Exception as error: return self._error(str(error),500)
        return self._error("Nicht gefunden.",404)

    def do_PUT(self):
        if not self._allowed(): return self._error("Zugriff nur über Home Assistant Ingress.",403)
        if not self._admin(): return self._error("Nur konfigurierte Wiki-Administratoren dürfen Seiten bearbeiten.",403)
        path=self.path_only
        if not path.startswith("api/manual/"): return self._error("Nicht gefunden.",404)
        name=path.removeprefix("api/manual/")
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}",name): return self._error("Ungültiger Seitenname.")
        try: content=str(self._body().get("content") or "")
        except Exception: return self._error("Ungültige Anfrage.")
        if not content.strip() or len(content.encode())>100_000: return self._error("Die Seite ist leer oder zu groß.")
        if any(pattern.search(content) for pattern in SECRET_VALUE_PATTERNS): return self._error("Die Seite enthält ein geheimnisähnliches Muster.")
        temporary=(MANUAL/f"{name}.md.new"); temporary.write_text(content,encoding="utf-8"); temporary.replace(MANUAL/f"{name}.md")
        MANUAL_DIRTY.touch()
        started=self.engine.trigger("manual_edit")
        return self._json({"saved":True,"update_started":started})


def main() -> None:
    engine=WikiEngine(); Handler.engine=engine
    if not (DATA/"publish-site").is_dir():
        bootstrap=Path("/app/bootstrap-site")
        if bootstrap.is_dir(): shutil.copytree(bootstrap,DATA/"publish-site")
    threading.Thread(target=scheduler,args=(engine,),daemon=True).start()
    built_version = BUILT_VERSION.read_text(encoding="utf-8").strip() if BUILT_VERSION.exists() else ""
    if built_version != runtime_version():
        engine.trigger("version_update")
    print("[haus-wiki] Dienst bereit auf Port 8099")
    ThreadingHTTPServer(("0.0.0.0",8099),Handler).serve_forever()
