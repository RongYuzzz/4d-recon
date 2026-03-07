# OpenProposal Phase 7 — ROI Alignment MVEs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用 1–2 个最小验证实验（MVE）判定：我们是否能在 THUman4.0 s00 上**稳定**做到 `psnr_fg ↑` 且 `lpips_fg ↓`（silhouette ROI），并满足 guardrail `ΔtLPIPS <= +0.01`。

**Architecture:** 基于 Phase6 的“可审计”工具链（mask scaling、fg evaluator 的 `psnr_fg_area/lpips_fg_comp`），先做**不改代码**的 weak-fusion schedule MVE（early-only），再做**小改代码但信息量最大**的 feature loss “silhouette-gated (oracle)” MVE（实现 `gating='cue'` 为稠密 silhouette gate）。可选补充：增加 boundary-band 指标，专门量化轮廓边界质量。

**Tech Stack:** Bash, Python, pytest, numpy, Pillow, torch, FreeTimeGsVanilla (`third_party/FreeTimeGsVanilla/.venv`), THUman4.0 adapter outputs.

---

## Preconditions / Non-goals

- **local-eval only**：禁止把 `data/`、`outputs/` 加入 git（含 masks、renders、cache、ckpt、视频）。只提交 `scripts/`、`docs/`、`notes/`。
- `outputs/` **append-only**：任何新实验必须用新的 `RESULT_DIR`（不要覆盖旧目录）。
- 本计划假设你已经完成并冻结了 baseline anchor：
  - `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats/test_step0599.json`
- 本计划建议直接从 Phase6 分支继续（因为它已包含：`scripts/scale_pseudo_masks_npz.py`、`eval_masked_metrics.py` 的 `psnr_fg_area/lpips_fg_comp` 等对照口径）。

---

### Task 0: Create Worktree + Gate Checks

**Files:**
- Create: *(none)*
- Modify: *(none)*
- Test: *(none)*

**Step 1: Create an isolated worktree off Phase6 branch**

Run:
```bash
git rev-parse --verify owner-b-20260305-fg-realign >/dev/null
git worktree add -b owner-b-20260305-phase7-roi-mve \
  .worktrees/owner-b-20260305-phase7-roi-mve \
  owner-b-20260305-fg-realign
cd .worktrees/owner-b-20260305-phase7-roi-mve
```

Expected: 进入新 worktree，`git status` 干净。

**Step 2: Run unit tests**

Run: `pytest -q`  
Expected: PASS

**Step 2.5: VGGT offline preflight (avoid mid-run download stalls)**

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

Expected: 打印 `ok`。  
If FAIL（本机没有完整缓存）：临时设 `HF_HUB_OFFLINE=0` 下载一次，再切回 `1`。

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
export PLANB_INIT_NPZ
```

Expected: 打印存在的 `init_points_planb_step*.npz` 路径与 sha256（后续所有 treatment 必须一致）。

---

### Task 1 (Optional but Recommended): Add Boundary-Band ROI Metrics

> 目的：silhouette 质量很多时候主要体现在边界 3–5px 的锯齿/漏光/抖动；在已有 `psnr_fg_area/lpips_fg_comp` 的基础上补一条更“对症”的指标，便于专家诊断。

**Files:**
- Modify: `scripts/eval_masked_metrics.py`
- Test: `scripts/tests/test_eval_masked_metrics_contract.py`

**Step 1: Update contract test (RED)**

Modify `scripts/tests/test_eval_masked_metrics_contract.py`：在 `cmd` 里增加 `--boundary_band_px 3`，并把断言 keys 增加：
```python
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir",
            str(data_dir),
            "--result_dir",
            str(result_dir),
            "--stage",
            "test",
            "--step",
            "599",
            "--mask_source",
            "dataset",
            "--bbox_margin_px",
            "4",
            "--lpips_backend",
            "dummy",
            "--boundary_band_px",
            "3",
        ]

        for key in (
            # ... existing keys ...
            "psnr_bd_area",
            "lpips_bd_comp",
            "boundary_band_px",
        ):
            assert key in obj, f"missing key: {key}"
        assert obj["boundary_band_px"] == 3
