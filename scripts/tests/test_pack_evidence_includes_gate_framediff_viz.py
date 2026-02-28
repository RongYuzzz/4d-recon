from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "pack_evidence.py"


class PackEvidenceIncludesGateFramediffVizTests(unittest.TestCase):
    def test_pack_should_include_gate_framediff_viz_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pack_evidence_gateviz_", dir=REPO_ROOT) as td:
            root = Path(td)
            (root / "README.md").write_text("demo\n", encoding="utf-8")
            (root / "notes").mkdir(parents=True, exist_ok=True)
            (root / "notes" / "demo-runbook.md").write_text("# runbook\n", encoding="utf-8")

            gate_dir = root / "outputs" / "viz" / "gate_framediff" / "demo"
            gate_dir.mkdir(parents=True, exist_ok=True)
            (gate_dir / "frame010_cam02_overlay_compare.png").write_bytes(b"fake-png")
            (gate_dir / "overlay_activation_summary.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (gate_dir / "README.txt").write_text("demo\n", encoding="utf-8")

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
                "outputs/viz/gate_framediff/demo/frame010_cam02_overlay_compare.png",
                "outputs/viz/gate_framediff/demo/overlay_activation_summary.csv",
                "outputs/viz/gate_framediff/demo/README.txt",
            }
            for name in must_have:
                self.assertIn(name, names)


if __name__ == "__main__":
    unittest.main()

