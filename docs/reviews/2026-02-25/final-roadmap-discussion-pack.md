# 后续推进讨论包（聚焦最终完成，而非中期汇报）

日期：2026-02-25  
主阵地：`/root/projects/4d-recon`  
当前唯一真源协议：`docs/protocol.yaml`（-> `docs/protocols/protocol_v1.yaml`）

## 0. 一页拍板清单（建议会议前 5 分钟就定掉）

> 目的：减少“讨论很久但不落地”的风险。下面每条都给推荐项，专家只需要确认/否决。

1. **唯一主线（02-26+）**：VGGT feature metric loss v2（推荐：YES）
2. **主叙事优先级**：主打“短时稳定性（tLPIPS / flicker / ghosting）”，PSNR/LPIPS 作为必要对照（推荐：YES）
3. **协议纪律**：`protocol_v1` 继续冻结；如需改动必须新建 `protocol_v2.yaml` 并重跑 baseline/control（推荐：YES）
4. **weak 路线是否继续投入 GPU**：停止在 canonical 上做 `PSEUDO_MASK_WEIGHT/END_STEP` 大 sweep（已止损）；weak 仅保留为对照与“关键发现”（推荐：YES）
5. **strong 路线定位**：timebox 加分项，不拖主线（推荐：YES）
6. **反 cherry-pick 口径**：优先采用 “second segment（seg200_260）” 作为附录证据，同时准备“第二场景 short-run”作为备份（推荐：YES）
7. **是否提前开 `protocol_v2`（更长预算/启用 densification/更大分辨率）**：02-26～03-08 阶段不建议开（会成倍增加 baseline 重跑成本）；等 feature-loss v2 出趋势后再决定（推荐：先 NO）

## 1. 本次讨论目标（请专家当场拍板）

1. **冻结 02-26+ 的唯一主线**：是否确认采用 **VGGT feature metric loss** 作为后续推进主线（推荐）。
2. **冻结“成功线/止损线”**：用同一套 protocol 与预算，什么算“可辩护的收益”，什么算“必须止损回退”。
3. **冻结“最终交付口径”**：最终项目的核心 claim 是“短时稳定性/减少 flicker/ghosting”还是“更高重建质量”，以及需要哪些必交实验来防 cherry-pick。

> 说明：我们现阶段最大的风险不是工程跑不通，而是**不断换帧段/换相机/换 scale/换 keyframe_step**导致所有对比不可比。后续必须通过“协议版本化 + evidence 固化”来约束漂移。

## 2. 当前项目状态（可直接给专家快速对齐）

### 2.1 已冻结的评测协议（Protocol v1）

文件：`docs/protocols/protocol_v1.yaml`

- 数据：`data/selfcap_bar_8cam60f`（SelfCap bar，8 cams x 60 frames）
- 帧段：`frame000000`–`frame000059`（60 帧）
- 相机：`02`–`09`
- split：train `02-07` / val `08` / test `09`
- 关键超参（冻结）：`seed=42`、`keyframe_step=5`、`global_scale=6`、`max_steps_full=600`、`image_downscale=2`
- 指标：PSNR / SSIM / LPIPS + **tLPIPS**（test cam 连续帧 flicker）

### 2.2 证据链与复现入口（已具备）

- 工程基底版本已固化（用于可追溯）：见 `notes/decision-log.md`（FreeTimeGsVanilla 主分支快照 commit hash 已记录）。
- 一键数据适配：`scripts/adapt_selfcap_release_to_freetime.py`（输入 `data/selfcap/bar-release.tar.gz`）
- 训练入口：
  - baseline：`scripts/run_train_baseline_selfcap.sh`
  - ours-weak：`scripts/run_train_ours_weak_selfcap.sh`
  - control（weak 结构但无 cue）：`scripts/run_train_control_weak_nocue_selfcap.sh`
  - strong（attempt + audit）：`scripts/run_train_ours_strong_selfcap.sh`
  - feature metric loss v1：`scripts/run_train_feature_loss_selfcap.sh`
