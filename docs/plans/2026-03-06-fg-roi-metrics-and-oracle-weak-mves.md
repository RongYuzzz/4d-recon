# FG ROI Metrics + Oracle-Weak MVEs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让“前景 silhouette 保真度提升”的结论可审计、可复现：补齐更可信的 ROI 指标（`psnr_fg_area/lpips_fg_comp` + boundary-band），并提供 **oracle 背景降权 weak-fusion** 的最小实验入口与 smoke 多 seed 判定流程。

**Architecture:** 先只做“测量 + 最小输入变更”来分离机制与信号质量（不急着改 trainer 的 weak-fusion 公式）；在 evaluator 侧新增 area-only / composite / boundary-band 指标，与现有 fill-black 口径并存；新增脚本把 dataset 的 silhouette mask 导出为 `pseudo_masks.npz`（背景=1/前景=0），从而在不改代码的前提下做 MVE-1。

**Tech Stack:** Python (`numpy`, `PIL`), `pytest`, Bash runners, existing trainer `third_party/FreeTimeGsVanilla/.../simple_trainer_freetime_4d_pure_relocation.py`.

---

## Pre-flight (worktree + tests)

### Task 0: Create a clean worktree for landing changes

**Files:**
- None (git worktree only)

**Step 1: Create worktree**

Run:
```bash
git worktree add -b feat/fg-roi-metrics-oracle-weak ../wt-fg-roi-metrics-oracle-weak
cd ../wt-fg-roi-metrics-oracle-weak
```

Expected: a new worktree directory exists and `git status` is clean.

**Step 2: Run current tests (baseline)**

Run:
```bash
pytest -q
```

Expected: PASS (if FAIL, stop and fix only what this plan touches).

**Step 3: Commit a no-op marker (optional)**

Skip unless you need a checkpoint.

---

## Phase 1: Evaluator metrics that match the diagnosis thresholds

> Why: 两份 opinions 的“通过/失败阈值”依赖 `psnr_fg_area/lpips_fg_comp`，以及（可选）boundary-band；当前 evaluator 只输出 fill-black 的 `psnr_fg/lpips_fg`。

### Task 1: Add `psnr_fg_area` + `lpips_fg_comp` + record `lpips_backend`

**Files:**
- Modify: `scripts/eval_masked_metrics.py`
- Modify: `scripts/tests/test_eval_masked_metrics_contract.py`

**Step 1: Write the failing tests (keys + deterministic ROI semantics)**

Edit `scripts/tests/test_eval_masked_metrics_contract.py` and make two changes.

1) Extend the required keys list:
```python
        for key in (
            "psnr",
            "ssim",
            "lpips",
            "tlpips",
            "psnr_fg",
            "lpips_fg",
            "psnr_fg_area",
            "lpips_fg_comp",
            "lpips_backend",
            "mask_source",
        ):
            assert key in obj, f"missing key: {key}"
        assert obj["lpips_backend"] in ("auto", "dummy", "none")
```

2) Add a direct-array helper plus a deterministic semantic test so the new metrics are not just “present”, but numerically correct under `dummy` LPIPS:
```python
def _write_canvas_concat_arrays(path: Path, gt: np.ndarray, pred: np.ndarray) -> None:
    canvas = np.concatenate([gt, pred], axis=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(canvas).save(path)


def test_eval_masked_metrics_roi_metrics_match_simple_case() -> None:
    with tempfile.TemporaryDirectory(prefix="eval_masked_metrics_exact_") as td:
        root = Path(td)
        data_dir = root / "data_scene"
        cam = "09"
        (data_dir / "images" / cam).mkdir(parents=True, exist_ok=True)
        (data_dir / "masks" / cam).mkdir(parents=True, exist_ok=True)

        gt = np.zeros((32, 40, 3), dtype=np.uint8)
        pred = np.zeros_like(gt)
        pred[..., 1] = 255
        pred[8:24, 10:30, 1] = 0
        pred[8:24, 10:30, 0] = 255

        Image.fromarray(gt).save(data_dir / "images" / cam / "000000.jpg")
        _write_mask(data_dir / "masks" / cam / "000000.png")

        result_dir = root / "run"
        (result_dir / "stats").mkdir(parents=True, exist_ok=True)
        (result_dir / "renders").mkdir(parents=True, exist_ok=True)
        (result_dir / "cfg.yml").write_text(
            "start_frame: 0\nend_frame: 1\ntest_camera_names: 09\neval_sample_every_test: 1\n",
            encoding="utf-8",
        )
        (result_dir / "stats" / "test_step0599.json").write_text(
            json.dumps({"psnr": 1.0, "ssim": 0.1, "lpips": 0.9, "tlpips": 0.01}) + "\n",
            encoding="utf-8",
        )
        _write_canvas_concat_arrays(result_dir / "renders" / "test_step599_0000.png", gt, pred)

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir", str(data_dir),
            "--result_dir", str(result_dir),
            "--stage", "test",
            "--step", "599",
            "--mask_source", "dataset",
            "--bbox_margin_px", "0",
            "--lpips_backend", "dummy",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"

        obj = json.loads((result_dir / "stats_masked" / "test_step0599.json").read_text(encoding="utf-8"))
        assert abs(obj["psnr_fg_area"] - 4.771212547196624) < 1e-6
        assert abs(obj["lpips_fg_comp"] - (320.0 / (32.0 * 40.0 * 3.0))) < 1e-6
```

