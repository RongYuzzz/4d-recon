# OpenProposal Pre-Expert Weight Tune (weak staticp99, w=0.7)

Date: 2026-03-05 (UTC)
Plan: `docs/plans/2026-03-05-openproposal-preexpert-weight-tune-staticp99.md`

## Baseline (reused)

- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed43`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed44`

## New treatments (this run, append-only)

- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.7_600_seed43`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.7_600_seed44`

All treatment runs use:
- `pseudo_mask_weight=0.7`
- `pseudo_mask_end_step=600`
- same `init_npz_path` as baseline (`outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`)

## Locked inputs

- `MASK_NPZ=/root/autodl-tmp/projects/4d-recon/outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz`
  - sha256: `37dd090e1ff25271dceb58c0d00db5a41f8c4dc8ea75e9929554f46434734743`
- `PLANB_INIT_NPZ=/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
  - sha256: `d6ce23a2a2116ce72dddee9a8b4e64741cdfe5f4ee91bae79cea3b695ca4c88f`

## Eval protocol

Foreground masked eval with `scripts/eval_masked_metrics.py`:
- `mask_source=dataset`
- `bbox_margin_px=32`
- `mask_thr=0.5`
- guardrail: `ΔtLPIPS <= +0.01`

## Per-seed deltas (treatment - baseline)

### seed43
- Δpsnr_fg: `+0.245204`
- Δlpips_fg: `-0.007882`
- ΔtLPIPS: `+0.000599` (guardrail pass)
- pass_fg: `True`, pass_guard: `True`, OK: `True`

### seed44
- Δpsnr_fg: `+0.272591`
- Δlpips_fg: `+0.001311`
- ΔtLPIPS: `+0.000934` (guardrail pass)
- pass_fg: `False`, pass_guard: `True`, OK: `False`

## Final decision

- `OVERALL_OK=False`
- 结论：`w=0.7` 仍未在 2-seed 下稳定满足 `psnr_fg↑ & lpips_fg↓`。
- 决策：按计划止损，不继续做 weight 扫描；进入专家诊断/更换假设。

