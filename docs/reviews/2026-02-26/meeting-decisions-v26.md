我把两份材料都看完了，直接给**最终拍板**（按“写进决议文件、当场能落地”的力度来给），并把同行指出的 4 个逻辑漏洞一并“修到叙事里”，保证你们后续组会/答辩不被一两句话掀桌。

------

## 0) 最终拍板（结论先给：今天就按这个执行）

### 0.1 主线（只能一条）

**选项 A：Plan‑B 作为唯一主线，立即进入写作冲刺；不再讨论回到 feature-loss v2。**

- `feature-loss v2`：正式 **No‑Go 冻结**（full600 三项全劣化已足够写成负结果/边界）。
- `Plan‑B`：正式 **Go**（不改 protocol_v1，仅替换 init velocities），且已有 canonical full600 + seg200_260 full600 + 4 段 smoke200（含 template hygiene）+ 定性视频 + 组件消融，证据链闭环。
- `Plan‑B + weak cue`：**No‑Go**，不为它申请任何新增 full600（已有“cue 注入负增益风险”信号）。

### 0.2 算力预算（写死）

**full600 新增预算：N = 0（默认不追加）。**

> 你们当前 full600 预算在既有决议下已用尽（剩余 0）；任何新增 full600 都必须另写决议并写死 N、成功线/止损线。

我这里的拍板就是：**不追加**。原因很简单：你们已经有两段 full600 的强证据（canonical + seg200_260）+ 多段趋势一致的 smoke200 + 定性视频；再烧 full600 的边际收益极小、风险是把“已锁定的 Evidence Pack”打散。

### 0.3 止损线（写进决议）

止损不是给实验用的（因为我们不再追加 full600），而是给**团队纪律**用的：

- **写作冲刺期禁止新增训练**（任何人想跑新实验 = 先写决议、写清动机与止损）。
- 允许的动作仅限 **No‑GPU/不改数值口径** 的补强：补齐吞吐 json、重打 report_pack、抽帧做图、整理 failure cases/limitations、打包 evidence tar/登记 SHA。

> 你们材料里已经明确：会中引用数字以 v26 的 `metrics.csv/scoreboard.md/planb_anticherrypick.md` 为准，其它写作型文本可能有历史残留；这个“口径纪律”必须保留。

------

## 1) 你现在手上“硬证据”到底强到什么程度（用来支撑你拍板 A）

### 1.1 canonical full600：Plan‑B 是明显正向，feature-loss v2 是明确负向

canonical（test@599）里：

- baseline_600：PSNR 18.9496 / LPIPS 0.4048 / tLPIPS 0.0230
- planb_init_600：PSNR 20.4488 / LPIPS 0.3497 / tLPIPS 0.0072
  - ΔPSNR +1.4992、ΔLPIPS -0.0551、ΔtLPIPS -0.0158
- feature_loss_v2_postfix_600：PSNR 18.6752 / LPIPS 0.4219 / tLPIPS 0.0261
  - 三项全劣化（No‑Go）

这组数本身就足够把路线从“VGGT 特征正则幻想”切换到“物理初始化破局”了：Plan‑B 不仅提升单帧指标，还把时序稳定性（tLPIPS）拉到明显更好。

### 1.2 anti-cherrypick：跨切片稳定同向（而且 seg200_260 还是 full600）

你们的 anti-cherrypick 表给出了 6 个切片（2 个 full600 + 4 个 smoke200）一致的同向增益：canonical ΔPSNR +1.4992，seg200_260 ΔPSNR +1.9950，并且 4 段 smoke200 在 step199 也都是 ΔPSNR 约 +0.18~0.19，同时 tLPIPS 大幅下降。

更关键的是：seg400_460、seg1800_1860 已做过 template hygiene（slice 用自己的 baseline init 做模板，只替换 velocities）后依然同向增益——这直接堵死“模板来自 canonical 导致偏置”的攻击点。

### 1.3 “初始化是不是离谱”的防守：Gate‑S1 统计很干净

