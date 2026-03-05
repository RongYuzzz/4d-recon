# Expert Diagnosis Dossier — OpenProposal Phase 3/4/6 (THUman4.0 s00)

Date: 2026-03-05 (UTC)  
Audience: 同行/专家（帮忙定位 root-cause + 给出“最小验证实验”建议）  
Scope: Phase 3（weak-fusion）、Phase 4（VGGT feature-metric loss）、Phase 6（FG realign follow-up）  
Constraints: **local-eval only**（不提供 raw dataset 帧/GT RGB；可提供 cfg/JSON 指标、渲染视频、非原图可视化与关键代码片段）

> **更完整的一站式材料请使用：** `docs/reviews/2026-03-05/expert-diagnosis-dossier_openproposal_phase2-7_preexpert.md`（包含 Phase2/7 与 pre-expert 复核）。

> 本文把分散在多个 note/review 中的材料合并成“一篇能读完就给建议”的文档；同时保持可审计：每个关键结论都能在证据包里找到对应 cfg/JSON/video/代码片段。

---

## 0) 我希望你回答的问题（请按此诊断）

在 THUman4.0 subject00（8 cams × 60 frames）上，我的目标是：

- **核心效果目标（FG）**：silhouette ROI 上 `psnr_fg ↑` 且 `lpips_fg ↓`
- **guardrail（全图）**：`ΔtLPIPS <= +0.01`（全图时间一致性不显著变差）

我尝试了两条主线，但都未能**稳定达成** FG 目标：

- Phase 3：Plan‑B init + weak-fusion（pseudo mask reweight）
- Phase 4：Plan‑B init + VGGT feature-metric loss（token_proj + framediff top‑p gating）

随后我做了 Phase 6 follow-up（排障/对齐实验），目的是把问题从“实现/没算/不公平”收敛到“信号是否对齐 silhouette ROI”。

请你基于本文与证据包：

1) 给出 **3–5 个最可能根因**（按置信度排序）；  
2) 每个根因给出 **1 个最小改动验证实验**（改什么、预期变化、判定标准）。

---

## 1) 证据包（你不用跑代码即可复核）

我提供了一个不含 raw dataset 帧的证据包（含 sha256 manifest）：

- `expert_diagnosis_pack_2026-03-05.tar.gz`
- 包内 `manifest_sha256.csv` 可做完整性校验
- 包内 `EXPERT_PACK_INDEX.md` 是文件索引

包内包含：

- 关键文档（Phase 3/4/6 结果与失败分析）
- 关键代码（trainer 的 weak-fusion / vggt feature loss、评测脚本、Phase 6 工具）
- 每个关键 run 的 `cfg.yml` + `stats/test_step0599.json` + `stats_masked/test_step0599*.json`
- 每个关键 run 的渲染视频：`videos/traj_4d_step599.mp4`
- 非原图可视化：token top‑k、TB scalars CSV、Phase 3 的 render-vs-render 对比视频等

**刻意不包含：**

- `data/`（任何 raw dataset 帧/GT RGB/相机原图）
- `outputs/**/renders/`（GT 对比图，容易夹带原图）
- `outputs/cue_mining/**/viz/`（overlay 基于原图）
- `outputs/**/tb/` 原始 event 文件（只给导出 CSV）

---

## 2) 数据、拆分与评测口径（决定一切是否可比）

### 2.1 数据与拆分（固定）

Data dir（不在证据包内）：`data/thuman4_subject00_8cam60f`

固定设置（从各 run 的 `cfg.yml` 可复核）：

- frames：`start_frame=0`, `end_frame=60`（共 60）
- train cams：`02,03,04,05,06,07`
- val cam：`08`
- test cam：`09`

上游限制（可审计事实；会影响时序监督强度）：

- triangulation 仅有 frame 0（跨帧几何约束极弱）
- Plan‑B init NPZ 不提供 velocity（`has_velocity==0`, `velocities==0`）

### 2.2 指标来源与 FG ROI 的定义（必须看清）

全图指标来自 trainer 落盘：

