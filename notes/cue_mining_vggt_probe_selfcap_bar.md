# Cue Mining Probe: diff(v1) vs vggt(probe) on selfcap_bar_8cam60f

## 数值对比（frame 0-59, 8 cams, downscale=4）

| cue | mask_min | mask_max | mask_mean | temporal_flicker_l1_mean |
| --- | ---: | ---: | ---: | ---: |
| diff(v1) | 0.000000 | 0.780392 | 0.001199 | 0.000522 |
| vggt(probe) | 0.000000 | 0.976471 | 0.004220 | 0.002123 |

说明：
- `diff(v1)` 来自 `outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz` 的统计。
- `vggt(probe)` 来自 `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json` 与同目录 `pseudo_masks.npz` 的一致统计。
- `vggt(probe)` 质量检查：`all_black=false`，`all_white=false`。

## Overlay 路径

- diff(v1):
  - `outputs/cue_mining/selfcap_bar_8cam60f_v1/viz/overlay_cam02_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_v1/viz/grid_frame000000.jpg`
- vggt(probe):
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam02_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/grid_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam03_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam04_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam05_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam06_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam07_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam08_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam09_frame000000.jpg`

## protocol_v2 候选判断

- 判断：**YES**
- 理由：VGGT probe 掩码非退化且多机位可视化齐全，已满足进入 weak 训练对比验证的最小可行条件。
