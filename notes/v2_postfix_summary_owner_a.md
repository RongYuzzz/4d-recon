# Feature-Loss v2 Post-Fix 复核总结（Owner A）

## 最终结论

- **Go/No-Go：No-Go（当前不建议继续该 v2 配置线作为主线）**
- 原因：在 post-fix 主线代码上，虽然 M1 smoke200 全部可控并通过，但 full600 主判据仍未形成优于 `baseline_600` / `control_weak_nocue_600` 的可辩护趋势。

## 关键判定依据

1. M1（200-step）：
- 非灾难退化，吞吐可控，gated 生效（`has_gate_framediff=True`，无 fallback）。
- `lambda` 两点 sweep（0.005 / 0.01）均未出现灾难。

2. M2（full600）：
- 已执行 `feature_loss_v2_postfix_600`（`lambda=0.01`）。
- test@599 指标：`PSNR=18.6752, LPIPS=0.4219, tLPIPS=0.0261`。
- 相对 `baseline_600`：`ΔPSNR=-0.2744, ΔLPIPS=+0.0172, ΔtLPIPS=+0.0031`。
- 不满足“可辩护正向趋势”，按计划不再执行第 2 次 gated full600。

## 本次 run 目录清单

- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_postfix`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200_postfix`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_gated_smoke200_postfix`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200_postfix_lam0.005`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200_postfix_lam0.01`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600`

## 证据与快照

- 文本快照：`docs/report_pack/2026-02-25-v15/`
- Evidence tar：`artifacts/report_packs/report_pack_2026-02-25-v15.tar.gz`
- SHA 登记：`artifacts/report_packs/SHA256SUMS.txt`

## 建议后续动作（供 B/后续计划使用）

- 进入失败归因与替代路径评估（Plan‑B 或新的 v2 参数/机制设计），避免在当前配置继续烧 full600 预算。