- `outputs/**/stats/test_step0599.json`（PSNR/SSIM/LPIPS/tLPIPS 等）

前景指标来自 evaluator（bbox crop + fill-black，ROI=dataset silhouette）：

- script：`scripts/eval_masked_metrics.py`
- 输出：`outputs/**/stats_masked/test_step0599*.json`

核心逻辑（摘录；细节以脚本为准）：

```py
bbox = _bbox_from_mask(gt_mask01, thr=mask_thr, margin=bbox_margin_px)
gt_crop   = gt[bbox].copy()
pred_crop = pred[bbox].copy()
keep = (gt_mask_crop > mask_thr).astype(np.float32)[..., None]
gt_crop   *= keep
pred_crop *= keep
psnr_fg  = mean(PSNR(pred_crop, gt_crop))
lpips_fg = mean(LPIPS(pred_crop, gt_crop))
```

本次所有 Phase 3/4/6 的 FG 评测使用同一口径（见各 note 记录）：

- `mask_source=dataset`
- `mask_thr=0.5`
- `bbox_margin_px=32`
- `lpips_backend=auto`（真实 LPIPS；通过 FreeTimeGsVanilla venv）

> 注意：`psnr_fg/lpips_fg` 对 silhouette 边界/细节非常敏感；训练目标若不显式对齐 ROI，很容易出现“全图还行，但 fg 不稳”的现象。

---

## 3) Runs 总览（同 init 的公平性 gate 已满足）

所有比较均满足“同 init NPZ”（从 `cfg.yml:init_npz_path` 可复核）：

- `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

### 3.1 Baseline anchor

- baseline：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`

### 3.2 Phase 3（weak-fusion）

