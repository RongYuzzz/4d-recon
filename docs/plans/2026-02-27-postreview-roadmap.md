# 2026-02-27 Post-Review Roadmap（Academic Completeness / protocol_v2）

日期：2026-02-27  
输入材料：
- 同行 A 审核意见：`docs/reviews/2026-02-27/review-2026-02-27.md`
- 专家 B 拍板意见：`docs/reviews/2026-02-27/decisions-2026-02-27.md`

> 注：本路线图的目标是“把开题承诺补齐到可答辩”，同时**不破坏**既有 `v26 + protocol_v1` 的可审计证据链。

---

## 0. 一句话拍板（以后所有文档统一口径）

**不硬拽回 VGGT 单主线**；把已跑通且证据很硬的 **Plan‑B（3D velocity init）** 纳入主线，重构为：

> **阶段一：物理运动先验（Plan‑B）打破劣速/零速基底的收敛陷阱；阶段二：几何语义先验（VGGT feature / attention-guided consistency）在物理底座上做高维时空对齐；最终用动静解耦渲染做可编辑性演示（object removal）。**

---

## 1. 不变量（必须遵守，避免把 v26 证据链冲掉）

1. **保留 `protocol_v1` 与 `docs/report_pack/2026-02-26-v26/` 不动**：它们是阶段一（物理底座）的最终证据。
2. 所有“对齐开题”的新实验统一落到 **`protocol_v2`**（或显式标注 `protocol_semantic_v1`），避免与 v26 数值口径混用。
3. 新实验必须写清：新增 loss、权重范围、warmup、timebox、成功线/止损线；并产出可视化（不接受“只说跑了但没证据”）。

---

## 2. 先做什么（按“收益/风险/成本”排序）

### Task A（必须，最低成本高冲击）：动静解耦渲染 + object removal demo

**目的**：兑现开题“动静显式分离/可编辑性”的承诺；不需要重训，只需要从已有 ckpt 导出视频。

**最小实现**：按速度幅值 `||v||` 阈值把 Gaussians 分两层：
- `static`: `||v|| < τ`
- `dynamic`: `||v|| ≥ τ`

**交付物**（论文/答辩可直接用）：
- 背景-only 视频（static-only）
- 动态层视频（dynamic-only）
- 一张速度直方图 + 阈值说明（含失败例：慢动的人被判静态）

实现提示：trainer 已支持 `--export-only` + `--export-vel-filter static_only|dynamic_only`（只在导出时过滤，不影响训练）。

---

### Task B（必须，补齐“VGGT 线索挖掘”的证据链）：VGGT 特征/伪掩码可视化

**目的**：回应“你到底从 VGGT 挖到了什么实例线索”的追问；先补**可解释材料**，再谈闭环提指标。

**最小交付**：
- 选 3–5 帧 × 多视角，导出 VGGT 某层 feature（或 token_proj）并做 PCA(3D) → RGB 可视化
- 或对像素/patch 特征做 k-means / spectral clustering，输出彩色簇图
- 对比跨视角一致性（同一实例在不同视角分到同一簇）作为“几何一致语义线索”的证据

---

### Task C（必须，关键实验）：重启 Plan‑B + VGGT Feature Metric Loss（warmup + 降权）

**目的**：把“阶段二语义对齐”真正补齐到可跑、可复现、有趋势的程度。

执行纪律（建议写进 protocol_v2/决议）：
- 先 `smoke200` 过稳定性与趋势，再做 `full600`
- `warmup`: 前 100–200 steps 不启用 feature loss
- `ramp`: λ 从 0 线性爬升到目标值
- 一旦出现“control 反而更好/三项全劣化”，按止损线立刻收口并记录 failure analysis

---

### Task D（加分项，严格 timebox）：注意力引导对应/对比学习（稀疏化版本）

**目的**：贴近开题“注意力→对应→对比损失”的完全体。

纪律：
- 只允许 patch/token 级 + top‑k 稀疏对应
- 必须可视化对应质量（否则评审会认为在做噪声对比学习）
- 建议 72h timebox：到点不出趋势就停，写成 future work 或 limitation

---

## 3. 文档侧必须同步（避免口径打架）

1. 更新开题主线：把 `Plan‑B` 写成“阶段一物理底座”，VGGT 写成“阶段二语义对齐”。
2. 把“端到端”改成可辩护表述：**不依赖外部 2D 强监督前置（SAM/DEVA/tracker）**；VGGT/伪掩码属于软先验，以 loss/weight 形式注入。
3. 把“注意力引导对比损失”写成**可实现版本**：patch/top‑k 稀疏 + 定义清楚“特征是什么、怎么渲染/绑定到像素、loss 施加点在哪里”。
4. 调整评测口径：删掉不现实的 Neural3DV/Multi‑Human + mIoU 强承诺，改为 SelfCap + PSNR/LPIPS/tLPIPS（时序稳定）+ 定性去重影/去闪烁。
5. 增补：资源约束/止损策略（MVP 必做 vs 加分项）。
