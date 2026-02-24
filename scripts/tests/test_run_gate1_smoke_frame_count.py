#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_gate1_smoke.sh"
RW_PATH = (
    REPO_ROOT
    / "third_party"
    / "FreeTimeGsVanilla"
    / "datasets"
    / "read_write_model.py"
)


def load_rw_module():
    spec = importlib.util.spec_from_file_location("rw", RW_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module at {RW_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_min_colmap(source_dir: Path, rw) -> None:
    Camera = rw.Camera
    Image = rw.Image
    Point3D = rw.Point3D

    (source_dir / "images").mkdir(parents=True, exist_ok=True)
    (source_dir / "images" / "camA.jpg").write_bytes(b"fake-jpeg")

    cameras = {
        1: Camera(
            id=1,
            model="PINHOLE",
            width=64,
            height=48,
            params=np.array([40.0, 40.0, 32.0, 24.0], dtype=np.float64),
        ),
    }
    images = {
        1: Image(
            id=1,
            qvec=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            tvec=np.array([0.0, 0.0, 0.0], dtype=np.float64),
            camera_id=1,
            name="camA.jpg",
            xys=np.array([[10.0, 10.0]], dtype=np.float64),
            point3D_ids=np.array([1], dtype=np.int64),
        ),
    }
    points3d = {
        1: Point3D(
            id=1,
            xyz=np.array([0.0, 0.0, 1.0], dtype=np.float64),
            rgb=np.array([128, 128, 128], dtype=np.uint8),
            error=0.1,
            image_ids=np.array([1], dtype=np.int32),
            point2D_idxs=np.array([0], dtype=np.int32),
        ),
    }

    sparse0 = source_dir / "sparse" / "0"
    sparse0.mkdir(parents=True, exist_ok=True)
    rw.write_model(cameras, images, points3d, str(sparse0), ext=".bin")


def write_frame_points(source_sparse: Path, frame_idx: int, x_value: float, rw) -> None:
    Point3D = rw.Point3D
    points3d = {
        1: Point3D(
            id=1,
            xyz=np.array([x_value, 0.0, 1.0], dtype=np.float64),
            rgb=np.array([10, 20, 30], dtype=np.uint8),
            error=0.1,
            image_ids=np.array([1], dtype=np.int32),
            point2D_idxs=np.array([0], dtype=np.int32),
        )
    }
    frame_dir = source_sparse / f"frame_{frame_idx}"
    frame_dir.mkdir(parents=True, exist_ok=True)
    rw.write_points3D_binary(points3d, str(frame_dir / "points3D.bin"))


def run_test() -> None:
    rw = load_rw_module()
    with tempfile.TemporaryDirectory(prefix="gate1_smoke_frame_count_") as tmp:
        root = Path(tmp)
        source_dir = root / "source"
        build_min_colmap(source_dir, rw)

        # Source range [0, 3): only frame_0 and frame_2 exist.
        sparse_root = source_dir / "sparse"
        write_frame_points(sparse_root, frame_idx=0, x_value=0.0, rw=rw)
        write_frame_points(sparse_root, frame_idx=2, x_value=2.0, rw=rw)

        adapted_dir = root / "adapted"
        result_dir = root / "result"

        # Use a fake FreeTime base dir so this test does not run real training.
        fake_base = root / "fake_base"
        (fake_base / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
        (fake_base / ".venv" / "bin" / "python").write_text(
            "#!/usr/bin/env bash\nexec python3 \"$@\"\n",
            encoding="utf-8",
        )
        os.chmod(fake_base / ".venv" / "bin" / "python", 0o755)

        captured_args = root / "run_pipeline_args.txt"
        (fake_base / "run_pipeline.sh").write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\nprintf \"%s\\n\" \"$@\" > \"$CAPTURE_ARGS\"\n",
            encoding="utf-8",
        )
        os.chmod(fake_base / "run_pipeline.sh", 0o755)

        env = os.environ.copy()
        env["BASE_DIR"] = str(fake_base)
        env["ADAPTER_PYTHON"] = sys.executable
        env["CAPTURE_ARGS"] = str(captured_args)
        env["MAX_STEPS"] = "2"

        cmd = [
            "bash",
            str(SCRIPT_PATH),
            str(source_dir),
            str(sparse_root),
            str(adapted_dir),
            str(result_dir),
            "0",  # gpu_id
            "0",  # frame_start
            "3",  # frame_end (exclusive)
            "1",  # keyframe_step
            "default_keyframe_small",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            raise AssertionError(
                "run_gate1_smoke.sh failed unexpectedly\n"
                f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
            )
        if not captured_args.exists():
            raise AssertionError("fake run_pipeline.sh was not invoked")

        args = captured_args.read_text(encoding="utf-8").splitlines()
        if len(args) < 5:
            raise AssertionError(f"unexpected run_pipeline args: {args}")

        # Arg 5 to run_pipeline is end_frame; it must match exported triangulation frame count.
        end_frame = int(args[4])
        if end_frame != 2:
            raise AssertionError(
                f"expected remapped end_frame=2 from triangulation frame count, got {end_frame}"
            )


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: run_gate1_smoke remaps train range to exported triangulation frame count")