- treatment：`.../planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- control（weak path + no cue）：`.../planb_init_weak_zeros_600`

### 3.3 Phase 4（VGGT feature-metric loss，same-init）

- treat‑1：`.../planb_feat_v2_gatediff0.10_600_sameinit`（`lambda_vggt_feat=0.01`）
- treat‑2：`.../planb_feat_v2_gatediff0.10_lam0.005_600_sameinit`（`lambda_vggt_feat=0.005`）

### 3.4 Phase 6（follow-up：FG realign）

Phase 6 的目标是排障与方向性对照：

- Phase 3 follow-up（scaling + 方向翻转）
  - dyn_scaled：`.../planb_init_weak_dynp99_w0.8_600_r1`
  - static_from_dyn_scaled：`.../planb_init_weak_staticp99_w0.8_600_r1`
- Phase 4 follow-up（激活性澄清）
  - nogate + ds4：`.../planb_feat_v2_nogate_lam0.005_600_sameinit_r1`（`phi_size=8×9`）
  - nogate + ds2：`.../planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1`（`phi_size=16×18`）

---

## 4) 关键结果（step=599；只列最重要指标）

### 4.1 Phase 3（weak-fusion）：全图略升，但 FG 退化

（完整见：`notes/openproposal_phase3_weak_supervision_result.md`）

| run | PSNR | SSIM | LPIPS | PSNR_FG | LPIPS_FG |
|---|---:|---:|---:|---:|---:|
| baseline `planb_init_600` | 16.1520 | 0.5621 | 0.7325 | 16.8066 | 0.2439 |
| treatment `diffmaskinv q0.950 w0.8` | 16.2809 | 0.5657 | 0.7265 | 16.6361 | 0.2508 |
| control `zeros w0.8` | 16.1574 | 0.5622 | 0.7347 | 16.4846 | 0.2446 |

结论：

- 全图：treatment 相对 baseline 有提升；
- FG：treatment 相对 baseline **退化**（`psnr_fg↓`、`lpips_fg↑`）。

### 4.2 Phase 4（VGGT feature loss）：guardrail PASS，但 FG 退化

（完整见：`notes/openproposal_phase4_attention_contrastive.md`）

| run | ΔtLPIPS | Δpsnr_fg | Δlpips_fg |
|---|---:|---:|---:|
| treat‑1 `lam=0.01` | +0.001030 | -0.348228 | +0.012048 |
| treat‑2 `lam=0.005` | +0.000043 | -0.124590 | +0.008596 |

结论：

- guardrail：`ΔtLPIPS<=+0.01` 通过；
- FG：两条 treatment 都未达成目标（`psnr_fg` 下降且 `lpips_fg` 上升）。

### 4.3 Phase 6 follow-up（排障结论）：问题主要不是“没算”，而是“信号/ROI 对齐不足”

#### Phase 6 / weak-fusion（scaling + 方向翻转）

（完整见：`notes/openproposal_phase6_fg_realign_phase3.md`）

| run | psnr | lpips | tlpips | psnr_fg | lpips_fg | psnr_fg_area | lpips_fg_comp |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16.1520 | 0.7325 | 0.007053 | 16.8066 | 0.24388 | 9.8674 | 0.04960 |
| dyn_p99_w0.8_r1 | 16.3438 | 0.7331 | 0.007187 | 16.5294 | 0.24611 | 9.5901 | 0.05174 |
| static_p99_w0.8_r1 | 16.2658 | 0.7437 | 0.008740 | 17.1048 | 0.24271 | 10.1655 | 0.05044 |

结论要点：

- scaling 后，weak 路径不再是明显 no-op（TB `pseudo_mask/active_ratio` 不再接近 1.0 饱和）。
- 方向翻转显示：`static_from_dynamic_scaled` 在 fg-local 指标上更接近目标，但伴随全图 lpips 代价 → 存在 trade-off。

#### Phase 6 / feature loss（nogate + 提高 phi_size）

（完整见：`notes/openproposal_phase6_fg_realign_phase4.md`）

| run | psnr | lpips | tlpips | psnr_fg | lpips_fg | psnr_fg_area | lpips_fg_comp |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16.1520 | 0.7325 | 0.007053 | 16.8066 | 0.24388 | 9.8674 | 0.04960 |
| feat_nogate_ds4_r1 | 16.1570 | 0.7314 | 0.007293 | 16.6825 | 0.24208 | 9.7433 | 0.05062 |
| feat_nogate_ds2_r1 | 16.1195 | 0.7367 | 0.007025 | 16.5078 | 0.24835 | 9.5686 | 0.05087 |

结论要点：

- `vggt_feat/active` 与 token grid 数量匹配（ds4=72、ds2=288）→ feature loss 路径确实被激活；
- 但 fg 仍不稳定胜过 baseline → 更像“信号不对齐 silhouette ROI”，不是“没算/没生效”。

---

## 5) 关键机制证据（为什么这些结果不是偶然）

### 5.1 Phase 3：mask 语义 + 数值分布错位（导致弱监督方向性不利于 fg）

Phase 3 训练注入使用（见 `cfg.yml`）：

- `pseudo_mask_npz = outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz`
- `pseudo_mask_weight = 0.8`

mask 统计（见失败分析文档的直接统计）：

- 原始 diff dynamicness：`mean≈0.00150`（极稀疏）
- invert 后 staticness：`mean≈0.99850`（几乎常数 1）

weak-fusion 代码将 mask 解释为 dynamicness 并降权动态像素（摘录）：

```py
# Interpret mask as dynamicness in [0,1], and downweight dynamic pixels:
#   w = 1 - alpha * mask, then normalize by mean(w) to keep loss scale stable.
w = 1.0 - alpha * mask
weighted_l1 = mean(|pred-gt| * w) / mean(w)
```

这解释了两个现象：

1) mask 若接近常数，归一化后 weak-fusion 接近 baseline L1（近似 no-op）；  
2) 即便 scaling 后有信号，机制仍倾向于“压弱动态/前景”→ 与 fg 目标天然冲突；方向翻转后 fg 指标变化更符合预期，但出现全图代价（trade-off）。

### 5.2 Phase 4：feature loss 监督“粗 + 稀疏 gate”

Phase 4 cache meta（见证据包）：

- ds4：`phi_size=[8,9]`（72 cells）
- `top_p=0.10` → 每次 gate 只激活 `ceil(0.1*72)=8` 个格子

gate 实现是 top‑p mask：

```py
k = ceil(top_p * (Hf*Wf))
mask_flat.scatter_(..., topk_idx, 1.0)
```

另外：`gating='cue'` 在当前实现中未实现，会 fallback 到 none（见 warning）。

这些事实共同意味着：Phase 4 的 feature loss 很难稳定对齐到 silhouette ROI 的边界/细节优化；Phase 6 已进一步确认“路径在算”，因此更可能是监督目标/覆盖度不匹配 ROI。

---

## 6) 我当前最需要你的建议（请给最小验证实验）

请你优先回答：

1) **如果把目标钉死在 FG 指标（psnr_fg↑、lpips_fg↓），训练目标应该如何对齐 ROI？**  
   - 是改 weak-fusion 的权重方向（upweight fg）？  
   - 还是让 feature loss 只在 silhouette ROI 生效（需要实现 cue/silhouette gating）？  
   - 或者需要先补足时序几何/对应（triangulation/velocity/corr）再谈 feature/cue？

2) **你认为最小、最值得做的 1–2 个实验是什么？**  
   请明确：改动点、预期趋势、通过/失败判据（最好只改一个变量）。

---

## Appendix A) 关键文件索引（证据包里都有）

读本：

- `docs/reviews/2026-03-05/expert-diagnosis-pack_phase3-4.md`
- `docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md`
- `docs/reviews/2026-03-05/openproposal-phase6-fg-realign-followup-review.md`

Phase 结果：

- `notes/openproposal_phase3_weak_supervision_result.md`
- `notes/openproposal_phase4_attention_contrastive.md`
- `notes/openproposal_phase6_fg_realign_phase3.md`
- `notes/openproposal_phase6_fg_realign_phase4.md`

关键 runs（每条都有 cfg + stats + masked stats + 视频）：

- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_zeros_600`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600_sameinit`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_lam0.005_600_sameinit`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_dynp99_w0.8_600_r1`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w0.8_600_r1`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_nogate_lam0.005_600_sameinit_r1`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1`

