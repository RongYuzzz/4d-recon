import io
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import adapt_selfcap_release_to_freetime as adapter


class SelfCapParserTests(unittest.TestCase):
    def test_parse_opencv_yml_mats(self):
        text = """%YAML:1.0
K_02: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [1000, 0, 512, 0, 1001, 384, 0, 0, 1]
Rot_02: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [1,0,0,0,1,0,0,0,1]
T_02: !!opencv-matrix
   rows: 3
   cols: 1
   dt: d
   data: [0.1, 0.2, 0.3]
"""
        mats = adapter.parse_opencv_yml_mats(text)
        self.assertIn("K_02", mats)
        self.assertIn("Rot_02", mats)
        self.assertIn("T_02", mats)
        self.assertEqual(mats["K_02"].shape, (3, 3))
        self.assertEqual(mats["T_02"].shape, (3, 1))
        self.assertAlmostEqual(float(mats["K_02"][0, 0]), 1000.0)

    def test_read_binary_ply_xyz_rgb(self):
        header = (
            b"ply\n"
            b"format binary_little_endian 1.0\n"
            b"element vertex 2\n"
            b"property float x\n"
            b"property float y\n"
            b"property float z\n"
            b"property uchar red\n"
            b"property uchar green\n"
            b"property uchar blue\n"
            b"end_header\n"
        )
        body = b"".join(
            [
                struct.pack("<fffBBB", 1.0, 2.0, 3.0, 10, 20, 30),
                struct.pack("<fffBBB", 4.0, 5.0, 6.0, 40, 50, 60),
            ]
        )
        xyz, rgb = adapter.read_binary_ply_xyz_rgb(io.BytesIO(header + body))
        self.assertEqual(xyz.shape, (2, 3))
        self.assertEqual(rgb.shape, (2, 3))
        self.assertTrue(np.allclose(xyz[1], np.array([4.0, 5.0, 6.0], dtype=np.float32)))
        self.assertTrue(np.allclose(rgb[0], np.array([10.0, 20.0, 30.0], dtype=np.float32)))

    def test_write_colmap_sparse0(self):
        camera_ids = ["02", "03"]
        K = {
            "K_02": np.array([[1000.0, 0.0, 512.0], [0.0, 1000.0, 384.0], [0.0, 0.0, 1.0]]),
            "K_03": np.array([[900.0, 0.0, 500.0], [0.0, 900.0, 360.0], [0.0, 0.0, 1.0]]),
        }
        Rot = {"Rot_02": np.eye(3), "Rot_03": np.eye(3)}
        T = {"T_02": np.zeros((3, 1)), "T_03": np.array([[0.1], [0.0], [0.0]])}
        xyz = np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]], dtype=np.float32)
        rgb = np.array([[255.0, 128.0, 0.0], [10.0, 20.0, 30.0]], dtype=np.float32)

        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "sparse" / "0"
            adapter.write_colmap_sparse0(
                out_sparse_dir=out_dir,
                camera_ids=camera_ids,
                intrinsics=K,
                rotations=Rot,
                translations=T,
                points_xyz=xyz,
                points_rgb=rgb,
                image_width=960,
                image_height=540,
                image_downscale=2,
            )
            self.assertTrue((out_dir / "cameras.bin").exists())
            self.assertTrue((out_dir / "images.bin").exists())
            self.assertTrue((out_dir / "points3D.bin").exists())


if __name__ == "__main__":
    unittest.main()
