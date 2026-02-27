# Plan-B v26 一页纸（Writing Mode，No-GPU）

## 1) 当前进度（v26 冻结态）
- `full600`：canonical 与 seg200_260 主表已齐；`baseline_600`、`planb_init_600`、`feature_loss_v2_postfix_600` 已有可复述结论（来源：`docs/report_pack/2026-02-26-v26/scoreboard.md`、`metrics.csv`）。
- `smoke200 anti-cherrypick`：seg300/400/600/1800 全部完成且方向一致（来源：`docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`）。
- `template hygiene + qualitative + ablation`：已完成重模板口径与 side-by-side 资产整理，写作入口聚合到 `docs/writing/`。

## 2) 当前路线选择（写死）
- 主线：Plan-B only（仅替换 init velocities，不改 `protocol_v1`）。
- 冻结：feature-loss v2 = No-Go；Plan-B + weak = No-Go。
- 预算纪律：新增 full600 `N=0`，本阶段仅做 No-GPU 写作与证据整理。

## 3) 三行关键数据（会中可直接念）
| Slice / Run | PSNR | SSIM | LPIPS | tLPIPS | 备注 |
| --- | ---: | ---: | ---: | ---: | --- |
| canonical `baseline_600` | 18.9496 | 0.6653 | 0.4048 | 0.0230 | 主表基线 |
| canonical `planb_init_600` | 20.4488 | 0.7070 | 0.3497 | 0.0072 | 相对 baseline：ΔPSNR +1.4992，ΔLPIPS -0.0551，ΔtLPIPS -0.0158 |
| canonical `feature_loss_v2_postfix_600` | 18.6752 | 0.6562 | 0.4219 | 0.0261 | 相对 baseline 三项退化 |
| seg200_260 `planb_init_600` vs `baseline_600` | 20.0417 vs 18.0468 | 0.6656 vs 0.6353 | 0.3534 vs 0.4138 | 0.0078 vs 0.0234 | ΔPSNR +1.9950，ΔLPIPS -0.0604，ΔtLPIPS -0.0156 |

## 4) anti-cherrypick 摘要（smoke200，planb-baseline）
- seg300_360：ΔPSNR +0.1811，ΔLPIPS -0.0497，ΔtLPIPS -0.0517。
- seg400_460：ΔPSNR +0.1845，ΔLPIPS -0.0481，ΔtLPIPS -0.0516。
- seg600_660：ΔPSNR +0.1905，ΔLPIPS -0.0488，ΔtLPIPS -0.0525。
- seg1800_1860：ΔPSNR +0.1799，ΔLPIPS -0.0489，ΔtLPIPS -0.0549。
- 防守句：seg400_460 与 seg1800_1860 已做 template hygiene（同 slice baseline init 模板，仅替换 velocities）。

## 5) Scope 声明
- 本阶段仅声明“短预算（600 steps）下的收敛性与时序稳定性改进”，不声明高保真上限。
- 会议策略：先视频证据，再表格数字，最后才讨论限制项。

## 6) Limitations（必须先说）
- 未测 Plan-B + Feature Loss 组合；原因是预算冻结（新增 full600 `N=0`），写作中标为 future work。
- feature-loss v2 保留为负结果边界材料，不再作为主线推进对象。

## 7) 证据入口（唯一口径）
- `docs/report_pack/2026-02-26-v26/metrics.csv`
- `docs/report_pack/2026-02-26-v26/scoreboard.md`
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`
- 离线 tar：`artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz`
- SHA 来源：`artifacts/report_packs/SHA256SUMS.txt` 第 24 行（`43e04974f95d4628c02cc7b65e5fbf44db4fd82329e306ec082a57dd90102536`）。
- Offline bundle (local-only, 若存在)：`artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`；SHA 真源：`notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`；校验：`sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`

## 8) 会议播放清单（先视频后数字）
- 必播 1：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`（canonical）。
- 必播 2：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`（seg200_260）。
- 任选 1：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`（或 seg300/600/1800 任一 smoke200）。
- 会议短片（12s 版本）与推荐播放顺序：`notes/planb_meeting_assets_v26_owner_a.md`。
- 会议播放 runbook（优先 loop12s 版本）：`notes/planb_meeting_runbook_v26_owner_a.md`。

## Owner A 接入口（已接线）
- 审计摘要：`notes/planb_v26_audit_owner_a.md`
- Table-1 摘要表：`notes/planb_table1_v26_owner_a.md`
- 定性主图/抽帧索引：`notes/planb_qualitative_frames_v26_owner_a.md`
- 资产与使用说明：`notes/handoff_planb_v26_assets_owner_a.md`
