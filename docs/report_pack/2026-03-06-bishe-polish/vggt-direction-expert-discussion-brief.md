# VGGT Direction Failure Analysis and Expert Discussion Brief

## 1. 这份文档要解决什么问题

这份文档讨论的不是“当前这版 `stage-2 VGGT feature loss` 还要不要继续拧超参”，而是：

> 在已经连续做完多轮 `stage-2` 重开且均未形成稳定闭环之后，
> **原版开题里“VGGT / 语义先验进入 4D 重建并带来下游收益”这个大方向，到底还剩下哪些可信空间？下一步最值得讨论和探索的路线是哪一条？**

这份文档的目标是把下面 4 件事说清楚：

1. 现在已经被什么证据否掉了；
2. 现在遇到的问题到底更像什么；
3. 哪些问题是当前 `SelfCap` 协议本身带来的；
4. 如果还想尽量对齐原版开题，后续最值得讨论的路线有哪些。

## 1.1 最小术语约定

为避免专家在阅读时把不同层次的问题混在一起，这里先固定 4 个术语：

- **`Plan-B`**：当前项目最稳的主线方案；本文里所有 `stage-2` 重开，都是拿“同一套 `Plan-B` 初始化/缓存条件下、**不加额外 VGGT loss** 的 control”做对照。
- **`stage-2`**：在 `Plan-B` 主线之上，额外加入某种 `VGGT` 相关训练约束的受控 paired rerun 家族；本文讨论的 `final knife`、`local-softmatch`、`loss-fix rerun`、`cue-soft` 都属于这一类。
- **`SelfCap`**：当前项目关于“`VGGT -> 优化 -> 收益` 是否成立”的主证据数据集；因此本文所有 route-level 判断默认都以 `SelfCap` 为主锚点。
- **`tLPIPS noise band = 0.001371`**：当前 paired go/no-go 口径使用的关键噪声带阈值；任何 `ΔtLPIPS` 改善如果没有明确越过这个量级，都不应被解释成可信正信号。

## 1.2 相比上一轮专家讨论，这次真正新增了什么

这份文档相对上一轮讨论，最关键的新事实不是“又多了一个想法”，而是：

- 两位专家在 `v6` 阶段都曾把 `local-window / soft matching` 视为最值得重开的训练路线之一；
- 这个建议后来已经被完整执行：`local-softmatch` 已跑、`loss-fix fairness rerun` 已跑，并且都以 `STOP` 收口；
- 随后又补做了只改 signal selection 的 `cue-soft`，结果依然 `STOP`；
- 因此，当前讨论目标已经从“下一条 `stage-2` 训练路线该试哪条”转成了“是否应放弃整个 `stage-2 online extra loss family`，转而讨论更前置/更离线的 `VGGT prior` 注入方式”。

---

## 2. 当前最稳的总判断

### 2.1 已经站住的东西

1. **`Plan-B` 仍是毕设主线硬结果**
   - 当前项目最稳的正结果仍然来自 `Plan-B`，而不是 `stage-2 VGGT extra loss`。
   - 因此 thesis mainline 仍应是：`Plan-B` 主结果 + `VGGT` soft-prior 证据链 + dynamic/static 可编辑性材料。

2. **`VGGT` 上游证据链已经成立**
   - `pseudo mask / cue` 已经落成；
   - `feature PCA` 结构证据已落成；
   - `sparse correspondence` 可解释示意已落成。
   - 这说明：`VGGT` 中的语义/动态/对应信息是真实存在的，不是空洞概念。

3. **dynamic/static 可编辑性证据已经成立**
   - 当前项目已经不只是“提取 cue”，而是已经把 `dynamic/static` 分解与 removal-style demo 做成了可播放材料。
   - 这部分本身已经能支撑“工作量 + 一点创新性 + 论文叙事完整度”。

### 2.2 已经基本站住的负结果

目前可以比较明确地下这个判断：

> **在当前 `SelfCap` 协议下，把 `VGGT` 作为 `stage-2` 的在线 extra feature loss 直接注入训练，这整个 family 已经非常不乐观。**

这不是来自单次失败，而是来自一串已经做完的受控重开：

