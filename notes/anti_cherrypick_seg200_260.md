# Anti-Cherrypick Record: SelfCap bar seg200_260

日期：2026-02-24  
目的：在同一场景不同帧段（`[200,260)`）复现 baseline vs ours-weak，验证主段结论是否可迁移。

## 1) Seg2 数据生成

命令：

```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-cuev2-seg2
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz /root/autodl-tmp/projects/4d-recon/data/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f_seg200_260 \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 200 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
```

数据路径：
- `data/selfcap_bar_8cam60f_seg200_260`

结构验收：
- `images/*/000000.jpg`：8 路相机均存在
- `triangulation/points3d_frame*.npy`：`60` 个
- `sparse/0/cameras.bin|images.bin|points3D.bin`：存在

## 2) Seg2 运行配置与路径

约束：不为 seg2 重调弱融合超参，沿用主段定稿参数。

- baseline run_dir  
  `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600`
- ours-weak run_dir  
  `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/ours_weak_600`

弱融合固定参数：
- `PSEUDO_MASK_WEIGHT=0.3`
- `PSEUDO_MASK_END_STEP=200`
- `CUE_TAG=selfcap_bar_8cam60f_seg200_260_v1`

## 3) 指标（test@step599）

baseline (`cam09`):
- PSNR: `18.0468`
- SSIM: `0.6353`
- LPIPS: `0.4138`
- tLPIPS: `0.02343`

ours-weak (`cam09`):
- PSNR: `18.2749`
- SSIM: `0.6398`
- LPIPS: `0.4127`
- tLPIPS: `0.02245`

差值（ours-weak - baseline）：
- ΔPSNR: `+0.2281`
- ΔSSIM: `+0.0045`
- ΔLPIPS: `-0.0011`（更好）
- ΔtLPIPS: `-0.0010`（更好）

补充（val@step599）：
- baseline: PSNR `17.6012`, SSIM `0.6055`, LPIPS `0.4294`
- ours-weak: PSNR `17.7674`, SSIM `0.6028`, LPIPS `0.4280`

## 4) 结论与失败模式

结论：
- 在 second segment（`seg200_260`）上，`ours-weak` 维持了 “not worse than baseline”，且 test 指标整体优于 baseline。
- anti-cherrypick 检查通过：主段结论在同场景不同帧段上未塌陷。

失败模式观察：
- 与主段相同，弱融合增益量级偏小（非数量级提升）；
- 未出现新型不稳定（NaN、明显训练发散、全黑/全白 cue）。
