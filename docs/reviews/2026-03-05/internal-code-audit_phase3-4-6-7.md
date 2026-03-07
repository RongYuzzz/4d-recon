# Internal Code Audit (Phase 3/4/6/7) — Why `psnr_fg↑ & lpips_fg↓` Didn’t Stably Land

Date: 2026-03-05  
Scope: **Phase 3 / Phase 4 / Phase 6 / Phase 7** (THUman4.0 s00, local-only eval)  
Goal of this audit: before asking external experts, **rule out “we failed because of a code mistake / confounded comparison / broken eval”**.

> Note: This audit is based on **already-generated artifacts** under `outputs/` + committed notes. In this environment, VGGT-1B forward is not feasible due to cgroup memory limits, so we do not recompute VGGT features here.

---

## 0) Hard “Fairness” Checks (No Confounds)

### Phase 3 (weak supervision)

Runs (see `notes/openproposal_phase3_weak_supervision_result.md`):
- baseline: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- treatment: `.../planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- control: `.../planb_init_weak_zeros_600`

All three runs match on:
- `init_npz_path`: `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- `start_frame=0`, `end_frame=60`
- `val_camera_names=08`, `test_camera_names=09`

So Phase 3 A/B is **not** explained by different init or different eval camera.

### Phase 4 (VGGT feature metric)

Valid comparison set (see `notes/openproposal_phase4_attention_contrastive.md`):
- baseline: `.../planb_init_600`
- same-init treatments:
  - `.../planb_feat_v2_gatediff0.10_600_sameinit` (`lambda_vggt_feat=0.01`)
  - `.../planb_feat_v2_gatediff0.10_lam0.005_600_sameinit` (`lambda_vggt_feat=0.005`)

