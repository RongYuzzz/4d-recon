# Expert Diagnosis Dossier — OpenProposal (THUman4.0 s00) Phase 2–7 + Pre‑Expert Checks

Date: 2026-03-05 (UTC)  
Audience: 同行/专家（请帮忙定位 root-cause，并给出最小验证实验建议）  
Scope: Phase 2（pseudomask mining）/ Phase 3（weak-fusion）/ Phase 4（VGGT feature-metric loss）/ Phase 6（FG realign follow-up）/ Phase 7（ROI MVEs）/ Pre‑Expert（seed replication + weight tune）  
Constraints: **local-eval only**（不分享 raw dataset 原始 RGB/GT 原图；可提供 cfg/JSON 指标、渲染视频、非原图可视化与关键代码片段）

> 本文是“专家会诊的一站式材料”：你只读这一份就能给出判断与建议；如需更强证据，再索取证据包（tar + sha256 manifest）。

---

## 0) 我希望你回答的问题（请按此诊断）

我在 THUman4.0 subject00（8 cams × 60 frames）上，希望达到：

- **核心效果目标（FG）**：silhouette ROI 上 **`psnr_fg ↑` 且 `lpips_fg ↓`**
- **guardrail（全图）**：`ΔtLPIPS <= +0.01`（全图时间一致性不显著变差）

我尝试了两条路线：

1) **weak-fusion**：Plan‑B init + pseudo-mask reweight（Phase 3/6/7/pre‑expert）  
2) **feature-metric loss**：Plan‑B init + VGGT token-proj feature loss（Phase 4/6/7）

现状：两条路线都未能**稳定**达成 FG 目标（多次同口径对照 + 2-seed 复核）。

请你基于本文：

1) 给出 **3–5 个最可能根因**（按置信度排序）；  
2) 每个根因给出 **1 个最小验证实验**（改什么、为什么、预期变化、判定标准）；  
3) 若你认为“当前问题定义/指标口径本身不合理”，请明确指出，并给出更合理的替代口径（仍需可复核）。

---

## 1) 证据包（可选：你不跑代码也能复核）

证据包（不含 raw dataset 原图），二选一即可：

- `outputs/expert_diagnosis_pack_2026-03-05_v2.tar.gz`（推荐；更新更全）
- `outputs/expert_diagnosis_pack_2026-03-05.tar.gz`（旧版）

包内包含：

- 本文相关的关键文档快照（failure analysis / follow-up review 等）
- 关键代码（trainer 的 weak-fusion / vggt feature loss、评测脚本、Phase 6/7 工具）
- 每个关键 run 的 `cfg.yml` + `stats/test_step0599.json` + `stats_masked/test_step0599*.json`
- 每个关键 run 的渲染视频：`videos/traj_4d_step599.mp4`
- 非原图可视化：token top‑k、TB scalars CSV、对比视频等

刻意不包含（合规原因）：

- `data/`（任何 raw dataset RGB/GT 原图）
- `outputs/**/renders/`（render canvas 可能包含原图拼接）
- overlay 类可视化（基于原图）
- 原始 TB event 文件（仅提供导出后的 CSV）

---

## 2) 数据、拆分与评测口径（决定一切是否可比）

### 2.1 数据与拆分（固定）

Data dir（本机路径；不在证据包内）：`data/thuman4_subject00_8cam60f`

固定设置（从各 run 的 `cfg.yml` 可复核）：

- frames：`start_frame=0`, `end_frame=60`（共 60）
- train cams：`02,03,04,05,06,07`
- val cam：`08`
- test cam：`09`

上游限制（会显著影响时序监督强度；是“已知硬事实”）：

- triangulation 仅覆盖 frame 0（跨帧几何约束极弱）
- Plan‑B init NPZ 不含非零 velocity（历史原因；Phase4 note 中已核对）

### 2.2 指标来源（full-frame vs FG ROI）

全图指标来自 trainer 落盘：

- `outputs/**/stats/test_step0599.json`（PSNR/SSIM/LPIPS/tLPIPS 等）

前景指标来自 evaluator（ROI=dataset silhouette）：

- script：`scripts/eval_masked_metrics.py`
- 输出：`outputs/**/stats_masked/test_step0599*.json`

评测使用的关键参数（Phase 3/4/6/7/pre‑expert 全部一致）：

- `mask_source=dataset`（THUman 提供的 silhouette masks）
- `mask_thr=0.5`（GT mask 二值化阈值）
- `bbox_margin_px=32`
- `lpips_backend=auto`（真实 LPIPS；使用 FreeTimeGsVanilla venv）

### 2.3 FG evaluator 的 4 种口径（为什么有 4 种）

同一个脚本会输出多种 “foreground quality” 口径，解决不同误差模式：

