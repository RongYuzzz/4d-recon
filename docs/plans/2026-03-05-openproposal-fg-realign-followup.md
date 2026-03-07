# OpenProposal Foreground Realignment (Phase 3/4 Follow-up) Implementation Plan

> **Execution note:** 按 Task 顺序逐条执行；每个 Task 的 Expected 通过后再进入下一步。

**Goal:** 让 Phase 3（weak-fusion）与 Phase 4（VGGT feature-metric loss）在 **silhouette ROI** 上真正“有信号、可解释、可迭代”：优先追求 `psnr_fg ↑`、`lpips_fg ↓`，并满足 guardrail `ΔtLPIPS <= +0.01`；同时把“mask 体检口径”和 evaluator 的敏感性补齐，避免被误导。

**Architecture:** 先用 TDD 落地 2 个小工具（pseudo-mask 幅度标定、fg evaluator 追加对照口径），再用 600-step timebox 做最小 A/B：  
Phase 3 先证明 weak-fusion 不是 no-op（mask 不再常数/饱和），再验证“方向是否反了”（相对 upweight dynamic）。  
Phase 4 先去掉稀疏 gate（或直接 gating=none），再提升 `phi_size`（降 `phi_downscale`）验证“监督过粗”是否为主因。所有结果写入 notes（不提交 data/outputs）。

**Tech Stack:** Python 3.12, numpy, Pillow, pytest, tensorboard event_accumulator, FreeTimeGsVanilla venv（torch+lpips+vggt）。

---

## Preconditions / 非目标

- **local-eval only**：禁止把 `data/`、`outputs/`（含 masks、renders、cache、ckpt、视频）加入 git；只提交脚本与 `notes/`/`docs/`。
- `outputs/` **append-only**：新实验必须用新的 `RESULT_DIR`（不要覆盖旧目录）。
- 本计划假设 baseline anchor 已存在：  
  `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats/test_step0599.json`
  - 若缺失：先按 Phase 1 计划补跑 baseline，再回到本计划。

---

### Task 0: Create Worktree + Gate Checks

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: Create an isolated worktree**

```bash
git worktree add -b owner-b-20260305-fg-realign \
  .worktrees/owner-b-20260305-fg-realign \
  HEAD
cd .worktrees/owner-b-20260305-fg-realign
```

**Step 2: Run unit tests (must start clean)**

Run: `pytest -q`  
Expected: PASS

**Step 2.5: VGGT offline preflight (avoid mid-run download stalls)**

> 说明：本仓库常用的 VGGT 缓存目录为 `/root/autodl-tmp/cache/vggt`（通常是指向 HF cache 的软链）。  
> 若你是第一次在该机跑 VGGT：把 `HF_HUB_OFFLINE=1` 临时改成 `0` 先下载一次。

Run:
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
test -x "$VENV_PYTHON"

export VGGT_MODEL_ID="facebook/VGGT-1B"
export VGGT_MODEL_CACHE_DIR="${VGGT_MODEL_CACHE_DIR:-/root/autodl-tmp/cache/vggt}"
mkdir -p "$VGGT_MODEL_CACHE_DIR" || true

HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" -c "from vggt.models.vggt import VGGT; VGGT.from_pretrained('$VGGT_MODEL_ID', cache_dir='$VGGT_MODEL_CACHE_DIR'); print('ok')"
```

Expected: 打印 `ok`

**Step 3: Pin baseline init NPZ (fairness gate)**

Run:
```bash
BASELINE_CFG="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/cfg.yml"
test -f "$BASELINE_CFG"

PLANB_INIT_NPZ="$(python3 - <<'PY'
from pathlib import Path
p = Path("outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/cfg.yml")
for line in p.read_text(encoding="utf-8").splitlines():
  if line.startswith("init_npz_path:"):
    print(line.split(":", 1)[1].strip())
    raise SystemExit(0)
