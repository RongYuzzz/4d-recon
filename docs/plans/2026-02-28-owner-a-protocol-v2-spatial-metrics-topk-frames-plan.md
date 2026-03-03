# protocol_v2 Spatial Metrics Top-K Frame Snapshots Implementation Plan (Owner A / GPU0)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `planb_init_600 -> planb_feat_v2_full600` 的空间指标（GT vs Pred 的 `MAE/MSE/PSNR`）补一组**可审计的逐帧 top‑k 快照**（GT / Pred / |Pred‑GT|），落到 `outputs/report_pack/diagnostics/`，用于解释“为何 PSNR 全帧提升但 MAE 存在局部劣化”以及与 `41->42` 时序锚点的差异。

**Architecture:** 读取两条 run 的 `renders/test_step599_*.png`（GT|Pred 横向拼接），裁出 GT(left) 与 Pred(right)，并生成 per‑frame error map（|Pred‑GT|，灰度）。基于已生成的 `spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv` 选取 `delta_mae` 最大的 top‑k 帧，输出每帧一张 2x3 composite（planb / planbfeat × GT/Pred/err）+ `README.md` 索引。

**Tech Stack:** `python3`、`Pillow`、`numpy`、`pytest`。可选用 GPU0 仅做后续扩展（本计划主体 CPU 即可）。

---

## Constraints / Invariants（必须遵守）

- 不新增 full600；不改动 stage‑1/v26 证据链。
- 产物必须落在 `outputs/report_pack/diagnostics/`（小文件，可被 `scripts/pack_evidence.py` 自动纳入离线包）。
- 尽量避免与 Owner B 冲突：本计划**不改** `docs/report_pack/2026-02-27-v2/README.md` / `docs/reviews/...`（B 统一落地入口与打包）。
- 若跑任何 GPU 相关（可选扩展），必须显式 `CUDA_VISIBLE_DEVICES=0`。

---

### Task 0: Preflight（5-10 分钟）

**Files:**
- Read: `outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv`
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/`
- Read: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/`

**Step 1: 确认关键输入存在**

Run:
```bash
ls -la outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/test_step599_0059.png
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/test_step599_0059.png
```
Expected: 3 个文件都存在。

---

### Task 1: Worktree（可选但推荐）（5 分钟）

**Step 1: 创建独立 worktree**

Run:
```bash
git worktree add .worktrees/owner-a-protocol-v2-spatial-metrics-topk-frames \
  -b owner-a/protocol-v2-spatial-metrics-topk-frames
cd .worktrees/owner-a-protocol-v2-spatial-metrics-topk-frames
```

**Step 2: 确认干净**

Run:
```bash
git status --porcelain
```
Expected: 空输出。

---

### Task 2: 写失败单测（contract）（10-15 分钟）

**Files:**
- Create: `scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py`

**Step 1: 写测试（先红）**

`scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py`（完整内容）：
```python
#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "viz_spatial_metrics_topk_frames.py"


def _write_concat_frame(path: Path, gt_value: int, pred_value: int, w: int = 8, h: int = 6) -> None:
    # Left half (GT) and right half (Pred) are concatenated horizontally.
    gt = np.full((h, w, 3), gt_value, dtype=np.uint8)
    pred = np.full((h, w, 3), pred_value, dtype=np.uint8)
    img = np.concatenate([gt, pred], axis=1)
    Image.fromarray(img).save(path)


def test_viz_spatial_metrics_topk_frames_contract(tmp_path: Path) -> None:
    renders_a = tmp_path / "a"
    renders_b = tmp_path / "b"
    renders_a.mkdir(parents=True, exist_ok=True)
    renders_b.mkdir(parents=True, exist_ok=True)

    # 2 frames. frame 0 has smaller delta_mae, frame 1 is top-1.
    _write_concat_frame(renders_a / "test_step599_0000.png", gt_value=0, pred_value=10)
    _write_concat_frame(renders_a / "test_step599_0001.png", gt_value=0, pred_value=10)
    _write_concat_frame(renders_b / "test_step599_0000.png", gt_value=0, pred_value=11)
    _write_concat_frame(renders_b / "test_step599_0001.png", gt_value=0, pred_value=50)

    delta_csv = tmp_path / "delta.csv"
    with delta_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["frame_idx", "delta_mae", "delta_psnr"])
        w.writeheader()
        w.writerow({"frame_idx": "0", "delta_mae": "0.0001", "delta_psnr": "0.0"})
        w.writerow({"frame_idx": "1", "delta_mae": "0.0002", "delta_psnr": "0.0"})

    out_dir = tmp_path / "out"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--renders_dir_a",
            str(renders_a),
            "--renders_dir_b",
            str(renders_b),
            "--delta_csv",
            str(delta_csv),
            "--out_dir",
            str(out_dir),
            "--k",
            "1",
            "--resize_w",
            "16",
            "--quality",
            "80",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, f"script failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert (out_dir / "README.md").exists()
    imgs = list(out_dir.glob("frame_*.jpg"))
    assert len(imgs) == 1
    assert imgs[0].name == "frame_0001.jpg"
```

