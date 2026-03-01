from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "pack_evidence.py"


class PackEvidenceIncludesSpatialTopKFramesTests(unittest.TestCase):
    def test_pack_should_include_spatial_metrics_topk_frames_note_and_readme(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pack_evidence_spatial_topk_", dir=REPO_ROOT) as td:
            root = Path(td)
            (root / "README.md").write_text("demo\n", encoding="utf-8")
            (root / "notes").mkdir(parents=True, exist_ok=True)
            (root / "notes" / "demo-runbook.md").write_text("# runbook\n", encoding="utf-8")

            (root / "notes" / "protocol_v2_spatial_metrics_topk_frames.md").write_text(
                "# spatial top-k\n",
                encoding="utf-8",
            )

            out_readme = (
                root
                / "outputs"
                / "report_pack"
                / "diagnostics"
                / "spatial_metrics_topk_frames_demo"
                / "README.md"
            )
            out_readme.parent.mkdir(parents=True, exist_ok=True)
            out_readme.write_text("# top-k frames\n", encoding="utf-8")

            out_tar = root / "pack.tar.gz"
            cmd = [
                sys.executable,
                str(SCRIPT),
                "--repo_root",
                str(root),
                "--out_tar",
                str(out_tar),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, msg=f"stderr:\n{proc.stderr}")

            with tarfile.open(out_tar, "r:gz") as tf:
                names = set(tf.getnames())

            must_have = {
                "notes/protocol_v2_spatial_metrics_topk_frames.md",
                "outputs/report_pack/diagnostics/spatial_metrics_topk_frames_demo/README.md",
            }
            for name in must_have:
                self.assertIn(name, names)


if __name__ == "__main__":
    unittest.main()