raise SystemExit("missing init_npz_path")
PY
)"
test -f "$PLANB_INIT_NPZ"
echo "PLANB_INIT_NPZ=$PLANB_INIT_NPZ"
sha256sum "$PLANB_INIT_NPZ"
```

Expected: 打印一个存在的 `init_points_planb_step*.npz` 路径 + 对应 sha256（后续所有 treatment 必须同一文件）

**Step 4: Record “local-only” discipline in note (optional but recommended)**

Create: `notes/openproposal_phase6_fg_realign_scope.md`

Content (copy/paste):
```md
# Phase 6 FG realign — local-only scope

- This phase is local-eval only.
- Do NOT commit anything under `data/` or `outputs/`.
- All new experiments must use new `outputs/.../<result_dir>` folders (append-only).
```

Run:
```bash
git add notes/openproposal_phase6_fg_realign_scope.md
git commit -m "docs(notes): add Phase6 fg realign local-only scope note"
```

---

### Task 1: Add Pseudo-Mask Scaling Tool (fix “mask is too weak / invert saturates”)

**Files:**
- Create: `scripts/scale_pseudo_masks_npz.py`
- Test: `scripts/tests/test_scale_pseudo_masks_npz_contract.py`

**Step 1: Write failing contract test**

Create `scripts/tests/test_scale_pseudo_masks_npz_contract.py`:
```python
#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "scale_pseudo_masks_npz.py"


def _write_npz(path: Path) -> None:
    masks = np.array([[[[0, 10], [20, 30]]]], dtype=np.uint8)  # [T=1,V=1,H=2,W=2]
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        masks=masks,
        camera_names=np.asarray(["09"], dtype=object),
        frame_start=np.int32(0),
        num_frames=np.int32(1),
        mask_downscale=np.int32(4),
    )


def test_scale_dynamic_matches_numpy_quantile() -> None:
    with tempfile.TemporaryDirectory(prefix="scale_pseudo_") as td:
        root = Path(td)
        in_npz = root / "in.npz"
        out_npz = root / "out.npz"
        _write_npz(in_npz)

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--in_npz",
            str(in_npz),
            "--out_npz",
            str(out_npz),
            "--quantile",
            "0.50",
            "--mode",
            "dynamic_scaled",
            "--overwrite",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"stdout:\\n{proc.stdout}\\n\\nstderr:\\n{proc.stderr}"
        assert out_npz.exists()

        with np.load(in_npz, allow_pickle=True) as din:
            m = din["masks"].astype(np.float32) / 255.0
        q = float(np.quantile(m.reshape(-1), 0.50))
        expected = np.clip(m / (q + 1e-6), 0.0, 1.0).astype(np.float32)

        with np.load(out_npz, allow_pickle=True) as dout:
            out = np.asarray(dout["masks"], dtype=np.float32)
            assert out.shape == expected.shape
            assert float(out.min()) >= 0.0
            assert float(out.max()) <= 1.0
            assert np.allclose(out, expected, atol=1e-6)


def test_scale_static_is_one_minus_dynamic() -> None:
    with tempfile.TemporaryDirectory(prefix="scale_pseudo_") as td:
        root = Path(td)
        in_npz = root / "in.npz"
        out_dyn = root / "dyn.npz"
        out_sta = root / "sta.npz"
        _write_npz(in_npz)

        base = [
            sys.executable,
            str(SCRIPT),
            "--in_npz",
            str(in_npz),
            "--quantile",
            "0.50",
            "--overwrite",
        ]
        subprocess.check_call(base + ["--out_npz", str(out_dyn), "--mode", "dynamic_scaled"])
        subprocess.check_call(base + ["--out_npz", str(out_sta), "--mode", "static_from_dynamic_scaled"])

        with np.load(out_dyn, allow_pickle=True) as dd, np.load(out_sta, allow_pickle=True) as ds:
            dyn = np.asarray(dd["masks"], dtype=np.float32)
            sta = np.asarray(ds["masks"], dtype=np.float32)
        assert np.allclose(sta, 1.0 - dyn, atol=1e-6)
