# Owner B Strong Fusion Attempt + Audit Plan (Next)

> 状态：待执行（Next）。本计划的目标是“attempt_and_audit”，不以指标必胜为前提，但必须产出可复现与可审计证据。

**Goal:** 在 `SelfCap bar 8cam60f`（`data/selfcap_bar_8cam60f`）上完成一次或多次 `Ours-Strong` 训练尝试，得到：
- 至少 1 个可复现 run（同预算 `MAX_STEPS=600`）与视频/指标；
- 清晰的参数与运行记录（含对应可视化）；
- 若失败，给出“可辩护”的 stoploss 结论与下一步建议。

**Non-Goal (本轮不做):**
- 不重写 KLT/光流或引入大工程（RAFT/全局 matching 等）。
- 不追求多场景刷榜；先在单场景给出强融合是否值得继续投入的结论。
- 不把 `data/` 与 `outputs/` 入库（只入脚本/文档/测试）。

**Parallel Safety:** Owner B 主要占用 `GPU1`，不阻塞 A（GPU0 weak tuning）与 C（GPU2 报表/打包）。

**Default Resources:** `GPU1`；优先 1 次 `60-step` smoke + 1 次 `200-step` 选参 + 1 次 `600-step` 交付 run（最多 3 次 full run，对齐 protocol v1）。

---

## Task B17: 创建隔离 Worktree/分支（避免污染 main）

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-b-20260224-strong-audit .worktrees/owner-b-20260224-strong-audit main
git -C .worktrees/owner-b-20260224-strong-audit status --porcelain=v1
```

Expected:
- worktree 干净（`status` 输出为空）

---

## Task B18: Strong Fusion 60-step Smoke（先确保“可跑 + 不爆炸 + 速度可接受”）

前置输入（应已存在）：
- `data/selfcap_bar_8cam60f/triangulation/`（60 帧）
- `outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz`

Run（示例）：
```bash
cd /root/projects/4d-recon
GPU=1 MAX_STEPS=60 \
RESULT_DIR=outputs/gate1_selfcap_ours_strong_smoke60 \
TEMPORAL_CORR_NPZ=outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz \
LAMBDA_CORR=0.05 TEMPORAL_CORR_END_STEP=60 TEMPORAL_CORR_MAX_PAIRS=200 \
PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=60 \
bash scripts/run_train_ours_strong_selfcap.sh
```

验收：
- `outputs/gate1_selfcap_ours_strong_smoke60/videos/traj_4d_step59.mp4` 存在
- 日志中出现 strong 配置加载信息（`[StrongFusion] Loaded temporal corr...`）
- `corr_pairs > 0`（表示 loss 实际生效，不是被自动禁用）

备注：
- 若 step 过慢或 IO 过重，优先把 `TEMPORAL_CORR_MAX_PAIRS` 降到 `50~200`（避免每步处理 500 对应）。

---

## Task B19: Strong 超参小 sweep（200-step 选候选）

目标：
- 在可控预算下，找到“不会明显伤害 baseline/weak”的 strong 组合，为 600-step 交付做准备。

固定条件（与 protocol v1 对齐）：
- `DATA_DIR=data/selfcap_bar_8cam60f`
- `START_FRAME=0 END_FRAME=60`
- `GLOBAL_SCALE=6`，`KEYFRAME_STEP=5`

Sweep 建议（先 3 组，不要超过 6 组）：
- `LAMBDA_CORR`: `0.01, 0.02, 0.05`
- `TEMPORAL_CORR_END_STEP`: `100 或 200`
- `TEMPORAL_CORR_MAX_PAIRS`: `100 或 200`

Run（示例）：
```bash
cd /root/projects/4d-recon
for lam in 0.01 0.02 0.05; do
  GPU=1 MAX_STEPS=200 \
  RESULT_DIR=outputs/gate1_selfcap_ours_strong_sweep_lam${lam} \
  TEMPORAL_CORR_NPZ=outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz \
  LAMBDA_CORR=$lam TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
  PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=200 \
  bash scripts/run_train_ours_strong_selfcap.sh
done
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

验收：
- 每个 run 都产出 `videos/traj_4d_step199.mp4` 与 `stats/val_step0199.json`
- `outputs/report_pack/metrics.csv` 增加对应行
- 新增运行记录：`notes/ours_strong_sweep_selfcap_bar.md`（写清楚每组参数、耗时、是否稳定、定性观测）

---

## Task B20: 选 1 个候选跑满 600-step（交付给 midterm 的 strong attempt）

选择规则（建议）：
- 优先：训练稳定（无 NaN、无明显发散），且 `corr_pairs` 稳定非 0
- 次优：指标不显著变差（允许小幅波动），或在动态区域定性更稳（smear 更少）

Run（示例）：
```bash
cd /root/projects/4d-recon
GPU=1 MAX_STEPS=600 \
RESULT_DIR=outputs/gate1_selfcap_ours_strong_600 \
TEMPORAL_CORR_NPZ=outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz \
LAMBDA_CORR=0.02 TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_strong_selfcap.sh

python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

验收：
- `outputs/gate1_selfcap_ours_strong_600/videos/traj_4d_step599.mp4` 存在
- `outputs/report_pack/metrics.csv` 含 strong 条目（gate 应为 `gate1`）

---

## Task B21: 审计包补齐（matching_viz + loss 口径 + stoploss）

目标：
- 满足 protocol v1 对 `ours_strong.required_artifacts` 的可审计要求，即使结论是 stoploss 也要“证据充分”。

交付物（建议）：
- 更新或新增：
  - `notes/ours_strong_attempt_selfcap_bar.md`
- 文档内容必须包含：
  - 运行命令（完整 env）
  - 使用的 `TEMPORAL_CORR_NPZ` 与生成方式（引用 `notes/selfcap_temporal_corr_klt.md`）
  - `outputs/correspondences/.../viz/` 的截图路径（matching 可视化）
  - 训练稳定性：是否出现 NaN、是否出现 `corr_pairs==0`、step 时间范围（粗略即可）
  - 结论：继续投入 or stoploss（写清依据与下一步动作）

验收：
- 文档可让第三人“拿命令复现”并理解 stoploss/继续原因

---

## Task B22 (Optional, Timebox 4h): 若 corr_pairs 经常为 0 或强融合被自动禁用，做最小修复

常见触发：
- parser 的 `factor/undistort/crop` 导致像素空间不一致，strong 自动禁用；
- `TEMPORAL_CORR_MAX_PAIRS` 过大导致 step 过慢；
- KLT 轨迹覆盖不足（动态/纹理弱导致）。

允许的最小修复（只做其一）：
1. 调整 extractor 使其输出的 `image_width/image_height` 与训练时 `factor` 一致（或明确把 extractor 在训练同像素空间执行）。
2. 在 trainer 里把 `idxs[:max_pairs]` 改为 “随机子采样” 以避免固定偏置（默认行为不变，受 `TEMPORAL_CORR_MAX_PAIRS` 控制）。

验收：
- 不开启 strong 时 baseline/weak 行为不变
- strong run `corr_pairs` 稳定非 0，或 step 时间显著下降

