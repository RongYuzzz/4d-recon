# Strong Fusion Prep: Temporal Correspondence Contract + Loss Design

日期：2026-02-24
作者：Owner B

## 1) Temporal Correspondence NPZ 契约（`temporal_corr.npz`）

本契约用于 strong-fusion 的时序监督输入，先约束 I/O，再替换对应来源。

必选 keys（最小集合）：

- `camera_names`: `str[V]`
  - 与 `data_dir/images/` 子目录一一对应，按字典序排序。
- `frame_start`: `int`
  - 源序列起始帧（对应 `images/<cam>/%06d.jpg`）。
- `num_frames`: `int`
  - 使用的帧数（覆盖 `[frame_start, frame_start + num_frames)`）。
- `image_width`, `image_height`: `int`
  - 像素尺寸，供后续归一化/采样边界检查。
- `src_cam_idx`: `int16[N]`
  - 源点所属相机下标，索引到 `camera_names`。
- `src_frame_offset`: `int16[N]`
  - 源点相对 `frame_start` 的帧偏移（0-based）。
- `dst_frame_offset`: `int16[N]`
  - 目标点相对 `frame_start` 的帧偏移；当前默认只做 `t -> t+1`。
- `src_xy`: `float32[N,2]`
  - 源像素坐标 `(x, y)`。
- `dst_xy`: `float32[N,2]`
  - 目标像素坐标 `(x', y')`。
- `weight`: `float32[N]`
  - 对应权重，当前默认 `1.0`；后续可注入置信度/遮挡过滤。

约束：

- `N` 为全局对应总数，所有 1D key 长度一致。
- `src_xy/dst_xy` 坐标必须在 `[0, width) x [0, height)`。
- 暂不引入跨相机对应；默认仅单相机时序对应（cam 内追踪）。

## 2) 对应来源策略

- 当前兜底实现：OpenCV KLT (`goodFeaturesToTrack + calcOpticalFlowPyrLK`)。
- 目标实现：VGGT attention/top-k 对应。

策略要求：

- 上游来源可替换，但 NPZ 契约不变。
- 下游训练只依赖契约 keys，不依赖来源细节。

## 3) Strong Fusion Loss 最小版本

先实现 flow-warp photometric 监督：

`L_corr = mean_i w_i * | I_pred(src, x_i) - I_gt(dst, x'_i) |`

说明：

- `x_i` 来自 `src_xy[i]`，`x'_i` 来自 `dst_xy[i]`。
- `w_i` 来自 `weight[i]`。
- 第一版只做 L1，后续可替换 Charbonnier/Huber。

默认关闭策略（必须）：

- `--lambda-corr` 默认 `0.0`（即关闭）。
- 仅当显式开启时生效。
- 只在前 `N` 步（建议 2k）启用，后期自动衰减或关闭，避免后期纹理劣化。

## 4) 验收口径

1. 训练稳定性：
- 无 NaN、无 OOM、训练可完整跑到目标 steps。

2. 动态性不退化：
- `velocity` 分布不退化到全 0（`nonzero count > 0`）。

3. 主观时序质量：
- 相比 baseline，flicker/断裂减少（即使指标提升不明显也可接受）。

## 5) 实施顺序建议

1. 先交付可复现 KLT 预计算脚本与可视化证据。
2. 再在 trainer 侧只接入读取与 loss gating（默认关闭）。
3. 最后做小规模 sweep，按统一 `metrics.csv` 汇总。
