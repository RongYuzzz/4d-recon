# 4d-recon 项目进度（Progress）

最后更新：2026-02-26  
对照执行计划：`docs/execution/2026-02-12-4d-reconstruction-execution.md`

## 0. 当前状态（一句话）

已完成 **协议 v1 冻结 + Plan‑B pivot（3D velocity init）**；Plan‑B 在 canonical 与 seg200_260（anti‑cherrypick）两段均显著优于 baseline（尤其 tLPIPS 大幅下降），feature-loss v2 主线继续冻结；未来 7 天 full600 预算（N=3）已用尽，进入 Writing Mode 收口与防守材料完善。

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

来源：`docs/report_pack/2026-02-26-v17/metrics.csv`

| 运行 | PSNR | SSIM | LPIPS | tLPIPS | 备注 |
|---|---:|---:|---:|---:|---|
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 | canonical baseline |
| ours_weak_600 | 19.0194 | 0.6661 | 0.4037 | 0.0231 | diff cue（当前默认） |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 | control 目前最好（提示 cue 仍需改进） |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 | **Plan‑B（主线 Go）** |
| ours_strong_v3_gate1_detach0_predpred_600 | 18.9491 | 0.6652 | 0.4072 | 0.0228 | strong v3：tLPIPS 有小幅改善但 LPIPS/PSNR 退化，已 stoploss |
| ours_weak_vggt_w0.3_end200_600 | 18.9808 | 0.6651 | 0.4047 | 0.0245 | VGGT probe：无稳定收益，不建议 protocol_v2 |

补充（seg200_260 anti‑cherrypick，test@599）：
- seg2 baseline_600：PSNR `18.0468` / SSIM `0.6353` / LPIPS `0.4138` / tLPIPS `0.02343`
- seg2 planb_init_600：PSNR `20.0417` / SSIM `0.6656` / LPIPS `0.3534` / tLPIPS `0.00779`

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

- Writing Mode（优先）：
  - 输出定性对比（side-by-side + 抽帧）：`docs/execution/2026-02-26-planb-qualitative.md`
  - 强化 negative result 防守：`notes/feature_loss_v2_failure_attribution_owner_b.md`
- weak 主线风险仍在（作为“方法边界/负增益”证据位保留）：
  - `control_weak_nocue_600` 在 LPIPS 上优于 `ours_weak_600`（见 `docs/report_pack/2026-02-26-v17/scoreboard.md` 风险提示）
  - `planb_ours_weak_smoke200_w0.3_end200` 相对 `planb_init_smoke200` 仅微弱改善（ΔPSNR `+0.0056` / ΔLPIPS `-0.0003` / ΔtLPIPS `+0.00025`），结论 `No-Go`，暂不申请新增 full600（见 `notes/planb_plus_weak_smoke200_owner_a.md`）
- 后续若要继续新增 full600：必须新建决议文件扩预算（否则不可比/不可审计）。

## 7. 2026-02-24 评审拍板（对后续计划的影响）

评审材料已收敛至：`docs/reviews/2026-02-24/`

- `02-25`（protocol v1）不大改：KLT strong 明确降级为 baseline/attempt；weak “无稳定收益（control 更好）”作为关键发现。
- `02-26+` 唯一主线已改为 **Plan‑B**（见 `docs/decisions/2026-02-26-planb-pivot.md`）：triangulation→3D velocity init，48h timebox；feature-loss 主线冻结。
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

## 9. 2026-02-25 Feature-Loss v2 Post-Fix 复核（Owner A，最终判定）

执行基线：
- 分支/工作树：`owner-a-20260226-v2-postfix` / `.worktrees/owner-a-20260226-v2-postfix`
- HEAD：`e761b18`（包含 `d1b95b2` 与 `a859078`）
- 协议：`protocol_v1`（数据/帧段/相机/split 不变）