**Step 2: Run the test to verify it fails**

Run:
```bash
pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q
```

Expected: FAIL with `missing key: psnr_fg_area` or with the new numeric assertions failing.

**Step 3: Implement minimal evaluator changes**

Edit `scripts/eval_masked_metrics.py`:

1) Add a helper (near `_psnr`) for mask-area-normalized PSNR:
```python
def _psnr_mask_area(pred01: np.ndarray, gt01: np.ndarray, keep01: np.ndarray) -> float:
    # keep01: [H,W,1] in {0,1}
    diff = (pred01.astype(np.float32) - gt01.astype(np.float32)) * keep01.astype(np.float32)
    denom = float(np.sum(keep01)) * 3.0
    if denom <= 1e-12:
        return float("nan")
    mse = float(np.sum(diff * diff) / denom)
    if mse <= 1e-12:
        return 99.0
    return 10.0 * math.log10(1.0 / mse)
```

2) In `main()` loop, after you compute `keep = ...[..., None]`:
```python
psnr_area_list.append(_psnr_mask_area(pred_crop, gt_crop, keep))

keep_full = (mask01 > float(args.mask_thr)).astype(np.float32)[..., None]
pred_comp = pred * keep_full + gt * (1.0 - keep_full)
value_lpips_comp = lpips_fn(pred_comp, gt)
if value_lpips_comp is not None:
    lpips_comp_list.append(float(value_lpips_comp))
```

Implementation constraints:
- `keep_full` must be built from full-res `mask01` (not bbox crop).
- Keep existing `psnr_fg/lpips_fg` behavior unchanged.
- If `bbox is None`, continue (do not count this frame into masked stats).

3) Add two new lists before the loop:
```python
psnr_area_list: list[float] = []
lpips_comp_list: list[float] = []
```

4) Extend JSON output:
```python
"lpips_backend": args.lpips_backend,
"psnr_fg_area": float(np.nanmean(psnr_area_list)) if psnr_area_list else float("nan"),
"lpips_fg_comp": float(np.mean(lpips_comp_list)) if lpips_comp_list else float("nan"),
```

**Step 4: Run the test again**

Run:
```bash
pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q
```

Expected: PASS.

**Step 5: Run full suite**

Run:
```bash
pytest -q
```

Expected: PASS.

**Step 6: Commit**

Run:
```bash
git add scripts/eval_masked_metrics.py scripts/tests/test_eval_masked_metrics_contract.py
git commit -m "feat(metrics): add psnr_fg_area and lpips_fg_comp to masked evaluator"
```

---

### Task 2: Add boundary-band ROI metrics (`psnr_bd_area` + `lpips_bd_comp`)

**Files:**
- Modify: `scripts/eval_masked_metrics.py`
- Modify: `scripts/tests/test_eval_masked_metrics_contract.py`

**Step 1: Update contract test first (keys + deterministic boundary semantics)**

Edit `scripts/tests/test_eval_masked_metrics_contract.py` and make two changes.

1) Add required keys:
```python
            "psnr_bd_area",
            "lpips_bd_comp",
            "boundary_band_px",
```

