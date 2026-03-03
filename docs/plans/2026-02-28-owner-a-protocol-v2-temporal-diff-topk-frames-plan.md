# protocol_v2 Temporal Diff Top-K Frame Snapshots Implementation Plan (Owner A / GPU0)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `planb_init_600 -> planb_feat_v2_full600` 的 temporal-diff top‑k 帧对补一组**可审计的帧级快照（Pred half）**与索引文档，落入 `outputs/report_pack/diagnostics/`，供 Owner B 在后续统一刷新离线证据包/README 时直接引用。

**Architecture:** 读取两条 run 的 `renders/test_step599_*.png`（GT|Pred 横向拼接），裁剪右半 Pred；基于 A 已产出的 `temporal_diff_delta_*.csv` 选取 delta 最大的 top‑k 帧对；对每个帧对导出一张小体积 composite 图（2 行 x 3 列：A prev/cur/diff + B prev/cur/diff），并生成 `README.md` 索引表格。脚本与测试走 TDD，小图单测确保 contract。

**Tech Stack:** `python3`、`Pillow`、`numpy`、`pytest`。

---

## Constraints / Invariants（必须遵守）

- 不新增 full600；不改动 `protocol_v1/v26` 已有证据链（只做离线诊断与可视化衍生物）。
- 产物必须落在 `outputs/report_pack/diagnostics/`（小文件，可被 `scripts/pack_evidence.py` 自动纳入离线包）。
- 尽量避免与 Owner B 冲突：不改 `docs/report_pack/2026-02-27-v2/README.md` / `docs/reviews/...`（B 负责入口与打包）。
- GPU0 本任务不强依赖（CPU 即可）；如需跑 GPU 相关（可选扩展），必须显式 `CUDA_VISIBLE_DEVICES=0`。

---

### Task 0: Worktree + Preflight（10 分钟）

**Files:**
- Read: `outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv`
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/`
- Read: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/`

**Step 1:（可选但推荐）创建独立 worktree**

Run:
```bash
git worktree add .worktrees/owner-a-protocol-v2-temporal-diff-topk-frames \
  -b owner-a/protocol-v2-temporal-diff-topk-frames
cd .worktrees/owner-a-protocol-v2-temporal-diff-topk-frames
```

**Step 2: 确认关键输入存在**

Run:
```bash
ls -la outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/test_step599_0041.png
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/test_step599_0042.png
```
Expected: 3 个文件都存在。

---

### Task 1: 写失败单测（viz top‑k 帧快照 contract）（10-15 分钟）

**Files:**
- Create: `scripts/tests/test_viz_temporal_diff_topk_frames_contract.py`

**Step 1: 写测试（先红）**

`scripts/tests/test_viz_temporal_diff_topk_frames_contract.py`（完整内容）：
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
SCRIPT = REPO_ROOT / "scripts" / "viz_temporal_diff_topk_frames.py"


def _write_concat_frame(path: Path, pred_value: int, w: int = 8, h: int = 6) -> None:
    # Left half (GT) and right half (Pred) are concatenated horizontally.
    gt = np.full((h, w, 3), 20, dtype=np.uint8)
    pred = np.full((h, w, 3), pred_value, dtype=np.uint8)
    img = np.concatenate([gt, pred], axis=1)
    Image.fromarray(img).save(path)


def test_viz_temporal_diff_topk_frames_contract(tmp_path: Path) -> None:
    renders_a = tmp_path / "a"
    renders_b = tmp_path / "b"
    renders_a.mkdir(parents=True, exist_ok=True)
    renders_b.mkdir(parents=True, exist_ok=True)

    # 3 frames for each run.
    for i, v in enumerate([10, 30, 50]):
        _write_concat_frame(renders_a / f"test_step599_{i:04d}.png", pred_value=v)
    for i, v in enumerate([10, 60, 90]):
        _write_concat_frame(renders_b / f"test_step599_{i:04d}.png", pred_value=v)

    # delta CSV: top-1 should pick pair (1,2).
    delta_csv = tmp_path / "delta.csv"
    with delta_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "pair_idx",
                "frame_prev",
                "frame_cur",
                "mean_abs_diff_a",
                "mean_abs_diff_b",
                "delta_mean_abs_diff",
            ],
        )
        w.writeheader()
        w.writerow(
            {
                "pair_idx": "0",
                "frame_prev": "0",
                "frame_cur": "1",
                "mean_abs_diff_a": "0.00000000",
                "mean_abs_diff_b": "0.00000000",
                "delta_mean_abs_diff": "0.00010000",
            }
        )
        w.writerow(
            {
                "pair_idx": "1",
                "frame_prev": "1",
                "frame_cur": "2",
                "mean_abs_diff_a": "0.00000000",
                "mean_abs_diff_b": "0.00000000",
                "delta_mean_abs_diff": "0.00020000",
            }
        )

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

    imgs = list(out_dir.glob("pair_*.jpg"))
    assert len(imgs) == 1, f"expected 1 output image, got {len(imgs)}"
    assert "0001_0002" in imgs[0].name
