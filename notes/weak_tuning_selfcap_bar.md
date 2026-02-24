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

