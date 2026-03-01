from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "pack_evidence.py"


class PackEvidenceProtocolV2SourcesTests(unittest.TestCase):
    def test_pack_should_include_vggt_cache_cfg_and_cue_mining_viz(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pack_evidence_v2_", dir=REPO_ROOT) as td:
            root = Path(td)
            (root / "README.md").write_text("demo\n", encoding="utf-8")
            (root / "notes").mkdir(parents=True, exist_ok=True)
            (root / "notes" / "demo-runbook.md").write_text("# runbook\n", encoding="utf-8")

            # vggt cache truth sources
            vggt_dir = root / "outputs" / "vggt_cache" / "demo_cache"
            vggt_dir.mkdir(parents=True, exist_ok=True)
            (vggt_dir / "gt_cache.npz").write_bytes(b"fake-npz")
            (vggt_dir / "meta.json").write_text('{"ok": true}\n', encoding="utf-8")
            vggt_viz = vggt_dir / "viz_pca"
            vggt_viz.mkdir(parents=True, exist_ok=True)
            (vggt_viz / "pca.jpg").write_bytes(b"fake-jpg")

            # cue mining: include quality + viz only, exclude heavy npz by policy
            cue_dir = root / "outputs" / "cue_mining" / "demo"
            cue_viz = cue_dir / "viz"
            cue_viz.mkdir(parents=True, exist_ok=True)
            (cue_dir / "quality.json").write_text('{"score": 1.0}\n', encoding="utf-8")
            (cue_viz / "pca.png").write_bytes(b"fake-png")
            (cue_dir / "pseudo_masks.npz").write_bytes(b"heavy-npz")

            # cfg.yml truth source under any run
            run_dir = root / "outputs" / "protocol_v2" / "selfcap_bar_8cam60f" / "demo_run"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "cfg.yml").write_text("demo: true\n", encoding="utf-8")

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
                "outputs/vggt_cache/demo_cache/gt_cache.npz",
                "outputs/vggt_cache/demo_cache/meta.json",
                "outputs/vggt_cache/demo_cache/viz_pca/pca.jpg",
                "outputs/cue_mining/demo/quality.json",
                "outputs/cue_mining/demo/viz/pca.png",
                "outputs/protocol_v2/selfcap_bar_8cam60f/demo_run/cfg.yml",
            }
            for name in must_have:
                self.assertIn(name, names)

            # Avoid packing large cue_mining blobs by default.
            self.assertNotIn("outputs/cue_mining/demo/pseudo_masks.npz", names)


if __name__ == "__main__":
    unittest.main()
