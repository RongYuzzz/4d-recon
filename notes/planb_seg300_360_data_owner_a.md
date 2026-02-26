# Plan-B seg300_360 Data Prep (Owner A)

- Date: 2026-02-26
- Slice: `frame_start=300`, `num_frames=60`
- Output dir: `/root/projects/4d-recon/data/selfcap_bar_8cam60f_seg300_360`

## Raw coverage check

- `tar -tzf /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz bar-release/pcds/000300.ply >/dev/null`: PASS
- `tar -tzf /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz bar-release/pcds/000359.ply >/dev/null`: PASS

## Adapter command

- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/adapt_selfcap_release_to_freetime.py --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz --output_dir /root/projects/4d-recon/data/selfcap_bar_8cam60f_seg300_360 --camera_ids 02,03,04,05,06,07,08,09 --frame_start 300 --num_frames 60 --image_downscale 2 --seed 0 --overwrite`

## Contract checks

- `data/selfcap_bar_8cam60f_seg300_360/images`: PASS
- `data/selfcap_bar_8cam60f_seg300_360/triangulation`: PASS
- `data/selfcap_bar_8cam60f_seg300_360/sparse/0/cameras.bin`: PASS
- `ls data/selfcap_bar_8cam60f_seg300_360/triangulation/points3d_frame*.npy | wc -l = 60`

## Conclusion

Data contract satisfied. Ready for baseline smoke200.
