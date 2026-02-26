# Owner A 计划：Feature‑Loss 梯度链验收（10 step）+ postfix_600 暴露（GPU0）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner A（GPU0，32GB）  
并行约束：Owner B 当前无 GPU，正推进 No‑GPU 写作/打包；本计划可独立执行，产物用于 B 的 v21+ evidence 刷新与答辩防守。

## 0. 目标（面向“完成项目”）

1. 补齐 `docs/reviews/2026-02-26/meeting-decision.md` 的 **Feature‑loss 最小失败归因包第 (5) 项**：梯度链检查（10 step 小跑）。
2. 将历史 `feature_loss_v2_postfix_600` 的 **关键产物暴露到主阵地 `outputs/`**，避免只存在 worktree 路径导致“证据链不可复现/不可引用”。

## 1. 不可违反的纪律

- 不新增任何 full600 训练（本计划仅 `MAX_STEPS=10` 的诊断小跑）。
- 不改 `protocol_v1` 的数据分布项（相机划分/seed/global_scale/keyframe_step/config 维持一致）。
- `data/`、`outputs/` 不入库；只提交 `docs/`、`notes/`。

## 2. 交付物（可验收）

入库交付（必须）：
- `notes/feature_loss_v2_grad_chain_owner_a.md`
- `notes/handoff_feature_loss_v2_grad_chain_owner_a.md`

主阵地可见（不入库，但供 B 直接复用）：
- 梯度 CSV（写入 evidence 会被自动收录）：
  - `outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv`
- 若存在则暴露的 v2 postfix full600 关键路径（以 symlink 或最小复制方式均可）：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/`
    - 至少包含：`stats/test_step0599.json`、`stats/val_step0599.json`、`videos/traj_4d_step599.mp4`、`tb/events.out.tfevents*`

## 3. 任务分解

### A81. 预检与对齐（10 分钟）

```bash
cd /root/projects/4d-recon
git fetch origin
git status -sb
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
```

验收：全部 PASS，工作区干净或仅包含计划内改动。

### A82. 暴露 `feature_loss_v2_postfix_600` 到主阵地 outputs（不新增训练）

背景：当前主仓 `outputs/protocol_v1/...` 下可能缺失 `feature_loss_v2_postfix_600`，但 worktree 中存在：
- `.worktrees/owner-a-20260226-v2-postfix/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600`

执行策略（二选一，推荐 1）：

1) **推荐：建立 symlink（最快且不复制大目录）**

```bash
cd /root/projects/4d-recon
SRC="$(realpath -m .worktrees/owner-a-20260226-v2-postfix/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600)"
DST="outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600"
test -d "$SRC"
mkdir -p "$(dirname "$DST")"
ln -sfn "$SRC" "$DST"
ls -la "$DST" | head
```

2) 备选：仅复制“最小可引用产物”（避免大目录）

验收：`$DST/stats/test_step0599.json` 与 `$DST/videos/traj_4d_step599.mp4` 可读。

### A83. Feature‑loss 梯度链检查（10 step，GPU0）

目标：证明 feature-loss 的梯度链路**非零且有限**（至少到 `velocities/durations` 这一类 gaussian params）。

说明：
- 这不是为了“修好 feature-loss”，而是为了在写作中排除“梯度链断/实现无效”这种致命质疑。
- 训练输出目录建议使用临时目录，避免污染 `metrics.csv`/scoreboard；但梯度 CSV 明确写入 `outputs/report_pack/diagnostics/`（供 evidence 自动收录）。

命令（建议直接调用 trainer，避免 runner 限制额外 flags）：

```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py

DATA_DIR=data/selfcap_bar_8cam60f
INIT_NPZ=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz
CACHE_NPZ=.worktrees/owner-a-20260226-v2-postfix/outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz

OUT_TMP=/tmp/feature_loss_v2_grad10
mkdir -p "$OUT_TMP"

# 10-step: isolate feature-loss as much as possible (disable other loss weights).
CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$INIT_NPZ" \
  --result-dir "$OUT_TMP" \
  --start-frame 0 \
  --end-frame 60 \
  --max-steps 10 \
  --eval-steps 10 \
  --save-steps 10 \
  --seed 42 \
  --train-camera-names 02,03,04,05,06,07 \
  --val-camera-names 08 \
  --test-camera-names 09 \
  --eval-sample-every 1 \
  --eval-sample-every-test 1 \
  --render-traj-path fixed \
  --global-scale 6 \
  --lambda-img 0 \
  --lambda-ssim 0 \
  --lambda-perc 0 \
  --lambda-4d-reg 0 \
  --lambda-duration-reg 0 \
  --vggt-feat-cache-npz "$CACHE_NPZ" \
  --lambda-vggt-feat 0.01 \
  --vggt-feat-loss-type cosine \
  --vggt-feat-every 1 \
  --vggt-feat-phi-name token_proj \
  --vggt-feat-gating none \
  --t0-debug-interval 1 \
  --t0-grad-log-path outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv
```

验收（必须满足）：
- `outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv` 生成且非空
- CSV 中 `vel_grad_norm`、`duration_grad_norm` 至少在若干 step 为非 0，且 `*_finite` 为 1

止损：
- 若出现 NaN/Inf 或训练报错：立即停止，记录错误到 `notes/feature_loss_v2_grad_chain_owner_a.md`（不继续扩展跑）。

### A84. 结论沉淀与交接（入库）

1) 记录结果：`notes/feature_loss_v2_grad_chain_owner_a.md`

必须包含：
- 上述命令（原样粘贴）
- `feature_loss_v2_grad_chain.csv` 的前 10 行摘要（含非零与 finite 证明）
- 一句话结论：梯度链路存在/不存在（严格措辞）

2) 交接给 B：`notes/handoff_feature_loss_v2_grad_chain_owner_a.md`

必须包含：
- `feature_loss_v2_postfix_600` 暴露路径（symlink 或复制策略）
- 梯度 CSV 路径与使用方式（B 在 v21 打包时无需 GPU）

### A85. 提交与推送

只提交 notes（不提交 outputs/data）：

```bash
cd /root/projects/4d-recon
git status -sb
git add notes/feature_loss_v2_grad_chain_owner_a.md notes/handoff_feature_loss_v2_grad_chain_owner_a.md
git commit -m "docs(feature-loss): add v2 grad-chain 10-step evidence note"
git push origin HEAD:main
```