```

**Step 2: Run the test (should FAIL)**

Run: `pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q`  
Expected: FAIL（未知参数 `--boundary_band_px` 或缺 key）。

**Step 3: Implement boundary band in evaluator (GREEN)**

Modify `scripts/eval_masked_metrics.py`：

1) `parse_args()` 增加参数：
```python
    ap.add_argument(
        "--boundary_band_px",
        type=int,
        default=0,
        help="If >0, also evaluate a boundary band around GT mask with this radius in pixels.",
    )
```

2) 增加 helper（放在文件顶部附近即可）：
```python
def _boundary_band_keep(mask01: np.ndarray, thr: float, radius_px: int) -> np.ndarray:
    if radius_px <= 0:
        return np.zeros_like(mask01, dtype=np.float32)
    from PIL import ImageFilter  # noqa: PLC0415

    m = (mask01 > float(thr)).astype(np.uint8) * 255
    img = Image.fromarray(m, mode="L")
    k = int(radius_px) * 2 + 1
    dil = img.filter(ImageFilter.MaxFilter(size=k))
    ero = img.filter(ImageFilter.MinFilter(size=k))
    dil01 = (np.asarray(dil, dtype=np.uint8) > 127)
    ero01 = (np.asarray(ero, dtype=np.uint8) > 127)
    band = np.logical_and(dil01, np.logical_not(ero01))
    return band.astype(np.float32)
```

3) 在每帧循环中，计算 band 指标（依赖你 Phase6 里已有的 `keep_full`、`_psnr_mask_area`、`pred_comp` 写法）：
```python
        if int(args.boundary_band_px) > 0:
            band_full = _boundary_band_keep(mask01, thr=float(args.mask_thr), radius_px=int(args.boundary_band_px))
            keep_bd = band_full[..., None]
            bbox_bd = _bbox_from_mask(band_full, thr=0.5, margin=margin)
            if bbox_bd is not None:
                gt_bd = gt[bbox_bd.y0:bbox_bd.y1, bbox_bd.x0:bbox_bd.x1].copy()
                pred_bd = pred[bbox_bd.y0:bbox_bd.y1, bbox_bd.x0:bbox_bd.x1].copy()
                keep_bd_crop = keep_bd[bbox_bd.y0:bbox_bd.y1, bbox_bd.x0:bbox_bd.x1]
                gt_bd *= keep_bd_crop
                pred_bd *= keep_bd_crop
                psnr_bd_area_list.append(_psnr_mask_area(pred_bd, gt_bd, keep_bd_crop))
                pred_bd_comp = pred * keep_bd + gt * (1.0 - keep_bd)
                value_lpips_bd_comp = lpips_fn(pred_bd_comp, gt)
                if value_lpips_bd_comp is not None:
                    lpips_bd_comp_list.append(float(value_lpips_bd_comp))
```
同时在循环外初始化 `psnr_bd_area_list/lpips_bd_comp_list`。

4) 输出 JSON 追加字段：
```python
        "boundary_band_px": int(args.boundary_band_px),
        "psnr_bd_area": float(np.nanmean(psnr_bd_area_list)) if psnr_bd_area_list else float("nan"),
        "lpips_bd_comp": float(np.mean(lpips_bd_comp_list)) if lpips_bd_comp_list else float("nan"),
```

**Step 4: Run tests**

Run:
```bash
pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q
pytest -q
```

Expected: PASS

**Step 5: Commit**

Run:
```bash
git add scripts/eval_masked_metrics.py scripts/tests/test_eval_masked_metrics_contract.py
git commit -m "feat(metrics): add boundary-band ROI metrics for silhouette analysis"
```

> NOTE: 如果你跳过本 Task，后续评测命令里要移除 `--boundary_band_px ...` 参数（否则会报“未知参数”）。

---

### Task 2: Prepare Scaled Masks for Weak-Fusion MVE

**Files:**
- Create: *(none)*
- Modify: *(none)*
- Test: *(none)*

**Step 1: Pick the Phase2/Phase6 mask source NPZ**

Run:
```bash
SRC_NPZ="outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz"
test -f "$SRC_NPZ"
```

Expected: 文件存在（若你要换来源，在 note 里写清楚新路径）。

**Step 2: Produce dynamic_scaled + static_from_dynamic_scaled**

Run:
```bash
OUT_DIR="outputs/cue_mining/_phase7_scaled/openproposal_thuman4_s00_diff_q0.950_ds4_med3_q0.99"
mkdir -p "$OUT_DIR"

