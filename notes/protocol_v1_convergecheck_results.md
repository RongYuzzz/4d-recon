# Protocol v1 Convergecheck Results (dur0 + L4D=1e-4)

Protocol: `docs/protocols/protocol_v1_convergecheck.yaml`  
Locked settings: `seed=42`, `lambda_duration_reg=0` (dur0), `lambda_4d_reg=1e-4` (L4D)  
Runs:
- baseline: `outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/baseline_long5k_dur0`
- planb_init: `outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/planb_init_long5k_dur0`

## Key numbers (test split)

| step | baseline PSNR | planb PSNR | ΔPSNR | baseline tLPIPS | planb tLPIPS | ΔtLPIPS |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 599 | 18.6148 | 19.8499 | +1.2351 | 0.0253 | 0.0130 | -0.0123 |
| 1999 | 22.9387 | 23.7671 | +0.8284 | 0.0070 | 0.0033 | -0.0037 |
| 4999 | 24.5499 | 25.2990 | +0.7491 | 0.0043 | 0.0020 | -0.0023 |

Source scoreboards:
- `docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck.md`
- `docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck_step2000.md`
- `docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck_step5000.md`

## Conclusion (for writing)

This matches case **A**: the performance gap does **not** collapse with longer training.  
Plan‑B init remains better than baseline at step 4999 (PSNR↑, LPIPS/tLPIPS↓), so the gain is not just an early‑convergence artifact.

## One figure

- `outputs/report_pack/diagnostics/closeout_20260306/convergecheck_v1_psnr_tlpips_vs_step.png`