**Step 2: 跑测试确认失败（脚本未实现）**

Run:
```bash
pytest -q scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py
```
Expected: FAIL。

---

### Task 3: 实现脚本让测试变绿（20-30 分钟）

**Files:**
- Create: `scripts/viz_spatial_metrics_topk_frames.py`

**Step 1: 实现最小脚本（满足 contract）**

`scripts/viz_spatial_metrics_topk_frames.py`（完整内容）：
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Row:
    frame_idx: int
    delta_mae: float
    delta_psnr: float | None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export top-k frame snapshots for spatial metrics delta (planbfeat - planb).")
    p.add_argument("--renders_dir_a", type=Path, required=True, help="planb_init_600 renders dir (GT|Pred concat).")
    p.add_argument("--renders_dir_b", type=Path, required=True, help="planb_feat_v2_full600 renders dir (GT|Pred concat).")
    p.add_argument("--delta_csv", type=Path, required=True, help="spatial_metrics_delta_*.csv")
    p.add_argument("--out_dir", type=Path, required=True, help="Output directory under outputs/report_pack/diagnostics/.")
    p.add_argument("--pattern_prefix", type=str, default="test_step599_", help="render filename prefix (default: test_step599_)")
    p.add_argument("--k", type=int, default=10, help="top-k frames by delta_mae desc")
    p.add_argument("--resize_w", type=int, default=0, help="resize width (0 keeps original)")
    p.add_argument("--quality", type=int, default=85, help="jpeg quality")
    return p.parse_args()


