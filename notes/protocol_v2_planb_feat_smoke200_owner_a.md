# Protocol v2 Plan-B + VGGT feature metric smoke200 (Owner A)

## Run command (exact)

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_warm100 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=100 \
VGGT_FEAT_RAMP_STEPS=100 \
VGGT_FEAT_EVERY=8 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

## Artifacts

- Result dir: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100/`
- Stats:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100/stats/val_step0199.json`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100/stats/test_step0199.json`
- Video:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100/videos/traj_4d_step199.mp4`

## Stability audit

- Training completed to step 199 (max 200), no NaN / no loss explosion.
- Final eval summary:
  - val: PSNR `13.5344`, SSIM `0.3000`, LPIPS `0.5536`
  - test: PSNR `12.8345`, SSIM `0.3106`, LPIPS `0.5802`, tLPIPS `0.0337`

## Metric sanity vs references

References:
- `planb_init_smoke200` (protocol_v1)
- `baseline_smoke200_planb_window` (protocol_v1)

Compared to `planb_init_smoke200`:
- val: ΔPSNR `-0.0042`, ΔSSIM `-0.00013`, ΔLPIPS `+0.00091`
- test: ΔPSNR `-0.0038`, ΔSSIM `-0.00041`, ΔLPIPS `+0.00067`, ΔtLPIPS `+0.00019`

Compared to `baseline_smoke200_planb_window`:
- val: ΔPSNR `+0.1759`, ΔSSIM `+0.00228`, ΔLPIPS `-0.0500`
- test: ΔPSNR `+0.1995`, ΔSSIM `+0.00400`, ΔLPIPS `-0.0495`, ΔtLPIPS `-0.0540`

Conclusion: smoke200 metrics are numerically sane. This run is ~par with `planb_init_smoke200` and clearly better than `baseline_smoke200_planb_window`.

## Qualitative quick check (traj_4d_step199)

- vs `planb_init_smoke200`: overall look is very close; no obvious collapse/flicker increase.
- vs `baseline_smoke200_planb_window`: fewer temporal artifacts than baseline; motion continuity remains acceptable.

## Optional second smoke (lambda=0.01)

- Executed with:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.01_warm100 \
LAMBDA_VGGT_FEAT=0.01 \
VGGT_FEAT_START_STEP=100 \
VGGT_FEAT_RAMP_STEPS=100 \
VGGT_FEAT_EVERY=8 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

