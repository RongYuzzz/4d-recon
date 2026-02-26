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

## Update (re-template baseline init, 2026-02-26)

- baseline template: `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/_baseline_init/keyframes_60frames_step5.npz`
- Gate-S1 key fields:
  - `match_ratio_over_eligible = 0.5887343944`
  - `clip_threshold_m_per_frame = 0.0113623817`
  - `n_clipped = 498`
- smoke200 (test@step199) baseline vs re-template planb:
  - baseline: `PSNR 12.5888776779 / LPIPS 0.6276710629 / tLPIPS 0.0851773545`
  - planb: `PSNR 12.7733364105 / LPIPS 0.5796048045 / tLPIPS 0.0336262509`
  - deltas (planb - baseline): `ΔPSNR +0.1844587326 / ΔLPIPS -0.0480662584 / ΔtLPIPS -0.0515511036`
- 判定：**PASS**（Gate-S1 与 Gate-S2 均通过）
- 一句话结论：re-template 后结果仍与既有结论同向，Plan-B 改善稳定且可用于 anti-cherrypick 证据位。

