# Plan-B seg400_460 Gate-S1 (Owner A)

- Date: 2026-02-26
- Data: `data/selfcap_bar_8cam60f_seg400_460`

## Init generation

Command:
- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/init_velocity_from_points.py --data_dir data/selfcap_bar_8cam60f_seg400_460 --baseline_init_npz outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz --frame_start 0 --frame_end_exclusive 60 --keyframe_step 5 --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg400_460`

Artifacts:
- `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/init_points_planb_step5.npz`
- `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/velocity_stats.json`

## Key fields

- `counts.match_ratio_over_eligible = 0.5510144213`
- `clip_threshold_m_per_frame = 0.0135933962`
- canonical `clip_threshold_m_per_frame = 0.0108813836`
- ratio vs canonical = `1.2492x`
- `n_clipped = 470`
- `n_valid_matches = 46958`
- `n_clipped / n_valid_matches = 0.0100089442`

## Decision

Gate-S1 No-Go checks:
- `match_ratio_over_eligible < 0.05`: not triggered
- clip threshold > `10x` canonical: not triggered

Decision: **PASS**. Proceed to Gate-S2 smoke200 runs.
