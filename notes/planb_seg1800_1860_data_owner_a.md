# Plan-B seg1800_1860 Data Build（Owner A）

- 日期：2026-02-26
- 目标切片：`frame_start=1800, num_frames=60`
- fallback：不适用（本计划固定切片且不越界）

## 数据生成命令

```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg1800
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f_seg1800_1860 \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 1800 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
```

## 契约验收

- `data/selfcap_bar_8cam60f_seg1800_1860/images`：存在
- `data/selfcap_bar_8cam60f_seg1800_1860/triangulation`：存在
- `data/selfcap_bar_8cam60f_seg1800_1860/sparse/0/cameras.bin`：存在
- `points3d_frame*.npy` 数量：60

## 结论

- 数据切片验收：PASS
