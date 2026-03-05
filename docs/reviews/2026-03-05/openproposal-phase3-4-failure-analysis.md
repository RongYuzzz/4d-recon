# OpenProposal — Phase 3/4 失败分析（Weak Fusion + VGGT Feature Metric on THUman4.0 s00）

Date: 2026-03-05 (UTC)  
Scope: 对 Phase 3（weak-fusion）与 Phase 4（VGGT feature-metric loss）在 THUman4.0 s00 上 **未提升前景指标**（`psnr_fg`/`lpips_fg`）的原因做可审计的 root-cause 分析，并给出下一步可执行的修正方向。  
Evidence: 本文只引用仓库内 **代码片段**与本机 `outputs/`/`data/` 的 **统计结果**；遵守 local-eval 约束（不提交 `data/`/`outputs/`）。  

---

## 0) 一句话结论（可写进答辩/论文的失败边界）

- Phase 3 的 weak-fusion 由于 **“mask 语义错位 + invert 后数值饱和（几乎常数）”**，对优化信号几乎不起作用或仅产生局部噪声重权重，导致出现“全图略升但前景退化”的可重复现象。
- Phase 4 的 VGGT feature-metric loss 在当前实现下属于 **“监督过粗 + gate 过稀疏 + 时序几何先验不足”**：`phi_size=8×9` 且 `top_p=0.10` 使得每次只有 **8 个格子**参与 feature loss，难以改善以 silhouette 为 ROI 的 `psnr_fg/lpips_fg`，反而可能扰动前景细节。

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


## Follow-up outcome (Phase 6)

- Phase 3 weak-fusion follow-up: scaling removed clear no-op behavior, and `static_from_dynamic_scaled` outperformed `dynamic_scaled` on foreground-local metrics (`psnr_fg`, `lpips_fg`, `psnr_fg_area`) while keeping `ΔtLPIPS` within guardrail (`<= +0.01`).
- Phase 4 feature-loss follow-up: `gating=none` and `phi_size` increase (`ds4 -> ds2`) both activated the intended supervision path (`vggt_feat/active` matched token grid size), but foreground quality still did not beat baseline consistently.
- Updated failure boundary: for current `token_proj + cosine + lambda=0.005` settings, even `ds2 + nogate` remains a non-winning treatment for fg ROI; prioritize Phase 3 direction for next iterations and treat Phase 4 as stop-loss at this configuration.
