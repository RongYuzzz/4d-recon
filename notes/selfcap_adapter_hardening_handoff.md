# SelfCap Adapter Hardening Handoff (Owner B -> Owner A)

日期：2026-02-24
分支：`owner-b-20260224-selfcap-hardening`

## 1) 新增/变更 CLI flags

`script`: `scripts/adapt_selfcap_release_to_freetime.py`

- `--overwrite`
  - 默认关闭。
  - 当 `output_dir` 非空时默认拒绝执行，避免污染已有产物。
  - 仅在显式 `--overwrite` 时清理已知子目录：`images/`、`sparse/`、`triangulation/`。

- `--no_images`
  - 跳过视频解码阶段，只导出 `triangulation + sparse/0`。
  - 适用于无视频文件或无解码环境的快速链路验证。
  - 仍会创建空的 `images/<cam>/` 目录，保持下游目录契约。

- `--image_width` / `--image_height`
  - 仅在 `--no_images` 模式下必填（>0）。
  - 用于写入 COLMAP `cameras.bin` 的图像尺寸。

## 2) 畸变支持（OPENCV 触发）

在 `write_colmap_sparse0()` 中：

- 读取 `dist_{cam}`（若存在）
- 当 `max(abs(dist[:4])) > 1e-12` 时：
  - camera model = `OPENCV`
  - params = `[fx, fy, cx, cy, k1, k2, p1, p2]`
- 否则保持：
  - camera model = `PINHOLE`
  - params = `[fx, fy, cx, cy]`

其中 `fx/fy/cx/cy` 一律按 `image_downscale` 同步缩放。

## 3) 新增测试文件与覆盖点

- `scripts/tests/test_selfcap_parsers.py`
  - `ensure_empty_or_overwrite`：
    - 非空目录 + `overwrite=False` 应报错
    - `overwrite=True` 应清理已知旧产物
  - `write_colmap_sparse0`：
    - `dist_*` 非零时写 `OPENCV`
    - 校验 params 长度与下采样后的内参

- `scripts/tests/test_selfcap_cli_no_images.py`
  - 构造最小 tar.gz（仅 `optimized/*.yml` + `pcds/*.ply`，无 `videos/`）
  - 验证 `--no_images --image_width --image_height` 可成功导出：
    - `triangulation/points3d_frame*.npy`
    - `sparse/0/cameras.bin`

## 4) 可选 sanity 结果（已跑）

- 输出：`outputs/gate1_selfcap_bar_8cam60f_hardened_sanity/stats/val_step0009.json`
- 说明：新增 flags 未破坏既有 Gate-1 基线路径。
