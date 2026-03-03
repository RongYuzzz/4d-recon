# protocol_v2 Spatial Metrics (GT vs Pred) Diagnostics Implementation Plan (Owner A / GPU0)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不新增 full600 的前提下，为 `planb_init_600 -> planb_feat_v2_full600` 补一份**逐帧（per-frame）空间质量**诊断（GT vs Pred 的 `PSNR/MSE/MAE`，可选再补 `LPIPS`），把产物落到 `outputs/report_pack/diagnostics/`，用于“阻塞修复后”的 stage‑2 failure analysis 与离线证据包审计。

**Architecture:** 读取两条 run 的 `renders/test_step599_*.png`（GT|Pred 横向拼接），分别裁出左半 GT 与右半 Pred；逐帧计算 `MAE/MSE/PSNR`（可选用 GPU0 计算 `LPIPS(alex, normalize=True)`）；导出每条 run 的 per-frame CSV、delta CSV（planbfeat - planb）、一张曲线图与 top-k markdown 表（定位最差帧段）。

**Tech Stack:** `python3`、`Pillow`、`numpy`、`matplotlib`（画曲线）、（可选）`torch` + `torchmetrics`（LPIPS），`pytest`。

---

## Constraints / Invariants（必须遵守）

- 不新增 full600；不改动 `protocol_v1/v26` stage‑1 证据链（仅离线诊断衍生物）。
- 产物必须落在 `outputs/report_pack/diagnostics/`（小文件、可打包、可审计）。
- 尽量避免与 Owner B 冲突：本计划**不改** `docs/report_pack/2026-02-27-v2/README.md`、`docs/reviews/...`、`docs/report_pack/.../manifest_sha256.csv`（这些由 B 统一落地与重打包）。
- 若启用 LPIPS，必须显式 `CUDA_VISIBLE_DEVICES=0`（GPU0）。

---

### Task 0: Preflight（5-10 分钟）

**Files:**
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/`
- Read: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/`

**Step 1: 确认输入 renders 存在**

Run:
```bash
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/test_step599_0000.png
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/test_step599_0000.png
```
Expected: 两个文件都存在。

**Step 2: 确认 Python 依赖可用（CPU 指标）**

Run:
```bash
python3 - <<'PY'
import numpy as np
from PIL import Image
import matplotlib
print("ok", np.__version__, Image.__version__, matplotlib.__version__)
PY
```
Expected: 打印 `ok ...`。

**Step 3（可选）：确认 GPU0 与 LPIPS 依赖可用**

Run:
```bash
CUDA_VISIBLE_DEVICES=0 python3 - <<'PY'
import torch
print("cuda:", torch.cuda.is_available(), "count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("gpu0:", torch.cuda.get_device_name(0))
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity
_ = LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True)
print("torchmetrics LPIPS ok")
PY
```
Expected: `torchmetrics LPIPS ok`（若 torch/torchmetrics 不可用，则本计划后续仅跑 PSNR/MSE/MAE 也可交付）。

---

### Task 1: Worktree（可选但推荐）（5 分钟）

**Step 1: 建独立 worktree（避免污染主目录）**

Run:
```bash
git worktree add .worktrees/owner-a-protocol-v2-spatial-metrics-diagnostics \
  -b owner-a/protocol-v2-spatial-metrics-diagnostics
cd .worktrees/owner-a-protocol-v2-spatial-metrics-diagnostics
```

**Step 2: 确认 worktree 干净**

Run:
```bash
git status --porcelain
```
Expected: 空输出。

---

### Task 2: 写失败单测（contract）（10-15 分钟）

**Files:**
- Create: `scripts/tests/test_analyze_spatial_metrics_from_renders_contract.py`

**Step 1: 写测试（先红）**

