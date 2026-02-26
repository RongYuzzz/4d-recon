#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAKE_SCRIPT = REPO_ROOT / "scripts" / "make_side_by_side_video.sh"
EXTRACT_SCRIPT = REPO_ROOT / "scripts" / "extract_video_frames.sh"


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, cwd=REPO_ROOT, **kwargs)


def _make_dummy_video(path: Path, color: str) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={color}:s=320x180:d=2:r=30",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(path),
    ]
    proc = _run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"failed to create dummy video:\n{proc.stdout}\n{proc.stderr}")


def run_test() -> None:
    if not MAKE_SCRIPT.exists():
        raise AssertionError(f"missing script: {MAKE_SCRIPT}")
    if not EXTRACT_SCRIPT.exists():
        raise AssertionError(f"missing script: {EXTRACT_SCRIPT}")

    with tempfile.TemporaryDirectory(prefix="planb_qual_", dir=REPO_ROOT) as td:
        root = Path(td)
        left = root / "baseline.mp4"
        right = root / "planb.mp4"
        out_dir = root / "out"
        out_video = out_dir / "planb_vs_baseline.mp4"
        frames_dir = out_dir / "frames"

        _make_dummy_video(left, "red")
        _make_dummy_video(right, "blue")

        # Missing ffmpeg should fail with clear message.
        proc_missing = _run(
            [
                "/bin/bash",
                str(MAKE_SCRIPT),
                "--left",
                str(left),
                "--right",
                str(right),
                "--out_dir",
                str(out_dir),
            ],
            env={"PATH": "/tmp/definitely-no-ffmpeg"},
        )
        if proc_missing.returncode == 0:
            raise AssertionError("script should fail when ffmpeg is unavailable")
        err_lower = (proc_missing.stderr + proc_missing.stdout).lower()
        if "ffmpeg" not in err_lower:
            raise AssertionError("missing ffmpeg error should mention ffmpeg explicitly")

        # Normal run should output side-by-side mp4.
        proc_make = _run(
            [
                "bash",
                str(MAKE_SCRIPT),
                "--left",
                str(left),
                "--right",
                str(right),
                "--out_dir",
                str(out_dir),
                "--out_name",
                out_video.name,
                "--left_label",
                "baseline_600",
                "--right_label",
                "planb_init_600",
            ]
        )
        if proc_make.returncode != 0:
            raise RuntimeError(f"make_side_by_side_video failed:\n{proc_make.stdout}\n{proc_make.stderr}")
        if not out_video.exists():
            raise AssertionError(f"side-by-side output missing: {out_video}")

        # Extract fixed frame indices for report snapshots.
        proc_extract = _run(
            [
                "bash",
                str(EXTRACT_SCRIPT),
                "--video",
                str(out_video),
                "--out_dir",
                str(frames_dir),
                "--frames",
                "0,30,59",
            ]
        )
        if proc_extract.returncode != 0:
            raise RuntimeError(f"extract_video_frames failed:\n{proc_extract.stdout}\n{proc_extract.stderr}")

        for idx in (0, 30, 59):
            jpg = frames_dir / f"frame_{idx:06d}.jpg"
            if not jpg.exists():
                raise AssertionError(f"missing extracted frame: {jpg}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: planb qualitative scripts produce side-by-side video and frame snapshots")
