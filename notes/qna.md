# Q&A

## What is the data contract?

最小可用（能训练）：
- `data/<scene>/images/<cam>/*`（多相机图像；SelfCap canonical 产物已满足）
- `data/<scene>/sparse/0/{cameras.bin,images.bin,points3D.bin}`（COLMAP sparse）
- `data/<scene>/triangulation/points3d_frame*.npy` + `colors_frame*.npy`（每帧点云）

其中：
- `trainer` 需要 `images/ + sparse/0`（相机与投影）
- `combine_frames_fast_keyframes.py` 需要 `triangulation/`（初始化关键帧/速度）

## Why do we need an adapter?

因为公开数据集通常给的是“多视角视频/图片 + 相机参数（yml/json）”，不会按我们工程约定直接提供：
- `sparse/0/*.bin`（COLMAP 工程文件）
- `triangulation/*.npy`（每帧点云中间产物）

所以必须把“适配/生成中间产物”纳入正式入口，否则会一直卡在找数据样例上。

## What does T0 prove?

T0 是基底审计（Go/No-Go）：
- `force_zero_velocity` 能退化成静态（零速度测试）
- `velocities/durations` 的梯度存在且有限（非全 0 / 非 NaN）

结论：证明“时间参数化 + motion 参数 + 训练管线”是健康的，后续做更复杂的约束/融合才有意义。