| Route | 关键改动 | 数据/预算 | 结果摘要 | 当前结论 |
|---|---|---|---|---|
| `final knife` | `framediff hard top-p gate + token_proj cosine` | `SelfCap`, `seed42/43`, `400-step` | `mean ΔPSNR=-0.001921`, `mean ΔLPIPS=+0.000474`, `mean ΔtLPIPS=-0.000359` | `negative/mixed closed loop -> stop` |
| `local-softmatch` | 把严格同-cell 匹配改成局部窗口 soft matching | `SelfCap`, `seed42/43`, `400-step` | `mean ΔPSNR=+0.028208`, `mean ΔLPIPS=+0.001404`, `mean ΔtLPIPS=+0.000487` | `mixed -> stop` |
| `local-softmatch loss-fix` | 只修 local-softmatch loss 公式偏置 | `SelfCap`, `seed42/43`, `400-step` | `mean ΔPSNR=-0.016166`, `mean ΔLPIPS=-0.000043`, `mean ΔtLPIPS=-0.000302` | `family still stop` |
| `cue-soft` | 把 `framediff hard gate` 改成 `VGGT cue-backed dense soft weighting` | `SelfCap`, `seed42 checkpoint-gated`, `400-step` | `step199` 触发 early-stop；`seed42@399` 单点为 `ΔPSNR=+0.034094`, `ΔLPIPS=-0.000179`, `ΔtLPIPS=-0.000244` | `stop` |
| `oracle weak` | `oracle backgroundness weak fusion` 诊断线 | `THUman4`, weak-init | 出现弱初始化 rescue 线索，但 replication 不足 | `mixed evidence -> stop` |

从这 5 条证据合起来看，当前最稳的说法不是“某个 gate 还没调好”，而是：

- `stage-2 extra loss` 这类实现已经反复给出 `mixed / stop`；
- 指标符号会变，但始终没有形成稳定、可复制、跨 seed 的正结果；
- 因此后续讨论不该再围绕“要不要再调当前 recipe”，而应转向“还剩什么不同机制的路线值得做”。

### 2.3 统一判据（避免对“看起来有点正”产生误读）

当前这些 route-level 判断共用的是一套比较保守的 paired 判据：

- 对完整 paired rerun，`GO` 至少要求：`mean ΔtLPIPS` 明确跨过噪声带（`<= -0.001371`）、`mean ΔLPIPS <= 0`、`mean ΔPSNR >= 0`，并尽量有跨 seed 一致性；
- 对 `cue-soft` 这类 checkpoint-gated rerun，额外还有一个 `step199` 早停条件：只有当 `ΔPSNR@199 < 0`、`ΔLPIPS@199 > 0`、`ΔtLPIPS@199 >= 0` 三者同时成立时，才直接 `STOP`；
- 因此，哪怕某个 route 在 `step399` 出现单 seed 的末端小正切面，只要它没有跨过 `tLPIPS` 噪声带、没有第二个 seed 复核、或者已经在 `step199` 命中早停，就不能被解释成 route-level positive。

以 `cue-soft` 为例：虽然它的 `seed42@399` 出现了 `ΔPSNR=+0.034094`、`ΔLPIPS=-0.000179`、`ΔtLPIPS=-0.000244` 的单点转正，但这个 `ΔtLPIPS` 量级只有噪声带阈值 `0.001371` 的约 18%，因此它不能推翻 `STOP`。

### 2.4 这份文档对应的核心更新

早先两份专家意见 `opinions-a-v6.md` 与 `opinions-b-v6.md` 都曾把 `local-window / soft matching` 视为最值得重开的一条训练路线，因为它最直接针对 `phi_shift_sensitivity / strict same-cell mismatch` 这个问题。

这个建议已经被认真执行到位：

- `local-softmatch` 已实跑并 `stop`；
- `local-softmatch loss-fix fairness rerun` 已实跑并 `stop`；
- 之后又进一步尝试了 `cue_soft` 这一条只改 signal selection 的路线，也仍然 `stop`。

因此，到目前为止，**“下一条该不该继续押在 `stage-2 training extra loss` 上”这个问题，答案已经越来越接近 `不该`。**

---

## 3. 什么已经被否掉了，什么没有被否掉

### 3.1 已经基本被否掉的

当前已经基本被否掉的是这类**具体实现假设**：

