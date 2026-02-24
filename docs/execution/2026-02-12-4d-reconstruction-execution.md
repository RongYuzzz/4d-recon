# 4D Reconstruction Execution Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 第一优先级保证 `2026-02-25` 汇报：在算力受限的两周窗口内完成“可交付且有创新”的 4DGS 闭环 Demo（MVP A）；同时给出 `2026-02-26` 起的后续推进路线（覆盖 3 月关键里程碑），用于把 02-25 的可运行底座扩展到完整毕设工作量与论文产出。

**Architecture:** 以 4DGS（优先线性运动基底，T0 不通过则切换 `Deformable-GS`）为重建核心；离线执行 VGGT 线索挖掘（pseudo mask + global attention）；先弱融合完成闭环，再强融合加入注意力引导的时空一致性约束（Correspondence/Contrastive Loss）。

**Tech Stack:** Python、PyTorch、CUDA、4DGS/4DGS-variant 代码库、VGGT（预训练，仅推理/特征提取）、视频/多视角数据集（优先 `Neural3DV` 最小子集，必要时单场景）。

---

## 0. 统一口径（必须冻结）

### 0.1 Training-free 定义（防御性）
- **Training-free 仅指** VGGT cue mining（特征/注意力提取、聚类生成伪掩码）阶段：**No-finetune**。
- 4DGS 主体仍是 **optimization-based reconstruction**（重建优化）。

### 0.2 项目主叙事（建议直接复用到 slide/论文摘要）
- “以非官方 `OpsiClear/FreeTimeGsVanilla` 为工程基底，进行严格审计与修正（重点：线性运动假设 + 时间归一化 + 梯度回传 + duration 窗口），在此基础上融合 VGGT 线索挖掘与注意力引导的时空一致性约束，实现动静解耦的 4D 场景重建。”

### 0.3 冲刺原则（保证 02-25 汇报）
- **范围控制**：`2026-02-25` 前只做路线 A（必达）+ 可选的路线 B（增强），明确 **不追路线 C**（全量 benchmark / 刷榜）。
- **关键路径优先**：T0 过闸门 → T1 闭环（baseline+weak）→ T2 证据包（表/消融/demo/失败分析）。
- **硬止损**：
  - `2026-02-14` 前 T0 不通过：切 `Deformable-GS`，不再修线性运动基底。
  - `2026-02-20` 前未闭环：冻结功能，先把 demo + 表 + 失败分析做出来。
  - `2026-02-22` 后：不加新功能，只修 bug 与补证据。
- **网络/代码获取风险预案**：若无法 `git clone`（网络限制），改用你本机已有基底/离线压缩包，放入 `projects/4d-recon/third_party/` 并固化版本信息。

### 0.4 冲刺日历（`2026-02-12` ～ `2026-02-25`，只列关键交付）

| 日期 | 目标 | 当天必须产出（可复用到汇报） |
|---|---|---|
| `02-12` | 建工作区 + 跑通基底最小样例 | `decision-log.md` 初始化、baseline 训练/渲染跑起来的截图/短视频 |
| `02-13` | 完成 T0 四项 sanity check | `t0_grad_check.md` + 其他检查日志/对比视频（PASS/FAIL 明确） |
| `02-14` | T0 结论与熔断执行 | Go：修到可稳定跑；No-Go：切 `Deformable-GS` 并跑通最小闭环 |
| `02-15` | cue mining 最小版可视化 | `cue_mining_vis/`（mask overlay + attention 热力图） |
| `02-16` | weak 融合接入训练 | baseline vs weak 对比视频（至少 1 场景） |
| `02-17` | T1 闭环稳态复现 | 固化配置/seed、可重复跑通的闭环命令（脚本） |
| `02-18` | strong 融合设计冻结 | `attention_loss_design.md`（对应/约束对象/损失形式三点拍板） |
| `02-19` | strong 融合最小实现跑起来 | Ours-Strong 初版训练日志 + 初版渲染视频 |
| `02-20` | T1 止损闸门日 | 若 strong 不稳：回退到 weak，开始集中打包证据 |
| `02-21` | 单场景关键消融 | weak vs strong 消融视频 + 初版指标 |
| `02-22` | 功能冻结 + 证据补齐 | 02-25 MVP 五件套缺什么补什么（只修 bug） |
| `02-23` | 汇报素材成套 | 指标表、消融图、失败案例图/视频、讲述要点草稿 |
| `02-24` | 彩排与备份 | 一键复现脚本、备份结果、演示口播与 Q&A 口径 |
| `02-25` | 汇报日 | 现场演示脚本 + 离线视频备份（防翻车） |

