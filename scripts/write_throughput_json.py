#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _fail(msg: str) -> "NoReturn":
    raise SystemExit(f"ERROR: {msg}")


def main() -> int:
    if len(sys.argv) != 2:
        _fail("usage: write_throughput_json.py <result_dir>")

    result_dir = Path(sys.argv[1]).resolve()
    stats_dir = result_dir / "stats"
    if not stats_dir.is_dir():
        _fail(f"missing stats dir: {stats_dir}")

    stats_files = sorted(stats_dir.glob("train_step*.json"))
    if not stats_files:
        _fail(f"no train_step stats found under {stats_dir}")

    best_path: Path | None = None
    best_step = -1
    best_elapsed = 0.0
    for path in stats_files:
        m = re.match(r"train_step(\d+)\.json$", path.name)
        if m is None:
            continue
        step = int(m.group(1))
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _fail(f"invalid json in {path}: {exc}")
        if "ellipse_time" not in data:
            _fail(f"missing ellipse_time in {path}")
        elapsed = float(data["ellipse_time"])
        if elapsed <= 0:
            _fail(f"ellipse_time must be >0 in {path}, got {elapsed}")
        if step > best_step:
            best_path = path
            best_step = step
            best_elapsed = elapsed

    if best_path is None:
        _fail(f"no valid train_step*.json found under {stats_dir}")

    throughput = {
        "source_stats": best_path.name,
        "step": best_step,
        "elapsed_sec": best_elapsed,
        "iter_per_sec": float(best_step + 1) / best_elapsed,
    }
    out_path = stats_dir / "throughput.json"
    out_path.write_text(json.dumps(throughput, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[Throughput] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