```

**Step 2: Run the new tests (should FAIL because script is missing)**

Run: `pytest -q scripts/tests/test_scale_pseudo_masks_npz_contract.py -q`  
Expected: FAIL with “No such file or directory: scale_pseudo_masks_npz.py” (or similar)

**Step 3: Implement minimal scaling script**

Create `scripts/scale_pseudo_masks_npz.py`:
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def _fail(msg: str) -> None:
    raise SystemExit(f"[ScalePseudoMasks][ERROR] {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Scale uint8/float pseudo masks into float32 [0,1].")
    ap.add_argument("--in_npz", required=True)
    ap.add_argument("--out_npz", required=True)
    ap.add_argument("--quantile", type=float, default=0.99, help="Global quantile for scaling (e.g. 0.99)")
    ap.add_argument("--eps", type=float, default=1e-6)
    ap.add_argument(
        "--mode",
        choices=["dynamic_scaled", "static_from_dynamic_scaled"],
        default="dynamic_scaled",
    )
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def _load_required(npz: Path) -> tuple[np.ndarray, np.ndarray, int, int, int]:
    with np.load(npz, allow_pickle=True) as obj:
        required = ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale")
        missing = [k for k in required if k not in obj]
        if missing:
            _fail(f"npz missing keys: {missing}")
        masks = np.asarray(obj["masks"])
        cams = np.asarray(obj["camera_names"])
        frame_start = int(obj["frame_start"])
        num_frames = int(obj["num_frames"])
        down = int(obj["mask_downscale"])
    return masks, cams, frame_start, num_frames, down


def _to_float01(masks: np.ndarray) -> np.ndarray:
    if masks.dtype == np.uint8:
        return masks.astype(np.float32) / 255.0
    if masks.dtype in (np.float16, np.float32, np.float64):
        return np.clip(masks.astype(np.float32), 0.0, 1.0)
    _fail(f"unsupported masks dtype: {masks.dtype}")
    raise AssertionError


def main() -> int:
    args = parse_args()
    in_npz = Path(args.in_npz).resolve()
    out_npz = Path(args.out_npz).resolve()
    if not in_npz.exists():
        _fail(f"missing in_npz: {in_npz}")
    if out_npz.exists() and not args.overwrite:
        _fail(f"out_npz exists: {out_npz} (use --overwrite)")
    out_npz.parent.mkdir(parents=True, exist_ok=True)

    masks, cams, frame_start, num_frames, down = _load_required(in_npz)
    m01 = _to_float01(masks)
    if not (0.0 < args.quantile < 1.0):
        _fail(f"quantile must be in (0,1), got {args.quantile}")
    q = float(np.quantile(m01.reshape(-1), float(args.quantile)))
    denom = q + float(args.eps)
    if not np.isfinite(denom) or denom <= 0:
        _fail(f"invalid denom from quantile: q={q} eps={args.eps}")

    dyn = np.clip(m01 / denom, 0.0, 1.0).astype(np.float32)
    if args.mode == "dynamic_scaled":
        out_masks = dyn
        op = "dynamic_scaled"
    else:
        out_masks = (1.0 - dyn).astype(np.float32)
        op = "static_from_dynamic_scaled"

    np.savez_compressed(
        out_npz,
        masks=out_masks,
        camera_names=cams,
        frame_start=np.int32(int(frame_start)),
        num_frames=np.int32(int(num_frames)),
        mask_downscale=np.int32(int(down)),
        source_npz=str(in_npz),
        scale_quantile=np.float32(float(args.quantile)),
        scale_value=np.float32(float(q)),
        op=np.asarray([op], dtype=object),
    )
    print(f"[ScalePseudoMasks] wrote: {out_npz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run the new tests (should PASS)**

Run: `pytest -q scripts/tests/test_scale_pseudo_masks_npz_contract.py -q`  
Expected: PASS

**Step 5: Run full test suite**

Run: `pytest -q`  
Expected: PASS

**Step 6: Commit**

```bash
git add scripts/scale_pseudo_masks_npz.py scripts/tests/test_scale_pseudo_masks_npz_contract.py
git commit -m "feat(cue): add pseudo mask scaling tool"
```

---

### Task 2: Extend Foreground Evaluator (add more sensitive fg metrics + record lpips_backend)

**Files:**
- Modify: `scripts/eval_masked_metrics.py`
- Modify: `scripts/tests/test_eval_masked_metrics_contract.py`

**Step 1: Update contract test first (make it fail)**

Edit `scripts/tests/test_eval_masked_metrics_contract.py` and extend required keys list:
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

**Step 2: Run the test (should FAIL because new keys are missing)**

Run: `pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q`  
Expected: FAIL with “missing key: psnr_fg_area” (or similar)

**Step 3: Implement evaluator changes**

Edit `scripts/eval_masked_metrics.py`:

1) Add helper for mask-area-normalized PSNR:
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

2) 在主 loop 里（已有 `keep = ...[..., None]` 之后）追加两项：
```python
psnr_area_list.append(_psnr_mask_area(pred_crop, gt_crop, keep))

