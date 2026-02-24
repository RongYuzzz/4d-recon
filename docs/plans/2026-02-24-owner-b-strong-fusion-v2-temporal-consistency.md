# Strong Fusion V2 (Temporal Consistency) Implementation Plan (Owner B)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不破坏现有 `protocol_v1` 可复现性的前提下，把 strong fusion 从“attempt_and_audit（stoploss）”推进到“机制更合理、信号更干净”的 V2：基于 KLT 轨迹的 **pred@t vs pred@t'** 时序一致性约束，并用更严格的 KLT 可靠性过滤/权重，给出是否值得继续投入 strong 的结论（含证据）。

**Architecture:** 复用现有 `temporal_corr.npz` 契约与提取脚本，扩展 strong loss 的计算模式：
- v1（现状）：`pred_t(src_xy)` vs `GT_{t'}(dst_xy)`（仅作历史对照）
- v2（目标）：`pred_t(src_xy)` vs `pred_{t'}(dst_xy)`（需要额外一次 rasterize 在 `t'`）
同时增强 KLT extractor：forward-backward check + 以误差生成 `weight`，降低错误对应对训练的干扰。

**Tech Stack:** Bash、Python、OpenCV KLT（`cv2.calcOpticalFlowPyrLK`）、PyTorch trainer（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`）、脚本级测试（`scripts/tests/*.py`）。

---

### Task B23: 建隔离 Worktree

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-b-20260224-strong-v2 .worktrees/owner-b-20260224-strong-v2 main
git -C .worktrees/owner-b-20260224-strong-v2 status --porcelain=v1
```

Expected:
- worktree 干净。

---

### Task B24: 写清 strong v2 设计与止损口径（先写文档再改代码）

**Files:**
- Update: `notes/attention_loss_design.md`
- Create: `notes/strong_fusion_v2_temporal_consistency.md`

写清 5 点（必须）：
1. v2 loss 定义（`pred_t` vs `pred_t'`，L1/Charbonnier/Huber 任选其一）
2. `t` 与 `t'` 的归一化时间计算（对齐 `FreeTime_dataset.py`：`frame_offset/(total_frames-1)`）
3. 采样策略（每 step 最大 pairs，是否随机子采样）
4. 对应置信度（KLT forward-backward 误差/err -> weight 的具体公式）
5. Stoploss（任一触发即停）：
   - step time 翻倍且无趋势
   - `corr_pairs==0` 或频繁退化
   - 指标与视觉均无改善，且 failure 机理可解释

验收：
- 文档可以让第三人复现并理解“为何 v2 比 v1 更合理”。

---

### Task B25: 扩展 trainer 支持 strong loss mode（V2 需要 second render）

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Modify: `scripts/tests/test_strong_fusion_flags.py`（或新增一个脚本级 test）

Step 1: 加入配置项（默认不影响 baseline/weak）
- 新增 config（建议）：
  - `temporal_corr_loss_mode: str = "pred_gt"`，可选 `pred_gt` / `pred_pred`
- 默认保持 `lambda_corr=0` 时完全不生效。

Step 2: 实现 `pred_pred` 分支（核心）
- 在 `_compute_temporal_corr_loss(...)` 内：
  - 从 `dst_frame` 计算 `t_dst = (dst_frame - cfg.start_frame)/max((cfg.end_frame-cfg.start_frame)-1,1)`
  - 调用一次 `self.rasterize_splats(..., t=t_dst, ...)` 得到 `colors_dst`
  - 取 `pred_src = colors[b] @ src_xy`，`pred_dst = colors_dst[b] @ dst_xy`
  - `loss = mean(|pred_src - pred_dst| * weight)`（可除以 `weight.mean()` 做归一化）

Step 3: 轻量日志（便于审计）
- 每 N step 打印：
  - `corr_mode`
  - `corr_pairs`
  - `corr_loss`（标量）

Step 4: 脚本级 test
- 更新/新增 test 断言：
  - config flag 名存在
  - `pred_pred` 字符串在实现中可见（避免回归删掉）

验收：
- `python3 scripts/tests/test_strong_fusion_flags.py` PASS。

---

### Task B26: 增强 KLT extractor 可靠性（forward-backward + weight）

**Files:**
- Modify: `scripts/extract_temporal_correspondences_klt.py`
- Modify: `scripts/tests/test_temporal_correspondences_klt_contract.py`
- Update: `notes/selfcap_temporal_corr_klt.md`

Step 1: forward-backward check
- 增加 `--fb_err_thresh`（默认例如 `1.5` 像素）
- 计算：
  - forward：`p0 -> p1`
  - backward：`p1 -> p0_back`
  - `fb_err = ||p0 - p0_back||`
- keep：`fb_err < thresh`

Step 2: weight 公式（写入 npz 的 `weight`）
- 建议：`weight = exp(-fb_err / sigma)` 或 `1/(1+fb_err)`，并裁剪到 `[w_min, 1]`

Step 3: 单测
- 断言：
  - keys 契约不变
  - `weight` 非全 1，且在 `[0,1]` 内

验收：
- 在 `data/selfcap_bar_8cam60f` 上重新生成：
  - `outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz`
  - `outputs/correspondences/selfcap_bar_8cam60f_klt/viz/*`

---

### Task B27: V2 实验（smoke60 + 200-step sweep + 600-step attempt）

**Runs (GPU1):**
- smoke60：确认不崩、`corr_pairs>0`、step 时间可接受
- sweep200：`lambda_corr ∈ {0.005, 0.01, 0.02}`，`mode=pred_pred`，`end_step=200`，`max_pairs=200`
- full600：选 sweep 最稳的一组跑满 600

Run（示例）：
```bash
cd /root/projects/4d-recon

# smoke
GPU=1 MAX_STEPS=60 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_smoke60 \
LAMBDA_CORR=0.01 TEMPORAL_CORR_END_STEP=60 TEMPORAL_CORR_MAX_PAIRS=200 \
STRONG_MODE=pred_pred \
bash scripts/run_train_ours_strong_selfcap.sh

# sweep (200 steps)
for lam in 0.005 0.01 0.02; do
  GPU=1 MAX_STEPS=200 \
  RESULT_DIR=outputs/sweeps/selfcap_bar_strong_v2_lam${lam}_end200_pairs200_s200 \
  LAMBDA_CORR=$lam TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
  STRONG_MODE=pred_pred \
  bash scripts/run_train_ours_strong_selfcap.sh
done

python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

验收：
- v2 的 600-step 目录存在 `stats/{val,test}_step0599.json` + `videos/traj_4d_step599.mp4`
- `outputs/report_pack/metrics.csv` 有 v2 条目（val/test）

---

### Task B28: 结论与交接（继续 or stoploss）

**Files:**
- Update: `notes/ours_strong_attempt_selfcap_bar.md`（追加 v2 结果与结论）
- (Optional) Create: `notes/ours_strong_v2_failure_analysis.md`

必须写清：
- v2 是否优于 v1/weak/baseline（同预算对比）
- 若 stoploss：
  - 主要阻塞点（loss 信号弱、对应噪声、算力开销、冲突项）
  - 下一步建议（例如：更长 track、多帧一致性、引入特征空间一致性、用 cue/attention 过滤对应）

验收：
- C 可直接用文档与 `outputs/report_pack/metrics.csv` 做最终证据包。

