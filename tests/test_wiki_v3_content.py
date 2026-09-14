from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_weekly_pipeline import _write_source
from generate_docs import main as generate_docs


ROOT = Path(__file__).resolve().parents[1]


class WikiV3ContentTests(unittest.TestCase):
    def test_backup_overview_replaces_bootstrap_preserves_manual_and_builds(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            source = project / "source"
            source.mkdir()
            docs = project / "docs"
            shutil.copytree(ROOT / "homewiki_gateway/runtime/docs", docs)
            shutil.copy2(ROOT / "homewiki_gateway/runtime/mkdocs.yml", project / "mkdocs.yml")
            _write_source(source, [{
                "alias": "Flurlicht",
                "use_blueprint": {"path": "example/lighting.yaml"},
            }])
            areas = source / ".storage/core.area_registry"
            document = json.loads(areas.read_text(encoding="utf-8"))
            document["data"]["areas"][0].pop("floor_id")
            areas.write_text(json.dumps(document), encoding="utf-8")
            overrides = project / "overrides.yaml"
            overrides.write_text("{}\n", encoding="utf-8")
            manual = docs / "manuell/index.md"
            manual.write_text("# Eigene Hinweise\n\nBleibt erhalten.\n", encoding="utf-8")
            args = ["generate_docs.py", str(source), str(docs), "--overrides", str(overrides), "--inventory-source-date", "2026-09-14T03:45:00+02:00"]
            with patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
                generate_docs()
            first = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()}
            with patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
                generate_docs()
            self.assertEqual(first, {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()})
            self.assertIn("Bleibt erhalten", manual.read_text(encoding="utf-8"))
            home = (docs / "index.md").read_text(encoding="utf-8")
            self.assertIn("2026-09-14T03:45:00+02:00", home)
            self.assertNotIn("Noch kein Backup", home)
            room_index = (docs / "raeume/index.md").read_text(encoding="utf-8")
            self.assertIn("generated/flur.md", room_index)
            automation = (docs / "automationen/generated/flurlicht.md").read_text(encoding="utf-8")
            self.assertNotIn("Status: aktiv", automation)
            self.assertNotIn("Stromverbrauch", automation)
            self.assertIn("nicht aufgelöst", automation)
            result = subprocess.run([sys.executable, "-m", "mkdocs", "build", "--strict", "--config-file", str(project / "mkdocs.yml")], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / "site/admin/index.html").is_file())


if __name__ == "__main__":
    unittest.main()
