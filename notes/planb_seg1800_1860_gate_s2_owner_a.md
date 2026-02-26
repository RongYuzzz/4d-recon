# Plan-B seg1800_1860 Gate-S2（Owner A）

- 日期：2026-02-26
- 切片：`data/selfcap_bar_8cam60f_seg1800_1860`
- 对比：`baseline_smoke200` vs `planb_init_smoke200`

## 执行命令

```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg1800
GPU=0 MAX_STEPS=200 DATA_DIR=data/selfcap_bar_8cam60f_seg1800_1860 RESULT_DIR=outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200 bash scripts/run_train_baseline_selfcap.sh

GPU=0 MAX_STEPS=200 DATA_DIR=data/selfcap_bar_8cam60f_seg1800_1860 PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/init_points_planb_step5.npz RESULT_DIR=outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200 bash scripts/run_train_planb_init_selfcap.sh
```

## Artifact 检查

- baseline `stats/test_step0199.json`: PASS
- baseline `stats/throughput.json`: PASS
- baseline `videos/traj_4d_step199.mp4`: PASS
- planb `stats/test_step0199.json`: PASS
- planb `stats/throughput.json`: PASS
- planb `videos/traj_4d_step199.mp4`: PASS

## 指标（test@199）

| run | PSNR | LPIPS | tLPIPS |
|---|---:|---:|---:|
| baseline_smoke200 | 12.5796 | 0.6290 | 0.08884 |
| planb_init_smoke200 | 12.7081 | 0.5845 | 0.03557 |

## 差值（planb - baseline）

- ΔPSNR: +0.1285
- ΔLPIPS: -0.0445
- ΔtLPIPS: -0.05327
- tLPIPS 相对下降比例: 59.96%

## Gate-S2 判定

- 条件1（tLPIPS 下降 ≥5% 且 PSNR 不劣化 >0.2dB）：PASS
- 条件2（LPIPS 下降 ≥0.01 且训练稳定）：PASS
- **总体：PASS**

## 结论

- 纳入 anti-cherrypick 防守位（seg1800_1860 同向支持 Plan-B）

## Update (re-template baseline init, 2026-02-26)

- baseline template: `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/_baseline_init/keyframes_60frames_step5.npz`
- Gate-S1 key fields:
  - `match_ratio_over_eligible = 0.5791285625`
  - `clip_threshold_m_per_frame = 0.0116234971`
  - `n_clipped = 490`
- smoke200 (test@step199) baseline vs re-template planb:
  - baseline: `PSNR 12.5796127319 / LPIPS 0.6289873719 / tLPIPS 0.0888407901`
  - planb: `PSNR 12.7594900131 / LPIPS 0.5800951719 / tLPIPS 0.0339605361`
  - deltas (planb - baseline): `ΔPSNR +0.1798772812 / ΔLPIPS -0.0488922000 / ΔtLPIPS -0.0548802540`
- 判定：**PASS**（Gate-S1 与 Gate-S2 均通过）
- 一句话结论：re-template 后 seg1800_1860 仍保持同向收益，可继续作为 anti-cherrypick 防守证据。

