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

- `tau_final = 0.070611` (from `p50(||v||_ckpt)`)

Static-only export:
- result dir:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_static_planb_init_600_tau0.070611`
- video:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_static_planb_init_600_tau0.070611/videos/traj_4d_step599.mp4`

Dynamic-only export:
- result dir:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_dynamic_planb_init_600_tau0.070611`
- video:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_dynamic_planb_init_600_tau0.070611/videos/traj_4d_step599.mp4`

Side-by-side:
- `/root/autodl-tmp/projects/4d-recon/outputs/qualitative_local/openproposal_phase5/static_vs_dynamic_planb_init_600_tau0.070611.mp4`

Sanity (export log):
- static kept `46374/92749 (0.500)`
- dynamic kept `46375/92749 (0.500)`

Execution note:
- If you see `Ninja is required to load C++ extensions`, ensure `PATH="$(dirname "$VENV_PYTHON"):$PATH"` before running the export command.

## 4) Optional mIoU (`miou_fg`) (Task 3)

- `gt_fg`: THUman4.0 dataset-provided masks (`data/thuman4_subject00_8cam60f/masks/<camera>/*.png`)
- `pred_fg`: Phase 2 pseudo masks (`mask_thr=0.5`):
  - `/root/autodl-tmp/projects/4d-recon/outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz`
- `miou_fg` snapshot JSON:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599_miou_phase5.json`
- Result (step=599): `miou_fg = 0.0` (with `mask_source=dataset`, `mask_thr=0.5`, `bbox_margin_px=32`)

Interpretation:
- This `miou_fg` is a foreground-consistency health check (dataset mask vs algorithmic pseudo mask), not “human instance segmentation GT”.
- `miou_fg=0.0` indicates the current pseudo masks are effectively too sparse / not aligned at `mask_thr=0.5` under this definition (consistent with Phase 2 observations).

## 5) Final Deliverables (Task 4)

Repro pointers (local):
- Plan: `docs/plans/2026-03-03-openproposal-phase5-edit-demo-miou.md`
- `CKPT_PATH`:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/ckpts/ckpt_599.pt`
- `tau_final = 0.070611` (from `p50(||v||_ckpt)` in `notes/openproposal_phase5_velocity_stats_planb_init_600.md`)
- Static-only video:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_static_planb_init_600_tau0.070611/videos/traj_4d_step599.mp4`
- Dynamic-only video:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_dynamic_planb_init_600_tau0.070611/videos/traj_4d_step599.mp4`
- Side-by-side:
  - `/root/autodl-tmp/projects/4d-recon/outputs/qualitative_local/openproposal_phase5/static_vs_dynamic_planb_init_600_tau0.070611.mp4`
- Optional `miou_fg`:
  - `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599_miou_phase5.json`

Limitations:
- Removal demo is **filtering**, not inpainting: occluded/background-unseen regions can appear as holes/ghosting after removal, especially in heavy self-occlusion frames.
