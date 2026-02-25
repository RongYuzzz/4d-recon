# Ours-Weak 调参与结论（SelfCap bar 8cam60f / Protocol v1）

本文记录在 `data/selfcap_bar_8cam60f` 上对 **Ours-Weak（cue mining + 弱融合）** 的调参过程与结论，目标是：
- 在同预算（`MAX_STEPS=600`）下，**不明显劣于 baseline**；
- 结论可复现、可审计（对应 `docs/protocol.yaml` / `docs/protocols/protocol_v1.yaml`）。

## 0. 协议与数据前提

- Frozen protocol：`docs/protocol.yaml`（v1，冻结日期 `2026-02-24`）
- 数据集根目录：`data/selfcap_bar_8cam60f`
- 相机划分：
  - train：`02,03,04,05,06,07`
  - val：`08`
  - test：`09`
- 帧段：`[0, 60)`，`KEYFRAME_STEP=5`，`GLOBAL_SCALE=6`，`SEED=42`
- 评测：同时产出 `val_step0599.json` 与 `test_step0599.json`；test 上开启 `tLPIPS`（要求 `eval_sample_every_test=1`）

## 1. Cue Mining 定版（VGGT 止损，使用 diff fallback）

### 1.1 结论
- `backend=vggt`：环境未安装，按 protocol 的 stoploss 规则止损。
- 使用 fallback：`backend=diff`，并固定 canonical 输出路径为：
  - `outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz`
  - `outputs/cue_mining/selfcap_bar_8cam60f_v1/viz/overlay_cam02_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_v1/viz/grid_frame000000.jpg`

### 1.2 复现命令
```bash
cd /root/projects/4d-recon
GPU=0 OUT_DIR=outputs/cue_mining/selfcap_bar_8cam60f_v1 \
bash scripts/run_cue_mining.sh data/selfcap_bar_8cam60f selfcap_bar_8cam60f_v1 0 60 diff 4
```

## 2. 200-step 小 sweep（快速筛选）

固定：
- `PSEUDO_MASK_END_STEP=200`（只在 early steps 施加弱融合，降低副作用）

扫描：
- `PSEUDO_MASK_WEIGHT ∈ {0.1, 0.2, 0.3, 0.5}`

产物：
- 每组均产出 `traj_4d_step199.mp4` + `val_step0199.json`（以及 test 若开启）
- 汇总会写入 `outputs/report_pack/metrics.csv`

## 3. 600-step 全量结果（Protocol v1 / test@step599, cam09）

下表为在同协议/同预算下的关键对比（`test_step0599.json`，cam09）：

| Run | 关键参数 | PSNR | SSIM | LPIPS | tLPIPS |
| --- | --- | --- | --- | --- | --- |
| baseline | - | 18.9926 | 0.6671 | 0.4064 | 0.0236 |
| ours-weak (w=0.5) | `PSEUDO_MASK_WEIGHT=0.5, END_STEP=200` | 19.0108 | 0.6669 | 0.4105 | 0.0231 |
| ours-weak (w=0.3) | `PSEUDO_MASK_WEIGHT=0.3, END_STEP=200` | 19.0119 | 0.6647 | 0.4060 | 0.0231 |

对应建议输出目录（示例命名，便于汇报对齐）：
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600`
- `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_tuned_600`（w=0.5）
- `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_tuned_w0.3_600`（w=0.3）

## 4. 最终推荐配置

推荐用于 midterm 的 weak 配置：
- `CUE_TAG=selfcap_bar_8cam60f_v1`
- `CUE_BACKEND=diff`
- `MASK_DOWNSCALE=4`
- `PSEUDO_MASK_WEIGHT=0.3`
- `PSEUDO_MASK_END_STEP=200`

理由：
- 相比 baseline：`PSNR` 与 `tLPIPS` 略优；`LPIPS` 不再劣化（略优）；`SSIM` 小幅下降但可接受。
- 只在 early steps 注入弱融合（`END_STEP=200`）更稳健，风险更低。

## 5. 复现命令（建议）

Baseline（protocol v1 目录建议）：
```bash
cd /root/projects/4d-recon
GPU=0 MAX_STEPS=600 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600 \
bash scripts/run_train_baseline_selfcap.sh
```

Ours-Weak tuned（w=0.3, end=200）：
```bash
cd /root/projects/4d-recon
GPU=0 MAX_STEPS=600 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_tuned_w0.3_end200_600 \
CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
PSEUDO_MASK_WEIGHT=0.3 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_weak_selfcap.sh
```

报表刷新与证据包：
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/pack_evidence.py --repo_root . --out_tar artifacts/report_packs/report_pack_2026-02-24-v4.tar.gz
```

## Weak Mask Sweep v2（2026-02-25, GPU1）

