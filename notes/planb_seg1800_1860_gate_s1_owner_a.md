# Plan-B seg1800_1860 Gate-S1（Owner A）

- 日期：2026-02-26
- 切片：`data/selfcap_bar_8cam60f_seg1800_1860`
- baseline 模板：`/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz`

## 产物检查

- `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/velocity_stats.json`：存在

## 关键统计

- `counts.match_ratio_over_eligible`: 0.535983
- `clip_threshold_m_per_frame`: 0.017100
- canonical `clip_threshold_m_per_frame`: 0.010881
- 相对 canonical 比值：1.5715x
- `n_clipped`: 457

## Gate-S1 判定

- 条件1（match_ratio >= 0.05）：PASS
- 条件2（clip_threshold 不超过 canonical 10x）：PASS
- **总体：PASS**

## 结论

- 进入 Gate-S2 smoke200（GPU0）
