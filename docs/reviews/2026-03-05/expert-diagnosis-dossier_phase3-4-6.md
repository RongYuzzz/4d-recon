# Expert Diagnosis Dossier — OpenProposal Phase 3/4/6/7 + Pre‑Expert Checks (THUman4.0 s00)

Date: 2026-03-05 (UTC)  
Audience: 同行/专家（帮忙定位 root‑cause + 给出“最小验证实验”建议）  
Scope:
- Phase 3（weak‑fusion / pseudo‑mask reweight）
- Phase 4（VGGT feature‑metric loss, framediff gate）
- Phase 6（FG realign follow‑up：mask scaling / evaluator upgrades / active 证据）
- Phase 7（ROI alignment MVEs：weak early‑only + **oracle silhouette cue gate** + boundary‑band ROI）
- Pre‑expert sanity checks（2‑seed replication + small weight tune）

Constraints: **local‑eval only**（不提供 raw dataset 帧/相机原图/GT RGB；可提供 cfg/JSON 指标、渲染视频、非原图可视化与关键代码片段）

> 本文把分散在多个 note/review/opinion 中的材料合并成“一篇读完就能给建议”的文档；同时尽量保持可审计：每个关键结论都能在本仓库的 `outputs/` 与对应代码/脚本里找到证据链（如需可索取证据包）。

---

## 0) 我希望你回答的问题（请按此诊断）

在 THUman4.0 subject00（8 cams × 60 frames）上，我的硬目标是：

- **核心效果目标（FG）**：silhouette ROI 上 `psnr_fg ↑` 且 `lpips_fg ↓`
- **guardrail（全图）**：`ΔtLPIPS <= +0.01`（全图时间一致性不显著变差）

我尝试了两条主线，但都未能**稳定达成** FG 目标：

- Phase 3：Plan‑B init + weak‑fusion（pseudo mask reweight）
- Phase 4：Plan‑B init + VGGT feature‑metric loss（token_proj + framediff top‑p gate）

之后我做了 Phase 6/7 + pre‑expert（排障/对齐/稳定性验证），把失败边界尽量收敛到“信号与 ROI 是否对齐、是否稳定可复现”，而不是“没算/不公平/评测坏了”。

请你基于本文：

1) 给出 **3–5 个最可能根因**（按置信度排序）；  
2) 每个根因给出 **1 个最小改动验证实验（MVE）**（改什么、预期变化、判定标准）；  
3) 如果你认为“600 steps 的预算不足以判断方向”，请明确：最少需要延长到多少步、为什么、以及你建议我先做哪个**最省算力的证伪实验**。

---

## 1) 证据与可审计性（你不必跑训练）

你可以只读本文得到完整上下文；若需要复核细节，我有可索取的证据包（不含 raw 原图）：

- `outputs/expert_diagnosis_pack_2026-03-05_v2.tar.gz`（Phase 3/4/6 主证据 + 关键脚本/代码 + sha256 manifest）

代码版本提示（方便对齐“当时的实现”与输出）：

- Phase 3/4/5 + pre‑expert runs 的代码基线：`e0e9fa55f57842762d2630dca8c99bd487126dd1`
- Phase 6（FG realign tools + evaluator upgrades）：`9d7e4aaed9f45354713a6e29202e0d42cfe6e9b7`
- Phase 7（oracle cue gate + boundary‑band ROI）：`a106328c7712481d4087a4a5a54fe3801b47a32a`

注意：

- Phase 7 + pre‑expert 的新增材料**不在 v2 包内**（当时尚未纳入）；但它们的产物与 notes 已在本仓库 `outputs/` / `notes/` 中落盘，可按需追加打包。

---

## 2) 数据、拆分与评测口径（决定一切是否可比）

### 2.1 数据与拆分（固定）

Data dir（不提供给外部）：`data/thuman4_subject00_8cam60f`

固定设置（可从各 run 的 `cfg.yml` 复核）：

- frames：`start_frame=0`, `end_frame=60`（共 60）
- train cams：`02,03,04,05,06,07`
- val cam：`08`
- test cam：`09`

数据/初始化限制（可审计事实；影响时序监督强度）：

- triangulation 仅有 frame 0（跨帧几何锚极弱）
- Plan‑B init NPZ 不提供 velocity（`has_velocity==0`, `velocities==0`）

### 2.2 THUman masks 的类型（重要）

THUman `masks/*.png` 不是严格二值 mask，而是 **alpha/matte（0~255 的灰度）**。例如：

- `data/thuman4_subject00_8cam60f/masks/02/000000.png`：unique 值约 252 个（0..255）

本项目评测会先除以 255 得到 `[0,1]` 的 `mask01`，再用 `mask_thr=0.5` 二值化得到 silhouette ROI。

### 2.3 指标来源与 ROI 的定义（主口径 + 抗误判口径）

全图指标来自 trainer 落盘：

- `outputs/**/stats/test_step0599.json`（PSNR/SSIM/LPIPS/tLPIPS 等）

FG/ROI 指标来自 evaluator（从 concat render 中切 GT|Pred，再按 mask 做 ROI）：

- script：`scripts/eval_masked_metrics.py`
- 输出：`outputs/**/stats_masked/test_step0599*.json`

本项目后续明确区分了两类 FG 指标（避免 “bbox+黑背景” 稀释/误判）：

1) **fill‑black crop**（历史口径，仍保留以便对齐旧实验）
   - `psnr_fg`：在 bbox crop 内把 ROI 外置黑后，直接算 PSNR（会被 bbox 内黑背景稀释）
   - `lpips_fg`：同样在 fill‑black crop 上算 LPIPS（可能被黑边上下文影响）

2) **更贴近“只看 ROI”的口径（推荐专家优先参考）**
   - `psnr_fg_area`：只在 ROI 像素上算 MSE（分母用 ROI 面积，不被 bbox 稀释）
   - `lpips_fg_comp`：构造 `pred_comp = pred*mask + gt*(1-mask)`，再算 `LPIPS(pred_comp, gt)`（只让 ROI 差异进入比较，同时保留真实背景上下文）

