import io
import struct
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = "/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python"
SCRIPT = REPO_ROOT / "scripts" / "adapt_selfcap_release_to_freetime.py"


def _opencv_matrix_block(name: str, rows: int, cols: int, data: list[float]) -> str:
    data_str = ", ".join(str(float(v)) for v in data)
    return (
        f"{name}: !!opencv-matrix\n"
        f"   rows: {rows}\n"
        f"   cols: {cols}\n"
        "   dt: d\n"
        f"   data: [{data_str}]\n"
    )


def _build_binary_ply(points: list[tuple[float, float, float, int, int, int]]) -> bytes:
    header = (
        b"ply\n"
        b"format binary_little_endian 1.0\n"
        + f"element vertex {len(points)}\n".encode("ascii")
        + b"property float x\n"
        + b"property float y\n"
        + b"property float z\n"
        + b"property uchar red\n"
        + b"property uchar green\n"
        + b"property uchar blue\n"
        + b"end_header\n"
    )
    body = io.BytesIO()
    for x, y, z, r, g, b in points:
        body.write(struct.pack("<fffBBB", x, y, z, r, g, b))
    return header + body.getvalue()


def _add_bytes_to_tar(tf: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tf.addfile(info, io.BytesIO(data))


class SelfCapCliNoImagesTests(unittest.TestCase):
    def test_cli_no_images_with_minimal_tar(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            tar_path = td_path / "bar-release.tar.gz"
            out_dir = td_path / "out"

            intri = "%YAML:1.0\n" + _opencv_matrix_block(
                "K_02",
                3,
                3,
                [1000, 0, 320, 0, 1000, 240, 0, 0, 1],
            )
            extri = "%YAML:1.0\n" + _opencv_matrix_block(
                "Rot_02", 3, 3, [1, 0, 0, 0, 1, 0, 0, 0, 1]
            ) + _opencv_matrix_block("T_02", 3, 1, [0, 0, 0])

            ply0 = _build_binary_ply(
                [
                    (0.0, 0.0, 0.0, 255, 0, 0),
                    (1.0, 0.0, 0.0, 0, 255, 0),
                    (0.0, 1.0, 0.0, 0, 0, 255),
                ]
            )
            ply1 = _build_binary_ply(
                [
                    (0.1, 0.0, 0.0, 255, 10, 0),
                    (1.1, 0.0, 0.0, 0, 255, 10),
                    (0.0, 1.1, 0.0, 10, 0, 255),
                ]
            )

            with tarfile.open(tar_path, "w:gz") as tf:
                _add_bytes_to_tar(tf, "bar-release/optimized/intri.yml", intri.encode("utf-8"))
                _add_bytes_to_tar(tf, "bar-release/optimized/extri.yml", extri.encode("utf-8"))
                _add_bytes_to_tar(tf, "bar-release/pcds/000000.ply", ply0)
                _add_bytes_to_tar(tf, "bar-release/pcds/000001.ply", ply1)

            cmd = [
                PYTHON,
                str(SCRIPT),
                "--tar_gz",
                str(tar_path),
                "--output_dir",
                str(out_dir),
                "--camera_ids",
                "02",
                "--frame_start",
                "0",
                "--num_frames",
                "2",
                "--no_images",
                "--image_width",
                "640",
                "--image_height",
                "480",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            self.assertTrue((out_dir / "triangulation" / "points3d_frame000000.npy").exists())
            self.assertTrue((out_dir / "triangulation" / "points3d_frame000001.npy").exists())
            self.assertTrue((out_dir / "sparse" / "0" / "cameras.bin").exists())


if __name__ == "__main__":
    unittest.main()
