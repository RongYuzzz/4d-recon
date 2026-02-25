# Ablation Notes (Midterm, 2026-02-25, Protocol v1)

当前文档用于中期汇报口径同步与 evidence 打包（`outputs/report_pack/`）。
维护说明：当前由 **Owner A / Owner B** 维护（Owner C 暂不可用）。

## Protocol
- Frozen protocol：`docs/protocol.yaml`（v1）
- 数据：`data/selfcap_bar_8cam60f`（8 cams x 60 frames）
- split：train `02-07` / val `08` / test `09`
- 预算：`MAX_STEPS=600`，统一比较 step=599

## Current Coverage (Protocol v1 / SelfCap bar 8cam60f)

1. Baseline
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600`
- test：PSNR 18.9496 / SSIM 0.6653 / LPIPS 0.4048 / tLPIPS 0.0230

2. Ours-Weak
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600`
- test：PSNR 19.0194 / SSIM 0.6661 / LPIPS 0.4037 / tLPIPS 0.0231

3. Control (Weak no-cue)
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600`
- test：PSNR 19.1099 / SSIM 0.6674 / LPIPS 0.4033 / tLPIPS 0.0236
- 结论：当前仍出现 `control_weak_nocue_600` 优于 `ours_weak_600` 的风险信号。

4. Ours-Strong v3（止损冻结）
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600`
- test：PSNR 18.9894 / SSIM 0.6648 / LPIPS 0.4060 / tLPIPS 0.0228
- 结论：tLPIPS 小幅下降但 LPIPS/PSNR 退化，未过成功线，按 stoploss 冻结。
- 参考：`notes/ours_strong_v3_gated_attempt.md`

5. Ours-Weak + VGGT cue probe（不升 protocol_v2）
- dir：`outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_600`
- cue：`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks.npz`
- test：PSNR 18.9808 / SSIM 0.6651 / LPIPS 0.4047 / tLPIPS 0.0245
- 结论：与 `ours_weak_600` / `control_weak_nocue_600` 相比无收益，不建议开启 `protocol_v2`。

6. Feature-loss v1（止损）
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600`
- 结论：在本协议和预算下未带来稳定正收益，按止损策略冻结。
- 参考：`notes/feature_loss_v1_attempt.md`

## Same-Budget Readout (test@step599, cam09)

| Method | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| ours_weak_600 | 19.0194 | 0.6661 | 0.4037 | 0.0231 |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| ours_strong_v3_gate1_detach0_predpred_600 | 18.9894 | 0.6648 | 0.4060 | 0.0228 |
| ours_weak_vggt_w0.3_end200_600 | 18.9808 | 0.6651 | 0.4047 | 0.0245 |

## Midterm Takeaways
- weak 主线：当前核心风险仍是 `control_weak_nocue_600` 优于 `ours_weak_600`。
- strong 主线：v3 已完成可审计尝试并触发止损冻结。
- VGGT cue：probe 可跑通且可视化正常，但未验证到可辩护收益，不升级 protocol。