Gate‑S1 的 `velocity_stats.json` 统计显示：各 slice 的 mutual 匹配率 ~0.58–0.60，远高于 Gate 阈值 0.05；clip_threshold 与 canonical 同量级（约 1.0x~1.07x），没有 10x 异常。

这意味着：Plan‑B 的收益不是靠“极端速度/异常裁剪”投机出来的，初始化分布本身稳定。

### 1.4 组件消融：Mutual NN 必要，但别再把它包装成“主要 PSNR 来源”

`planb_ablate_no_mutual_smoke200` 相对 default：ΔPSNR -0.0534、ΔLPIPS +0.0097、ΔtLPIPS +0.0135（一致退化）。

这组消融最正确的解释是：**Mutual NN 是必要的“稳定器/去噪器”，但不是 +1.5dB 的主因**——这正好对应同行指出的“漏洞 1”。

------

## 2) 把同行的 4 个“致命漏洞”逐条修正成你们的最终叙事（这部分非常关键）

下面是我建议你们立刻改掉的“表述与结构”，不是建议，是为了避免你们在会上被击穿。

### 漏洞 1：消融与 Claim 冲突（Mutual NN 不是主要 PSNR 来源）

**修正后的主 Claim（推荐你们论文/答辩第一句话这么讲）：**

> Plan‑B 的核心贡献是：**用物理一致的 3D 运动先验（速度初始化）打破劣质速度基底下的收敛陷阱**，显著提升短预算训练（600 steps）的收敛质量与时序稳定性；Mutual NN 等组件用于**匹配去噪与轨迹平滑**，主要体现在 tLPIPS 稳定性与鲁棒性上。

**你们需要立即替换的点：**

- 不要再说“收益来源于 Mutual NN 带来的高质量运动场”。这个说法会被消融数据一秒打穿。
- 把 Mutual NN 的定位改成：**必要但次要（stabilizer）**，并用“ΔtLPIPS 退化 +0.0135”来支撑它的价值。

### 漏洞 2：绝对 PSNR 20.4 过低会被喷“未收敛”

你们必须**主动降调**，把 scope 写死成“短预算收敛性研究”，不要再贴“高保真”标签。同行的建议非常对：卖点是“收敛速度/跳出局部最优/时序稳定”，不是最终画质。

**我建议你们在 paper/slide 里加一句范围声明（中英文都给你一版）：**

- 中文：

  > 受限于算力预算，我们研究聚焦于稀疏视角下 4DGS 在极短训练（600 steps）中的收敛路径与时序稳定性，而非最终高保真重建的绝对上限。

- English（可直接贴到论文）：

  > *Due to limited compute, we focus on convergence behavior and temporal stability under a short training budget (600 steps) in sparse-view 4DGS, rather than claiming high-fidelity reconstruction at convergence.*

并且：会上前 5 分钟必须播 side-by-side 视频，用视觉冲击力对抗“PSNR 低”的直觉攻击。

### 漏洞 3：Feature Loss vs Plan‑B 是“正交”，你不能把 feature-loss 彻底判死刑

这点你必须在论文里“主动写 Limitation”，否则盲审会问：

> Plan‑B 是初始化，Feature Loss 是正则化，为什么不组合？

你们不需要去补实验（也不应该补），但必须把这句话写进 limitation：

> 在劣质速度基底（近似“零速陷阱”）上，纯 2D 语义特征约束（Feature Loss）无法单骑救主，甚至可能产生优化对抗。受限于算力预算，我们未测试良性初始化（如 Plan‑B）下叠加 Feature Loss 的效果；但实证显示物理初始化（3D 运动先验）在当前设定下具有更高优先级与更强有效性。

这段话的作用是：**把“没做组合实验”从漏洞变成边界条件与未来工作**。

### 漏洞 4：会议议程太“防守”，会显得你心虚

你们的 SHA256 / template hygiene 是护城河，但不能占用主叙事时间。正确打法是：