3) **boundary‑band ROI（Phase 7 新增）**
   - `psnr_bd_area` / `lpips_bd_comp`：在 GT silhouette 的边界带（dilate−erode）上计算；更直接针对“silhouette 边界质量”

本 dossier 的所有 masked eval 均锁定：

- `mask_source=dataset`
- `mask_thr=0.5`
- `bbox_margin_px=32`
- `lpips_backend=auto`（真实 torch+lpips）

（可选）masked eval 的复核命令模板（只跑评测，不跑训练）：

```bash
VENV_PYTHON="third_party/FreeTimeGsVanilla/.venv/bin/python3"
$VENV_PYTHON scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir <RUN_DIR> \
  --stage test --step 599 \
  --mask_source dataset --mask_thr 0.5 --bbox_margin_px 32 \
  --lpips_backend auto \
  --boundary_band_px 3
```

---

## 3) Runs 与关键配置（公平性 gate：同 init）

所有关键 A/B 都满足 “同 init NPZ”（从 `cfg.yml:init_npz_path` 可复核）：

- `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

关键输入锁定（sha256，便于专家对齐“到底用的哪份 mask/npz”）：

- Plan‑B init NPZ：`outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
  - `sha256=d6ce23a2a2116ce72dddee9a8b4e64741cdfe5f4ee91bae79cea3b695ca4c88f`
- Phase3 cue（raw dynamicness）：`outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz`
  - `sha256=86adef37964dd6445422293c2e146c77221219d6ed709d62bc762672f4339c23`
- Phase3 使用的 invert(staticness)：`outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz`
  - `sha256=85155e78781e421c21883005a1dc6aa445486e31a47a6f3d6b63a249100aec48`
- Phase6 dyn_scaled（q=0.99）：`outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_dyn_p99.npz`
  - `sha256=edc158a58582a9ed5c90a48fb1f8cbf0b3ab3aa0fd44c7b576e9fc44497d06f0`
- Phase6 static_from_dyn_scaled（q=0.99）：`outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz`
  - `sha256=37dd090e1ff25271dceb58c0d00db5a41f8c4dc8ea75e9929554f46434734743`

### 3.1 Baseline anchor

- baseline：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`

### 3.2 Phase 3（weak‑fusion）

- treatment：`.../planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- control（weak path + no cue）：`.../planb_init_weak_zeros_600`

### 3.3 Phase 4（VGGT feature‑metric loss，same‑init）

（首轮因 init 不一致已判定作废，本文只保留 same‑init 组）

- treat‑1：`.../planb_feat_v2_gatediff0.10_600_sameinit`（`lambda_vggt_feat=0.01`）
- treat‑2：`.../planb_feat_v2_gatediff0.10_lam0.005_600_sameinit`（`lambda_vggt_feat=0.005`）

### 3.4 Phase 6（FG realign follow‑up）

- weak follow‑up（mask scaling + 方向翻转）
  - dyn_scaled：`.../planb_init_weak_dynp99_w0.8_600_r1`
  - static_from_dyn_scaled：`.../planb_init_weak_staticp99_w0.8_600_r1`
- feature follow‑up（激活性澄清）
  - nogate + ds4：`.../planb_feat_v2_nogate_lam0.005_600_sameinit_r1`
  - nogate + ds2：`.../planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1`

### 3.5 Phase 7（ROI alignment MVEs）

目的：把“ROI 对齐不足”这个假设用最小实验打穿/证伪。

- MVE‑1（weak early‑only）：`.../planb_init_weak_staticp99_w0.8_end200_600_r2`
  - mask：`outputs/cue_mining/_phase7_scaled/.../pseudo_masks_static_from_dynamic_scaled_q0.99.npz`
  - schedule：`pseudo_mask_end_step=200`
- MVE‑2（feature loss + **oracle silhouette cue gate**）：`.../planb_feat_v2_cuegate_lam0.005_600_sameinit_r2`
  - `vggt_feat_gating=cue`（直接用 dataset silhouette masks 在 phi grid 上做 dense gate）
  - `boundary_band_px=3`（额外输出 bd 指标）

### 3.6 Pre‑expert stability checks（2‑seed replication）

目的：在请专家前先回答一个问题：**是否只是 “seed‑sensitive 的偶然正例/负例”**。

- seedrep（weak staticp99 + w0.8）：
  - baseline：`.../_seedrep_planb_init_600_seed43`, `.../_seedrep_planb_init_600_seed44`
  - treatment：`.../_seedrep_weak_staticp99_w0.8_600_seed43`, `.../_seedrep_weak_staticp99_w0.8_600_seed44`
- weight tune（weak staticp99 + w0.7）：
  - treatment：`.../_seedrep_weak_staticp99_w0.7_600_seed43`, `.../_seedrep_weak_staticp99_w0.7_600_seed44`

---

## 4) 关键结果（step=599；只列核心）

### 4.1 Phase 3（weak‑fusion）：全图略升，但 FG 退化

（详见：`notes/openproposal_phase3_weak_supervision_result.md`）

| run | PSNR | SSIM | LPIPS | PSNR_FG | LPIPS_FG |
|---|---:|---:|---:|---:|---:|
| baseline `planb_init_600` | 16.1520 | 0.5621 | 0.7325 | 16.8066 | 0.2439 |
| treat `diffmaskinv q0.950 w0.8` | 16.2809 | 0.5657 | 0.7265 | 16.6361 | 0.2508 |
| control `zeros w0.8` | 16.1574 | 0.5622 | 0.7347 | 16.4846 | 0.2446 |

结论：全图略好，但 **FG 明确变差**。

### 4.2 Phase 4（feature loss framediff gate）：guardrail PASS，但 FG 退化

（详见：`notes/openproposal_phase4_attention_contrastive.md`）

