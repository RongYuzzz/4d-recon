#!/usr/bin/env python3
"""Export selected TensorBoard scalar tags from a run into CSV (and optional PNG)."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from tensorboard.backend.event_processing import event_accumulator

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_TAGS = (
    "loss/total",
    "loss/l1_raw",
    "loss/feat_raw",
    "loss_weighted/l1",
    "loss_weighted/feat",
)


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT / path


def _parse_tags(raw_tags: str) -> list[str]:
    tags = [part.strip() for part in raw_tags.split(",")]
    return [tag for tag in tags if tag]


def _derive_run_and_tb_dir(run_dir_arg: str, tb_dir_arg: str) -> tuple[Path, Path]:
    run_dir = _resolve_path(run_dir_arg) if run_dir_arg else None
    tb_dir = _resolve_path(tb_dir_arg) if tb_dir_arg else None

    if run_dir is None and tb_dir is None:
        raise ValueError("must provide --run_dir or --tb_dir")

    if run_dir is None and tb_dir is not None:
        run_dir = tb_dir.parent if tb_dir.name == "tb" else tb_dir
    if tb_dir is None and run_dir is not None:
        tb_dir = run_dir / "tb"

    if run_dir is None or tb_dir is None:
        raise AssertionError("run_dir/tb_dir resolution failed")
    return run_dir, tb_dir


def _ensure_events_exist(tb_dir: Path) -> None:
    if not tb_dir.exists():
        raise FileNotFoundError(f"tb directory missing: {tb_dir}")
    event_files = sorted(tb_dir.glob("events.*"))
    if not event_files:
        raise FileNotFoundError(f"no tensorboard event file found under: {tb_dir}")


def _load_scalars(tb_dir: Path, tags: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    acc = event_accumulator.EventAccumulator(
        str(tb_dir),
        size_guidance={event_accumulator.SCALARS: 0},
    )
    acc.Reload()
    available = set(acc.Tags().get("scalars", []))

    rows: list[dict[str, str]] = []
    missing: list[str] = []
    for tag in tags:
        if tag not in available:
            missing.append(tag)
            continue
        for item in acc.Scalars(tag):
            rows.append(
                {
                    "tag": tag,
                    "step": str(int(item.step)),
                    "value": f"{float(item.value):.9g}",
                    "wall_time": f"{float(item.wall_time):.9f}",
                }
            )

    rows.sort(key=lambda row: (row["tag"], int(row["step"])))
    return rows, missing


def _write_csv(path: Path, run_name: str, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["run_name", "tag", "step", "value", "wall_time"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "run_name": run_name,
                    "tag": row["tag"],
                    "step": row["step"],
                    "value": row["value"],
                    "wall_time": row["wall_time"],
                }
            )


def _write_plot(path: Path, rows: list[dict[str, str]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: skip png export because matplotlib is unavailable: {exc}", file=sys.stderr)
        return

    grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for row in rows:
        grouped[row["tag"]].append((int(row["step"]), float(row["value"])))

    if not grouped:
        return

    plt.figure(figsize=(9, 5))
    for tag in sorted(grouped):
        points = sorted(grouped[tag], key=lambda item: item[0])
        xs = [item[0] for item in points]
        ys = [item[1] for item in points]
        plt.plot(xs, ys, label=tag, linewidth=1.5)
    plt.xlabel("step")
    plt.ylabel("value")
    plt.title("TensorBoard Scalar Curves")
    plt.grid(alpha=0.3)
    plt.legend(loc="best", fontsize=8)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run_dir", default="", help="run directory containing tb/events.*")
    parser.add_argument("--tb_dir", default="", help="tensorboard directory path (contains events.*)")
    parser.add_argument("--out_dir", default="outputs/report_pack/diagnostics")
    parser.add_argument("--tags", default=",".join(DEFAULT_TAGS), help="comma-separated scalar tags to export")
    parser.add_argument("--plot_png", action="store_true", help="also export a loss curves png")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tags = _parse_tags(args.tags)
    if not tags:
        raise ValueError("no tags specified after parsing --tags")

    run_dir, tb_dir = _derive_run_and_tb_dir(args.run_dir, args.tb_dir)
    _ensure_events_exist(tb_dir)
    run_name = run_dir.name

    rows, missing_tags = _load_scalars(tb_dir, tags)
    out_dir = _resolve_path(args.out_dir)
    out_csv = out_dir / f"{run_name}_tb_scalars.csv"
    _write_csv(out_csv, run_name, rows)

    if missing_tags:
        for tag in missing_tags:
            print(f"WARNING: tag not found, skipped: {tag}", file=sys.stderr)

    if args.plot_png and rows:
        out_png = out_dir / f"{run_name}_loss_curves.png"
        _write_plot(out_png, rows)
        print(f"wrote {out_png}", file=sys.stderr)

    print(f"wrote {out_csv} ({len(rows)} rows)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
