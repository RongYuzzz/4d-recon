# Plan-B v26 Q&A 防守卡片（统一话术）

> 统一前置句：以下数字只引用 `docs/report_pack/2026-02-26-v26/` 四件套；新增训练预算为 `N=0`。

## Q1. 你们是不是 cherry-pick（挑帧/挑段/挑 seed）？
答：我们先给 canonical full600，再给 seg200_260 full600，最后补四个切片 smoke200，顺序固定，避免只挑有利片段。canonical 的 `planb_init_600` 相对 `baseline_600` 为 ΔPSNR +1.4992、ΔLPIPS -0.0551、ΔtLPIPS -0.0158；seg200_260 仍是同向（+1.9950/-0.0604/-0.0156）。smoke200 的 seg300/400/600/1800 也全部同向，不存在“某一个片段特例”。此外，seg400_460 与 seg1800_1860 已做 template hygiene 重跑，避免模板来源被质疑。

## Q2. 绝对 PSNR 还是不高，这个结果意义是什么？
答：我们这轮不声称高保真上限，研究范围写死为“600 steps 短预算下的收敛性与时序稳定性”。在这个 scope 下，Plan-B 同时提升 PSNR 并降低 LPIPS/tLPIPS，且在多切片上方向一致。会中表达方式是“先视频证据，再数字，再边界”，而不是拿短预算数字去对齐长训上限。这个 scope/limitation 在决议文件里已经写死，避免口径漂移。

## Q3. Plan-B 会不会只是速度投机（偶然吃到速度先验）？
答：我们的口径不是“速度越大越好”，而是“修正 velocity prior 的质量/尺度/一致性”。如果只是偶然投机，通常不会在 canonical、seg200_260 和四个 smoke200 切片上都保持同向改善。Gate-S1 与组件消融作为附录，用来说明该改动是系统性稳定收益，而不是单点异常。会中不把这个问题放主叙事，避免防守过载。

## Q4. Mutual NN 到底是什么定位，是否主要拉高 PSNR？
答：我们统一表述为“Mutual NN 是 stabilizer（稳定器）”，重点体现在时序稳定性与退化风险控制，不宣称它是主要 PSNR 来源。依据是 smoke200 消融里去掉 mutual 后三项指标同向变差，尤其 tLPIPS 变差最明显。主结论仍由 `planb_init_600` 相对 `baseline_600` 的整体收益来承载，而不是由某个组件单独背书。答辩时避免把 mutual 夸成“万能增益项”。

## Q5. 为什么冻结 feature-loss v2？为什么不测 Plan-B + Feature Loss？
答：`feature_loss_v2_postfix_600` 在 canonical 相对 baseline 是三项退化（PSNR 18.6752 vs 18.9496，LPIPS 0.4219 vs 0.4048，tLPIPS 0.0261 vs 0.0230），因此主线已冻结为负结果。Plan-B 与 Feature Loss 在方法上正交，但组合实验需要新增训练预算；当前决议明确新增 full600 `N=0`，所以写作阶段把它作为 limitation/future work。这个处理是预算纪律，不是回避问题。未来若要做组合，需先升级决议并写清成功线/止损线。

## Q6. 为什么 Plan-B + weak cue 判定 No-Go？
答：No-Go 原因是“证据不足且时序指标未同向”。在 canonical 里，`control_weak_nocue_600` 的 LPIPS（0.4033）优于 `ours_weak_600`（0.4037），说明 cue 注入路径存在负增益风险。Plan-B smoke200 对照中，`planb_ours_weak_smoke200_w0.3_end200` 虽有轻微 LPIPS 优势（0.5792 vs 0.5796），但 tLPIPS 变差（0.0338 vs 0.0335），不满足“同向改善”准入标准。在 `N=0` 冻结期下，这不足以申请新增 full600。

## 快速收口句（会末 10 秒）
- Plan-B only，feature-loss v2 No-Go，Plan-B+weak No-Go。
- 现阶段结论是“短预算可复现改进 + 可审计证据链”，不是高保真上限宣称。
- 若新增训练，必须先升级决议，不在本轮口径内。
