#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "thuman4_inventory.py"


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_thuman4_inventory_emits_adapter_command_and_detects_cams() -> None:
    with tempfile.TemporaryDirectory(prefix="thuman4_inv_") as td:
        root = Path(td)
        subj = root / "subject00"
        for cam in ("000", "001", "002", "003", "004", "005", "006", "007"):
            for frame in (0, 1, 2, 3):
                _touch(subj / "images" / cam / f"{frame}.jpg")
                _touch(subj / "masks" / cam / f"{frame}.png")

        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input_dir",
                str(subj),
                "--num_cams",
                "8",
                "--num_frames",
                "4",
            ],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        out = proc.stdout
        assert "detected_cameras" in out
        assert "python3 scripts/adapt_thuman4_release_to_freetime.py" in out
        assert "--camera_ids" in out and "--output_camera_ids" in out

