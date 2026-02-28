#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tarfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "pack_evidence.py"


def test_pack_evidence_follows_top_level_outputs_symlink_dirs(tmp_path: Path) -> None:
    root = tmp_path
    (root / "README.md").write_text("demo\n", encoding="utf-8")

    (root / "notes").mkdir(parents=True, exist_ok=True)
    (root / "notes" / "demo.md").write_text("# demo\n", encoding="utf-8")

    # Create a real run directory outside `outputs/`, then symlink it into `outputs/protocol_v2`.
    real_run = root / "_real" / "runA"
    (real_run / "stats").mkdir(parents=True, exist_ok=True)
    (real_run / "videos").mkdir(parents=True, exist_ok=True)
    (real_run / "stats" / "val_step0001.json").write_text('{"psnr": 1.0}\n', encoding="utf-8")
    (real_run / "stats" / "test_step0001.json").write_text('{"psnr": 1.0}\n', encoding="utf-8")
    (real_run / "stats" / "throughput.json").write_text(
        '{"source_stats":"test_step0001.json","step":1,"elapsed_sec":1.0,"iter_per_sec":1.0}\n',
        encoding="utf-8",
    )
    (real_run / "videos" / "traj_4d_step1.mp4").write_bytes(b"fake-mp4")
    (real_run / "cfg.yml").write_text("seed: 0\n", encoding="utf-8")

    outputs = root / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "protocol_v2").symlink_to(root / "_real", target_is_directory=True)

    out_tar = root / "pack.tar.gz"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--repo_root",
        str(root),
        "--out_tar",
        str(out_tar),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"pack_evidence failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert out_tar.exists(), "expected output tar to exist"

    with tarfile.open(out_tar, "r:gz") as tf:
        names = set(tf.getnames())

    must_have = {
        "outputs/protocol_v2/runA/stats/val_step0001.json",
        "outputs/protocol_v2/runA/stats/test_step0001.json",
        "outputs/protocol_v2/runA/stats/throughput.json",
        "outputs/protocol_v2/runA/videos/traj_4d_step1.mp4",
        "outputs/protocol_v2/runA/cfg.yml",
    }
    for name in must_have:
        assert name in names, f"missing required member: {name}"