- 一句话带过：“已通过多切片交叉验证 + template hygiene 重跑”。
- 把时间全部用来播视频、讲结果、讲机制。视觉冲击是唯一武器。
- 会议上不要再给导师 B/C 选项——强势收口到 A（写作）。

------

## 3) 你们接下来 7 天怎么排（按 2026-02-26 起算，给到“谁/交付物/验收”）

> v26 会议包要求“7 天排期表”必须当场拍板。下面这版你可以直接照抄进会后纪要/决议。

我按 **Day0–Day6**（共 7 天）列，日期写死，避免“明天/后天”漂。

### Day0（2/26，今天）：冻结 + 统一口径 + 会前弹药

**Owner A（实验/证据链）**

- 运行 5 分钟自检：校验 tar SHA、重建 report_pack、spot-check 关键 delta（seg300/400/1800）。
- 补齐吞吐证据缺口：对缺 `stats/throughput.json` 的 run_dir 跑 `scripts/write_throughput_json.py`（No‑GPU）。
- 准备会议播放清单：确保 canonical 与 seg200_260 的 step599 对比视频本地可秒开。

**Owner B（写作/叙事）**

- 立即改 Q3 话术：把“Mutual NN 是核心”替换成“物理初始化破局 + Mutual NN 稳定器”。
- 在 `docs/writing/planb_paper_outline.md` 加 Limitation（Feature Loss 与 Plan‑B 正交且未组合）。

**验收：**会议开始前，所有引用数字只来自 v26 report_pack 三件套（scoreboard/planb_anticherrypick/metrics.csv）。

------

### Day1（2/27）：核心图表与主表落地（“一页能讲清”）

**Owner A**

- 从 `manifest_sha256.csv` 指定 3 张抽帧（frame_000000/30/59）做“主图组”。
- 把 canonical + seg200_260 的 full600 指标做成“主表（Table 1）”版式（PSNR/SSIM/LPIPS/tLPIPS + Δ）。

**Owner B**

- 写完 Introduction + Problem：明确“短预算 600 steps + 稀疏视角 + 时序稳定性”为研究范围（避免 PSNR 原罪）。

**验收：**一页 PDF/slide（或 markdown）能讲清：baseline vs planb vs feature-loss 的主结论。

------

### Day2（2/28）：方法章节定稿（Plan‑B 讲清楚但不过度工程化）

**Owner A**

- 把 Plan‑B 的“可复现入口”写成方法框：脚本、runner、执行文档入口（不需要讲细枝末节）。
- Gate‑S1 统计做成一张“小表/一句话”，用于防守“初始化离谱”。

**Owner B**

- 写 Methods：一句话定义 Plan‑B（triangulation → 3D velocity init），强调“protocol_v1 不变，只替换 init velocities”。

**验收：**Methods 读完，评委能复述：你们到底改了什么、没改什么。

------

### Day3（3/1）：实验章节 + 防守附录骨架

**Owner A**

- 整理 anti-cherrypick 表（6 slices）作为 Appendix A，并注明 smoke200 vs full600 口径。
- 整理 component ablation（no_mutual）作为 Appendix B，明确“Mutual NN = stabilizer”。

**Owner B**

- 写 feature-loss v2 负结果（Appendix 或 Failure Analysis）：不是“我们失败了”，而是“假设边界/优化对抗”。

**验收：**“主文只讲主线，防守全部进附录”结构完成。

------

### Day4（3/2）：定性结果“进攻化”（视频 + 失败案例）

**Owner A**

- 挑 2–3 个最能体现“baseline 重影/闪烁 → planb 稳定”的片段（canonical + seg200_260 必选）。

**Owner B**

- 写 Qualitative 叙事：把“低 PSNR 原罪”转成“短预算下的可见改善”，并点名你们不声称收敛上限。

**验收：**你在会上播放 1 段视频，导师能直接说“确实稳了/少闪了”。

------

### Day5（3/3）：答辩/组会 slide v1 + Q&A 卡片