1) `psnr_fg` / `lpips_fg`（**主口径**）  
   - 做 bbox crop，再在 bbox 内把非前景像素填黑（fill-black），只比较 silhouette 内像素。  

2) `psnr_fg_area`（更“面积归一”）  
   - 与 `psnr_fg` 相同的 fill-black，但 MSE 分母按 **mask 面积**（而不是裁剪 bbox 的面积）计，避免 bbox 大小对 PSNR 产生额外影响。  

3) `lpips_fg_comp`（更“上下文不敏感”）  
   - 在**全图**上做复合图：`pred_comp = pred*keep + gt*(1-keep)`，再算 `LPIPS(pred_comp, gt)`。  
   - 直觉：把非 ROI 区域的差异“屏蔽掉”，但保留全图结构与边界上下文，避免 crop 引入的边界/对齐伪影主导 LPIPS。  

4) boundary band（边界带，Phase7 引入）  
   - `psnr_bd_area` / `lpips_bd_comp`：只评估 GT silhouette 边界附近 `radius_px` 的一圈 band（边界质量常是最敏感失败点）。  

> 我们的核心 gate 仍以 `psnr_fg↑ & lpips_fg↓` 为准；其余口径用于诊断“到底是 interior 还是 boundary 在坏”。

---

## 3) Phase 2 — Pseudomask Mining（后续所有 weak/feature 实验都依赖它）

### 3.1 cue_mining 的 frozen tags 与命令（可复核）

diff backend（frozen）：

```bash
DATA_DIR="data/thuman4_subject00_8cam60f"
OUT_DIR="outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3"
VENV_PYTHON="third_party/FreeTimeGsVanilla/.venv/bin/python"

"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIR" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend diff \
  --temporal_smoothing median3 \
  --overwrite
```

vggt backend（frozen；VGGT-1B depthdiff）：

```bash
DATA_DIR="data/thuman4_subject00_8cam60f"
OUT_DIR="outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3"
VENV_PYTHON="third_party/FreeTimeGsVanilla/.venv/bin/python"

HF_HUB_OFFLINE=0 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIR" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend vggt \
  --temporal_smoothing median3 \
  --vggt_model_id "facebook/VGGT-1B" \
  --vggt_cache_dir "/root/autodl-tmp/cache/vggt" \
  --vggt_mode crop \
  --overwrite
```

输出契约（两路一致）：

- `pseudo_masks.npz`
- `quality.json`
- `viz/grid_frame000000.jpg`（不含原图）

### 3.2 pseudo_masks 的语义（重要）

当前 pseudo mask 在本仓库中被视为 **dynamicness cue in [0,1]**（“哪里更可能是动态/前景区域”），用于 weak-fusion 或 gating 的软权重。  
它不是论文意义上“dynamic-region mask”的严格实现，除非另行证明等价性。

### 3.3 关键 QA 事实（影响后续预期）

在 `q0.995` frozen tags 下：

- `quality.json`：均非 all-black / all-white（避免完全崩溃）
- 但数值分布极度稀疏，且 **`mask_thr=0.5` 下几乎为空**（mIoU health-check 接近 0）

因此 Phase 3/6/7 主要使用了更“松”的 tag：`q0.950`，并在 Phase 6 中加入了 scaling（见 5.1）。

### 3.4 NPZ schema（你需要知道数组是什么）

`pseudo_masks.npz` 的关键字段（见实际 npz）：

- `masks`: float/uint8，shape 约为 `[T, V, Hm, Wm]`（此处 `T=60`，`V=8`，`mask_downscale=4`）
- `camera_names`: list/array（对应 V 维）
- `frame_start`, `num_frames`, `mask_downscale`

训练侧会把 `[Hm,Wm]` bilinear 上采样到训练渲染分辨率 `[H,W]`。

---

## 4) Runs 总览（公平性 gate：same-init 已满足）

所有关键对比均满足同一 init（从 `cfg.yml:init_npz_path` 可复核）：

- `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

baseline anchor：

- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`

### Phase 3（weak-fusion）

