# 4d-recon 项目进度（Progress）

最后更新：2026-02-24  
对照执行计划：`docs/execution/2026-02-12-4d-reconstruction-execution.md`

## 0. 当前状态（一句话）

已完成 **T0 基底审计 PASS**、**T1 闭环跑通**、**协议 v1 冻结**、并已产出 **baseline/ours-weak/control/ours-strong(attempt) 的可复现结果**与 **evidence pack v4**；当前主要瓶颈在 **cue mining 质量与收益（弱融合未稳定优于 baseline）**，strong 线按 stoploss 暂停大投入。

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

来源：`docs/report_pack/2026-02-24-v4/metrics.csv`

| 运行 | PSNR | SSIM | LPIPS | tLPIPS | 备注 |
|---|---:|---:|---:|---:|---|
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 | canonical baseline |
| ours_weak_600 | 19.0194 | 0.6661 | 0.4037 | 0.0231 | diff cue（当前默认） |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 | control 目前最好（提示 cue 仍需改进） |
| ours_strong_600 | 19.0236 | 0.6660 | 0.4094 | 0.0233 | strong attempt；按审计结论建议 stoploss |

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

- 协议内收益线（Weak）：
  - cue mining 质量“可诊断 + 可止损”（A：cue mining v2/质量统计）。
  - anti-cherrypick：同场景第二段 60 帧（seg2）复现实验（A）。
- strong 线（加分项，严格 timebox）：
  - strong v2（pred@t vs pred@t' 一致性、KLT FB check/weight），只做小预算验证，满足止损线立刻回退（B）。
- 汇报交付面：
  - scoreboard 自动生成与 evidence v5 刷新（C）。