2) Add a deterministic boundary-only semantic test under `dummy` LPIPS:
```python
def test_eval_masked_metrics_boundary_metrics_match_simple_case() -> None:
    with tempfile.TemporaryDirectory(prefix="eval_masked_metrics_boundary_") as td:
        root = Path(td)
        data_dir = root / "data_scene"
        cam = "09"
        (data_dir / "images" / cam).mkdir(parents=True, exist_ok=True)
        (data_dir / "masks" / cam).mkdir(parents=True, exist_ok=True)

        gt = np.zeros((32, 40, 3), dtype=np.uint8)
        pred = np.zeros_like(gt)
        band = np.zeros((32, 40), dtype=np.uint8)
        band[7:25, 9:31] = 1
        band[9:23, 11:29] = 0
        pred[band == 1, 0] = 255

        Image.fromarray(gt).save(data_dir / "images" / cam / "000000.jpg")
        _write_mask(data_dir / "masks" / cam / "000000.png")

        result_dir = root / "run"
        (result_dir / "stats").mkdir(parents=True, exist_ok=True)
        (result_dir / "renders").mkdir(parents=True, exist_ok=True)
        (result_dir / "cfg.yml").write_text(
            "start_frame: 0\nend_frame: 1\ntest_camera_names: 09\neval_sample_every_test: 1\n",
            encoding="utf-8",
        )
        (result_dir / "stats" / "test_step0599.json").write_text(
            json.dumps({"psnr": 1.0, "ssim": 0.1, "lpips": 0.9, "tlpips": 0.01}) + "\n",
            encoding="utf-8",
        )
        _write_canvas_concat_arrays(result_dir / "renders" / "test_step599_0000.png", gt, pred)

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir", str(data_dir),
            "--result_dir", str(result_dir),
            "--stage", "test",
            "--step", "599",
            "--mask_source", "dataset",
            "--bbox_margin_px", "0",
            "--lpips_backend", "dummy",
            "--boundary_band_px", "1",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"

        obj = json.loads((result_dir / "stats_masked" / "test_step0599.json").read_text(encoding="utf-8"))
        assert abs(obj["psnr_bd_area"] - 4.771212547196624) < 1e-6
        assert abs(obj["lpips_bd_comp"] - (144.0 / (32.0 * 40.0 * 3.0))) < 1e-6
```

**Step 2: Run the test to verify it fails**

Run:
```bash
pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q
```

Expected: FAIL with `missing key: psnr_bd_area` or with the new boundary numeric assertions failing.

**Step 3: Implement boundary-band in evaluator**

Edit `scripts/eval_masked_metrics.py`:

1) Add a CLI flag:
```python
ap.add_argument("--boundary_band_px", type=int, default=0, help=">=1 enables boundary-band metrics")
```

2) Add helper to compute band mask from `keep_full` using PIL morphology (no scipy dependency):
```python
from PIL import ImageFilter


def _boundary_band01(keep_full01: np.ndarray, band_px: int) -> np.ndarray:
    # keep_full01: [H,W,1] float in {0,1}
    if band_px <= 0:
        return np.zeros_like(keep_full01, dtype=np.float32)
    size = int(2 * band_px + 1)
    mask_u8 = (keep_full01[..., 0] * 255.0).astype(np.uint8)
    im = Image.fromarray(mask_u8, mode="L")
    dil = im.filter(ImageFilter.MaxFilter(size=size))
    ero = im.filter(ImageFilter.MinFilter(size=size))
    dil01 = (np.asarray(dil, dtype=np.uint8) > 0).astype(np.float32)
    ero01 = (np.asarray(ero, dtype=np.uint8) > 0).astype(np.float32)
    band01 = np.clip(dil01 - ero01, 0.0, 1.0)[..., None]
    return band01
```

3) Add two new lists before the loop:
```python
psnr_bd_area_list: list[float] = []
lpips_bd_comp_list: list[float] = []
```

4) In the loop (after `keep_full` exists), if `args.boundary_band_px >= 1`:
```python
band01 = _boundary_band01(keep_full, int(args.boundary_band_px))
psnr_bd_area_list.append(_psnr_mask_area(pred, gt, band01))

pred_bd_comp = pred * band01 + gt * (1.0 - band01)
value_lpips_bd_comp = lpips_fn(pred_bd_comp, gt)
if value_lpips_bd_comp is not None:
    lpips_bd_comp_list.append(float(value_lpips_bd_comp))
```

