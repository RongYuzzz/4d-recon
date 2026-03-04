# OpenProposal Phase 3 — Weak Supervision A/B Result (THUman4.0 s00)

Date: 2026-03-04 (UTC)
Plan: `docs/plans/2026-03-03-openproposal-phase3-weak-supervision.md`
Scope: local-eval only

## 1) Runs And Configs

Baseline:
- run: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- full metrics: `stats/test_step0599.json`
- masked metrics: `stats_masked/test_step0599.json`

Treatment (Phase 3 default path):
- run: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- full metrics: `stats/test_step0599.json`
- masked metrics: `stats_masked/test_step0599.json`
- weak-fusion args:
  - `--pseudo-mask-npz /root/autodl-tmp/projects/4d-recon/outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz`
  - `--pseudo-mask-weight 0.8`
  - `--pseudo-mask-end-step 600`

Optional control (weak path + no cue):
- run: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_zeros_600`
- full metrics: `stats/test_step0599.json`
- masked metrics: `stats_masked/test_step0599.json`
- weak-fusion args:
  - `--pseudo-mask-npz /root/autodl-tmp/projects/4d-recon/outputs/cue_mining/openproposal_thuman4_s00_zeros_ds4/pseudo_masks.npz`
  - `--pseudo-mask-weight 0.8`
  - `--pseudo-mask-end-step 600`

Common eval settings (masked):
- `mask_source=dataset`
- `bbox_margin_px=32`
- fill-black mouth/ROI convention from `scripts/eval_masked_metrics.py`
- `mask_thr=0.5`

## 2) Full-Frame Metrics (from `stats/test_step0599.json`)

| run | psnr | ssim | lpips | tlpips |
|---|---:|---:|---:|---:|
| baseline (`planb_init_600`) | 16.152018 | 0.562077 | 0.732467 | 0.007053 |
| weak diff-invert q0.950 w0.8 | 16.280893 | 0.565718 | 0.726545 | 0.007182 |
| weak zeros w0.8 (control) | 16.157368 | 0.562174 | 0.734700 | 0.007545 |

A/B (treatment - baseline):
- `ΔPSNR = +0.128875`
- `ΔSSIM = +0.003641`
- `ΔLPIPS = -0.005922` (improved)

## 3) Foreground-Masked Metrics (from `stats_masked/test_step0599.json`)

| run | psnr_fg | lpips_fg | bbox_margin_px | mask_thr |
|---|---:|---:|---:|---:|
| baseline (`planb_init_600`) | 16.806620 | 0.243883 | 32 | 0.5 |
| weak diff-invert q0.950 w0.8 | 16.636105 | 0.250786 | 32 | 0.5 |
| weak zeros w0.8 (control) | 16.484616 | 0.244610 | 32 | 0.5 |

A/B (treatment - baseline):
- `ΔPSNR_FG = -0.170515`
- `ΔLPIPS_FG = +0.006903` (worse)

## 4) Conclusion

Main A/B conclusion (`planb_init_600` vs `planb_init_weak_diffmaskinv_q0.950_w0.8_600`):
- **Full-frame improves**, but **foreground-masked degrades**.
- Therefore this weak setup did not improve the target FG quality gate in this scene.

Interpretation with control:
- `weak_zeros_600` does not bring the same full-frame gain as diff-invert treatment.
- This suggests the gain is not purely from enabling the weak path; cue content matters for full-frame behavior.
- However, both weak variants are below baseline on `psnr_fg`, so current weak setting is still not FG-beneficial.

Most likely causes (for Phase 4 follow-up):
1. **Mask semantics and weighting mismatch**: invert + `weight=0.8` likely suppresses static background strongly, improving global reconstruction metrics while hurting fine FG detail restoration.
2. **Cue quality/stability still insufficient for FG gate**: even after q0.950 fallback, mask confidence/noise pattern is not aligned enough with dataset foreground objective under current fusion schedule.

## 5) Qualitative Output (Local Only)

Side-by-side (no GT) video:
- `/root/autodl-tmp/projects/4d-recon/outputs/qualitative_local/openproposal_phase3/planb_vs_weak_step599.mp4`

