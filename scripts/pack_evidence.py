#!/usr/bin/env python3
"""Create a compact evidence tarball with sha256 manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import subprocess
import tarfile
from datetime import date
from pathlib import Path
from typing import Iterable

STEP_PATTERN = re.compile(r"step(\d+)")
VAL_PATTERN = re.compile(r"^val_step(\d+)\.json$")
TEST_PATTERN = re.compile(r"^test_step(\d+)\.json$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo_root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path",
    )
    parser.add_argument(
        "--out_tar",
        default="",
        help="Output tar.gz path (default: outputs/report_pack_<YYYY-MM-DD>.tar.gz)",
    )
    return parser.parse_args()


def _step_from_name(name: str, pattern: re.Pattern[str]) -> int:
    m = pattern.search(name)
    return int(m.group(1)) if m else -1


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _latest_per_run(paths: Iterable[Path], run_from_file: callable, step_from_file: callable) -> list[Path]:
    best: dict[Path, tuple[int, Path]] = {}
    for p in paths:
        run = run_from_file(p)
        step = step_from_file(p)
        current = best.get(run)
        if current is None or step > current[0]:
            best[run] = (step, p)
    return [best[k][1] for k in sorted(best)]


def collect_files(repo_root: Path) -> list[Path]:
    files: set[Path] = set()

    readme = repo_root / "README.md"
    if readme.exists():
        files.add(readme)

    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        # Protocol + execution plan are part of the evidence chain.
        for p in [
            docs_dir / "README.md",
            docs_dir / "protocol.yaml",
        ]:
            if p.exists():
                files.add(p)
        files.update(p for p in (docs_dir / "protocols").glob("*.yaml") if p.is_file())
        files.update(p for p in (docs_dir / "execution").glob("*.md") if p.is_file())
        files.update(p for p in (docs_dir / "report_pack").rglob("*") if p.is_file())

    notes_dir = repo_root / "notes"
    if notes_dir.exists():
        files.update(p for p in notes_dir.glob("*.md") if p.is_file())

    outputs = repo_root / "outputs"
    if not outputs.exists():
        return sorted(files)

    stats_latest_val = _latest_per_run(
        outputs.glob("**/stats/val_step*.json"),
        run_from_file=lambda p: p.parent.parent,
        step_from_file=lambda p: _step_from_name(p.name, VAL_PATTERN),
    )
    files.update(p for p in stats_latest_val if p.is_file())

    stats_latest_test = _latest_per_run(
        outputs.glob("**/stats/test_step*.json"),
        run_from_file=lambda p: p.parent.parent,
        step_from_file=lambda p: _step_from_name(p.name, TEST_PATTERN),
    )
    files.update(p for p in stats_latest_test if p.is_file())

    video_latest = _latest_per_run(
        outputs.glob("**/videos/traj_*.mp4"),
        run_from_file=lambda p: p.parent.parent,
        step_from_file=lambda p: _step_from_name(p.name, STEP_PATTERN),
    )
    files.update(p for p in video_latest if p.is_file())

    files.update(p for p in outputs.glob("**/t0_grad.csv") if p.is_file())

    report_pack_dir = outputs / "report_pack"
    if report_pack_dir.exists():
        files.update(p for p in report_pack_dir.rglob("*") if p.is_file())

    excluded_tokens = {"ckpts", "tb", "renders"}
    filtered = []
    for p in sorted(files):
        rel = p.relative_to(repo_root)
        if any(part in excluded_tokens for part in rel.parts):
            continue
        filtered.append(p)
    return filtered


def build_manifest(repo_root: Path, files: list[Path]) -> bytes:
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(["path", "sha256"])
    for p in files:
        writer.writerow([p.relative_to(repo_root).as_posix(), _sha256(p)])
    return sio.getvalue().encode("utf-8")


def build_git_rev_bytes(repo_root: Path) -> bytes:
    """Return a small, human-readable git provenance blob (always returns bytes)."""
    lines: list[str] = [f"repo_root: {repo_root}"]
    try:
        head = subprocess.check_output(["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True).strip()
        short = subprocess.check_output(["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"], text=True).strip()
        status = subprocess.check_output(["git", "-C", str(repo_root), "status", "--porcelain=v1"], text=True)
        status = status.strip("\n")
        lines.append(f"git_head: {head}")
        lines.append(f"git_head_short: {short}")
        lines.append("git_status_porcelain:")
        lines.append(status if status else "<clean>")
    except Exception as exc:  # pragma: no cover - depends on external git state
        lines.append(f"git: unavailable ({exc})")
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    if args.out_tar:
        out_tar = Path(args.out_tar)
        if not out_tar.is_absolute():
            out_tar = repo_root / out_tar
    else:
        out_tar = repo_root / "outputs" / f"report_pack_{date.today().isoformat()}.tar.gz"

    out_tar.parent.mkdir(parents=True, exist_ok=True)

    files = collect_files(repo_root)
    manifest_bytes = build_manifest(repo_root, files)
    git_rev_bytes = build_git_rev_bytes(repo_root)

    with tarfile.open(out_tar, "w:gz") as tf:
        for p in files:
            arcname = p.relative_to(repo_root).as_posix()
            tf.add(p, arcname=arcname)

        info = tarfile.TarInfo(name="git_rev.txt")
        info.size = len(git_rev_bytes)
        tf.addfile(info, io.BytesIO(git_rev_bytes))

        info = tarfile.TarInfo(name="manifest_sha256.csv")
        info.size = len(manifest_bytes)
        tf.addfile(info, io.BytesIO(manifest_bytes))

    print(f"wrote {out_tar} ({len(files)} files + manifest)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
