# Meeting Index v26 (Start Here)

## Start Here (2 min)
- 首先阅读：
  - `docs/reviews/2026-02-26/meeting-checklist-v26.md`
  - `docs/reviews/2026-02-26/meeting-handout-v26.md`
- 该 handout 是会前统一口径单文件：结论、关键数字、播放顺序、证据入口都已收口。

## Presenter Pack
- `docs/writing/planb_talk_outline_v26.md`
- `docs/writing/planb_qa_cards_v26.md`
- `notes/planb_meeting_assets_v26_owner_a.md`
- `notes/planb_meeting_runbook_v26_owner_a.md`
- Offline bundle (local-only, 若存在)：`artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`；SHA 真源：`notes/planb_meeting_assets_v26_owner_a.md`；校验：`sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`
- 播放策略：若 `outputs/qualitative/planb_vs_baseline/clips_v26_looped/` 存在，优先使用 loop12s 版本。

## Evidence Source of Truth
- `docs/decisions/2026-02-26-planb-v26-freeze.md`（唯一决议真源）
- `docs/report_pack/2026-02-26-v26/metrics.csv`
- `docs/report_pack/2026-02-26-v26/scoreboard.md`
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`

## Key Deltas
- 统一定义：`Δ = planb - baseline`。
- full600 口径：主结论来自 canonical + seg200_260（step=599, stage=test）。
- smoke200 口径：用于 anti-cherrypick 稳健性补强（step=199, stage=test）。
- 报告时禁止把 smoke200 与 full600 混为同一预算结论。

## No-New-Training Rule
- 冻结期纪律：新增 full600 预算 `N=0`。
- 不新增 smoke200/full600，不运行 `run_train_*.sh`。
- 仅允许 docs/notes 入口整理与引用接线，不生成新 vXX report-pack。
