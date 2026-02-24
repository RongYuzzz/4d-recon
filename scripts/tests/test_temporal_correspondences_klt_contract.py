import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = "/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python"
GEN_SCRIPT = REPO_ROOT / "scripts" / "generate_synthetic_scene01.py"
KLT_SCRIPT = REPO_ROOT / "scripts" / "extract_temporal_correspondences_klt.py"


class TemporalCorrespondenceKLTContractTests(unittest.TestCase):
    def test_contract_on_synthetic_scene(self):
        gen = subprocess.run([PYTHON, str(GEN_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(gen.returncode, 0, msg=f"generator failed\n{gen.stdout}\n{gen.stderr}")

        data_dir = REPO_ROOT / "data" / "scene01" / "colmap"
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            out_npz = tmp / "temporal_corr.npz"
            viz_dir = tmp / "viz"

            cmd = [
                PYTHON,
                str(KLT_SCRIPT),
                "--data_dir",
                str(data_dir),
                "--camera_ids",
                "cam00,cam01",
                "--frame_start",
                "0",
                "--num_frames",
                "3",
                "--max_tracks_per_pair",
                "300",
                "--min_track_len",
                "1",
                "--fb_err_thresh",
                "1.5",
                "--fb_weight_sigma",
                "1.5",
                "--fb_weight_min",
                "0.05",
                "--out_npz",
                str(out_npz),
                "--viz_dir",
                str(viz_dir),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, msg=f"extractor failed\n{res.stdout}\n{res.stderr}")

            self.assertTrue(out_npz.exists())
            z = np.load(out_npz, allow_pickle=True)

            required = {
                "camera_names",
                "frame_start",
                "num_frames",
                "image_width",
                "image_height",
                "src_cam_idx",
                "src_frame_offset",
                "dst_frame_offset",
                "src_xy",
                "dst_xy",
                "weight",
            }
            self.assertTrue(required.issubset(set(z.files)))

            src_xy = z["src_xy"]
            self.assertEqual(src_xy.ndim, 2)
            self.assertEqual(src_xy.shape[1], 2)
            self.assertGreater(src_xy.shape[0], 0)

            weight = z["weight"].astype(np.float32)
            self.assertEqual(weight.ndim, 1)
            self.assertEqual(weight.shape[0], src_xy.shape[0])
            self.assertTrue(np.all(np.isfinite(weight)))
            self.assertTrue(np.all(weight >= 0.0))
            self.assertTrue(np.all(weight <= 1.0))
            # FB-weight should provide non-trivial confidence distribution.
            self.assertFalse(np.allclose(weight, np.ones_like(weight)))

            viz_images = list(viz_dir.glob("*.jpg"))
            self.assertGreaterEqual(len(viz_images), 1)


if __name__ == "__main__":
    unittest.main()
