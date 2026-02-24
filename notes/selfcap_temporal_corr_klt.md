# SelfCap Temporal Correspondences (KLT)

日期：2026-02-24
工作树：`/root/projects/4d-recon/.worktrees/owner-b-20260224-strong-v2`

## 1) v1 基线（历史版本，保留不覆盖）

```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
mkdir -p outputs/correspondences/selfcap_bar_8cam60f_klt/viz
$PY scripts/extract_temporal_correspondences_klt.py \
  --data_dir data/selfcap_bar_8cam60f \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 0 \
  --num_frames 60 \
  --max_tracks_per_pair 500 \
  --out_npz outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz \
  --viz_dir outputs/correspondences/selfcap_bar_8cam60f_klt/viz
```

## 2) v2 FB 过滤版本（本轮新增）

```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
mkdir -p outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/viz
$PY scripts/extract_temporal_correspondences_klt.py \
  --data_dir data/selfcap_bar_8cam60f \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 0 \
  --num_frames 60 \
  --max_tracks_per_pair 500 \
  --min_track_len 1 \
  --fb_err_thresh 1.5 \
  --fb_weight_sigma 1.5 \
  --fb_weight_min 0.05 \
  --out_npz outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/temporal_corr.npz \
  --viz_dir outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/viz
```

## 3) 结果摘要（v2）

- 输出 NPZ：`outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/temporal_corr.npz`
- 文件大小：约 `2.2 MB`
- 总对应数 `N`：`236000`
- 相机：`02,03,04,05,06,07,08,09`
- `weight` 统计：
  - min: `0.99888`
  - max: `1.0`
  - mean: `0.99977`
  - 非全 1：`True`

## 4) 可视化证据（v2）

- 目录：`outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/viz`
- 当前输出 8 张 overlay（每相机 1 张）：
  - 例如：`outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/viz/frame000000_to_000001_cam02.jpg`
  - 例如：`outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/viz/frame000000_to_000001_cam09.jpg`

## 5) 备注

- 本版先做 cam 内 `t -> t+1` 对应（`min_track_len=1`）。
- v2 在 KLT 上增加 forward-backward 过滤与置信度权重映射，不改变 NPZ keys 契约。
- **未覆盖历史文件** `outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz`，确保旧 run 可审计复现。
