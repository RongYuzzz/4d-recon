# OpenProposal Phase 3 (THUman4.0) — Weak Supervision Closed-Loop Implementation Plan

> **Execution note:** 按 Task 顺序逐条执行；每个 Task 的 Expected 通过后再进入下一步。

**Goal:** 把 Phase 2 的 `pseudo_masks.npz` 真正用进训练闭环（weak reweight），并在 THUman 子集上给出 **可审计的 A/B 结论**（提升/退化都可以，但必须能复核、能解释）。

**Architecture:** 本 Phase 对齐总计划 `docs/plans/2026-03-02-align-opening-proposal-v1.md` 的 Phase 3（不得与其矛盾）。训练仍复用 FreeTimeGsVanilla 的 weak-fusion 参数（`--pseudo-mask-npz/--pseudo-mask-weight/--pseudo-mask-end-step`）。评测使用 Phase 1 的 `scripts/eval_masked_metrics.py` 做 **foreground-masked** 的 `psnr_fg/lpips_fg`（bbox+fill-black 口径）。所有数据/GT 仍 **local-eval only**。

**Tech Stack:** `scripts/run_train_planb_init_selfcap.sh`（baseline/确保 Plan‑B init 产物存在），直接调用 trainer 注入 weak-fusion（避免改 init 造成 A/B 混淆），新增一个轻量 mask 变换工具（invert），`scripts/eval_masked_metrics.py`，`pytest`。

**2026-03-04 状态更新（来自 Phase 2 QA，影响 Phase 3 默认选择）：**
- frozen `q0.995` 下 mask 在 `mask_thr=0.5(=128/255)` 口径非常稀疏，`miou_fg` 近似 0（health-check 不过关不代表 bug，但提示“阈值/语义不匹配”）。
- 在本 scene 上，`diff` 分支更像“落在人体/运动区域”；`vggt` 分支存在更明显的背景误激活（见 `notes/openproposal_phase2_vggt_pseudomask.md`）。
- **因此 Phase 3 默认用 `diff q0.950` 做 weak 注入**；`vggt` 路线留作可选对照（不作为默认 gate）。

---

### Task 0: Gate Check（确认 Phase 1/2 产物齐全）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 检查 Phase 1 anchor run 是否存在**

Run:
```bash
DATA_DIR="data/thuman4_subject00_8cam60f"
RUN_BASE="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f"
test -d "$DATA_DIR/images"
test -d "$DATA_DIR/masks"
test -d "$DATA_DIR/triangulation"
test -f "$RUN_BASE/planb_init_600/stats/test_step0599.json" || echo "[WARN] baseline planb_init_600 missing; will be generated in Task 2 Step 2"
```

Expected: 全部通过

**Step 2: 检查 Phase 2 的 pseudo masks 是否存在**

Run:
```bash
test -f outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3/pseudo_masks.npz
test -f outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3/pseudo_masks.npz

# Phase 3 默认注入用（Phase 2 止损回调产物；若不存在可回退到 q0.995）
test -f outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz || echo \"[WARN] diff q0.950 missing; fall back to diff q0.995\"
```

Expected: 两个文件都存在

---

### Task 1: 生成“weak-fusion 用”的 mask 变体（invert 动态性 → 静态性）

> 目的：trainer 的 weak fusion 默认把 mask 解释为 dynamicness，并执行 `w = 1 - alpha * mask`。  
> 若我们希望“相对强调前景/动态区域”，可把输入 mask 取反（≈ staticness），从而 **下调静态背景的权重**。

**Files:**
- Create: `scripts/invert_pseudo_masks_npz.py`
- Test: `scripts/tests/test_invert_pseudo_masks_npz_contract.py`

> 如果仓库中已存在上述两个文件且 `pytest -q scripts/tests/test_invert_pseudo_masks_npz_contract.py -q` 为 PASS，直接跳到 **Task 2**。

**Step 1: 写失败的 contract test**

新增 `scripts/tests/test_invert_pseudo_masks_npz_contract.py`：

```python
#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "invert_pseudo_masks_npz.py"


def test_invert_npz_preserves_contract_and_inverts_values() -> None:
    with tempfile.TemporaryDirectory(prefix="invert_npz_") as td:
        root = Path(td)
        in_npz = root / "in.npz"
        out_npz = root / "out.npz"

        masks = np.zeros((2, 3, 4, 5), dtype=np.uint8)
        masks[0, 0, 1, 2] = 255
        masks[1, 2, 3, 4] = 7
        np.savez_compressed(
            in_npz,
            masks=masks,
            camera_names=np.asarray(["02", "03", "09"]),
            frame_start=np.int32(0),
            num_frames=np.int32(2),
            mask_downscale=np.int32(4),
        )

        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--in_npz", str(in_npz), "--out_npz", str(out_npz), "--overwrite"],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"stdout:\\n{r.stdout}\\n\\nstderr:\\n{r.stderr}"
        assert out_npz.exists()

        obj = np.load(out_npz, allow_pickle=True)
        for key in ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale"):
            assert key in obj.files
        out = obj["masks"]
        assert out.dtype == np.uint8
        assert out.shape == masks.shape
        assert int(out[0, 0, 1, 2]) == 0  # 255 -> 0
        assert int(out[1, 2, 3, 4]) == 248  # 7 -> 248
```