---

## 1. 里程碑与硬闸门（按 `4D_discussion_review_report_v5.3.2.md`）

### T0：基底审计期（`2026-02-11` ～ `2026-02-13`，最晚 `2026-02-14`）
**目标：** 判定线性运动基底是否可用（Go/No-Go）。

**Go/No-Go（必须全部通过）：**
1. **零速度退化测试**：设 `v=0` 时能退化为静态 3DGS（无异常漂移/闪烁）。
2. **时间尺度一致性**：速度 `v`（每帧位移）与归一化时间 `t∈[0,1]` 的单位严格对齐（运动幅度不崩）。
3. **梯度检查**：`∂L/∂v`、`∂L/∂duration` 存在且量级合理（非全 0 / 非 NaN）。
4. **Densification 继承**：split/clone 时动态参数（`v`、`duration` 等）正确复制。

**熔断机制：**
- 若到 **`2026-02-14`** 仍无法跑通上述检查：**立即放弃**线性运动基底，切换到成熟 `Deformable-GS`；VGGT 创新主线保留不变。

### T1：闭环构建期（`2026-02-14` ～ `2026-02-20`）
**目标：** 跑通“输入多视角视频 → 输出渲染视频”闭环。

**策略：**
- 先只做 **VGGT 弱融合**（用于初始化/伪掩码辅助动静解耦），不强推新 loss。

**止损闸门（`2026-02-20`）：**
- 若未闭环：冻结功能，收敛到最低交付（只保留能跑通的最小版本），不再加新模块。

### T2：交付打磨期（`2026-02-21` ～ `2026-02-25`）
**目标：** 单场景深度证据（表 + 消融 + demo + 失败分析）。

**功能冻结：**
- **`2026-02-22`** 后不再新增功能，只修 bug、补证据、做可视化与写作。

---

## 2. `2026-02-25` 最低交付（MVP A，建议冻结）

1. **完整闭环 Demo**：cue mining → 4DGS 训练 → 渲染视频。
2. **1 张定量对比表**：Baseline vs Ours（指标至少 PSNR/SSIM；能加 LPIPS 更好）。
3. **1 组关键消融**：弱融合 vs 强融合（验证 Attention Loss/Correspondence 约束有效性）。
4. **1 个演示视频**：动静解耦或实例编辑（如物体移除）。
5. **失败案例分析**：机制级（例如时间尺度错配/梯度断裂/遮挡导致 attention 错配）。

---

## 3. 工程落地目录建议（便于并行与复现实验）

> 说明：当前 `/home/ry` 下未发现 `FreeTimeGsVanilla` 代码与 `run_pipeline.sh`，因此这里按“新建项目工作区 + 拉取第三方基底”的方式规划。

- Create: `projects/4d-recon/`
- Create: `projects/4d-recon/third_party/`（第三方基底仓库）
- Create: `projects/4d-recon/data/`（数据软链接/下载目录）
- Create: `projects/4d-recon/outputs/`（训练输出、render、表格）
- Create: `projects/4d-recon/notes/`（决策记录、失败日志）
- Create: `projects/4d-recon/scripts/`（T0 检查、跑实验、导出视频）

---

## 4. 任务拆解（可直接照单执行）

### Task 1: 建立工作区与基底拉取

**Files:**
- Create: `projects/4d-recon/README.md`
- Create: `projects/4d-recon/notes/decision-log.md`

**Step 1: 创建目录骨架**

Run: `mkdir -p projects/4d-recon/{third_party,data,outputs,notes,scripts}`

