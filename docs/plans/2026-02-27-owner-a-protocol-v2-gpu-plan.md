# Owner A (GPU0) Protocol v2 GPU Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** On GPU0, produce the stage-2 (protocol_v2) “academic completeness” artifacts: static/dynamic split demo, VGGT feature cache, and a Plan‑B + VGGT feature-metric smoke run (with strict stoploss).

**Architecture:** Reuse the already-trained `planb_init_600` checkpoint for qualitative export-only demos. For semantic alignment, precompute a VGGT `gt_cache.npz` once, then run a single, timeboxed Plan‑B + feature-metric experiment (smoke200 → optional full600 only if justified).

**Tech Stack:** bash, Python, PyTorch, `third_party/FreeTimeGsVanilla` trainer, VGGT (`facebook/VGGT-1B`), existing runners under `scripts/`.

---

## Parallelism / Handoff (what B will consume)

As you complete tasks below, post the **final artifact paths** for B to reference in doc edits:
- static-only / dynamic-only videos: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_*_tau*/videos/traj_4d_step*.mp4`
- VGGT cache: `outputs/vggt_cache/*/gt_cache.npz` + `meta.json`
- smoke200 stats: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200*/stats/test_step0199.json`

## Task 0: Preconditions (GPU0 + data + ckpt)

**Files:**
- Read: `data/selfcap_bar_8cam60f/`
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt`
- Read: `third_party/FreeTimeGsVanilla/.venv/`

**Step 1: Verify GPU0 is visible**

Run: `nvidia-smi -L`  
Expected: GPU 0 exists and is the 32GB card you will use.

**Step 2: Verify venv + dataset + checkpoint exist**

Run:
```bash
ls -la third_party/FreeTimeGsVanilla/.venv/bin/python
ls -la data/selfcap_bar_8cam60f/images data/selfcap_bar_8cam60f/triangulation
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt
```
Expected: all paths exist.

---

## Task 1: Object removal demo (static-only / dynamic-only export from existing Plan‑B ckpt)

**Files:**
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt`
- Read: `outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- Create: `notes/velocity_stats_planb_init_600.md`
- Create: `notes/protocol_v2_static_dynamic_tau.md`
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau*/videos/`
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau*/videos/`

**Step 1: Export velocity stats (for τ selection)**

Run:
```bash
python3 scripts/export_velocity_stats.py \
  --init_npz_path outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz \
  --ckpt_path outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt \
  --out_md_path notes/velocity_stats_planb_init_600.md
```
Expected: `notes/velocity_stats_planb_init_600.md` exists and contains `p50/p90/p99` for `||v||` at step599.

**Step 2: Pick two τ candidates and do a quick A/B**

Rule of thumb:
- Start with `τ_low = p50(||v||)` and `τ_high = p90(||v||)` from the step599 section.
- Goal: `static_only` removes obvious movers but keeps most background structure.

Record your picks in `notes/protocol_v2_static_dynamic_tau.md` (include the stats row + the chosen τ).

**Step 3: Export static-only video (τ = τ_low)**

Run (edit `TAU` + `OUT`):
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
CKPT=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt
DATA=data/selfcap_bar_8cam60f

TAU=0.20
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau${TAU}

CUDA_VISIBLE_DEVICES=0 "$VENV_PYTHON" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA" \
  --result-dir "$OUT" \
  --start-frame 0 \
  --end-frame 60 \
  --ckpt-path "$CKPT" \
  --export-only \
  --render-traj-path fixed \
  --export-vel-filter static_only \
  --export-vel-threshold "$TAU"
```
Expected:
- Log contains `[Export] applied export_vel_filter: mode=static_only ...`
- Video exists at `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau*/videos/traj_4d_step*.mp4`

**Step 4: Export dynamic-only video (τ = same τ_low)**

Run (edit `OUT` only):
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
CKPT=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt
DATA=data/selfcap_bar_8cam60f

TAU=0.20
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau${TAU}

CUDA_VISIBLE_DEVICES=0 "$VENV_PYTHON" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA" \
  --result-dir "$OUT" \
  --start-frame 0 \
  --end-frame 60 \
  --ckpt-path "$CKPT" \
  --export-only \
  --render-traj-path fixed \
  --export-vel-filter dynamic_only \
  --export-vel-threshold "$TAU"
```
Expected: dynamic-only video exists under `.../videos/`.