| run | ΔtLPIPS | Δpsnr_fg | Δlpips_fg |
|---|---:|---:|---:|
| treat‑1 `lam=0.01` | +0.001030 | -0.348228 | +0.012048 |
| treat‑2 `lam=0.005` | +0.000043 | -0.124590 | +0.008596 |

结论：feature loss 路径不是 no‑op（见 Phase 6 active 证据），但 **FG 方向反了**。

### 4.3 Phase 6（排障）：不是“没算”，更像“信号/ROI 对齐不足 + trade‑off”

（详见：`notes/openproposal_phase6_fg_realign_phase3.md`、`notes/openproposal_phase6_fg_realign_phase4.md`）

- weak follow‑up：`static_p99_w0.8_r1` 在 FG‑local 上更接近目标，但伴随全图 LPIPS 代价（trade‑off）。
- feature follow‑up：`vggt_feat/active` 与 token grid 数量匹配（ds4=72, ds2=288）→ 确实在算；但 FG 仍不稳定优于 baseline。

### 4.4 Phase 7（ROI alignment MVEs）：即使 oracle cue gate / boundary‑band，也仍然 FG 退化

#### MVE‑1（weak early‑only, end=200）

（详见：`notes/openproposal_phase7_mve1_weak_earlyonly.md`）

- guardrail：`ΔtLPIPS=+0.000174` PASS
- ROI：`Δpsnr_fg=-0.3361`, `Δlpips_fg=+0.010479` FAIL
- boundary band：`Δpsnr_bd_area=-0.4133`, `Δlpips_bd_comp=+0.001593` FAIL

#### MVE‑2（feature loss + **oracle silhouette cue gate**）

（详见：`notes/openproposal_phase7_mve2_feat_cue_gate.md`）

- activation：`vggt_feat/active` 在 step 0/200/400 为 19/21/16（非 0）
- guardrail：`ΔtLPIPS=+0.000405` PASS
- ROI：`Δpsnr_fg=-0.4025`, `Δlpips_fg=+0.012711` FAIL
- boundary band：`Δpsnr_bd_area=-0.2820`, `Δlpips_bd_comp=+0.000294` FAIL

Phase7 的含义：即便用 **GT silhouette 作为 gate（oracle）** 把 feature loss 对齐到 ROI，仍没有把 FG 指标推向目标。

### 4.5 Pre‑expert：出现“单 seed 正例”，但 2‑seed 不稳定

（详见：`notes/openproposal_preexpert_seedrep_staticp99.md` 与 `notes/openproposal_preexpert_weight_tune_staticp99.md`）

#### seedrep staticp99 + w0.8

- seed43：`Δpsnr_fg=+1.619054`, `Δlpips_fg=-0.017309`, `ΔtLPIPS=+0.000795` → OK=True  
- seed44：`Δpsnr_fg=+0.280750`, `Δlpips_fg=+0.000248`, `ΔtLPIPS=+0.001401` → OK=False  

#### weight tune staticp99 + w0.7

- seed43：`Δpsnr_fg=+0.245204`, `Δlpips_fg=-0.007882`, `ΔtLPIPS=+0.000599` → OK=True  
- seed44：`Δpsnr_fg=+0.272591`, `Δlpips_fg=+0.001311`, `ΔtLPIPS=+0.000934` → OK=False  

结论：该设置对 FG 指标**有可能有效**，但在 2‑seed 下**不稳定**；更像高方差 + trade‑off，而非稳健改进。

---

## 5) 关键机制证据（为什么这些结果不是偶然）

### 5.1 pseudo‑mask 的分布与阈值敏感性（解释了很多弱监督现象）

以 Phase 3 的 cue 源为例：

- `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks.npz`

把 mask 归一化到 `[0,1]` 后的统计（全 T×V×H×W）：

- mean ≈ **0.001497**
- `q99 ≈ 0.0392`, `q99.5 ≈ 0.0784`, `q99.9 ≈ 0.2000`, `max ≈ 0.7961`
- `frac(mask > 0.5) ≈ 1.92e-05`（极稀疏）

这意味着：

- 用 `mask_thr=0.5` 做 pred mask 二值化会让它“看起来几乎全空”（mIoU≈0 也就不意外），但这不代表 cue 没信号；
- cue 的主要信息集中在非常低的值域（如 0.01~0.05），需要 scaling 或更低阈值才可用。

### 5.2 weak‑fusion 的语义是 dynamicness，并且默认是“降权 dynamic”

Phase 3/6/7 的 weak‑fusion 注入使用（见各 `cfg.yml`）：

- `pseudo_mask_npz = .../pseudo_masks_*.npz`
- `pseudo_mask_weight = α`
- `pseudo_mask_end_step = ...`

Trainer 的核心公式（见 Appendix B.2）是：

- 解释 mask 为 **dynamicness in [0,1]**
- `w = 1 - α·mask_dyn`，并用 `mean(w)` 归一化保持尺度

因此：

- “dynamic mask”更容易把监督从动态/前景区域移走（可能改善全图稳定性，但不直接优化 FG 细节）；
- “staticness mask”可能间接 upweight FG（因为 dynamic 区域值更低），但易产生全图代价与 seed‑variance。

### 5.3 feature loss 的空间粒度与覆盖（即使算了，也不一定对齐 silhouette 细节）

Phase 4/6 关键事实：

- token‑proj 的 `phi_size` 很小（常见为 `8×9`）；framediff gate 还会在每次只取 top‑p（如 p=0.10 → 8 cells）
- Phase 6 证明 `vggt_feat/active` 非 0 → 不是没算

Phase 7 进一步把 “ROI 对齐”做到极致（oracle）：

- `gating=cue` 直接读取 **dataset silhouette mask** 并缩到 phi grid 上作为 dense gate（Appendix B.5）

但结果仍然是 FG 指标变差 → 这更像是：