非原图可视化：

- `outputs/qualitative_local/openproposal_phase3/planb_vs_weak_step599.mp4`
- `outputs/qualitative_local/openproposal_phase4/tokenproj_topk/*.jpg`
- `outputs/qualitative_local/openproposal_phase6/tb_scalars/*.csv`

---

## Appendix B) 关键代码摘录（让专家只读本文也能理解机制）

> 说明：以下摘录仅覆盖“直接决定结果走向/口径”的关键片段；更完整上下文请看对应源文件。

### B.1 FG evaluator：`psnr_fg/lpips_fg` 的 ROI 与 fill-black（`scripts/eval_masked_metrics.py`）

关键点：

- 从 concat canvas 中切出 GT|Pred；
- 用 `mask_source=dataset` 时读取 `masks/*.png`；
- 用 GT mask 计算 bbox，并在 bbox 内做 fill-black（只保留 ROI 内前景像素）；
- `miou_fg` 的实现对 GT 与 pred 使用同一个 `mask_thr`（这会导致 pred mask 幅度很低时 mIoU≈0）。

```py
# scripts/eval_masked_metrics.py (around line ~240)
canvas = _load_rgb01(render_path)
width = canvas.shape[1] // 2
gt = canvas[:, :width, :]
pred = canvas[:, width:, :]

if args.mask_source == "dataset":
    mask_path = gt_mask_dir / f"{frame_offset:06d}.png"
    mask01 = _load_mask01(mask_path)
else:
    pred_small = _load_pred_mask_tv(pred_npz, camera=camera, t_local=frame_offset)
    mask_img = Image.fromarray((pred_small * 255.0).astype(np.uint8), mode="L")
    mask_img = mask_img.resize((gt.shape[1], gt.shape[0]), resample=Image.Resampling.BILINEAR)
    mask01 = np.asarray(mask_img, dtype=np.float32) / 255.0

bbox = _bbox_from_mask(mask01, thr=float(args.mask_thr), margin=margin)
if bbox is None:
    continue

gt_crop = gt[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1].copy()
pred_crop = pred[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1].copy()
mask_crop = mask01[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1]
keep = (mask_crop > float(args.mask_thr)).astype(np.float32)[..., None]
gt_crop *= keep
pred_crop *= keep

psnr_list.append(_psnr(pred_crop, gt_crop))
value_lpips = lpips_fn(pred_crop, gt_crop)
if value_lpips is not None:
    lpips_list.append(float(value_lpips))

if args.compute_miou:
    gt_bin = mask01 > float(args.mask_thr)
    pred_small = _load_pred_mask_tv(pred_npz, camera=camera, t_local=frame_offset)
    pred_img = Image.fromarray((pred_small * 255.0).astype(np.uint8), mode="L")
    pred_img = pred_img.resize((gt.shape[1], gt.shape[0]), resample=Image.Resampling.BILINEAR)
    pred01 = np.asarray(pred_img, dtype=np.float32) / 255.0
    pred_bin = pred01 > float(args.mask_thr)
    inter = float(np.logical_and(gt_bin, pred_bin).sum())
    union = float(np.logical_or(gt_bin, pred_bin).sum())
    if union > 0:
        iou_list.append(inter / union)
```