- Result dir: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.01_warm100/`
- Final eval:
  - val: PSNR `13.5242`, SSIM `0.2997`, LPIPS `0.5527`
  - test: PSNR `12.8224`, SSIM `0.3102`, LPIPS `0.5801`, tLPIPS `0.0336`
- Relative to lambda=0.005:
  - val/test PSNR both lower (about `-0.010` to `-0.012`)
  - test SSIM lower (`-0.00036`)
  - LPIPS/tLPIPS near-tied (tiny changes)

Decision: keep `lambda=0.005` as preferred smoke setting for the full600 gate.

## Full600 gate justification (pre-run)

- smoke200 (`lambda=0.005`) is stable (no NaN / no explosion).
- smoke200 is defensible: near-parity vs `planb_init_smoke200`, clearly better than `baseline_smoke200_planb_window`.
- stoploss for full600: if final test `PSNR/LPIPS/tLPIPS` are all worse than `planb_init_600`, stop and do not iterate blindly.

## Full600 run (single run)

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=600 \
RESULT_TAG=planb_feat_v2_full600_lam0.005_warm100_ramp400 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=100 \
VGGT_FEAT_RAMP_STEPS=400 \
VGGT_FEAT_EVERY=8 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- result dir: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_warm100_ramp400/`
- stats:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_warm100_ramp400/stats/val_step0599.json`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_warm100_ramp400/stats/test_step0599.json`
- video:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_warm100_ramp400/videos/traj_4d_step599.mp4`

Final metrics (`step0599`):
- val: PSNR `19.5645`, SSIM `0.6778`, LPIPS `0.3775`
- test: PSNR `20.4106`, SSIM `0.7057`, LPIPS `0.3530`, tLPIPS `0.00741`

## Stoploss check vs `planb_init_600`

Reference `planb_init_600` test (`step0599`):
- PSNR `20.4488`, LPIPS `0.3497`, tLPIPS `0.00720`

Delta (`full600 - planb_init_600`, test):
- ΔPSNR `-0.0382` (worse)
- ΔLPIPS `+0.0033` (worse)
- ΔtLPIPS `+0.00022` (worse)

Result: hits the defined stoploss condition (`PSNR/LPIPS/tLPIPS` all worse vs `planb_init_600`).  
Action: stop here; no further blind iteration.

## Follow-up (2026-02-27): framediff gating trend check (smoke200 only)

Goal: try a **small, explainable** change to avoid full600 “all-worse” outcomes, without blind sweeps.

### Candidate 1: `VGGT_FEAT_GATING=framediff` (top-p aligned to cache meta)

Run:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.10_lam0.005_warm100 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=100 \
VGGT_FEAT_RAMP_STEPS=100 \
VGGT_FEAT_EVERY=8 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.10 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- result dir: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.10_lam0.005_warm100/`
- test stats: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.10_lam0.005_warm100/stats/test_step0199.json`

Final metrics (`step0199`):
- val: PSNR `13.5126`, SSIM `0.2995`, LPIPS `0.5535`
- test: PSNR `12.8155`, SSIM `0.3101`, LPIPS `0.5805`, tLPIPS `0.03377`

Delta vs `planb_init_smoke200` (test):
- ΔPSNR `-0.0228`, ΔSSIM `-0.00084`, ΔLPIPS `+0.00096`, ΔtLPIPS `+0.00025`  → mild but consistent regression

### Candidate 2: reduce lambda (single conservative point)

Run:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.10_lam0.002_warm100 \
LAMBDA_VGGT_FEAT=0.002 \
VGGT_FEAT_START_STEP=100 \
VGGT_FEAT_RAMP_STEPS=100 \
VGGT_FEAT_EVERY=8 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.10 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- result dir: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.10_lam0.002_warm100/`
- test stats: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.10_lam0.002_warm100/stats/test_step0199.json`

Delta vs `planb_init_smoke200` (test):
- ΔPSNR `-0.0102`, ΔSSIM `-0.00027`, ΔLPIPS `+0.00016`, ΔtLPIPS `+0.00041`  → smaller regression, but still all-worse

Decision:
- smoke200 gate did **not** show a “non-regressing” trend (still all-worse vs `planb_init_smoke200`), so we **do not** run a framediff-gated full600.

Failure analysis (short):
- framediff gating likely focuses feature loss on high-change regions where photometric alignment is hardest; even with reduced lambda the added constraint is not helping objective metrics on this dataset/setting.

---

## 2026-02-27 protocol_v2 next（Task0/Task1/Task2 追加审计）

Reference baseline（test@step0199）:
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json`
- PSNR `12.8382835388`, SSIM `0.3109734058`, LPIPS `0.5795553327`, tLPIPS `0.0335242674`

### Task0：lambda=0 sanity 对照（可比性检查）

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0_sanity \
LAMBDA_VGGT_FEAT=0 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifact:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0_sanity/stats/test_step0199.json`

Metrics（test@step0199）:
- PSNR `12.8409252167`, SSIM `0.3107084930`, LPIPS `0.5791982412`, tLPIPS `0.0336953215`

Delta vs `planb_init_smoke200`:
- ΔPSNR `+0.0026416779`
- ΔSSIM `-0.0002649128`
- ΔLPIPS `-0.0003570914`
- ΔtLPIPS `+0.0001710542`

判定：差异处于极小噪声量级，**可比性通过**（继续 Task1）。

### Task1.1：候选 A（晚开 + 降频）

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifact:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16/stats/test_step0199.json`