- 报表与证据包：
  - `scripts/build_report_pack.py` -> `outputs/report_pack/metrics.csv`
  - `scripts/summarize_scoreboard.py` -> `outputs/report_pack/scoreboard.md`
  - `scripts/pack_evidence.py` -> `artifacts/report_packs/report_pack_*.tar.gz`（tar.gz 不入库，sha 入库）

### 2.3 当前最关键的观测（决定后续方向）

当前 canonical 下（test@599）的结果摘要来自：`docs/report_pack/2026-02-25-v13/metrics.csv`：

| run | PSNR | SSIM | LPIPS | tLPIPS | 结论 |
| --- | ---: | ---: | ---: | ---: | --- |
| `baseline_600` | 18.9496 | 0.6653 | 0.4048 | 0.0230 | baseline |
| `ours_weak_600` | 19.0194 | 0.6661 | 0.4037 | 0.0231 | weak（mask reweight）无稳定优势 |
| `control_weak_nocue_600` | 19.1099 | 0.6674 | 0.4033 | 0.0236 | **control 优于 ours_weak（风险信号）** |
| `ours_strong_v3_gate1_detach0_predpred_600` | 18.9491 | 0.6652 | 0.4072 | 0.0228 | tLPIPS 小降但 LPIPS/PSNR 退化，已 stoploss |
| `feature_loss_v1_600` | 16.0347 | 0.6061 | 0.4927 | 0.0443 | 显著退化（止损） |
| `feature_loss_v1_retry_lam0.005_s200_600` | 19.0555 | 0.6644 | 0.4054 | 0.0239 | 接近 baseline，但无可辩护收益趋势 |

结论含义（给专家的“硬逻辑”）：
- **mask 级 cue + photometric reweight（weak）目前要么无效，要么在拖后腿**（control 更好）。
- KLT strong 已降级为 bridge/attempt，继续堆 strong 工程会被质疑“创新点悬空”。
- 因此后续必须把 VGGT 从“mask 工具人”提升到“可辩护 prior”，最短路径是 **feature metric loss**（但需要 v2 规格，v1 失败不代表路线错）。

### 2.4 关键补充进度（对“完成项目”很关键）

1. **v13 快照已修复已知文档/口径问题**
- `docs/report_pack/2026-02-25-v13/scoreboard.md` 已为“干净版本”（修复了误用重定向导致的文件头污染）。
- `strong v3` 在 `ablation_notes.md` / `Progress.md` 的指标口径已按 `metrics.csv` 校正。

2. **weak 的“只调 w/end”的路线已止损**
- `notes/weak_tuning_selfcap_bar.md` 已追加 `Weak Mask Sweep v2（2026-02-25, GPU1）`：两次 full600 均无法消除 `control > weak` 风险信号，结论为 **STOPLOSS**。

3. **已具备 anti-cherrypick 证据位**
- 同场景 second segment（`seg200_260`）在 `notes/anti_cherrypick_seg200_260.md` 中记录：`ours-weak` 相对 `baseline` 有可见但小幅收益（ΔPSNR `+0.2281`）。
- 这条证据的意义是“防 cherry-pick”，不是用来反向挑段讲提升。

4. **速度信号不是“全零死路”（用于防守/也影响后续判断）**
- `notes/velocity_stats_selfcap_bar_8cam60f.md` 显示：`||v||` 在训练后显著非零（mean 从 `0.0169` 到 `0.2515`），因此“完全没有速度信号”不是当前主瓶颈的首要证据。

5. **当前训练预算/配置对“最终画质上限”可能有限（需要专家确认是否值得为 final 开 v2）**
- 现状：`config_name=default_keyframe_small` + `max_steps_full=600` 是一个“短预算”协议，适合做闭环与机制对比，但可能不适合讲“高保真重建”。
- 风险：若最终需要显著提高画质，可能必须启用更长训练或 densification（意味着 `protocol_v2` + baseline/control 全重跑）。
- 建议：在 feature-loss v2 还没出趋势前，不要贸然开 v2；否则会把 GPU 都消耗在重跑 baseline 上。

## 3. 02-26+ 推荐推进主线（建议专家拍板冻结）