**Step 5: Repeat Step 3–4 for τ_high and decide the final τ**

Acceptance:
- static-only: background is visibly “cleaner” (less ghosting / less moving people), and not overly “empty”.
- dynamic-only: main movers show up; if it’s mostly noise or mostly blank, τ is off.

Update `notes/protocol_v2_static_dynamic_tau.md` with:
- final chosen `τ_final`
- the two “final” video paths to use in talk/paper
- one known failure case (e.g., slow mover misclassified as static)

---

## Task 2: Precompute VGGT feature cache once (token_proj, full 60 frames × 8 cams)

**Files:**
- Read: `data/selfcap_bar_8cam60f/images/`
- Create: `outputs/vggt_cache/<tag>/gt_cache.npz`
- Create: `outputs/vggt_cache/<tag>/meta.json`

**Step 1: Sanity-check VGGT import in venv**

Run:
```bash
third_party/FreeTimeGsVanilla/.venv/bin/python -c "from vggt.models.vggt import VGGT; print('VGGT import ok')"
```
Expected: prints `VGGT import ok`. If it fails, install VGGT into the venv first (see `notes/vggt_setup.md`).

**Step 2: Precompute cache**

Run (tag can be adjusted, but keep it stable once used):
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
CUDA_VISIBLE_DEVICES=0 "$VENV_PYTHON" scripts/precompute_vggt_cache.py \
  --data_dir data/selfcap_bar_8cam60f \
  --out_dir outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4 \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 0 \
  --num_frames 60 \
  --backend vggt \
  --phi_name token_proj \
  --phi_downscale 4 \
  --token_layer_idx 17 \
  --token_proj_dim 32 \
  --token_proj_seed 20260225 \
  --vggt_model_id facebook/VGGT-1B \
  --vggt_mode crop
```
Expected:
- `outputs/vggt_cache/.../gt_cache.npz` exists
- `outputs/vggt_cache/.../meta.json` exists

---

## Task 3: Plan‑B + VGGT feature metric loss (smoke200 only, strict stoploss)

**Files:**
- Read: `scripts/run_train_planb_feature_loss_v2_selfcap.sh`
- Read: `outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- Read: `outputs/vggt_cache/.../gt_cache.npz` (from Task 2)
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200*/`
- Create: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`

**Step 1: Run smoke200**

Run:
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
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```
Expected:
- Result dir: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100/`
- Stats files exist: `.../stats/val_step0199.json`, `.../stats/test_step0199.json`
- Training is stable (no loss explosions / NaNs).

**Step 2: Write a short audit note**

Create/update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md` with:
- exact command (copy-paste)
- whether metrics look sane vs `planb_init_smoke200` / `baseline_smoke200`
- any obvious qualitative differences in `.../videos/traj_4d_step*.mp4`

**Step 3: Optional second smoke (only if Step 1 is stable but too weak)**

Try `LAMBDA_VGGT_FEAT=0.01` with the same warmup/ramp, and record in the same note.

---

## Task 4: Full600 gate (ONLY IF smoke looks defensible + budget explicitly approved)

**Files:**
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600*/`
- Update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`

**Step 1: Before running full600, write the “why this is worth GPU time” in the note**

Minimum justification:
- smoke200 is stable
- no obvious regression in tLPIPS trend
- you have a clear stoploss (if full600 is all-worse vs Plan‑B, stop)

**Step 2: Run full600 (single run only)**

Run:
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
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```
Expected:
- Stats files exist: `.../stats/val_step0599.json`, `.../stats/test_step0599.json`
- If `PSNR/LPIPS/tLPIPS` are all worse than `planb_init_600`, treat as stoploss and do not iterate blindly.
