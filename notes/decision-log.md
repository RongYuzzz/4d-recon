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

### Task 3 - T0 零速度检查改动（已完成，详见 2026-02-24）
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

### 当时阻塞（截至 2026-02-15）
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

## 2026-02-24

### SelfCap Gate-1 Canonical 定版
- 主入口定版为：`scripts/adapt_selfcap_release_to_freetime.py`。
- 推荐默认输入/输出：
  - 输入 tarball：`data/selfcap/bar-release.tar.gz`
  - 输出目录：`data/selfcap_bar_8cam60f`
- 默认参数固定为 8 机位 60 帧配置：`02,03,04,05,06,07,08,09` + `frame_start=0` + `num_frames=60` + `image_downscale=2`。
- `scripts/run_mvp_repro.sh` 统一为上述默认值；当 `data/selfcap_bar_8cam60f/triangulation` 不存在且 tar/script/venv 就绪时自动执行 adapter（`--dry-run` 仅打印命令）。
- `prepare_selfcap_for_freetime.py` 路线降级为 Legacy/Alternative，仅用于特定场景兼容。

### Docs/Artifacts 收敛（防丢）
- 执行总计划已收敛到仓库内：`docs/execution/2026-02-12-4d-reconstruction-execution.md`
  - 兼容：`/root/2026-02-12-4d-reconstruction-execution.md` 保留为指向仓库文件的 symlink
- 历史 evidence pack tarball 已从 worktree 复制到：`artifacts/report_packs/`（tarball 本体不进 git；校验和入库）
- 汇报材料文本快照（metrics/ablation/failure_cases）已提取到：`docs/report_pack/`

### Data - SelfCap 路线验证完成
- 已确认 HF 数据集 `zju3dv/SelfCap-Dataset` 的 `bar-release.tar.gz` 可用，本地缓存位于：
  - `data/raw/selfcap/bar-release.tar.gz`
- Canonical 入口路径（脚本默认）：
  - `data/selfcap/bar-release.tar.gz`（建议为上述缓存的 symlink）
- 已验证 `bar-release` 内部结构：
  - `videos/*.mp4`
  - `pcds/*.ply`（每帧 sparse 点云）
  - `dense_pcds/*.ply`
  - `optimized/{intri.yml, extri.yml}`

### Task 2/3 - 数据适配入口补齐（SelfCap -> FreeTimeGS）
- 新增脚本：`/root/projects/4d-recon/scripts/prepare_selfcap_for_freetime.py`
- 功能：
  - 从 `optimized/intri.yml + optimized/extri.yml` 生成 `colmap/sparse/0/*.bin`
  - 从 `pcds/*.ply` 生成 `triangulation/points3d_frame*.npy` 与 `colors_frame*.npy`
  - 可选从 `videos/*.mp4` 抽帧到 `colmap/images/<cam>/`（`--extract_images`）
- 新增测试：`/root/projects/4d-recon/scripts/tests/test_selfcap_adapter.py`
- 已通过测试：
  - `scripts/tests/test_export_triangulation_adapter.py`
  - `scripts/tests/test_selfcap_adapter.py`

### 当前数据状态（阻塞已解除）
- 已安装工具：
  - `ffmpeg`：`/usr/bin/ffmpeg`
  - `ffprobe`：`/usr/bin/ffprobe`
  - `colmap`：`/usr/bin/colmap`
- 已执行 SelfCap 适配与抽帧：
  - `python scripts/prepare_selfcap_for_freetime.py --selfcap_root data/raw/selfcap/extracted/bar-release --out_root data/scene_selfcap_bar_200_260 --frame_start 200 --frame_end 260 --extract_images`（legacy）
- 产物状态：
  - `triangulation/points3d_frame*.npy`：`60`
  - `triangulation/colors_frame*.npy`：`60`
  - `colmap/sparse/0/{cameras.bin,images.bin,points3D.bin}`：齐全
  - `colmap/images/<cam>/*`：`18` 路相机、`1080` 张图像

### Task 3 - T0 baseline vs zero-velocity 实跑完成
- 运行命令（使用绝对路径，避免 `run_t0_zero_velocity.sh` 内部 `cd` 后相对路径失效）：
  - `bash scripts/run_t0_zero_velocity.sh /root/projects/4d-recon/data/scene_selfcap_bar_200_260/triangulation /root/projects/4d-recon/data/scene_selfcap_bar_200_260/colmap /root/projects/4d-recon/outputs/t0_zero_velocity 0 -1 5 0 default_keyframe_small`
