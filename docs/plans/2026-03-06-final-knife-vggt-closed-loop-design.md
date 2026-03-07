# Final Knife VGGT Closed-Loop Design

## Objective

这份 design 只服务一个问题：

> 能否用一组最小、干净、可判定成败的受控实验，证明 `VGGT soft prior / correspondence-inspired gating` 不只是“有图、有解释”，而是真的对下游 4D 重建优化带来了可辩护的收益？

这就是当前项目距离原版开题最近、也是最关键的一刀。

## Why this is the right target

原版开题最核心的创新闭环，不是单独的 cue 可视化，也不是单独的动静解耦 demo，而是：

- `VGGT` 提供语义/动态/对应线索；
- 这些线索进入 4DGS 优化；
- 下游重建因此在稳定性或质量上得到可解释收益。

目前仓库现状是：

- `Plan-B` 主线已经闭环；
- `VGGT cue / PCA / token-topk` 已有上游证据；
- `dynamic/static` 已有定性演示；
- 但“`VGGT -> 优化 -> 收益`”仍未形成干净的正向闭环。

因此，最后一刀不应再补“更多上游分析”，而应补“最小因果闭环测试”。

## Scope boundary

本轮 design 严格只做一条默认路线：

- **默认路线：`framediff-gated stage-2 paired run`**

不做：

- 不重开 `oracle-weak`；
- 不做新的 `full600` 多 seed 扫描；
- 不同时并行尝试多种 gating 机制；
- 不把已有 mixed/trade-off 包装成已成功闭环。

这是一把“单刀”，不是新一轮搜索。

## Candidate approaches

### Approach A — 继续补上游分析，不做新的下游因果测试

优点：低风险、低成本。

缺点：解决不了最关键的问题。你仍然只能说“VGGT 看起来有信息”，不能说“VGGT 确实推动了优化收益”。

### Approach B — 单一路线的最小因果测试（推荐）

用同一数据、同一 schedule、同一 seeds、同一截面，只改变一个因素：

- `ungated stage-2`
- `framediff-gated stage-2`

然后比较 `199/399` 的 `PSNR / LPIPS / tLPIPS`，并辅以可选的局部 temporal-diff 诊断。

优点：
- 最接近原版开题第 2 条“时空关联约束进入优化”；
- 因果结构最清楚；
- 成败判定最明确；
- 即使失败，也能形成一份高质量负结果闭环。

缺点：
- 仍然有训练成本；
- 如果 `framediff gate` 本身信号弱，最终可能只得到 mixed/negative result。

### Approach C — 改成 cue-gated 或更多 gating 备选并行对比

优点：覆盖面更广。

缺点：重新变成搜索问题，打破“最后一刀”的简洁性与判定性。

## Recommendation

选择 **Approach B**。

理由：现在最缺的不是“备选方案数量”，而是一份足够干净的闭环证据。`framediff-gated paired run` 已经有现成代码入口和历史上下文，最适合作为最后一刀的默认路线。

## Experiment definition

### Core causal question

在固定 `Plan-B + stage-2 schedule` 的前提下，仅引入 `framediff gating`，是否能让 `stage-2` 在时序稳定性上获得超出噪声带的收益，并且不把 `LPIPS / PSNR` 明显拖坏？

### Fixed design

- 数据：`SelfCap` 主证据链数据；
- 对照：`ungated stage-2`；
- 处理：`framediff-gated stage-2`；
- steps：`400`；
- 截面：`199`, `399`；
- seeds：`42`, `43`；
- 默认 schedule：`lambda=0.005`, `start=150`, `ramp=150`, `every=16`。

### Why 400 and not 600

- `400` 足以给出一个“进入中后期”的因果测试；
- 比 `600` 更省预算；
- 更符合“最后一刀”的 timebox 性质；
- 避免把当前闭环测试重新扩张成 sweep。

## Outcome taxonomy

### Strong positive closed loop

同时满足：

- `seed42` 与 `seed43` 在 `step399` 都有 `ΔtLPIPS <= -0.001371`；
- 两个 seed 都有 `ΔLPIPS <= 0`；
- 两个 seed 都有 `ΔPSNR >= 0`；
- 若有 renders，temporal-diff 局部诊断与数值结论同方向。

这时可以说：

- 已形成一个较强的 `VGGT gating -> optimization benefit` 最小正向闭环。

### Minimal thesis-grade closed loop

满足：

- 两个 seed 在 `step399` 的 `ΔtLPIPS` 同方向为负；
- 至少一个 seed 的 `ΔtLPIPS` 超过噪声带阈值 `-0.001371`；
- `ΔLPIPS` 没有明显变差；
- `PSNR` 至少均值不下降。

这时可以说：

- 已形成一个**最小可辩护闭环**，足以支撑“创新路线不只停留在图和解释层面”。

### Negative but closed result

若结果显示：

- 改善不超过噪声带；
- 或两个 seed 不同向；
- 或 `LPIPS / tLPIPS` 退步明显；

则不能说“正向闭环成功”，但可以说：

- 这条路线已经形成一份**负结果闭环**：上游信号存在，但当前注入方式未转化成稳定下游收益。

## Early stop rule

为避免无意义扩张，设置一个前置止损：

- 先看 `seed42 @ step199`；
- 如果 `gated` 相比 `ungated` 在 `LPIPS` 和 `tLPIPS` 同时更差，且 `PSNR` 也没有补偿，则不新增任何额外 seed / steps / settings；
- 保留当前最小配对设计并收口。

## Deliverables

本轮只交付 3 类产物：

1. 配对 runner 与合同测试；
2. `seed42/43 × step199/399` 的配对结果 note；
3. 若条件满足，再附一份 focused temporal-diff 诊断包。

## Final claim discipline

无论结果如何，都只能在以下三种口径中选一个：

- `promising positive closed loop`
- `minimal thesis-grade closed loop`
- `negative/mixed closed loop`

不允许使用：

- “已证明 stage-2 全面有效”
- “已稳定优于基线”
- “已完成原版开题全部创新闭环”

## Design summary

这最后一刀的本质，不是再补一份材料，而是做一次最小的因果测试：

- 上游证据已经存在；
- 现在要测的只剩一句话：
  - **把这个 `VGGT-inspired gating` 放进训练后，下游到底有没有变得更好？**

只要这句话能被清楚回答，无论答案是正还是负，这条创新路线才算真正闭到头。
