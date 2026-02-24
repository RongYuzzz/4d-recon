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

        (root / "notes").mkdir(parents=True, exist_ok=True)
        (root / "notes" / "demo-runbook.md").write_text("# runbook\n", encoding="utf-8")

        stats = root / "outputs" / "runA" / "stats"
        videos = root / "outputs" / "runA" / "videos"
        ckpts = root / "outputs" / "runA" / "ckpts"
        stats.mkdir(parents=True, exist_ok=True)
        videos.mkdir(parents=True, exist_ok=True)
        ckpts.mkdir(parents=True, exist_ok=True)

        (stats / "val_step0001.json").write_text('{"psnr": 1.0}', encoding="utf-8")
        (videos / "traj_4d_step1.mp4").write_bytes(b"fake-mp4")
        (ckpts / "ckpt_1.pt").write_bytes(b"fake-ckpt")

        # Strong-fusion audit: correspondences viz should be included in pack.
        corr_viz = root / "outputs" / "correspondences" / "demo" / "viz"
        corr_viz.mkdir(parents=True, exist_ok=True)
        (corr_viz / "klt_pair.png").write_bytes(b"fake-png")

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
            "notes/demo-runbook.md",
            "outputs/runA/stats/val_step0001.json",
            "outputs/runA/videos/traj_4d_step1.mp4",
            "outputs/correspondences/demo/viz/klt_pair.png",
            "git_rev.txt",
            "manifest_sha256.csv",
        }
        for name in must_have:
            if name not in names:
                raise AssertionError(f"missing required member: {name}")

        if "outputs/runA/ckpts/ckpt_1.pt" in names:
            raise AssertionError("ckpt should be excluded from tar")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: pack_evidence excludes large dirs and writes manifest")
