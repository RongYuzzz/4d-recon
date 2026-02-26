# Meeting Handout v26（Plan-B，No-GPU）

## 1) 结论 10 行（先结论）
- 主线固定：Plan-B only（仅替换 init velocities，不改 `protocol_v1`）。
- 冻结决议：`feature-loss v2` No-Go，保留为负结果边界材料。
- 冻结决议：`Plan-B + weak` No-Go，当前证据不足且时序指标未同向改善。
- 预算纪律：新增 full600 `N=0`，本轮仅允许 No-GPU 写作与证据整理。
- canonical 上 Plan-B 相对 baseline 同时提升 PSNR/SSIM 并降低 LPIPS/tLPIPS。
- seg200_260 full600 仍保持同向改善，支持“非单片段特例”。
- seg300/400/600/1800 smoke200 全部同向，anti-cherrypick 防守成立。
- seg400_460 与 seg1800_1860 已做 template hygiene 重跑，防模板泄漏质疑。
- Scope 明确限定为“600 steps 短预算下的收敛性与时序稳定性改进”。
- Limitation 写死：未测 Plan-B + Feature Loss 组合（future work）。

## 2) 三行关键数据（v26 真源）
| Slice / Run | PSNR | SSIM | LPIPS | tLPIPS | 说明 |
| --- | ---: | ---: | ---: | ---: | --- |
| canonical `baseline_600` | 18.9496 | 0.6653 | 0.4048 | 0.0230 | 主表基线 |
| canonical `planb_init_600` | 20.4488 | 0.7070 | 0.3497 | 0.0072 | ΔPSNR +1.4992，ΔLPIPS -0.0551，ΔtLPIPS -0.0158 |
| seg200_260 `planb_init_600` vs `baseline_600` | 20.0417 vs 18.0468 | 0.6656 vs 0.6353 | 0.3534 vs 0.4138 | 0.0078 vs 0.0234 | ΔPSNR +1.9950，ΔLPIPS -0.0604，ΔtLPIPS -0.0156 |

## 3) anti-cherrypick 摘要（smoke200，planb-baseline）
- seg300_360：ΔPSNR +0.1811，ΔLPIPS -0.0497，ΔtLPIPS -0.0517。
- seg400_460：ΔPSNR +0.1845，ΔLPIPS -0.0481，ΔtLPIPS -0.0516。
- seg600_660：ΔPSNR +0.1905，ΔLPIPS -0.0488，ΔtLPIPS -0.0525。
- seg1800_1860：ΔPSNR +0.1799，ΔLPIPS -0.0489，ΔtLPIPS -0.0549。
- 防守句：seg400_460 与 seg1800_1860 的模板已按同 slice baseline init 重建，仅替换 velocities。

## 4) Scope + Limitations
- Scope：只声明“短预算（600 steps）收敛性与时序稳定性”，不声明 high-fidelity 上限。
- Limitation A：feature-loss v2 已冻结为负结果，不再新增训练。
- Limitation B：Plan-B 与 Feature Loss 组合未测，受预算冻结（新增 full600 `N=0`）约束，列为 future work。

## 5) 会议播放清单（先视频后数字）
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`（canonical）
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`（seg200_260）
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`（可选，或 seg300/600/1800 其一）
- 会议 clips/frames 清单与推荐播放顺序：`notes/planb_meeting_assets_v26_owner_a.md`
- 会议播放 runbook（优先 loop12s 版本）：`notes/planb_meeting_runbook_v26_owner_a.md`
- 定性主图索引：`notes/planb_qualitative_frames_v26_owner_a.md`
- 资产交接说明：`notes/handoff_planb_v26_assets_owner_a.md`

## 6) 证据入口（唯一数字口径）
- `docs/report_pack/2026-02-26-v26/metrics.csv`
- `docs/report_pack/2026-02-26-v26/scoreboard.md`
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`
- 离线证据包：`artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz`
- SHA 索引来源：`artifacts/report_packs/SHA256SUMS.txt` 第 24 行
- Offline bundle (local-only, 若存在)：`artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`；SHA 真源：`notes/planb_meeting_assets_v26_owner_a.md`；校验：`sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`

## 7) Q&A 入口
- `docs/writing/planb_qa_cards_v26.md`
- `docs/writing/planb_onepager_v26.md`
- `docs/writing/planb_talk_outline_v26.md`

## 8) 决议真源
- `docs/decisions/2026-02-26-planb-v26-freeze.md`
