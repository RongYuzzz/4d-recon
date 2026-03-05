# OpenProposal — Phase 3/4/6 失败分析（Weak Fusion + VGGT Feature Metric + FG Realign Follow-up on THUman4.0 s00）

Date: 2026-03-05 (UTC)  
Scope: 对 Phase 3（weak-fusion）、Phase 4（VGGT feature-metric loss）以及 Phase 6（FG realign follow-up）在 THUman4.0 s00 上 **未稳定提升前景指标**（`psnr_fg`/`lpips_fg`）的原因做可审计的 root-cause 分析，并给出下一步可执行的修正方向。  
Evidence: 本文只引用仓库内 **代码片段**与本机 `outputs/`/`data/` 的 **统计结果**；遵守 local-eval 约束（不提交 `data/`/`outputs/`）。  

---

## 0) 一句话结论（可写进答辩/论文的失败边界）

- Phase 3 的 weak-fusion 由于 **“mask 语义错位 + invert 后数值饱和（几乎常数）”**，对优化信号几乎不起作用或仅产生局部噪声重权重，导致出现“全图略升但前景退化”的可重复现象。
- Phase 4 的 VGGT feature-metric loss 在当前实现下属于 **“监督过粗 + gate 过稀疏 + 时序几何先验不足”**：`phi_size=8×9` 且 `top_p=0.10` 使得每次只有 **8 个格子**参与 feature loss，难以改善以 silhouette 为 ROI 的 `psnr_fg/lpips_fg`，反而可能扰动前景细节。
- Phase 6 follow-up 的结论是“把疑点收敛”：weak-fusion 经 scaling 后不再是 no-op，但其默认设计是 **downweight dynamic**，与 fg 目标存在方向冲突；VGGT feature loss 路径在 `nogate + (ds4/ds2)` 下已证实被激活，但 fg 依旧不稳定胜过 baseline，说明主要问题更像 **信号/ROI 对齐不足**，而不只是实现 bug 或算力问题。

---

## 1) 观测到的“失败现象”（从落盘 JSON 复核）

### 1.1 Phase 3：weak-fusion（baseline vs treatment vs control）

数据与场景：
- `data/thuman4_subject00_8cam60f`（8 cams × 60 frames，test cam=09）

Runs：
- baseline：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- treatment：`.../planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- control：`.../planb_init_weak_zeros_600`

关键指标（step=599，来自 `stats/test_step0599.json` 与 `stats_masked/test_step0599.json`）：
- **全图（full-frame）**：treatment 比 baseline 更好（PSNR↑、LPIPS↓）。
- **前景（fg-masked）**：treatment 比 baseline 更差（`psnr_fg↓`、`lpips_fg↑`）。

详见（已审查文档）：
- `notes/openproposal_phase3_weak_supervision_result.md`
- `docs/reviews/2026-03-04/openproposal-phase3-review.md`

### 1.2 Phase 4：VGGT feature-metric loss（same-init 有效对照）

Runs（same-init 有效对照集）：
- baseline：`.../planb_init_600`
- treat-1：`.../planb_feat_v2_gatediff0.10_600_sameinit`（`lambda_vggt_feat=0.01`）
- treat-2：`.../planb_feat_v2_gatediff0.10_lam0.005_600_sameinit`（一次迭代，仅改 `lambda_vggt_feat`）

结论：
- guardrail `ΔtLPIPS<=+0.01` 满足；
- 但两条 treatment 的 `psnr_fg` 下降、`lpips_fg` 上升 → **主目标失败**。

详见（已审查文档）：
- `notes/openproposal_phase4_attention_contrastive.md`
- `docs/reviews/2026-03-04/openproposal-phase4-review.md`

### 1.3 Phase 6：FG realign follow-up（排障与方向性对照）

目的：把 Phase 3/4 的关键疑点从“算没算/有没有生效”收敛到“信号是否对齐 fg ROI”。Phase 6 主要做了两类 follow-up：

- Phase 3 follow-up：对 pseudo mask 做幅度标定（scaling），验证 weak-fusion 不再是 no-op；并做方向翻转对照（dynamic_scaled vs static_from_dynamic_scaled）。
- Phase 4 follow-up：先去 gating（`gating=none`），再提高 token grid 分辨率（`phi_size`：`ds4 -> ds2`），验证 feature loss 路径是否确实被激活、以及激活后对 fg 的影响。

Phase 6 的详细数据与结论见本文第 7 节，以及：
- `docs/reviews/2026-03-05/openproposal-phase6-fg-realign-followup-review.md`
- `notes/openproposal_phase6_fg_realign_phase3.md`
- `notes/openproposal_phase6_fg_realign_phase4.md`

---

## 2) Phase 3 失败原因：pseudo mask 的数值分布与语义错位

### 2.1 关键事实：Phase 3 默认使用 “invert 后的 staticness mask”

Phase 3 训练注入使用：
- `pseudo_mask_npz = outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz`
- `pseudo_mask_weight = 0.8`

见：
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_diffmaskinv_q0.950_w0.8_600/cfg.yml`
- Phase 3 计划：`docs/plans/2026-03-03-openproposal-phase3-weak-supervision.md`