Metrics（test@step0199）:
- PSNR `12.8365163803`, SSIM `0.3107088208`, LPIPS `0.5793841481`, tLPIPS `0.0337754749`

Delta vs `planb_init_smoke200`:
- ΔPSNR `-0.0017671585`
- ΔSSIM `-0.0002645850`
- ΔLPIPS `-0.0001711845`
- ΔtLPIPS `+0.0002512075`

Gate 判定：
- 未出现 `PSNR↓ + LPIPS↑ + tLPIPS↑` 三项全劣化（LPIPS 略优），**通过 smoke gate（保留候选池）**。

### Task1.2：候选 B（稀疏 patch 采样）

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=100 \
VGGT_FEAT_RAMP_STEPS=100 \
VGGT_FEAT_EVERY=8 \
VGGT_FEAT_PATCH_K=4 \
VGGT_FEAT_PATCH_HW=3 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifact:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100/stats/test_step0199.json`

Metrics（test@step0199）:
- PSNR `12.8275718689`, SSIM `0.3104844689`, LPIPS `0.5800493956`, tLPIPS `0.0342545919`

Delta vs `planb_init_smoke200`:
- ΔPSNR `-0.0107116699`
- ΔSSIM `-0.0004889369`
- ΔLPIPS `+0.0004940629`
- ΔtLPIPS `+0.0007303245`

Gate 判定：
- 命中 `PSNR↓ + LPIPS↑ + tLPIPS↑` 三项全劣化，**不通过 smoke gate**。

Task1 结论（用于 Task2 触发）：
- 候选 A 通过 gate，候选 B 未通过。
- 满足“至少一个 smoke200 候选不全线退步”，可进入单次 full600（最多 1 次）。

### Task2：单次 full600（基于候选 A 外推）

选择理由（为何候选 A 更合理）：
- 其 smoke200 未出现三项全劣化，且 LPIPS 仍小幅优于 `planb_init_smoke200`；
- 采用“晚开 + 降频”可以减少早期几何/时序尚未稳定时的 feature 约束干扰。

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=600 \
RESULT_TAG=planb_feat_v2_full600_lam0.005_start300_ramp200_every16 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=300 \
VGGT_FEAT_RAMP_STEPS=200 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- Result dir: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/`
- Stats:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/stats/val_step0599.json`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/stats/test_step0599.json`

Metrics:
- val@step0599: PSNR `19.6280937195`, SSIM `0.6756199598`, LPIPS `0.3757396638`
- test@step0599: PSNR `20.5725364685`, SSIM `0.7057183981`, LPIPS `0.3515161574`, tLPIPS `0.0075643724`

Stoploss check vs `planb_init_600`（test@step0599）:
- Reference: PSNR `20.4488086700`, SSIM `0.7070096731`, LPIPS `0.3496737480`, tLPIPS `0.0071958611`
- Delta (`full600 - planb_init_600`):
  - ΔPSNR `+0.1237277985`
  - ΔSSIM `-0.0012912750`
  - ΔLPIPS `+0.0018424094`
  - ΔtLPIPS `+0.0003685113`
- 判定：**未触发止损**（不是 `PSNR↓ / LPIPS↑ / tLPIPS↑` 三项同时劣化）。

预算纪律收口：
- full600 已执行 1 次，达到本轮上限；后续不再新增 full600，除非有新的预算决议。

### Handoff to Owner B（可复制路径）

- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0_sanity/`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0_sanity/stats/test_step0199.json`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16/`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16/stats/test_step0199.json`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100/`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100/stats/test_step0199.json`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/stats/test_step0599.json`

---

## 2026-02-28 stage2-tradeoff 计划补充：C1/C2 smoke200（不新增 full600）

Reference baseline（test@step0199）:
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json`
- PSNR `12.8382835388`, SSIM `0.3109734058`, LPIPS `0.5795553327`, tLPIPS `0.0335242674`

