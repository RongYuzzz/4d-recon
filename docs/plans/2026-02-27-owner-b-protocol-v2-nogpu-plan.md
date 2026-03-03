# Owner B (No-GPU) Protocol v2 Docs/Packaging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不使用 GPU 的前提下，完成 protocol_v2（双阶段框架）的“可答辩材料补齐”：开题文本 v2、方法可实现定义、评测口径/止损/资源约束说明，以及 protocol_v2 的报表/素材落盘与索引（等待 A 的 GPU 产物后做填空式合入）。

**Architecture:** B 侧工作分两段：
1) 立即可并行：纯文档与脚本侧的“叙事/口径/可实现性”修订（不依赖 GPU 产物）。  
2) A 产物到位后：把 static/dynamic 视频、VGGT cache、smoke200 stats 等路径回填到文档与 report-pack 索引，并生成 protocol_v2 的 scoreboard。

**Tech Stack:** Markdown、Python（现有 `scripts/build_report_pack.py` / `scripts/summarize_scoreboard.py`）、仓库既有决议/协议文件。

---

## Task 0: Preflight（No-GPU + 对齐真源）

**Files:**
- Read: `docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- Read: `docs/protocols/protocol_v2.yaml`
- Read: `docs/plans/2026-02-27-postreview-roadmap.md`
- Read: `4D-Reconstruction.md`

**Step 1: 明确“阶段一/阶段二”边界与不变量**

核对以下口径在你后续所有文本中一致：
- 阶段一证据链：`v26 + protocol_v1`（保留不动）
- 阶段二新增：`protocol_v2`（所有新实验/新结论必须归入 v2，避免与 v26 数值混用）

---

## Task 1: 输出对外可提交的开题文本（v2，不带内部审阅段）

**Files:**
- Create: `4D-Reconstruction-v2.md`
- Read: `docs/reviews/2026-02-27/opening-proposal-review-4D-Reconstruction.md`
- Read: `docs/reviews/2026-02-27/review-2026-02-27.md`
- Read: `docs/reviews/2026-02-27/decisions-2026-02-27.md`

**Step 1: 基于 `4D-Reconstruction.md` 生成 v2 草稿**

做法：
- 复制 `4D-Reconstruction.md` → `4D-Reconstruction-v2.md`
- 删除/不包含末尾“内部审阅要点（2026-02-27）”段（对外版本不带内部审阅记录）

**Step 2: 新增【本文主要贡献】（3 条可验证条目）**

放置位置建议：在“研究的主要内容与预期目标”之前或之后（但要显眼）。

必须覆盖：
- 对比 FreeTimeGS：修复劣速/零速基底（Plan‑B 速度初始化）→ 体现为短预算下 tLPIPS/稳定性收益
- 对比 Split4D：避免重度逐帧对比学习管线 → 用更轻量、可审计的 render-and-compare/feature metric
- 对比 VGGT4D：不把大模型当 2D mask 生成器 → 用几何一致特征做 4DGS 的软先验约束

**Step 3: 修正“端到端”表述（可辩护版本）**

全局替换/改写要点：
- 从“**不依赖任何外部 2D 分割/跟踪器**”改为：
  - “**无需外部 2D 强监督前置（如 SAM/DEVA 掩码或 tracker 轨迹）**”
  - 说明 VGGT/伪掩码属于冻结的软先验（soft prior），以 loss/weight 形式注入

**Step 4: 把‘注意力→对应→对比损失’写成可实现版本**

写作目标：回答三个同行必问点（不要求论文级推导，但必须可实现/可复现）：
- 高斯“特征”是什么（建议：为 Gaussian 附加可学习特征，splat 渲染成 2D feature map）
- 像素/patch ↔ 高斯怎么绑定（建议：通过 rasterizer 的 splatting 权重天然绑定）
- 对应如何稀疏化（建议：patch/token 级 + top‑k；明确不是 O((HW)^2)）

可选：把“跨帧 attention 对应”作为加分项/未来工作，主实现先落在 feature metric（蒸馏式）以保证可跑。

**Step 5: 调整预期目标与评测口径**

必须修改：
- 删除 “Neural3DV / Multi‑Human + mIoU 保证优于 ……” 这类硬承诺
- 改为：SelfCap + PSNR/SSIM/LPIPS + **tLPIPS（时序稳定）**，措辞用“对标/力争/显著改善”

**Step 6: 增补‘资源约束与止损策略’**

要求：
- 写清 full600 的预算口径（不确定绝对时长时，可写“以 `stats/throughput.json` 为准并落盘”）
- 模块分级：MVP 必做（Plan‑B + tLPIPS + demo），加分项（VGGT feature metric），高风险项（attention 对应/对比学习）
- 明确止损线与回退：阶段二失败不影响阶段一交付（Plan‑B 为保底）

**Step 7: 修正文献小问题（观感项）**

根据内部审阅：
- FreeTimeGS URL 空格修正
- 重复作者修正（如 Yohann Cabon 重复）

---

## Task 2: 准备 protocol_v2 的“填空式材料框架”（等待 A 产物回填）

**Files:**
- Create: `docs/report_pack/2026-02-27-v2/README.md`
- Create: `docs/report_pack/2026-02-27-v2/scoreboard.md` (placeholder, later overwritten)

**Step 1: 创建 report-pack 占位目录**

创建 `docs/report_pack/2026-02-27-v2/README.md`，内容只放三块：
- protocol_v2 的目标与不变量（不要引用 v26 数值）
- 需要 A 提供的 3 类产物路径（static/dynamic 视频、VGGT cache、smoke200 stats）
- 生成 scoreboard 的命令（见 Task 3）

---

## Task 3: protocol_v2 scoreboard 生成（No-GPU，等 A 跑完再执行）

**Files:**
- Read: `outputs/report_pack/metrics.csv`
- Create/Update: `docs/report_pack/2026-02-27-v2/scoreboard.md`

**Step 1: 刷新 metrics.csv（等 A 的 stats 落盘后）**

Run: `python3 scripts/build_report_pack.py`  
Expected: `outputs/report_pack/metrics.csv` 更新，包含 `outputs/protocol_v2/...` 的行。

**Step 2: 生成 protocol_v2 scoreboard（smoke200 或 full600）**

示例（smoke200 时 step=199；full600 时 step=599）：
```bash
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2/ \
  --stage test \
  --step 199
```
Expected: `docs/report_pack/2026-02-27-v2/scoreboard.md` 生成成功，且 header 的 filter/prefix 指向 `outputs/protocol_v2/`。

---

## Task 4: 回填 A 的 GPU 产物路径（并行对接点）

**Files:**
- Update: `docs/report_pack/2026-02-27-v2/README.md`
- Update: `4D-Reconstruction-v2.md`
- Optional Update: `docs/plans/2026-02-27-postreview-roadmap.md`

**Step 1: 等 A 发出最终路径后回填**

需要 A 提供（以实际输出为准）：
- static-only / dynamic-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_*_tau*/videos/traj_4d_step*.mp4`
- VGGT cache：`outputs/vggt_cache/*/gt_cache.npz` + `meta.json`
- smoke200 stats：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200*/stats/test_step0199.json`

在 `4D-Reconstruction-v2.md` 的“动静解耦验证/可编辑性”与“VGGT 特征约束可落地性/资源约束”处引用这些路径（避免空口无凭）。