Notes:
- Boundary band is computed on full frame to avoid bbox-induced artifacts.
- Keep it optional: if `--boundary_band_px=0`, do not compute / keep output as NaN.

5) Add output fields:
```python
"boundary_band_px": int(args.boundary_band_px),
"psnr_bd_area": float(np.nanmean(psnr_bd_area_list)) if psnr_bd_area_list else float("nan"),
"lpips_bd_comp": float(np.mean(lpips_bd_comp_list)) if lpips_bd_comp_list else float("nan"),
```

**Step 4: Run contract test**

Run:
```bash
pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q
```

Expected: PASS.

**Step 5: Run full suite**

Run:
```bash
pytest -q
```

Expected: PASS.

**Step 6: Commit**

Run:
```bash
git add scripts/eval_masked_metrics.py scripts/tests/test_eval_masked_metrics_contract.py
git commit -m "feat(metrics): add boundary-band psnr_bd_area and lpips_bd_comp"
```

---

## Phase 2: Oracle backgroundness pseudo mask (for weak-fusion MVE-1 without trainer changes)

> Why: opinions-b 的 MVE-1 要求“oracle 背景降权”：给现有公式 `w = 1 - α·mask` 喂 **backgroundness**（背景=1，前景=0），从而相对上调前景 photometric 监督；这是最快的机制证伪。

Precondition:
- `--data_dir` 下必须存在 `masks/<cam>/<frame>.png`。
- `masks/` 必须覆盖训练会用到的所有 camera（否则 trainer 的 pseudo mask 加载会因为缺 camera 而报错）。

### Task 3: Add script to export dataset silhouette to `pseudo_masks.npz` (backgroundness)

**Files:**
- Create: `scripts/export_oracle_background_pseudo_masks_npz.py`
- Test: `scripts/tests/test_export_oracle_background_pseudo_masks_npz_contract.py`

**Step 1: Write failing contract test**

Create `scripts/tests/test_export_oracle_background_pseudo_masks_npz_contract.py`:
```python
#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "export_oracle_background_pseudo_masks_npz.py"


def test_export_oracle_background_pseudo_masks_npz_emits_valid_npz() -> None:
    with tempfile.TemporaryDirectory(prefix="oracle_bg_npz_") as td:
        root = Path(td)
        data_dir = root / "data_scene"
        cam = "09"
        masks_dir = data_dir / "masks" / cam
        masks_dir.mkdir(parents=True, exist_ok=True)

        # 3 frames: simple rectangle silhouette
        for t in range(3):
            arr = np.zeros((16, 20), dtype=np.uint8)
            arr[4:12, 6:14] = 255
            Image.fromarray(arr).save(masks_dir / f"{t:06d}.png")

        out_npz = root / "oracle_bg.npz"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir",
            str(data_dir),
            "--out_npz",
            str(out_npz),
            "--frame_start",
            "0",
            "--num_frames",
            "3",
            "--mask_downscale",
            "4",
            "--overwrite",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 0, f"stdout:\\n{r.stdout}\\n\\nstderr:\\n{r.stderr}"
        assert out_npz.exists()

        with np.load(out_npz, allow_pickle=True) as obj:
            for key in ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale"):
                assert key in obj, f"missing key: {key}"
            masks = obj["masks"]
            assert masks.dtype == np.uint8
            assert masks.shape[0] == 3
            assert masks.shape[1] == 1
            assert int(obj["frame_start"]) == 0
            assert int(obj["num_frames"]) == 3
            assert int(obj["mask_downscale"]) == 4
            # Backgroundness should be mostly 255 (since silhouette is a small rectangle)
            mean = float(masks.astype(np.float32).mean())
            assert mean > 200.0
```

**Step 2: Run the test to verify it fails**

Run:
```bash
pytest -q scripts/tests/test_export_oracle_background_pseudo_masks_npz_contract.py -q
```

Expected: FAIL because the script does not exist.

**Step 3: Implement the script**

