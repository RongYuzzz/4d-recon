# protocol_v2 framediff gate 可视化（p=0.10 vs p=0.02）

日期：2026-02-28  
任务：Post dual-GPU next tasks / Task A3（Owner A, GPU0 side analysis）

## 输入缓存

- p=0.10 cache：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
- p=0.02 cache：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz`

## 输出路径

- 可视化目录：`outputs/viz/gate_framediff/2026-02-28-p010-vs-p002/`
- report-pack 诊断目录（用于离线包）：
  - `outputs/report_pack/diagnostics/gate_framediff_p010/`
  - `outputs/report_pack/diagnostics/gate_framediff_p002/`
- overlay 样例（2 视角 × 3 帧，共 6 张）：
  - `outputs/viz/gate_framediff/2026-02-28-p010-vs-p002/frame010_cam02_overlay_compare.png`
  - `outputs/viz/gate_framediff/2026-02-28-p010-vs-p002/frame010_cam08_overlay_compare.png`
  - `outputs/viz/gate_framediff/2026-02-28-p010-vs-p002/frame030_cam02_overlay_compare.png`
  - `outputs/viz/gate_framediff/2026-02-28-p010-vs-p002/frame030_cam08_overlay_compare.png`
  - `outputs/viz/gate_framediff/2026-02-28-p010-vs-p002/frame050_cam02_overlay_compare.png`
  - `outputs/viz/gate_framediff/2026-02-28-p010-vs-p002/frame050_cam08_overlay_compare.png`
- 统计汇总：`outputs/viz/gate_framediff/2026-02-28-p010-vs-p002/overlay_activation_summary.csv`

## 一句话结论（供答辩/失败分析引用）

- 从 p=0.10 到 p=0.02，`gate_framediff` 在 9×9 token 网格上的激活由 **9/81** 收缩到 **2/81**（激活比例约从 **0.1093** 降到 **0.0243**，约 4.5× 更稀疏）；overlay 显示其主要保留在高帧差边界附近，解释了“约束更少、更稳但改善幅度有限”的趋势。
