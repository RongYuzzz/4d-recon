# Expert Diagnosis Pack — OpenProposal Phase 3/4 (THUman4.0 s00)

Date: 2026-03-05 (UTC)  
Audience: 同行/专家（帮忙定位 root-cause + 给出最小验证实验建议）  
Scope: 仅 Phase 3（weak-fusion）与 Phase 4（VGGT feature-metric loss）。Phase 1/2 只提供必要口径与 cue 来源背景。  
Constraints: **local-eval only**（不对外提供 raw images / GT masks；可提供 cfg/JSON 指标、统计摘要、关键代码片段）。

---

## 0) 我希望你回答的问题（请按此诊断）

在 THUman4.0 subject00（8 cams × 60 frames）上，我的目标是：
- **前景质量提升**：`psnr_fg ↑` 且 `lpips_fg ↓`
- **guardrail**：`ΔtLPIPS <= +0.01`（全图 temporal-LPIPS 不显著变差）

我做了两条主线但都未达成前景目标：
- Phase 3：Plan‑B init + weak-fusion（pseudo mask reweight）
- Phase 4：Plan‑B init + VGGT feature-metric loss（token_proj + framediff gating）

请你基于下文材料：
1) 给出 **3–5 个最可能根因**（按置信度排序）；  
2) 每个根因给出 **1 个最小改动验证实验**（改什么、预期变化、判定标准）。

---

## 1) 可复核锚点（仓库、数据、指标口径）

### 1.1 Repo / 训练代码入口

- Branch（本次实验整合分支）：`owner-b/openproposal-waiting-thuman4`
- Key commits：
  - Phase 3 note：`2e8fe37`（`docs(notes): Phase3 weak supervision A/B result on THUman`）
  - Phase 4 note：`04ca0d0`（`docs(notes): Phase4 feature-metric loss result + guardrail`）

- Trainer（FreeTimeGsVanilla fork）：
  - `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Phase 3 结果 note：`notes/openproposal_phase3_weak_supervision_result.md`
- Phase 4 结果 note：`notes/openproposal_phase4_attention_contrastive.md`
- 审查报告（执行质量 / 公平性 gate）：
  - Phase 3：`docs/reviews/2026-03-04/openproposal-phase3-review.md`
  - Phase 4：`docs/reviews/2026-03-04/openproposal-phase4-review.md`
- 失败分析（更细的 root-cause 链路与统计）：`docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md`

Runtime stack（FreeTimeGsVanilla venv；便于专家判断“是否实现/数值问题”）：
- Python: 3.12.3
- torch: 2.10.0+cu128（torch.version.cuda=12.8）
- torchvision: 0.25.0
- lpips: 0.1.4
- vggt: 0.0.1（用于 `facebook/VGGT-1B` 推理/缓存）

说明：
- 当前会话环境下 `torch.cuda.is_available() == False`（无法从这里导出 GPU 型号）；但实验产物已在 `outputs/` 固化，可直接审阅 cfg/stats/TB 标量与 cache meta。

### 1.2 数据与相机拆分（固定）

Data dir：
- `data/thuman4_subject00_8cam60f`

固定设置（见各 run 的 `cfg.yml`）：
- frames：`start_frame=0`, `end_frame=60`（共 60）
- train cams：`02,03,04,05,06,07`
- val cam：`08`
- test cam：`09`

上游限制（可审计事实）：
- triangulation 仅有 frame0：`data/thuman4_subject00_8cam60f/triangulation/points3d_frame000000.npy`
- Plan‑B init NPZ 的速度字段为 0（init 不提供 velocity）：  
  `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`（`velocities==0`, `has_velocity==0`）

### 1.3 评测口径（最关键：`psnr_fg/lpips_fg` 的定义）

全图指标（PSNR/SSIM/LPIPS/tLPIPS）来自 trainer 落盘 JSON：
- `outputs/**/stats/test_step0599.json`

前景指标来自自定义 evaluator（GT mask → bbox crop → fill-black）：
- `scripts/eval_masked_metrics.py`
- 输出：`outputs/**/stats_masked/test_step0599.json`（Phase 4 额外存档为 `test_step0599_phase4.json`）

其 ROI 与 fill-black 实现核心逻辑（摘录）：
```py
# scripts/eval_masked_metrics.py
bbox = _bbox_from_mask(mask01, thr=mask_thr, margin=bbox_margin_px)
gt_crop   = gt[bbox].copy()
pred_crop = pred[bbox].copy()
keep = (mask_crop > mask_thr).astype(np.float32)[..., None]
gt_crop   *= keep
pred_crop *= keep
psnr_fg  = mean(PSNR(pred_crop, gt_crop))
lpips_fg = mean(LPIPS(pred_crop, gt_crop))
```

注意事项：
- `mask_thr` 默认 `0.5`（即 128/255 的二值化阈值）。
- `--compute_miou` 当前实现对 GT 与 pred 使用 **同一个阈值**（会导致 pred mask 幅度偏低时 mIoU≈0；见 §3.3）。

---

## 2) Phase 3：weak-fusion（pseudo mask reweight）

### 2.1 runs（A/B + control）

根目录：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/`