Create `scripts/export_oracle_background_pseudo_masks_npz.py`:
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def _fail(msg: str) -> None:
    raise SystemExit(f"[ExportOracleBG][ERROR] {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Export dataset silhouette masks as backgroundness pseudo_masks.npz (bg=1, fg=0)."
    )
    ap.add_argument("--data_dir", required=True, help="Dataset root containing masks/<cam>/<frame>.png")
    ap.add_argument("--out_npz", required=True, help="Output pseudo_masks.npz path")
    ap.add_argument("--frame_start", type=int, required=True)
    ap.add_argument("--num_frames", type=int, required=True)
    ap.add_argument("--mask_downscale", type=int, default=4)
    ap.add_argument("--mask_thr", type=float, default=0.5)
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def _list_camera_names(masks_root: Path) -> list[str]:
    if not masks_root.exists():
        _fail(f"missing masks dir: {masks_root}")
    cams = sorted([p.name for p in masks_root.iterdir() if p.is_dir()])
    if not cams:
        _fail(f"no camera subdirs under: {masks_root}")
    return cams


def _load_mask01(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        arr = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    return np.clip(arr, 0.0, 1.0)


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    out_npz = Path(args.out_npz).resolve()
    masks_root = data_dir / "masks"

    if out_npz.exists() and not args.overwrite:
        _fail(f"out_npz exists: {out_npz} (use --overwrite)")
    out_npz.parent.mkdir(parents=True, exist_ok=True)

    frame_start = int(args.frame_start)
    num_frames = int(args.num_frames)
    if num_frames <= 0:
        _fail(f"num_frames must be >0, got {num_frames}")
    mask_downscale = int(args.mask_downscale)
    if mask_downscale <= 0:
        _fail(f"mask_downscale must be >=1, got {mask_downscale}")

    camera_names = _list_camera_names(masks_root)

    # Determine small mask shape from first frame/cam
    sample = masks_root / camera_names[0] / f"{frame_start:06d}.png"
    if not sample.exists():
        _fail(f"missing sample mask: {sample}")
    m0 = _load_mask01(sample)
    h, w = int(m0.shape[0]), int(m0.shape[1])
    hm, wm = max(1, h // mask_downscale), max(1, w // mask_downscale)

    masks_u8 = np.zeros((num_frames, len(camera_names), hm, wm), dtype=np.uint8)
    thr = float(args.mask_thr)

    for t_local in range(num_frames):
        frame_idx = frame_start + t_local
        for v, cam in enumerate(camera_names):
            p = masks_root / cam / f"{frame_idx:06d}.png"
            if not p.exists():
                _fail(f"missing mask: {p}")
            m01 = _load_mask01(p)
            fg = (m01 > thr).astype(np.float32)
            bg01 = 1.0 - fg
            im = Image.fromarray((bg01 * 255.0).astype(np.uint8), mode="L")
            im = im.resize((wm, hm), resample=Image.Resampling.NEAREST)
            masks_u8[t_local, v] = np.asarray(im, dtype=np.uint8)

    np.savez_compressed(
        out_npz,
        masks=masks_u8,
        camera_names=np.asarray(camera_names, dtype=object),
        frame_start=np.int32(frame_start),
        num_frames=np.int32(num_frames),
        mask_downscale=np.int32(mask_downscale),
    )
    print(f"[ExportOracleBG] wrote: {out_npz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run the test again**

Run:
```bash
pytest -q scripts/tests/test_export_oracle_background_pseudo_masks_npz_contract.py -q
```

Expected: PASS.

**Step 5: Run full suite**

Run:
```bash
pytest -q
```

Expected: PASS.

**Step 6: Commit**

Run:
```bash
git add scripts/export_oracle_background_pseudo_masks_npz.py scripts/tests/test_export_oracle_background_pseudo_masks_npz_contract.py
git commit -m "feat(cue): export oracle background pseudo masks npz"
```

---

## Phase 3: Reproducible MVEs (oracle weak + multi-seed smoke)

### Task 4: Add a dedicated runner for oracle-background weak-fusion on SelfCap

**Files:**
- Create: `scripts/run_train_ours_weak_oracle_bg_selfcap.sh`
- Test: `scripts/tests/test_run_train_ours_weak_oracle_bg_selfcap_contract.py` (static contract only)

**Step 1: Write failing static contract test**

Create `scripts/tests/test_run_train_ours_weak_oracle_bg_selfcap_contract.py`:
```python
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "run_train_ours_weak_oracle_bg_selfcap.sh"


def test_runner_exists_and_mentions_oracle_bg_exporter() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "export_oracle_background_pseudo_masks_npz.py" in text
    assert "PSEUDO_MASK_NPZ" in text
    assert "PSEUDO_MASK_WEIGHT" in text
    assert "PSEUDO_MASK_END_STEP" in text
```

**Step 2: Run the test to verify it fails**

Run:
```bash
pytest -q scripts/tests/test_run_train_ours_weak_oracle_bg_selfcap_contract.py -q
```

Expected: FAIL because the runner does not exist.

**Step 3: Implement the runner**

Create `scripts/run_train_ours_weak_oracle_bg_selfcap.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [result_dir]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
DATA_DIR="${DATA_DIR:-$REPO_ROOT/data/selfcap_bar_8cam60f}"
RESULT_DIR="${1:-${RESULT_DIR:-$REPO_ROOT/outputs/gate1_selfcap_bar_8cam60f_ours_weak_oracle_bg}}"

START_FRAME="${START_FRAME:-0}"
END_FRAME="${END_FRAME:-60}"
MASK_DOWNSCALE="${MASK_DOWNSCALE:-4}"
MASK_THR="${MASK_THR:-0.5}"

# Keep same default weak knobs but allow override for MVE-1 (often try 0.8 / 600)
PSEUDO_MASK_WEIGHT="${PSEUDO_MASK_WEIGHT:-0.8}"
PSEUDO_MASK_END_STEP="${PSEUDO_MASK_END_STEP:-600}"

ORACLE_TAG="${ORACLE_TAG:-oracle_bg_silhouette_ds${MASK_DOWNSCALE}_thr${MASK_THR}}"
ORACLE_DIR="${ORACLE_DIR:-$REPO_ROOT/outputs/cue_mining/$ORACLE_TAG}"
PSEUDO_MASK_NPZ="${PSEUDO_MASK_NPZ:-$ORACLE_DIR/pseudo_masks.npz}"

mkdir -p "$(realpath -m "$RESULT_DIR")"
mkdir -p "$ORACLE_DIR"

if [ ! -f "$PSEUDO_MASK_NPZ" ]; then
  echo "[Oracle-Weak] building oracle background pseudo mask: $PSEUDO_MASK_NPZ"
  "$VENV_PYTHON" "$REPO_ROOT/scripts/export_oracle_background_pseudo_masks_npz.py" \
    --data_dir "$DATA_DIR" \
    --out_npz "$PSEUDO_MASK_NPZ" \
    --frame_start "$START_FRAME" \
    --num_frames "$((END_FRAME - START_FRAME))" \
    --mask_downscale "$MASK_DOWNSCALE" \
    --mask_thr "$MASK_THR" \
    --overwrite
fi

PSEUDO_MASK_NPZ="$PSEUDO_MASK_NPZ" \
PSEUDO_MASK_WEIGHT="$PSEUDO_MASK_WEIGHT" \
PSEUDO_MASK_END_STEP="$PSEUDO_MASK_END_STEP" \
  bash "$REPO_ROOT/scripts/run_train_ours_weak_selfcap.sh" "$RESULT_DIR"
```

**Step 4: Run the test again**

Run:
```bash
pytest -q scripts/tests/test_run_train_ours_weak_oracle_bg_selfcap_contract.py -q
```

Expected: PASS.

**Step 5: Run full suite**

Run:
```bash
pytest -q
```

Expected: PASS.

**Step 6: Commit**

Run:
```bash
git add scripts/run_train_ours_weak_oracle_bg_selfcap.sh scripts/tests/test_run_train_ours_weak_oracle_bg_selfcap_contract.py
git commit -m "feat(runners): add oracle-bg weak-fusion selfcap runner"
```

---

### Task 5: Document the MVE execution checklist (no code, but auditable)

**Files:**
- Modify: `notes/` (choose one)
  - Preferred: `notes/decision-log.md` (if exists)
  - Or create: `notes/2026-03-06-oracle-weak-mve-checklist.md`

**Step 1: Create a short checklist note**

Write:
- Baseline command (600 steps) + result_dir.
- Oracle weak command (same seed) + result_dir.
- Eval commands producing `stats_masked/*.json` with new keys.
- Pass/fail criteria (copy opinions thresholds).

Example commands to include:
```bash
# (1) Train baseline
SEED=42 MAX_STEPS=600 bash scripts/run_train_planb_init_selfcap.sh outputs/mve_baseline_s42

# (2) Train oracle weak
SEED=42 MAX_STEPS=600 PSEUDO_MASK_WEIGHT=0.8 PSEUDO_MASK_END_STEP=600 \
  bash scripts/run_train_ours_weak_oracle_bg_selfcap.sh outputs/mve_oracleweak_s42

# (3) Evaluate masked metrics (dataset masks)
VENV_PYTHON="${VENV_PYTHON:-third_party/FreeTimeGsVanilla/.venv/bin/python}"
"$VENV_PYTHON" scripts/eval_masked_metrics.py --data_dir data/selfcap_bar_8cam60f --result_dir outputs/mve_baseline_s42 \
  --stage test --step 599 --mask_source dataset --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2
"$VENV_PYTHON" scripts/eval_masked_metrics.py --data_dir data/selfcap_bar_8cam60f --result_dir outputs/mve_oracleweak_s42 \
  --stage test --step 599 --mask_source dataset --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2
```

**Step 2: Commit the note**

Run (choose the actual file path you edited):
```bash
git add notes/decision-log.md
# or
git add notes/2026-03-06-oracle-weak-mve-checklist.md
git commit -m "docs(notes): add oracle weak MVE checklist and thresholds"
```

---

### Task 6: Add a 4-seed smoke200 runner with built-in delta summary

**Files:**
- Create: `scripts/run_oracle_weak_smoke200_multiseed.sh`
- Test: `scripts/tests/test_run_oracle_weak_smoke200_multiseed_contract.py` (static contract only)

**Step 1: Write failing static contract test**

Create `scripts/tests/test_run_oracle_weak_smoke200_multiseed_contract.py`:
```python
#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "run_oracle_weak_smoke200_multiseed.sh"


def test_runner_exists_and_mentions_smoke200_summary_metrics() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "SEEDS" in text
    assert "MAX_STEPS" in text
    assert "run_train_planb_init_selfcap.sh" in text
    assert "run_train_ours_weak_oracle_bg_selfcap.sh" in text
    assert "eval_masked_metrics.py" in text
    assert "psnr_fg_area" in text
    assert "lpips_fg_comp" in text
```

**Step 2: Run the test to verify it fails**

Run:
```bash
pytest -q scripts/tests/test_run_oracle_weak_smoke200_multiseed_contract.py -q
```

Expected: FAIL because the runner does not exist.

**Step 3: Implement the runner**

Create `scripts/run_oracle_weak_smoke200_multiseed.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [output_root]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
DATA_DIR="${DATA_DIR:-$REPO_ROOT/data/selfcap_bar_8cam60f}"
OUTPUT_ROOT="${1:-${OUTPUT_ROOT:-$REPO_ROOT/outputs/oracle_weak_smoke200_multiseed}}"

SEEDS="${SEEDS:-41,42,43,44}"
MAX_STEPS="${MAX_STEPS:-200}"
STEP_INDEX="$((MAX_STEPS - 1))"
PSEUDO_MASK_WEIGHT="${PSEUDO_MASK_WEIGHT:-0.8}"
PSEUDO_MASK_END_STEP="${PSEUDO_MASK_END_STEP:-200}"
BOUNDARY_BAND_PX="${BOUNDARY_BAND_PX:-2}"
LPIPS_BACKEND="${LPIPS_BACKEND:-auto}"

mkdir -p "$(realpath -m "$OUTPUT_ROOT")"
IFS=',' read -ra SEED_ARR <<< "$SEEDS"

for seed in "${SEED_ARR[@]}"; do
  seed="${seed// /}"
  [ -n "$seed" ] || continue

  BASE_DIR="$OUTPUT_ROOT/seed${seed}/baseline"
  ORACLE_DIR="$OUTPUT_ROOT/seed${seed}/oracle_weak"

  SEED="$seed" MAX_STEPS="$MAX_STEPS" \
    bash "$REPO_ROOT/scripts/run_train_planb_init_selfcap.sh" "$BASE_DIR"

  SEED="$seed" MAX_STEPS="$MAX_STEPS" \
    PSEUDO_MASK_WEIGHT="$PSEUDO_MASK_WEIGHT" PSEUDO_MASK_END_STEP="$PSEUDO_MASK_END_STEP" \
    bash "$REPO_ROOT/scripts/run_train_ours_weak_oracle_bg_selfcap.sh" "$ORACLE_DIR"

  "$VENV_PYTHON" "$REPO_ROOT/scripts/eval_masked_metrics.py" \
    --data_dir "$DATA_DIR" --result_dir "$BASE_DIR" \
    --stage test --step "$STEP_INDEX" --mask_source dataset \
    --bbox_margin_px 32 --lpips_backend "$LPIPS_BACKEND" --boundary_band_px "$BOUNDARY_BAND_PX"

  "$VENV_PYTHON" "$REPO_ROOT/scripts/eval_masked_metrics.py" \
    --data_dir "$DATA_DIR" --result_dir "$ORACLE_DIR" \
    --stage test --step "$STEP_INDEX" --mask_source dataset \
    --bbox_margin_px 32 --lpips_backend "$LPIPS_BACKEND" --boundary_band_px "$BOUNDARY_BAND_PX"
done

"$VENV_PYTHON" - "$OUTPUT_ROOT" "$SEEDS" "$STEP_INDEX" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
seeds = [s.strip() for s in sys.argv[2].split(",") if s.strip()]
step_index = int(sys.argv[3])
pass_count = 0

for seed in seeds:
    base_path = root / f"seed{seed}" / "baseline" / "stats_masked" / f"test_step{step_index:04d}.json"
    oracle_path = root / f"seed{seed}" / "oracle_weak" / "stats_masked" / f"test_step{step_index:04d}.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))

    d_psnr = float(oracle["psnr_fg_area"]) - float(base["psnr_fg_area"])
    d_lpips = float(oracle["lpips_fg_comp"]) - float(base["lpips_fg_comp"])
    d_tlpips = float(oracle["tlpips"]) - float(base["tlpips"])
    d_bd_psnr = float(oracle["psnr_bd_area"]) - float(base["psnr_bd_area"])
    d_bd_lpips = float(oracle["lpips_bd_comp"]) - float(base["lpips_bd_comp"])

    passed = (
        d_psnr >= 0.2
        and d_lpips <= -0.003
        and d_tlpips <= 0.01
        and (d_bd_psnr >= 0.2 or d_bd_lpips <= -0.001)
    )
    pass_count += int(passed)
    print(
        f"seed={seed} pass={passed} "
        f"d_psnr_fg_area={d_psnr:+.4f} d_lpips_fg_comp={d_lpips:+.6f} "
        f"d_tlpips={d_tlpips:+.6f} d_psnr_bd_area={d_bd_psnr:+.4f} d_lpips_bd_comp={d_bd_lpips:+.6f}"
    )

print(f"pass_count={pass_count}/{len(seeds)}")
if pass_count >= 3:
    print("decision=continue")
else:
    print("decision=stop")
PY
```

**Step 4: Run the test again**

Run:
```bash
pytest -q scripts/tests/test_run_oracle_weak_smoke200_multiseed_contract.py -q
```

Expected: PASS.

**Step 5: Run full suite**

Run:
```bash
pytest -q
```

Expected: PASS.

**Step 6: Commit**

Run:
```bash
git add scripts/run_oracle_weak_smoke200_multiseed.sh scripts/tests/test_run_oracle_weak_smoke200_multiseed_contract.py
git commit -m "feat(runners): add multiseed smoke200 oracle weak driver"
```

---

## Decision Gates (stop/continue rules)

After Phase 1–3 lands, run MVEs and decide:

1) **If oracle weak passes** (≥ +0.2dB `psnr_fg_area`, ≤ -0.003 `lpips_fg_comp`, `ΔtLPIPS ≤ +0.01`, boundary-band at least one improves):
   - Continue weak line with early-only schedule; consider later aligning trainer formula to `w=1+α·mask` to remove confusion, but only after you freeze the “oracle proof”.

2) **If oracle weak fails** (FG + boundary-band still collectively reverse):
   - Stop spending time on weak-fusion pseudo-mask weighting; jump to silhouette/opacity direct constraints or stronger motion priors (out of scope for this plan).

3) **If results are not stable across seeds**:
   - Run `scripts/run_oracle_weak_smoke200_multiseed.sh`; if its final summary reports `pass_count <= 2/4`, stop that line.

---

## Verification Before Completion

Before claiming this plan “done”:
- `pytest -q` must PASS.
- A sample masked stats JSON must contain new keys:
  - `psnr_fg_area`, `lpips_fg_comp`, `lpips_backend`, `psnr_bd_area`, `lpips_bd_comp`, `boundary_band_px`.