**Step 2: 运行 test，确认失败**

Run: `pytest -q scripts/tests/test_invert_pseudo_masks_npz_contract.py -q`

Expected: FAIL

**Step 3: 实现脚本（最小功能）**

新增 `scripts/invert_pseudo_masks_npz.py`：

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def _fail(msg: str) -> None:
    raise SystemExit(f"[InvertPseudoMasks][ERROR] {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Invert masks in pseudo_masks.npz: m := 255 - m.")
    ap.add_argument("--in_npz", required=True)
    ap.add_argument("--out_npz", required=True)
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    in_npz = Path(args.in_npz).resolve()
    out_npz = Path(args.out_npz).resolve()
    if not in_npz.exists():
        _fail(f"missing in_npz: {in_npz}")
    if out_npz.exists() and not args.overwrite:
        _fail(f"out_npz exists (use --overwrite): {out_npz}")

    obj = np.load(in_npz, allow_pickle=True)
    for key in ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale"):
        if key not in obj.files:
            _fail(f"in_npz missing key: {key}")
    masks = np.asarray(obj["masks"])
    if masks.dtype != np.uint8:
        _fail(f"expected uint8 masks, got {masks.dtype}")
    inv = (255 - masks).astype(np.uint8, copy=False)

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_npz,
        masks=inv,
        camera_names=np.asarray(obj["camera_names"]),
        frame_start=np.int32(int(obj["frame_start"])),
        num_frames=np.int32(int(obj["num_frames"])),
        mask_downscale=np.int32(int(obj["mask_downscale"])),
        source_npz=str(in_npz),
        op=np.asarray(["invert_255_minus"], dtype=object),
    )
    print(f"[InvertPseudoMasks] wrote: {out_npz}")


if __name__ == "__main__":
    main()
```

**Step 4: 运行 test，确认通过**

Run: `pytest -q scripts/tests/test_invert_pseudo_masks_npz_contract.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/invert_pseudo_masks_npz.py scripts/tests/test_invert_pseudo_masks_npz_contract.py
git commit -m "feat(cue): add invert tool for pseudo_masks.npz"
```

---

### Task 2: 跑最小 A/B 训练（Plan-B vs Plan-B+Weak）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 生成 diff pseudo mask 的 inverted 版本（weak-fusion 用；Phase 3 默认）**

Run:
```bash
python3 scripts/invert_pseudo_masks_npz.py \
  --in_npz outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz \
  --out_npz outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz \
  --overwrite
```

Expected:
- 输出 `pseudo_masks_invert_staticness.npz` 存在

**Step 2: baseline（如果 Phase 1 已有 planb_init_600，可跳过）**

Run:
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

DATA_DIR="data/thuman4_subject00_8cam60f" \
RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600" \
GPU=0 MAX_STEPS=600 VENV_PYTHON="$VENV_PYTHON" \
bash scripts/run_train_planb_init_selfcap.sh "$RESULT_DIR"
```

Expected:
- `.../planb_init_600/stats/test_step0599.json`

**Step 3: treatment：Plan-B + weak fusion（使用 inverted mask）**

IMPORTANT（避免 A/B 混淆）：
- baseline 与 treatment 必须使用 **同一份 Plan‑B init NPZ**（`outputs/plan_b/<scene>/init_points_planb_step*.npz`），否则会把“初始化差异”误判为“weak supervision 差异”。

Run（建议先 timebox 到 600 steps）：
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
TRAINER_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"

DATA_DIR="data/thuman4_subject00_8cam60f"
GPU=0
MAX_STEPS=600
KEYFRAME_STEP=5

PLANB_INIT_NPZ="$REPO_ROOT/outputs/plan_b/$(basename "$DATA_DIR")/init_points_planb_step${KEYFRAME_STEP}.npz"
test -f "$PLANB_INIT_NPZ"

RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_diffmaskinv_q0.950_w0.8_600"
PSEUDO_MASK_NPZ="outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz"
# NOTE: Phase 2 显示 mask 值域较低；weight=0.3 基本接近 no-op。这里默认更强的 0.8 以确保 A/B 有信号。
PSEUDO_MASK_WEIGHT=0.8