- 在 `SelfCap` 主协议下；
- 以 `stage-2` 为主战场；
- 通过在线增加一项 `VGGT feature loss`；
- 再配合某种 gate / soft weight / local matching；
- 试图直接把 `VGGT` 的结构信息转成稳定的下游 `PSNR / LPIPS / tLPIPS` 收益。

更直接一点说：

> **不是只有 `framediff hard gate` 被否了，而是“把 `VGGT` 当 `stage-2 online extra feature loss` 来打”的这一整个 family，都已经拿不到强证据了。**

### 3.2 没有被彻底否掉的

没有被彻底否掉的是这个更大的方向：

- `VGGT` 线索是否能作为 4D 重建中的有效 soft prior；
- `VGGT` 的 cue / 对应 / 动态信息是否应该进入系统的更前置、更加结构化的位置；
- `VGGT` 是否更适合作为离线约束生成器、初始化过滤器、或可解释 prior，而不是在线训练 loss。

也就是说：

- **被否掉的，是一个注入位置与训练机制；**
- **没被彻底否掉的，是“VGGT / 语义先验对 4D 重建有价值”这个原版开题大方向。**

---

## 4. 现在遇到的问题：综合所有失败因素后的诊断

下面把目前最可能的问题分成两层：

- **A. 方法层问题**：这类 `stage-2 extra loss` 从机制上为什么总是 mixed；
- **B. 协议层问题**：当前 `SelfCap` 协议里，哪些设置使得这类路线更容易失败。

### 4.1 方法层问题一：signal selection / gate 与真正优化目标错位

`final knife` 的核心做法是：

- 用 `gray framediff top-p` 选区；
- 但真正优化的是 `token_proj cosine feature loss`。

这意味着：

- gate 强调的是“变化大 / 帧差大”的位置；
- loss 强调的是“render feature 与 GT feature 的几何对齐”；
- 这两者并不天然一致。

变化大的区域往往更难对齐、更容易有遮挡/形变/亮度变化；如果再用严格 feature 对齐去压它，选区越“激进”，越可能把 loss 变成噪声源。

这解释了为什么：

- `framediff hard gate` 没有把路线救正；
- 只把 hard gate soft 化成 `cue_soft`，也没有稳定救回来；
- 问题看起来不只是“gate 过硬”，而是“signal 与 loss 目标本来就未必匹配”。

### 4.2 方法层问题二：feature loss 对轻微空间错位过于敏感

这也是早先两位专家都盯住的主矛盾：

- 只要 render feature 与 GT feature 在空间上有 1~2 个 cell 的轻微偏移；
- 严格同-cell 的 cosine loss 就会迅速变坏；
- 于是一个“看起来像合理监督”的 feature loss，实际变成高噪声监督。

`local-softmatch` 及其 `loss-fix rerun` 已经直接去碰这个问题，但结果仍然没有翻成稳定正例：

- 第一轮 `local-softmatch`：`PSNR` 有小幅上升，但 `LPIPS/tLPIPS` 同步变差；
- `loss-fix rerun`：指标符号结构变了，但仍然没有形成双 seed 一致改善。

这说明：

- **错位敏感性确实是问题；**
- **但它不是唯一问题。**

换句话说，即使你把“严格同-cell”这个最显眼的尖刺磨平，当前 `stage-2 extra loss` 这条线仍然拿不到够强的净增益。

### 4.3 方法层问题三：`stage-2` 本体可能就存在 intrinsic trade-off

从多轮结果看，`stage-2` 非常像一个有内在 trade-off 的分支：

- 有时 `PSNR` 略涨，但 `LPIPS / tLPIPS` 恶化；
- 有时 `LPIPS` 略降，但 `PSNR` 转负；
- 有时单 seed 晚期切面看起来有点正，但 early-stop 早已触发。

这表明：

> 当前 `stage-2` 可能不是一个“只要把先验喂对就自然起飞”的分支，而是本来就容易在 pixel fidelity / perceptual quality / temporal stability 之间摇摆。

如果这条判断成立，那么继续在这个分支里堆新的 extra loss，本身就不划算。

### 4.4 方法层问题四：`cue_soft` 只是在“哪里算 loss”上做文章，没有改变 loss geometry