pred_comp = pred * keep_full + gt * (1.0 - keep_full)  # keep_full = (mask01>thr)[...,None]
lpips_comp = lpips_fn(pred_comp, gt)
if lpips_comp is not None:
    lpips_comp_list.append(float(lpips_comp))
```

实现细节约束：
- `keep_full` 应该用 full-res 的 mask（不是 bbox crop）。
- 如果 mask 为空（bbox None），保持当前逻辑 continue（不统计该帧）。

3) 输出 JSON 追加字段（按 “只新增、不破坏旧字段”）：
```python
"lpips_backend": args.lpips_backend,
"psnr_fg_area": float(np.nanmean(psnr_area_list)) if psnr_area_list else float("nan"),
"lpips_fg_comp": float(np.mean(lpips_comp_list)) if lpips_comp_list else float("nan"),
```

**Step 4: Run the updated test**

Run: `pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q`  
Expected: PASS

**Step 5: Run full test suite**

Run: `pytest -q`  
Expected: PASS

**Step 6: Commit**

```bash
git add scripts/eval_masked_metrics.py scripts/tests/test_eval_masked_metrics_contract.py
git commit -m "feat(metrics): add psnr_fg_area and lpips_fg_comp to masked evaluator"
```

---

### Task 3 (Recommended): Add “Mask Health-Check” Script (thr_pred sweep + top-p overlap)

**Files:**
- Create: `scripts/mask_healthcheck_sweep.py`
- Test: `scripts/tests/test_mask_healthcheck_sweep_contract.py`

**Step 1: Write failing contract test**

Create `scripts/tests/test_mask_healthcheck_sweep_contract.py` (keep it minimal: only checks JSON keys exist & values are finite):
```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "mask_healthcheck_sweep.py"


def test_mask_healthcheck_emits_summary_json() -> None:
    with tempfile.TemporaryDirectory(prefix="mask_health_") as td:
        root = Path(td)
        data_dir = root / "data_scene"
        cam = "09"
        (data_dir / "masks" / cam).mkdir(parents=True, exist_ok=True)

        # GT: rectangle mask for 3 frames
        for t in range(3):
            arr = np.zeros((16, 20), dtype=np.uint8)
            arr[4:12, 6:14] = 255
            Image.fromarray(arr).save(data_dir / "masks" / cam / f"{t:06d}.png")

        # Pred: low-amplitude soft mask aligned with GT
        masks = np.zeros((3, 1, 4, 5), dtype=np.uint8)
        masks[:, 0, 1:3, 2:4] = 20  # small values
        pred_npz = root / "pred.npz"
        np.savez_compressed(
            pred_npz,
            masks=masks,
            camera_names=np.asarray([cam], dtype=object),
            frame_start=np.int32(0),
            num_frames=np.int32(3),
            mask_downscale=np.int32(4),
        )

        out_json = root / "out.json"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir",
            str(data_dir),
            "--pred_mask_npz",
            str(pred_npz),
            "--camera",
            cam,
            "--out_json",
            str(out_json),
            "--thr_pred_list",
            "0.01,0.05,0.10,0.50",
            "--top_p_list",
            "0.05,0.10",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"stdout:\\n{proc.stdout}\\n\\nstderr:\\n{proc.stderr}"
        obj = json.loads(out_json.read_text(encoding="utf-8"))
        for key in ("best_miou_fg", "best_thr_pred", "top_p_overlap"):
            assert key in obj