- Baseline 输出：
  - 指标：`PSNR=25.5860`，`SSIM=0.8369`，`LPIPS=0.1831`
  - 视频：`/root/projects/4d-recon/outputs/t0_zero_velocity/baseline/videos/traj_4d_step29999.mp4`
  - 梯度日志：`/root/projects/4d-recon/outputs/t0_zero_velocity/baseline/t0_grad.csv`
- Zero-velocity 输出：
  - 指标：`PSNR=25.9955`，`SSIM=0.8209`，`LPIPS=0.1803`
  - 视频：`/root/projects/4d-recon/outputs/t0_zero_velocity/zero_velocity/videos/traj_4d_step29999.mp4`
  - 梯度日志：`/root/projects/4d-recon/outputs/t0_zero_velocity/zero_velocity/t0_grad.csv`

### T0 结论
- 梯度检查通过：两组实验 `vel_grad_finite` 与 `duration_grad_finite` 均为全程 `1`，且 `vel/duration` 梯度非零计数均为 `30000/30000`。
- 先前“缺少 COLMAP 中间产物导致阻塞”的记录已过时，当前 T0 已进入可复现完成态。
- 下一步建议进入 T1（弱融合闭环）并固定一套可复现配置做后续消融。

### Task A (2026-02-24) - Cue Mining + Weak Fusion MVP
- 新增 `notes/cue_mining_spec.md`，冻结 `pseudo_masks.npz` 契约：
  - `masks[T,V,Hm,Wm]`、`camera_names`、`frame_start`、`num_frames`、`mask_downscale`
  - 明确训练样本 `frame_idx/camera_idx` 到 mask 索引映射规则。
- 新增 `scripts/cue_mining.py` + `scripts/run_cue_mining.sh` + `scripts/tests/test_cue_mining_contract.py`：
  - MVP 默认 `--backend diff`（帧差分）可运行；
  - `--backend vggt` 预留接口，缺依赖时给出明确报错与回退指引。
- 训练弱融合接入（默认关闭）：
  - 在 trainer 新增参数：`pseudo_mask_npz`、`pseudo_mask_weight`、`pseudo_mask_end_step`
  - 仅在 `weight>0` 且 `step<end_step` 时对 L1 启用 mask 加权，其余损失项保持不变。
- 新增静态回归测试：`scripts/tests/test_weak_fusion_flags.py`。
- 新增可复现实验入口：
  - `scripts/run_train_baseline_selfcap.sh`
  - `scripts/run_train_ours_weak_selfcap.sh`
  - 默认协议 full run：`GPU=0`、`MAX_STEPS=600`、`RENDER_TRAJ_PATH=fixed`（短跑 sanity 可用 `MAX_STEPS=200` 覆盖）。

## 2026-02-26

### 路线拍板：从 feature-loss v2 切换到 Plan‑B，并进入 Writing Mode
- 触发：canonical 下 `feature-loss v2` full600 三项全劣化，主线 No‑Go。
- 决议文件：`docs/decisions/2026-02-26-planb-pivot.md`
- 依据材料（早期版本）：
  - `docs/reviews/2026-02-26/meeting-opinions.md`
  - `docs/reviews/2026-02-26/meeting-decision.md`

### v26 会议收口：Plan‑B only + 冻结训练（新增 full600 预算 N=0）
- 目标：把“拍板”写成可执行纪律，避免口径漂移与证据链被打散。
- 决议文件（最新）：`docs/decisions/2026-02-26-planb-v26-freeze.md`
- 依据材料（v26 强化版）：
  - `docs/reviews/2026-02-26/meeting-opinions-v26.md`
  - `docs/reviews/2026-02-26/meeting-decisions-v26.md`
  - `docs/reviews/2026-02-26/meeting-pack-v26.md`
- 唯一数字口径：`docs/report_pack/2026-02-26-v26/{metrics.csv,scoreboard.md,planb_anticherrypick.md,manifest_sha256.csv}`
- 离线证据包：`artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz`（SHA 见 `artifacts/report_packs/SHA256SUMS.txt`）