python3 scripts/scale_pseudo_masks_npz.py \
  --in_npz "$SRC_NPZ" \
  --out_npz "$OUT_DIR/pseudo_masks_dynamic_scaled_q0.99.npz" \
  --quantile 0.99 \
  --mode dynamic_scaled \
  --overwrite

python3 scripts/scale_pseudo_masks_npz.py \
  --in_npz "$SRC_NPZ" \
  --out_npz "$OUT_DIR/pseudo_masks_static_from_dynamic_scaled_q0.99.npz" \
  --quantile 0.99 \
  --mode static_from_dynamic_scaled \
  --overwrite
```

Expected:
- 两个输出 npz 都存在
- 后续 weak-fusion treatment 用这两份（不再直接用原始 `pseudo_masks.npz`）。

---

### Task 3: MVE-1 (No Code Change): Weak-Fusion Early-Only Schedule

**Files:**
- Create: `notes/openproposal_phase7_mve1_weak_earlyonly.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: Launch treatment run (static_from_dynamic_scaled + end_step=200)**

Run:
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
TRAINER_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"

DATA_DIR="data/thuman4_subject00_8cam60f"
GPU=0
MAX_STEPS=600
END_STEP=200
PSEUDO_MASK_WEIGHT=0.8

PSEUDO_MASK_NPZ="outputs/cue_mining/_phase7_scaled/openproposal_thuman4_s00_diff_q0.950_ds4_med3_q0.99/pseudo_masks_static_from_dynamic_scaled_q0.99.npz"
RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w${PSEUDO_MASK_WEIGHT}_end${END_STEP}_600_r1"

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
  --pseudo-mask-end-step "$END_STEP" \
  --eval-on-test
```

Expected:
- `.../stats/test_step0599.json` 存在
- `cfg.yml` 中 `init_npz_path` 与 baseline 一致（fairness gate）。

**Step 2: Run masked eval (dataset masks)**

Run:
```bash
"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir "$RESULT_DIR" \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend auto \
  --boundary_band_px 3
```

If you skipped Task 1, run the same command but **without** `--boundary_band_px 3`.

Expected: `.../stats_masked/test_step0599.json` 存在，包含 `psnr_fg/lpips_fg/psnr_fg_area/lpips_fg_comp`（以及可选的 `psnr_bd_area/lpips_bd_comp`）。

**Step 3: Guardrail check (ΔtLPIPS vs baseline)**

Run:
```bash
TREAT_DIR="$RESULT_DIR" python3 - <<'PY'
import json
import os
from pathlib import Path

def load(p: str) -> dict:
  return json.loads(Path(p).read_text(encoding="utf-8"))

base = load("outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats/test_step0599.json")
treat_dir = Path(os.environ["TREAT_DIR"])
treat = load(str(treat_dir / "stats" / "test_step0599.json"))

