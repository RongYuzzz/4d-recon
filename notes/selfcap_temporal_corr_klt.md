# SelfCap Temporal Correspondences (KLT)

日期：2026-02-24
工作树：`/root/projects/4d-recon/.worktrees/owner-b-20260224-strongprep`

## 1) 可复现命令

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

## 2) 结果摘要

- 输出 NPZ：`outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz`
- 文件大小：约 `2.091 MB`
- 总对应数 `N`：`236000`
- 相机：`02,03,04,05,06,07,08,09`
- 每相机对应数：
  - 02: 29500
  - 03: 29500
  - 04: 29500
  - 05: 29500
  - 06: 29500
  - 07: 29500
  - 08: 29500
  - 09: 29500
- 每相机平均：`29500`

## 3) 可视化证据

- 目录：`outputs/correspondences/selfcap_bar_8cam60f_klt/viz`
- 当前输出 8 张 overlay（每相机 1 张）：
  - 例如：`outputs/correspondences/selfcap_bar_8cam60f_klt/viz/frame000000_to_000001_cam02.jpg`
  - 例如：`outputs/correspondences/selfcap_bar_8cam60f_klt/viz/frame000000_to_000001_cam09.jpg`

## 4) 备注

- 本版先做 cam 内 `t -> t+1` 对应（`min_track_len=1`）。
- 数据契约与 `notes/attention_loss_design.md` 保持一致，可后续替换为 VGGT attention 对应来源。
