# Feature Metric Loss v2 执行文档（`protocol_v1`，唯一主线）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
唯一真源协议：`docs/protocol.yaml`（-> `docs/protocols/protocol_v1.yaml`）  
路线图真源：`docs/reviews/2026-02-25/final-roadmap-discussion-pack.md`

> 目的：把 “VGGT feature metric loss v2” 从讨论变成可执行工程对象；用 **两次 full600** 在 canonical 上给出“趋势”或“明确失败归因”，并保持证据链可审计可复现。

## 0. 不可违反的硬约束（违反即不可比）

1. **协议纪律（硬约束 A）**
- 任何 feature-loss v2 变体必须在同一套 `protocol_v1` 下对齐 baseline/control。
- 只要改动训练分布项（帧段/相机/scale/step/resolution/densification），必须升级 `protocol_v2.yaml` 并重跑 baseline/control。

2. **成功线与 trade-off（硬约束 B）**
- 主成功线优先级：`tLPIPS`（稳定性）优先，PSNR/LPIPS/SSIM 作为必要对照。
- 若 `tLPIPS` 达标（建议 ≥10% 下降），允许 `PSNR` ≤0.2 dB 退化、`LPIPS` ≤ +0.01 退化，但必须提供“机制解释页 + 失败分析页”。
- 禁止口号化：必须做 `lambda_vggt_feat` 的小范围 sweep，画 **PSNR vs tLPIPS 的 Pareto 图**，选 knee point。

## 1. 固定输入与输出（所有人必须按同一路径跑）

1. canonical 数据：
- `DATA_DIR=data/selfcap_bar_8cam60f`
- cameras：`02-09`（train `02-07` / val `08` / test `09`）
- frames：`[0, 60)`

2. 结果目录规范（必须一致，便于报表聚合）：
- v2（无 gating）：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_600/`
- v2_gated（framediff gating）：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_gated_600/`
- cache：`outputs/vggt_cache/<tag>/`（必须包含 `gt_cache.npz` + `meta.json`）

## 2. v2 规格（拍板版，先保守提高成功率）

### 2.1 phi / layer

1. **默认：stride=16 的中间层表观特征**（作为 v2 第一版）。
2. stride=8 仅作为第二变体：stride16 出趋势后才允许。
3. v2 不以 `depth/world_points` 作为默认 phi（v1 已验证高风险）。

### 2.2 loss（推荐 normalize + cosine）

1. `F_pred_n = F.normalize(F_pred, dim=-1, eps=1e-6)`
2. `F_gt_n = F.normalize(F_gt.detach(), dim=-1, eps=1e-6)`（GT 分支允许 detach）
3. `loss = 1 - (F_pred_n * F_gt_n).sum(dim=-1)`

注意：
- 冻结 VGGT 参数不等于 `torch.no_grad()`。
- **render 分支严禁 `torch.no_grad()`**，否则梯度断（loss 对 Gaussians 不生效）。

### 2.3 sanity（必须具备）

1. GT self-consistency：同一张 `I_gt` 两次预处理+VGGT 的 loss 接近 0。
2. cache round-trip：cache 读出的 `phi(I_gt)` 与在线算的 `phi(I_gt)` 一致（同 meta/同 dtype/同尺寸）。

落地要求：
- 新增脚本：`scripts/check_vggt_preprocess_consistency.py`（输出 PASS/FAIL + 关键统计）。

### 2.4 gating（默认 framediff + top‑p%）

1. 默认 gating：`framediff`。
2. framediff 计算建议：灰度 + 轻微 blur，或 per-frame normalize 后 diff（抗曝光/压缩噪声）。
3. patch 采样建议：不设阈值，使用 **top‑p%**（例如 10%）作为候选区域，再从中采样 patch。
4. “相机运动风险”处理：
- 先做一次性 pose 判定（基于 `sparse/0/images.bin`）：若相机固定，直接 simple diff。
- 只有 pose 明确显示相机在动时，才允许启用更复杂 warp（并必须可回退）。

### 2.5 吞吐纪律（必须证据化）

1. v2 必须记录吞吐（iter/s 或 step time）。
2. 写入 `stats/*_step*.json` 或独立 `throughput.json`（两者择一，但必须落盘）。
3. 止损线：吞吐下降 >2× 且无法通过 `every/patch/分辨率` 降下来则止损。

## 3. Gate 执行与验收（不准跳关）

### Gate M1（工程可控）

