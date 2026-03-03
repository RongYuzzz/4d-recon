# OpenProposal (Waiting THUman4.0) — CPU-Only Prep Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 THUman4.0 数据仍在上传/不可用期间，完成所有 **不依赖数据本体** 的准备工作：把 Phase 1 的“数据一到即可跑通”的步骤写死 + 增加一个 THUman raw inventory 工具（自动吐 adapter 命令）+ 把 waiting‑THUman smoke 的状态固化成可审计说明。

**Architecture:** 本计划只做 **CPU-only + code/docs**；不运行训练、不运行 COLMAP、不触碰任何真实数据文件内容。遵守 **local-eval only**：任何公开数据帧/GT mask 只允许留在本机 `data/` 与 `outputs/`，禁止进入 git/PR/report-pack。

**Tech Stack:** Python（标准库 + `numpy` 可选）、`pytest`、已有脚本 `scripts/adapt_thuman4_release_to_freetime.py`、`scripts/export_triangulation_from_colmap_sparse.py`、`scripts/eval_masked_metrics.py`、COLMAP CLI（仅写 runbook，不执行）。

---

### Task 0: 写清本计划“不会做什么”（合规/边界）

**Files:**
- Create: `notes/openproposal_waiting_thuman4_cpu_prep_scope.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: 新建 scope note（避免后续误操作）**

Create `notes/openproposal_waiting_thuman4_cpu_prep_scope.md`（最小内容即可）：
- 明确：本计划不执行任何训练/colmap
- 明确：不提交 `data/` 与 `outputs/`
- 明确：report-pack 不允许包含 GT 帧/GT mask

**Step 2: Commit**

```bash
git add notes/openproposal_waiting_thuman4_cpu_prep_scope.md
git commit -m "docs(notes): define waiting-THUman CPU-only prep scope"
```

---

### Task 1: THUman raw inventory 工具（自动列出可用相机/帧并吐 adapter 命令）

**Files:**
- Create: `scripts/thuman4_inventory.py`
- Test: `scripts/tests/test_thuman4_inventory_contract.py`

**Step 1: 写失败的 contract test**

Create `scripts/tests/test_thuman4_inventory_contract.py`：
```python
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
        # Minimal THUman-like layout: images/<cam>/<frame>.jpg, masks/<cam>/<frame>.png
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
```

**Step 2: 运行 test，确认失败**

Run: `pytest -q scripts/tests/test_thuman4_inventory_contract.py -q`

Expected: FAIL（脚本不存在）。

**Step 3: 实现最小脚本（只做文件名扫描，不读图片内容）**

Create `scripts/thuman4_inventory.py`：
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _fail(msg: str) -> None:
    raise SystemExit(f"[THUman4Inventory][ERROR] {msg}")


def _list_cams(root: Path) -> list[str]:
    images = root / "images"
    masks = root / "masks"
    if not images.is_dir():
        _fail(f"missing images/: {images}")
    if not masks.is_dir():
        _fail(f"missing masks/: {masks}")
    img_cams = sorted(p.name for p in images.iterdir() if p.is_dir())
    msk_cams = sorted(p.name for p in masks.iterdir() if p.is_dir())
    cams = sorted(set(img_cams).intersection(msk_cams))
    if not cams:
        _fail("no common camera dirs between images/ and masks/")
    return cams


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Scan THUman4.0 subject directory and emit an adapter command.")
    ap.add_argument("--input_dir", required=True, help="THUman subject dir containing images/ and masks/")
    ap.add_argument("--num_cams", type=int, default=8)
    ap.add_argument("--num_frames", type=int, default=60)
    ap.add_argument("--frame_start", type=int, default=0)
    ap.add_argument("--image_downscale", type=int, default=2)
    ap.add_argument(
        "--output_camera_ids",
        default="02,03,04,05,06,07,08,09",
        help="Default FreeTime camera ids for 8-cam subset",
    )
    ap.add_argument(
        "--output_dir",
        default="data/thuman4_subject00_8cam60f",
        help="Default output dir under repo data/ (local-eval only)",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    cams = _list_cams(input_dir)

    n = int(args.num_cams)
    if n <= 0:
        _fail("--num_cams must be > 0")
    if len(cams) < n:
        _fail(f"not enough cameras: detected={len(cams)} need={n}")
    picked = cams[:n]

    out = {
        "input_dir": str(input_dir),
        "detected_cameras": cams,
        "picked_cameras": picked,
        "frame_start": int(args.frame_start),
        "num_frames": int(args.num_frames),
        "image_downscale": int(args.image_downscale),
        "output_dir": str(args.output_dir),
        "output_camera_ids": str(args.output_camera_ids),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("")
    print("# Suggested adapter command (local-eval only):")
    print("python3 scripts/adapt_thuman4_release_to_freetime.py \\")
    print(f"  --input_dir '{input_dir}' \\")
    print(f"  --output_dir '{args.output_dir}' \\")
    print(f"  --camera_ids '{','.join(picked)}' \\")
    print(f"  --output_camera_ids '{args.output_camera_ids}' \\")
    print(f"  --frame_start {int(args.frame_start)} \\")
    print(f"  --num_frames {int(args.num_frames)} \\")
    print(f"  --image_downscale {int(args.image_downscale)} \\")
    print("  --overwrite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: 运行 test，确认通过**

Run: `pytest -q scripts/tests/test_thuman4_inventory_contract.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/thuman4_inventory.py scripts/tests/test_thuman4_inventory_contract.py
git commit -m "feat(data): add THUman4 raw inventory helper"
```

---

### Task 2: Phase 1 一键 runbook（只写文档，等数据到位再执行）

**Files:**
- Create: `notes/openproposal_phase1_thuman4_runbook.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: 写 runbook（命令顺序写死，路径用变量占位）**