```

**Step 2: 跑测试确认失败（脚本未实现）**

Run:
```bash
pytest -q scripts/tests/test_viz_temporal_diff_topk_frames_contract.py
```
Expected: FAIL（`scripts/viz_temporal_diff_topk_frames.py` 不存在或 returncode != 0）。

---

### Task 2: 实现最小脚本让测试变绿（20-30 分钟）

**Files:**
- Create: `scripts/viz_temporal_diff_topk_frames.py`

**Step 1: 实现脚本（满足单测 contract）**

`scripts/viz_temporal_diff_topk_frames.py`（完整内容）：
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export composite frame snapshots for temporal-diff top-k pairs.")
    p.add_argument("--renders_dir_a", type=Path, required=True, help="Renders dir for planb_init_600 (GT|Pred concat).")
    p.add_argument("--renders_dir_b", type=Path, required=True, help="Renders dir for planb_feat_v2_full600 (GT|Pred concat).")
    p.add_argument("--delta_csv", type=Path, required=True, help="temporal_diff_delta_*.csv (planbfeat - planb).")
    p.add_argument("--out_dir", type=Path, required=True, help="Output directory under outputs/report_pack/diagnostics/.")
    p.add_argument("--pattern_prefix", type=str, default="test_step599_", help="Filename prefix (default: test_step599_).")
    p.add_argument("--k", type=int, default=10, help="Top-k pairs to export (default: 10).")
    p.add_argument("--resize_w", type=int, default=640, help="Resize Pred-half tiles to this width (default: 640).")
    p.add_argument("--quality", type=int, default=85, help="JPEG quality (default: 85).")
    return p.parse_args()


def _pred_half(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w % 2 != 0:
        raise ValueError(f"expected even width for gt|pred concat: {path} ({w})")
    mid = w // 2
    return img.crop((mid, 0, w, h))


def _resize_to_w(img: Image.Image, w: int) -> Image.Image:
    if w <= 0:
        raise ValueError("resize_w must be > 0")
    ow, oh = img.size
    if ow == w:
        return img
    nh = max(1, int(round(oh * (w / float(ow)))))
    return img.resize((w, nh), resample=Image.BILINEAR)


def _absdiff_vis(a: Image.Image, b: Image.Image) -> Image.Image:
    # Visualize absdiff(a, b) as grayscale (auto-scaled by p99) for audit.
    aa = np.asarray(a, dtype=np.float32)
    bb = np.asarray(b, dtype=np.float32)
    if aa.shape != bb.shape:
        raise ValueError(f"shape mismatch: {aa.shape} vs {bb.shape}")
    d = np.abs(aa - bb).mean(axis=2)  # [H,W], 0..255
    p99 = float(np.percentile(d, 99.0))
    scale = 255.0 / max(p99, 1e-6)
    dv = np.clip(d * scale, 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(dv, mode="L").convert("RGB")


def _composite(a_prev: Image.Image, a_cur: Image.Image, b_prev: Image.Image, b_cur: Image.Image) -> Image.Image:
    # 2 rows (A,B) x 3 cols (prev,cur,diff)
    pad = 6
    a_diff = _absdiff_vis(a_prev, a_cur)
    b_diff = _absdiff_vis(b_prev, b_cur)

    tiles = [
        [a_prev, a_cur, a_diff],
        [b_prev, b_cur, b_diff],
    ]
    tile_w, tile_h = tiles[0][0].size
    canvas_w = pad + 3 * (tile_w + pad)
    canvas_h = pad + 2 * (tile_h + pad)
    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(16, 16, 16))

    for r in range(2):
        for c in range(3):
            x = pad + c * (tile_w + pad)
            y = pad + r * (tile_h + pad)
            canvas.paste(tiles[r][c], (x, y))
    return canvas


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(args.delta_csv.open(newline="", encoding="utf-8")))
    if not rows:
        raise SystemExit(f"empty delta_csv: {args.delta_csv}")

    # Sort by delta desc; take top-k.
    rows_sorted = sorted(rows, key=lambda r: float(r["delta_mean_abs_diff"]), reverse=True)
    rows_top = rows_sorted[: max(0, int(args.k))]

    readme_lines = [
        "# Temporal Diff Top-k Frame Snapshots (Pred half)",
        "",
        f"- delta_csv: `{args.delta_csv}`",
        "",
        "| rank | frame_prev | frame_cur | delta_mean_abs_diff | image |",
        "| ---: | ---: | ---: | ---: | --- |",
    ]

    for rank, r in enumerate(rows_top, 1):
        fp = int(r["frame_prev"])
        fc = int(r["frame_cur"])
        delta = float(r["delta_mean_abs_diff"])

        pa_prev = args.renders_dir_a / f"{args.pattern_prefix}{fp:04d}.png"
        pa_cur = args.renders_dir_a / f"{args.pattern_prefix}{fc:04d}.png"
        pb_prev = args.renders_dir_b / f"{args.pattern_prefix}{fp:04d}.png"
        pb_cur = args.renders_dir_b / f"{args.pattern_prefix}{fc:04d}.png"

        a_prev = _resize_to_w(_pred_half(pa_prev), args.resize_w)
        a_cur = _resize_to_w(_pred_half(pa_cur), args.resize_w)
        b_prev = _resize_to_w(_pred_half(pb_prev), args.resize_w)
        b_cur = _resize_to_w(_pred_half(pb_cur), args.resize_w)

        out_name = f"pair_{fp:04d}_{fc:04d}.jpg"
        out_path = args.out_dir / out_name
        comp = _composite(a_prev, a_cur, b_prev, b_cur)
        comp.save(out_path, quality=int(args.quality), optimize=True)

        readme_lines.append(f"| {rank} | {fp} | {fc} | {delta:.8f} | `{out_name}` |")

    (args.out_dir / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out_dir} ({len(rows_top)} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 2: 跑测试变绿**

Run:
```bash
pytest -q scripts/tests/test_viz_temporal_diff_topk_frames_contract.py
```
Expected: PASS。

**Step 3: Commit（脚本+测试）**

Run:
```bash
git add scripts/viz_temporal_diff_topk_frames.py scripts/tests/test_viz_temporal_diff_topk_frames_contract.py
git commit -m "feat(diagnostics): add temporal diff top-k frame snapshot exporter"
```

---

### Task 3: 生成真实 top‑k 帧快照产物（10-20 分钟）

**Files:**
- Create: `outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599/README.md`
- Create: `outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599/pair_*.jpg`

**Step 1: 跑脚本导出 top‑k（k=10）**

Run:
```bash
python3 scripts/viz_temporal_diff_topk_frames.py \
  --renders_dir_a outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders \
  --renders_dir_b outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders \
  --delta_csv outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv \
  --out_dir outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599 \
  --k 10 \
  --resize_w 640 \
  --quality 85
