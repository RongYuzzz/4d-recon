# Plan-B seg2 Gate-S2 (Owner A)

- Date: 2026-02-26
- Compared runs:
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_smoke200`
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_smoke200`

## Artifact checks

Both smoke200 runs contain:
- `stats/test_step0199.json`
- `videos/traj_4d_step199.mp4`
- `stats/throughput.json`

## Metrics (test@199)

- baseline_smoke200:
  - PSNR `12.7162103653`
  - LPIPS `0.6349298358`
  - tLPIPS `0.0861575082`
- planb_init_smoke200:
  - PSNR `12.9204168320`
  - LPIPS `0.5819285512`
  - tLPIPS `0.0337698422`

Delta (planb - baseline):
- `ΔPSNR = +0.2042064667 dB`
- `ΔLPIPS = -0.0530012846`
- `ΔtLPIPS = -0.0523876660` (relative drop `60.80%`)

## Gate-S2 decision

PASS condition (any one):
1. `tLPIPS` relative drop ≥ 5% and PSNR not worse than -0.2 dB
2. LPIPS drop ≥ 0.01 and training stable

Observed:
- Condition 1: **PASS**
- Condition 2: **PASS**
- Stability: no NaN / divergence observed

Decision: **Gate-S2 PASS**.

Action: proceed to A55 (`planb_init_600`), consuming the last full600 budget slot.