### C1：仅改 λ（0.005 -> 0.002）

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.002_start150_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.002 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_USE_CONF=1 \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.002_start150_ramp50_every16/`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.002_start150_ramp50_every16/stats/test_step0199.json`

Metrics（test@step0199）:
- PSNR `12.8394651413`, SSIM `0.3108914793`, LPIPS `0.5797820687`, tLPIPS `0.0338456966`

Delta vs `planb_init_smoke200`:
- ΔPSNR `+0.0011816025`
- ΔSSIM `-0.0000819266`
- ΔLPIPS `+0.0002267361`
- ΔtLPIPS `+0.0003214292`

Gate 判定：
- 未命中 `PSNR↓ + LPIPS↑ + tLPIPS↑` 三项全劣化，**通过 gate**（但 tLPIPS 退步扩大，不是优先候选）。

### C2：仅改 conf（on -> off）

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_USE_CONF=0 \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf/`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf/stats/test_step0199.json`

Metrics（test@step0199）:
- PSNR `12.8384075165`, SSIM `0.3108756542`, LPIPS `0.5789281726`, tLPIPS `0.0335766487`

Delta vs `planb_init_smoke200`:
- ΔPSNR `+0.0001239777`
- ΔSSIM `-0.0000977516`
- ΔLPIPS `-0.0006271601`
- ΔtLPIPS `+0.0000523813`

Gate 判定：
- 未命中 `PSNR↓ + LPIPS↑ + tLPIPS↑` 三项全劣化，**通过 gate**。

### Decision（对应 Task4）

- 相比前一版 `lam0.005_start150_ramp50_every16`（ΔtLPIPS `+0.0002512075`），C2 将 tLPIPS 退步压缩到 `+0.0000523813`，且 LPIPS 仍有改善，属于“减轻 tLPIPS 退步”的趋势。
- 本计划纪律要求不直接追加 `full600`；建议向负责人申请 **1 次新增 full600 预算**，仅验证 C2（`VGGT_FEAT_USE_CONF=0`）是否能把 smoke 趋势外推到 full600。

### Handoff to B（stage2-tradeoff 增量清单）

- 新 smoke runs：
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.002_start150_ramp50_every16/`
    - `.../stats/test_step0199.json`
    - `.../videos/traj_4d_step199.mp4`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf/`
    - `.../stats/test_step0199.json`
    - `.../videos/traj_4d_step199.mp4`
- 新 export-only runs（planb_feat_v2_full600）：
  - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.075432/videos/traj_4d_step599.mp4`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau0.075432/videos/traj_4d_step599.mp4`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.139066/videos/traj_4d_step599.mp4`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau0.139066/videos/traj_4d_step599.mp4`
