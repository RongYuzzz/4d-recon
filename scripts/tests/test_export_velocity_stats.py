#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "export_velocity_stats.py"


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="velocity_stats_test_") as td:
        root = Path(td)
        init_npz = root / "init.npz"
        ckpt = root / "ckpt_599.pt"
        out_md = root / "velocity_stats.md"

        np.savez_compressed(
            init_npz,
            velocities=np.asarray([[0.0, 0.0, 0.0], [3.0, 4.0, 0.0]], dtype=np.float32),
            times=np.asarray([[0.0], [1.0]], dtype=np.float32),
            durations=np.asarray([[0.2], [0.2]], dtype=np.float32),
        )
        torch.save(
            {
                "step": 599,
                "splats": {
                    "velocities": torch.tensor([[0.0, 0.0, 0.0], [0.0, 0.0, 2.0]], dtype=torch.float32),
                    "times": torch.tensor([[0.1], [0.9]], dtype=torch.float32),
                    # Checkpoint stores log-duration in trainer; use exp(log(0.3)) = 0.3.
                    "durations": torch.tensor([[-1.2039728], [-1.2039728]], dtype=torch.float32),
                },
            },
            ckpt,
        )

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--init_npz_path",
            str(init_npz),
            "--ckpt_path",
            str(ckpt),
            "--out_md_path",
            str(out_md),
            "--eps",
            "1e-4",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise AssertionError(
                "export_velocity_stats.py failed\n"
                f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
            )

        if not out_md.exists():
            raise AssertionError(f"missing markdown output: {out_md}")
        text = out_md.read_text(encoding="utf-8")

        required_snippets = [
            "step0 (init npz)",
            "step599 (ckpt)",
            "ratio(||v|| < eps)",
            "min",
            "mean",
            "p50",
            "p90",
            "p99",
            "max",
            "times min/mean/max",
            "durations min/mean/max",
        ]
        for snippet in required_snippets:
            if snippet not in text:
                raise AssertionError(f"missing field in markdown output: {snippet}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: export_velocity_stats emits required markdown fields")