### B.2 Weak-fusion：mask 被解释为 dynamicness 并“降权 dynamic”（`simple_trainer_freetime_4d_pure_relocation.py`）

关键点：

- mask 的语义是 **dynamicness in [0,1]**；
- `w = 1 - α·mask_dyn`，并且除以 `mean(w)` 保持 loss 尺度稳定；
- 这对 “mask 近似常数” 极易退化为 near no-op；
- 也意味着 weak-fusion 的默认设计倾向于 **压弱动态/前景区域的重建监督**。

```py
# third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py (around line ~3725)
use_weak_fusion = (
    self.pseudo_masks is not None
    and cfg.pseudo_mask_weight > 0.0
    and cfg.pseudo_mask_end_step > 0
    and step < cfg.pseudo_mask_end_step
)
if use_weak_fusion:
    mask_batch = self._get_pseudo_mask_batch(
        frame_idx=data["frame_idx"],
        camera_idx=data["camera_idx"],
        height=height,
        width=width,
    )  # [B,1,H,W]
    if mask_batch is not None:
        # Interpret mask as dynamicness in [0,1], and downweight dynamic pixels:
        #   w = 1 - alpha * mask, then normalize by mean(w) to keep loss scale stable.
        alpha = float(cfg.pseudo_mask_weight)
        alpha = max(0.0, min(1.0, alpha))
        w = 1.0 - alpha * mask_batch.permute(0, 2, 3, 1)  # [B,H,W,1]
        weighted_l1_loss = (torch.abs(colors - pixels) * w).mean() / w.mean().clamp(min=1e-6)
        l1_loss = weighted_l1_loss
        pseudo_mask_active_ratio = float(mask_batch.mean().item())
```

### B.3 Phase 6 的“排障证据”为什么可信：TB 标量里有明确 tag

```py
# third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py (around line ~3975)
if pseudo_mask_active_ratio is not None:
    self.writer.add_scalar("pseudo_mask/active_ratio", pseudo_mask_active_ratio, step)
if feat_active > 0:
    self.writer.add_scalar("vggt_feat/active", feat_active, step)
```

对应导出产物（在证据包中）：

- `outputs/qualitative_local/openproposal_phase6/tb_scalars/planb_init_weak_dynp99_w0.8_600_r1_tb_scalars.csv`
- `outputs/qualitative_local/openproposal_phase6/tb_scalars/planb_feat_v2_nogate_lam0.005_600_sameinit_r1_tb_scalars.csv`
- `outputs/qualitative_local/openproposal_phase6/tb_scalars/planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1_tb_scalars.csv`

### B.4 VGGT feature loss：top‑p gate、`gating='cue'` 未实现、active 计数（`simple_trainer_freetime_4d_pure_relocation.py`）

