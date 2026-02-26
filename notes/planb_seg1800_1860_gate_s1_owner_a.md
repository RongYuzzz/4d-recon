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

## Update (re-template baseline init, 2026-02-26)

- baseline template: `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/_baseline_init/keyframes_60frames_step5.npz`
- Gate-S1 key fields:
  - `match_ratio_over_eligible = 0.5791285625`
  - `clip_threshold_m_per_frame = 0.0116234971`
  - `n_clipped = 490`
- smoke200 (test@step199) baseline vs re-template planb:
  - baseline: `PSNR 12.5796127319 / LPIPS 0.6289873719 / tLPIPS 0.0888407901`
  - planb: `PSNR 12.7594900131 / LPIPS 0.5800951719 / tLPIPS 0.0339605361`
  - deltas (planb - baseline): `ΔPSNR +0.1798772812 / ΔLPIPS -0.0488922000 / ΔtLPIPS -0.0548802540`
- 判定：**PASS**（Gate-S1 与 Gate-S2 均通过）
- 一句话结论：re-template 后 seg1800_1860 仍保持同向收益，可继续作为 anti-cherrypick 防守证据。

