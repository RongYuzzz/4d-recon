# OpenProposal — Phase 3 审查报告（Weak Supervision Closed-Loop）

Date: 2026-03-04 (UTC)  
Scope: 审查 `docs/plans/2026-03-03-openproposal-phase3-weak-supervision.md` 的执行质量与可复核性（仅 Phase 3）。

## 0) 审查结论（摘要）

- **总体结论：Phase 3 达标（PASS）**：已把 Phase 2 的 pseudo mask 注入训练（weak-fusion），并在 THUman4.0 s00 上给出可审计的 baseline vs treatment A/B 结论（全图提升、前景退化），同时提供了 control（zeros）与本机可播放的对照视频。
- **A/B 的抗混淆措施到位**：baseline / treatment / control 三条 run 的 `init_npz_path` 一致，且关键超参（`seed/max_steps/lambda_*`、相机拆分）一致，差异集中在 `pseudo_mask_*` 字段，结论可复核。
- **计划文档存在 2 处“会直接跑不通”的命令问题（已修复）**：baseline runner 调用缺少 `result_dir` 参数、side-by-side 视频脚本使用了错误的 positional 参数形式（脚本仅支持 `--left/--right/...`）。

## 1) 目标与口径对齐检查

Phase 3 目标（来自计划）：
- 将 Phase 2 的 `pseudo_masks.npz` 用入训练闭环（weak reweight），并产出可审计 A/B 结论（提升/退化均可，但必须能复核与解释）。

评测口径（来自 Phase 1 evaluator）：
- masked eval：`mask -> bbox crop (+margin=32) -> fill-black outside mask -> metric`
- `mask_source=dataset`（THUman4.0 dataset-provided masks）
- `mask_thr=0.5`
- LPIPS：使用 FreeTimeGsVanilla venv 下的 `--lpips_backend auto`（真实 LPIPS；非 dummy）

合规（local-eval only）：
- 不提交 `data/`、`outputs/`；对照视频仅留在 `outputs/qualitative_local/**`。

## 2) 关键产物与复核点（local-only evidence）

### 2.1 训练 runs（均为 step=599 指标）

根目录：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/`

- baseline：`planb_init_600`
- treatment：`planb_init_weak_diffmaskinv_q0.950_w0.8_600`
- control：`planb_init_weak_zeros_600`

每条 run 的可复核产物（本次审查已核对存在性）：
- `cfg.yml`
- `stats/test_step0599.json`
- `stats_masked/test_step0599.json`
- `videos/traj_4d_step599.mp4`

### 2.2 注入用 mask

- treatment 的 pseudo mask（invert staticness）：
  - `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_invert_staticness.npz`
- control 的 zero mask：
  - `outputs/cue_mining/openproposal_thuman4_s00_zeros_ds4/pseudo_masks.npz`（已验证全 0）

## 3) 指标复核（从落盘 JSON 读取）

Full-frame（`stats/test_step0599.json`）：
- baseline：PSNR 16.1520 / SSIM 0.5621 / LPIPS 0.7325
- treatment：PSNR 16.2809 / SSIM 0.5657 / LPIPS 0.7265
- control：PSNR 16.1574 / SSIM 0.5622 / LPIPS 0.7347

结论（treatment - baseline）：
- **ΔPSNR +0.1289，ΔSSIM +0.0036，ΔLPIPS -0.0059（提升）**

Foreground-masked（`stats_masked/test_step0599.json`）：
- baseline：PSNR_FG 16.8066 / LPIPS_FG 0.2439
- treatment：PSNR_FG 16.6361 / LPIPS_FG 0.2508
- control：PSNR_FG 16.4846 / LPIPS_FG 0.2446

结论（treatment - baseline）：
- **ΔPSNR_FG -0.1705，ΔLPIPS_FG +0.0069（退化）**

## 4) 抗混淆检查（A/B validity）

从 `cfg.yml` 抽取关键字段复核（本次审查已核对）：
- 三条 run 的 `init_npz_path` 一致：
  - `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- 训练与评测拆分一致：train=`02..07`, val=`08`, test=`09`
- `seed=42`, `max_steps=600`, `lambda_img/ssim/perc/4d_reg/duration_reg` 一致
- 差异集中在：
  - `pseudo_mask_npz / pseudo_mask_weight / pseudo_mask_end_step`

因此 Phase 3 的 A/B 结论可认为有效（不被 init/seed/split 混淆）。

## 5) 定性证据（local only）

- side-by-side（baseline vs weak，无 GT）：
  - `outputs/qualitative_local/openproposal_phase3/planb_vs_weak_step599.mp4`

## 6) 发现的问题 / 风险与建议

1) **计划文档的两处命令错误（已修复）**
   - baseline runner 调用缺少 `"$RESULT_DIR"` 参数，按 runner 约定会失败或写错目录；
   - `scripts/make_side_by_side_video.sh` 仅支持 flag 形式（`--left/--right/...`），计划用 positional 会直接报错。

2) **masked evaluator 输出 JSON 未显式记录 `lpips_backend`**
   - 风险：后续整理表格时可能把 dummy LPIPS 与真实 LPIPS 混用。
   - 当前缓解：Phase 3 结果 note 已显式声明本次使用 `lpips_backend=auto`（真实 LPIPS）。
   - 建议（可选）：后续给 `scripts/eval_masked_metrics.py` 输出加一个 `lpips_backend` 字段，永久消歧。

3) **invert 后 mask 几乎全 1（静态性占绝大多数）**
   - 现象：`pseudo_masks_invert_staticness.npz` 的 `mean(mask01)≈0.9985`（本质上对大多数像素施加强下调）。
   - 这与 “全图指标提升但 FG 退化” 的现象一致，建议 Phase 4/后续排查优先关注 `pseudo_mask_weight`、invert/非 invert 选择、以及 mask 语义与目标（FG silhouette）是否一致。

## 7) Phase 3 审查 Gate Verdict

- weak 注入闭环：PASS
- 可审计 A/B 结论：PASS
- 抗混淆（same init / same split / same seed）：PASS
- 合规（local-eval only）：PASS