### 3.1 主线定义：VGGT Feature Metric Loss v2（推荐唯一主线）

目标：在不改 protocol_v1 的冻结项前提下，引入一个**可控、可审计、吞吐可接受**的 feature-level prior，使得至少在以下任一指标上出现可辩护收益：
- `tLPIPS` 下降 ≥ 10%（主打“时间稳定性/减少 flicker”叙事）
- 或 `LPIPS` 下降 ≥ 0.01
- 或 `PSNR` +0.2 dB

必须满足的工程约束（否则直接止损）：
- 训练吞吐下降 **≤ 2x**（通过低频触发 + 低分辨率 + patch 采样实现）
- 2 次 full600 仍无任何趋势 -> 止损并转入失败分析/Plan‑B

### 3.2 v1 为什么失败（我们希望专家重点审查）

我们已有 `feature_loss_v1_attempt.md` 的事实结论：`phi_name=depth` 的 v1 在 `lambda=0.05` 下明显压死质量；降到 `lambda=0.005` 且 `start=200` 后接近 baseline，但仍无收益。

需要专家判断的“最可能根因”候选（按优先级）：
1. **phi 选错**：depth/几何类特征不适合作为 photometric 替代约束，容易与现有优化目标冲突。
2. **对齐/预处理不一致**：VGGT 的 crop/resize/归一化与训练渲染视图不一致，导致 feature loss 实际在惩罚坐标误差。
3. **loss 施加位置不对**：全图/全时刻施加 feature loss 会把优化压成“平均化”；需要 warmup + 只在动态/困难区域触发。
4. **采样策略问题**：patch 采样若大多落在静态背景，会变成无意义正则；需要 dynamic-patch gating。

### 3.3 v2 的可执行规格（建议作为拍板版）

离线 cache（必须离线）：
- 对 **GT 图像**计算 VGGT 的选定特征层 `phi(I_gt)`，缓存到 `outputs/vggt_cache/<tag>/...`。

训练时（必须可控）：
- 只对 `I_render` 前向 VGGT（或轻量 encoder），并与 cache 中 `phi(I_gt)` 对齐计算：
  - 低频：每 `VGGT_FEAT_EVERY` step 才计算一次（建议 4 或 8）
  - 低分辨率：输入固定小分辨率（例如 256/384，按你们实际实现）
  - patch：每次只采样 K 个 patch（例如 32/64）
  - warmup/ramp：前 20% steps 不开；随后线性 ramp 到目标权重
  - gating（强烈建议）：只在动态区域/高误差区域采样 patch（先用帧差 gating，不强依赖 cue）

最小消融矩阵（同 protocol_v1，避免漂）：
1. baseline_600（已有）
2. control_weak_nocue_600（已有，关键对照）
3. feature_loss_v2_600（新主线）
4. feature_loss_v2_gated_600（新主线 + gating）

反 cherry-pick（最终必须有其一）：
- 方案 A：同场景第二段（已具备 appendix 协议）：`docs/protocols/protocol_v1_seg200_260.yaml`
- 方案 B：第二场景 short-run（同协议、短 steps、定性即可）

### 3.4 需要专家重点提醒的“细节坑位”（不提前约束，后面会返工）

1. **特征对齐（最容易把 feature loss 变成“惩罚坐标误差”）**
- 需要明确：GT feature 的输入分辨率、crop 策略、归一化方式，必须与 render->VGGT 的路径一致。
- cache 里必须写死 meta（已在 v1 做了 `meta.json`，但 v2 需要继续强化审计）。

2. **phi 选择（决定你是在“补纹理”还是“压死几何”）**
- 需要专家对“用 depth/几何类 vs 中间层语义特征”的优先级给建议。
- 推荐优先尝试中间层/多层组合，而不是把 depth 当作 feature loss 的默认。

3. **patch/gating 的定义（决定吞吐与有效性）**
- gating 若用帧差：需要固定阈值/比例并写入协议附录（否则又会变成“挑出来的提升”）。
- patch 采样必须可复现（seed 固定，采样策略写入 cfg/日志）。