- baseline：`planb_init_600`
- treatment：`planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- control：`planb_init_weak_zeros_600`（weak 路径开启但 cue=全 0）

抗混淆（同 init）：
- 三条 run 的 `init_npz_path` 一致：  
  `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

### 2.2 关键配置差异（从 cfg.yml 抽取）

baseline（`planb_init_600/cfg.yml`）：
- `pseudo_mask_weight=0.0`（禁用 weak-fusion）

treatment（`planb_init_weak_diffmaskinv_q0.950_w0.8_600/cfg.yml`）：
- `pseudo_mask_npz=.../outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz`
- `pseudo_mask_weight=0.8`
- `pseudo_mask_end_step=600`（训练全程）

### 2.3 指标结果（step=599）

（完整表在 `notes/openproposal_phase3_weak_supervision_result.md`）

| Run | PSNR | SSIM | LPIPS | PSNR_FG | LPIPS_FG |
|---|---:|---:|---:|---:|---:|
| baseline `planb_init_600` | 16.1520 | 0.5621 | 0.7325 | 16.8066 | 0.2439 |
| treatment `weak diff-invert q0.950 w0.8` | 16.2809 | 0.5657 | 0.7265 | 16.6361 | 0.2508 |
| control `weak zeros w0.8` | 16.1574 | 0.5622 | 0.7347 | 16.4846 | 0.2446 |

结论：
- 全图指标：treatment 相对 baseline 有提升；
- 目标前景指标：treatment **退化**（`psnr_fg↓`, `lpips_fg↑`）。

---

## 3) Phase 3 关键诊断证据：mask 语义/幅度/是否“近似常数”

### 3.1 pseudo mask 的生成链路（Phase 2 → Phase 3）

Phase 2 diff cue mining（`backend=diff`）输出：
- `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz`

Phase 3 额外做了 invert（255-x）得到：
- `.../pseudo_masks_invert_staticness.npz`

invert 实现（摘录）：
```py
# scripts/invert_pseudo_masks_npz.py
out_masks = (255 - masks).astype(np.uint8)
```

### 3.2 weak-fusion 的损失定义（mask 语义固定为 dynamicness）

训练代码将 mask 解释为 dynamicness，并 **下调 dynamic 像素的 L1 权重**（摘录）：
```py
# simple_trainer_freetime_4d_pure_relocation.py
# w = 1 - alpha * mask, then normalize by mean(w)
w = 1.0 - alpha * mask
weighted_l1 = mean(|pred-gt| * w) / mean(w)
```

因此：
- 如果你给的是 staticness（invert 后接近 1 的 mask），语义会“翻转”；
- 如果 mask 接近常数，weak-fusion 会退化为近似 no-op（或只剩局部噪声重权重）。

### 3.3 我对 Phase 3 用到的 mask 的直接统计（关键数据）

对 `openproposal_thuman4_s00_diff_q0.950_ds4_med3`：

1) 原始 dynamicness（未 invert）`pseudo_masks.npz`：
- `mean≈0.00150`
- `P99≈0.039`
- `ratio(mask>=0.5)≈1.92e-05`（几乎全都 < 0.5）

2) invert 后 staticness `pseudo_masks_invert_staticness.npz`：
- `mean≈0.99850`
- `ratio(mask>=0.5)≈0.99998`（几乎全都 > 0.5）

这会导致：
- `pseudo_mask/active_ratio` 接近 1（TB 复核：≈0.9989）。
- weak-fusion 的权重 `w=1-α*mask` 变成几乎常数，归一化后接近 baseline L1。

此外：Phase 2 的 “miou_fg≈0” 很大程度是阈值口径错位（同阈值 0.5 同时阈值 GT 与 pred）。  
示例（test cam=09，diff q0.950）：`thr_pred=0.02` 时 mIoU≈0.203，但 `thr_pred=0.50` 变成 0。

---

## 4) Phase 4：VGGT feature-metric loss（token_proj + framediff top‑p gating）

### 4.1 runs（same-init 有效对照）

