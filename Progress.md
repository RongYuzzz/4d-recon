# 4d-recon 项目进度（Progress）

最后更新：2026-02-25  
对照执行计划：`docs/execution/2026-02-12-4d-reconstruction-execution.md`

## 0. 当前状态（一句话）

已完成 **协议 v1 冻结 + A/B 双人接管**；B 已将 **VGGT feature-loss v2**（含 `token_proj` 对齐修复与更保守默认）合入 `main`；A 已在旧提交 `2948fa0` 上完成 v2 **M1/M2 复跑闭环**（M1 PASS、M2 FAIL 并 stoploss，结论仅作 pre-fix 失败证据），当前待在 `origin/main`（>=`d1b95b2`/`a859078`）上决定是否重跑以形成最终结论。

## 1. 与原执行计划的关键差异（已记录且可辩护）

- 数据集选择从“Neural3DV 最小子集”切换为 **SelfCap (bar-release)**：
  - 原因：项目实际输入契约需要 `COLMAP sparse + per-frame triangulation/*.npy`，SelfCap 更接近该契约且可 HF 下载。
  - Canonical 数据已锁定为 `data/selfcap_bar_8cam60f`（8 cams × 60 frames）。
- 评测口径从“临时脚本/随手跑”升级为 **冻结协议文件**：
  - 唯一真源：`docs/protocol.yaml` -> `docs/protocols/protocol_v1.yaml`。
- strong 融合从“VGGT attention 对应”先降级为 **KLT temporal correspondence** 的可审计实现：
  - 目的：先让 strong 线端到端可跑、可复现、可止损；后续再做 strong v2/更严谨对应。

## 2. 冻结协议（Protocol v1）

文件：`docs/protocol.yaml`（symlink 到 `docs/protocols/protocol_v1.yaml`）

- 数据：`data/selfcap_bar_8cam60f`
- 帧段：`frame000000`–`frame000059`（60 帧）
- 相机：`02`–`09`（8 cams）
- Split：train=`02`–`07`（6 cams），val=`08`（1 cam），test=`09`（1 cam）
- 关键超参：`seed=42`、`keyframe_step=5`、`global_scale=6`、`max_steps_full=600`、`image_downscale=2`
- 指标（test）：PSNR / SSIM / LPIPS + **tLPIPS**

## 3. 可复现入口（脚本）

- 数据适配（SelfCap -> FreeTimeGS 输入）：`scripts/adapt_selfcap_release_to_freetime.py`
- 一键 MVP 复现（含自动适配）：`scripts/run_mvp_repro.sh`
- 协议 v1 训练入口：
  - baseline：`scripts/run_train_baseline_selfcap.sh`
  - ours-weak：`scripts/run_train_ours_weak_selfcap.sh`
  - control（weak 结构但无 cue）：`scripts/run_train_control_weak_nocue_selfcap.sh`
  - ours-strong（attempt + audit）：`scripts/run_train_ours_strong_selfcap.sh`
- 报表与证据链：
  - 产出 `metrics.csv`：`scripts/build_report_pack.py`
  - 打包 evidence tar：`scripts/pack_evidence.py`

## 4. 当前结果摘要（Protocol v1，test@step599）

来源：`docs/report_pack/2026-02-25-v13/metrics.csv`

| 运行 | PSNR | SSIM | LPIPS | tLPIPS | 备注 |
|---|---:|---:|---:|---:|---|
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 | canonical baseline |
| ours_weak_600 | 19.0194 | 0.6661 | 0.4037 | 0.0231 | diff cue（当前默认） |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 | control 目前最好（提示 cue 仍需改进） |
| ours_strong_v3_gate1_detach0_predpred_600 | 18.9491 | 0.6652 | 0.4072 | 0.0228 | strong v3：tLPIPS 有小幅改善但 LPIPS/PSNR 退化，已 stoploss |
| ours_weak_vggt_w0.3_end200_600 | 18.9808 | 0.6651 | 0.4047 | 0.0245 | VGGT probe：无稳定收益，不建议 protocol_v2 |

## 5. 对照执行计划：Task 1–11 完成情况

对照：`docs/execution/2026-02-12-4d-reconstruction-execution.md`