**Step 2: 拉取基底（线性运动优先）**

Run: `git clone https://github.com/OpsiClear/FreeTimeGsVanilla.git projects/4d-recon/third_party/FreeTimeGsVanilla`

**Step 3: 固化“基底版本”**

Run: `cd projects/4d-recon/third_party/FreeTimeGsVanilla && git rev-parse HEAD`
Expected: 输出一个 commit hash，并写入 `projects/4d-recon/notes/decision-log.md`（用于答辩时可追溯）。

---

### Task 2: 环境与最小数据准备（只做到能跑通）

**Files:**
- Create: `projects/4d-recon/notes/env.md`

**Step 1: 基底依赖安装（以仓库说明为准）**
- 优先根据 `projects/4d-recon/third_party/FreeTimeGsVanilla/pyproject.toml` 与 README 走“可复现安装”。

**Step 2: 选择最小数据（单场景优先）**
- 目标：只要能完整跑完 1 个场景训练 + render。
- 建议：`Neural3DV` 选 1 个场景；若下载/预处理时间不可控，则改用仓库自带示例或你已有的小视频样例。

**验收：**
- 能通过基底自带脚本在单卡上跑到“有可播放的渲染视频”。

---

### Task 3: T0-1 零速度退化测试（Showstopper #1）

**Files:**
- Modify: `projects/4d-recon/third_party/FreeTimeGsVanilla/run_pipeline.sh`
- Modify: `projects/4d-recon/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`

**Step 1: 找到 motion 参数入口**
- Run: `cd projects/4d-recon/third_party/FreeTimeGsVanilla && rg -n \"velocity|duration|time|t\\b\" src`
Expected: 定位 `v`、`duration`、`t` 的定义与更新位置。

**Step 2: 强制 `v=0` 并训练少量 iter**
- 要求：输出可视化中动态部分不应产生“凭空运动/闪烁”，且整体效果接近静态 3DGS。

**验收：**
- 记录一段对比视频（baseline 正常 vs `v=0`），存入 `projects/4d-recon/outputs/t0_zero_velocity/`。

---

### Task 4: T0-2 时间尺度一致性审计（Showstopper #2）

**Files:**
- Modify: `projects/4d-recon/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`

**Step 1: 打印关键统计量**
- 每 N iter 打印：`t` 的取值范围、`||v||` 的统计（min/mean/max）、`||Δx||` 实际位移幅度（至少抽样 100 个 gaussian）。

**Step 2: 对齐单位（只做“最小修复”）**
- 原则：要么把 `v` 明确定义成“每归一化时间单位位移”，要么把 `t` 改成以帧为单位；两者只能选其一，并在 `notes/decision-log.md` 写清楚。

**验收：**
- 修复后运动幅度不崩（不出现整体飞走/抖爆），且对同一场景不同帧率/采样配置不会出现数量级差异。

---

### Task 5: T0-3 梯度链路检查（Showstopper #3）