```

**Step 2: Run test (should FAIL because script missing)**

Run: `pytest -q scripts/tests/test_mask_healthcheck_sweep_contract.py -q`  
Expected: FAIL

**Step 3: Implement the script (pure numpy, no sklearn)**

Create `scripts/mask_healthcheck_sweep.py`:
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _fail(msg: str) -> None:
    raise SystemExit(f"[MaskHealthcheck][ERROR] {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sweep pred thresholds and report mIoU/top-p overlap vs GT silhouette.")
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--pred_mask_npz", required=True, help="pseudo_masks.npz")
    ap.add_argument("--camera", required=True)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--thr_gt", type=float, default=0.5)
    ap.add_argument("--thr_pred_list", default="0.01,0.02,0.05,0.1,0.2,0.5")
    ap.add_argument("--top_p_list", default="0.01,0.05,0.1")
    return ap.parse_args()


def _load_mask01(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        m = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    return np.clip(m, 0.0, 1.0)


def _load_pred01_tv(pred_npz: Path, camera: str) -> np.ndarray:
    with np.load(pred_npz, allow_pickle=True) as d:
        masks = np.asarray(d["masks"])
        cams = [str(x) for x in d["camera_names"].tolist()]
        if camera not in cams:
            _fail(f"camera not found in npz: {camera} not in {cams}")
        vi = cams.index(camera)
        m = masks[:, vi].astype(np.float32)
        if float(m.max()) > 1.0:
            m = m / 255.0
        return np.clip(m, 0.0, 1.0)


def _resize_pred_to_gt(pred01_small: np.ndarray, hw: tuple[int, int]) -> np.ndarray:
    h, w = hw
    out = np.empty((pred01_small.shape[0], h, w), dtype=np.float32)
    for t in range(pred01_small.shape[0]):
        im = Image.fromarray((pred01_small[t] * 255.0).astype(np.uint8), mode="L")
        im = im.resize((w, h), resample=Image.Resampling.BILINEAR)
        out[t] = np.asarray(im, dtype=np.float32) / 255.0
    return np.clip(out, 0.0, 1.0)


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    pred_npz = Path(args.pred_mask_npz).resolve()
    out_json = Path(args.out_json).resolve()
    cam = str(args.camera)

    gt_dir = data_dir / "masks" / cam
    if not gt_dir.is_dir():
        _fail(f"missing GT mask dir: {gt_dir}")
    if not pred_npz.exists():
        _fail(f"missing pred_mask_npz: {pred_npz}")

    pred_small = _load_pred01_tv(pred_npz, camera=cam)
    num_frames = int(pred_small.shape[0])
    gt0 = _load_mask01(gt_dir / f"{0:06d}.png")
    pred = _resize_pred_to_gt(pred_small, hw=gt0.shape[:2])

    gt = []
    for t in range(num_frames):
        p = gt_dir / f"{t:06d}.png"
        if not p.exists():
            _fail(f"missing GT mask frame: {p}")
        gt.append(_load_mask01(p))
    gt = np.stack(gt, axis=0)
    gt_bin = gt > float(args.thr_gt)

    thr_list = [float(x) for x in args.thr_pred_list.split(",") if x.strip()]
    top_p_list = [float(x) for x in args.top_p_list.split(",") if x.strip()]

    def miou_for_thr(thr: float) -> float:
        ious = []
        for t in range(num_frames):
            pb = pred[t] > thr
            gb = gt_bin[t]
            inter = float(np.logical_and(pb, gb).sum())
            union = float(np.logical_or(pb, gb).sum())
            if union > 0:
                ious.append(inter / union)
        return float(np.mean(ious)) if ious else float("nan")

    best_thr = None
    best_miou = -1.0
    for thr in thr_list:
        m = miou_for_thr(thr)
        if np.isfinite(m) and m > best_miou:
            best_miou = float(m)
            best_thr = float(thr)

    top_p_overlap: dict[str, float] = {}
    for p in top_p_list:
        if p <= 0 or p > 1:
            continue
        overlaps = []
        for t in range(num_frames):
            flat = pred[t].reshape(-1)
            k = max(1, int(np.ceil(p * flat.size)))
            idx = np.argpartition(flat, -k)[-k:]
            topk = np.zeros_like(flat, dtype=bool)
            topk[idx] = True
            gb = gt_bin[t].reshape(-1)
            inter = float(np.logical_and(topk, gb).sum())
            denom = float(np.sum(topk)) if float(np.sum(topk)) > 0 else 1.0
            overlaps.append(inter / denom)
        top_p_overlap[f"{p:g}"] = float(np.mean(overlaps)) if overlaps else float("nan")

    out: dict[str, Any] = {
        "camera": cam,
        "num_frames": num_frames,
        "thr_gt": float(args.thr_gt),
        "thr_pred_list": thr_list,
        "best_miou_fg": float(best_miou),
        "best_thr_pred": float(best_thr) if best_thr is not None else None,
        "top_p_overlap": top_p_overlap,
        "pred_mask_npz": str(pred_npz),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"[MaskHealthcheck] wrote: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: Run test (PASS)**

Run: `pytest -q scripts/tests/test_mask_healthcheck_sweep_contract.py -q`  
Expected: PASS

**Step 5: Run full test suite + commit**

```bash
pytest -q
git add scripts/mask_healthcheck_sweep.py scripts/tests/test_mask_healthcheck_sweep_contract.py
git commit -m "feat(diagnostics): add pseudomask healthcheck sweep tool"
```

---

### Task 4: Phase 3 Follow-up Runs (prove non-no-op + test direction flip)

**Files:**
- Create: `notes/openproposal_phase6_fg_realign_phase3.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: Produce scaled dynamic & non-saturating static masks**