`scripts/tests/test_analyze_spatial_metrics_from_renders_contract.py`（完整内容）：
```python
#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "analyze_spatial_metrics_from_renders.py"


def _write_concat_frame(path: Path, gt_value: int, pred_value: int, w: int = 8, h: int = 6) -> None:
    # Left half = GT, right half = Pred, concatenated horizontally.
    gt = np.full((h, w, 3), gt_value, dtype=np.uint8)
    pred = np.full((h, w, 3), pred_value, dtype=np.uint8)
    img = np.concatenate([gt, pred], axis=1)
    Image.fromarray(img).save(path)


def test_analyze_spatial_metrics_from_renders_contract(tmp_path: Path) -> None:
    renders = tmp_path / "renders"
    renders.mkdir(parents=True, exist_ok=True)

    # 2 frames with different GT-vs-Pred errors.
    _write_concat_frame(renders / "test_step599_0000.png", gt_value=0, pred_value=255)
    _write_concat_frame(renders / "test_step599_0001.png", gt_value=0, pred_value=127)

    out_csv = tmp_path / "out.csv"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--renders_dir",
            str(renders),
            "--pattern_prefix",
            "test_step599_",
            "--out_csv",
            str(out_csv),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"script failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert out_csv.exists()

    rows = list(csv.DictReader(out_csv.open(newline="", encoding="utf-8")))
    assert [r["frame_idx"] for r in rows] == ["0", "1"]
    assert set(rows[0].keys()) == {"frame_idx", "mae", "mse", "psnr"}

    # frame 0: GT=0, Pred=255 => diff=1.0 => MAE=1.0, MSE=1.0, PSNR=0.0
    mae0 = float(rows[0]["mae"])
    mse0 = float(rows[0]["mse"])
    psnr0 = float(rows[0]["psnr"])
    assert abs(mae0 - 1.0) < 1e-7
    assert abs(mse0 - 1.0) < 1e-7
    assert abs(psnr0 - 0.0) < 1e-7

    # frame 1: GT=0, Pred=127 => diff=127/255
    d1 = 127.0 / 255.0
    mae1 = float(rows[1]["mae"])
    mse1 = float(rows[1]["mse"])
    psnr1 = float(rows[1]["psnr"])
    assert abs(mae1 - d1) < 1e-6
    assert abs(mse1 - (d1 * d1)) < 1e-6
    exp_psnr1 = 10.0 * math.log10(1.0 / (d1 * d1))
    assert abs(psnr1 - exp_psnr1) < 1e-5
```

**Step 2: 跑测试确认失败（脚本未实现）**

Run:
```bash
pytest -q scripts/tests/test_analyze_spatial_metrics_from_renders_contract.py
```
Expected: FAIL（`scripts/analyze_spatial_metrics_from_renders.py` 不存在或 returncode != 0）。

---

### Task 3: 实现脚本让测试变绿（20-30 分钟）

**Files:**
- Create: `scripts/analyze_spatial_metrics_from_renders.py`

**Step 1: 实现脚本（满足 contract，先做 MAE/MSE/PSNR；LPIPS 走可选 flag 且 lazy import）**

`scripts/analyze_spatial_metrics_from_renders.py`（完整内容）：
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


FRAME_SUFFIX = re.compile(r"_(\\d+)\\.png$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compute per-frame spatial metrics (GT vs Pred) from concat renders (GT|Pred).")
    p.add_argument("--renders_dir", type=Path, required=True, help="Directory containing renders like test_step599_0041.png")
    p.add_argument("--pattern_prefix", type=str, default="test_step599_", help="Filename prefix to match frames.")
    p.add_argument("--out_csv", type=Path, required=True, help="Output CSV path.")
    # Optional: LPIPS(alex) via torchmetrics (GPU-friendly). Kept off by default to keep CPU-only contract tests cheap.
    p.add_argument("--with_lpips", action="store_true", help="Also compute LPIPS(alex, normalize=True) per-frame.")
    p.add_argument("--device", type=str, default="cuda", help="torch device for LPIPS (e.g. cuda/cpu).")
    return p.parse_args()


def _frame_idx_from_name(name: str) -> int:
    m = FRAME_SUFFIX.search(name)
    if not m:
        raise ValueError(f"cannot parse frame idx from filename: {name}")
    return int(m.group(1))


def _load_gt_pred_concat(path: Path) -> tuple[np.ndarray, np.ndarray]:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    h, w, _ = arr.shape
    if w % 2 != 0:
        raise ValueError(f"expected even width for GT|Pred concat, got w={w} for {path}")
    half = w // 2
    gt = arr[:, :half, :]
    pred = arr[:, half:, :]
    return gt, pred