invert 工具实现非常直接（摘录）：
```py
# scripts/invert_pseudo_masks_npz.py
out_masks = (255 - masks).astype(np.uint8)
```

### 2.2 关键事实：原始 diff mask 过稀疏；invert 后几乎变成常数 1

我对 Phase 3 使用的 diff `q0.950` 做了直接统计（masks 归一化到 [0,1]）：

1) 原始 dynamicness（未 invert）：
- 文件：`outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz`
- shape：`(60, 8, 143, 166)`, dtype=`uint8`
- `mean≈0.00150`
- `P99≈0.039`
- `ratio(mask>=0.5)≈1.92e-05`（几乎全都 < 0.5）

2) invert 后的 staticness：
- 文件：`outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz`
- shape：同上
- `mean≈0.99850`
- `ratio(mask>=0.5)≈0.99998`（几乎全都 > 0.5）
- `min≈0.2039`（只有极少区域明显小于 1）

**这意味着：** weak-fusion 的 mask 在绝大多数像素上几乎是常数。

### 2.3 weak-fusion 的权重公式决定了“常数 mask → 近似 no-op / 只剩噪声重权重”

训练代码（摘录）：
```py
# third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
# Interpret mask as dynamicness in [0,1], and downweight dynamic pixels:
#   w = 1 - alpha * mask, then normalize by mean(w) to keep loss scale stable.
alpha = float(cfg.pseudo_mask_weight)
w = 1.0 - alpha * mask_batch.permute(0, 2, 3, 1)
weighted_l1_loss = (torch.abs(colors - pixels) * w).mean() / w.mean().clamp(min=1e-6)
l1_loss = weighted_l1_loss
```

推论（与观测一致）：
- 若 `mask≈常数`，则 `w≈常数`，归一化后 `weighted_l1_loss≈原始 L1`，weak-fusion 对训练几乎不起作用；
- invert 后虽然整体接近常数，但 **极少像素**会偏离 1，从而造成“局部重权重”（更像噪声注入），足以导致 fg 指标轻微退化，但很难产生稳定的 fg 提升趋势。

### 2.4 语义错位：invert_staticness 被当作 “dynamicness” 使用

上面代码注释与实现都明确：mask 被解释为 **dynamicness**，并对其做 downweight。  
而 Phase 3 使用的是 `invert_staticness`（staticness），等价于把语义翻转：
- static 像素会被更强 downweight；
- 原始被认为“更动态”的像素反而获得相对更大权重（但这些区域在 diff backend 下极少且可能不稳定）。

在当前 scene（THUman4.0 s00，人物动作/背景变化都较弱）下，这个错位非常容易导致：
- 全图指标出现轻微波动（可能更稳，也可能更抖）；
- 但要把 `psnr_fg/lpips_fg` 明显推高，缺少可持续信号。

---

## 3) Phase 2/3 的 “miou_fg≈0” 主要是口径问题：同阈值对 GT 与 pred 不合理