- feature loss 的梯度方向/表征本身与 “提升 silhouette ROI 的像素/感知指标”不一致，或
- 在当前时序/几何先验缺失（triangulation 仅 frame0、vel=0）的条件下，feature prior 更容易引入 trade‑off。

---

## 6) 我需要你的建议（给最小验证实验）

在你给建议前，我希望你明确 “你认为最可能的一类问题” 属于：

1) **训练目标方向性错了**（例如 weak‑fusion 的符号应该反、或应该显式 upweight FG）  
2) **信号/ROI 不可辨识或高方差**（需要更多 seed / 更长 budget / 更稳健 ROI 指标）  
3) **feature prior 本身不适合这个目标**（该止损，换成更直接的 boundary/alpha 约束）

请给出 1–2 个你认为最值得做的 MVE，并写清：

- 改动点（1 个变量最好）
- 预期趋势（psnr_fg / lpips_fg / tLPIPS / 你更信哪个 ROI 指标）
- 通过/失败判据（写死阈值更好）

---

## Appendix A) 关键文件索引（本仓库中都可直接打开）

主读本（更详细的推导/统计）：

- `docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md`
- `docs/reviews/2026-03-05/openproposal-phase6-fg-realign-followup-review.md`
- `docs/reviews/2026-03-05/internal-code-audit_phase3-4-6-7.md`

Phase 结果 notes：

- `notes/openproposal_phase3_weak_supervision_result.md`
- `notes/openproposal_phase4_attention_contrastive.md`
- `notes/openproposal_phase6_fg_realign_phase3.md`
- `notes/openproposal_phase6_fg_realign_phase4.md`
- `notes/openproposal_phase7_mve1_weak_earlyonly.md`
- `notes/openproposal_phase7_mve2_feat_cue_gate.md`
- `notes/openproposal_preexpert_seedrep_staticp99.md`
- `notes/openproposal_preexpert_weight_tune_staticp99.md`

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
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w0.8_end200_600_r2`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_cuegate_lam0.005_600_sameinit_r2`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_*`（seed43/44 的 paired runs）

---

## Appendix B) 关键代码摘录（让专家只读本文也能理解机制）

> 说明：以下摘录仅覆盖“直接决定结果走向/口径”的关键片段；更完整上下文请看对应源文件。

### B.1 Masked evaluator：ROI、`psnr_fg_area`、`lpips_fg_comp`（`scripts/eval_masked_metrics.py`）

关键点：

- 从 concat canvas 中切出 GT|Pred；
- 用 dataset masks 计算 bbox，并在 bbox 内做 fill‑black；
- 额外计算：
  - `psnr_fg_area`：只在 keep==1 的像素上算 PSNR（不被 bbox 稀释）
  - `lpips_fg_comp`：把 pred 只替换到 GT 的前景上再算 LPIPS（保留背景上下文）

```py
# scripts/eval_masked_metrics.py (main loop around keep/bbox)
keep_full = (mask01 > mask_thr).astype(np.float32)[..., None]
bbox = _bbox_from_mask(mask01, thr=mask_thr, margin=margin)
gt_crop = gt[bbox].copy()
pred_crop = pred[bbox].copy()
keep = (mask_crop > mask_thr).astype(np.float32)[..., None]
gt_crop *= keep
pred_crop *= keep

psnr_fg = _psnr(pred_crop, gt_crop)
psnr_fg_area = _psnr_mask_area(pred_crop, gt_crop, keep)
lpips_fg = lpips(pred_crop, gt_crop)
pred_comp = pred * keep_full + gt * (1.0 - keep_full)
lpips_fg_comp = lpips(pred_comp, gt)
```

### B.2 Weak‑fusion：mask 被解释为 dynamicness，并且默认“降权 dynamic”（`simple_trainer_freetime_4d_pure_relocation.py`）

```py
# third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
# (weak fusion around pseudo_mask_weight)
alpha = float(cfg.pseudo_mask_weight)
w = 1.0 - alpha * mask_batch.permute(0, 2, 3, 1)  # mask is dynamicness in [0,1]
weighted_l1_loss = (torch.abs(colors - pixels) * w).mean() / w.mean().clamp(min=1e-6)
l1_loss = weighted_l1_loss
```

### B.3 Feature loss：framediff top‑p gate（Phase 4 主配置）

```py
# top-p mask
k = ceil(top_p * (Hf*Wf))
mask_flat.scatter_(1, topk_idx, 1.0)

# framediff gate -> weight_map *= top_p_mask(gate_use)
gate_mask = self._top_p_mask(gate_use, float(cfg.vggt_feat_gating_top_p))
weight_map = gate_mask if weight_map is None else (weight_map * gate_mask)
```

### B.4 Feature loss：oracle silhouette cue gate（Phase 7 MVE‑2）

Phase 7 实现了 `gating=cue`：直接读取 `data_dir/masks/...png` 的 silhouette mask，并缩到 phi grid 上当作 dense gate（本质是 “oracle ROI alignment”）。

```py
gating_mode = str(cfg.vggt_feat_gating).strip().lower()
if gating_mode == "cue":
    gate_use = self._get_vggt_feat_cue_gate_batch(
        frame_idx=data["frame_idx"],
        camera_idx=data["camera_idx"],
        hf=int(self.vggt_feat_phi_size[0]),
        wf=int(self.vggt_feat_phi_size[1]),
    )
    if gate_use is not None:
        gate_use = _vggt_feat_downsample_dense_gate(gate_use, hf=..., wf=...)
        weight_map = gate_use if weight_map is None else (weight_map * gate_use)
