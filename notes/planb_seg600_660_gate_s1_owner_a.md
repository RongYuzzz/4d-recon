# Plan-B seg600_660 Gate-S1（Owner A）

- 日期：2026-02-26
- 切片：`data/selfcap_bar_8cam60f_seg600_660`
- 目标：训练前验证 velocity 统计是否在可接受范围

## 产物检查

- `outputs/plan_b/selfcap_bar_8cam60f_seg600_660/velocity_stats.json`：存在

## 关键统计

- `counts.match_ratio_over_eligible`: 0.5863
- `clip_threshold_m_per_frame`: 0.011418
- canonical `clip_threshold_m_per_frame`: 0.010881
- `clip_threshold` 相对 canonical 比值：1.0493x
- `n_clipped`: 495

## Gate-S1 判定

- 条件1（match_ratio >= 0.05）：PASS
- 条件2（clip_threshold 不超过 canonical 的 10x）：PASS
- **总体：PASS**

## 结论

- 进入 Gate-S2 smoke200（GPU0）