Phase 2 的 `miou_fg` health-check 使用了 evaluator 默认阈值 `mask_thr=0.5`（同阈值同时阈值 GT 与 pred）。  
但 Phase 2 记录已表明 pred mask 的数值幅度极低（上节 P99 量级），因此 `thr=0.5` 会把 pred 判成“几乎全空”，mIoU 会接近 0。

我对 test cam=09 做了一个阈值 sweep（示例，说明 mIoU 并非“绝对没信号”，而是“阈值错位”）：
- diff `q0.950`：
  - `thr_pred=0.02 → mIoU≈0.203`
  - `thr_pred=0.50 → mIoU=0`
- vggt `q0.950`：
  - `thr_pred=0.02 → mIoU≈0.004`

结论：
- Phase 2/3 的 cue 在 **幅度标定**上与 `mask_thr=0.5` 不匹配；
- 若后续仍需要用 mIoU 做“mask 可用性体检”，应改为：
  - `thr_pred` 独立 sweep（或用 Otsu/percentile 自适应），不要固定等于 GT 的阈值；
  - 或直接报告 AUC / PR 曲线（若只做本地评测，足够）。

相关实现见：
- `scripts/eval_masked_metrics.py`（`--compute_miou` 的实现使用同一个 `mask_thr`）

---

## 4) Phase 4 失败原因：feature loss 的“监督分辨率/覆盖度”不足以推动 fg 指标

### 4.1 关键事实：VGGT cache 的 `phi_size=8×9`（极粗）

cache meta（本机落盘）：
- `outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10/meta.json`
  - `phi_name=token_proj`
  - `phi_downscale=4`
  - `input_size=[448,518]`
  - `phi_size=[8,9]`

解释：
- token/proj 的 feature map 本质是 patch grid；在 downscale=4 下进一步变粗，最终只有 `8×9=72` 个格子。
- 这类 loss 对“细节与边界”的约束能力天然弱；而 `psnr_fg/lpips_fg` 的 ROI 来自 silhouette，边界/细节非常关键。

### 4.2 关键事实：`top_p=0.10` gate → 每次只激活 8 个格子

训练中 gate 的实现是 top-p 二值 mask（摘录）：
```py
# third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
def _top_p_mask(self, score_map, top_p):
  total = hf * wf
  k = ceil(top_p * total)
  topk_idx = torch.topk(flat, k=k).indices
  mask_flat.scatter_(1, topk_idx, 1.0)
```

在 `phi_size=8×9` 时：
- `total=72`
- `top_p=0.10 → k=ceil(7.2)=8`

这不是推测：TB 中 `vggt_feat/active=8.0`（只在 step 0/200/400 这些“真正计算 feature loss”的 step 记录到）。

**结论：** Phase 4 的 feature loss 实际上是“每次只约束 8 个粗格子”，其优化目标很难与 `psnr_fg/lpips_fg`（silhouette ROI）直接对齐。

### 4.3 训练并非“没算”：feature loss 确实生效，但信号过弱/过粗

TB 复核（以 `planb_feat_v2_gatediff0.10_600_sameinit` 为例）：
- `loss_weighted/feat` 在 step 200/400 非零（符合 `vggt_feat_every=8` 与 `tb_every=50` 的采样规律）。
- step 0 的 `loss_weighted/feat=0` 是因为 `vggt_feat_ramp_steps=400`：起始时 lambda≈0，属于预期。

因此 Phase 4 的失败更像是：
- “算了，但这个算的东西（粗格子 + 稀疏 gate）对 fg 指标没帮助”，而不是实现 bug。

---

## 5) 上游限制：时序几何监督极弱，会放大 Phase 3/4 的不确定性

两个可审计事实：
1) triangulation 只有 frame 0（几乎没有跨帧几何约束）  
   - `data/thuman4_subject00_8cam60f/triangulation/` 仅含 `points3d_frame000000.npy` 等