bt = float(base.get("tlpips"))
tt = float(treat.get("tlpips"))
print("baseline_tlpips=", bt)
print("treat_tlpips   =", tt)
print("delta_tlpips   =", (tt - bt))
PY
```

Expected: `delta_tlpips <= +0.01`（PASS）。

**Step 4: Write a 1-page note and commit it**

Create `notes/openproposal_phase7_mve1_weak_earlyonly.md`，至少包含：
- baseline / treatment 的目录与 `init_npz_path` 一致性证据
- `psnr/lpips/tlpips` 与 `psnr_fg/lpips_fg/psnr_fg_area/lpips_fg_comp`（可选：boundary-band）
- 结论：是否满足 “`psnr_fg↑ & lpips_fg↓` 且 ΔtLPIPS<=+0.01”
- 建议写入明确的“通过阈值”（便于外部专家快速判断），例如：
  - `Δpsnr_fg >= +0.2 dB` 且 `Δlpips_fg <= -0.001`

Run:
```bash
git add notes/openproposal_phase7_mve1_weak_earlyonly.md
git commit -m "docs(notes): Phase7 MVE1 weak-fusion early-only results"
```

**Step 5 (Conditional): If MVE-1 is “close but trade-off”, run END_STEP=300**

Only if Step 4 shows “FG 有改善但全图代价偏大”，再跑一条：
- `END_STEP=300`，其它不变，`RESULT_DIR` 改名包含 `end300`
- 重复 Step 2–4

---

### Task 4: Implement Feature-Loss Cue Gating as Dense Silhouette Gate (Oracle MVE)

> 目的：一次性验证 Phase4 的关键假设：feature loss 是否因为 ROI 没对齐才失败。若 “silhouette-gated” 仍无法让 fg 变好，则 feature loss 路线可止损（至少对这个 ROI 目标）。

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Test: `scripts/tests/test_vggt_feat_cue_gate_downsample.py`

**Step 1: Write failing test (RED)**

Create `scripts/tests/test_vggt_feat_cue_gate_downsample.py`:
```python
#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAINER = (
    REPO_ROOT
    / "third_party"
    / "FreeTimeGsVanilla"
    / "src"
    / "simple_trainer_freetime_4d_pure_relocation.py"
)
HELPER_NAME = "_vggt_feat_downsample_dense_gate"


def _load_helper() -> object:
    src = TRAINER.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(TRAINER))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == HELPER_NAME:
            fn_src = ast.get_source_segment(src, node)
            if not fn_src:
                raise AssertionError(f"failed to extract source for {HELPER_NAME}")
            ns: dict[str, object] = {"torch": torch, "F": F, "Tensor": torch.Tensor}
            exec("from __future__ import annotations\n" + fn_src, ns)  # noqa: S102
            return ns[HELPER_NAME]
    raise AssertionError(f"missing helper in trainer: {HELPER_NAME}")


def run_test() -> None:
    helper = _load_helper()
    g = torch.Generator(device="cpu")
    g.manual_seed(20260305)
    mask = (torch.rand((2, 1, 32, 40), generator=g) > 0.7).float()
    out = helper(mask, hf=8, wf=9)
    assert tuple(out.shape) == (2, 1, 8, 9)
    assert float(out.min()) >= 0.0
    assert float(out.max()) <= 1.0


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: vggt dense gate downsample helper exists and is bounded")
```

**Step 2: Run the test (should FAIL)**

Run: `pytest -q scripts/tests/test_vggt_feat_cue_gate_downsample.py -q`  
Expected: FAIL（helper 不存在）。

**Step 3: Implement cue gating in trainer (GREEN)**

Modify `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`：

1) 在 module-level 增加 helper（放在 `_top_p_mask` 附近即可）：
```python
def _vggt_feat_downsample_dense_gate(mask_b1hw: Tensor, hf: int, wf: int) -> Tensor:
    """Downsample a dense gate mask [B,1,H,W] into feature grid space [B,1,hf,wf]."""
    if mask_b1hw.dim() != 4 or mask_b1hw.shape[1] != 1:
        raise ValueError(f"mask_b1hw must be [B,1,H,W], got {tuple(mask_b1hw.shape)}")
    gate = F.interpolate(mask_b1hw.float(), size=(int(hf), int(wf)), mode="bilinear", align_corners=False)
    return gate.clamp(0.0, 1.0)
```

2) 在 `FreeTime4DRunner.__init__` 中初始化一个小缓存（避免每步反复读盘）：
```python
        self._vggt_feat_cue_gate_cache: dict[tuple[int, int], torch.Tensor] = {}
        self._vggt_feat_warned_missing_cue_mask = False
