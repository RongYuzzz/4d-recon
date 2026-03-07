# V2.5 Bridge Experiments Design

## Context

当前仓库已经形成一套相对稳健但偏保守的 `v2` 交付：

- 主线硬结果由 `Plan-B` 承担；
- `VGGT soft prior` 已有可解释证据包；
- `dynamic/static` 已有可编辑性演示；
- `oracle-weak` 已收口为 `mixed evidence -> stop`。

问题在于：仅以当前 `v2` 口径答辩，虽然已经足够诚实，但与原版开题 `4D-Reconstruction.md` 的三条研究主线仍有明显距离，容易让人觉得“主线很稳，但创新部分偏保守”。

因此，目标不是重开高风险大实验，而是补一组 **介于原版开题与 v2 之间的桥接型中等实验（v2.5）**：既保持预算纪律和可审计性，又把原版三条路线分别往前推进半步到一步。

## Constraints

- 不重开 `oracle-weak` 路线。
- 不做新的 `full600` 多 seed 大扫参。
- 不破坏既有主线结论：`Plan-B` 仍是硬结果，`stage-2` 仍需诚实区分 `stable positive / mixed / exploratory`。
- `outputs/` 只新增，不改写旧结果。
- 只有一项允许消耗中等 GPU 预算；其余两项应主要是分析/诊断型实验。

## Candidate approaches

### Approach A — 只继续包装，不补实验

优点：最稳、最快、无额外资源风险。

缺点：虽然够答辩，但“创新性”仍主要依赖写法而非新增证据，难以把项目抬到比当前 `v2` 更接近原版开题的位置。

### Approach B — 3 个桥接型中等实验（推荐）

把原版开题的三条主线分别补一刀：

1. **VGGT cue 定量化**：把 `pseudo mask` 从“只有可视化”推进到“有定量边界”；
2. **对应关系定量探针**：把 `token top-k` 从“只有示意图”推进到“有可检验一致性”；
3. **timeboxed gated stage-2 配对中预算实验**：把 `soft prior / gating` 从“有探索”推进到“有一组更接近原版主线的受控训练证据”。

优点：
- 与原版开题的三条研究问题一一对应；
- 只把 GPU 预算集中在 1 项中预算训练，其余为低到中成本分析；
- 不要求翻盘出“全面稳定更优”，但能显著提升“工作量饱满 + 有一点创新性”的说服力。

缺点：
- 需要新增 2 个分析脚本 + 1 个中预算 runner/summary；
- 若第 3 项训练仍是 mixed evidence，最终仍需诚实收口。

### Approach C — 直接回到原版开题强承诺

做更多训练、更多数据集、更多 seed，试图重新逼近“多数据集 + 全指标稳定优于”。

优点：如果极少数情况下成功，会非常强。

缺点：高风险、高成本、时间不稳，而且极容易把当前已经收好的主线节奏再次打散。

## Recommendation

选择 **Approach B**。

理由：它是当前最合理的“v2.5”路径——既不回到原版开题那种高风险全量承诺，也不满足于纯文档包装，而是用 3 个桥接实验把三条研究路线各向前推一步：

- `VGGT 线索提取`：从可视化升级为“可视化 + 定量边界”；
- `注意力/对应关系`：从可视化升级为“可视化 + 一致性探针”；
- `几何语义先验注入训练`：从旧 mixed trend 升级为“更接近原版机制的 timeboxed 中预算验证”。

## Selected experiment set

### Experiment 1 — THUman4 VGGT cue quantization

**Goal:** 在有 `masks/` 的 `THUman4` 上，对 `VGGT pseudo mask` 做阈值扫与定量评估，把 cue 从“可解释图”升级成“有可量化边界的 weak cue”。

**Dataset choice:** `data/thuman4_subject00_8cam60f`。

**Reason:** 该数据已经具备 `masks/`，可以客观回答“VGGT cue 到底和前景/动态区域有多少对齐度”；这个结论不直接证明主线训练成功，但能显著增强原版第 1 条研究问题的可信度。

**Expected outputs:**
- 新的 THUman4 cue 目录；
- 阈值扫 CSV / JSON；
- `mIoU / precision / recall / pred_fg_coverage / temporal_flicker` 等摘要；
- 一份失败边界 note。

### Experiment 2 — SelfCap token-topk vs KLT correspondence probe

**Goal:** 用 `KLT` 做低成本 pseudo-reference，对 `token_proj temporal top-k` 的时序对应做一致性探针，把“只有对应示意图”推进到“有一个可检验的定量结果”。

**Dataset choice:** `data/selfcap_bar_8cam60f`。

**Reason:** SelfCap 是当前主证据链所在数据；用已有 `token_proj cache` 和现成 `KLT` 提取器，可以低成本评估 top-k 对应是否至少比随机/无结构假设更有意义。

**Expected outputs:**
- KLT correspondence NPZ；
- token-topk vs KLT 对齐 JSON / CSV；
- 关键帧/相机的小表格与解释 note。

### Experiment 3 — SelfCap framediff-gated stage-2 paired 400-step run

**Goal:** 只做一组受控、timeboxed 的 `400-step` 配对训练，把 `framediff gating` 从“已有代码入口”推进到“有成体系的受控实验”。

**Dataset choice:** `data/selfcap_bar_8cam60f`。

**Design:**
- 同一 schedule 下做 `ungated` vs `gated(framediff)` 成对比较；
- `MAX_STEPS=400`；
- 优先 2 seeds（`42,43`）；
- 固定取 `199/399` 截面，不向 `600` 扩张；
- 目标不是证明“稳定全面更优”，而是回答 gating 是否让 stage-2 更接近原版“时空关联约束”的机制方向。

**Expected outputs:**
- 一键 driver；
- paired runs summary；
- 若有必要，再补一份局部时序差异图或 gate activation 解释图；
- 一份受控训练 note。

## Success criteria

本轮 `v2.5` 不以“翻盘出全线正结果”为成功标准，而以以下三点为成功标准：

1. 原版三条研究问题都新增了至少一份更硬的证据；
2. 至少有 1 项新增证据进入“定量 + 可解释”双重形态，而不只是图片；
3. 即便 Experiment 3 最终仍是 mixed evidence，也能把项目从“保守 v2”提升为“更接近原版开题但边界清楚”的版本。

## Risk controls

- 若 Experiment 1 的 cue 对齐很弱，也照样保留：它能把失败边界写实，而不是把 `VGGT cue` 写成空话。
- 若 Experiment 2 的 top-k 对齐不佳，也照样保留：它能支持“对应关系仍属 exploratory”的诚实收口。
- 若 Experiment 3 在 `seed42` 的 `step199` 已对 `ungated` 明显更差（尤其 `LPIPS/tLPIPS` 同时更差），则不要继续扩展额外 seed 或更长训练；维持 timebox。

## Expected thesis impact

若这 3 个实验按设计完成，项目口径将从当前偏保守的 `v2`，升级为更接近原版开题的 `v2.5`：

- 主结果仍由 `Plan-B` 兜底；
- `VGGT` 不再只是“有图”，而是“有图 + 有定量边界 + 有 correspondence 探针”；
- `stage-2` 不再只是历史 mixed trend，而是多了一组更贴近原版机制的 gated 受控实验。

这不会把项目变成“全面稳定突破”的版本，但会明显抬高“工作量饱满”和“有一点创新性”的把握度。