- treatment：`.../planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- control：`.../planb_init_weak_zeros_600`

### Phase 4（VGGT feature loss，same-init）

- `.../planb_feat_v2_gatediff0.10_600_sameinit`（`lambda_vggt_feat=0.01`）
- `.../planb_feat_v2_gatediff0.10_lam0.005_600_sameinit`（`lambda_vggt_feat=0.005`）

### Phase 6（FG realign follow-up）

weak-fusion follow-up（scaling + direction flip）：

- dyn_scaled：`.../planb_init_weak_dynp99_w0.8_600_r1`
- static_from_dyn_scaled：`.../planb_init_weak_staticp99_w0.8_600_r1`

feature loss follow-up（激活性澄清）：

- nogate + ds4：`.../planb_feat_v2_nogate_lam0.005_600_sameinit_r1`（`phi_size=8×9`）
- nogate + ds2：`.../planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1`（`phi_size=16×18`）

### Phase 7（ROI-alignment MVEs）

- MVE-1（weak early-only）：`.../planb_init_weak_staticp99_w0.8_end200_600_r2`
- MVE-2（feature + cue gating）：`.../planb_feat_v2_cuegate_lam0.005_600_sameinit_r2`

### Pre‑Expert（最低成本复核：2-seed）

seed replication（`w=0.8`）：

- baseline seed43/44：`.../_seedrep_planb_init_600_seed43|44`
- treatment seed43/44：`.../_seedrep_weak_staticp99_w0.8_600_seed43|44`

weight tune（`w=0.7`，只重跑 treatment，baseline 复用）：

- treatment seed43/44：`.../_seedrep_weak_staticp99_w0.7_600_seed43|44`

---

## 5) 关键结果汇总（step=599）

> 下方均为“可复核数字”，直接来自对应 `stats/*.json` 与 `stats_masked/*.json`。

### 5.1 Phase 3（weak-fusion）：全图略升，但 FG 退化

| run | PSNR | SSIM | LPIPS | PSNR_FG | LPIPS_FG |
|---|---:|---:|---:|---:|---:|
| baseline `planb_init_600` | 16.1520 | 0.5621 | 0.7325 | 16.8066 | 0.2439 |
| treat `diffmaskinv q0.950 w0.8` | 16.2809 | 0.5657 | 0.7265 | 16.6361 | 0.2508 |
| control `zeros w0.8` | 16.1574 | 0.5622 | 0.7347 | 16.4846 | 0.2446 |

结论：treatment 全图改善，但 FG 退化（`psnr_fg↓`、`lpips_fg↑`）。

### 5.2 Phase 4（feature loss）：guardrail PASS，但 FG 退化

| run | ΔtLPIPS | Δpsnr_fg | Δlpips_fg |
|---|---:|---:|---:|
| `lam=0.01` | +0.001030 | -0.348228 | +0.012048 |
| `lam=0.005` | +0.000043 | -0.124590 | +0.008596 |

结论：feature loss 路径不会显著破坏 tLPIPS，但 FG 仍系统性退化。

### 5.3 Phase 6 follow-up：证明“不是没算”，更像“信号/ROI 对齐不足”

weak-fusion follow-up（direction flip）：

| run | psnr | lpips | tlpips | psnr_fg | lpips_fg | psnr_fg_area | lpips_fg_comp |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16.1520 | 0.7325 | 0.007053 | 16.8066 | 0.24388 | 9.8674 | 0.04960 |
| dyn_p99_w0.8_r1 | 16.3438 | 0.7331 | 0.007187 | 16.5294 | 0.24611 | 9.5901 | 0.05174 |
| static_p99_w0.8_r1 | 16.2658 | 0.7437 | 0.008740 | 17.1048 | 0.24271 | 10.1655 | 0.05044 |

结论：static_p99 在 fg-local 更接近目标，但有全图 lpips 代价（trade-off），且后续证明该信号不稳定（见 pre‑expert）。

feature loss follow-up（nogate + ds2）：

| run | psnr | lpips | tlpips | psnr_fg | lpips_fg | psnr_fg_area | lpips_fg_comp |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16.1520 | 0.7325 | 0.007053 | 16.8066 | 0.24388 | 9.8674 | 0.04960 |
| feat_nogate_ds4_r1 | 16.1570 | 0.7314 | 0.007293 | 16.6825 | 0.24208 | 9.7433 | 0.05062 |
| feat_nogate_ds2_r1 | 16.1195 | 0.7367 | 0.007025 | 16.5078 | 0.24835 | 9.5686 | 0.05087 |

结论：`vggt_feat/active` 与 token grid 数量匹配（监督确实激活），但 FG 仍不稳定胜过 baseline。

### 5.4 Phase 7：两条 MVE 都未达成 FG gate（止损）

- MVE-1（weak early-only）：guardrail PASS，但 `Δpsnr_fg<0` 且 `Δlpips_fg>0`  
- MVE-2（feature + cue gating oracle）：监督激活非零，但 ROI 仍退化（全图近中性）

结论：即使使用 silhouette 作为 oracle gate，feature loss 仍未带来稳定 ROI 提升。

### 5.5 Pre‑Expert：2-seed 复核显示“FG win 不稳定”（关键结论）

严格 gate：`Δpsnr_fg > 0` **and** `Δlpips_fg < 0`；guardrail：`ΔtLPIPS <= +0.01`。

seed replication（`w=0.8`，treat - base）：

- seed43：`Δpsnr_fg=+1.619054`、`Δlpips_fg=-0.017309`、`ΔtLPIPS=+0.000795` → OK  
- seed44：`Δpsnr_fg=+0.280750`、`Δlpips_fg=+0.000248`、`ΔtLPIPS=+0.001401` → FG fails  
- `OVERALL_OK=False`

weight tune（`w=0.7`，treat - base；baseline 复用）：

- seed43：`Δpsnr_fg=+0.245204`、`Δlpips_fg=-0.007882`、`ΔtLPIPS=+0.000599` → OK  
- seed44：`Δpsnr_fg=+0.272591`、`Δlpips_fg=+0.001311`、`ΔtLPIPS=+0.000934` → FG fails  
- `OVERALL_OK=False`

结论：该“FG win”配置在 2-seed 复核下表现为 **seed-sensitive / 不稳定**；“简单调 weight”不足以稳定化。

---

## 6) 已排除的“实现/评测错误”类解释（重要：避免专家花时间走弯路）

1) **A/B confound（init 不一致）**：已通过 `cfg.yml:init_npz_path` gate 严格排除；Phase4 首轮 confounded run 已弃用。  
2) **FG ROI 为空**：关键 runs 的 `stats_masked` 中 `num_fg_frames=60`；非空。  
3) **weak/feature loss 没算**：TB 标量证明 weak path 与 feature path 均激活过（`pseudo_mask/active_ratio`、`vggt_feat/active`）。  
4) **仅由阈值 `mask_thr=0.5` 导致的假象**：FG eval 使用的是 **dataset GT silhouette**，不是 pseudo mask 阈值；因此“pseudo mask 很稀疏”不会让 `psnr_fg/lpips_fg` 变成空 ROI。  

---

## 7) 关键机制（专家只读本文也能理解）

### 7.1 Weak-fusion 的语义：mask 被解释为 dynamicness 并“降权 dynamic”

训练代码（节选；以 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` 为准）：

```py
mask_batch = self._get_pseudo_mask_batch(...)  # [B,1,H,W], dynamicness in [0,1]
alpha = float(cfg.pseudo_mask_weight)  # 0..1
w = 1.0 - alpha * mask_batch.permute(0, 2, 3, 1)  # [B,H,W,1]
weighted_l1 = (abs(pred-gt) * w).mean() / w.mean().clamp(min=1e-6)
l1_loss = weighted_l1
```

关键后果：

- dynamicness 越大（越“动态/前景”），权重越小 → **默认不直接优化 FG ROI**，而更像在“压动态像素的重建监督”。
- 若 mask 近似常数（尤其是 invert/staticness 近 1），归一化后容易出现近 no-op 或引入强 trade-off。

### 7.2 Feature loss 的空间粒度与 gating

Phase4/6 的 token-proj cache 常见为 `phi_size=[8,9]`（72 cells）。`top_p=0.1` 时只激活 8 个 cell，空间监督非常粗。

Phase7 实现了 `gating='cue'`（使用 dataset silhouette mask 作为 dense gate 的 oracle 实验）；即便如此 ROI 仍未稳定提升 → 说明失败不完全由 “gate 不对” 导致。

---

## 8) 你给我的建议应如何表达（我最需要的输出格式）

请按如下模板给建议（越具体越好）：

1) **Root cause #k（置信度 X/10）**：一句话描述  
   - 证据：指出本文中支持它的 1–3 条事实  
   - 最小验证实验：改动点（尽量 1 个变量），跑哪些 run，对照谁，预算（建议 ≤ 600 steps），预期趋势  
   - 判定标准：哪些指标必须同向？是否接受 trade-off？  

---

## Appendix A) 最小复核命令（如果你想复算指标）

masked eval（对任意 result_dir）：

```bash
VENV_PYTHON="third_party/FreeTimeGsVanilla/.venv/bin/python"
DATA_DIR="data/thuman4_subject00_8cam60f"
RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600"

"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir "$DATA_DIR" \
  --result_dir "$RESULT_DIR" \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --mask_thr 0.5 \
  --boundary_band_px 3 \
  --lpips_backend auto
```

TB 标量抽取（示例：pseudo_mask/active_ratio）：

```bash
python3 - <<'PY'
import glob
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
run="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.7_600_seed44"
f=sorted(glob.glob(run+"/tb/events.out.tfevents.*"))[0]
ea=EventAccumulator(f); ea.Reload()
ev=ea.Scalars("pseudo_mask/active_ratio")
print("first", ev[0].step, float(ev[0].value))
print("last ", ev[-1].step, float(ev[-1].value))
PY
```

---

如需完整可审计证据包（cfg/JSON/视频/可视化 + sha256 manifest），可索取 `outputs/expert_diagnosis_pack_2026-03-05_v2.tar.gz`。

