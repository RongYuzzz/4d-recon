# Feature-Loss v2 Post-Fix：Gate M2 记录（Owner A）

## 1) 候选选择（基于 M1 sweep）

候选：`lambda=0.01`（`ramp=400, layer=17, gating=none`）

选择理由（smoke200 Pareto）：
- 相比 `lam0.005`，`lam0.01` 在 `tLPIPS` 上更优（0.086305 vs 0.086826），且 `iter/s` 更高（15.29 vs 14.10）；
- 相比 `feature_loss_v2_smoke200_postfix` 默认 run，表现同量级，具备可审计目录名（显式 `lam0.01`）。

## 2) 执行命令（仅 1 次 full600 主判据）

```bash
GPU=0 MAX_STEPS=600 LAMBDA_VGGT_FEAT=0.01 \
  RESULT_TAG=feature_loss_v2_postfix_600 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh
```

## 3) 产物核验

已生成：
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/stats/test_step0599.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/stats/throughput.json`

## 4) full600 结果与快判

`feature_loss_v2_postfix_600`（test@599）：
- `PSNR=18.6752, LPIPS=0.421948, tLPIPS=0.026052`
- `iter_per_sec=15.3796`

对比 `baseline_600`（18.9496 / 0.404781 / 0.022959）：
- `ΔPSNR=-0.2744`
- `ΔLPIPS=+0.01717`
- `ΔtLPIPS=+0.00309`

对比 `control_weak_nocue_600`（19.1099 / 0.403327 / 0.023602）：
- `ΔPSNR=-0.4346`
- `ΔLPIPS=+0.01862`
- `ΔtLPIPS=+0.00245`

## 5) 是否允许第 2 次 full600（gated）？

计划规则：仅当无 gating full600 出现“可辩护正向趋势”时才允许继续 gated full600。

本次观察：
- 虽未触发“显著灾难退化”硬止损（未超过 `PSNR -1dB` 或 `tLPIPS +0.01`），
- 但相对 baseline/control 仍是 **PSNR/LPIPS/tLPIPS 全维劣化**，未出现正向趋势。

**决策：不执行第 2 次 gated full600（stop at 1 run）。**

## 6) M2 阶段结论

- Gate M2（选择性 1+1）在本轮只执行 1 条主判据 full600；
- 结论为 **No-Go（当前 post-fix v2 仍未形成优于 baseline/control 的可辩护趋势）**；
- 转入 Task 4：证据链刷新 + 结论收敛文档。