目标：在不改 `docs/protocol.yaml (protocol_v1)` 的前提下，仅调 `PSEUDO_MASK_WEIGHT / PSEUDO_MASK_END_STEP`，确认是否能稳定消除 `control_weak_nocue_600` 优于 weak 分支的风险信号；若不能则给出止损结论。

### 执行命令（审计）

200-step sweep：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep

for spec in \
  "0.1 200" \
  "0.3 60" \
  "0.3 200" \
  "0.3 600" \
  "1.0 200" \
  "1.0 600"; do
  w="$(echo "$spec" | awk '{print $1}')"
  end="$(echo "$spec" | awk '{print $2}')"
  GPU=1 MAX_STEPS=200 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
  RESULT_DIR=outputs/sweeps/weak_mask_v2/selfcap_bar_8cam60f/w${w}_end${end}_s200 \
  CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
  PSEUDO_MASK_WEIGHT="$w" PSEUDO_MASK_END_STEP="$end" \
  bash scripts/run_train_ours_weak_selfcap.sh
done
```

full600（最多 2 个）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep

GPU=1 MAX_STEPS=600 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_v2_w1.0_end600_600 \
CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
PSEUDO_MASK_WEIGHT=1.0 PSEUDO_MASK_END_STEP=600 \
bash scripts/run_train_ours_weak_selfcap.sh

GPU=1 MAX_STEPS=600 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_v2_w1.0_end200_600 \
CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
PSEUDO_MASK_WEIGHT=1.0 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_weak_selfcap.sh
```

### test 指标（PSNR/SSIM/LPIPS/tLPIPS）

#### 200-step 候选（test@199）

| RESULT_DIR | step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | --- | ---: | ---: | ---: | ---: |
| `outputs/sweeps/weak_mask_v2/selfcap_bar_8cam60f/w0.1_end200_s200` | 199 | 12.6366 | 0.3066 | 0.6297 | 0.0875 |
| `outputs/sweeps/weak_mask_v2/selfcap_bar_8cam60f/w0.3_end60_s200` | 199 | 12.6303 | 0.3065 | 0.6304 | 0.0881 |
| `outputs/sweeps/weak_mask_v2/selfcap_bar_8cam60f/w0.3_end200_s200` | 199 | 12.6303 | 0.3065 | 0.6300 | 0.0877 |
| `outputs/sweeps/weak_mask_v2/selfcap_bar_8cam60f/w0.3_end600_s200` | 199 | 12.6312 | 0.3064 | 0.6301 | 0.0873 |
| `outputs/sweeps/weak_mask_v2/selfcap_bar_8cam60f/w1.0_end200_s200` | 199 | 12.6368 | 0.3064 | 0.6297 | 0.0880 |
| `outputs/sweeps/weak_mask_v2/selfcap_bar_8cam60f/w1.0_end600_s200` | 199 | 12.6345 | 0.3066 | 0.6301 | 0.0871 |

#### full600 确认（test@599）

| RESULT_DIR | step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | --- | ---: | ---: | ---: | ---: |
| `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_v2_w1.0_end600_600` | 599 | 18.9757 | 0.6650 | 0.4064 | 0.0235 |
| `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_v2_w1.0_end200_600` | 599 | 19.0078 | 0.6661 | 0.4070 | 0.0238 |

#### 对照（test@599）

| RESULT_DIR | step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | --- | ---: | ---: | ---: | ---: |
| `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600` | 599 | 19.0194 | 0.6661 | 0.4037 | 0.0231 |
| `outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600` | 599 | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600` | 599 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |

### 结论（固定口径）

**STOPLOSS**：在 canonical 段（`selfcap_bar_8cam60f`）上，弱融合 v2（本轮 sweep 的 `w/end` 组合）未能稳定优于 `ours_weak_600`，也未消除 `control_weak_nocue_600` 更优的风险信号，进入止损结论并作为限制记录。

量级说明（vs `ours_weak_600`）：
- `ours_weak_v2_w1.0_end200_600`：`ΔPSNR=-0.0117`，`ΔSSIM=-0.0000`，`ΔLPIPS=+0.0033`，`ΔtLPIPS=+0.0007`。
- `ours_weak_v2_w1.0_end600_600`：`ΔPSNR=-0.0437`，`ΔSSIM=-0.0011`，`ΔLPIPS=+0.0027`，`ΔtLPIPS=+0.0004`。

解读：
- `PSNR/SSIM` 变化有一部分接近噪声量级，但 `LPIPS` 在两次 full600 都持续劣于 `ours_weak_600`（`+0.0027 ~ +0.0033`），不支持 ADOPT。
- 因此保持 `ours_weak_600 (w=0.3,end=200)` 作为当前 weak 参考，同时将 canonical 段“收益不可稳定复现”写入 failure cases；seg200-260 的正例可继续用于 anti-cherrypick 对照。