```

3) 增加一个方法（放在 `_get_pseudo_mask_batch` 附近即可）：
```python
    def _get_vggt_feat_cue_gate_batch(
        self,
        frame_idx: Union[Tensor, np.ndarray, List[int]],
        camera_idx: Union[Tensor, np.ndarray, List[int]],
        hf: int,
        wf: int,
    ) -> Optional[Tensor]:
        """Load dataset silhouette masks and resize to phi grid as dense gate [B,1,hf,wf]."""
        cfg = self.cfg
        frame_idx_t = torch.as_tensor(frame_idx, dtype=torch.long, device="cpu").view(-1)
        camera_idx_t = torch.as_tensor(camera_idx, dtype=torch.long, device="cpu").view(-1)
        out: List[torch.Tensor] = []
        for t_raw, cam_raw in zip(frame_idx_t.tolist(), camera_idx_t.tolist()):
            t_local = int(t_raw) - int(cfg.start_frame)
            cam_name = str(self.parser.camera_names[int(cam_raw)])
            key = (t_local, int(cam_raw))
            cached = self._vggt_feat_cue_gate_cache.get(key)
            if cached is None:
                mask_path = os.path.join(cfg.data_dir, "masks", cam_name, f"{t_local:06d}.png")
                if not os.path.exists(mask_path):
                    if not self._vggt_feat_warned_missing_cue_mask:
                        print(f"[VGGTFeat][WARN] missing cue mask for gating='cue': {mask_path}. Falling back to none.")
                        self._vggt_feat_warned_missing_cue_mask = True
                    return None
                from PIL import Image  # noqa: PLC0415
                img = Image.open(mask_path).convert("L").resize((int(wf), int(hf)), resample=Image.Resampling.BILINEAR)
                arr = (np.asarray(img, dtype=np.float32) / 255.0).reshape(1, int(hf), int(wf))
                cached = torch.from_numpy(arr)  # [1,hf,wf] on CPU
                self._vggt_feat_cue_gate_cache[key] = cached
            out.append(cached)
        gate = torch.stack(out, dim=0)  # [B,1,hf,wf] on CPU
        return gate.to(device=self.device, dtype=torch.float32).clamp(0.0, 1.0)
```

4) 在 `_compute_vggt_feature_loss` 的 gating 分支里，实现 `gating='cue'`（替换原来的 warn）：
```python
        gating_mode = str(cfg.vggt_feat_gating).strip().lower()
        if gating_mode == "cue":
            gate_use = self._get_vggt_feat_cue_gate_batch(
                frame_idx=data["frame_idx"],
                camera_idx=data["camera_idx"],
                hf=int(self.vggt_feat_phi_size[0]),
                wf=int(self.vggt_feat_phi_size[1]),
            )
            if gate_use is not None:
                weight_map = gate_use if weight_map is None else (weight_map * gate_use)
```
并保留 framediff gating 的逻辑不变（允许后续做 framediff*cue 的交集，但本 MVE 先只用 cue）。

**Step 4: Run tests**

Run:
```bash
pytest -q scripts/tests/test_vggt_feat_cue_gate_downsample.py -q
pytest -q
```

Expected: PASS

**Step 5: Commit**

Run:
```bash
git add third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py \
  scripts/tests/test_vggt_feat_cue_gate_downsample.py
git commit -m "feat(vggt): implement dense silhouette cue gating for feature loss"
```

---

### Task 5: MVE-2 (Code Change): Feature Loss with Silhouette Cue Gating

**Files:**
- Create: `notes/openproposal_phase7_mve2_feat_cue_gate.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: Launch treatment run (VGGT_FEAT_GATING=cue)**

