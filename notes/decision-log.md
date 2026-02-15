# Decision Log

## 2026-02-15

### Task 1 - 工作区初始化
- 已创建目录：`/root/projects/4d-recon/{third_party,data,outputs,notes,scripts}`。
- 已创建：`/root/projects/4d-recon/README.md`。

### Task 1 - 基底获取与版本固化
- 原计划 `git clone https://github.com/OpsiClear/FreeTimeGsVanilla.git` 受网络限制（`github.com` 连接超时）。
- 按预案切换为离线包方式：
  - 下载地址：`https://codeload.github.com/OpsiClear/FreeTimeGsVanilla/tar.gz/refs/heads/main`
  - 解压目录：`/root/projects/4d-recon/third_party/FreeTimeGsVanilla`
  - 压缩包 SHA256：`d5935738fe5db7ee27f50bf5dabf71a5b61ff37b29e9f946aa0047dd3e161e90`
- 通过 GitHub API 记录主分支快照提交（用于答辩可追溯）：
  - `main` commit: `911dcf4157a3ddf5c96d9147f97627480268fe0f`
  - commit date (UTC): `2026-01-23T18:53:31Z`

### Task 3 - T0 零速度检查改动（进行中）
- 已在训练配置中新增 T0 审计开关：
  - `force_zero_velocity_for_t0`
  - `t0_debug_interval`
  - `t0_grad_log_path`
- 已在 `run_pipeline.sh` 增加环境变量入口：
  - `FORCE_ZERO_VELOCITY_FOR_T0`
  - `T0_DEBUG_INTERVAL`
  - `T0_GRAD_LOG_PATH`
- 已增加训练期日志：
  - `t` 取值范围
  - `||v||` min/mean/max
  - `||Δx||` min/mean/max
  - `||grad_v||`、`||grad_duration||` 及 finite 标记

### 当前阻塞
- 真实数据（triangulation output + COLMAP）尚未放入 `data/`，暂无法产出 baseline vs `v=0` 视频。

### Task 2 - 环境进展（已达可运行）
- 已创建虚拟环境：`/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv`。
- 已完成依赖闭环并通过导入检查（含 `torch_scatter`、`fused_ssim`、`plas`、`gsplat`）。
- 包安装方式说明：
  - 常规包通过镜像源安装；
  - `fused-ssim`、`PLAS` 通过 `codeload.github.com` tarball + `--no-build-isolation`；
  - `torch-scatter` 通过本机 CUDA 编译。

### Task 3 - 数据兜底通路补齐（COLMAP sparse -> triangulation_input_dir）
- 新增脚本：`/root/projects/4d-recon/scripts/export_triangulation_from_colmap_sparse.py`
- 功能：从 `colmap_data_dir/sparse/0` 按 `image.name` 顺序导出
  - `points3d_frame%06d.npy`
  - `colors_frame%06d.npy`
- 用途：在无 ROMA/上游三角化产物时先跑通 T0 审计。
- 更新：`run_t0_zero_velocity.sh` 支持 `end_frame=-1` 自动推断（按 `points3d_frame*.npy` 最大编号 + 1）。
