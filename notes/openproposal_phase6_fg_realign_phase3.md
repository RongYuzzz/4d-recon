# Phase 6 FG realign - Phase 3 follow-up (weak-fusion)

Date: 2026-03-05

## Run list (same-init fairness check)

- baseline: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- treatment A (dynamic_scaled): `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_dynp99_w0.8_600_r1`
- treatment B (static_from_dynamic_scaled): `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w0.8_600_r1`

`init_npz_path` in all 3 `cfg.yml`:

- `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

## Mask preprocessing sanity

- source npz: `/root/autodl-tmp/projects/4d-recon/outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz`
- scaled dynamic (`q=0.99`) mean: `0.0215` (not near zero)
- static-from-dynamic mean: `0.9785` (still highly saturated toward 1)

## Metrics @ step 599

| run | psnr | lpips | tlpips | psnr_fg | lpips_fg | psnr_fg_area | lpips_fg_comp | lpips_backend |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 16.1520 | 0.7325 | 0.007053 | 16.8066 | 0.24388 | 9.8674 | 0.04960 | auto |
| dyn_p99_w0.8_r1 | 16.3438 | 0.7331 | 0.007187 | 16.5294 | 0.24611 | 9.5901 | 0.05174 | auto |
| static_p99_w0.8_r1 | 16.2658 | 0.7437 | 0.008740 | 17.1048 | 0.24271 | 10.1655 | 0.05044 | auto |

Guardrail check (`ΔtLPIPS <= +0.01`, vs baseline):

- dyn_p99_w0.8_r1: `+0.000134` (PASS)
- static_p99_w0.8_r1: `+0.001687` (PASS)

## Weak path activity evidence

TB export:

- `/root/autodl-tmp/projects/4d-recon/outputs/qualitative_local/openproposal_phase6/tb_scalars/planb_init_weak_dynp99_w0.8_600_r1_tb_scalars.csv`

`pseudo_mask/active_ratio` (12 samples):

- min/max/mean = `0.0117 / 0.0303 / 0.0212`

Interpretation: weak-fusion branch is not a no-op, and active ratio is far from saturation (`~1.0`).

## Decision

- If target priority is strictly `psnr_fg↑` and `lpips_fg↓` together, neither treatment strictly dominates baseline.
- Compared to dynamic_scaled, static_from_dynamic_scaled improves foreground metrics (`psnr_fg`, `lpips_fg`, `psnr_fg_area`) but worsens full-frame `lpips`.
- For Phase 3 direction test, `static_from_dynamic_scaled` is the better candidate to carry forward, while keeping guardrail monitoring on full-frame quality.