```bash
MASK_DIR="outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3"
IN_NPZ="$MASK_DIR/pseudo_masks.npz"
OUT_DYN="$MASK_DIR/pseudo_masks_dyn_p99.npz"
OUT_STA="$MASK_DIR/pseudo_masks_static_from_dyn_p99.npz"

python3 scripts/scale_pseudo_masks_npz.py --in_npz "$IN_NPZ" --out_npz "$OUT_DYN" --quantile 0.99 --mode dynamic_scaled --overwrite
python3 scripts/scale_pseudo_masks_npz.py --in_npz "$IN_NPZ" --out_npz "$OUT_STA" --quantile 0.99 --mode static_from_dynamic_scaled --overwrite
```

Expected: 两个 `*.npz` 都存在，且 `masks` dtype 为 float（非 uint8 也可）

**Step 2: Sanity-check mask ranges (must not be “almost constant”)**

Run:
```bash
python3 - <<'PY'
import numpy as np
def show(path):
  with np.load(path, allow_pickle=True) as d: m=np.asarray(d["masks"], dtype=np.float32)
  print(path, "shape", m.shape, "min/max/mean", float(m.min()), float(m.max()), float(m.mean()))
  flat=m.reshape(-1)
  for thr in [0.1,0.2,0.5,0.8]:
    print(" ratio>=",thr, float((flat>=thr).mean()))
  print()
show("outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_dyn_p99.npz")
show("outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz")
PY
```

Expected (heuristic): dyn 的 `mean` 明显大于原始 0.001 量级；static 不应接近 1.0 常数

**Step 3: Run treatment A (dynamic_scaled, same init)**

```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
TRAINER="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"

DATA_DIR="data/thuman4_subject00_8cam60f"
GPU=0
MAX_STEPS=600

RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_dynp99_w0.8_600"
PSEUDO_MASK_NPZ="outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_dyn_p99.npz"
PSEUDO_MASK_WEIGHT=0.8

CUDA_VISIBLE_DEVICES="$GPU" "$VENV_PYTHON" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
  --result-dir "$RESULT_DIR" \
  --start-frame 0 --end-frame 60 \
  --max-steps "$MAX_STEPS" \
  --eval-steps "$MAX_STEPS" \
  --save-steps "$MAX_STEPS" \
  --seed 42 \
  --train-camera-names "02,03,04,05,06,07" \
  --val-camera-names "08" \
  --test-camera-names "09" \
  --eval-sample-every 1 \
  --eval-sample-every-test 1 \
  --render-traj-path fixed \
  --global-scale 6 \
  --pseudo-mask-npz "$PSEUDO_MASK_NPZ" \
  --pseudo-mask-weight "$PSEUDO_MASK_WEIGHT" \
  --pseudo-mask-end-step "$MAX_STEPS" \
  --eval-on-test
```

