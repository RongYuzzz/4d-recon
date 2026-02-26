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