这轮 `cue_soft` 的 treatment 是：

- `token_proj + cosine + cue_soft + lambda=0.005 + start=150 + ramp=150 + every=16`

核心逻辑其实很简单：

```python
use_feat_loss = step >= start_step and (step % every == 0)
...
weight_map = cue_mask if weight_map is None else (weight_map * cue_mask)
feat_loss = (loss_map * weight_map).sum() / weight_map.sum().clamp(min=1e-6)
```

这说明：

- `cue_soft` 并没有引入新的 correspondence；
- 没有显式优化 temporal association；
- 没有改 feature loss 的几何定义；
- 它只是把同一个 `cosine loss` 重新加权。

因此，如果真正问题在“监督本体就不够稳”，那 `cue_soft` 最多只能改变指标符号结构，不太可能从根本上把路线救成稳定正结果。

### 4.5 协议层问题一：当前 `SelfCap` cue 本身很弱，而且缺少 GT silhouette 校准

这轮 `cue_soft` preflight 已经明确记录：

- `SelfCap` 缺少 `dataset silhouettes`；
- 因此 silhouette healthcheck 被跳过；
- 只能依赖 cue distribution audit。

同时，`quality.json` 显示原始 cue 的平均覆盖很低：

- `mask_mean_per_t` 大多只有约 `0.004`；
- `mask_mean_per_view` 也都很低；
- raw cue 虽然不是全黑/全白，但并不强。

更关键的是，真正用于 `cue-soft` 的 scaled cue 也并不是真正意义上的 dense soft mask：

- scaled cue 的全局均值约为 `0.0787`，但中位数仍为 `0`；
- 约 `88.3%` 的像素值就是 `0`；
- 在进入当前 `9x9` token grid 后，每张图平均只有约 `10 / 81` 个 cell 大于 `0.1`。

这意味着：

- 当前 `cue` 更像“弱线索”，不是高可信监督；
- 它可能适合做 prior / filtering / reweighting；
- 但不一定适合直接承担在线训练里的主监督角色。

### 4.6 协议层问题二：`VGGT` feature cache 太粗，当前是 `phi_size=9x9`

当前 `token_proj` cache 的元信息是：

- `phi_size = [9, 9]`
- `has_conf = false`

这两个细节都很关键。

`9x9` 的含义是：

- 不管 raw cue、边界、细粒度前景结构在原图里多复杂；
- 到 `stage-2 feature loss` 这里，都会被压到一个很粗的 token 网格上。

于是会出现两个直接后果：

1. 原本细粒度的 cue / ROI 对齐信息被抹平；
2. 轻微空间偏移在粗网格下更容易变成同-cell 失配。

这会放大 `strict alignment` 与 `wrong region emphasis` 两类问题。

### 4.7 协议层问题三：`VGGT_FEAT_USE_CONF=1` 在当前 cache 下其实帮不上忙

虽然 runner 里开了 `VGGT_FEAT_USE_CONF=1`，但当前 cache 元信息明确写着：

- `has_conf = false`

代码里只有在 `conf_gt is not None` 时才会真的使用 confidence weighting。

这意味着：

- 在当前 `SelfCap` cache 下，`use_conf` 这个开关几乎没有提供额外保护；
- 你实际上是在没有 feature confidence 防护的前提下，直接把弱 cue 和粗网格喂给了 `stage-2 extra loss`。

### 4.8 协议层问题四：feature loss 生效太晚、太稀疏

当前 `cue_soft` 与之前多轮 rerun 使用的都是同一类调度：

- `start=150`
- `ramp=150`
- `every=16`
- `budget=400`

而训练代码按全局 `step % every == 0` 才触发 feature loss，不是按 `start_step` 对齐。

这意味着到 `step199` 为止，真正启用 feature loss 的步数极少，而且 ramp 还很小。更具体地说，在当前 `start=150`、`every=16`、按全局 `step % 16 == 0` 触发的实现下，`step199` 之前实际只有 `160 / 176 / 192` 这 **3 个 step** 会真的计算 feature loss，对应的 ramp ratio 也只有约 `0.067 / 0.173 / 0.280`。

结果就是：

