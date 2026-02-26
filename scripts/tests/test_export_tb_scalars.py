#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from tensorboard.compat.proto.event_pb2 import Event
from tensorboard.compat.proto.summary_pb2 import Summary
from tensorboard.summary.writer.event_file_writer import EventFileWriter


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "export_tb_scalars.py"


def _add_scalar(writer: EventFileWriter, tag: str, step: int, value: float) -> None:
    event = Event(
        wall_time=time.time(),
        step=step,
        summary=Summary(value=[Summary.Value(tag=tag, simple_value=float(value))]),
    )
    writer.add_event(event)


def _write_tb_events(tb_dir: Path) -> None:
    tb_dir.mkdir(parents=True, exist_ok=True)
    writer = EventFileWriter(str(tb_dir))
    try:
        _add_scalar(writer, "loss/total", 0, 1.0)
        _add_scalar(writer, "loss/total", 1, 0.9)
        _add_scalar(writer, "loss/l1_raw", 0, 0.8)
        _add_scalar(writer, "loss/l1_raw", 1, 0.7)
        _add_scalar(writer, "loss_weighted/l1", 0, 0.6)
        _add_scalar(writer, "loss_weighted/l1", 1, 0.5)
    finally:
        writer.flush()
        writer.close()


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="tb_scalars_test_", dir=REPO_ROOT) as td:
        root = Path(td)
        run_dir = root / "outputs" / "protocol_v1" / "selfcap_bar_8cam60f" / "feature_loss_v2_postfix_600"
        tb_dir = run_dir / "tb"
        out_dir = root / "outputs" / "report_pack" / "diagnostics"
        _write_tb_events(tb_dir)

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--run_dir",
            str(run_dir.relative_to(REPO_ROOT)),
            "--out_dir",
            str(out_dir.relative_to(REPO_ROOT)),
            "--tags",
            "loss/total,loss/l1_raw,missing/tag",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            raise RuntimeError(f"export_tb_scalars failed:\n{proc.stdout}\n{proc.stderr}")
        if proc.stdout.strip():
            raise AssertionError(f"stdout should stay empty, got: {proc.stdout.strip()}")

        out_csv = out_dir / "feature_loss_v2_postfix_600_tb_scalars.csv"
        if not out_csv.exists():
            raise AssertionError(f"csv missing: {out_csv}")

        rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8", newline="")))
        if len(rows) != 4:
            raise AssertionError(f"expected 4 rows (2 tags * 2 steps), got {len(rows)}")

        tags = sorted({row["tag"] for row in rows})
        if tags != ["loss/l1_raw", "loss/total"]:
            raise AssertionError(f"unexpected tags: {tags}")

        step_map: dict[str, list[int]] = {}
        for row in rows:
            step_map.setdefault(row["tag"], []).append(int(row["step"]))
            float(row["value"])
        if step_map.get("loss/total") != [0, 1]:
            raise AssertionError(f"unexpected steps for loss/total: {step_map.get('loss/total')}")
        if step_map.get("loss/l1_raw") != [0, 1]:
            raise AssertionError(f"unexpected steps for loss/l1_raw: {step_map.get('loss/l1_raw')}")
        if "missing/tag" in tags:
            raise AssertionError("missing tag should be skipped")

        if "WARNING" not in proc.stderr or "missing/tag" not in proc.stderr:
            raise AssertionError("missing tag should emit warning in stderr")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: export_tb_scalars exports selected tags and warns on missing tags")
