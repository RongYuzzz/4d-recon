# 2026-02-27 决议：采用“双阶段框架”，在不破坏 v26 证据链前提下补齐开题（protocol_v2）

日期：2026-02-27  
适用仓库：`/root/projects/4d-recon`  
依据材料：
- 同行 A：`docs/reviews/2026-02-27/review-2026-02-27.md`
- 专家 B：`docs/reviews/2026-02-27/decisions-2026-02-27.md`

---

## 1. 背景（为什么要升级路线）

开题 `4D-Reconstruction.md` 的主叙事是 VGGT 语义/注意力驱动的 4D 重建；而仓库当前“最硬的证据链”已经收口为 **Plan‑B（3D velocity init）** 并在 `protocol_v1` 下显著改善 tLPIPS。  
若不修正路线，答辩会被最致命的口径攻击：**“你开题说做 VGGT，最后交付速度初始化，你到底研究了什么？”**

---

## 2. 最终拍板（统一叙事与技术路线）

**不走“硬拽回 VGGT 单主线”。** 后续路线统一为：

> **阶段一：物理运动先验（Plan‑B）**——用更物理一致的 3D 差分速度初始化，修复劣速/零速基底导致的收敛陷阱。  
> **阶段二：几何语义先验（VGGT）**——在物理底座上加入可实现的 feature metric / attention-guided consistency 约束，提升遮挡/纹理漂移下的时空对齐稳定性。  
> **展示：动静解耦 + 可编辑性（object removal）**——基于速度阈值的静/动层分离渲染，产出强定性演示。

---

## 3. 证据链纪律（必须遵守）

1. **`v26 + protocol_v1` 作为阶段一最终证据链保留不动**（写作与引用口径继续可用）。  
2. 所有“补齐开题/学术完善”的新实验与新结论统一归入 **`protocol_v2`**，避免与 v26 数值混用。
3. `protocol_v2` 的每条实验必须写清：新增 loss、权重范围、warmup、timebox、成功线/止损线，并产出可审计产物（视频/可视化/日志）。

协议文件：
- 阶段一（冻结）：`docs/protocols/protocol_v1.yaml`（由 `docs/protocol.yaml` 指向）
- 阶段二（新增）：`docs/protocols/protocol_v2.yaml`（新增，不覆盖 v1）

---

## 4. protocol_v2 必做交付（按优先级）

### A. 动静解耦渲染（必须，低成本高冲击）

- 实现：按 `||v||` 阈值将 Gaussians 分成 static/dynamic 两层导出视频（允许仅导出，不要求重训）。
- 交付：static-only 背景视频 + dynamic-only 视频 + 速度直方图与阈值说明（含失败例）。

### B. VGGT 线索挖掘可视化（必须，补齐可解释材料）

- 实现：VGGT feature 的 PCA / 聚类可视化（3–5 帧 × 多视角即可）。
- 交付：彩色特征图/簇图 + 跨视角一致性对比图（写入论文方法/附录）。

### C. Plan‑B + Feature Metric Loss（必须，关键实验）

- 纪律：必须 warmup + ramp，且先 smoke 后 full；若出现全线劣化按止损线收口。
- 交付：至少 1 个可复现实验（含超参、曲线、val/test 指标与定性片段）。

### D. 注意力引导对应/对比损失（加分项，严格 timebox）

- 只允许 patch/token 级 + top‑k 稀疏对应；对应质量必须可视化。
- 建议 timebox：72h 到点停；不允许拖死主线。

---

## 5. 文档修订（必须同步）

对 `4D-Reconstruction.md` 的修订目标是“可答辩”而非“写得宏大”：

1. 新增贡献列表：对标 FreeTimeGS / Split4D / VGGT4D 的**可验证**差异点。
2. 修正“端到端”：改为“无需外部 2D 强监督前置（SAM/DEVA/tracker）”；VGGT/伪掩码属于软先验（以 loss/weight 注入）。
3. 把“注意力引导对比损失”写成可实现版本：稀疏化策略 + loss 落点 + 像素/patch↔高斯绑定方式。
4. 调整评测口径与措辞：以 SelfCap + PSNR/LPIPS/tLPIPS 为主；删除不现实的 mIoU/Neural3DV/Multi‑Human 强承诺。
5. 增补资源约束与止损策略：MVP 必做 vs 加分项，失败回退明确写 Plan‑B 保底。

---

## 6. 下一步动作（落地到仓库）

1. 新增 `protocol_v2`：`docs/protocols/protocol_v2.yaml`（不覆盖 v1）。
2. 新增执行路线图：`docs/plans/2026-02-27-postreview-roadmap.md`。
3. 后续实验产物统一落 `outputs/protocol_v2/...`，并在 `docs/report_pack/<date>-v2/` 形成新快照。

