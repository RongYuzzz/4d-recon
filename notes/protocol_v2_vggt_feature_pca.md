# Protocol v2：VGGT token_proj feature（PCA->RGB）可视化

目的：补齐“feature 本体”的可解释材料（不仅是伪掩码 overlay）。

## 输入（真源，已落盘）

- cache：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
- meta：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/meta.json`

cache 摘要（来自 `meta.json`）：
- `phi_name=token_proj`, `phi_shape=(60,8,32,9,9)`, `phi_is_normalized=true`
- `input_size=(518,518)`, `phi_size=(9,9)`, `vggt_mode=crop`

## 输出（落盘在 cache 同目录，便于审计）

目录：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/viz_pca/`

- 单视角：`pca_rgb_cam02_frame000000.jpg`（以及 cam03..cam09；frame000015/000030/000045/000059）
- 网格：`grid_pca_frame000000.jpg`（以及 frame000015/000030/000045/000059）

生成脚本：`scripts/viz_vggt_cache_pca.py`

## PCA 拟合范围（确保同帧跨视角颜色一致）

- **按帧拟合**：对每个 frame t，取该帧的所有视角 token_proj（8 cams × 9×9 tokens）拼成矩阵 `(N=8*81, C=32)`。
- 对该矩阵做 PCA（SVD），取前三主成分作为 3D 表示，再映射到 RGB。
- 这样同一帧的 PCA 基底与归一化范围都来自“跨视角联合统计”，因此**同一帧跨视角颜色尽量一致**。

## 归一化 / 拉伸

- 对投影后的 3 个通道分别做 `p1~p99` 分位裁剪，再线性映射到 `[0,255]`（clamp）。
- 可视化分辨率：将 `9×9` token 网格用 nearest resize 到 `518×518`（对应 cache 的 `input_size`）。

## 失败例 / 边界（至少 1 条）

- **跨帧颜色不保证一致**：PCA 是按帧拟合的，分量/符号在不同帧可变化，因此不同帧的颜色不能当作“同一语义颜色恒定”。
- **纹理混簇**：PCA 仅保证解释方差最大，可能把“纹理/光照变化”当作主要方向；相似纹理区域会被映射到相近颜色，未必对应语义类别。

## 引用建议

- 开题/论文：优先引用 `grid_pca_frame000000.jpg` + `grid_pca_frame000030.jpg`（再补 1–2 张单视角图作为局部放大）。
