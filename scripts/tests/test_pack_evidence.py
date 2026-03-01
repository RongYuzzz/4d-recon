#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "pack_evidence.py"


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="pack_evidence_test_") as td:
        root = Path(td)
        (root / "README.md").write_text("demo\n", encoding="utf-8")

        docs_runbook = root / "docs" / "runbook"
        docs_runbook.mkdir(parents=True, exist_ok=True)
        (docs_runbook / "demo.md").write_text("# demo runbook\n", encoding="utf-8")

        (root / "notes").mkdir(parents=True, exist_ok=True)
        (root / "notes" / "demo-runbook.md").write_text("# runbook\n", encoding="utf-8")

        stats = root / "outputs" / "runA" / "stats"
        videos = root / "outputs" / "runA" / "videos"
        ckpts = root / "outputs" / "runA" / "ckpts"
        stats.mkdir(parents=True, exist_ok=True)
        videos.mkdir(parents=True, exist_ok=True)
        ckpts.mkdir(parents=True, exist_ok=True)

        (stats / "val_step0001.json").write_text('{"psnr": 1.0}', encoding="utf-8")
        (stats / "throughput.json").write_text(
            '{"source_stats":"train_step0199.json","step":199,"elapsed_sec":100.0,"iter_per_sec":2.0}',
            encoding="utf-8",
        )
        (videos / "traj_4d_step1.mp4").write_bytes(b"fake-mp4")
        (ckpts / "ckpt_1.pt").write_bytes(b"fake-ckpt")

        # Strong-fusion audit: correspondences viz should be included in pack.
        corr_viz = root / "outputs" / "correspondences" / "demo" / "viz"
        corr_viz.mkdir(parents=True, exist_ok=True)
        (corr_viz / "klt_pair.png").write_bytes(b"fake-png")

        # Plan-B audit artifacts should be included in pack.
        planb_dir = root / "outputs" / "plan_b" / "selfcap_bar_8cam60f"
        planb_dir.mkdir(parents=True, exist_ok=True)
        (planb_dir / "velocity_stats.json").write_text('{"ok": true}\n', encoding="utf-8")
        (planb_dir / "init_points_planb_step5.npz").write_bytes(b"fake-npz")

        # Qualitative side-by-side artifacts should be included when present.
        qual_dir = root / "outputs" / "qualitative" / "planb_vs_baseline"
        qual_frames = qual_dir / "frames"
        qual_frames.mkdir(parents=True, exist_ok=True)
        (qual_dir / "planb_vs_baseline_step599.mp4").write_bytes(b"fake-side-by-side")
        (qual_frames / "frame_000000.jpg").write_bytes(b"fake-jpg")

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
        if proc.returncode != 0:
            raise RuntimeError(f"pack_evidence failed:\n{proc.stdout}\n{proc.stderr}")

        if not out_tar.exists():
            raise AssertionError("output tar missing")

        with tarfile.open(out_tar, "r:gz") as tf:
            names = set(tf.getnames())

        must_have = {
            "README.md",
            "docs/runbook/demo.md",
            "notes/demo-runbook.md",
            "outputs/runA/stats/val_step0001.json",
            "outputs/runA/stats/throughput.json",
            "outputs/runA/videos/traj_4d_step1.mp4",
            "outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json",
            "outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz",
            "outputs/correspondences/demo/viz/klt_pair.png",
            "outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4",
            "outputs/qualitative/planb_vs_baseline/frames/frame_000000.jpg",
            "git_rev.txt",
            "manifest_sha256.csv",
        }
        for name in must_have:
            if name not in names:
                raise AssertionError(f"missing required member: {name}")

        if "outputs/runA/ckpts/ckpt_1.pt" in names:
            raise AssertionError("ckpt should be excluded from tar")


def test_pack_evidence_contract() -> None:
    run_test()


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: pack_evidence excludes large dirs and writes manifest")
