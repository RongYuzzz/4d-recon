# Owner A 计划：Plan‑B 组件消融（smoke200，budget-neutral）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner A（GPU0，32GB）  
并行约束：Owner B 当前无 GPU，本计划不依赖 B，可独立推进；产物以“可被 B 直接打包/写作复用”为交付口径。

## 0. 目标（为什么要做）

Plan‑B 已在 canonical 与 seg2 full600 上给出显著收益，但目前缺少“机制解释”级别证据。该计划补齐最小组件消融，回答：

- Plan‑B 的收益主要来自哪几个稳定性补丁（mutual NN / drift removal / clip）？
- 这些补丁缺失时是否会显著退化（可写入论文/答辩的“方法必要性”）？

## 1. 不可违反的纪律

- 不新增 full600（本计划只做 `MAX_STEPS=200` smoke runs）。
- 不改 `protocol_v1` 的数据分布项（相机划分/seed/global_scale/keyframe_step/config 等保持不变）。
- 只用 GPU0。
- `outputs/` 与 `data/` 不入库；只提交 `docs/`、`notes/`、`scripts/tests/`（若确有必要）。

## 2. 产物清单（交付给 B 的“可复用资产”）

- 新增 smoke200 run 目录（不入库，但必须在主阵地 `outputs/` 可见）：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_no_drift_smoke200/`
  - `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_no_mutual_smoke200/`
  - `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_clip_p95_smoke200/`（可选，见 Task A73）
- 每个 run 必须包含（用于 report-pack 扫描与审计）：
  - `stats/test_step0199.json`
  - `stats/val_step0199.json`
  - `stats/throughput.json`
  - `videos/traj_4d_step199.mp4`
- 消融结论记录（入库）：
  - `notes/planb_component_ablation_smoke200_owner_a.md`
  - `notes/handoff_planb_component_ablation_owner_a.md`

## 3. 任务分解

### A71. 预检（必须先做）

在 `origin/main` 上执行：

```bash
cd /root/projects/4d-recon
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
test -d data/selfcap_bar_8cam60f/triangulation
```

验收：全部 PASS。

### A72. 生成 Plan‑B init 变体（CPU，可并行于 B 写作）

统一基线模板：

- `DATA_DIR=data/selfcap_bar_8cam60f`
- `BASELINE_INIT=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz`

生成三个变体（每个变体用不同 `--out_dir`，避免覆盖）：

1) no_drift（禁用 drift removal）

```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f \
  --baseline_init_npz outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --disable_drift_removal \
  --out_dir outputs/plan_b_ablation/selfcap_bar_8cam60f/no_drift
```

2) no_mutual（禁用 mutual NN）

```bash
$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f \
  --baseline_init_npz outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --no_mutual_nn \
  --out_dir outputs/plan_b_ablation/selfcap_bar_8cam60f/no_mutual
```

3) clip_p95（更激进的 clip；默认是 quantile=0.99，这里做 0.95 的对照）

```bash
$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f \
  --baseline_init_npz outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --clip_quantile 0.95 \
  --out_dir outputs/plan_b_ablation/selfcap_bar_8cam60f/clip_p95
```

验收：

- 每个 `out_dir` 下都生成：
  - `init_points_planb_step5.npz`
  - `velocity_stats.json`

### A73. smoke200 训练消融（GPU0）

对照组不重跑，复用已存在的两条（确保口径一致）：

- baseline：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window`
- planb default：`outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200`

对三个变体分别跑 smoke200（只变 `PLANB_INIT_NPZ` 与 `RESULT_DIR`）：

1) no_drift

```bash
GPU=0 MAX_STEPS=200 \
PLANB_INIT_NPZ=outputs/plan_b_ablation/selfcap_bar_8cam60f/no_drift/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_no_drift_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

2) no_mutual

```bash
GPU=0 MAX_STEPS=200 \
PLANB_INIT_NPZ=outputs/plan_b_ablation/selfcap_bar_8cam60f/no_mutual/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_no_mutual_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

3) clip_p95

```bash
GPU=0 MAX_STEPS=200 \
PLANB_INIT_NPZ=outputs/plan_b_ablation/selfcap_bar_8cam60f/clip_p95/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_clip_p95_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

止损线（任一触发即停本变体，记录原因即可，不硬跑完）：

- 训练不稳定（loss 爆/渲染发散）
- `stats/test_step0199.json` 缺失或指标“全线崩”（PSNR/LPIPS/tLPIPS 三项显著恶化）

### A74. 结论沉淀与交接（入库）

1) 刷新 metrics（本地即可，不要求提交 `outputs/report_pack/*`）

```bash
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

2) 用统一分析脚本生成 smoke200 对比表（入库）

```bash
python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md notes/planb_component_ablation_smoke200_owner_a.md \
  --step 199 \
  --stage test \
  --select_prefix outputs/protocol_v1/ \
  --select_contains selfcap_bar_8cam60f \
  --baseline_regex baseline_smoke200_planb_window
```

3) 追加 handoff（入库）：`notes/handoff_planb_component_ablation_owner_a.md`

必须包含：

- 三个变体的 `RESULT_DIR` 列表（供 B 直接打包/引用）
- 一句“可写进正文”的结论（例如：禁用 drift removal 会显著恶化 tLPIPS，说明其必要）

### A75. 收尾（提交）

只提交文本（不提交 `outputs/`、`data/`）：

```bash
cd /root/projects/4d-recon
git status -sb
git add notes/planb_component_ablation_smoke200_owner_a.md notes/handoff_planb_component_ablation_owner_a.md
git commit -m "docs(planb): add component ablation smoke200 note (mutual/drift/clip)"
git push origin HEAD:main
```

验收：`origin/main` 可见新 notes，且不包含任何 `outputs/` 大文件变更。

## 4. 交接给 B（并行点）

Owner B 后续只需要做 No‑GPU 刷新：

- `python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack`
- `python3 scripts/summarize_scoreboard.py`
- `python3 scripts/pack_evidence.py --out_tar artifacts/report_packs/report_pack_2026-02-26-vXX.tar.gz`
- 生成 `docs/report_pack/2026-02-26-vXX/` 快照并更新 `SHA256SUMS.txt`

