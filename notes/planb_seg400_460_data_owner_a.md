# Plan-B seg400_460 Data Slice (Owner A)

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg400`

## Generation command

- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/adapt_selfcap_release_to_freetime.py --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz --output_dir data/selfcap_bar_8cam60f_seg400_460 --camera_ids 02,03,04,05,06,07,08,09 --frame_start 400 --num_frames 60 --image_downscale 2 --seed 0 --overwrite`

## Script summary

- frame_range: `[400, 460)`
- image_size: `1055x1880` with downscale=`2`
- sparse_points3D: `7812`

## Data contract checks

- `test -d data/selfcap_bar_8cam60f_seg400_460/images`: PASS
- `test -d data/selfcap_bar_8cam60f_seg400_460/triangulation`: PASS
- `test -f data/selfcap_bar_8cam60f_seg400_460/sparse/0/cameras.bin`: PASS
- `ls data/selfcap_bar_8cam60f_seg400_460/triangulation/points3d_frame*.npy | wc -l`: `60`

## Conclusion

Data slice generated and validated; proceed to Gate-S1 init quality check.
