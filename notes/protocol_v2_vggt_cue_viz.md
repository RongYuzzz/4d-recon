# Protocol v2：VGGT cue / 伪掩码（可解释证据包）

本 note 目的：答辩/写作时能直接回答“从 VGGT 挖到了什么、证据在哪、失败边界是什么”。

## 产物路径（可直接引用）

- 质量统计：`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json`
- 伪掩码（uint8，已落盘）：`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks.npz`
- 可视化：
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/grid_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam02_frame000000.jpg`
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/overlay_cam02_frame000030.jpg`
  - 其余视角同名模式：`overlay_cam*_frame*.jpg`

## cue 定义（是什么 / 不是什么）

- **是什么**：由 VGGT probe 管线产生的 **pseudo mask（伪掩码）**，用于在 2D 图像上提供“可能与动态/前景相关”的弱线索（weak cue）。
- **落盘格式**：`pseudo_masks.npz:masks` 形状 `(T=60, V=8, H=129, W=129)`，`dtype=uint8`，`mask_downscale=4`，`camera_names=['02'..'09']`。
- **不是什么**：不是人工标注 GT，也不保证是语义分割；更多是“可视化/可解释线索”，用于展示 VGGT 能提供的结构信息与失败边界。

## quality.json 关键数字（摘要）

- `mask_min=0.0`, `mask_max=0.9765`
- `temporal_flicker_l1_mean=0.00212`（帧间抖动的简单量化；越小越平滑）
- `all_black=false`, `all_white=false`（未退化为全黑/全白）
- `mask_mean_per_view`（8 视角均值，约 `0.0024~0.0079`；整体较稀疏）

## 失败例 / 边界（至少 1 条）

- 伪掩码整体偏稀疏：对**慢速运动**或**小幅形变**的目标可能漏检；同时在纹理/反光/强边缘区域可能出现“看起来像前景”的误触发。

## 引用建议

- 开题/论文：主图优先引用 `viz/grid_frame000000.jpg` + 1–2 张 `overlay_camXX_frameYYYYYY.jpg` 作为例子；质量数字引用 `quality.json`。
