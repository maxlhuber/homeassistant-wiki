from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from weekly_update import _review_is_approved  # noqa: E402


class ReviewApprovalTests(unittest.TestCase):
    def test_approval_is_bound_to_exact_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            approval = Path(temporary) / "approval.json"
            approval.write_text(
                json.dumps({"approved": True, "snapshot_fingerprint": "a" * 64}),
                encoding="utf-8",
            )
            self.assertTrue(_review_is_approved(approval, "a" * 64))
            self.assertFalse(_review_is_approved(approval, "b" * 64))


if __name__ == "__main__":
    unittest.main()
