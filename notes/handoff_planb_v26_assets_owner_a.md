# Handoff: Plan-B v26 Assets (Owner A -> Owner B)

- Date: 2026-02-26
- Scope: A131/A132/A133 outputs for writing mode freeze (`v26`)
- Decision source: `docs/decisions/2026-02-26-planb-v26-freeze.md`

## A131 audit artifacts

- Audit note:
  - `notes/planb_v26_audit_owner_a.md`
- Snapshot source of truth:
  - `docs/report_pack/2026-02-26-v26/metrics.csv`
  - `docs/report_pack/2026-02-26-v26/scoreboard.md`
  - `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
  - `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`
- Rebuilt (non-git output path):
  - `/root/projects/4d-recon/outputs/report_pack/metrics.csv`
  - `/root/projects/4d-recon/outputs/report_pack/scoreboard.md`
  - `/root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md`

## A132 qualitative assets

- Frame directory:
  - `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/frames_selected_v26`
- Frame-selection note:
  - `notes/planb_qualitative_frames_v26_owner_a.md`
- Side-by-side videos (6 clips):
  - `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
  - `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`
  - `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4`
  - `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`
  - `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg600_660_step199.mp4`
  - `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4`

## A133 Table-1 extract

- Table note:
  - `notes/planb_table1_v26_owner_a.md`
- Includes:
  - canonical full600 baseline/planb and deltas
  - seg200_260 full600 baseline/planb and deltas
  - explicit `Δ = planb - baseline`

## 5-minute pre-meeting playback order

1. canonical (`planb_vs_baseline_step599.mp4`)
2. seg200_260 (`planb_vs_baseline_seg200_260_step599.mp4`)
3. one smoke200 slice of choice (recommended: `seg300_360` first; fallback: `seg400_460` or `seg1800_1860`)

## One-line narrative reminder

Plan-B 的主因是“物理速度先验打破收敛陷阱”，Mutual NN 的定位是稳定器（stabilizer），用于解释消融行为与 tLPIPS 改善方向。