```

### B.5 Boundary‑band ROI（Phase 7 新增；`psnr_bd_area / lpips_bd_comp`）

```py
band = dilate(mask_bin, r) AND (NOT erode(mask_bin, r))
psnr_bd_area = PSNR(mask_area_only)
lpips_bd_comp = LPIPS(pred*band + gt*(1-band), gt)
```

### B.6 pseudo‑mask scaling（Phase 6 工具；把低幅值 cue 拉伸到可用范围）

```py
q = quantile(m01, q99)
dyn = clip(m01 / (q + eps), 0, 1)
static = 1 - dyn
```

---

## Appendix C) 既有两份诊断意见（可选阅读；避免重复建议）

> 如果你希望“完全不被他人意见锚定”，可以跳过本 Appendix。

### C.1 opinions‑a‑v2（全文）

````text
这份诊断包做得非常扎实，不仅控制了变量（同 init 锚点），还通过 Phase 6 的排障实验把“没算”和“没对齐”的边界划得很清楚。

基于你提供的详实证据，以下是针对你的唯一硬目标（`psnr_fg ↑` 且 `lpips_fg ↓`，`ΔtLPIPS <= +0.01`）的 3 个最可能根因，以及对应的最小验证实验（MVE）。

---

### 1. 最可能根因与证据拆解

#### Root-Cause 1: Weak-fusion 的公式设计在“惩罚”前景，与你的目标完全反向 (置信度：极高)

* **证据点**：【B.2 Weak-fusion 代码】`w = 1.0 - alpha * mask_batch`。
* **推演**：代码注释写明将 mask 解释为 dynamicness（动态区域，即你的前景 ROI）。当 `mask` 越大（越接近前景），`w` 就越小。这意味着你的网络在训练时，**前景区域的 L1 权重被刻意降低了**。网络当然会选择拟合权重更高的静态背景，从而牺牲前景细节。
* **旁证**：在【4.3 Phase 6 排障结论】中，当你传入 `static_p99`（背景=1，前景=0）时，`w = 1 - alpha * static` 使得前景权重=1，背景权重=0.2。这实质上**变相实现了前景加权**，所以该 run 的 `psnr_fg` 达到了 17.1048，显著超越 baseline 的 16.8066。

#### Root-Cause 2: VGGT 特征监督粒度过粗，且 Gating 机制破坏了空间连续性 (置信度：高)

* **证据点**：【5.2 Phase 4 Cache meta】`phi_size=[8,9]`，且 `top_p=0.10`（每次仅激活 8 个 token）；【4.3 Phase 6 排障结论】nogate 激活全图后，`psnr_fg` 依然未能稳定胜过 baseline。
* **推演**：8×9 的特征图对原图来说极其粗糙，人体 Silhouette 边缘在这个分辨率下可能只占不到 1 个像素的边界。强行在如此粗的特征上拉近 L2 距离，会迫使网络为了宏观语义/姿态对齐，而破坏高频的几何边缘，直接导致 `lpips_fg` 上升。而 `top_p` 随机选取 8 个点，进一步撕裂了梯度的空间连续性。

#### Root-Cause 3: 缺乏跨帧的时序/几何强先验，导致弱监督容易“带偏”网络 (置信度：中)

* **证据点**：【2.1 数据与拆分】triangulation 仅有 frame 0，且 init velocities=0。
* **推演**：4D 重建在没有初始速度和多帧强三角化点云锚定的情况下，网络本身就处于一种“容易形变”的欠约束状态。此时无论是引入弱空间注意力（Phase 3）还是粗特征正则（Phase 4），稍微的信号错位（如背景干扰）都会导致前景色块在时序上发生漂移或模糊，从而影响 `psnr_fg` 和 `tLPIPS`。

---

### 2. 最小改动验证实验（MVE）建议

为了快速排除假设，请严格**每次只改动一个变量**。

#### MVE 1 (针对 RC1): 显式且正向地 Upweight Foreground

* **改动点**：修改 `simple_trainer_freetime_4d_pure_relocation.py` 约 3725 行，将减号改为加号。
```python
# 修改前: w = 1.0 - alpha * mask_batch.permute(0, 2, 3, 1)
# 修改后:
w = 1.0 + alpha * mask_batch.permute(0, 2, 3, 1) 

```


同时，`cfg` 中传入 Phase 6 的 `dynamic_scaled` mask（即前景为高值），`pseudo_mask_weight` 设为 0.5（避免过度破坏背景）。
* **预期指标趋势**：`psnr_fg` 显著提升（应 > 17.0），`lpips_fg` 下降。全图 `tLPIPS` 可能会有极轻微的上升。
* **通过/失败判据**：若 `psnr_fg > 16.9` 且 `lpips_fg < 0.243`，则通过。说明框架没问题，纯粹是之前方向反了。

#### MVE 2 (针对 RC2): VGGT 仅在 Silhouette ROI 内稠密生效 (实现 gating='cue')

* **改动点**：在 `simple_trainer_freetime_4d_pure_relocation.py` 中，补齐 `gating='cue'` 的逻辑。不使用 `top_p`，而是直接将降采样后的前景色罩（可以用 MVE 1 里的 `dynamic_scaled` mask，通过 avg_pool2d 降采样到 `phi_size` 8x9）作为 `weight_map`。
```python
# 伪代码思路
elif gating_mode == "cue":
    # 假设 mask_batch 是 [B, 1, H, W] 的前景 dynamic mask
    gate_mask = F.adaptive_avg_pool2d(mask_batch, (hf, wf))
    weight_map = gate_mask if weight_map is None else (weight_map * gate_mask)

