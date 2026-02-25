# Owner B Plan: Ours-Strong v3（伪 mask 门控 + pred_pred detach）+ 72h 止损（两人两 GPU 版）

> 状态：待执行（Next）。本计划默认 **只用 GPU1**；GPU0 留给 Owner A。  
> 背景：Owner C 暂时无法工作；A 负责 report-pack/evidence 接管与 weak(vggt) 探针；B 继续推进 strong 线但必须严格止损，避免拖死主线交付。

## Goal

在不改 `docs/protocol.yaml (v1)` 的前提下，给出一个**可审计**的 `Ours-Strong v3` 尝试：

1. 增强 strong 线的“可辩护性”：用 **pseudo mask（dynamicness）对 temporal correspondences 做门控**，减少动态区域错误 correspondence 对训练的破坏。
2. 提供 `pred_pred` 模式的一个更稳选项：**detach target**（避免两次渲染同时被拉扯导致不稳定）。
3. 产出至少 1 个 full600 run（或触发止损的完整失败证据），并写清结论与回退。

## Non-Goal

- 不动 weak 线（`pseudo mask` 生成与 weak 训练由 A/既有脚本负责）。
- 不升级 protocol（不新建 `protocol_v2`，不改帧段/相机 split/超参冻结项）。
- 不做 feature-loss 大改（已有 v1 尝试已止损；本轮聚焦 strong v3）。
- 不把 `outputs/`、`data/`、`artifacts/*.tar.gz` 入库。

## Parallel Safety（并发约束）