**Files:**
- Modify: `projects/4d-recon/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Create: `projects/4d-recon/scripts/t0_grad_check.md`

**Step 1: 在训练循环内记录梯度范数**
- 对 `v`、`duration` 的参数张量（或对应 optimizer param group）记录 `grad.norm()`。

**Step 2: 判定规则**
- FAIL：连续多步 `grad` 恒为 0 或出现 NaN/Inf。
- PASS：`grad` 大部分时间非 0，且数值稳定（随 loss 变化有响应）。

**验收：**
- 输出一份日志与简短结论写入 `projects/4d-recon/scripts/t0_grad_check.md`（含 PASS/FAIL 与截图/数值片段）。

---

### Task 6: T0-4 Duration 窗口与 Densification 继承

**Files:**
- Modify: `projects/4d-recon/third_party/FreeTimeGsVanilla/src/**`（以实际搜索结果为准）

**Step 1: Duration 窗口可视化**
- 输出：同一 gaussian 在时间上的可见性曲线/开窗函数（抽样 50 个）。

**Step 2: Densification 参数继承断言**
- 在 split/clone 处加断言：新 gaussian 的 `v`、`duration` 与父 gaussian 保持一致（或按你定义的规则缩放）。

**验收：**
- 训练过程中 densify 后不出现动态参数“归零/随机跳变”导致的闪烁。

---

### Task 7: T0 结论与切换决策（硬闸门）

**Files:**
- Update: `projects/4d-recon/notes/decision-log.md`

**Step 1: 形成 Go/No-Go 结论**
- 写清楚：4 项检查是否 PASS；若 FAIL，具体失败点与不可修复原因（时间成本/工程不可控）。

**Step 2: No-Go 切换预案（若触发）**
- 选择并拉取 `Deformable-GS` 基底，目标只要满足“可稳定闭环 + 可插入 VGGT 模块”。

---

### Task 8: 模块A（VGGT Cue Mining，Training-free）

**Files:**
- Create: `projects/4d-recon/scripts/run_cue_mining.sh`
- Create: `projects/4d-recon/notes/cue_mining_spec.md`

**Step 1: 定义输入输出契约（先写 spec 再写代码）**
- 输入：多视角视频帧（frame_id, view_id）及相机参数（若有）。
- 输出（最小集）：`pseudo_mask[frame, view, H, W]`、`global_attention[(frame_i, frame_j)]`（可用 top-k 稀疏形式存）。

**Step 2: 伪掩码生成策略（按 `4D Reconstruction.md`）**
- 语义聚类：VGGT 浅层特征 + 谱聚类（或先用 k-means 做可跑通版本）。
- 动态过滤：中深层 Gram 矩阵时间方差，抑制背景噪声；可先只保留“运动高频区域”作为动态候选。

**验收：**
- 输出可视化：mask overlay + attention 热力图；存 `projects/4d-recon/outputs/cue_mining_vis/`。

---

### Task 9: 模块B（4DGS 闭环 + 弱融合）

**Files:**
- Modify: `projects/4d-recon/third_party/**`（以你的基底为准）
- Create: `projects/4d-recon/scripts/run_train_baseline.sh`
- Create: `projects/4d-recon/scripts/run_train_ours_weak.sh`

**Step 1: 闭环 baseline 固化**
- 目标：baseline 单场景可稳定复现（固定 seed、固定配置）。

**Step 2: 弱融合（只影响初始化/分组）**
- 用 `pseudo_mask` 做：
  - 动静分组初始化（动态 gaussian 初始位置/密度/速度初始化更激进；静态更保守），或
  - 训练初期对动态区域加权（仅前 N iter）。

**验收：**
- 同一场景输出 baseline vs weak-fusion 对比视频，且不会引入新的不稳定。

---

### Task 10: 模块C（强融合：注意力引导时空一致性约束）

**Files:**
- Modify: `projects/4d-recon/third_party/**`（loss 接入训练循环）
- Create: `projects/4d-recon/notes/attention_loss_design.md`
- Create: `projects/4d-recon/scripts/run_train_ours_strong.sh`

**Step 1: 先写设计决策（避免临场拍脑袋）**
在 `attention_loss_design.md` 里冻结以下三点：
1. **对应形式**：attention 产生的像素对（top-k）如何映射到 4DGS（例如通过渲染的深度/gaussian-id map 或其他代理）。
2. **约束对象**：约束的是颜色特征、几何（3D/4D 位置）、还是额外的可学习 embedding。
3. **损失形式**：L2/InfoNCE/对比学习的正负样本定义（先实现最简单可收敛版本）。

**Step 2: 最小可用实现（建议顺序）**
1. 先做 **attention-weighted feature consistency**（正样本一致，负样本先不做或随机采样）。
2. 再升级到 **对比损失**（InfoNCE），并加入 hard negative（跨实例/跨区域）。

**验收：**
- 至少在 1 个“快速运动/遮挡”片段上，strong-fusion 相比 weak-fusion 明显减少时序漂移/断裂（允许指标提升有限，但现象要更稳）。

---

### Task 11: 证据打包（表格 + 消融 + Demo + 失败分析）

**Files:**
- Create: `projects/4d-recon/outputs/report/table_metrics.md`
- Create: `projects/4d-recon/outputs/report/ablation.md`
- Create: `projects/4d-recon/outputs/report/failure_cases.md`

**Step 1: 指标表（最小版本）**
- 表格行：Baseline / Ours-Weak / Ours-Strong
- 列：PSNR、SSIM（可选：LPIPS、训练时长、显存占用）

**Step 2: 单场景关键消融**
- 固定场景、固定 seed，只改动 “是否启用 attention loss/对应约束”。

**Step 3: Demo 视频**
- 动静解耦可视化（动态层/静态层分开渲染）；
- 或实例编辑（移除某个实例后重渲染）。

**Step 4: 失败分析（机制级）**
- 至少 2 个失败案例：一个来自 T0（工程风险），一个来自 T2（attention 对应失败/遮挡）。

---

## 5. 资源与并行策略（按 `4D_discussion_review_report_v5.3.2.md`）

- 优先申请：`2×48GB`
- 价值定位：并行跑 `Baseline/Ours/消融`（不是多卡并行训练）
- 脚本约束：若 `run_pipeline.sh` 仍是 `CUDA_VISIBLE_DEVICES=$GPU_ID` 单进程单卡，则用两张卡同时跑不同配置来控变量。

---

## 6. `2026-02-26` 起后续推进路线（不删减，和 02-25 冲刺同等重要）

> 说明：第 0～5 节确保 `2026-02-25` 汇报不翻车；第 6 节把 02-25 的可运行系统，持续扩展为“工作量饱满 + 写作质量高 + 有创新”的完整毕设闭环。两者不是二选一：只是时间上先交付 02-25，然后立刻进入第 6 节推进。

### 6.1 3 月里程碑（`2026-02-26` ～ `2026-03-31`）

| 周期 | 目标 | 必须产出（可直接写进论文/中期检查） |
|---|---|---|
| `02-26`～`03-01` | 冻结复现口径 + 补齐诊断页 + 主线设计冻结 | 1) protocol v1 一键复现脚本与证据包刷新；2) 两页防守证据：`||v||` 分布统计 + cue 对齐 overlay；3) VGGT feature metric loss（主线）接口设计与 stoploss 写清 |
| `03-02`～`03-08` | **唯一主线：VGGT feature metric loss v1** 落地并跑出趋势 | 1) 离线 GT 特征 cache；2) 训练时低频/低分辨率/patch 的 feature loss；3) 在 canonical 场景上跑出 baseline/control/feature-loss 的可审计对比（优先看 tLPIPS） |
| `03-09`～`03-15` | cue mining 质量/对齐/稳定化 + anti-cherrypick | 1) cue mining `quality.json` 与更多 overlay；2) second segment（seg2）对比（baseline vs 主线方法）；3) failure modes 总结 |
| `03-16`～`03-22` | strong（VGGT-based）从“有效现象”升级到“机制证据”（严格 timebox） | 1) 机制级消融矩阵（至少 2×2）；2) matching/feature 可视化证据；3) 可审计止损与失败分析（strong 成功非强制） |
| `03-23`～`03-31` | 写作与 evidence 固化进入稳定节奏 | 论文/报告 Method & Experiments 两章初稿（图表/表格可复现），以及答辩 Q&A 口径 |

- 主线（只选一条，避免 GPU/注意力被撕裂）：**VGGT feature metric loss**（离线 GT cache；训练时低频/低分辨率/patch；必要时 dynamic gating）。
- Plan-B（触发式救火开关，不并行）：triangulation→粗 3D velocity 初始化，48h timebox（仅当主线连续 full runs 无趋势时才启动）。
- 其它：cue mining 继续升级为“可解释/可诊断”，但定位为主线的辅助（gating/诊断），而非唯一创新点。
- 第10-11周：多场景定量 + 完整消融矩阵
- 第12周：编辑演示（移除/替换/重放）
- 第13-14周：论文撰写与查重（术语与主叙事沿用第 0 节冻结口径）