def _load_gt_pred_concat(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with Image.open(path) as im:
        im = im.convert("RGB")
        arr = np.asarray(im, dtype=np.float32) / 255.0
    h, w, _ = arr.shape
    if w % 2 != 0:
        raise ValueError(f"expected even width for GT|Pred concat, got w={w} for {path}")
    half = w // 2
    gt = arr[:, :half, :]
    pred = arr[:, half:, :]
    return gt, pred


def _to_u8(img_f: np.ndarray) -> Image.Image:
    x = np.clip(img_f * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(x, mode="RGB")


def _err_u8(gt: np.ndarray, pred: np.ndarray) -> Image.Image:
    err = np.mean(np.abs(pred - gt), axis=2, keepdims=True)  # HWC, 1 channel
    err = np.repeat(err, 3, axis=2)
    return _to_u8(err)


def _resize_keep_aspect(im: Image.Image, resize_w: int) -> Image.Image:
    if resize_w <= 0:
        return im
    w, h = im.size
    if w == resize_w:
        return im
    new_h = max(1, int(round(h * (resize_w / float(w)))))
    return im.resize((resize_w, new_h), resample=Image.BILINEAR)


def _read_rows(delta_csv: Path) -> list[Row]:
    rows: list[Row] = []
    with delta_csv.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            frame_idx = int(row["frame_idx"])
            delta_mae = float(row["delta_mae"])
            delta_psnr = row.get("delta_psnr", "")
            rows.append(Row(frame_idx=frame_idx, delta_mae=delta_mae, delta_psnr=float(delta_psnr) if delta_psnr else None))
    if not rows:
        raise SystemExit(f"[ERROR] empty delta csv: {delta_csv}")
    return rows


def _render_path(renders_dir: Path, prefix: str, frame_idx: int) -> Path:
    return renders_dir / f"{prefix}{frame_idx:04d}.png"


def _write_readme(out_dir: Path, rows: list[Row], chosen: list[Row], delta_csv: Path) -> None:
    lines: list[str] = []
    lines.append("# spatial metrics top-k frame snapshots (planbfeat - planb) @ test_step599")
    lines.append("")
    lines.append(f"- delta csv: `{delta_csv}`")
    lines.append(f"- k: `{len(chosen)}` (sorted by `delta_mae` desc)")
    lines.append("")
    lines.append("| rank | frame_idx | delta_mae | delta_psnr | file |")
    lines.append("|---|---|---|---|---|")
    for i, row in enumerate(chosen, 1):
        fname = f"frame_{row.frame_idx:04d}.jpg"
        dpsnr = f\"{row.delta_psnr:.8f}\" if row.delta_psnr is not None else \"\"
        lines.append(f\"| {i} | {row.frame_idx} | {row.delta_mae:.8f} | {dpsnr} | {fname} |\")
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = _read_rows(args.delta_csv)
    rows_sorted = sorted(rows, key=lambda x: x.delta_mae, reverse=True)
    chosen = rows_sorted[: max(0, int(args.k))]

    args.out_dir.mkdir(parents=True, exist_ok=True)

    for row in chosen:
        pa = _render_path(args.renders_dir_a, args.pattern_prefix, row.frame_idx)
        pb = _render_path(args.renders_dir_b, args.pattern_prefix, row.frame_idx)
        if not pa.exists():
            raise SystemExit(f"[ERROR] missing frame in A: {pa}")
        if not pb.exists():
            raise SystemExit(f"[ERROR] missing frame in B: {pb}")

        gt_a, pred_a = _load_gt_pred_concat(pa)
        gt_b, pred_b = _load_gt_pred_concat(pb)

        tiles = [
            _to_u8(gt_a),
            _to_u8(pred_a),
            _err_u8(gt_a, pred_a),
            _to_u8(gt_b),
            _to_u8(pred_b),
            _err_u8(gt_b, pred_b),
        ]
        tiles = [_resize_keep_aspect(t, args.resize_w) for t in tiles]

        tw, th = tiles[0].size
        canvas = Image.new("RGB", (tw * 3, th * 2), color=(0, 0, 0))
        for idx, t in enumerate(tiles):
            x = (idx % 3) * tw
            y = (idx // 3) * th
            canvas.paste(t, (x, y))

        out_path = args.out_dir / f"frame_{row.frame_idx:04d}.jpg"
        canvas.save(out_path, quality=int(args.quality), optimize=True)

    _write_readme(args.out_dir, rows, chosen, args.delta_csv)
    print(f"wrote {len(chosen)} frames to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 2: 跑单测变绿**

Run:
```bash
pytest -q scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py
```
Expected: PASS。

**Step 3: Commit（只提交脚本+测试）**

Run:
```bash
git add scripts/viz_spatial_metrics_topk_frames.py \
  scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py
git commit -m "feat(diagnostics): add spatial metrics top-k frame snapshot exporter"
```

---

### Task 4: 跑真实数据并落盘（10-20 分钟）

**Files:**
- Create: `outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599/README.md`
- Create: `outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599/frame_*.jpg`

Run:
```bash
python3 scripts/viz_spatial_metrics_topk_frames.py \
  --renders_dir_a outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders \
  --renders_dir_b outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders \
  --delta_csv outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv \
  --out_dir outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599 \
  --k 10 \
  --resize_w 640 \
  --quality 80
```

**Acceptance:**
- `README.md` 存在
- `frame_*.jpg` 数量为 10
- 目录体积保持在 MB 级（不要上百 MB）

---

### Task 5: 写独立 note（避免与 B 冲突）（10-15 分钟）

**Files:**
- Create: `notes/protocol_v2_spatial_metrics_topk_frames.md`

最小内容：
- 说明该目录是 `delta_mae top-k` 的可审计快照
- 指向 `spatial_metrics_topk_frames_.../README.md`
- 一句话：top-k 是否集中在 `52-59`，与 temporal/tLPIPS 的 `41->42` 锚点如何互补

Commit:
```bash
git add notes/protocol_v2_spatial_metrics_topk_frames.md
git commit -m "docs(protocol_v2): add spatial metrics top-k frame snapshots note"
```

---

### Task 6: 交接给 Owner B（5 分钟）

把下面两条路径发给 B：
- `outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599/`
- `notes/protocol_v2_spatial_metrics_topk_frames.md`