- B 只触碰：
  - `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
  - `scripts/run_train_ours_strong_selfcap.sh`
  - `scripts/tests/test_strong_fusion_flags.py`（必要时）
  - 新增 `notes/ours_strong_v3_gated_attempt.md`
- B 不触碰 `docs/report_pack/*`、`artifacts/report_packs/*`（A 在接管打包）。

---

## Task B41：建立隔离 worktree（避免污染 main）

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-b-20260225-strong-v3 .worktrees/owner-b-20260225-strong-v3 main
git -C .worktrees/owner-b-20260225-strong-v3 status --porcelain=v1
```

Expected:
- worktree 干净（无输出）

---

## Task B42：实现 strong v3 两个新开关（默认关闭，不影响现有结果）

### B42.1 新增 config/flags（trainer）

在 `TrainConfig` 增加（默认均关闭）：
- `temporal_corr_gate_pseudo_mask: bool = False`
  - 含义：对每条 correspondence 的权重做 `w *= (1 - mask_dyn(src))` 门控（src 同帧同相机）。
- `temporal_corr_pred_pred_detach_target: bool = False`
  - 含义：当 `temporal_corr_loss_mode=pred_pred` 时，将 `target` 做 `.detach()`，只让梯度从 `pred_src` 回传。

实现位置建议：
- 门控：`_compute_temporal_corr_loss()` 内部，在 `w` 与 `diff` 相乘前。
- detach：`loss_mode == "pred_pred"` 分支内构造 `target` 后。

验收：
- 默认不开启时，行为与当前 `main` 完全一致（baseline/weak/已有 strong 不受影响）。
- 若开启门控但 pseudo mask 未加载（例如未传 `--pseudo-mask-*`），打印一次 warning 并自动降级为不门控（不要 silent wrong）。

### B42.2 runner 脚本透传（scripts）

修改 `scripts/run_train_ours_strong_selfcap.sh`：
- 新增 env：
  - `TEMPORAL_CORR_GATE_PSEUDO_MASK`（默认 0）
  - `TEMPORAL_CORR_PRED_PRED_DETACH_TARGET`（默认 0）
- 对应透传 trainer flags：
  - `--temporal-corr-gate-pseudo-mask`
  - `--temporal-corr-pred-pred-detach-target`

### B42.3 单测/契约（必须）

更新 `scripts/tests/test_strong_fusion_flags.py`：
- 断言 run script 与 trainer 中存在上述新 token（最少保证“接口存在，默认关闭”）。

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-strong-v3
python3 scripts/tests/test_strong_fusion_flags.py
python3 scripts/tests/test_temporal_correspondences_klt_contract.py
python3 scripts/tests/test_run_pipeline_env_flags.py
```

Expected:
- PASS（不引入回归）

---

## Task B43：GPU1 200-step sanity（挑 1-2 个组合，别做大 sweep）

目标：只看“会不会更稳 + 不会明显退化”，不追求最终指标。

固定（对齐 protocol v1）：
- `DATA_DIR=data/selfcap_bar_8cam60f`
- `START_FRAME=0 END_FRAME=60`
- `KEYFRAME_STEP=5 GLOBAL_SCALE=6 SEED=42`
- `EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1`

组合 1（推荐优先跑）：`pred_pred + detach + gate_mask`
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-strong-v3

GPU=1 MAX_STEPS=200 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/sweeps/selfcap_bar_strong_v3_gate1_detach1_predpred_s200 \
TEMPORAL_CORR_LOSS_MODE=pred_pred \
TEMPORAL_CORR_GATE_PSEUDO_MASK=1 \
TEMPORAL_CORR_PRED_PRED_DETACH_TARGET=1 \
LAMBDA_CORR=0.01 TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
bash scripts/run_train_ours_strong_selfcap.sh
```

组合 2（对照）：`pred_pred + no_detach + gate_mask`
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-strong-v3

GPU=1 MAX_STEPS=200 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/sweeps/selfcap_bar_strong_v3_gate1_detach0_predpred_s200 \
TEMPORAL_CORR_LOSS_MODE=pred_pred \
TEMPORAL_CORR_GATE_PSEUDO_MASK=1 \
TEMPORAL_CORR_PRED_PRED_DETACH_TARGET=0 \
LAMBDA_CORR=0.01 TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
bash scripts/run_train_ours_strong_selfcap.sh
```

验收：
- 两个目录都产出 `stats/test_step0199.json` 与 `videos/traj_4d_step199.mp4`
- 训练无 NaN/崩溃；吞吐开销不要超过 2x（粗看 wall-time/step 即可）

记录：
- 新增 `notes/ours_strong_v3_gated_attempt.md`：写下每个 run 的命令、指标（PSNR/SSIM/LPIPS/tLPIPS）与肉眼现象。

---

## Task B44：GPU1 full600（只跑 1 个 best 候选；否则触发止损）

选择规则（200-step 之后当场拍板）：
- 优先看 `tLPIPS` 是否有下降趋势（或至少不恶化）
- 若两者都无趋势：直接止损，不跑 full600

Run（示例，按 B43 结果选其一）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-strong-v3

GPU=1 MAX_STEPS=600 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach1_predpred_600 \
TEMPORAL_CORR_LOSS_MODE=pred_pred \
TEMPORAL_CORR_GATE_PSEUDO_MASK=1 \
TEMPORAL_CORR_PRED_PRED_DETACH_TARGET=1 \
LAMBDA_CORR=0.01 TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
bash scripts/run_train_ours_strong_selfcap.sh
```

验收：
- `stats/test_step0599.json` 与 `videos/traj_4d_step599.mp4` 存在
- `test_step0599.json` 含 `tlpips` 字段

---

## Task B45：止损判定（必须写死，避免无限试）

止损条件（满足任一条立刻停）：
- full600 未达到任一“成功线”：
  - `tLPIPS` 相对 `ours_weak_600` 下降 ≥ 10%
  - 或 `LPIPS` 下降 ≥ 0.01
  - 或 `PSNR` 提升 ≥ 0.2 dB
- 或 1k-2k steps 内出现明显不稳定趋势（loss 爆、render 明显更闪、densification 异常）。

回退产物（失败也必须交付）：
- 至少 1 份 correspondence 可视化（来自 `outputs/correspondences/.../viz/`）
- 训练曲线/日志片段（写在 `notes/ours_strong_v3_gated_attempt.md`）
- “为什么不可辩护”的一句话归因（例如对应错位/动态区域污染/梯度互拉等）

---

## Task B46：合入 main（只合代码/文档，不合产物）

提交内容：
- 代码：trainer + runner + tests
- 文档：`notes/ours_strong_v3_gated_attempt.md`

合入前检查：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-strong-v3
python3 scripts/tests/test_*.py
git status --porcelain=v1
```

交接给 A（用于打包/报表刷新）：
- 给出最终 full600 的 `RESULT_DIR` 路径（或明确“已止损，无 full600”）。