Run:
```bash
REPO_ROOT="$(pwd)"

# CRITICAL: pin a THUman cache tag (do NOT accidentally reuse selfcap cache defaults).
VGGT_CACHE_TAG="${VGGT_CACHE_TAG:-openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10}"
VGGT_CACHE_OUT_DIR="${VGGT_CACHE_OUT_DIR:-$REPO_ROOT/outputs/vggt_cache/$VGGT_CACHE_TAG}"

DATA_DIR="data/thuman4_subject00_8cam60f" \
RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_cuegate_lam0.005_600_sameinit_r1" \
GPU=1 MAX_STEPS=600 \
VENV_PYTHON="${VENV_PYTHON:-$(pwd)/third_party/FreeTimeGsVanilla/.venv/bin/python}" \
PLANB_INIT_NPZ="$PLANB_INIT_NPZ" \
VGGT_MODEL_ID="${VGGT_MODEL_ID:-facebook/VGGT-1B}" \
VGGT_MODEL_CACHE_DIR="${VGGT_MODEL_CACHE_DIR:-/root/autodl-tmp/cache/vggt}" \
VGGT_CACHE_TAG="$VGGT_CACHE_TAG" \
VGGT_CACHE_OUT_DIR="$VGGT_CACHE_OUT_DIR" \
VGGT_FEAT_PHI_NAME="token_proj" \
VGGT_FEAT_LOSS_TYPE="cosine" \
LAMBDA_VGGT_FEAT="0.005" \
VGGT_FEAT_START_STEP="0" \
VGGT_FEAT_RAMP_STEPS="400" \
VGGT_FEAT_EVERY="8" \
VGGT_FEAT_GATING="cue" \
VGGT_FEAT_GATING_TOP_P="0.10" \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Expected:
- `.../stats/test_step0599.json` 存在
- TB scalars 中 `vggt_feat/active` 非 0（至少在 steps 0/200/400 出现）。

**Step 2: Run masked eval**

Run:
```bash
VENV_PYTHON="${VENV_PYTHON:-$(pwd)/third_party/FreeTimeGsVanilla/.venv/bin/python}"
"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_cuegate_lam0.005_600_sameinit_r1 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend auto \
  --boundary_band_px 3
```

If you skipped Task 1, run the same command but **without** `--boundary_band_px 3`.

Expected: `stats_masked/test_step0599.json` 存在。

**Step 3: Fairness gate (same init)**

Run:
```bash
echo "[baseline init_npz_path]" && rg -n "^init_npz_path:" outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/cfg.yml
echo "[treat init_npz_path]" && rg -n "^init_npz_path:" outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_cuegate_lam0.005_600_sameinit_r1/cfg.yml
```

Expected: 两边路径完全一致；否则该 run 视为 confounded（必须重跑）。

**Step 4: Write a 1-page note and commit it**

Create `notes/openproposal_phase7_mve2_feat_cue_gate.md`，至少包含：
- baseline vs treatment 的全图/fg 指标对照（含 `psnr_fg_area/lpips_fg_comp`，可选 boundary-band）
- `ΔtLPIPS` guardrail（vs baseline）
- 结论：oracle gating 是否让 fg 指标“同时变好”
- 建议写入明确的“通过阈值”（便于外部专家快速判断），例如：
  - `Δpsnr_fg >= +0.2 dB` 且 `Δlpips_fg <= -0.003`

Run:
```bash
git add notes/openproposal_phase7_mve2_feat_cue_gate.md
git commit -m "docs(notes): Phase7 MVE2 feature loss cue-gating results"
```

---

### Task 6: Update Expert Dossier + Stop/Go Decision

**Files:**
- Modify: `docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md`
- Modify: `docs/reviews/2026-03-05/expert-diagnosis-dossier_phase3-4-6.md`

**Step 1: Append Phase7 outcomes (2–3 paragraphs each MVE)**

在两份文档末尾追加：
- MVE-1（weak early-only）的配置、指标、结论（是否通过核心目标）
- MVE-2（cue-gated feature loss）的配置、指标、结论（是否通过核心目标）
- 明确写下 Stop/Go：
  - 若两条都失败：建议止损（把结论写死：weak/feat 都更像 trade-off 调参，不能稳定提升 silhouette ROI）
  - 若任一成功：进入下一阶段（只围绕成功路线做小范围 schedule/权重扫描）

**Step 2: Run docs-only checks**

Run:
```bash
pytest -q
rg -n "TODO_" docs/reviews/2026-03-05 || true
```

Expected: PASS（允许 `rg TODO_` 有输出，但必须是“明确标注可选项”的 TODO，不得影响复核）。

**Step 3: Commit**

Run:
```bash
git add docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md \
  docs/reviews/2026-03-05/expert-diagnosis-dossier_phase3-4-6.md
git commit -m "docs(review): append Phase7 ROI-alignment MVE outcomes"
```
