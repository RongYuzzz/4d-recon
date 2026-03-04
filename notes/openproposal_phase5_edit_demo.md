# OpenProposal Phase 5 — Edit Demo (Removal) + Optional mIoU (THUman4.0 s00)

Date: 2026-03-04 (UTC)  
Plan: `docs/plans/2026-03-03-openproposal-phase5-edit-demo-miou.md`  
Scope: local execution + local export/eval

## 1) Gate Check (Task 0)

- Selected `CKPT_PATH`:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/ckpts/ckpt_599.pt`
- `CKPT_RUN=planb_init_600`

## 2) Velocity Stats And Tau Selection (Task 1)

- Stats report:
  - `notes/openproposal_phase5_velocity_stats_planb_init_600.md`
- Source section for thresholding:
  - `step599 (ckpt)` in the report above

`||v||` snapshot from `step599 (ckpt)`:
- `p50 = 0.070611`
- `p90 = 0.133772`

Tau candidates (fixed):
- `tau_low = 0.070611` (from `p50(||v||_ckpt)`, more aggressive split)
- `tau_high = 0.133772` (from `p90(||v||_ckpt)`, more conservative split)

CPU keep-ratio precheck:
- `tau=0.070611`: `static_ratio(<tau)=0.4999946091062976`, `dynamic_ratio(>=tau)=0.5000053908937023`
- `tau=0.133772`: `static_ratio(<tau)=0.8999989218212595`, `dynamic_ratio(>=tau)=0.10000107817874047`

Final threshold for demo:
- `tau_final = 0.070611`
- Rationale: For removal demo interpretability, `p50` gives balanced static/dynamic split and avoids the too-conservative `p90` case (only ~10% dynamic), which is less likely to show clear foreground removal.

## 3) Export Results (Task 2)

- Pending

## 4) Optional mIoU (`miou_fg`) (Task 3)

- Pending

## 5) Final Deliverables (Task 4)

- Pending