```

**Step 2: 验收（数量/关键帧对/体积）**

Run:
```bash
ls -la outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599/README.md
ls -la outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599/pair_0041_0042.jpg
ls outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599/pair_*.jpg | wc -l
du -sh outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599
```
Expected:
- `README.md` 存在
- `pair_0041_0042.jpg` 存在（与 top‑k 结论对齐）
- 图片数量为 10
- 目录体积应为 MB 级（避免把 renders 全量打进离线包）

---

### Task 4: 写独立 note（避免与 B 改同一段落）（10 分钟）

**Files:**
- Create: `notes/protocol_v2_temporal_diff_topk_frames.md`

**Step 1: 新增 note（最小可用）**

`notes/protocol_v2_temporal_diff_topk_frames.md`（内容建议）：
```markdown
# protocol_v2 temporal diff top-k frame snapshots (Pred half)

诊断目标：把 `planb_init_600 -> planb_feat_v2_full600_*` 的时序不稳定用“帧对锚点 + 帧级快照”固化，便于离线审计与答辩复现。

证据产物：
- `outputs/report_pack/diagnostics/temporal_diff_curve_planb_vs_planbfeat_test_step599.png`
- `outputs/report_pack/diagnostics/temporal_diff_topk_table_planbfeat_minus_planb_test_step599.md`
- `outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv`
- `outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599/README.md`

一句话结论：
- top‑k 最大增量帧对集中在 `37-45` 区间，rank1 为 `(41,42)`；对应的帧级快照见 `temporal_diff_topk_frames_.../pair_0041_0042.jpg`。
```

**Step 2: Commit（note + 可选把 stage2 note 纳入 git）**

Run（最小）:
```bash
git add notes/protocol_v2_temporal_diff_topk_frames.md
git commit -m "docs(protocol_v2): add temporal diff top-k frame snapshots note"
```

Run（可选，若 `notes/protocol_v2_stage2_tradeoff_qual.md` 仍为 untracked，建议一起纳入版本库避免丢失）:
```bash
git add notes/protocol_v2_stage2_tradeoff_qual.md
git commit -m "docs(protocol_v2): track stage2 trade-off qualitative note"
```

---

## Handoff（给 Owner B）

把下面 2 个路径 + 1 句结论发给 B，用于其 Task 4（README 指针 + 离线包重打）：
- `outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599/README.md`
- `notes/protocol_v2_temporal_diff_topk_frames.md`
- 结论一句话：top‑k delta 帧对集中在 `37-45`，rank1 为 `(41,42)`。

