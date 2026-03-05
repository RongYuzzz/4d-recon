# Phase7 MVE-1: Weak-Fusion Early-Only (static_from_dynamic_scaled q0.99, end_step=200)

## Experiment setup

- **Baseline**: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- **Treatment**: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w0.8_end200_600_r2`
- **Mask NPZ**: `outputs/cue_mining/_phase7_scaled/openproposal_thuman4_s00_diff_q0.950_ds4_med3_q0.99/pseudo_masks_static_from_dynamic_scaled_q0.99.npz`
- **Schedule**: `pseudo_mask_weight=0.8`, `pseudo_mask_end_step=200`, `max_steps=600`
- **Masked eval**: dataset silhouette, `bbox_margin_px=32`, `boundary_band_px=3`

## Fairness gate (same init)

`init_npz_path` in both cfg files is identical:

- baseline: `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- treatment: `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

## Metrics (test_step0599)

### Full-image metrics

- `psnr`: 16.1520 → 16.3206 (**Δ +0.1686**)
- `lpips`: 0.732467 → 0.735531 (**Δ +0.003064**, worse)
- `tlpips`: 0.0070530 → 0.0072271 (**Δ +0.0001741**, guardrail pass)

### Foreground ROI metrics (silhouette)

- `psnr_fg`: 16.8066 → 16.4705 (**Δ -0.3361**, worse)
- `lpips_fg`: 0.243883 → 0.254362 (**Δ +0.010479**, worse)
- `psnr_fg_area`: 9.86738 → 9.53129 (**Δ -0.33609**, worse)
- `lpips_fg_comp`: 0.0496048 → 0.0504020 (**Δ +0.0007973**, worse)

### Optional boundary-band metrics (`boundary_band_px=3`)

- `psnr_bd_area`: 12.9387 → 12.5254 (**Δ -0.4133**, worse)
- `lpips_bd_comp`: 0.0244575 → 0.0260501 (**Δ +0.0015926**, worse)

## Pass/fail against target

Target: `psnr_fg ↑` and `lpips_fg ↓` with guardrail `ΔtLPIPS <= +0.01`.

- Guardrail: **PASS** (`ΔtLPIPS=+0.000174 <= +0.01`)
- Core ROI objective (`psnr_fg↑ & lpips_fg↓`): **FAIL**

Suggested strict threshold for quick expert screening:

- `Δpsnr_fg >= +0.2 dB` and `Δlpips_fg <= -0.001`
- Observed: `Δpsnr_fg=-0.3361`, `Δlpips_fg=+0.010479` → **FAIL**

## Decision for conditional END_STEP=300

Conditional rerun (`END_STEP=300`) was **not** launched in this pass because MVE-1 is not “close but trade-off”; ROI metrics and boundary metrics are consistently worse.
