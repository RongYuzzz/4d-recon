# Strong Fusion: Temporal Correspondence Contract + V2 Loss Design

日期：2026-02-24  
作者：Owner B

## 1) Temporal Correspondence NPZ 契约（`temporal_corr.npz`）

本契约用于 strong fusion 的时序监督输入。对应来源可替换（KLT/VGGT），但训练侧只依赖该契约。

必选 keys（最小集合）：
- `camera_names`: `str[V]`
- `frame_start`: `int`
- `num_frames`: `int`
- `image_width`, `image_height`: `int`
- `src_cam_idx`: `int16[N]`
- `src_frame_offset`: `int16[N]`
- `dst_frame_offset`: `int16[N]`
- `src_xy`: `float32[N,2]`
- `dst_xy`: `float32[N,2]`
- `weight`: `float32[N]`

约束：
- 所有一维数组长度一致为 `N`。
- `src_xy/dst_xy` 坐标均在像素边界内。
- 当前默认仅 cam 内时序对应（不做跨相机对应）。
- `weight` 取值范围约束在 `[0, 1]`。

## 2) Strong Loss 模式定义（v1 对照 + v2 目标）

令 `i` 为对应索引，`rho` 为鲁棒函数（默认 L1，可切 Charbonnier/Huber）。

- v1（`pred_gt`，历史对照）  
  `L_corr_v1 = mean_i [ w_i * rho( I_pred(t, src_xy_i) - I_gt(t', dst_xy_i) ) ]`
- v2（`pred_pred`，本轮目标）  
  `L_corr_v2 = mean_i [ w_i * rho( I_pred(t, src_xy_i) - I_pred(t', dst_xy_i) ) ]`

其中 `pred_pred` 需要在 `t'` 额外做一次 rasterize。

## 3) 时间归一化口径（必须与 dataset 对齐）

与 `FreeTime_dataset.py` 保持同口径：
- `total_frames = end_frame - start_frame`
- `denom = max(total_frames - 1, 1)`
- `t = src_frame_offset / denom`
- `t' = dst_frame_offset / denom`

若使用全局帧号，则先转 offset：  
`frame_offset = frame_id - start_frame`。

## 4) 采样策略（每 step 对应上限 + 随机子采样）

目标是降低 step-time 波动并避免固定前缀偏置：
- 每 step 使用 `TEMPORAL_CORR_MAX_PAIRS` 上限。
- 当候选数大于上限时做随机子采样（每 step 重采样）。
- 结合 `TEMPORAL_CORR_END_STEP` timebox，仅在前期启用 strong。

建议：
- smoke: `max_pairs=200`, `end_step=60`
- sweep/full: `max_pairs=200`, `end_step=200`

## 5) KLT 置信度权重（forward-backward）

对每个 track 点计算前后向误差：
- `fb_err = || p0 - p0_back ||_2`

过滤与权重：
- keep 条件：`fb_err < fb_err_thresh`
- 建议权重：`w = exp(-fb_err / sigma)`，再 clip 到 `[w_min, 1.0]`

推荐默认：
- `fb_err_thresh = 1.5`
- `sigma = 1.5`
- `w_min = 0.05`

## 6) Stoploss 口径（任一触发即停）

- step time 相对 weak/baseline 明显翻倍，且在 50~100 step 窗口无回落趋势。
- `corr_pairs == 0` 或频繁退化到极低值。
- 在同预算（200/600 step）下，指标与视觉均无改善，且 failure 机理可解释。

## 7) 默认安全策略

- `lambda_corr=0` 时 strong 完全不生效，不影响 baseline/weak 可复现性。
- 默认模式保留 `pred_gt`，仅显式设置 `temporal_corr_loss_mode=pred_pred` 才启用 v2。