Create `notes/openproposal_phase1_thuman4_runbook.md`，至少包含以下段落与命令（不执行）：
1) `scripts/thuman4_inventory.py` 选定 camera_ids/frame_start/num_frames
2) `scripts/adapt_thuman4_release_to_freetime.py` 生成 `data/thuman4_subject00_8cam60f/images/` + `masks/`
3) COLMAP：建立 `_colmap_ref_images`（每相机 1 帧）并跑 `colmap feature_extractor / matcher / mapper` 得到 `sparse/0`
4) `python3 scripts/export_triangulation_from_colmap_sparse.py` 生成 `triangulation/`
5) smoke200（训练命令占位，明确用 `outputs/protocol_v3_openproposal/...`）
6) `scripts/eval_masked_metrics.py --mask_source dataset` 跑 `psnr_fg/lpips_fg`
7) local-eval only 提醒：禁止把 GT 帧/GT mask 写进 report-pack

**Step 2: Commit**

```bash
git add notes/openproposal_phase1_thuman4_runbook.md
git commit -m "docs(notes): add Phase1 THUman4 runbook (commands only)"
```

---

### Task 3: 固化 waiting‑THUman smoke 的可审计摘要（避免切到 THUman 后丢上下文）

**Files:**
- Create: `notes/openproposal_waiting_thuman4_smoke_summary.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: 写 summary（只写路径/sha/指标，不复制任何数据帧/GT）**

Create `notes/openproposal_waiting_thuman4_smoke_summary.md`：
- 列出完成的目录树（cue mining / runs / export / qualitative_local）
- 引用 `notes/openproposal_waiting_thuman4_smoke_mask_lock.md`（弱监督 run 用的 mask 锁定）
- 摘录关键 stats 路径与数值（PSNR/LPIPS、masked psnr_fg/lpips_fg）

**Step 2: Commit**

```bash
git add notes/openproposal_waiting_thuman4_smoke_summary.md
git commit -m "docs(notes): summarize waiting-THUman pipeline smoke status"
```

---

### Task 4: 全量单测（确保“写完就不会破坏主线”）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: `scripts/tests/*`

**Step 1: 跑单测**

Run: `pytest -q`

Expected: PASS

