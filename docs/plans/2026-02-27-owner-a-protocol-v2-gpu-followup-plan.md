# Owner A（GPU0 / 32GB）后续计划（protocol_v2 follow-up）

日期：2026-02-27  
目标：在已 **PASS** 的 protocol_v2 基础上，把“开题承诺补齐到可答辩”的剩余硬缺口补齐，并在不盲烧卡的前提下尝试拿到 1 个**有正收益趋势**的 stage‑2 实验（若无趋势，按止损纪律收口）。

依据：
- 路线图：`docs/plans/2026-02-27-postreview-roadmap.md`
- 决议：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- A 侧审计：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

资源约束：
- 仅使用 GPU0（32GB）
- 所有新结论/新实验统一写入 `outputs/protocol_v2/...`（不污染 `protocol_v1/v26` 证据链）

---

## Task 1（必须）：补齐“VGGT 线索挖掘/可解释材料”到可答辩

> 目的：让答辩时能回答“你从 VGGT 挖到了什么、证据在哪、失败边界是什么”，不要求先闭环指标收益。

### 1.1 固化一份“VGGT cue / 伪掩码”证据包（可直接引用路径）

- 复用已有产物（无需重跑）：
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam*_frame*.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/grid_frame000000.jpg`
- 产出 1 份短 note（若已有可补充即可）：
  - 建议：新建/补齐 `notes/protocol_v2_vggt_cue_viz.md`
  - 内容最少包含：使用的 cue 定义、可视化样例路径、`quality.json` 关键数字、1 个失败例/边界说明。

### 1.2（推荐加固）：基于 `token_proj` cache 做 PCA(3D)->RGB 的 feature 可视化

> 目的：补齐“feature 本体”的图，而不仅是伪掩码 overlay；选 3–5 帧 × 多视角即可。

- 输入真源（已落盘）：
  - `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
  - `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/meta.json`
- 期望输出（建议落盘到 cache 同目录，便于审计）：
  - `outputs/vggt_cache/.../viz_pca/`
    - `pca_rgb_cam02_frame000000.jpg`（至少）
    - `grid_pca_frame000000.jpg`（至少）
    -（可选）`pca_rgb_cam02_frame000030.jpg` 等
- 交付要求：
  - **同一帧跨视角颜色尽量一致**（PCA 基底需固定：建议对“同一帧的多视角 token_proj”一起拟合 PCA，再投影到各视角）
  - 写入 `notes/protocol_v2_vggt_feature_pca.md`：说明 PCA 拟合范围、归一化/拉伸方式、一个失败例（例如纹理相似导致混簇）。

**验收标准**：B 能从 note 里直接复制路径到开题/论文，并且你能现场解释“这些图代表什么/不代表什么”。

---

## Task 2（可选，但强建议 timebox）：让 stage‑2 至少出现一次“非全线劣化”的 full600

> 背景：当前 `planb_feat_v2_full600_lam0.005_warm100_ramp400` 相对 `planb_init_600` 触发止损（PSNR/LPIPS/tLPIPS 全劣化），已经按纪律停止。这里仅允许 **小步**、**可解释**、**可审计** 的尝试。

### 2.1 先 smoke200 做趋势筛选（不通过就停）

候选 1（最小改动）：**framediff gating**（只在变化更明显区域施加 feature loss）

- 关键开关：
  - `VGGT_FEAT_GATING=framediff`
  - `VGGT_FEAT_GATING_TOP_P=0.10`（需与 cache `meta.json: framediff_top_p` 对齐；否则 top‑p 会对二值 mask 产生不稳定子采样）
- 运行：
  - 以 `smoke200` 先看是否稳定、是否相对 `planb_init_smoke200` 至少“非明显退步”

候选 2（如果候选1稳定但仍劣化）：**降低 lambda**

- 仅尝试 1 个更保守点，例如：
  - `LAMBDA_VGGT_FEAT=0.002`（或 0.001）

### 2.2 通过 smoke200 gate 后，再跑 1 次 full600（最多 1 次）

止损线（沿用 02‑27 协议）：
- 若 full600 的 test `PSNR/LPIPS/tLPIPS` 再次出现“全线劣化 vs planb_init_600”，立即停止，不做盲 sweep。

审计要求：
- 把新 run 的命令、产物路径、相对 `planb_init_600` 的 delta 写入同一份审计 note（建议直接追加到 `notes/protocol_v2_planb_feat_smoke200_owner_a.md`，避免散落）。

**验收标准**：要么拿到 1 个 full600 的“非全线劣化”结果并可解释；要么形成可引用的 failure analysis（为什么 gating/降权仍不行，下一步该换什么假设）。

---

## Task 3（加分项，严格 timebox=72h）：稀疏对应/可视化（贴近“注意力→对应→对比”承诺）

> 只做“可解释 + 可视化”的最小闭环，不追求立刻进训练主线。

建议交付：
- 产出 1 个 `outputs/correspondences/<tag>/viz/*.jpg` 的对应可视化（patch/token top‑k）
- 1 份 note：`notes/protocol_v2_sparse_corr_viz.md`（解释对应质量、失败例）

到点停：72h 内没有清晰可视化与可解释结论，则写入 limitation / future work，不再扩展。

---

## Handoff（给 B 的固定输出口径）

当 Task 1/2 任一完成后，给 B 发送以下“可复制粘贴”的路径清单：
- VGGT cue/伪掩码：`outputs/cue_mining/.../viz/*` + `quality.json` + 对应 note
- VGGT token_proj PCA：`outputs/vggt_cache/.../viz_pca/*` + 对应 note（若完成）
- stage‑2 最终实验（若有新 run）：`outputs/protocol_v2/.../stats/test_step0199|0599.json` + 审计 note