- `step199` 更像一个“还没真正热起来”的早期观察点；
- 如果一条路线属于慢热弱信号，它很容易在这里就被 early-stop 卡死；
- 但反过来说，如果它连这么宽松的 early-stop 都过不了，也说明它没有“稳健的早期正效应”。

这解释了 `cue_soft` 为什么会出现：

- `step199` 负面早停；
- 但 `step399` 单 seed 末端切面又稍微转正。

它更像“弱、慢、且不稳”的效应，而不是“可信的正例”。

### 4.9 协议层问题五：当前评测口径本身更偏向筛选 smoke-robust / early-robust effect

当前 go/no-go 口径看重的是：

- 跨 seed 一致性；
- `tLPIPS` 是否跨过噪声带；
- 是否在早期就出现明显坏信号。

这个口径对于科研是合理的，因为它避免你被晚期单 seed 偶然正例误导。

但它的副作用是：

- 它天然不偏爱“慢热型、小幅型、后期才勉强转正”的路线；
- 所以如果某条路线只能靠一个 seed 的 `step399` 单点小好看来证明自己，那么它本来就不够强。

因此，`cue_soft` 的 late-looking single-seed positive 并不能推翻 `STOP`，反而说明它更不适合作为主线。

---

## 5. 综合判断：现在最像真相的是什么

如果把所有证据合起来，我认为当前最像真相的结论是：

> **不是 `VGGT` 本身没有信息，而是当前 `SelfCap + stage-2 online extra feature loss` 这套组合，把“弱 cue / 粗 token / 晚启动 / 低频更新 / 对错位敏感的 loss”叠在了一起，因此信号太弱、太慢、太不稳，无法形成跨 seed 的稳定净增益。**

更简化一点说：

- 上游 prior 是有信息的；
- 但当前注入位置与优化机制不对；
- 所以这条 family 看起来不像“再小修一下就能变正”，而更像“应该换介入位置”。

---

## 6. 现在最值得讨论的，不是继续修这条 family，而是后续哪条路线最有希望对齐原版开题

下面给出我认为**仍有希望对齐原版开题**、且彼此机制真正不同的几条路线。

### Route A：把 `VGGT` prior 前移到初始化 / 过滤 / 采样 / triangulation 侧

#### 核心思路

不要再让 `VGGT` 先验承担 `stage-2 online feature loss` 的角色，而是把它前移到更适合弱 prior 的地方，例如：

- 点初始化过滤；
- triangulation / visibility filtering；
- frame/view weighting；
- dynamic/static 候选选择；
- foreground/backgroundness 的点级或视角级加权。

#### 为什么这条现在最稳

因为当前已经知道：

- cue 是弱的、粗的，但不是没信息；
- 弱先验更适合做“筛选 / 过滤 / weighting”，而不是直接当训练主监督；
- 这条路和 `Plan-B` 主线更容易耦合，工程风险比再开一个新 training family 小得多。

#### 与原版开题的关系

- 它仍然属于“VGGT latent cue mining / 几何语义 weak cue 提取 -> 进入 4D 重建流程”；
- 只是它更偏“前置 prior 注入”，而不是“中后期训练 loss 注入”。

#### 优点

- 成功概率最高；
- 最容易产出可审计、可解释的中等实验；
- 最适合在毕设周期里补“工作量”和“创新性”的最后一刀。

#### 风险

- 与原版开题中“注意力/对应关系引导的时空一致约束”相比，它更偏保守；
- 更像“先验介入流程”，而不是“训练闭环桥接成功”。

### Route B：把 `VGGT` 对应/动态信息做成**离线 correspondence-backed prior**，再接入系统

#### 核心思路

保留原版开题里最想要的那一刀：

- `attention / correspondence-guided spatiotemporal consistency`

但不要再走“在线 stage-2 feature loss”这条路，而是改成：

- 先离线生成更可信的 sparse tracks / affinity / visibility / pseudo-correspondence；
- 再把这些结构性结果接入下游的 temporal consistency、triangulation、点过滤、或轨迹关联。

#### 为什么它比继续改 gate 更合理

因为它真正改变的是**先验进入系统的位置和形式**：

- 不再要求训练时直接拿 feature loss 对齐；
- 而是先把 `VGGT` 的结构信息显式化、离线化；
- 这样更贴近原版开题“对应关系引导”的叙事，也更绕开当前 `same-cell cosine` 的脆弱点。

