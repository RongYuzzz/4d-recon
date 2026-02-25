# Feature-Loss v2（VGGT token_proj）A/B 工作整合记录（2026-02-25）

目的：把 Owner A（GPU 复跑）与 Owner B（No-GPU 工程落地/修复）两条线的产出收敛成同一条可审计证据链，避免口径漂移。

## 1) B 线（工程与修复，已合入 main）

1. v2 端到端工程链路（runner/cache/trainer/scoreboard）：
- runner：`scripts/run_train_feature_loss_v2_selfcap.sh`、`scripts/run_train_feature_loss_v2_gated_selfcap.sh`
- cache v2：`scripts/precompute_vggt_cache.py`（支持 `token_proj` + `gate_framediff`）
- trainer v2：`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- scoreboard：`scripts/summarize_scoreboard.py`
- sanity：`scripts/check_vggt_preprocess_consistency.py`

2. 高风险一致性修复（必须记入审计）：
- `token_proj` 的 trainer 侧 `phi_render` 计算与 cache 的 downscale 对齐：先投影到原 patch 网格，再 `bilinear resize` 到 cache `phi_size`。
- 单测锁死：`scripts/tests/test_token_proj_resize_alignment.py`

3. 更保守的 M1 默认值（降低灾难退化概率）：
- runner 默认：`LAMBDA_VGGT_FEAT=0.01`、`VGGT_FEAT_RAMP_STEPS=400`、`TOKEN_LAYER_IDX=17`
- 执行口径：`docs/execution/2026-02-26-feature-loss-v2.md`（M1 必须对齐 `baseline_smoke200`）

## 2) A 线（GPU 复跑，证据与结论）

Owner A 在干净 worktree 上完成了 v2 的 M1/M2 复跑闭环，并生成文本快照与 notes：
- 预检：`notes/v2_m1_preflight_owner_a.md`
- M1：`notes/v2_m1_results_owner_a.md`
- M2：`notes/v2_m2_results_owner_a.md`
- 报表快照：`docs/report_pack/2026-02-25-v14/`

关键限制（必须同时声明）：
- A 的 full600 运行发生在提交 `2948fa0`，早于 B 的 `d1b95b2`（token_proj 对齐修复）与 `a859078`（runner 更保守默认值）。
- 因此：A 的 M2 FAIL 结论应被视为 **pre-fix 失败证据**，不能直接作为 v2 最终 Go/No-Go 判决。

## 3) 当前“可对外复述”的整合口径

1. 我们已经把 feature-loss v2 变成了“可执行的工程对象”，并用单测锁死了最关键的 token_proj 对齐语义。
2. 在旧版本上做过一次 M1/M2 端到端复跑：M1 可控、但 M2 在 full600 明显退化并触发 stoploss。
3. 下一步不再“凭感觉”追加 full runs；如需继续，必须在包含 `d1b95b2`/`a859078` 的 `origin/main` 上按同协议复核。

