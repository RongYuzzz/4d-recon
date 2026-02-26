# Owner A Plan (GPU0): Plan-B seg200_260 Anti-Cherrypick + Optional Second-Scene Smoke

日期：2026-02-26  
Owner：A  
GPU：仅 `GPU=0`（32GB）  
目标：在不改 `protocol_v1` 的前提下，为 **Plan‑B（3D velocity init）**补齐“反 cherry-pick”证据位，并输出可交接产物给 Writing Mode 打包/写作。

## 0. 约束（必须遵守）

- 不修改 `docs/protocols/protocol_v1.yaml` 与 `data/`（仅使用既有数据目录）。
- 不新增与 feature-loss 相关 full600（已冻结）。
- full600 预算：`N=3`（见 `docs/decisions/2026-02-26-planb-pivot.md`），当前剩余 **1 次**，仅在 Gate 通过后消耗。
- 产物不入库：`outputs/`、`data/`、`artifacts/report_packs/*.tar.gz` 均不 commit。
- 必须落地可审计记录到 `notes/`（命令、commit hash、指标、结论）。

## 1. 输入与目标产物

输入数据（已存在）：
- `data/selfcap_bar_8cam60f_seg200_260`（8 cams × 60 frames，`[200,260)`）

计划输出（必须产物）：
- Plan‑B init（seg2）：
  - `outputs/plan_b/selfcap_bar_8cam60f_seg200_260/init_points_planb_step5.npz`
  - `outputs/plan_b/selfcap_bar_8cam60f_seg200_260/velocity_stats.json`
- smoke200（seg2）：
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_smoke200/`
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_smoke200/`
- full600（seg2，条件执行）：
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_600/`

## 2. Gate 设计（避免把最后 1 次 full600 烧在明显无效配置上）

Gate‑S1（seg2 init 自检，No‑Go 任一触发即停）：
- `velocity_stats.json` 中 `counts.match_ratio_over_eligible < 0.05`
- 或 `clip_threshold_m_per_frame` 极端离谱（相对 canonical `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json` 高 10 倍以上，且 `n_clipped/n_valid_matches` 很高）

Gate‑S2（seg2 smoke200 对比，满足任一条即可继续）：
- `tLPIPS` 相对 seg2 baseline_smoke200 下降 ≥ 5%，且 PSNR 不劣化超过 0.2 dB
- 或 LPIPS 下降 ≥ 0.01 且训练稳定（无 NaN/发散）

若 Gate‑S2 FAIL：停止，不消耗最后 1 次 full600；只落盘失败归因（用于写作防守）。

## 3. 任务清单（按顺序执行）

### Task A51：预检与 provenance 记录（10 分钟）

产出：
- `notes/planb_seg2_preflight_owner_a.md`

检查：
```bash
cd /root/projects/4d-recon
git rev-parse HEAD
python3 scripts/tests/test_init_velocity_from_points_contract.py
test -d data/selfcap_bar_8cam60f_seg200_260/triangulation
```

### Task A52：生成 Plan‑B init（seg2）并做 Gate‑S1 判定（CPU+IO，<30 分钟）

```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f_seg200_260 \
  --baseline_init_npz outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg200_260
```

验收：
- 产物存在且 `velocity_stats.json` 含 `counts.match_ratio_over_eligible`、`clip_threshold_m_per_frame`、`n_clipped`。
- 按 Gate‑S1 写结论到 `notes/planb_seg2_gate_s1_owner_a.md`。

### Task A53：seg2 baseline_smoke200（GPU0，200 steps）

```bash
cd /root/projects/4d-recon
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 \
RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_smoke200 \
bash scripts/run_train_baseline_selfcap.sh
```

### Task A54：seg2 planb_init_smoke200（GPU0，200 steps）+ Gate‑S2 判定

```bash
cd /root/projects/4d-recon
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg200_260/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

验收与记录：
- 两个 smoke200 目录均存在 `stats/test_step0199.json`、`videos/traj_4d_step199.mp4`、`stats/throughput.json`。
- 在 `notes/planb_seg2_gate_s2_owner_a.md` 记录：
  - baseline_smoke200 vs planb_init_smoke200 的 PSNR/LPIPS/tLPIPS
  - Gate‑S2 的 PASS/FAIL 与理由

### Task A55（条件执行）：seg2 planb_init_600（GPU0，消耗最后 1 次 full600 预算）

前置条件：Gate‑S2 = PASS。

```bash
cd /root/projects/4d-recon
GPU=0 MAX_STEPS=600 \
DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg200_260/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_600 \
bash scripts/run_train_planb_init_selfcap.sh
```

验收：
- `stats/test_step0599.json`、`videos/traj_4d_step599.mp4` 存在。
- 在 `notes/anti_cherrypick_seg200_260.md` 新增小节：
  - `planb_init_600` vs seg2 `baseline_600` 的 PSNR/SSIM/LPIPS/tLPIPS 差值
  - 一句话结论（提升/持平/退化）与可能原因（若退化）

### Task A56：交接给 Owner B（Writing Mode）

产出：
- `notes/handoff_planb_seg2_owner_a.md`

内容包含：
- 以上输出目录列表（必须路径）
- full600 预算消耗状态（是否已用尽）
- 若 Gate‑S2 FAIL：给出“下一步不应再烧 full600”的建议与证据路径（两段 smoke200 + velocity_stats）

## 4. 可选加分（不阻塞主线）

若 Owner B 并行准备了第二场景数据目录 `data/selfcap_<scene>_8cam60f`（结构同 canonical），则补两条 smoke200（不烧 full600）：
- baseline_smoke200
- planb_init_smoke200

目的：给最终报告提供“非同段/非同场景”的定性补充，降低 cherry-pick 质疑。