def _compute_mae_mse_psnr(gt: np.ndarray, pred: np.ndarray) -> tuple[float, float, float]:
    diff = pred - gt
    mae = float(np.mean(np.abs(diff)))
    mse = float(np.mean(diff * diff))
    if mse == 0.0:
        psnr = float("inf")
    else:
        psnr = 10.0 * math.log10(1.0 / mse)
    return mae, mse, psnr


def _lpips_metric(device: str):
    # Lazy import to avoid making CPU-only tests depend on torch/torchmetrics.
    import torch
    from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity

    metric = LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True)
    metric = metric.to(device)
    metric.eval()
    return torch, metric


def main() -> int:
    args = parse_args()
    renders_dir: Path = args.renders_dir
    out_csv: Path = args.out_csv
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    paths = [p for p in renders_dir.glob(f"{args.pattern_prefix}*.png") if p.is_file()]
    if not paths:
        raise SystemExit(f"[ERROR] no frames matched in {renders_dir} with prefix {args.pattern_prefix!r}")
    paths = sorted(paths, key=lambda p: _frame_idx_from_name(p.name))

    want_lpips = bool(args.with_lpips)
    torch = None
    lpips = None
    if want_lpips:
        torch, lpips = _lpips_metric(args.device)

    fieldnames = ["frame_idx", "mae", "mse", "psnr"] + (["lpips"] if want_lpips else [])
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for p in paths:
            frame_idx = _frame_idx_from_name(p.name)
            gt, pred = _load_gt_pred_concat(p)
            mae, mse, psnr = _compute_mae_mse_psnr(gt, pred)

            row: dict[str, Any] = {
                "frame_idx": str(frame_idx),
                "mae": f"{mae:.8f}",
                "mse": f"{mse:.8f}",
                "psnr": f"{psnr:.8f}" if math.isfinite(psnr) else "inf",
            }

            if want_lpips:
                assert torch is not None and lpips is not None
                with torch.no_grad():
                    # HWC float32 -> NCHW float32
                    gt_t = torch.from_numpy(gt).permute(2, 0, 1).unsqueeze(0).to(args.device)
                    pred_t = torch.from_numpy(pred).permute(2, 0, 1).unsqueeze(0).to(args.device)
                    row["lpips"] = f"{float(lpips(pred_t, gt_t).item()):.8f}"

            w.writerow(row)

    print(f"wrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 2: 跑单测变绿**

Run:
```bash
pytest -q scripts/tests/test_analyze_spatial_metrics_from_renders_contract.py
```
Expected: PASS。

**Step 3: Commit（只提交脚本+测试）**

Run:
```bash
git add scripts/analyze_spatial_metrics_from_renders.py \
  scripts/tests/test_analyze_spatial_metrics_from_renders_contract.py
git commit -m "feat(diagnostics): add per-frame spatial metrics from concat renders"
```

---

### Task 4: 跑真实数据并落盘到 report-pack diagnostics（20-40 分钟）

**Files:**
- Create: `outputs/report_pack/diagnostics/spatial_metrics_planb_init_600_test_step599.csv`
- Create: `outputs/report_pack/diagnostics/spatial_metrics_planb_feat_v2_full600_test_step599.csv`
- Create: `outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv`
- Create: `outputs/report_pack/diagnostics/spatial_metrics_curve_planb_vs_planbfeat_test_step599.png`
- Create: `outputs/report_pack/diagnostics/spatial_metrics_topk_planbfeat_minus_planb_test_step599.md`

**Step 1: 生成 planb_init_600 的 per-frame 指标**

Run:
```bash
python3 scripts/analyze_spatial_metrics_from_renders.py \
  --renders_dir outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders \
  --pattern_prefix test_step599_ \
  --out_csv outputs/report_pack/diagnostics/spatial_metrics_planb_init_600_test_step599.csv
```

**Step 2: 生成 planb_feat_v2_full600 的 per-frame 指标**

Run:
```bash
python3 scripts/analyze_spatial_metrics_from_renders.py \
  --renders_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders \
  --pattern_prefix test_step599_ \
  --out_csv outputs/report_pack/diagnostics/spatial_metrics_planb_feat_v2_full600_test_step599.csv
```

**Step 3（可选，GPU0）：补 LPIPS 列（会覆盖同名 CSV，或另存 *_with_lpips.csv 也可）**

Option A（覆盖同名 CSV，推荐一次到位）:
```bash
CUDA_VISIBLE_DEVICES=0 python3 scripts/analyze_spatial_metrics_from_renders.py \
  --with_lpips --device cuda \
  --renders_dir outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders \
  --pattern_prefix test_step599_ \
  --out_csv outputs/report_pack/diagnostics/spatial_metrics_planb_init_600_test_step599.csv

CUDA_VISIBLE_DEVICES=0 python3 scripts/analyze_spatial_metrics_from_renders.py \
  --with_lpips --device cuda \
  --renders_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders \
  --pattern_prefix test_step599_ \
  --out_csv outputs/report_pack/diagnostics/spatial_metrics_planb_feat_v2_full600_test_step599.csv
```

**Step 4: 生成 delta CSV（planbfeat - planb；自动适配是否含 lpips 列）**

Run:
```bash
python3 - <<'PY'
import csv
from pathlib import Path

a = Path("outputs/report_pack/diagnostics/spatial_metrics_planb_init_600_test_step599.csv")
b = Path("outputs/report_pack/diagnostics/spatial_metrics_planb_feat_v2_full600_test_step599.csv")
out = Path("outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv")

ra = list(csv.DictReader(a.open(newline="", encoding="utf-8")))
rb = list(csv.DictReader(b.open(newline="", encoding="utf-8")))
assert len(ra) == len(rb) and len(ra) > 0

have_lpips = "lpips" in ra[0] and "lpips" in rb[0]
fieldnames = ["frame_idx","mae_a","mae_b","delta_mae","psnr_a","psnr_b","delta_psnr"]
if have_lpips:
    fieldnames += ["lpips_a","lpips_b","delta_lpips"]

out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for xa, xb in zip(ra, rb, strict=True):
        assert xa["frame_idx"] == xb["frame_idx"]
        mae_a = float(xa["mae"]); mae_b = float(xb["mae"])
        psnr_a = float(xa["psnr"]) if xa["psnr"] != "inf" else float("inf")
        psnr_b = float(xb["psnr"]) if xb["psnr"] != "inf" else float("inf")
        row = {
            "frame_idx": xa["frame_idx"],
            "mae_a": f"{mae_a:.8f}",
            "mae_b": f"{mae_b:.8f}",
            "delta_mae": f"{(mae_b - mae_a):.8f}",
            "psnr_a": f"{psnr_a:.8f}" if psnr_a != float("inf") else "inf",
            "psnr_b": f"{psnr_b:.8f}" if psnr_b != float("inf") else "inf",
            "delta_psnr": f"{(psnr_b - psnr_a):.8f}" if (psnr_a != float("inf") and psnr_b != float("inf")) else "",
        }
        if have_lpips:
            lp_a = float(xa["lpips"]); lp_b = float(xb["lpips"])
            row.update({
                "lpips_a": f"{lp_a:.8f}",
                "lpips_b": f"{lp_b:.8f}",
                "delta_lpips": f"{(lp_b - lp_a):.8f}",
            })
        w.writerow(row)
print("wrote", out, "have_lpips=", have_lpips)
PY
```

**Step 5: 画曲线图（PSNR/MAE；若含 LPIPS 列则额外画一条）**

Run:
```bash
python3 - <<'PY'
import csv
from pathlib import Path

import matplotlib.pyplot as plt

a = Path("outputs/report_pack/diagnostics/spatial_metrics_planb_init_600_test_step599.csv")
b = Path("outputs/report_pack/diagnostics/spatial_metrics_planb_feat_v2_full600_test_step599.csv")
out = Path("outputs/report_pack/diagnostics/spatial_metrics_curve_planb_vs_planbfeat_test_step599.png")

ra = list(csv.DictReader(a.open(newline="", encoding="utf-8")))
rb = list(csv.DictReader(b.open(newline="", encoding="utf-8")))
xs = [int(r["frame_idx"]) for r in ra]
mae_a = [float(r["mae"]) for r in ra]
mae_b = [float(r["mae"]) for r in rb]
psnr_a = [float(r["psnr"]) if r["psnr"] != "inf" else float("nan") for r in ra]
psnr_b = [float(r["psnr"]) if r["psnr"] != "inf" else float("nan") for r in rb]
have_lpips = "lpips" in ra[0] and "lpips" in rb[0]
lp_a = [float(r["lpips"]) for r in ra] if have_lpips else None
lp_b = [float(r["lpips"]) for r in rb] if have_lpips else None

rows = 3 if have_lpips else 2
fig, axes = plt.subplots(rows, 1, figsize=(10, 3.0 * rows), sharex=True)
if rows == 1:
    axes = [axes]

axes[0].plot(xs, psnr_a, label="planb_init_600 PSNR", lw=1.5)
axes[0].plot(xs, psnr_b, label="planb_feat_v2_full600 PSNR", lw=1.5)
axes[0].set_ylabel("PSNR (dB)")
axes[0].grid(True, alpha=0.25)
axes[0].legend()

axes[1].plot(xs, mae_a, label="planb_init_600 MAE", lw=1.5)
axes[1].plot(xs, mae_b, label="planb_feat_v2_full600 MAE", lw=1.5)
axes[1].set_ylabel("MAE")
axes[1].grid(True, alpha=0.25)
axes[1].legend()

if have_lpips:
    axes[2].plot(xs, lp_a, label="planb_init_600 LPIPS(GT)", lw=1.5)
    axes[2].plot(xs, lp_b, label="planb_feat_v2_full600 LPIPS(GT)", lw=1.5)
    axes[2].set_ylabel("LPIPS")
    axes[2].grid(True, alpha=0.25)
    axes[2].legend()

axes[-1].set_xlabel("frame_idx")
fig.tight_layout()
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=160)
print("wrote", out, "have_lpips=", have_lpips)
PY
```

**Step 6: 生成 top-k 表（默认按 delta_mae 降序，列出最差 10 帧）**

Run:
```bash
python3 - <<'PY'
import csv
from pathlib import Path

delta = Path("outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv")
out = Path("outputs/report_pack/diagnostics/spatial_metrics_topk_planbfeat_minus_planb_test_step599.md")

rows = list(csv.DictReader(delta.open(newline="", encoding="utf-8")))
rows_sorted = sorted(rows, key=lambda r: float(r["delta_mae"]), reverse=True)[:10]

have_lpips = "delta_lpips" in rows[0]
lines = []
lines.append("# spatial metrics top-k (planbfeat - planb) @ test_step599")
lines.append("")
cols = ["rank","frame_idx","delta_mae","delta_psnr"]
if have_lpips:
    cols.append("delta_lpips")
lines.append("| " + " | ".join(cols) + " |")
lines.append("|" + "|".join(["---"] * len(cols)) + "|")
for i, r in enumerate(rows_sorted, 1):
    row = [str(i), r["frame_idx"], r["delta_mae"], r.get("delta_psnr","")]
    if have_lpips:
        row.append(r.get("delta_lpips",""))
    lines.append("| " + " | ".join(row) + " |")

out.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
print("wrote", out)
PY
```

**Acceptance:**
- 5 个产物都存在且可打开（2 个 per-run CSV + delta CSV + 曲线 PNG + top-k MD）
- top-k 是否命中/邻近既有锚点 `41->42`（不要求完全一致，但应能解释“哪里变差/变好”）

---

### Task 5: 写独立 note（避免与 B 冲突）（10-20 分钟）

**Files:**
- Create: `notes/protocol_v2_spatial_metrics_diagnostics.md`

内容最小要点（不要长文）：
- 输入 renders 两条路径（planb / planbfeat）
- 方法：GT|Pred split + per-frame 指标 + delta + top-k
- 关键发现：top-k 帧号（尤其是否包含 41/42 邻域）
- 指针：本次 5 个产物的 repo 绝对路径（B 后续会把它们串进 report-pack README）

Commit:
```bash
git add notes/protocol_v2_spatial_metrics_diagnostics.md
git commit -m "docs(protocol_v2): add spatial metrics per-frame diagnostics note"
```

---

### Task 6: 交付给 Owner B（5 分钟）

把以下信息写到 handoff/汇报里（最少 3 行即可）：
- `outputs/report_pack/diagnostics/spatial_metrics_*` 产物列表
- `notes/protocol_v2_spatial_metrics_diagnostics.md`
- 一句话结论：top-k 最差帧段是否与 `41->42` 锚点对齐