| 执行计划任务 | 状态 | 证据/产物（路径） |
|---|---|---|
| Task 1 建工作区 + 固化基底版本 | DONE | `third_party/FreeTimeGsVanilla/`、`notes/decision-log.md` |
| Task 2 环境 + 最小数据能跑 | DONE | `.venv`、`data/selfcap_bar_8cam60f`、`scripts/run_mvp_repro.sh` |
| Task 3 T0-1 零速度退化 | DONE | `scripts/run_t0_zero_velocity.sh`、`outputs/t0_zero_velocity/` |
| Task 4 T0-2 时间尺度一致性审计 | DONE（以 T0 debug 日志覆盖） | trainer `--t0-debug-interval` 日志、`notes/decision-log.md`、`scripts/t0_grad_check.md` |
| Task 5 T0-3 梯度链路检查 | DONE | `scripts/t0_grad_check.md`、`outputs/t0_selfcap/*/t0_grad.csv` |
| Task 6 T0-4 duration 窗口 + densification 继承 | PARTIAL / NOT BLOCKING | 当前 `default_keyframe_small` 在 600-step 预算内禁用标准 densification（`refine_start_iter=100000`）；若后续启用 split/clone 需补齐继承断言与可视化 |
| Task 7 T0 Go/No-Go 与切换决策 | DONE（Go） | `notes/decision-log.md`（T0 结论：PASS） |
| Task 8 模块A（cue mining） | PARTIAL | `scripts/cue_mining.py`（diff 后端可跑）、`notes/cue_mining_spec.md`、`notes/vggt_setup.md`（VGGT 后端仍待稳定/止损） |
| Task 9 模块B（baseline + weak 融合闭环） | DONE | `scripts/run_train_*_selfcap.sh`、`outputs/protocol_v1/selfcap_bar_8cam60f/*_600/` |
| Task 10 模块C（strong 融合最小实现） | DONE（attempt + audit，已止损） | `scripts/extract_temporal_correspondences_klt.py`、`notes/ours_strong_attempt_selfcap_bar.md`、`outputs/correspondences/selfcap_bar_8cam60f_klt/` |
| Task 11 证据打包（表/消融/demo/失败分析） | DONE（v4） | `docs/report_pack/2026-02-24-v4/`、`artifacts/report_packs/report_pack_2026-02-24-v4.tar.gz`、`artifacts/report_packs/SHA256SUMS.txt` |

## 6. 当前待办（按优先级）

- weak 主线风险仍在：
  - `control_weak_nocue_600` 仍优于 `ours_weak_600`，需要更合理 cue / 注入策略。
- strong 主线已冻结：
  - `ours_strong_v3_gate1_detach0_predpred_600` 触发 stoploss（trade-off 不可接受），暂不扩展算力。
- 下一步负责人（B）：
  - 继续“weak 的更合理 cue/注入”或“更强但可解释的 strong”探索，参考 `docs/plans/2026-02-25-owner-b-strong-v3-gated-corr-stoploss.md`。

## 7. 2026-02-24 评审拍板（对后续计划的影响）

评审材料已收敛至：`docs/reviews/2026-02-24/`

- `02-25`（protocol v1）不大改：KLT strong 明确降级为 baseline/attempt；weak “无稳定收益（control 更好）”作为关键发现。
- `02-26+` 唯一主线：VGGT **feature metric loss**（离线 GT cache + 训练时低频/低分辨率/patch）。
- Plan‑B（触发式救火开关，不并行）：triangulation→粗 3D velocity 初始化，48h timebox。
- 强制新增两页诊断证据：`||v||` 分布统计 + cue 对齐 overlay（用于防守“zero velocity 死路”等攻击点）。

## 8. 2026-02-25 Feature-Loss v2 复跑闭环（Owner A，pre-fix 证据）

说明：
- 该次 v2 full600 运行发生在 `2948fa0`，**早于** `d1b95b2`（`token_proj` resize 对齐修复）与 `a859078`（更保守 runner 默认值 + baseline_smoke200 口径修订）。
- 因此本节结论仅作为 **pre-fix 失败证据**，不可直接作为 v2 的最终 Go/No-Go 判决（需在新 `main` 上复核）。

Gate M1（200-step，对齐 baseline_smoke200）：
- baseline_smoke200：PSNR 12.6315 / LPIPS 0.63023 / tLPIPS 0.08774
- v2_smoke200：PSNR 12.5438 / LPIPS 0.62999 / tLPIPS 0.08326
- v2_gated_smoke200：PSNR 12.5357 / LPIPS 0.63067 / tLPIPS 0.08337
- gated 生效证据见：`notes/v2_m1_results_owner_a.md`（`has_gate_framediff=True`，无 v1 fallback）

Gate M2（full600，两次上限；按成功线止损）：
- v2_600：PSNR 15.9437 / LPIPS 0.4996 / tLPIPS 0.0462
- v2_gated_600：PSNR 15.1714 / LPIPS 0.5140 / tLPIPS 0.0507
- 相对 baseline_600 出现显著退化，按 `docs/execution/2026-02-26-feature-loss-v2.md` 触发 stoploss。

文本快照与运行记录：
- `docs/report_pack/2026-02-25-v14/`
- `notes/v2_m1_preflight_owner_a.md`
- `notes/v2_m1_results_owner_a.md`
- `notes/v2_m2_results_owner_a.md`
