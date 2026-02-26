# 2026-02-26 决议：冻结 Feature‑loss，触发 Plan‑B（3D velocity init）并进入 Writing Mode

日期：2026-02-26  
适用仓库：`/root/projects/4d-recon`  
依据材料：
- `docs/reviews/2026-02-26/meeting-opinions.md`
- `docs/reviews/2026-02-26/meeting-decision.md`

## 1. 背景（触发条件）

在 canonical `protocol_v1` 下，`feature_loss_v2_postfix_600` 相比 `baseline_600` 出现 **PSNR/LPIPS/tLPIPS 三项全劣化**（见 `docs/report_pack/2026-02-25-v15/metrics.csv`、`notes/v2_postfix_summary_owner_a.md`），因此 **feature‑loss‑v2 主线 No‑Go**。

## 2. 最终拍板（唯一主线）

1. **主线切换：立即执行 Plan‑B（triangulation → 3D velocity initialization）**，严格 **48h timebox**。
2. **feature‑loss 主线冻结**：
   - 禁止新增 feature‑loss 相关 full600（以及任何“为了 feature‑loss 继续烧 full600”的扩展）。
   - 允许的动作仅限于：无需 full600 的失败归因可视化与统计（用于写作防守）。
3. **进入 Writing Mode**：后续新增实验以“收口与防守”为主，避免探索性发散。

## 3. full600 预算（未来 7 天写死）

最多 `N=3` 次 full600（不含 smoke200）：

1. `planb_init_600`（必须）
2. `seg200_260_baseline_600`（防守必须）
3. `seg200_260_control_600`（防守建议；如 GPU 不够，可降级为 smoke200，但必须写明理由）

## 4. Plan‑B 验收口径（不改 protocol_v1）

`protocol_v1` 的成功线不动；为 Plan‑B 额外新增一个 **48h 决议口径**（用于 Day2 一次 full600 的 Go/No‑Go）：

1. **Go（满足任一条即可）**
   - `tLPIPS` 相对 `baseline_600` 下降 ≥ 5%，且 PSNR 不劣化超过 0.2 dB
   - 或者：动态区域 ghosting 明显减少（定性），且训练稳定、指标不全线崩
2. **No‑Go**
   - PSNR/LPIPS/tLPIPS 三项全劣化
   - 或训练明显不稳（loss 爆炸、渲染发散、densification 异常等）

## 5. Plan‑B 实施纪律（必须遵守）

1. 不改 `data/`，不改 `protocol_v1`。
2. Plan‑B 的初始化文件输出必须隔离到 `outputs/plan_b/...`，且 **不得覆盖 baseline 的 init**。
3. Plan‑B 脚本必须自检并落盘 `velocity_stats.json`，至少包含：
   - `mean/p50/p90/p99/max(||v||)`
   - `ratio(||v|| < eps)`
   - `Δt` 定义与 velocity 单位说明
   - clip 阈值与匹配率
4. 叙事口径禁用“零速陷阱/零速初始化已被证实”：
   - 改为：**velocity prior 的质量/尺度/一致性不足或噪声过大**，Plan‑B 目标是用更物理一致的 3D 差分修正初始化。

## 6. 48h Gate（执行级）

见执行文档：`docs/execution/2026-02-26-planb.md`

1. Gate‑B1（Day1）：生成 Plan‑B init + 200-step sanity（baseline_init vs planb_init）
2. Gate‑B2（Day2）：仅 1 次 full600（planb_init_600），跑完立刻按 Go/No‑Go 决议口径判断

## 7. 会后立刻动作（避免“拍板不落地”）

1. 新增脚本：`scripts/init_velocity_from_points.py`
2. 新增执行入口：`docs/execution/2026-02-26-planb.md`
3. 将本决议作为后续 7 天的唯一真源（除非新建决议文件升级版本）