2) Plan-B init NPZ 不提供速度（velocities/has_velocity 全 0）  
   - `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

这意味着：
- 想依靠“feature/weak reweight”去显著改善 dynamic/fg 的时序细节，本身就处在较难的先验条件下；
- 更合理的顺序通常是：先补足更强的时序监督/对应（例如 temporal correspondences / 更密 triangulation），再谈 feature/cue 的精细对齐。

---

## 6) 下一步“最小代价修正”建议（按 ROI=fg 指标优先级排序）

> 目标是让后续实验更有机会提升 `psnr_fg/lpips_fg`，同时保持可审计与时间可控；这里给的是设计建议，不改动现有证据链。

### 6.1 修正 Phase 3 的 mask 语义与数值标定（不改 trainer 也能做）

1) **不要直接 invert 再当 dynamicness 用**  
   - 若仍想用当前 weak-fusion（downweight dynamicness），就喂 **dynamicness**（未 invert 的 `pseudo_masks.npz`），并调 `pseudo_mask_weight`（例如 0.2/0.4/0.6）看是否有一致趋势。

2) **对 pred mask 做幅度标定（把“极稀疏小数值”拉伸到可用区间）**  
   - 例如 per-frame/per-view percentile normalize：把 P95→1、P50→0（或 P90→1），再 clip 到 [0,1]。
   - 目的：让 `pseudo_mask_weight` 真正产生可控的像素重权重，而不是“几乎常数”。

3) **mIoU 体检改成 pred 阈值 sweep**  
   - 先用 `thr_pred` sweep 找到能对齐 silhouette 的阈值范围，再决定固定阈值或自适应阈值。

### 6.2 修正 Phase 4 的 feature loss 覆盖度（保持实现不大改）

1) **提高 phi 分辨率**：将 `phi_downscale` 从 4 降到 2（甚至 1）  
   - 直觉：从 `8×9` 提升到更细网格，feature loss 才可能影响 silhouette 边界与细节。

2) **放宽 gate**：把 `top_p` 从 0.10 提高到 0.30/0.50，或先关 gate（`gating=none`）做一次 sanity  
   - 在粗网格上过稀 gate（只剩 8 格）几乎不可能稳定改善 fg。

3) **实现/替代 cue gating**（让 gate 真正对齐 silhouette ROI）  
   - 当前代码里 `gating='cue'` 明确未实现（会 fallback 到 none 并 warning）。
   - 若要对齐 fg，最直接的 gate 是：用 dataset silhouette（或更可靠的 pseudo mask）在 phi-space 做投影 gate。

---

## 7) Phase 6 follow-up：把“没稳定达成 fg 目标”的原因收敛到哪里

Phase 6 的定位不是“换一个方法再赌一次”，而是对 Phase 3/4 的关键疑点做排障与方向性实验（timebox=600 steps）：

- Plan: `docs/plans/2026-03-05-openproposal-fg-realign-followup.md`
- Review: `docs/reviews/2026-03-05/openproposal-phase6-fg-realign-followup-review.md`
- Notes（结果细节与路径）：`notes/openproposal_phase6_fg_realign_phase3.md`、`notes/openproposal_phase6_fg_realign_phase4.md`

### 7.1 Phase 6 的关键改动（确保结论可归因）

1) **消除 weak-fusion 的 “mask 近似常数 → 近似 no-op”**  
对 Phase 3 用到的 diff `q0.950` pseudo mask 做幅度标定（percentile scaling）：

- 工具：`scripts/scale_pseudo_masks_npz.py`
- 产物：`pseudo_masks_dyn_p99.npz` 与 `pseudo_masks_static_from_dyn_p99.npz`

2) **让 fg 评测更“敏感/可解释”**（避免只盯 `psnr_fg/lpips_fg` 时被单点噪声误导）  
在 `scripts/eval_masked_metrics.py` 增加：
- `psnr_fg_area`：更像“fg ROI 内的像素能量/面积型”指标
- `lpips_fg_comp`：comp 口径（与 fill-black/crop 的交互更可控）
- `lpips_backend`：显式记录 backend（确保是 real LPIPS）

3) **把 mask “可用性”从单一阈值解耦出来**  
提供阈值 sweep 的体检工具，避免 Phase 2/3 的 `mIoU≈0` 误判：
- 工具：`scripts/mask_healthcheck_sweep.py`

### 7.2 Phase 6 — Phase 3 follow-up（weak-fusion：scaling + 方向翻转）

Runs（same-init fairness gate 一致）：
- baseline：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- dynamic_scaled：`.../planb_init_weak_dynp99_w0.8_600_r1`
- static_from_dynamic_scaled：`.../planb_init_weak_staticp99_w0.8_600_r1`

关键结果（step=599；来自 `stats/test_step0599.json` 与 `stats_masked/test_step0599.json`）：

| run | psnr | lpips | tlpips | psnr_fg | lpips_fg | psnr_fg_area | lpips_fg_comp |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16.1520 | 0.7325 | 0.007053 | 16.8066 | 0.24388 | 9.8674 | 0.04960 |
| dyn_p99_w0.8_r1 | 16.3438 | 0.7331 | 0.007187 | 16.5294 | 0.24611 | 9.5901 | 0.05174 |
| static_p99_w0.8_r1 | 16.2658 | 0.7437 | 0.008740 | 17.1048 | 0.24271 | 10.1655 | 0.05044 |

解释（为什么这组结果能“收敛疑点”）：

- weak-fusion 的真实机制是 **downweight dynamicness**：`w = 1 - α·mask_dyn`（再除以 `mean(w)` 稳定尺度），见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` 的 weak-fusion 片段（第 2.3 节已摘录）。
- 因此在 **dynamic_scaled** 下，mask 越“动态/更像人”，权重越小 → 对 fg ROI 的重建信号被压弱，出现 `psnr_fg↓`、`lpips_fg↑` 是符合机制预期的。
- 而 **static_from_dynamic_scaled** 等价于喂入 `mask_sta = 1 - mask_dyn`：  
  `w = 1 - α·mask_sta = (1-α) + α·mask_dyn`  
  归一化后，相当于 **相对 upweight 更动态/更像 fg 的区域**。这与本轮看到的 `psnr_fg↑`、`lpips_fg↓` 一致（但全图 `lpips` 变差，也符合“把优化预算从背景挪向 fg”的 trade-off）。