Top‑p mask（注意 `k = ceil(top_p * total)`）：

```py
# around line ~2594
def _top_p_mask(self, score_map: Tensor, top_p: float) -> Tensor:
    bsz, _, hf, wf = score_map.shape
    total = int(hf * wf)
    if top_p <= 0.0:
        return torch.zeros_like(score_map, dtype=torch.float32)
    if top_p >= 1.0:
        return torch.ones_like(score_map, dtype=torch.float32)
    k = max(1, min(total, int(math.ceil(float(top_p) * float(total)))))
    flat = score_map.reshape(bsz, total)
    topk_idx = torch.topk(flat, k=k, dim=1, largest=True, sorted=False).indices
    mask_flat = torch.zeros_like(flat, dtype=torch.float32)
    mask_flat.scatter_(1, topk_idx, 1.0)
    return mask_flat.reshape(bsz, 1, hf, wf)
```

Gate 逻辑（`cue` 未实现会 fallback；`framediff` 会转成 top‑p 二值 mask）：

```py
# around line ~2701
gating_mode = str(cfg.vggt_feat_gating).strip().lower()
if gating_mode == "cue":
    print("[VGGTFeat][WARN] gating='cue' is not implemented. Falling back to none.")
elif gating_mode == "framediff":
    ...
    gate_mask = self._top_p_mask(gate_use, float(cfg.vggt_feat_gating_top_p))
    weight_map = gate_mask if weight_map is None else (weight_map * gate_mask)
```

loss 与 active 的定义（active=weight_map>0 的数量；nogate 时 active=全部 token）：

```py
# around line ~2745
if weight_map is None:
    feat_loss = loss_map.mean()
    active = int(loss_map.shape[0] * loss_map.shape[-2] * loss_map.shape[-1])
    return feat_loss, active

w_sum = weight_map.sum()
feat_loss = (loss_map * weight_map).sum() / w_sum.clamp(min=1e-6)
active = int((weight_map > 0).sum().item())
return feat_loss, active
```

### B.5 Phase 6 的 pseudo-mask scaling（`scripts/scale_pseudo_masks_npz.py`）

目标：把“幅度极低/极稀疏”的 pseudo mask 拉伸到可用范围，避免 weak-fusion 因 mask 近似常数而 no-op，并提供方向翻转对照（`static_from_dynamic_scaled = 1 - dyn_scaled`）。

```py
# scripts/scale_pseudo_masks_npz.py (around line ~64)
m01 = _to_float01(masks)
q = float(np.quantile(m01.reshape(-1), float(args.quantile)))
denom = q + float(args.eps)
dyn = np.clip(m01 / denom, 0.0, 1.0).astype(np.float32)
if args.mode == "dynamic_scaled":
    out_masks = dyn
else:
    out_masks = (1.0 - dyn).astype(np.float32)
```

---

如需完整可审计证据包（cfg/JSON/视频/可视化 + sha256 manifest），可索取 `expert_diagnosis_pack_2026-03-05_v2.tar.gz`。

---

## Phase 7 addendum (ROI-alignment MVEs, 2026-03-05)

### MVE-1: weak-fusion early-only（no code change）

我们在 `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w0.8_end200_600_r2` 上执行了最小 schedule 验证（`static_from_dynamic_scaled q0.99`, `weight=0.8`, `end_step=200`），并确认 baseline 与 treatment 使用同一 `init_npz_path`（same-init fairness 成立）。

量化结果：guardrail 通过（`ΔtLPIPS=+0.000174`），但核心 ROI 指标失败：`psnr_fg 16.8066 -> 16.4705 (Δ-0.3361)`，`lpips_fg 0.243883 -> 0.254362 (Δ+0.010479)`；并且 `psnr_fg_area/lpips_fg_comp` 与 boundary-band (`psnr_bd_area/lpips_bd_comp`) 同向变差。该模式不是“接近可用的 trade-off”，而是 silhouette ROI 的系统性退化。

因此本轮未触发 `END_STEP=300` 的条件补跑，避免在已失败方向上继续消耗计算预算。

