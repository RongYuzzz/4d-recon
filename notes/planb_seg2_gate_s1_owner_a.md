# Plan-B seg2 Gate-S1 (Owner A)

- Date: 2026-02-26
- Input data: `data/selfcap_bar_8cam60f_seg200_260`

## Execution

Command:
- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/init_velocity_from_points.py --data_dir data/selfcap_bar_8cam60f_seg200_260 --baseline_init_npz outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600/keyframes_60frames_step5.npz --frame_start 0 --frame_end_exclusive 60 --keyframe_step 5 --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg200_260`

Artifacts:
- `outputs/plan_b/selfcap_bar_8cam60f_seg200_260/init_points_planb_step5.npz`
- `outputs/plan_b/selfcap_bar_8cam60f_seg200_260/velocity_stats.json`

## Key stats

From `velocity_stats.json`:
- `counts.match_ratio_over_eligible = 0.5922857277`
- `clip_threshold_m_per_frame = 0.0109599937`
- `n_clipped = 507`
- `n_valid_matches = 50612`
- `n_clipped / n_valid_matches = 0.0100173872`

Canonical reference (`outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json`):
- `clip_threshold_m_per_frame = 0.0108813836`
- seg2/canonical ratio = `1.0072x`

## Gate-S1 decision

No-Go conditions:
- `match_ratio_over_eligible < 0.05` -> **not triggered**
- `clip_threshold > 10x canonical` and clipped ratio high -> **not triggered**

Decision: **Gate-S1 PASS**.
