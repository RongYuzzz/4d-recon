# Strong Fusion V2: Temporal Consistency Design + Audit Gate

日期：2026-02-24  
作者：Owner B  
范围：`selfcap_bar_8cam60f`，不破坏 `protocol_v1` 既有可复现性。

## A. v2 loss 定义（核心）

本轮使用 `pred_pred` 时序一致性约束：

`L_corr = mean_i [ w_i * | I_pred(t, src_xy_i) - I_pred(t', dst_xy_i) | ]`

- `i` 为对应点索引
- `w_i` 来自 KLT forward-backward 置信度
- 误差项默认 L1（后续可切 Charbonnier/Huber）

与历史 `pred_gt` 的区别：
- `pred_gt`: `pred_t` 对 `GT_{t'}`（受遮挡/曝光域偏差影响更大）
- `pred_pred`: `pred_t` 对 `pred_{t'}`（一致性目标更直接）

## B. 时间归一化（与数据口径对齐）

严格对齐 dataset 口径：
- `total_frames = end_frame - start_frame`
- `denom = max(total_frames - 1, 1)`
- `t = src_frame_offset / denom`
- `t' = dst_frame_offset / denom`

如果输入是全局帧号，则先转 offset：
- `src_frame_offset = src_frame - start_frame`
- `dst_frame_offset = dst_frame - start_frame`

## C. 采样策略（效率与稳健）

- 每 step 对应数上限：`TEMPORAL_CORR_MAX_PAIRS`
- 超上限时随机子采样（避免固定前缀偏置）
- strong 启用窗口：`step < TEMPORAL_CORR_END_STEP`

推荐默认（本轮）：
- smoke60: `max_pairs=200`, `end_step=60`
- sweep/full: `max_pairs=200`, `end_step=200`

## D. 对应置信度（KLT FB + weight）

KLT forward-backward：
- 前向：`p0 -> p1`
- 反向：`p1 -> p0_back`
- 误差：`fb_err = ||p0 - p0_back||_2`

过滤 + 权重：
- 保留条件：`fb_err < fb_err_thresh`
- 权重：`w = exp(-fb_err / sigma)`
- 裁剪：`w = clip(w, w_min, 1.0)`

默认建议：
- `fb_err_thresh=1.5`, `sigma=1.5`, `w_min=0.05`

## E. Stoploss 规则（任一触发即停）

1. step time 相比 v1/weak 明显翻倍，且在稳定窗口内无改善趋势。  
2. `corr_pairs==0` 或高频退化到极低值。  
3. 同预算下（200/600）指标与视觉都无改善，且 failure 机理可解释。  

## F. 审计所需最小证据

- run 命令（完整 env）
- `cfg.yml` 中 `temporal_corr_loss_mode=pred_pred`
- `run.log` 中 strong 加载/模式/`corr_pairs`/`corr_loss` 记录
- `outputs/report_pack/metrics.csv` 中 v2 val/test 条目
- temporal correspondence 可视化路径（`outputs/correspondences/.../viz/*`）