CUDA_VISIBLE_DEVICES="$GPU" "$VENV_PYTHON" "$TRAINER_SCRIPT" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
  --result-dir "$RESULT_DIR" \
  --start-frame 0 \
  --end-frame 60 \
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
- `.../planb_init_weak_diffmaskinv_q0.950_w0.8_600/stats/test_step0599.json`

**Step 4 (可选，但推荐): control：weak path 但无 cue（zeros mask）**

Run:
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
TRAINER_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"

DATA_DIR="data/thuman4_subject00_8cam60f"
GPU=0
MAX_STEPS=600
KEYFRAME_STEP=5

PLANB_INIT_NPZ="$REPO_ROOT/outputs/plan_b/$(basename "$DATA_DIR")/init_points_planb_step${KEYFRAME_STEP}.npz"
test -f "$PLANB_INIT_NPZ"

# 0) build a constant "no-cue" pseudo mask (all zeros) for control
ZERO_MASK_DIR="outputs/cue_mining/openproposal_thuman4_s00_zeros_ds4"
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$ZERO_MASK_DIR" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend zeros \
  --temporal_smoothing median3 \
  --overwrite

# 1) control run
RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_zeros_600"
PSEUDO_MASK_NPZ="$ZERO_MASK_DIR/pseudo_masks.npz"
PSEUDO_MASK_WEIGHT=0.8

CUDA_VISIBLE_DEVICES="$GPU" "$VENV_PYTHON" "$TRAINER_SCRIPT" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
  --result-dir "$RESULT_DIR" \
  --start-frame 0 \
  --end-frame 60 \
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
- `.../planb_init_weak_zeros_600/stats/test_step0599.json`

---

### Task 3: 统一口径评测（psnr_fg/lpips_fg）+ 结果总结（必须可审计）

**Files:**
- Create: `notes/openproposal_phase3_weak_supervision_result.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: 对 baseline 跑 fg-masked eval（dataset masks）**

Run:
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend auto
```

Fallback（若本机没有 torch+lpips）：
```bash
python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend dummy
```

Expected:
- `.../planb_init_600/stats_masked/test_step0599.json` 存在，含 `psnr_fg/lpips_fg`

**Step 2: 对 weak run 跑同样的 masked eval**

Run（同上，替换 result_dir）：
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_diffmaskinv_q0.950_w0.8_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend auto
```

Fallback（若本机没有 torch+lpips）：
```bash
python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_diffmaskinv_q0.950_w0.8_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend dummy
```

**Step 3: 写结论文档（1 页即可）**

在 `notes/openproposal_phase3_weak_supervision_result.md` 中写清：
- 两条 run 的路径（baseline vs weak）
- 配置差异（pseudo_mask_npz / weight / end_step）
- full-frame 指标（来自 `stats/test_step0599.json`）
- fg-masked 指标（来自 `stats_masked/test_step0599.json`）
- 结论（提升/退化/无差异）+ 最可能原因（mask 质量/方向/权重/时序不稳等）

**Step 4: Commit（仅文档）**

```bash
git add notes/openproposal_phase3_weak_supervision_result.md
git commit -m "docs(notes): Phase3 weak supervision A/B result on THUman"
```

---

### Task 4: 定性对照视频（只渲染，不包含 GT）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 产出 side-by-side 视频（baseline vs weak）**

Run（示例；确保只用 renders，不要拼 GT）：
```bash
OUT_DIR="outputs/qualitative_local/openproposal_phase3"
mkdir -p "$OUT_DIR"

bash scripts/make_side_by_side_video.sh \
  --left "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/videos/traj_4d_step599.mp4" \
  --right "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_diffmaskinv_q0.950_w0.8_600/videos/traj_4d_step599.mp4" \
  --out_dir "$OUT_DIR" \
  --out_name "planb_vs_weak_step599.mp4" \
  --left_label "planb_init_600" \
  --right_label "weak_diffmaskinv_q0.950_w0.8_600" \
  --overwrite
```

Expected:
- `outputs/qualitative_local/openproposal_phase3/planb_vs_weak_step599.mp4` 可播放

**Step 2: 在 Phase3 结论文档里只写本机路径（不入证据链）**

---

## Exit Criteria（过闸门才能进入 Phase 4）

- 至少有一个可审计的对照结论：`planb_init_600` vs `planb_init_weak_*_600`（正/负/无差都可）
- `psnr_fg/lpips_fg` 口径在文档中写清（bbox margin=32, fill-black）
- 若指标未提升：必须给出 1–2 个最可能的归因点（并为 Phase 4 的排查提供线索）
