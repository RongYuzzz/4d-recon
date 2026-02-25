# 4d-recon 项目后续推进会议包（用于“完成项目”拍板）

日期：2026-02-26（建议会议时间：02-26 或 02-27，45 分钟）  
主阵地：`/root/projects/4d-recon`  
唯一真源协议：`docs/protocol.yaml`（-> `docs/protocols/protocol_v1.yaml`）  
会前材料来源：`docs/reviews/2026-02-25/review-2026-02-25-v1.md`、`docs/reviews/2026-02-25/review-2026-02-25-v2.md`  

---

## 0. 本次会议要“当场拍板”的输出（必须写死）

> 会议结束时，必须产出 3 件事：**单一路线**、**止损线**、**7 天排期表**。  
> 否则我们会继续在“能跑但结论漂”的状态里打转。

1. **后续主线选择（只能选 1 条）**
   - 选项 A：继续推进 Feature-Loss（VGGT feature prior）但需要“明确要改什么、最多几次 full600”
   - 选项 B：切换到 Plan‑B（基于 `triangulation/*.npy` 的 3D velocity 初始化），timebox 48h
   - 选项 C：停止新增 full600，把现有结果固化为“负结果 + 强失败分析”，以写作为主（仅补最少防 cherry-pick）
2. **full600 剩余预算（写死数字）**
   - 例：未来 7 天最多 `N=2~4` 次 full600（不含 smoke200），并写清楚分别给哪条路线用
3. **验收口径（写入协议或决议文件）**
   - 是否仍沿用当前成功线（`tLPIPS -10%` / `LPIPS -0.01` / `PSNR +0.2dB`）？
   - 是否允许 trade-off：`tLPIPS` 达标但 `PSNR/LPIPS` 轻微退化（阈值写死）？

### 0.1 会前纪律（直到会议拍板前都遵守）

1. **暂停新增 full600**：会前只允许做“无需 full600 的失败归因准备/可视化/脚本补齐/200-step sanity”（除非导师明确要求跑某个 full600）。
2. **禁止改协议分布项**：帧段/相机/scale/step/resolution/densification 一律不动；若要动，必须会议拍板并升级 `protocol_v2`。

---

## 1. 现状一页纸（给导师/专家/同行快速扫完）

### 1.1 资源与约束

