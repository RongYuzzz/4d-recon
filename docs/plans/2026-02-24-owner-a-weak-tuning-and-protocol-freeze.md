# Owner A Weak Fusion Tuning + Protocol Freeze Plan (Next)

> 状态：待执行（Next）。本计划以 `docs/protocol.yaml` 为准，且所有改动必须保证 baseline 可复现不回归。

**Goal:** 在 `SelfCap bar 8cam60f`（`data/selfcap_bar_8cam60f`）上，把 “Ours-Weak（cue mining + 弱融合）” 调到**不明显劣于 baseline**（同预算 `MAX_STEPS=600`），并把 protocol/入口/产物路径固定成“可审计、可复现、可打包”的形态。

**Non-Goal (本轮不做):**
- 不做 strong fusion（对应项由 Owner B 主导；本计划只保证 weak 不拖后腿）。
- 不改数据入口契约（adapter/triangulation 已稳定）。
- 不做多场景刷榜；先单场景把 midterm 口径讲清楚。

**Parallel Safety:** 所有新增能力默认关闭；Owner A 主要占用 `GPU0`，不阻塞 B（GPU1 strong）与 C（GPU2 报表/打包）。

**Default Resources:** `GPU0`；先 `200-step` 小 sweep 选候选，再做 `600-step` 复跑；`outputs/` 不入库。

---

## Task A17: 创建隔离 Worktree/分支（避免污染 main）

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-a-20260224-weak-tune .worktrees/owner-a-20260224-weak-tune main
git -C .worktrees/owner-a-20260224-weak-tune status --porcelain=v1
```

Expected:
- worktree 干净（`status` 输出为空）

---

## Task A18: Protocol 冻结与主线 Git Hygiene（一次性把“口径”定死）

动机：
- 当前已有 `docs/protocol.yaml` 与 `docs/protocols/protocol_v1.yaml`（含更新策略与 midterm/final 要求）；需要入库并让 `docs/README.md` / `README.md` 指向它，避免口径漂移。

Files:
- Add: `docs/protocol.yaml`
- Add: `docs/protocols/protocol_v1.yaml`
- (Optional) Update: `docs/README.md`（加一段“本项目以 protocol 为单一真相源”）
- (Optional) Update: `notes/decision-log.md`（记录 protocol v1 frozen）

验收：
- `git status` 显示 protocol 文件已入库（plan 本身不要求 push）
- 协议里 `dataset.root=data/selfcap_bar_8cam60f` 与当前目录一致

---

## Task A19: 固化 cue mining 的 canonical 输出路径（对齐 protocol v1）

当前问题：
- 已有的 `pseudo_masks.npz` 产物路径可能与 `docs/protocol.yaml` 的 `ours_weak.cue_mining.output_npz` 不一致，导致现场复现“找不到文件/跑到旧产物”。

目标：
- 让 protocol 的 `outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz` **真实存在且可复现生成**。

建议做法（二选一，优先 1）：
1. 直接用当前 `scripts/run_cue_mining.sh` 重新生成一次到 v1 目录（最干净、最可审计）。
2. 若时间非常紧：对已有的 `pseudo_masks.npz` 建立软链到 v1（但要在 notes 里写清“源自哪个 tag/命令”）。

Run（示例，方案 1）：
```bash
cd /root/projects/4d-recon
GPU=0 \
OUT_DIR=outputs/cue_mining/selfcap_bar_8cam60f_v1 \
bash scripts/run_cue_mining.sh data/selfcap_bar_8cam60f selfcap_bar_8cam60f_v1 0 60 diff 4
ls -la outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz
```

验收：
- `outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz` 存在
- `outputs/cue_mining/selfcap_bar_8cam60f_v1/viz/overlay_cam02_frame000000.jpg` 存在（便于汇报引用）

---

## Task A20: Weak Fusion 超参小 sweep（200-step 选候选）

目标：
- 在不改 trainer 代码的前提下，调 `PSEUDO_MASK_WEIGHT` 与 `PSEUDO_MASK_END_STEP`，让 weak 至少做到**不明显劣于 baseline**，并形成“为何这样选”的可解释记录。

固定条件（与 protocol v1 对齐）：
- 数据：`data/selfcap_bar_8cam60f`
- 帧段：`START_FRAME=0 END_FRAME=60`
- 相机 split：train `02-07`，val `08`，test `09`
- `GLOBAL_SCALE=6`，`KEYFRAME_STEP=5`，`SEED=42`

Sweep 建议（先跑 4 个组合，别贪多）：
- `PSEUDO_MASK_WEIGHT`: `0.1, 0.2, 0.3, 0.5`
- `PSEUDO_MASK_END_STEP`: `200`（先只早期施加，降低伤害）

Run（示例）：
```bash
cd /root/projects/4d-recon
for w in 0.1 0.2 0.3 0.5; do
  GPU=0 MAX_STEPS=200 \
  RESULT_DIR=outputs/gate1_selfcap_weak_sweep_w${w}_end200 \
  CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
  PSEUDO_MASK_WEIGHT=$w PSEUDO_MASK_END_STEP=200 \
  bash scripts/run_train_ours_weak_selfcap.sh
done
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

验收：
- 4 个 run 都产出 `videos/traj_4d_step199.mp4` 与 `stats/val_step0199.json`
- `outputs/report_pack/metrics.csv` 增加对应行（可被证据包捕捉）
- 新增记录：`notes/weak_tuning_selfcap_bar.md`（写明组合、指标、观察到的失败模式）

---

## Task A21: 选 1 个候选跑满 600-step（midterm 口径）

选择规则（建议）：
- 首选：`LPIPS` 不变差（或更好）
- 次选：`PSNR/SSIM` 不明显掉（容忍轻微波动）
- 若所有候选都更差：选“视觉更稳定/动态 smear 更少”的那个（把定性证据写进 failure_cases）

Run（示例）：
```bash
cd /root/projects/4d-recon
GPU=0 MAX_STEPS=600 \
RESULT_DIR=outputs/gate1_selfcap_ours_weak_tuned_600 \
CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_weak_selfcap.sh

python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/pack_evidence.py --out_tar outputs/midterm_evidence_2026-02-24-v4.tar.gz
```

验收：
- `outputs/gate1_selfcap_ours_weak_tuned_600/videos/traj_4d_step599.mp4` 存在
- `metrics.csv` 含 tuned 条目，并在 `ablation_notes.md` 解释 tuned 的选择原因

---

## Task A22 (Optional, Timebox 4h): 若 weak 全面劣化，提出“最小改代码”的补救开关

触发条件：
- 所有 `PSEUDO_MASK_WEIGHT` / `END_STEP` 组合都明显劣于 baseline，且差异可复现。

允许的最小改动（只选其一，避免引入大范围不稳定）：
1. 在 trainer 增加 `--pseudo-mask-mode {downweight_dynamic,upweight_dynamic}`（默认保持现状），验证一种替代模式是否更合理。
2. 不改 loss 形式，仅把弱融合限制到更短窗口（例如 `END_STEP=50/100`）并把理由写清楚（“只做 warm-start”）。

验收：
- baseline 不受影响（同命令输出一致、测试不回归）
- 至少 1 个替代设置在 200-step 不明显劣化，能进入 A21 的 600-step 复跑