Both same-init runs match baseline on:
- `init_npz_path`: `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- camera split: `val=08`, `test=09`
- frame range: `0..60`

The first-pass treatments **were correctly discarded** as confounded (worktree-local init path).

---

## 1) Masked-Eval Sanity (ROI is Real, Not Empty)

All Phase 3/4 masked metrics were computed with:
- `mask_source=dataset` (THUman GT silhouette masks)
- `bbox_margin_px=32`, `mask_thr=0.5`
- `num_fg_frames=60/60` for the key runs

So “FG metrics got worse” is **not** caused by empty masks or missing frames.

---

## 2) Pseudo-Mask Pipeline: Key Quantitative Facts (Explains Most Weak-Fusion Behavior)

### 2.1 The cue-mined masks are **soft and low-valued** (threshold 0.5 makes them look “empty”)

For the Phase 3 cue source:
- `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz`

Basic stats in mask-NPZ space (downscaled):
- mean ≈ **0.00150**
- `frac(mask > 0.5)` ≈ **1.9e-05** (≈ 0.0019% pixels)

This is why “mIoU at `mask_thr=0.5`” can appear near-zero: **0.5 is simply not a calibrated binarization point for these soft cues**.

We confirmed this via a threshold sweep vs GT silhouette (camera `09`):
- original dynamic mask (`pseudo_masks.npz`):
  - best `mIoU_fg ≈ 0.2986` at `thr_pred=0.01`
- scaled dynamic mask (`pseudo_masks_dyn_p99.npz`):
  - best `mIoU_fg ≈ 0.3968` at `thr_pred=0.02`

Implication:
- The cue is **not random garbage**, but its **dynamicness signal is concentrated in low values**.
- Any analysis that interprets “`mask > 0.5` is foreground/dynamic” will systematically conclude “empty”.

### 2.2 Inverted/static masks are **saturated** and dominated by background

For:
- `pseudo_masks_invert_staticness.npz`: mean ≈ **0.9985**
- `pseudo_masks_static_from_dyn_p99.npz`: mean ≈ **0.9785**

This means “staticness masks” are almost-all-ones; their **top-value pixels are mostly background**, so any “top-p” selection or gating can easily pick background-heavy regions.

This also explains the Phase 6 trade-off:
- static-from-dynamic scaling can improve FG a bit, but tends to **hurt full-frame LPIPS**, because it heavily reweights the loss landscape.

---

## 3) Weak-Fusion Loss Semantics (Not a Bug, but Easy to Mis-Expect)

In trainer code (see `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`), weak fusion does:
- interpret pseudo mask as **dynamicness** in `[0,1]`
- apply **downweight**: `w = 1 - alpha * mask`

So:
- “dynamic mask” → reduces loss on dynamic pixels (helps stability / background), tends to **not** directly optimize dynamic/FG quality.
- “staticness mask” (near-1 everywhere) → downweights most pixels and effectively emphasizes the rare low-mask regions; can easily cause **full-frame vs FG trade-offs**.

This is consistent with observed behavior and does not indicate a coding error.

---

## 4) VGGT Feature-Metric Loss: It Was Actually Active (Phase 4 Not a No-op)

Phase 4 note already established:
- feature loss is non-zero at expected steps (due to `vggt_feat_every=8` + `tb_every=50` recording cadence)
- the treatments were evaluated only in the **same-init** set

Two additional technical constraints that explain limited/unstable ROI gains (non-bug):

1) **Very low spatial granularity in phi space** (token-proj cache)
- cache meta: `phi_size = [8, 9]` (72 cells total)
- `top_p=0.10` → selects **8** cells only

So even a “correct” feature loss is extremely coarse spatially; it is not well-positioned to consistently improve fine FG details under short budgets.

2) **Short budget + ramp + sparse application**
- `MAX_STEPS=600`, `vggt_feat_every=8`, `ramp_steps=400`
- effective “full-strength” updates are limited; improvements may not emerge reliably at <1k steps.

---

## 5) Phase 6 Partial Positive Signal (Pipeline Isn’t Broken)

Phase 6 Phase-3 follow-up shows at least one run that **does** satisfy the core FG effect gate:

From `notes/openproposal_phase6_fg_realign_phase3.md`:
- baseline `planb_init_600`: `psnr_fg=16.8066`, `lpips_fg=0.24388`
- `planb_init_weak_staticp99_w0.8_600_r1`: `psnr_fg=17.1048`, `lpips_fg=0.24271`
- `ΔtLPIPS` guardrail passes for this run

But it is **not strict dominance** because full-frame LPIPS worsens in that run, and it is not yet replicated across seeds/runs.

This strongly suggests:
- the evaluation pipeline is functioning,
- the weak/feature branches are not universally no-ops,
- the remaining problem is **stability + trade-off**, not a single broken line of code.

---

## 6) Remaining “Code-Risk” Items Worth Checking (But Not Proven Broken)

These are the only items that could still be “we implemented it wrong”:

1) **Cache preprocess vs trainer preprocess mismatch**  
   Cache uses `vggt.utils.load_fn.load_and_preprocess_images` while trainer uses a custom tensor preprocess.  
   We measured input-space diff on one THUman frame (cam02, t0) between those two preprocessors:
   - max abs diff ≈ **0.086**
   - mean abs diff ≈ **0.0019**
   This might be acceptable, but it is a plausible contributor to “feature loss not helping”.

   Action (requires a real VGGT forward, best done on a GPU box / full env):
   - compute `phi` for the same GT image using **both** preprocessors, compare `max_abs_diff(phi)`.
   - if large, replace trainer preprocess with an exact replica of `load_and_preprocess_images`.

2) **Token-proj patch grid assumptions**  
   Trainer uses `patch_h0 = input_h//14`, `patch_w0 = input_w//14`.  
   For THUman cache input `[448,518]`, this is consistent; for other scenes, ensure input sizes remain multiples of 14.

---

## 7) Bottom Line

No smoking-gun bug was found that would explain Phase 3/4/6/7 failures as “broken code”.

Most likely explanations for “not stably getting `psnr_fg↑ & lpips_fg↓`”:
- pseudo masks are **soft/low-valued** and extremely threshold-sensitive; staticness/invert masks saturate and bias toward background,
- weak fusion’s default semantics are not directly optimizing the FG objective,
- feature metric loss is spatially **very coarse** (`8×9`) and sparsely applied under short budgets,
- improvements appear as **small, unstable trade-offs**, not a clean dominance.

This suggests the next step is either:
- redesign the supervision to be more FG-aligned (mask calibration + weighting schedule + longer budget), **or**
- ask experts for algorithmic guidance (now that code correctness has been reasonably audited).

