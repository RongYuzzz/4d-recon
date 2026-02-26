# Plan-B seg300_360 Gate-S1 (Owner A)

- Date: 2026-02-26
- Slice data: `/root/projects/4d-recon/data/selfcap_bar_8cam60f_seg300_360`
- Baseline template (template hygiene): `/root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360/_baseline_init/keyframes_60frames_step5.npz`

## Commands

1. 固化 baseline init 模板：
- `cp outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200/keyframes_60frames_step5.npz outputs/plan_b/selfcap_bar_8cam60f_seg300_360/_baseline_init/keyframes_60frames_step5.npz`

2. 仅替换 velocities 生成 Plan-B init：
- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/init_velocity_from_points.py --data_dir /root/projects/4d-recon/data/selfcap_bar_8cam60f_seg300_360 --baseline_init_npz /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360/_baseline_init/keyframes_60frames_step5.npz --frame_start 0 --frame_end_exclusive 60 --keyframe_step 5 --out_dir /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360`

## Artifact checks

- `/root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360/init_points_planb_step5.npz`: PASS
- `/root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360/velocity_stats.json`: PASS

## Gate-S1 key fields

- `counts.match_ratio_over_eligible = 0.5955913473`
- `clip_threshold_m_per_frame = 0.0115640901`
- `n_clipped = 507`
- canonical `clip_threshold_m_per_frame = 0.0108813836`
- ratio vs canonical = `1.0627x`

## Gate-S1 decision

- 条件1（`match_ratio_over_eligible >= 0.05`）：PASS
- 条件2（clip threshold 不超过 canonical `10x`）：PASS
- **总体：PASS**

## Conclusion

Gate-S1 通过，进入 `planb_init_smoke200`（GPU0，MAX_STEPS=200）。
