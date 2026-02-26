# Ablation Notes (Plan-B + Writing Mode, 2026-02-26)

本文件为 2026-02-26 的写作收口版，随 `scripts/pack_evidence.py` 打包（`outputs/report_pack/`）。

## Protocol 与纪律

- Frozen protocol：`docs/protocol.yaml`（`protocol_v1`）
- 不改 `data/`，不新增 feature-loss full600
- Plan-B 口径：问题来源于 **velocity prior 质量/尺度/一致性不足或噪声过大**，而非“速度为 0 已被证实”

## 关键四行对比（test@step599）

| Slice | Run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | --- | ---: | ---: | ---: | ---: |
| canonical | `baseline_600` | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| canonical | `control_weak_nocue_600` | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| canonical (Plan-B) | `planb_init_600` | 20.4488 | 0.7070 | 0.3497 | 0.0072 |
| seg200_260 anti-cherrypick | `control_weak_nocue_600` | 18.1969 | 0.6369 | 0.4157 | 0.0222 |

> 参考：`outputs/report_pack/metrics.csv`、`outputs/report_pack/scoreboard.md`

## 读法与结论

1. Plan-B 初始化在 canonical 上形成明显优势（PSNR/SSIM 上升，LPIPS/tLPIPS 下降）。
2. seg200_260 子区间补充了独立切片证据，降低 cherry-pick 质疑。
3. 结论可辩护点：此次 pivot 属于“物理一致初始化修正”，不是通过改协议分布制造指标幻觉。

## 与 feature-loss 的关系（用于答辩）

- feature-loss 主线已冻结，不再增加 full600 预算。
- 失败归因转入 No-GPU 最小包：见 `notes/feature_loss_failure_attribution_minpack.md`。
- 叙事策略：将 negative result 归因为“方法边界/优化对抗 vs 工程实现”的可验证区分，而非模糊归因。
