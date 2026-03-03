# v27 推进计划：双重引导框架（Plan‑B 物理先验 + VGGT 几何语义先验）

日期：2026-02-27  
适用仓库：`/root/projects/4d-recon`  
目的：在不破坏 v26（Plan‑B）既有证据链的前提下，把开题承诺补齐到“可实现 + 可复现 + 可答辩”的程度。

依据（本计划不新增观点，仅落地执行）：
- 同行 A 审核：`docs/reviews/2026-02-27/review-2026-02-27.md`
- 专家 B 拍板：`docs/reviews/2026-02-27/decisions-2026-02-27.md`

---

## 0. 统一叙事（之后所有文档都按这一句说）

> **先用 Plan‑B 提供物理合理的初始运动（避免零速/劣速基底陷阱），再用 VGGT 的几何一致语义特征提供特征空间一致性约束（Feature Metric / Attention‑guided Consistency），最后用动静解耦渲染展示可编辑性（object removal）。**

---

## 1. 冻结与升级策略（避免冲掉 v26 证据链）

1. 保留并继续引用 v26 的“阶段一物理底座”证据链（不改口径，不回滚）：  
   - 冻结决议：`docs/decisions/2026-02-26-planb-v26-freeze.md`  
   - 数字真源：`docs/report_pack/2026-02-26-v26/`
2. 所有“对齐开题”的新增实验统一开 **新协议**（建议名：`protocol_v2_semantic` 或 `protocol_semantic_v1`），必须写清：
   - 新增 loss / 权重范围 / warmup / timebox
   - 成功线与止损线（尤其避免再次出现“control 更好但不承认”的口径风险）
3. 训练纪律：高风险项（attention‑guided 对应/对比学习）**严格 timebox 72h**，失败即收口为负结果材料。

---

## 2. v27 优先级（从“最稳能交付”到“加分项”）

### P0：开题文本对齐（必须，避免口径攻击）

- 产物：建议新建 `4D-Reconstruction-v2.md`（保留 `4D-Reconstruction.md` 原稿），完成以下修改：
  1) 新增【本文主要贡献】（对标 FreeTimeGS / VGGT4D / Split4D）  
  2) 把“端到端”改成“无需外部 2D 强监督前置（SAM/DEVA）”  
  3) 把“注意力→对应→损失”写成可实现版本（patch/top‑k + loss 落点定义）  
  4) 评测口径改为 SelfCap + tLPIPS（Neural3DV/Multi‑Human 作为扩展，不承诺必做）  
  5) 增加资源约束与止损策略（Plan‑B 作为保底交付）

### P1：兑现“动静解耦 + 可编辑性”（最稳的强定性结果）

- 目标：从已有训练 ckpt 直接导出“仅静态高斯”的轨迹视频（背景干净版）。
- 方法：按 `||v||` 阈值分割 static/dynamic，export-only 渲染静态子集（不新增训练）。
- 产物：背景视频 + 一张 `||v||` 统计（阈值说明）+ 1 个失败例（limitation）。

### P2：VGGT 线索挖掘可视化（先做“可解释材料”，不急着追指标）

- 目标：输出 VGGT 特征（或 token_proj phi）的 PCA/聚类可视化图，用于 Method/Appendix Figure。
- 产物：跨视角一致的彩色特征图 / 聚类图（3–5 帧即可），证明“几何语义先验确实存在”。

### P3：Plan‑B + VGGT Feature Metric Loss（阶段二的关键量化实验）

- 目标：在 Plan‑B 物理底座上重启 feature metric loss（先从稳定可控的版本做起），看是否改善遮挡/纹理漂移下的稳定性。
- 策略：
  - warmup：前 100–200 steps 不开 feature loss
  - ramp：线性爬坡（例如 400 steps）
  - 低权重起步（例如 lambda=0.005~0.01），先 smoke200 再 full600
- 产物：新协议下的 `metrics.csv/scoreboard.md` + 失败归因（若无提升）。

### P4（加分项）：注意力引导对应/对比学习（严格 72h timebox）

- 只允许 patch/token 级 top‑k 稀疏对应；必须带对应可视化，否则一律判不可答辩。

---

## 3. 立即可落地的仓库 TODO（对应脚本/文件）

1. 新建/更新开题 v2：`4D-Reconstruction-v2.md`（或直接改 `4D-Reconstruction.md` 也可，但建议保留历史）
2. 静态导出工具：
   - 在 trainer 的 `--export-only` 路径下增加“按速度过滤后再渲染”的开关
3. 新增 runner：
   - `scripts/run_train_planb_feature_loss_v2_selfcap.sh`：Plan‑B init + feature-loss v2（warmup/ramp/低 lambda）