Expected:
- `$RESULT_DIR/stats/test_step0599.json` exists

**Step 4: Run treatment B (static_from_dynamic_scaled, direction flip without negative alpha)**

Same as Step 3, only change:
- `RESULT_DIR=".../planb_init_weak_staticp99_w0.8_600"`
- `PSEUDO_MASK_NPZ="$OUT_STA"`

Expected:
- `$RESULT_DIR/stats/test_step0599.json` exists

**Step 5: Run masked eval (must use real LPIPS when possible)**

```bash
for R in \
  outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600 \
  outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_dynp99_w0.8_600 \
  outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w0.8_600
do
  "$VENV_PYTHON" scripts/eval_masked_metrics.py \
    --data_dir data/thuman4_subject00_8cam60f \
    --result_dir "$R" \
    --stage test \
    --step 599 \
    --mask_source dataset \
    --bbox_margin_px 32 \
    --mask_thr 0.5 \
    --lpips_backend auto
done
```

Expected:
- each run emits `stats_masked/test_step0599.json`（含 `psnr_fg_area` / `lpips_fg_comp` / `lpips_backend`）

**Step 6: Export TB scalars to prove weak path is active (pseudo_mask/active_ratio not ~1.0)**

```bash
python3 scripts/export_tb_scalars.py \
  --run_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_dynp99_w0.8_600 \
  --tags "pseudo_mask/active_ratio,loss/l1_raw,loss_weighted/l1" \
  --out_dir outputs/qualitative_local/openproposal_phase6/tb_scalars
```

Expected: CSV exists under `outputs/qualitative_local/openproposal_phase6/tb_scalars/`

**Step 7: Write results note + commit**

Create `notes/openproposal_phase6_fg_realign_phase3.md` with:
- three runs paths + init_npz_path equality check
- full-frame + masked metrics table（至少填：psnr/lpips/tlpips/psnr_fg/lpips_fg/psnr_fg_area/lpips_fg_comp）
- decision: 哪条（dyn/static）更接近目标；是否满足 `ΔtLPIPS<=+0.01`

Commit:
```bash
git add notes/openproposal_phase6_fg_realign_phase3.md
git commit -m "docs(notes): Phase6 Phase3 fg realign follow-up results"
```

---

### Task 5: Phase 4 Follow-up Runs (disable gating, then increase phi_size)

**Files:**
- Create: `notes/openproposal_phase6_fg_realign_phase4.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: Run feature-loss with gating disabled (same cache, same init)**

Run (example; pick an unused RESULT_DIR):
```bash
DATA_DIR="data/thuman4_subject00_8cam60f" \
RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_nogate_lam0.005_600_sameinit" \
GPU=0 MAX_STEPS=600 \
VENV_PYTHON="${VENV_PYTHON:-$(pwd)/third_party/FreeTimeGsVanilla/.venv/bin/python}" \
PLANB_INIT_NPZ="$PLANB_INIT_NPZ" \
VGGT_MODEL_ID="${VGGT_MODEL_ID:-facebook/VGGT-1B}" \
VGGT_MODEL_CACHE_DIR="${VGGT_MODEL_CACHE_DIR:-/root/autodl-tmp/cache/vggt}" \
VGGT_CACHE_OUT_DIR="outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10" \
VGGT_FEAT_PHI_NAME="token_proj" \
VGGT_FEAT_LOSS_TYPE="cosine" \
LAMBDA_VGGT_FEAT="0.005" \
VGGT_FEAT_START_STEP="0" \
VGGT_FEAT_RAMP_STEPS="400" \
VGGT_FEAT_EVERY="8" \
VGGT_FEAT_GATING="none" \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Expected:
- `.../stats/test_step0599.json` exists
- TB 中 `vggt_feat/active` 在 step 200/400 非零
- 数量级检查：`vggt_feat/active` 应接近 `meta.json` 里的 `phi_size[0] * phi_size[1]`

**Step 1.5（关键公平性 Gate）：确认 treatment `init_npz_path` 与 baseline 完全一致**