结论（Phase 3 方向层面）：
- Phase 3 原版失败并不只因为“没信号/没算”，更关键的是 **方向**：在当前 trainer 里，weak-fusion 的默认设计会压弱动态/fg；要追 fg 指标，至少需要“方向翻转/ROI 对齐”的机制。
- 同时注意：即便做了 scaling，`static_from_dynamic_scaled` 的 mask 仍偏饱和（见 `notes/openproposal_phase6_fg_realign_phase3.md` 里的均值统计），说明这条路要想“稳定双赢”，仍需要更好的幅度标定与 schedule，而不是单点调参。

### 7.3 Phase 6 — Phase 4 follow-up（VGGT feature loss：nogate + 提高 phi_size）

Runs（same-init fairness gate 一致）：
- baseline：`.../planb_init_600`
- nogate + ds4：`.../planb_feat_v2_nogate_lam0.005_600_sameinit_r1`（`phi_size=8×9`）
- nogate + ds2：`.../planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1`（`phi_size=16×18`）

监督路径激活证据（TB 导出 CSV；结论写入 `notes/openproposal_phase6_fg_realign_phase4.md`）：
- ds4：`vggt_feat/active=72`（与 token grid 一致）
- ds2：`vggt_feat/active=288`（与 token grid 一致）

关键结果（step=599）：

| run | psnr | lpips | tlpips | psnr_fg | lpips_fg | psnr_fg_area | lpips_fg_comp |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16.1520 | 0.7325 | 0.007053 | 16.8066 | 0.24388 | 9.8674 | 0.04960 |
| feat_nogate_ds4_r1 | 16.1570 | 0.7314 | 0.007293 | 16.6825 | 0.24208 | 9.7433 | 0.05062 |
| feat_nogate_ds2_r1 | 16.1195 | 0.7367 | 0.007025 | 16.5078 | 0.24835 | 9.5686 | 0.05087 |

解释（为什么它仍没稳定达成 fg 目标）：