```


保持 `lambda_vggt_feat` 较低（如 0.005）。
* **预期指标趋势**：在保证 `ΔtLPIPS <= +0.01` 的前提下，观察 `psnr_fg` 是否能至少保持中立或微升（不像之前猛掉 -0.34）。
* **通过/失败判据**：只要 `psnr_fg` 不再出现超过 0.1 的掉点，且 `tLPIPS` 达标，就说明 Feature loss 必须被严格限制在 ROI 内。如果依然掉点，彻底放弃 8x9 的 VGGT 用于精细 Foreground 优化。

---

### 3. FG 评测口径审查 (关于 `eval_masked_metrics.py`)

**你的直觉是对的，当前的 `bbox crop + fill-black` 口径确实存在严重的“误判”风险，会把“稍微胖一点但结构更好”的结果判定为更差。**

**风险点分析**：
在【B.1】中，你使用了 `gt_crop *= keep` 和 `pred_crop *= keep`。这意味着只要 pred 的像素超出了 GT 的 mask 边界哪怕 1 个像素，它也会被生硬地截断置为绝对的黑色（0,0,0）。
这在计算 LPIPS 时是致命的。LPIPS 使用 VGG/AlexNet 提取特征，这种**人工制造的、无限锐利的黑边（高频伪影）**会产生巨大的 feature 误差。网络只要在前景色域边缘多渲染了一点点（这在 3DGS 中很常见，因为 splats 会飞散），其真实视觉可能并无大碍，但 `lpips_fg` 会瞬间爆炸。

**替代口径建议（低成本、可审计）：**
不要做硬性的 Fill-black，而是计算 **"Valid-Masked LPIPS / PSNR"**。

1. **针对 PSNR**：直接在非零掩码的像素点上算 MSE，不要算黑色区域。
```python
# 替代实现思路
mse = ((pred_crop - gt_crop) ** 2)
valid_mse = mse[mask_crop > float(args.mask_thr)].mean()
psnr_fg_valid = -10.0 * np.log10(valid_mse)

