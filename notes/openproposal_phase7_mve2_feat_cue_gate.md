# Phase7 MVE-2: Feature Loss with Silhouette Cue Gating (oracle)

## Experiment setup

- **Baseline**: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- **Treatment**: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_cuegate_lam0.005_600_sameinit_r2`
- **Feature config**: `phi=token_proj`, `loss=cosine`, `lambda=0.005`, `start=0`, `ramp=400`, `every=8`, `gating=cue`
- **Cache tag**: `openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10`
- **Masked eval**: dataset silhouette, `bbox_margin_px=32`, `boundary_band_px=3`

## Activation evidence (feature loss actually active)

From exported TB scalars (`vggt_feat/active`):

- step 0: `19`
- step 200: `21`
- step 400: `16`

All are non-zero, so cue-gated feature loss was active during training.

## Fairness gate (same init)

`init_npz_path` in both cfg files is identical:

- baseline: `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- treatment: `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

## Metrics (test_step0599)

### Full-image metrics

- `psnr`: 16.1520 → 16.3144 (**Δ +0.1624**)
- `lpips`: 0.732467 → 0.731939 (**Δ -0.0005275**, slight improvement)
- `tlpips`: 0.0070530 → 0.0074583 (**Δ +0.0004053**, guardrail pass)

### Foreground ROI metrics (silhouette)

- `psnr_fg`: 16.8066 → 16.4042 (**Δ -0.4025**, worse)
- `lpips_fg`: 0.243883 → 0.256594 (**Δ +0.012711**, worse)
- `psnr_fg_area`: 9.86738 → 9.46493 (**Δ -0.40245**, worse)
- `lpips_fg_comp`: 0.0496048 → 0.0510573 (**Δ +0.0014525**, worse)

### Optional boundary-band metrics (`boundary_band_px=3`)

- `psnr_bd_area`: 12.9387 → 12.6567 (**Δ -0.2820**, worse)
- `lpips_bd_comp`: 0.0244575 → 0.0247514 (**Δ +0.0002939**, worse)

## Pass/fail against target

Target: `psnr_fg ↑` and `lpips_fg ↓` with guardrail `ΔtLPIPS <= +0.01`.

- Guardrail: **PASS** (`ΔtLPIPS=+0.000405 <= +0.01`)
- Core ROI objective (`psnr_fg↑ & lpips_fg↓`): **FAIL**

Suggested strict threshold for quick expert screening:

- `Δpsnr_fg >= +0.2 dB` and `Δlpips_fg <= -0.003`
- Observed: `Δpsnr_fg=-0.4025`, `Δlpips_fg=+0.012711` → **FAIL**

## Conclusion

In this oracle-style cue-gated feature-loss run, full-image metrics are roughly neutral/slightly better, but silhouette ROI consistently degrades. This does not support the hypothesis that prior feature-loss failure was mainly due to missing ROI alignment.