#### 与原版开题的关系

这条路线是几条备选里**最贴近原版开题表述**的一条，因为它最像：

- 先挖出对应关系；
- 再把对应关系转成重建约束。

#### 优点

- 与原版开题最对齐；
- 创新性表述最好；
- 如果做成，即使只是小规模，也比继续改 `stage-2 loss` 更有说服力。

#### 风险

- 风险高于 Route A；
- 前提是当前 `VGGT sparse correspondence` 必须能从“可解释示意级”进一步提升到“可作为离线 prior 使用”的程度；
- 如果 correspondence 质量本身不稳，这条路也会卡住。

### Route C：如果坚持再做 training 路线，也必须换介入点，而不是继续在当前 family 里修补

这条路线不是我最推荐的，但如果专家坚持“还要保留一条训练探索线”，那它至少应满足两个条件：

1. **不再是当前这类 `stage-2 extra feature loss family` 的微调变体；**
2. **必须同时改协议假设，而不只是改 gate / matching 一个局部。**

例如，如果真要再试 training 方向，至少要同时回答：

- 是否需要更 dense 的 feature grid，而不是 `9x9`；
- 是否需要真实 `conf`，而不是 `has_conf=false`；
- 是否要更早、更连续地施加 prior；
- 是否要让 prior 作用到 sampler / visibility / geometry，而不是只改 loss weight。

如果做不到这些前提，那么继续重开 training family 大概率只是重复现在的 `mixed/stop`。

#### 当前态度

- **不建议把 Route C 作为默认首选。**
- 它只应该作为“专家强烈坚持必须保留训练路线”时的备选讨论对象。

---

## 7. 我当前给专家的推荐排序

如果把“与原版开题对齐程度”和“在当前项目里成功概率”两件事综合起来，我的排序是：

### 第一梯队：真正值得讨论的两条

1. **Route B：离线 correspondence-backed prior / consistency route**
   - **最贴近原版开题**；
   - 不是继续修当前 family；
   - 但风险高于 Route A。

2. **Route A：VGGT cue / prior 前移到初始化 / 过滤 / weighting 路线**
   - **最稳、最容易落地**；
   - 更适合毕设周期；
   - 与原版开题的“语义先验进入系统”仍然同方向，只是没那么激进。

### 第二梯队：不建议作为默认首选

3. **Route C：继续重开 training route，但必须换协议和介入点**
   - 不再建议继续做当前 `stage-2 extra loss family` 的局部修补；
   - 除非专家明确认为必须保留训练闭环探索，否则不推荐。

---

## 8. 如果现在必须做一个策略判断，我的建议是什么

### 8.1 关于毕设主线

我的建议非常明确：

> **毕设主线不要再依赖“VGGT -> 在线优化 -> 稳定收益”这条闭环。**

主线应保持：

- `Plan-B` 主增益结果；
- `VGGT` 上游 soft-prior / 可解释证据包；
- dynamic/static 可编辑性材料；
- 再加上对这条训练闭环失败原因的诚实诊断。

这已经是一个能自洽答辩、并且工作量与创新性都能说清楚的主叙事。

### 8.2 关于是否还值得再做 1 次探索

如果你还想尽量向原版开题靠齐，我认为**可以再做 1 次有边界的探索**，但必须满足：

- 只选 1 条路线；
- 这条路线不能再属于当前 `stage-2 extra loss family`；
- 目的不是“强行救 thesis mainline”，而是“判断原版开题方向是否还能被再推进一步”。

### 8.3 如果只能选 1 条最值得和专家重点讨论的路线

我会建议你把讨论重点聚焦在下面这个二选一上：

- **如果更重视“最大程度贴原版开题”**：优先讨论 `Route B`；
- **如果更重视“毕设周期内更可能做成”**：优先讨论 `Route A`。

我不建议现在还把主要讨论资源放在：

- `framediff` 怎么再 soft 一点；
- `local-softmatch` 半径再调一轮；
- `cue_soft` 再换一个阈值；
- `lambda/start/ramp/every` 再 sweep 一轮。

这些都太像继续在已收口 family 里打转。

---