```


2. **针对 LPIPS**：放弃在裁剪图上做 fill-black 乘法。直接将完整的 `gt_crop` 和 `pred_crop`（保持原背景）送入 `lpips_fn`。LPIPS 本身是一个 patch-based 的特征距离，既然你已经通过 bbox 切出了 ROI，直接算 bbox 内部的全图 LPIPS 即可。如果你非要剥离背景干扰，可以对 GT mask 做一个形态学膨胀（Dilation，比如 +10px），用这个扩大的软边界去 masking，避免在真实的物体边缘产生刀切一样的黑边。

建议你先跑 MVE 1，因为那个代码改动只有 1 个字符，并且从 Phase 6 的反推来看，成功率极高。
````

### C.2 opinions‑b‑v2（全文）

````text
According to a document from **2026-03-05**, 你现在 Phase3/4 “算是算了、也能通过 guardrail”，但**前景（silhouette ROI）指标不稳定变好**，更像是“训练信号/覆盖区域与 FG 评测 ROI 没对齐”，而不是单纯实现没生效：

* Phase3 weak-fusion：全图 PSNR/LPIPS 略好，但 **PSNR_FG↓、LPIPS_FG↑**。
* Phase4 VGGT feature loss：**ΔtLPIPS ≤ +0.01 PASS**，但 **Δpsnr_fg < 0 且 Δlpips_fg > 0**（两条 λ 都失败）。
* Phase6 follow-up：weak-fusion 经过 scaling/方向翻转后，能把 FG 往目标方向推一点，但会出现全图 LPIPS 代价；feature loss 在 ds4/ds2 下 active 计数匹配（说明路径激活），却仍难稳定胜过 baseline → 指向“信号/ROI 对齐不足”。

下面按**置信度从高到低**给 4 个最可能 root-cause（每条都给最小验证实验）。

---

## Root-cause 1（最高置信）：Phase3 的 pseudo-mask “数值分布 + 语义”错位，导致 weak-fusion 近似 no-op 或方向性不利于 FG

### 证据点

* mask 统计：原始 diff dynamicness **mean≈0.00150**（极稀疏），invert 后 staticness **mean≈0.99850**（几乎常数 1）。
* weak-fusion 代码把 mask 当 **dynamicness∈[0,1]**，并用 `w=1-α·mask` 下调高 mask 区域的 L1 权重，同时 **除以 mean(w)** 保持尺度：常数 mask → 归一化后接近 baseline（near no-op）。
* 结果符合现象：Phase3 treatment 全图略升，但 FG 退化。

### 机制解释

你把“几乎全 1 的 staticness”喂给了“期望 dynamicness”的模块，并且模块内部还做了 `mean(w)` 归一化：

* **mask 近常数** → 权重 `w` 近常数 → 被 `mean(w)` 抵消 → 训练几乎不变（或只剩噪声级别的重权重）。
* 就算后续把 mask 拉伸到可用范围，`w=1-α·mask` 这类**“高 mask 降权”**也天然倾向压弱被 mask 标记的区域（而这个区域往往与“动/人”相关），与 fg 目标冲突（这点在 RC2 展开）。

### 最小验证实验（只改 mask 文件，不动训练主逻辑）

**改动点**

* 用 Phase6 的 scaling 工具把 dynamic mask 拉伸：`dyn = clip(m / (q99+eps), 0, 1)`，并生成两份：`dynamic_scaled` 与 `static_from_dynamic_scaled=1-dyn`。
* 保持 `pseudo_mask_weight=0.8`，其它不变。

**预期趋势**

* 若此前确实 no-op：`pseudo_mask/active_ratio` 不再接近 1.0 饱和，指标会显著偏离 baseline（至少看到“dyn vs static”方向性分化）。
* 你 Phase6 已经观测到：dyn_p99 往“全图更好但 fg 更差”走；static_p99 往“fg 更接近目标但全图 lpips 付费”走。

**通过/失败判据**

* 通过（确认该根因）：

  1. `pseudo_mask/active_ratio` 明显远离 1.0 饱和；且
  2. dyn_p99 与 static_p99 的 FG 指标出现可复现的方向差异（至少 Δpsnr_fg 的符号相反或 Δlpips_fg 的符号相反）。
* 失败（说明还有更上游的对齐问题）：scaling 后 active_ratio 仍接近饱和，或 dyn/static 两种输入指标几乎无差别 → 优先排查 mask 读取对齐（frame/cam index、resize）而不是继续调 α。

---

## Root-cause 2（高置信）：weak-fusion 的目标函数本质是“压弱动态/困难像素监督”，与“silhouette ROI 指标提升”天然冲突 → 形成 trade-off

### 证据点

* weak-fusion 明确“Interpret mask as dynamicness … downweight dynamic pixels”：`w=1-α·mask_dyn`。
* dossier 直接总结：即便 scaling 后有信号，机制仍倾向于“压弱动态/前景”→ 与 fg 目标冲突；方向翻转后 fg 变化更符合预期，但出现全图代价（trade-off）。
* Phase6 结论要点也点名 trade-off：`static_from_dynamic_scaled` 更接近 fg-local 目标，但全图 lpips 变差。

### 机制解释

如果你的 pseudo mask（无论来自 framediff 还是 cue mining）在统计上**与“人/边界/运动区域”高度相关**，那么：

* `mask_dyn` 高的区域 ≈ “你最想修的 fg/边界/动态”
* weak-fusion 做的是 **“高 mask 降权”** → 等价于把训练资源从 FG 转移走
  → 所以很容易出现你现在的模式：**全图略升，但 FG 退化**；翻转方向能把 FG 拉回来，但必然会触发全图/背景的代价（因为你在重新分配监督权重）。

### 最小验证实验（不改代码，只改一个 cfg：让 weak-fusion 只在早期生效）

**改动点**

* 继续用 Phase6 表现更接近 FG 目标的 `static_from_dynamic_scaled`（即“方向翻转”那条）。
* 把 `pseudo_mask_end_step` 从 600 缩到 **200 或 300**（weak-fusion 只影响 early stage）。启用条件就在 trainer 里：`step < cfg.pseudo_mask_end_step`。

**预期趋势**

* 如果 trade-off 主要来自“后期持续重分配监督”，那么 early-only 会：

  * `psnr_fg` 仍保持上升趋势、`lpips_fg` 仍保持下降（至少不比 baseline 差）
  * 同时**全图 lpips 的代价减轻**（因为后半程 photometric 接管细节）
  * `ΔtLPIPS` 仍应轻微变化且 **≤ +0.01**（你现有多条 run guardrail 都很宽松）。

**通过/失败判据**

* 通过：相对 baseline（同 init，同 step=599），满足

  * `Δpsnr_fg ≥ +0.2 dB` 且 `Δlpips_fg ≤ -0.001`
  * 并且 `ΔtLPIPS ≤ +0.01`
  * 同时全图 lpips 的恶化幅度明显小于 static_p99_full600（作为定性判据即可）。
* 失败：FG 提升消失（说明需要持续加权才有 fg gain），或者全图代价不降（说明代价不是“后期累积”，而是“权重方向/ROI 本身不对齐”→ 回到“需要 fg-gating”的思路）。

---

## Root-cause 3（高-中置信）：Phase4 feature loss 的监督“太粗 + gate 太稀疏/不可靠”，且 cue-gating 其实未实现 → 对齐不到 silhouette ROI

### 证据点

* Phase4 cache meta：ds4 时 `phi_size=[8,9]`（72 cells），`top_p=0.10` → 每次 gate 只激活 `ceil(0.1*72)=8` 个格子。
* `gating='cue'` 未实现，会 fallback 到 none（你如果以为启用了 cue gating，实际没有）。
* Phase6 feature loss：nogate + 提高 phi_size 后，`vggt_feat/active` 与 token grid 数量匹配（ds4=72、ds2=288）→ 路径确实激活；但 fg 仍不稳定胜过 baseline → 更像 ROI 不对齐，不是没算。
* Phase4 指标：guardrail PASS 但 FG 退化。

### 机制解释

你希望 feature loss 帮你把**人**的外观/边界修好，但你实际给 feature loss 的“空间覆盖”要么：

* gatediff top_p：**只打 8 个 token**（8×9 网格里），很难覆盖完整 silhouette 及其边界；而且 framediff top_p 选的是“变化最大处”，未必等于“silhouette ROI 的误差最大处”。
* nogate：反过来变成“全图 feature regularization”，又会把梯度分到背景，或者把 photometric 纹理压平，导致 FG 的 PSNR 反而降。

### 最小验证实验（一次就能把“ROI 对齐假设”拍死/拍活）

**改动点（小改代码，但逻辑极简单、也最可审计）**

* 在 feature loss 的 `weight_map` 上乘一个 **silhouette mask downsample**（来自 dataset 的 masks/*.png，同 evaluator 的 mask_source=dataset 一致）。
* 配置建议：

  * `phi_size=ds4`（先别再加算力）
  * `lambda_vggt_feat=0.005`（你 Phase4/6 用过）
  * `gating_mode=none`（先别混入 framediff）
  * 最终：`weight_map = silhouette_ds4`（或 `weight_map *= silhouette_ds4`）

**预期趋势**

* 如果“问题就是 feature loss 没对齐 silhouette ROI”，那么 silhouette-gated feature loss 应该：

  * `psnr_fg ↑`、`lpips_fg ↓`（相对 baseline，且比 feat_nogate_ds4 更稳定）
  * `ΔtLPIPS` 小幅变化但 ≤ +0.01（通常不会突然爆）。
* 如果仍然 fg 变差：说明 feature loss 本身的梯度方向/表征对你的任务就是对抗的（那就应该止损，不再围绕 gating 调参）。

**通过/失败判据**

* 通过：相对 baseline（step=599）满足

  * `Δpsnr_fg ≥ +0.2 dB` 且 `Δlpips_fg ≤ -0.003`，并 `ΔtLPIPS ≤ +0.01`。
* 失败：任一 fg 指标持续反向（psnr_fg 降或 lpips_fg 升）→ 结论可写死为“feature loss 不适合作为提升 silhouette ROI 的约束（至少在 token_proj/ds4 这条实现上）”。

---

## Root-cause 4（中置信）：feature loss 与 photometric 在后期产生“优化对抗”，λ 越大 fg 越差 → 需要 annealing 才可能两全

### 证据点

* Phase4：λ 从 0.005 → 0.01，fg 退化幅度更大（Δpsnr_fg 更负、Δlpips_fg 更正），但 guardrail 仍 PASS。
  这说明“不是 tLPIPS 把你卡死了”，而是 feature loss 本身在 fg 指标上方向不对/时机不对。

### 机制解释

在 4DGS 这类优化里，feature prior 很容易在后期变成“把纹理往特征更像的方向拉”，但这个方向未必降低 **mask 内像素误差**：

* PSNR_FG 更像像素级保真
* LPIPS_FG 更像感知相似
  feature loss 可能让你在 feature space 更近，但在 ROI 像素空间更远（尤其边界、细纹理）。

### 最小验证实验（只改 schedule，不改损失形式）

**改动点**

* 做一个 **λ annealing**：前 1/3 训练用 λ=0.005，后 2/3 线性或指数衰减到 0。
  （你已经有 `step < ..._end_step` 这种 end_step 控制思路用于 weak-fusion；feature loss 也用同类 end_step 或在 code 里乘一个 `anneal(t)` 即可。）

**预期趋势**

* 若“后期对抗”成立：相比 constant λ，annealing 应该能

  * 把 `psnr_fg` 拉回（不再明显下降）
  * 同时 `lpips_fg` 不再上升，甚至下降
  * `tLPIPS` 维持 guardrail 内（大概率更稳）。

**通过/失败判据**

* 通过：相对 Phase4 的 treat‑2（λ=0.005 constant），annealing 版至少让

  * `Δpsnr_fg` 从负变为 ≥0（最好 ≥ +0.1 dB）
  * 且 `Δlpips_fg` 从正变为 ≤0
  * 并 `ΔtLPIPS ≤ +0.01`。
* 失败：annealing 仍无法让 fg 指标回正 → 说明不是“时机问题”，是“feature loss 对你这个 ROI 目标就不对齐”。

---

## 你当前 FG 评测口径（bbox crop + fill-black）确实有“与训练信号错位/误判”的风险

### 你现在的实现到底在算什么

Evaluator 做法是：

1. 用 **GT mask** 取 bbox；
2. 在 bbox 内，把 GT/pred 都乘 `keep=(mask>thr)`，bbox 里背景变黑；
3. 对整个 crop 直接算 PSNR/LPIPS。

这有两个常见副作用：

* **PSNR 会被“bbox 内的黑背景面积”稀释**：因为 bbox 内 keep=0 的像素对误差是 0，但仍进入 mean 的分母 → 指标变化幅度被压小（更难看出真实 fg 改善）。
* **LPIPS 在黑背景上下文里可能放大/扭曲边界差异**：卷积特征在边界处会受到黑背景影响，导致一些“看起来更自然”的变化反而被判更差（尤其边界抖动/锯齿）。这类误判不是必然，但风险客观存在。

另外你文档也明确：mIoU 的健康检查实现是 GT 与 pred 用同一个 `mask_thr`，当 pred mask 幅度很低时会得到 mIoU≈0（容易误判“mask 无信号”）。

### 我更认可、且成本低/可审计的替代口径（建议做成对照表）

你 Phase6 表里已经开始记录 `psnr_fg_area` 和 `lpips_fg_comp` 这类“更贴近 ROI”的口径（非常好）。

我建议你把对照实验写死成三套（都不需要 raw GT 外传，且可复核）：

1. **Mask-only PSNR（推荐主用）**

   * 只在 keep==1 的像素上算 MSE，然后再算 PSNR（分母用 `sum(keep)`，不是 bbox 总像素数）。
   * 目的：去掉 bbox 黑背景的稀释效应。

2. **Composite LPIPS（推荐主用）**

   * 构造 `pred_comp = pred*keep + gt*(1-keep)`，然后算 `LPIPS(pred_comp, gt)`。
   * 目的：保留自然背景上下文，同时只让 fg 差异进入比较（避免黑背景对 LPIPS 特征的干扰）。

3. **Boundary-band 指标（强烈建议加一条）**

   * `band = dilate(mask,r) - erode(mask,r)`（比如 r=3 或 5），只在 band 上算 PSNR/LPIPS。
   * 目的：你要的“silhouette 质量”很多时候主要体现在边界 3~5px 的一致性/锯齿/漏光，这条指标更对症。

**对照实验怎么判定“原口径在误判”**

* 用 baseline / dyn_p99 / static_p99 / feat_nogate_ds4（你已有）各跑一遍三套评测，比较排序是否一致：

  * 若排序显著翻转（例如旧口径说 static_p99 更差，但 composite/boundary 说更好），那旧口径确实在误判你要的视觉变化；
  * 若排序一致但幅度不同，则旧口径更多是“信噪比低/变化被稀释”，可以作为次要指标保留。

---

## 如果你只想做 1–2 个最小实验，我建议优先做这两个

（都能最大化信息量，最快排除大类假设）

1. **weak-fusion：static_p99 + 缩短 pseudo_mask_end_step（200/300）**

   * 不改代码，只改 cfg。
   * 目的：验证“方向翻转确实能推 fg，但代价来自后期累积”的假设。

2. **feature loss：silhouette-gated（oracle）版本**

   * 小改代码但非常直接、最可审计。
   * 目的：一把拍死“feature loss 到底是不是因为 ROI 不对齐才失败”。

如果这两条都不能让 `psnr_fg ↑ & lpips_fg ↓` 同时成立（且 ΔtLPIPS ≤ +0.01），那基本可以很硬地把结论写成：**在当前实现与信息条件下，weak / feature 这两类约束更像是在做 trade-off 调参，而不是稳定提升 silhouette ROI 的有效信号**（Phase6 的“不是没算，而是 ROI 对齐不足”已经在往这个结论靠）。
````

---

如需完整可审计证据包（cfg/JSON/视频/可视化 + sha256 manifest），可索取 `outputs/expert_diagnosis_pack_2026-03-05_v2.tar.gz`（以及包含 Phase 7 + pre‑expert 的增量包）。