**Owner A + B**

- Slide 结构强制：
  1. 先播视频（5 分钟内播完）
  2. 再给主表（canonical + seg200_260 full600）
  3. 再给 anti-cherrypick（6 slices）一句话
  4. 最后才是防守（template hygiene / Gate‑S1 / ablation / feature-loss 负结果）

**验收：**slide 能在 10–12 分钟讲完，且不需要翻文档解释口径。

------

### Day6（3/4）：内审 + “签字版”会后落地文件

**Owner B**

- 输出 paper/报告 v1（可读、可提交、逻辑无漏洞）。

**Owner A**

- 若担心文稿历史残留被挑刺：可选做 v27 “文档清洁快照”（不改实验数值，只修标题/引用，重新打包 evidence 并登记 SHA）。

**验收：**

- 决议文件写死：主线 A、N=0、写作冲刺期禁止新增训练。
- v26 evidence tar + SHA 可分发、可审计。

------

## 4) 你可以直接在会上用的“升级版 Q&A”（我把矛盾点都提前拆了）

### Q1：你们是不是 cherry-pick？

A：主证据是 canonical full600 + seg200_260 full600；另外 seg300/400/600/1800 多段 smoke200 同向，其中 seg400/1800 已按 template hygiene 重跑后仍同向；所有结果可追溯到 v26 report_pack。

### Q2：Plan‑B 到底改了什么？有没有偷偷改协议？

A：不改 `protocol_v1`、不改数据/划分/训练超参，只替换 init velocities 的来源（triangulation → 3D velocity init）；执行入口与脚本在 v26 文档已固化。

### Q3：Plan‑B 是不是“速度从 0 变成非 0”的投机？

A（推荐你们采用同行升级版，但加一层“避免被抓字眼”）：

> 我们承认：打破劣质速度基底导致的收敛陷阱，是短预算下获得 1.5dB 提升的核心机制；但这不是随便给个非零速度就行。消融显示去掉 Mutual NN 匹配会显著伤害 tLPIPS 稳定性；同时 Gate‑S1 统计表明匹配率与裁剪阈值分布稳定，说明不是靠异常速度投机。

### Q4：Feature Loss 你们为什么直接判死刑？为什么不和 Plan‑B 组合？

A：Feature Loss 是正则化、Plan‑B 是初始化，两者正交；我们在“劣质速度基底”上观察到纯 2D 特征约束会与优化对抗，导致 full600 三项全劣化。受限于预算未测试“Plan‑B + Feature Loss”，已在 Limitation 中明确声明为未来工作，同时实证表明物理初始化在当前设定下优先级更高。

------

## 5) 我建议你们“会后落地”直接写进决议文件的模板（复制即可）

你们可以新建一个（名字随你，但建议带日期/版本）：

```
docs/decisions/2026-02-26-planb-v26-freeze.md
```

内容建议包含这 6 条（写死）：

1. **Mainline**：Plan‑B only（protocol_v1 不变，仅替换 init velocities）。
2. **Budget**：新增 full600 = 0；冲刺期禁止新增训练。
3. **Evidence source of truth**：会中引用数字只来自 v26 report_pack 的 scoreboard/planb_anticherrypick/metrics.csv。
4. **Scope statement**：短预算（600 steps）收敛性与时序稳定性；不声称高保真收敛上限。
5. **Limitations**：未测试 Plan‑B + Feature Loss；原因是预算；已写入论文 limitation。
6. **Deliverables (7 days)**：paper/slide v1 + 主表 + anti-cherrypick 附录 + 失败分析 + 视频清单。

------

## 最后一句（你要的“专家拍板”）

你们现在不是“还差一个实验才能证明”，而是已经完成了**可审计闭环**：Plan‑B 的 full600 主证据 + seg full600 防 cherry‑pick + 多段趋势一致 + template hygiene + 机制消融 + 定性视频。接下来 7 天唯一正确的动作就是：**冻结、收口、写作，把叙事从工程防守改成科学进攻**。