M1（smoke200 + sweep）：
- baseline：`baseline_smoke200_postfix`
- 主对照：`feature_loss_v2_smoke200_postfix`、`feature_loss_v2_gated_smoke200_postfix`
- sweep：`feature_loss_v2_smoke200_postfix_lam0.005`、`feature_loss_v2_smoke200_postfix_lam0.01`
- 判定：PASS（未出现灾难退化；gated 确认 `has_gate_framediff=True` 且无 fallback）

M2（选择性 full600）：
- 执行：`feature_loss_v2_postfix_600`（`lambda=0.01`）
- 结果：`PSNR=18.6752, LPIPS=0.4219, tLPIPS=0.0261`
- 相对 baseline_600：`ΔPSNR=-0.2744, ΔLPIPS=+0.0172, ΔtLPIPS=+0.0031`
- 结论：无可辩护正向趋势，**不执行第 2 次 gated full600**，判定 **No-Go**。

证据快照：
- `docs/report_pack/2026-02-25-v15/`
- `notes/v2_postfix_preflight_owner_a.md`
- `notes/v2_postfix_m1_owner_a.md`
- `notes/v2_postfix_m2_owner_a.md`

## 10. 2026-02-26 会后决议：Pivot 到 Plan‑B（48h timebox）

决议文件（唯一真源）：
- `docs/decisions/2026-02-26-planb-pivot.md`

会议结论（可执行版）：
- feature‑loss‑v2 主线 **No‑Go 冻结**：禁止新增 feature‑loss full600，仅允许做“无需 full600 的失败归因统计/可视化”用于写作防守。
- **触发 Plan‑B**：`triangulation/*.npy → 3D velocity init`，严格 **48h timebox**，并按 Gate 执行（Day1 smoke200 sanity，Day2 仅 1 次 full600 给 Go/No‑Go）。
- 未来 7 天 full600 预算写死：`N=3`（planb_init_600 + seg200_260 baseline/control）。

执行入口：
- 脚本：`scripts/init_velocity_from_points.py`
- runner：`scripts/run_train_planb_init_selfcap.sh`
- 执行文档：`docs/execution/2026-02-26-planb.md`

执行结果（已闭环）：
- canonical：`planb_init_600` 相对 `baseline_600`：
  - ΔPSNR `+1.4992`，ΔLPIPS `-0.0551`，ΔtLPIPS `-0.0158`
- seg200_260：`planb_init_600` 相对 `baseline_600`：
  - ΔPSNR `+1.9950`，ΔLPIPS `-0.0604`，ΔtLPIPS `-0.01564`
- seg400_460（smoke200，budget-neutral）：`planb_init_smoke200` 相对 `baseline_smoke200`：ΔPSNR `+0.1721`，ΔLPIPS `-0.0438`，ΔtLPIPS `-0.04990`（与 canonical/seg200_260 同向，Gate-S2 PASS）
- seg600_660（smoke200，budget-neutral）：`planb_init_smoke200` 相对 `baseline_smoke200`：ΔPSNR `+0.1905`，ΔLPIPS `-0.0488`，ΔtLPIPS `-0.05252`（与 canonical/seg200_260/seg400_460 同向，Gate-S2 PASS）
- seg1800_1860（smoke200，budget-neutral）：`planb_init_smoke200` 相对 `baseline_smoke200`：ΔPSNR `+0.1285`，ΔLPIPS `-0.0445`，ΔtLPIPS `-0.05327`（与 canonical/seg200_260/seg400_460/seg600_660 同向，Gate-S2 PASS）
- 证据快照：`docs/report_pack/2026-02-26-v19/`
- 关键记录：
  - `notes/planb_gate_b1_owner_a.md`、`notes/planb_gate_b2_owner_a.md`
  - `notes/planb_seg2_gate_s1_owner_a.md`、`notes/planb_seg2_gate_s2_owner_a.md`
  - `notes/anti_cherrypick_seg200_260.md`
  - `notes/anti_cherrypick_seg400_460.md`
  - `notes/anti_cherrypick_seg600_660.md`
  - `notes/anti_cherrypick_seg1800_1860.md`
  - `notes/planb_verdict_writeup_owner_b.md`

预算状态（7 天 full600，N=3）：已用尽（剩余 0）。