4. **成功线的拍板（会直接影响你们最终 claim）**
- 需要专家确认：是否允许 “tLPIPS 明显下降但 PSNR/LPIPS 小幅退化” 作为主 claim（时间稳定性优先）。

## 4. 备选路线与止损定位（避免抢主线 GPU）

### 4.1 Strong（VGGT-based）定位：加分项，必须 timebox

已验证：KLT strong v3 只能带来极小 tLPIPS 改善且 trade-off，不应再作为主战场。

建议定位：
- strong 只允许“接口连通性 + 可审计失败/成功证据”，不允许拖主线（最多 48–72h timebox）。
- 若要替换 KLT：优先考虑 RAFT/GMFlow 作为更强 2D correspondence extractor（仍需可审计 precision）。

### 4.2 Plan‑B（救火开关）：triangulation → 粗 3D velocity 初始化（48h）

触发条件（必须同时满足）：
- feature-loss v2 在 2 次 full600 下仍无任何趋势
- 你们有明确证据认为“速度初始化/动态污染”是主瓶颈（例如 `||v||` 分布与渲染现象强相关）

约束：
- 不做 depth‑lift scene flow（容易算力黑洞）
- 优先利用你们已有的数据契约：`triangulation/points3d_frame*.npy`

交付形式：
- 一个初始化脚本 + 1 次 full run 对比 + 失败/成功证据（不允许演变成新项目）

## 5. 最终完成的“Definition of Done”（建议专家确认）

建议把“最终完成”定义为可审计的 5 件套（满足即可，不追 SOTA）：

1. **冻结协议**：至少保留 `protocol_v1`，如需升级必须 `protocol_v2` 版本化并重跑 baseline。
2. **主线方法可复现**：feature-loss v2（含 gated 变体）的代码、脚本、配置齐全。
3. **定量结果 + 防 cherry-pick**：
   - canonical（bar 8cam60f）full600：baseline/control/ours（+消融）
   - 第二段或第二场景 short-run：baseline vs ours（至少定性 + 指标）
4. **证据链可一键打包**：report-pack + evidence tar + sha256 可追溯（无需提交大文件，但 sha 必须入库）。
5. **写作材料闭环**：Method/Experiments/Failure cases 三块有图表与证据路径（复用 `docs/report_pack/*` + `notes/*`）。

## 6. 给专家/同行的“问题清单”（请按顺序问，避免发散）

1. VGGT feature metric loss 里，`phi` 最推荐选哪一层/哪类特征？（depth vs intermediate features vs multi-layer）
2. 对齐策略：VGGT 的 `crop/resize/normalize` 应如何与训练渲染视图一致化，避免在惩罚坐标误差？
3. loss 形式：L2 / cosine / Huber，哪个更稳？是否建议对特征做 `normalize`？
4. gating：用帧差 gating 是否足够，还是必须依赖 cue mining 输出？K 与 patch size 推荐范围？
5. 成功线取舍：若 `tLPIPS` 大幅下降但 `PSNR` 小幅下降，是否接受作为主 claim？（需要拍板）
6. 反 cherry-pick：优先选“seg200_260”还是“第二场景”？（考虑工作量/风险）

---

## 附录 A：关键证据文件索引（会议时快速打开）

- 主线评测协议：`docs/protocol.yaml`、`docs/protocols/protocol_v1.yaml`
- 当前结果快照（v13）：`docs/report_pack/2026-02-25-v13/metrics.csv`
- weak 风险与 probe 结论：`notes/weak_vggt_probe_selfcap_bar.md`
- weak v2 sweep 止损结论：`notes/weak_tuning_selfcap_bar.md`（末尾 v2 段落）
- strong v3 止损结论：`notes/ours_strong_v3_gated_attempt.md`
- feature loss v1 尝试与止损：`notes/feature_loss_v1_attempt.md`
- anti-cherrypick(seg200_260)：`docs/protocols/protocol_v1_seg200_260.yaml`、`notes/anti_cherrypick_seg200_260.md`
- 速度统计（防守页）：`notes/velocity_stats_selfcap_bar_8cam60f.md`（如需补图可由脚本导出）

---

