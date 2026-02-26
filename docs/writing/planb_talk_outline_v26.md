# Plan-B v26 Slide 讲稿大纲（10-12 分钟）

## 0) 开场（0:00-0:30）
- 先声明口径：只引用 `docs/report_pack/2026-02-26-v26/` 四件套；训练冻结，新增 full600 `N=0`。
- 本次目标：展示 Plan-B 在短预算下的稳定收益与可审计证据链。

## 1) 先播 side-by-side（0:30-4:30）
- Slide 1（canonical，约 90s）：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`。
- Slide 2（seg200_260，约 90s）：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`。
- Slide 3（可选其一，约 60-90s）：推荐 `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`。
- 讲法：只讲“同向改善”与“先看视觉，再看数字”，不展开机制争论。

## 2) 再给主表 Table 1（4:30-7:00）
- Slide 4（canonical full600）：
  - `baseline_600`: 18.9496 / 0.6653 / 0.4048 / 0.0230
  - `planb_init_600`: 20.4488 / 0.7070 / 0.3497 / 0.0072
  - Δ(planb-baseline): PSNR +1.4992, LPIPS -0.0551, tLPIPS -0.0158
- Slide 5（seg200_260 full600）：
  - `baseline_600`: 18.0468 / 0.6353 / 0.4138 / 0.0234
  - `planb_init_600`: 20.0417 / 0.6656 / 0.3534 / 0.0078
  - Δ(planb-baseline): PSNR +1.9950, LPIPS -0.0604, tLPIPS -0.0156

## 3) 再给 anti-cherrypick（7:00-8:30）
- Slide 6（smoke200 多切片同向）：
  - seg300_360: ΔPSNR +0.1811, ΔLPIPS -0.0497, ΔtLPIPS -0.0517
  - seg400_460: ΔPSNR +0.1845, ΔLPIPS -0.0481, ΔtLPIPS -0.0516
  - seg600_660: ΔPSNR +0.1905, ΔLPIPS -0.0488, ΔtLPIPS -0.0525
  - seg1800_1860: ΔPSNR +0.1799, ΔLPIPS -0.0489, ΔtLPIPS -0.0549
- 附一句：seg400_460/seg1800_1860 已做 template hygiene 重跑，防模板泄漏质疑。

## 4) 最后才进防守附录（8:30-10:30）
- Slide 7（Gate-S1 统计）：给结论性一句话与入口路径，不在主流程展开细节。
- Slide 8（component ablation）：突出 mutual NN 的定位是稳定器，主要反映在时序指标稳定性。
- Slide 9（feature-loss v2 负结果）：主线冻结、保留失败归因链，不再追加 full600。
- Slide 10（为何不做 Plan-B + Feature Loss）：二者正交，但预算冻结（`N=0`）下写作阶段仅保留为 limitation/future work。

## 5) Ending（10:30-12:00）
- 决议复述：Plan-B only、feature-loss v2 No-Go、Plan-B+weak No-Go、新增 full600 `N=0`。
- 写作冲刺交付：`planb_onepager_v26.md`、`planb_talk_outline_v26.md`、`planb_qa_cards_v26.md`。
- 收口：当前贡献是“短预算收敛与时序稳定性”的可复现改进，而非高保真上限宣称。

## 证据口径（页尾固定）
- `docs/report_pack/2026-02-26-v26/metrics.csv`
- `docs/report_pack/2026-02-26-v26/scoreboard.md`
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`