### MVE-2: feature loss with cue-gated silhouette（small code change）

Phase7 已实现 `gating='cue'` 的稠密 silhouette gate，并用 `scripts/tests/test_vggt_feat_cue_gate_downsample.py` 完成 RED→GREEN 验证。实验 run：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_cuegate_lam0.005_600_sameinit_r2`；same-init fairness 通过。

监督激活证据来自 TB：`vggt_feat/active` 在 step `0/200/400` 分别为 `19/21/16`（非零）。即“feature loss 没起作用”的解释被排除。尽管如此，ROI 仍失败：`psnr_fg 16.8066 -> 16.4042 (Δ-0.4025)`，`lpips_fg 0.243883 -> 0.256594 (Δ+0.012711)`；边界带也恶化（`Δpsnr_bd_area=-0.2820`, `Δlpips_bd_comp=+0.000294`）。同时全图指标基本中性（`Δpsnr=+0.1624`, `Δlpips=-0.00053`），guardrail 仍通过（`ΔtLPIPS=+0.000405`）。

该结果说明：即使在 oracle-style ROI gating 条件下，feature loss 线路也没有呈现稳定 silhouette ROI 改善。

### Stop/Go

- **Stop（建议）**：两条 MVE（weak early-only / cue-gated feature loss）均未达到 `psnr_fg↑ & lpips_fg↓` 的核心目标。
- 建议将“止损结论”写入主结论：当前 weak/feat 路线主要表现为 trade-off 调参，尚不具备稳定 ROI 提升能力。
- **Go 条件（仅保留为未来入口）**：若要继续，应建立新的假设与最小试验（如更强几何约束或边界专用监督），而不是在当前参数族内继续扫描。

---

## Pre‑Expert addendum (seed replication of the only FG‑win setting, 2026-03-05)

目的：在“不请专家”前，用最小成本验证 Phase6 里唯一观察到的 `psnr_fg↑ & lpips_fg↓` 配置（weak `staticp99 + w0.8`）是否可复现。

计划与审计 note：
- plan：`docs/plans/2026-03-05-openproposal-preexpert-seedrep-staticp99.md`
- note：`notes/openproposal_preexpert_seedrep_staticp99.md`（含输入 sha256、4 个 run 路径与逐 seed deltas）

复核设置：
- 两个新 seed：`43`、`44`
- 每个 seed 运行 baseline + treatment 一对（共 4 个 600-step run）
- same-init fairness：baseline 与 treatment 的 `init_npz_path` 完全一致
- FG gate：`Δpsnr_fg > 0` 且 `Δlpips_fg < 0`，guardrail `ΔtLPIPS <= +0.01`

结果（step=599，treat - base）：
- seed43：`Δpsnr_fg=+1.619054`、`Δlpips_fg=-0.017309`、`ΔtLPIPS=+0.000795` → **OK**
- seed44：`Δpsnr_fg=+0.280750`、`Δlpips_fg=+0.000248`、`ΔtLPIPS=+0.001401` → **FG fails**

结论：
- `OVERALL_OK=False`。该“FG win”配置在 2-seed 复核下表现为 **seed-sensitive / 不稳定**，不宜作为稳定改进结论对外陈述。

补充（weight tune）：
- 计划：`docs/plans/2026-03-05-openproposal-preexpert-weight-tune-staticp99.md`
- 审计：`notes/openproposal_preexpert_weight_tune_staticp99.md`
- 只改动 `pseudo_mask_weight: 0.8 -> 0.7`（其余同 seedrep；baseline 复用；新增两条 treatment）。
- 结果（step=599，treat - base）：
  - seed43：`Δpsnr_fg=+0.245204`、`Δlpips_fg=-0.007882`、`ΔtLPIPS=+0.000599` → OK
  - seed44：`Δpsnr_fg=+0.272591`、`Δlpips_fg=+0.001311`、`ΔtLPIPS=+0.000934` → FG fails
- 结论：`OVERALL_OK=False`；“简单调 weight”不足以把该配置稳定化，继续做 weight 扫描性价比很低。
