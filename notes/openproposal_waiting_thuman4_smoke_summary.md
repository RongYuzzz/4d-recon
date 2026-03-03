# OpenProposal Waiting-THUman4 Smoke 摘要（可审计）

> 仅记录路径、配置与指标；不复制任何数据帧/GT mask 内容。

## 1) 已落地目录树（waiting-THUman）

- cue mining:
  - `outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_diff_q0.995_ds4_med3`
  - `outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_zeros_ds4`
  - `outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_vggt1b_depthdiff_q0.995_ds4_med3`
  - `outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_vggt1b_depthdiff_q0.995_ds4_med3_backup_before_strict_rerun_20260303T084305Z`
- runs:
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200`
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/weak_zeros_smoke200`
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/weak_invert_vggt_smoke200`
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/planb_feat_v2_smoke200`
- export:
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/export_static_planb_feat_v2_smoke200_tau0.01`
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/export_dynamic_planb_feat_v2_smoke200_tau0.01`
- qualitative_local:
  - `outputs/qualitative_local/openproposal_waiting_thuman4/static_vs_dynamic_planb_feat_v2_smoke200_tau0.01.mp4`

## 2) mask 锁定引用（弱监督 run 对齐）

- 见：`notes/openproposal_waiting_thuman4_smoke_mask_lock.md`
- 锁定文件：
  - `outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_vggt1b_depthdiff_q0.995_ds4_med3_backup_before_strict_rerun_20260303T084305Z/pseudo_masks_invert.npz`
- sha256:
  - `7f57a7def6521df11f4f198dd954a45872a815adcf1bafeedc41d21b81ec9449`

## 3) 关键 stats 路径与数值（test@step0199）

- `planb_init_smoke200`
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200/stats/test_step0199.json`
  - `psnr=12.941564559936523`, `lpips=0.5722535848617554`
- `weak_zeros_smoke200`
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/weak_zeros_smoke200/stats/test_step0199.json`
  - `psnr=12.935441970825195`, `lpips=0.5715867877006531`
- `weak_invert_vggt_smoke200`
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/weak_invert_vggt_smoke200/stats/test_step0199.json`
  - `psnr=12.93540096282959`, `lpips=0.5727353096008301`
- `planb_feat_v2_smoke200`
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/planb_feat_v2_smoke200/stats/test_step0199.json`
  - `psnr=12.90611743927002`, `lpips=0.573330283164978`
- masked fg（当前已记录）
  - `outputs/protocol_v3_openproposal/_waiting_thuman/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200/stats_masked/test_step0199.json`
  - `psnr_fg=47.6973505464518`, `lpips_fg=0.09026979971677065`

