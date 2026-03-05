# OpenProposal Pre‑Expert Seed Replication — weak `staticp99 + w0.8` (THUman4.0 s00)

Date: 2026-03-05 (UTC)  
Plan: `docs/plans/2026-03-05-openproposal-preexpert-seedrep-staticp99.md`  
Worktree: `.worktrees/owner-b-20260305-preexpert-seedrep-staticp99`  
Code version: `e0e9fa55f57842762d2630dca8c99bd487126dd1`

Goal (strict):
- FG objective: `Δpsnr_fg > 0` **and** `Δlpips_fg < 0`
- Guardrail: `ΔtLPIPS <= +0.01`

All comparisons are paired A/B with **same seed** and **same `init_npz_path`**; treatment adds weak fusion.

---

## Locked inputs (hashes)

- Plan‑B init NPZ (shared by all 4 runs):  
  `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`  
  `sha256=d6ce23a2a2116ce72dddee9a8b4e64741cdfe5f4ee91bae79cea3b695ca4c88f`

- Weak mask (treatment only):  
  `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz`  
  `sha256=37dd090e1ff25271dceb58c0d00db5a41f8c4dc8ea75e9929554f46434734743`

---

## Run paths (4)

- Baseline seed43: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed43`
- Treatment seed43: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.8_600_seed43`
- Baseline seed44: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed44`
- Treatment seed44: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.8_600_seed44`

Common training settings (from each `cfg.yml`):
- frames: `start_frame=0`, `end_frame=60`
- cams: train `02,03,04,05,06,07`, val `08`, test `09`
- steps: `max_steps=600`

Treatment-only settings (from `cfg.yml`):
- `pseudo_mask_npz = .../pseudo_masks_static_from_dyn_p99.npz`
- `pseudo_mask_weight = 0.8`
- `pseudo_mask_end_step = 600`

---

## Evaluation convention (FG metrics)

Script:
- `scripts/eval_masked_metrics.py`

Command template (used for all 4 runs):
- `third_party/FreeTimeGsVanilla/.venv/bin/python3 scripts/eval_masked_metrics.py ... --lpips_backend auto`

Locked args:
- `--mask_source dataset` (THUman dataset-provided silhouette masks)
- `--bbox_margin_px 32`
- `--mask_thr 0.5`
- `--stage test --step 599`

Outputs:
- `stats_masked/test_step0599.json` (all 4 runs exist, and `num_fg_frames=60`)

---

## Results (step=599)

Full-frame metrics come from `stats/test_step0599.json`.  
FG metrics come from `stats_masked/test_step0599.json`.

### seed43 (OK=True)

Baseline:
- psnr `16.380287`, lpips `0.735250`, tlpips `0.007900`
- psnr_fg `16.844789`, lpips_fg `0.254605`

Treatment (staticp99 + w0.8):
- psnr `16.627344`, lpips `0.739219`, tlpips `0.008696`
- psnr_fg `18.463843`, lpips_fg `0.237296`

Deltas (treat - base):
- `Δpsnr_fg = +1.619054`
- `Δlpips_fg = -0.017309`
- `ΔtLPIPS = +0.000795` (guardrail pass)

### seed44 (OK=False; FG fails)

Baseline:
- psnr `16.587322`, lpips `0.731089`, tlpips `0.007328`
- psnr_fg `18.031932`, lpips_fg `0.207696`

Treatment (staticp99 + w0.8):
- psnr `16.982124`, lpips `0.739832`, tlpips `0.008729`
- psnr_fg `18.312683`, lpips_fg `0.207945`

Deltas (treat - base):
- `Δpsnr_fg = +0.280750`
- `Δlpips_fg = +0.000248` (**fails `lpips_fg↓`**)
- `ΔtLPIPS = +0.001401` (guardrail pass)

---

## Final decision

- `OVERALL_OK = False` (2-seed replication did not pass the strict FG gate for both seeds).
- Conclusion: weak `staticp99 + w0.8` yields **seed-sensitive / not-stably-reproducible** FG improvement under this budget.

Next step (per plan rule):
- proceed to expert consultation **or** run a tiny “weight/schedule” follow-up to test stability improvement (explicitly tracked as new Phase / new plan).

