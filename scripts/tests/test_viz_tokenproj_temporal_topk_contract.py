from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "viz_tokenproj_temporal_topk.py"


class VizTokenProjTemporalTopKContractTests(unittest.TestCase):
    def test_script_should_write_expected_viz(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tokenproj_topk_viz_", dir=REPO_ROOT) as td:
            root = Path(td)
            cache_npz = root / "gt_cache.npz"
            out_dir = root / "viz"

            rng = np.random.RandomState(0)
            # Minimal cache: T=2, V=1, C=8, H=W=3
            phi = rng.randn(2, 1, 8, 3, 3).astype(np.float32)
            np.savez_compressed(
                cache_npz,
                phi=phi,
                camera_names=np.array(["02"]),
                frame_start=np.int32(0),
                num_frames=np.int32(2),
                phi_name=np.array("token_proj"),
                vggt_mode=np.array("crop"),
                input_size=np.array([48, 64], dtype=np.int32),
                phi_size=np.array([3, 3], dtype=np.int32),
            )

            cmd = [
                sys.executable,
                str(SCRIPT),
                "--cache_npz",
                str(cache_npz),
                "--out_dir",
                str(out_dir),
                "--frames",
                "0",
                "--topk",
                "3",
                "--camera_ids",
                "02",
                "--cell",
                "20",
                "--gap",
                "40",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
            self.assertEqual(proc.returncode, 0, msg=f"stderr:\n{proc.stderr}")

            out_img = out_dir / "token_top3_cam02_frame000000_to_000001.jpg"
            self.assertTrue(out_img.exists(), msg=f"missing output image: {out_img}")
            self.assertGreater(out_img.stat().st_size, 0, msg="output image is empty")


if __name__ == "__main__":
    unittest.main()