根目录：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/`

- baseline：`planb_init_600`
- treat‑1：`planb_feat_v2_gatediff0.10_600_sameinit`（`lambda_vggt_feat=0.01`）
- treat‑2：`planb_feat_v2_gatediff0.10_lam0.005_600_sameinit`（`lambda_vggt_feat=0.005`）

无效对照（已弃用）：
- `planb_feat_v2_gatediff0.10_600` 与 `..._lam0.005_600`：`init_npz_path` 不同（confounded）。

### 4.2 VGGT cache（预计算产物）

cache dir：
- `outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10/`

meta（关键字段）：
- `phi_name=token_proj`
- `phi_size=8×9`（非常粗）
- `has_gate_framediff=true`
- `framediff_top_p=0.1`

Gate 统计（从 `gt_cache.npz` 直接算）：
- `ratio(gate>0)≈0.109`（≈ 8/72；见下一条）

### 4.3 top‑p gate 的实现意味着：每次只有 8 个格子参与监督

在 `phi_size=8×9` 时，总格子数 `72`。  
`top_p=0.10 → k=ceil(0.10*72)=8`，对应 TB 标量：
- `vggt_feat/active = 8.0`（只在真正计算 feat loss 的 step 记录到，例如 0/200/400）。

这使 feature loss 更像“稀疏、粗粒度正则”，很难直接改善 silhouette ROI 的 `psnr_fg/lpips_fg`。

### 4.4 指标结果（same-init 有效对比）

（完整表在 `notes/openproposal_phase4_attention_contrastive.md`）

| Run | ΔtLPIPS | Δpsnr_fg | Δlpips_fg |
|---|---:|---:|---:|
| treat‑1 `lam=0.01` | +0.001030 | -0.348228 | +0.012048 |
| treat‑2 `lam=0.005` | +0.000043 | -0.124590 | +0.008596 |

结论：
- guardrail PASS（`ΔtLPIPS<=+0.01`）；
- 但两条 treatment 的前景指标均退化 → **Phase 4 主目标失败**。

---

## 5) 当前最可信的 root-cause 候选（带“证据点”）

> 更完整版本见 `docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md`；这里给专家快速浏览版。

1) **weak-fusion mask 语义错位 + invert 饱和 → 近似 no-op / 噪声重权重**
   - 证据：invert 后 mask `mean≈0.9985` 且 TB `pseudo_mask/active_ratio≈0.9989`；
   - weak-fusion 的 `w` 被归一化，常数 mask 基本回到 baseline L1。

2) **weak-fusion 的目标函数与 fg ROI 可能天然冲突**
   - mask 被解释为 dynamicness 并被 downweight；
   - 若 cue 与 silhouette/前景相关，就在“降权前景”，极易出现“全图略好但 fg 更差”。

3) **mIoU 健康检查阈值口径不合理（同阈值阈值 GT 与 pred）导致误判“mask 无信号”**
   - 证据：pred mask 幅度很低；`thr_pred` sweep 能得到非零 mIoU。

4) **VGGT feature loss 监督过粗（`phi_size=8×9`）且 gate 过稀疏（top‑p=0.10 → 8 active cells）**
   - 证据：meta `phi_size=8×9`，TB `vggt_feat/active=8.0`。

5) **时序几何先验不足（triangulation 仅 frame0、init velocities=0）**
   - 这会放大“弱监督/粗 feature 正则”带来的背景偏置与前景细节退化风险。

---

## 6) 附件索引（如果你需要更细节）

- Phase 3 结果：`notes/openproposal_phase3_weak_supervision_result.md`
- Phase 4 结果：`notes/openproposal_phase4_attention_contrastive.md`
- Phase 3/4 失败分析（含统计/代码摘录/复核命令）：`docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md`
- Phase 3 审查（执行质量与 validity gate）：`docs/reviews/2026-03-04/openproposal-phase3-review.md`
- Phase 4 审查（执行质量与 validity gate）：`docs/reviews/2026-03-04/openproposal-phase4-review.md`

## Follow-up outcome (Phase 6)

- Phase 3 weak-fusion follow-up: scaling removed clear no-op behavior, and `static_from_dynamic_scaled` outperformed `dynamic_scaled` on foreground-local metrics (`psnr_fg`, `lpips_fg`, `psnr_fg_area`) while keeping `ΔtLPIPS` within guardrail (`<= +0.01`).
- Phase 4 feature-loss follow-up: `gating=none` and `phi_size` increase (`ds4 -> ds2`) both activated the intended supervision path (`vggt_feat/active` matched token grid size), but foreground quality still did not beat baseline consistently.
- Updated failure boundary: for current `token_proj + cosine + lambda=0.005` settings, even `ds2 + nogate` remains a non-winning treatment for fg ROI; prioritize Phase 3 direction for next iterations and treat Phase 4 as stop-loss at this configuration.