目标：v2 端到端可跑 + 可审计 + 200-step 不灾难。

必须交付：
1. cache v2（含 meta：phi/layer/stride/预处理/normalize/dtype/size）。
2. `scripts/check_vggt_preprocess_consistency.py`：PASS。
3. 200-step sanity：
- baseline（已有，可不重跑）
- `feature_loss_v2`（200-step）
- `feature_loss_v2_gated`（200-step）
 - **硬要求：M1 质量判定必须与 `baseline_smoke200` 同 step 对齐比较，禁止拿 smoke200 直接对比 `baseline_600`。**
4. 吞吐对比落盘（证明 ≤2×）。

M1 最短可比跑法（同协议、同 step=200）：
```bash
# 1) baseline smoke200（作为 M1 对照真值）
MAX_STEPS=200 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200 \
  bash scripts/run_train_baseline_selfcap.sh

# 2) feature-loss v2 smoke200
MAX_STEPS=200 RESULT_TAG=feature_loss_v2_smoke200 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh

# 3) feature-loss v2 gated smoke200
MAX_STEPS=200 RESULT_TAG=feature_loss_v2_gated_smoke200 \
  bash scripts/run_train_feature_loss_v2_gated_selfcap.sh
```

M1 跑完后（含 lambda sweep）用一条命令生成对比表 + Pareto：
```bash
python3 scripts/analyze_smoke200_m1.py
```

输出：
- `outputs/report_pack/scoreboard_smoke200.md`（smoke200 全量对比、相对 `baseline_smoke200` 的 delta）
- `Pareto Frontier`（maximize PSNR, minimize tLPIPS 的非支配点）
- `Recommendation`（在阈值约束内的推荐点，便于决定是否进入 full600）

止损条件（M1 就要敢止损）：
- 200-step 出现“明显压死画质”的退化（类似 v1 PSNR 掉到 16 的级别）。
- 吞吐 >2× 且无法通过 `every/patch/分辨率` 控制。

### Gate M2（两次 full600 给趋势或失败归因）

约束：**只允许两次 full600**（避免 3 月把 GPU 烧光）。

必须交付：
- `feature_loss_v2_600`（full600）
- `feature_loss_v2_gated_600`（full600）
- 两条 run 都必须有 `stats/test_step0599.json` + `videos/traj_4d_step599.mp4`。
- 报表刷新：`scripts/build_report_pack.py` + `scripts/summarize_scoreboard.py` + evidence 打包。

成功判据（满足任一条即可）：
- `tLPIPS` 下降 ≥10%（推荐主成功线）
- 或 `LPIPS` 下降 ≥0.01
- 或 `PSNR` +0.2 dB

若以 `tLPIPS` 达标作为成功线，允许 trade-off 见硬约束 B（需 Pareto sweep + 机制解释页）。

失败/止损：
- 连续 2 次 full600 无任何趋势：止损进入失败归因 + Plan‑B 评估。

### Gate M3（anti‑cherrypick）

目标：同场景第二段（`seg200_260`）或第二场景 short-run 的对照证据位。

必须交付（至少其一）：
- seg200_260：baseline vs v2（short-run 允许）
- 第二场景 short-run：baseline vs v2（只做定性+指标）

### Gate M4（写作闭环）

目标：Method / Experiments / Failure cases 初稿。

必须交付：
- 图表均能从 evidence pack 复现（禁止手工改表）。
- failure cases 至少 1 类机制级解释（对齐误差、gating 误判、吞吐 trade-off 等）。

## 4. Plan‑B（战备库存，不跑 GPU）

允许在 M1 期间只做“脚本战备库存”，不运行：
- 预期脚本：`scripts/init_velocity_from_points.py`

纪律：
- 不改 `data/`、不改 `protocol_v1`；输出只写 `outputs/plan_b/...`。
- 脚本必须自检并落盘 `||v||` 分布与时间尺度说明（见 final-roadmap 的 Plan‑B 纪律）。

## 5. 需要落库的“立刻动作清单”（对应外部评审 v1）

1. 新增：`docs/execution/2026-02-26-feature-loss-v2.md`（本文件）
2. 新增 runner（v2 专用）：
- `scripts/run_train_feature_loss_v2_selfcap.sh`
- `scripts/run_train_feature_loss_v2_gated_selfcap.sh`
3. 新增 sanity：
- `scripts/check_vggt_preprocess_consistency.py`
4. 吞吐落盘：
- `stats/*` 或 `throughput.json`