## 9. 建议你带给同行/专家的核心问题

建议把讨论聚焦在下面 5 个问题，而不是泛泛地问“为什么失败”：

### Q1. 你是否同意：当前被否掉的是 `stage-2 online extra VGGT feature loss family`，而不是整个 `VGGT direction`？

### Q2. 在 Route A 与 Route B 之间，你认为哪条更值得给一次有边界的探索机会？

- `Route A`：`VGGT cue / prior` 前移到初始化、过滤、weighting、triangulation；
- `Route B`：把 `VGGT` 对应/动态信息变成离线 prior，再接入时空一致性或轨迹关联。

### Q3. 你认为当前 `SelfCap` 协议里最致命的失败因素是哪一个？

可让专家在下面几项里排序：

- signal-loss mismatch
- feature shift sensitivity
- `stage-2` intrinsic trade-off
- cue too weak / too coarse
- `9x9` token grid too coarse
- no confidence in cache
- schedule too late / too sparse

### Q4. 如果只允许再做 1 个最小而决定性的实验，应该怎么设计？

请专家明确限定：

- 选哪条路线；
- 在哪个数据集；
- 需要几个 seed；
- 看哪些指标；
- 什么结果算 `continue`，什么结果算 `final stop`。

### Q5. 从毕设/论文叙事角度看，现在最优策略是：

- 直接以 `Plan-B + soft-prior evidence + editability demo` 收口；
- 还是允许做 1 次“与原版开题更对齐”的 bounded exploration。

---

## 10. 我当前的默认立场

如果不考虑情绪，只考虑证据，我当前的默认立场是：

1. **当前 `stage-2 extra loss` family 已经应当视为项目级 stop。**
2. **`VGGT direction` 本身没有被逻辑上判死，但后续必须换介入位置。**
3. **最值得和专家重点讨论的是 `Route A` 与 `Route B`，而不是继续修 `Route C`。**
4. **毕设主线现在已经够稳，不应再被训练闭环绑架。**

---

## 11. 关键证据锚点

如果专家要追原始证据，优先看这些文件：

### 主线与对齐

- `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
- `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`

### 已收口的 stage-2 训练路线

- `.worktrees/owner-b-20260306-final-knife/notes/2026-03-06-final-knife-vggt-closed-loop.md`
- `.worktrees/owner-b-20260306-vggt-softmatch/notes/2026-03-06-vggt-local-softmatch-go-nogo.md`
- `.worktrees/owner-b-20260306-vggt-softmatch-lossfix/notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md`
- `.worktrees/owner-b-20260307-vggt-cuesoft-go-nogo/notes/2026-03-07-vggt-cuesoft-go-nogo.md`

### 协议与上游 prior 证据

- `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/meta.json`
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json`
- `notes/protocol_v2_vggt_cue_viz.md`
- `notes/protocol_v2_vggt_feature_pca.md`
- `notes/protocol_v2_sparse_corr_viz.md`
- `notes/protocol_v2_stage2_tradeoff_qual.md`

### 专家意见与补充诊断

- `opinions-a-v6.md`
- `opinions-b-v6.md`
- `notes/2026-03-06-thuman4-oracle-weak-decision.md`

---

## 12. 一段可以直接发给专家的摘要

> 我现在不是想继续调当前这版 `stage-2 VGGT feature loss`，而是想和你讨论：在已经连续做完 `framediff-gated final knife`、`local-softmatch`、`local-softmatch loss-fix`、`cue-soft` 这些重开且均未形成稳定闭环之后，原版开题里“VGGT / 语义先验进入 4D 重建并带来下游收益”这个大方向还应如何继续。当前我比较确定的是：被基本否掉的是 `SelfCap + stage-2 online extra VGGT feature loss` 这整个 family，不是 `VGGT direction` 本身。综合现在的失败因素，我觉得如果还要再往原版开题靠一步，应该优先讨论两条真正不同的路线：一条是把 `VGGT cue / prior` 前移到初始化、过滤、weighting、triangulation 侧；另一条是把 `VGGT` 对应/动态信息先做成离线 prior，再接入时空一致性或轨迹关联。我想请你帮我判断：这两条里哪条更值得给一次有边界的探索机会，以及最小决定性实验该怎么设计。`