Run:
```bash
BASELINE_CFG="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/cfg.yml"
TREAT_CFG="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_nogate_lam0.005_600_sameinit/cfg.yml"
test -f "$BASELINE_CFG"
test -f "$TREAT_CFG"

echo "[baseline init_npz_path]" && rg -n "^init_npz_path:" "$BASELINE_CFG"
echo "[treat init_npz_path]" && rg -n "^init_npz_path:" "$TREAT_CFG"
```

Expected: 两边路径完全相同；若不同，该 run 视为 **confounded**（无效对照），需要重跑 same-init。

**Step 2: Masked eval + export TB scalars**

Masked eval:
```bash
"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_nogate_lam0.005_600_sameinit \
  --stage test --step 599 \
  --mask_source dataset --bbox_margin_px 32 --mask_thr 0.5 \
  --lpips_backend auto
```

TB export:
```bash
python3 scripts/export_tb_scalars.py \
  --run_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_nogate_lam0.005_600_sameinit \
  --tags "vggt_feat/active,loss/feat_raw,loss_weighted/feat,loss/total" \
  --out_dir outputs/qualitative_local/openproposal_phase6/tb_scalars
```

**Step 3 (Gate): if fg still degrades, increase phi_size by lowering phi_downscale**

Precompute new cache (ds2, no framediff gate):
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
test -x "$VENV_PYTHON"

export VGGT_MODEL_ID="facebook/VGGT-1B"
export VGGT_MODEL_CACHE_DIR="/root/autodl-tmp/cache/vggt"

NEW_TAG="openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds2_nogate"
NEW_CACHE_DIR="outputs/vggt_cache/$NEW_TAG"

HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" scripts/precompute_vggt_cache.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --out_dir "$NEW_CACHE_DIR" \
  --camera_ids "02,03,04,05,06,07,08,09" \
  --frame_start 0 --num_frames 60 \
  --backend vggt \
  --phi_name token_proj \
  --phi_downscale 2 \
  --token_layer_idx 17 \
  --token_proj_dim 32 \
  --token_proj_seed 20260225 \
  --token_proj_normalize 1 \
  --save_framediff_gate 0 \
  --framediff_top_p 1.0 \
  --vggt_model_id "$VGGT_MODEL_ID" \
  --vggt_cache_dir "$VGGT_MODEL_CACHE_DIR" \
  --vggt_mode crop \
  --overwrite
```

Expected:
- `$NEW_CACHE_DIR/meta.json` shows `phi_size` 相比 ds4 约翻倍（通常接近 `16×18`，以实际 `meta.json` 为准）

Then rerun training with the new cache dir (same as Step 1, only change):
- `RESULT_DIR=".../planb_feat_v2_ds2_nogate_lam0.005_600_sameinit"`
- `VGGT_CACHE_OUT_DIR="$NEW_CACHE_DIR"`

Expected:
- TB `vggt_feat/active` 应接近 `meta.json` 的 `phi_size[0] * phi_size[1]`（在 compute steps）

**Step 4: Write results note + commit**

Create `notes/openproposal_phase6_fg_realign_phase4.md` with:
- run list + cache meta summary（phi_size、gating）
- baseline vs treatments 指标表（含新 evaluator 的 `psnr_fg_area/lpips_fg_comp`）
- 是否满足 guardrail 与下一步建议（继续/止损）

Commit:
```bash
git add notes/openproposal_phase6_fg_realign_phase4.md
git commit -m "docs(notes): Phase6 Phase4 fg realign follow-up results"
```

---

### Task 6: Update Diagnosis Docs (optional but recommended)

**Files:**
- Modify: `docs/reviews/2026-03-05/expert-diagnosis-pack_phase3-4.md`
- Modify: `docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md`

**Step 1: Append a short “Follow-up outcome” section**

Include:
- 哪些 ablation 改变了方向/是否改善 fg
- 如果仍失败，更新 failure boundary（例如“ds2 + nogate 仍 fg 退化”）

**Step 2: Commit**

```bash
git add docs/reviews/2026-03-05/expert-diagnosis-pack_phase3-4.md docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md
git commit -m "docs(review): append Phase6 fg realign follow-up outcomes"
```
