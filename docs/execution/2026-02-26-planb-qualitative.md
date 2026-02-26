# 2026-02-26 Plan-B Qualitative 产物流程（No-GPU）

目的：把 `baseline_600` 与 `planb_init_600` 的定性对比做成可复用命令，避免临场手工剪辑。

## 1) 生成 side-by-side 对比视频

默认输入：
- left: `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4`
- right: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/videos/traj_4d_step599.mp4`

命令：

```bash
cd /root/projects/4d-recon
bash scripts/make_side_by_side_video.sh --overwrite
```

默认输出：
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`

可选参数：
- `--left/--right`：自定义输入视频
- `--left_label/--right_label`：覆盖画面左上角标签
- `--out_dir/--out_name`：覆盖输出目录与文件名

## 2) 抽取关键帧（用于报告图）

默认抽帧索引：`0,30,59`

命令：

```bash
cd /root/projects/4d-recon
bash scripts/extract_video_frames.sh \
  --video outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline/frames \
  --frames 0,30,59 \
  --overwrite
```

输出：
- `outputs/qualitative/planb_vs_baseline/frames/frame_000000.jpg`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000030.jpg`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000059.jpg`

## 3) 常见错误

- `ffmpeg not found`：先安装 ffmpeg（Ubuntu 示例：`sudo apt-get install -y ffmpeg`）。
- `output exists`：加 `--overwrite` 覆盖已有输出。

## 4) 入库策略

- 不提交 `outputs/qualitative/` 下的视频与图片。
- 只提交脚本与文档，保证流程可复现。