## 7. 进度安排表（用于“完成项目”的宏观推进）

> 说明：这是按“当前仅 A/B 两人两卡（GPU0/GPU1）”的节奏制定；若人力恢复，可把同周任务再细分并行。
>  
> 时间范围先按 `docs/execution/2026-02-12-4d-reconstruction-execution.md` 的 3 月里程碑组织；具体截止日期需结合你们学校/导师节点再落到日历。

### 7.1 里程碑（必须可审计）

1. **M1（主线落地）**：feature-loss v2 端到端可跑（含 cache、训练、评测、报表入 scoreboard）
2. **M2（主线趋势）**：在 canonical 上至少出现“趋势可辩护”的指标变化或明确失败归因（两次 full600 内给结论）
3. **M3（防 cherry-pick）**：seg2（或第二场景）上完成 baseline vs ours 的对照（short-run 允许）
4. **M4（写作闭环）**：Method/Experiments/Failure cases 初稿（图表可复现、证据路径可追溯）

### 7.2 周计划表（建议作为会议拍板版）

| 周期 | 负责人/资源 | 目标 | 必交产物（可审计） | 止损条件 |
| --- | --- | --- | --- | --- |
| 02-26 ～ 03-01 | A(无GPU) + B(GPU1) | 设计冻结 + v2 最小实现 + 200-step sanity | 1) `feature_loss_v2` 代码与 flags 测试；2) cache v2 产物+meta；3) 200-step 视频+stats；4) 文档：`notes/feature_loss_v2_design.md`（若新增） | 吞吐>2x 且无法通过 every/patch 降下来；或 200-step 直接明显退化 |
| 03-02 ～ 03-08 | B(GPU1) + A(打包) | canonical full600：v2 与 v2_gated（最多 2 次 full600） | 1) `outputs/protocol_v1/.../feature_loss_v2*_600/stats/test_step0599.json`；2) report-pack vN 快照与 sha | 连续 2 次 full600 无任何趋势 -> stoploss，转入 Plan‑B 评估 |
| 03-09 ～ 03-15 | A(GPU0 可选) + B(GPU1) | 反 cherry-pick：seg2 或第二场景 short-run | 1) seg2 的 baseline vs ours（或第二场景）对照；2) 失败模式归类更新 `docs/report_pack/*/failure_cases.md` | 新场景适配成本失控（>1天还没出 stats）则回退 seg2 |
| 03-16 ～ 03-22 | B(GPU1, timebox) | strong（VGGT-based）加分项尝试（可失败） | 1) matching/feature 可视化；2) 1-2 次 full run 以内的审计结论；3) stoploss 记录 | 72h 或 3 次 full run 上限触发立即停止 |
| 03-23 ～ 03-31 | A主导写作 + B补实验缺口 | 写作与 evidence 固化节奏化 | 1) Method/Experiments/Failure cases 初稿；2) evidence pack 周更（sha 入库） | 写作缺证据则暂停探索，补齐证据链后再写 |

### 7.3 会议上必须确认的“日程依赖”（否则表无法落地）

1. 你们的最终“完成项目”硬截止日期（学校/导师/答辩节点）
2. 这段时间是否稳定只有两卡两人，还是会恢复到三人三卡
3. 是否强制需要“第二场景 full600”，还是允许“第二场景 short-run + 定性”

### 7.4 03-31 之后（可选扩展，用于“真正最终完成”而不是只到初稿）

> 这一段依赖你们的真实截止日期（论文终稿/答辩）。建议专家给一个“最小必做清单”，其余全部当加分项。

1. **多场景最小泛化（防守用）**
- 目标：至少 1 个额外场景（或同场景第二段）跑出 baseline vs ours 的短跑对比（可不追 full600）。

2. **长跑定性（只讲现象，不当主 claim）**
- 目标：挑 1 个代表性配置跑更长步数，出一条“长时序视频”作为附录/愿景，不把它作为主要定量对比。

3. **写作收口**
- 目标：把 `docs/report_pack/*` 与 `notes/*` 升级成论文/报告可直接引用的图表与叙事，并保持 evidence 可复现。
