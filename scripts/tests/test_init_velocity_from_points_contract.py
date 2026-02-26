#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = "/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python"
SCRIPT = REPO_ROOT / "scripts" / "init_velocity_from_points.py"


def run_test() -> None:
    if not Path(PYTHON).exists():
        raise AssertionError(f"missing venv python: {PYTHON}")

    with tempfile.TemporaryDirectory(prefix="planb_init_contract_") as td:
        root = Path(td)
        data_dir = root / "data" / "selfcap_bar_8cam60f"
        tri_dir = data_dir / "triangulation"
        tri_dir.mkdir(parents=True, exist_ok=True)

        # Two frames (0 and 5) with mostly-static background + one moving point.
        p0 = np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [2.0, 0.0, 0.0],  # moving
            ],
            dtype=np.float32,
        )
        p5 = np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [2.5, 0.0, 0.0],  # +0.5m over 5 frames => 0.1 m/frame
            ],
            dtype=np.float32,
        )
        np.save(tri_dir / "points3d_frame000000.npy", p0)
        np.save(tri_dir / "points3d_frame000005.npy", p5)

        # Baseline init template: positions at keyframe=0 only.
        total_frames = 6  # end_exclusive=6 => frame_end(inclusive)=5
        times = np.zeros((len(p0), 1), dtype=np.float32)  # keyframe 0 => 0/6
        durations = np.ones((len(p0), 1), dtype=np.float32) * 0.25
        colors = np.zeros_like(p0, dtype=np.float32)
        velocities = np.zeros_like(p0, dtype=np.float32)
        has_velocity = np.zeros((len(p0),), dtype=bool)

        baseline_npz = root / "baseline_init.npz"
        np.savez_compressed(
            baseline_npz,
            positions=p0,
            velocities=velocities,
            colors=colors,
            times=times,
            durations=durations,
            has_velocity=has_velocity,
            frame_start=0,
            frame_end=5,
            keyframe_step=5,
            mode="keyframes_with_velocity",
        )

        out_dir = root / "outputs" / "plan_b" / "selfcap_bar_8cam60f"
        cmd = [
            PYTHON,
            str(SCRIPT),
            "--data_dir",
            str(data_dir),
            "--baseline_init_npz",
            str(baseline_npz),
            "--frame_start",
            "0",
            "--frame_end_exclusive",
            str(total_frames),
            "--keyframe_step",
            "5",
            "--out_dir",
            str(out_dir),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            raise AssertionError(
                "init_velocity_from_points failed\n"
                f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
            )

        out_npz = out_dir / "init_points_planb_step5.npz"
        out_stats = out_dir / "velocity_stats.json"
        if not out_npz.exists():
            raise AssertionError(f"missing out npz: {out_npz}")
        if not out_stats.exists():
            raise AssertionError(f"missing out stats: {out_stats}")

        z = np.load(out_npz, allow_pickle=False)
        for k in ("positions", "velocities", "colors", "times", "durations", "has_velocity"):
            if k not in z.files:
                raise AssertionError(f"missing key in out npz: {k}")

        v = z["velocities"].astype(np.float32)
        hv = z["has_velocity"].astype(bool)
        if v.shape != (3, 3):
            raise AssertionError(f"unexpected velocities shape: {v.shape}")
        if hv.shape != (3,):
            raise AssertionError(f"unexpected has_velocity shape: {hv.shape}")

        # Expect at least one non-zero velocity (the moving point).
        mags = np.linalg.norm(v, axis=1)
        if not np.any(mags > 1e-6):
            raise AssertionError("expected at least one non-zero velocity")

        # Stats JSON should contain the required audit fields.
        obj = json.loads(out_stats.read_text(encoding="utf-8"))
        must_keys = {
            "baseline_init_npz",
            "out_npz",
            "keyframe_step",
            "max_match_distance",
            "clip_quantile",
            "clip_threshold_m_per_frame",
            "counts",
            "vel_mag_m_per_frame",
            "per_pair",
        }
        if not must_keys.issubset(set(obj.keys())):
            missing = must_keys - set(obj.keys())
            raise AssertionError(f"missing keys in velocity_stats.json: {sorted(missing)}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: planb init_velocity_from_points emits expected artifacts/schema")