- 当前可用人力：A、B（C 暂不可用）
- 当前算力：2 张卡（GPU0/GPU1）；B 近期可能阶段性无 GPU（以当天为准）
- 协议纪律：任何影响训练分布的改动（帧段/相机/scale/step/resolution/densification）必须升级 `protocol_v2.yaml` 并重跑 baseline/control（禁止“悄悄改”）
- 大文件策略：`data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库；只入库 `docs/report_pack/*` 文本快照与 `artifacts/report_packs/SHA256SUMS.txt`

### 1.2 冻结协议（Protocol v1，canonical）

见：`docs/protocols/protocol_v1.yaml`

- 数据：`data/selfcap_bar_8cam60f`（SelfCap bar，8 cams × 60 frames）
- 相机：02–09（train 02–07 / val 08 / test 09）
- 帧段：`frame000000`–`frame000059`
- 冻结超参：`seed=42`、`keyframe_step=5`、`global_scale=6`、`image_downscale=2`、`MAX_STEPS=600`
- 主指标：PSNR/SSIM/LPIPS + **tLPIPS**（test cam 连续帧稳定性）

### 1.3 当前“硬结论”（已可审计）

来源：
- canonical 主对比：`docs/report_pack/2026-02-25-v13/metrics.csv`
- v2 post-fix 最终判定：`docs/report_pack/2026-02-25-v15/metrics.csv`、`notes/v2_postfix_summary_owner_a.md`

| 运行（test@599） | PSNR | LPIPS | tLPIPS | 相对 baseline_600 | 结论 |
| --- | ---: | ---: | ---: | --- | --- |
| baseline_600 | 18.9496 | 0.4048 | 0.0230 | — | canonical baseline |
| ours_weak_600 | 19.0194 | 0.4037 | 0.0231 | PSNR 小涨，tLPIPS 几乎不动 | weak 没形成稳定优势 |
| control_weak_nocue_600 | 19.1099 | 0.4033 | 0.0236 | **PSNR/LPIPS 更好**，tLPIPS 更差 | 风险信号：cue 注入可能在“帮倒忙/无效” |
| feature_loss_v2_postfix_600 | 18.6752 | 0.4219 | 0.0261 | ΔPSNR -0.2744，ΔLPIPS +0.0172，ΔtLPIPS +0.0031 | **No‑Go（M2 失败）** |

结论一句话：
- **Feature-loss v2 已按 Gate 执行到 M2，post-fix 仍无正向趋势**；继续“盲跑 full600”不划算。
- 当前最紧迫的不是再写新 loss，而是：**明确下一条主线（继续 v2 还是触发 Plan‑B），并冻结 7 天计划**。

### 1.4 会议上必须问清楚的 4 个问题（否则无法收敛）

1. **论文/毕设目标优先级**：必须有“指标正向提升”吗？还是可接受“负结果 + 强失败分析”作为主贡献？
2. **是否立即切 Plan‑B**：什么条件下立刻切、切了就不回头继续 v2？
3. **算力预算**：未来 7 天/14 天最多还能给几次 full600？
4. **成功线是否调整**：继续沿用当前成功线，还是会议拍板修改并版本化（`protocol_v2` 或单独决议）？

---

## 2. 我们已经排除/确认的事情（避免会议反复争论）

### 2.1 已排除的“显性工程坑”

- `token_proj` 与 cache downscale **对齐 bug 已修复并有单测锁死**：
  - 修复与测试：`scripts/tests/test_token_proj_resize_alignment.py`
  - 修复说明：trainer 侧先在原 patch 网格投影，再 `bilinear resize` 到 cache `phi_size`（避免左上角截断错位）
- 吞吐已可审计（≤2x 止损线能证据化）：
  - 统一产出：`stats/throughput.json`（runner 已接入）
  - evidence 自动收录：`scripts/pack_evidence.py`
  - smoke200 对比+Pareto：`scripts/analyze_smoke200_m1.py`

### 2.2 已确认的事实（对后续路线有约束意义）

- M1（smoke200）可以“看起来 OK”，但 **full600 会显著拖垮 PSNR/LPIPS/tLPIPS**（至少在当前 v2 配置线中成立）
- 目前最好的 PSNR/LPIPS 来自 `control_weak_nocue_600`，说明：
  - “weak 的代码路径本身”不是问题
  - “cue 的信息/注入方式”才是主风险点（可能噪声、对齐、或权重破坏了优化）

---

## 3. 关键未知：为什么 M1 PASS 但 M2 全维变差？

> 这一段的目的：把“猜”变成“可验证假设”，从而决定该不该继续烧 full600。

建议在会议上选 **3 条** 最可能的假设作为“下一周唯一诊断主线”，每条假设对应一个**无需 full600**即可判断方向的实验/可视化。

1. **loss 权重/日程在后期开始主导（把 photometric 压死）**
   - 现象：早期还行，后期开始过度正则，细节/对齐/时序都变差
   - 快速验证：在 full600 的日志里画 `L_photo` vs `L_feat` 的量级曲线（或每 50 step 的均值）；确认是否出现 `L_feat` 主导
2. **phi 选择不适合“像素级对齐误差”显著的 4DGS early stage**
   - 现象：特征损失在惩罚坐标误差而不是结构误差
   - 快速验证：做 `I_gt` 的 cache round-trip 与在线一致性（已具备工具），再做一组“对 GT 做 1~2px 平移”的敏感性曲线（无需训练）
3. **gating/patch 采样没有真正命中动态区域（或命中的是噪声）**
   - 现象：feature loss 变成背景正则/噪声正则，带来负迁移
   - 快速验证：导出 gated patch 的空间分布热图（覆盖 60 帧），检查是否集中在动态体/边界/遮挡处
4. **梯度链在某个分支被无意切断（“看起来跑了”但没优化到想要的变量）**
   - 快速验证：在 10 step 小跑里打印 `∂L_feat/∂(render_rgb)` 与 `∂L_feat/∂(gaussian params)` 的 norm（不需要 full600）

---

## 4. 路线选项（会议的核心：选 1 条）

### 选项 A：继续 Feature‑Loss（但必须“改动点写死 + full600 上限写死”）

适用条件：
- 专家认为上述关键未知中存在“明确可修”的 1~2 个根因，且预计 **1 次 full600** 就能验证趋势

必须写死的纪律：
- 允许的改动只限于：`phi/loss/gating/patch schedule/lambda schedule`（不得改协议分布项）
- full600 上限：`<= 2` 次（包含 gated），超过直接止损

预期交付：
- 1 页“失败归因/修复点”说明 + 1 次 full600 结果（无论正负）

### 选项 B：触发 Plan‑B（triangulation → 3D velocity init，48h timebox）

适用条件：
- 我们需要一个**更“物理一致”的改动点**，而不是继续在 feature 正则上赌
- 可接受：即使最终没提升，也能产出“可审计失败证据”（对毕设写作很重要）

纪律（必须写进脚本头注释与执行文档）：
- 不改 `data/`，不改 `protocol_v1`；输出只到 `outputs/plan_b/...`
- 脚本必须带自检并落盘：
  - `||v||` 的 mean/p50/p90/p99/max
  - `ratio(||v|| < 1e-4)`
  - 时间尺度说明（`t` 的单位/归一化方式）

建议 timebox 内最小交付：
1. `scripts/init_velocity_from_points.py`（战备库存变可执行）
2. 200-step sanity（baseline_init vs planb_init）
3. 1 次 full600（只跑 1 次，作为 Go/No-Go）

### 选项 C：停止新增 full600，以写作与失败分析为主（只补最少防 cherry-pick）

适用条件：
- 导师/评审可以接受“负结果 + 强失败分析”作为核心贡献（需会议当场确认）

最小必交（为了让“负结果”也显得像研究）：
- 明确的 Gate/止损纪律（我们已经有）
- 失败归因页：为什么这些路线在 canonical 下失败（含可视化）
- anti-cherrypick：seg2 或第二段 short-run 作为防守证据

---

## 5. 建议会议议程（45 分钟）

1. 5 min：对齐目标（“完成项目”Definition of Done + 还能烧几次 full600）
2. 10 min：事实快照（协议 + 四条关键指标表 + v2 No-Go）
3. 15 min：三路线讨论（A/B/C）+ 风险/收益/时间
4. 10 min：当场拍板（主线 + 止损线 + 7 天排期 + 谁负责）
5. 5 min：会后行动（写入 `docs/decisions/`，冻结计划并执行）

---

## 6. 会前“打开就能看”的证据索引（建议按顺序）

1. 当前进度与结论总览：`Progress.md`
2. 协议真源：`docs/protocols/protocol_v1.yaml`
3. canonical 完整指标表（含 weak/control/strong/v1）：`docs/report_pack/2026-02-25-v13/metrics.csv`
4. v2 post-fix 最终判定（只含 v2 相关项）：`docs/report_pack/2026-02-25-v15/metrics.csv`、`notes/v2_postfix_summary_owner_a.md`
5. 外部评审原文：`docs/reviews/2026-02-25/review-2026-02-25-v1.md`、`docs/reviews/2026-02-25/review-2026-02-25-v2.md`
6. 既有路线图（可能需要更新）：`docs/reviews/2026-02-25/final-roadmap-discussion-pack.md`

---

## 7. 会后落地要求（避免“会开完就散”）

会议结束后 2 小时内必须完成：

1. 新建决议文件（唯一真源）：
   - 建议路径：`docs/decisions/2026-02-26-finish-roadmap.md`
2. 把“主线/止损线/full600 预算/7 天排期”写死到决议文件
3. 把需要执行的命令与产物路径写死（避免口头复述）
