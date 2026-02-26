# Failure Cases (Writing Defense Update, 2026-02-26)

本文件用于 02-26 版本的失败分析与答辩防守文本，随 `scripts/pack_evidence.py` 打包（`outputs/report_pack/`）。

## Case 1: feature-loss v2 在 canonical 上全维退化（已冻结）

- 现象：`feature_loss_v2_postfix_600` 相比 `baseline_600` 未形成可辩护趋势（见快照指标与 meeting decision）。
- 当前处理：主线 No-Go，停止新增 feature-loss full600。
- 防守口径：该结果不能被简单解释为“实现 bug”，需用最小归因包继续排除实现级风险。

## Case 2: 风险信号来自 control vs weak 的对照

- 现象：在 canonical slice，`control_weak_nocue_600` 的 LPIPS 优于 `ours_weak_600`（见 `outputs/report_pack/scoreboard.md` 风险提示）。
- 含义：当前 cue/注入路径可能出现负增益，提示方法设计边界，而非仅靠调参可解。

## Case 3: Plan-B 不等于“速度为 0 问题修复”

- 禁用表述：不要写“零速陷阱已证实”。
- 统一表述：Plan-B 旨在缓解 **velocity prior 质量/尺度/一致性不足或噪声过大** 导致的 ghosting 与时序不稳。
- 证据：`planb_init_600` 在 canonical 指标显著改善，且 seg200_260 控制组补充了 anti-cherrypick 侧证。

## Case 4: 失败归因最小包（No-GPU）执行入口

按 `notes/feature_loss_failure_attribution_minpack.md` 的 5 项执行：

1. loss 量级曲线（TB scalars CSV/PNG）
2. cache round-trip 一致性
3. 1-2px 平移敏感性（可选）
4. gating/patch 命中率热图（待补）
5. 梯度链 10-step 检查

目标：形成“已排除实现级错误 / 仍存在方法边界”的可辩护负结果链路。