- 新定性对比视频（step599）：
  - `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
  - `outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_step599.mp4`
  - `outputs/qualitative/planb_vs_baseline/baseline_vs_planbfeat_full600_step599.mp4`
- 新增说明文档：
  - `notes/protocol_v2_stage2_tradeoff_qual.md`
  - `notes/velocity_stats_planb_feat_v2_full600_start300.md`
  - `notes/protocol_v2_static_dynamic_tau_planb_feat_v2_full600.md`

---

## 2026-02-28 C2(noconf) full600 预算闸门执行（Owner A / Task 0）

### Step 1：预算申请（已提交）

- 申请内容：新增 **1 次 full600**，仅用于验证 C2（`VGGT_FEAT_USE_CONF=0`）是否可把 smoke200 的趋势外推到 full600。
- 证据指针（最小集）：
  - C2 smoke：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf/stats/test_step0199.json`
  - baseline：`outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json`
  - 审计主文：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`（本文件）
- 关键 delta（test@step0199, C2 - baseline）：
  - ΔPSNR `+0.0001239777`
  - ΔSSIM `-0.0000977516`
  - ΔLPIPS `-0.0006271601`
  - ΔtLPIPS `+0.0000523813`

### Step 2：预算决议记录（是否批准/批准人/日期）

- 是否批准：**未批准**
- 批准人：**N/A（未形成新增预算决议）**
- 日期：**2026-02-28**
- 依据：
  - `docs/report_pack/2026-02-27-v2/README.md` 已记录“新增 `..._noconf full600` 预算未获批，停止新增 full600 sweep”；
  - 现行冻结纪律仍为新增 full600 预算 `N=0`（见 `docs/decisions/2026-02-26-planb-v26-freeze.md`）。

### Gate 结论与执行结果

- 按预算闸门规则：未获批不运行 `full600`，因此不创建  
  `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/`。
- 本轮收口：stage‑2 保持 **mixed trend + failure analysis** 口径，不新增 full600 sweep。
- Done Criteria 命中：`1) 预算未批准` 分支成立（已在审计 note 记录“不跑 full600”的决策与理由）。


## 2026-02-28 dual-gpu smoke trend：A1（framediff p=0.02）

Run tag: `planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16`

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.02 \
VGGT_CACHE_TAG=selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16/cfg.yml`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16/stats/test_step0199.json`
- `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/meta.json`（`framediff_top_p=0.02`）

Metrics（test@step0199）:
- PSNR `12.8370990753`
- SSIM `0.3108907044`
- LPIPS `0.5795375705`
- tLPIPS `0.0338274352`

Delta vs `planb_init_smoke200`:
- ΔPSNR `-0.0011844635`
- ΔSSIM `-0.0000827014`
- ΔLPIPS `-0.0000177622`
- ΔtLPIPS `+0.0003031678`

Gate 判定（规则：`PSNR↓ + LPIPS↑ + tLPIPS↑` 三项全劣化为 fail）:
- 结论：**gate pass**；非优先候选（tLPIPS 仍退步）。


## 2026-02-28 dual-gpu smoke trend：A2（framediff p=0.02）

Run tag: `planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16`

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=200 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.02 \
VGGT_CACHE_TAG=selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16/cfg.yml`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16/stats/test_step0199.json`

Metrics（test@step0199）:
- PSNR `12.8370590210`
- SSIM `0.3106554151`
- LPIPS `0.5797344446`
- tLPIPS `0.0337359235`

Delta vs `planb_init_smoke200`:
- ΔPSNR `-0.0012245178`
- ΔSSIM `-0.0003179908`
- ΔLPIPS `+0.0001791120`
- ΔtLPIPS `+0.0002116561`

Gate 判定（规则：`PSNR↓ + LPIPS↑ + tLPIPS↑` 三项全劣化为 fail）:
- 结论：**gate fail**；非优先候选（命中三项全劣化）。

审计口径补充：
- 该 run 使用 `MAX_STEPS=200` 且 `VGGT_FEAT_START_STEP=200`；训练循环最后一步为 `step=199`，不满足 `step >= start_step`，因此 **feature loss 实际不生效**。
- 该 run 仅作为“噪声/随机性参考”，不纳入 feature-loss 超参对比结论。


## 2026-02-28 dual-gpu smoke trend：A3（framediff p=0.02）

Run tag: `planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16`

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.002 \
VGGT_FEAT_START_STEP=200 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.02 \
VGGT_CACHE_TAG=selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16/cfg.yml`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16/stats/test_step0199.json`

Metrics（test@step0199）:
- PSNR `12.8393793106`
- SSIM `0.3108184934`
- LPIPS `0.5799948573`
- tLPIPS `0.0336236507`

Delta vs `planb_init_smoke200`:
- ΔPSNR `+0.0010957718`
- ΔSSIM `-0.0001549125`
- ΔLPIPS `+0.0004395247`
- ΔtLPIPS `+0.0000993833`

Gate 判定（规则：`PSNR↓ + LPIPS↑ + tLPIPS↑` 三项全劣化为 fail）:
- 结论：**gate pass**；非优先候选（tLPIPS/LPIPS 仍退步）。

审计口径补充：
- 该 run 使用 `MAX_STEPS=200` 且 `VGGT_FEAT_START_STEP=200`；训练循环最后一步为 `step=199`，不满足 `step >= start_step`，因此 **feature loss 实际不生效**。
- 该 run 仅作为“噪声/随机性参考”，不纳入 feature-loss 超参对比结论。

### Handoff to Owner B（2026-02-28，dual-gpu smoke trend 增量）

新增 runs（均为 smoke200 / GPU0）：
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16/`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16/stats/test_step0199.json`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16/`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16/stats/test_step0199.json`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16/`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16/stats/test_step0199.json`

A 侧审计真源：
- `notes/protocol_v2_planb_feat_smoke200_owner_a.md`（本文件）

收口结论（用于 scoreboard 口径）：
- A1: gate pass（LPIPS 改善，但 tLPIPS 退步）
- A2: gate fail（命中 `PSNR↓ + LPIPS↑ + tLPIPS↑`）
- A3: gate pass（PSNR 小幅改善，但 LPIPS/tLPIPS 退步）
- 口径修正：A2/A3 因 `VGGT_FEAT_START_STEP(200) >= MAX_STEPS(200)` 导致 feature loss 未生效，仅作为噪声参考，不纳入 feature-loss 超参对比。
- 本轮未出现“ΔtLPIPS ≤ 0 且 ΔLPIPS ≤ 0”的同一候选，暂不触发新增 full600 预算讨论。

### Owner B -> Owner A Sync（2026-02-28，GPU1 seed-noise）

新增 B 侧 smoke200 runs（GPU1）：
- `planb_feat_v2_smoke200_lam0_sanity_s42_gpu1`
- `planb_feat_v2_smoke200_lam0_sanity_s43_gpu1`
- `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s42_gpu1`
- `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s43_gpu1`
- `planb_feat_v2_smoke200_lam0.005_start200_ramp50_every16_s42_gpu1`
- `planb_feat_v2_smoke200_lam0.002_start200_ramp50_every16_s42_gpu1`

tLPIPS seed 噪声带（test@step199, vs `planb_init_smoke200` 口径）：
- `|B1-B2| = 0.000631`
- `|B3-B4| = 0.000685`
- 建议阈值：可置信改善至少 `> 0.001371`（2x 噪声带）

口径同步：
- 在该阈值以下的 `tLPIPS` 变化优先视为噪声，不作为“稳定改善”证据。
- 当前未满足“同一候选在 >=2 seeds 同时 `ΔtLPIPS <= 0` 且 `ΔLPIPS <= 0`”触发条件，不建议追加 full600 预算。

## 2026-02-28 protocol_v2 gpu-followup：Task3 optional（seed=44, smoke200）

Run tag:
- `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0`

Command:

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 SEED=44 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=none \
VGGT_FEAT_USE_CONF=0 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0/cfg.yml`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0/stats/test_step0199.json`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0/videos/traj_4d_step199.mp4`

Metrics（test@step0199）:
- PSNR `12.8402814865`
- SSIM `0.3112471700`
- LPIPS `0.5792871714`
- tLPIPS `0.0339146405`

Delta vs `planb_init_smoke200`:
- ΔPSNR `+0.001998`
- ΔSSIM `+0.000274`
- ΔLPIPS `-0.000268`
- ΔtLPIPS `+0.000390`

Noise-band check（from `docs/report_pack/2026-02-27-v2/README.md`）:
- tLPIPS 2x noise band threshold: `0.001371`
- 本次 `|ΔtLPIPS| = 0.000390 < 0.001371`，属于噪声带内变化。

结论（收口）：
- 单 seed44 仅表现为 `LPIPS` 轻微改善、`tLPIPS` 轻微退步且在噪声带内；**不构成稳定候选**。
- 继续维持“不新增 sweep / 不触发新增 full600 预算讨论”的收口口径。