- 本轮已排除“没算/没激活”：`vggt_feat/active` 与 `phi_size` 对齐说明 feature loss 真的在参与优化。
- 但 nogate/ds2 仍不稳定赢 fg，意味着主因更像是 **feature 监督与 silhouette ROI 的对齐不足**（尤其是边界/细节），以及其对重建目标的干扰可能大于收益。
- 另一个结构性事实：当前实现中 `gating='cue'` 并未实现，会直接 fallback 到 none（摘录）：
  ```py
  # third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
  gating_mode = str(cfg.vggt_feat_gating).strip().lower()
  if gating_mode == "cue":
      print("[VGGTFeat][WARN] gating='cue' is not implemented. Falling back to none.")
  ```
  这解释了为什么 Phase 4 想“用 cue 对齐 fg”的直觉在当前代码里无法成立：缺少一个把 feature loss 投影到 silhouette/fg 的 gate。

结论（Phase 4 边界层面）：
- 以当前 `token_proj + cosine + lambda=0.005` 的组合，即使做 `nogate`、提高 `phi_size`，也没有形成稳定的 fg 胜出趋势 → Phase 4 在这条配置线上止损是合理的。

### 7.4 Phase 6 之后的“更窄 root-cause 链路”（你现在真正缺的是什么）

Phase 6 把 Phase 3/4 的问题从“实现/配置误差”进一步收敛为：

- **Phase 3：方向性问题是主因之一**。当前 weak-fusion 的默认机制在做 `downweight dynamic`，与“要提升 fg”存在冲突；当你通过 `static_from_dynamic_scaled` 让它等价于“相对 upweight 动态/fg”后，fg 指标出现了更符合预期的变化，但伴随全图代价与稳定性问题（说明还需更好的幅度标定/日程/ROI 对齐）。
- **Phase 4：不是没激活，而是信号没对齐**。feature loss 算得很“粗/全局”，且缺少 cue/silhouette gate；在时序几何先验很弱（triangulation 仅 frame0，velocities=0）的前提下，更难指望它稳定推动 fg 细节。

---

## Appendix A) 复核本文关键数值的本机命令（local only）

1) 统计 mask 分布（示例：diff q0.950 + invert）：
```bash
python3 - <<'PY'
import numpy as np
def stats(path):
  with np.load(path, allow_pickle=True) as d: m=d["masks"]
  m01=m.astype("float32")/255.0 if m.dtype==np.uint8 else m.astype("float32")
  flat=m01.reshape(-1)
  print(path)
  print(" shape", m.shape, "dtype", m.dtype)
  print(" min/max/mean", float(flat.min()), float(flat.max()), float(flat.mean()))
  for p in [50,90,95,99,99.5,99.9]:
    print(" p%g"%p, float(np.quantile(flat, p/100.0)))
  for thr in [0.01,0.05,0.1,0.2,0.5]:
    print(" ratio>=",thr, float((flat>=thr).mean()))
  print()
stats("outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz")
stats("outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz")
PY
```

2) 查看 VGGT cache meta：
```bash
cat outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10/meta.json
```

3) 从 TB 提取 `pseudo_mask/active_ratio`（Phase 3 treatment）：
```bash
python3 - <<'PY'
import glob
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
files=sorted(glob.glob("outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_diffmaskinv_q0.950_w0.8_600/tb/events.out.tfevents.*"))
for f in files:
  ea=EventAccumulator(f); ea.Reload()
  if "pseudo_mask/active_ratio" in ea.Tags()["scalars"]:
    ev=ea.Scalars("pseudo_mask/active_ratio")
    print(f, "n=",len(ev), "first=", (ev[0].step, ev[0].value), "last=", (ev[-1].step, ev[-1].value))
PY
```

4) 从 TB 提取 Phase 4 的 `vggt_feat/active` 与 `loss_weighted/feat`：
```bash
python3 - <<'PY'
import glob
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
run="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600_sameinit"
f=sorted(glob.glob(run+"/tb/events.out.tfevents.*"))[0]
ea=EventAccumulator(f); ea.Reload()
for tag in ["vggt_feat/active","loss_weighted/feat","loss/feat_raw"]:
  ev=ea.Scalars(tag); print(tag, [(e.step, float(e.value)) for e in ev])
PY
```
