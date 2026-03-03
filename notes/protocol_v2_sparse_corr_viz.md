# Protocol v2：稀疏对应（token/patch top-k）可视化（timebox deliverable）

目的：补齐“注意力/特征 → 对应 → 对比”的最小可解释闭环（偏可视化，不承诺立刻进训练主线）。

## 输入

- token_proj cache：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
  - `phi_shape=(60,8,32,9,9)`，每个 token 是 32-d 向量。

## 方法（最小闭环）

- **同一视角的时间对应**：对每个 camera，在 `t -> t+1` 间计算 token cosine similarity。
- 对每个 src token 取 best-match dst token（argmax），再做 greedy 去重，选出 `top-k` 作为可视化连线。
- 可视化画在 `9×9` token 网格上（左：t；右：t+1），连线颜色表示 cosine 相似度（红→黄→绿）。

## 输出

目录：`outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/`

一键复现命令（示例，生成与下述命名一致的可视化图）：

```bash
python3 scripts/viz_tokenproj_temporal_topk.py \
  --cache_npz outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
  --out_dir outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz \
  --camera_ids 02,05,09 \
  --frames 0,30 \
  --topk 20
```

已生成样例（top20）：
- `outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam02_frame000000_to_000001.jpg`
- `outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam02_frame000030_to_000031.jpg`
- `outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam05_frame000000_to_000001.jpg`
- `outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam05_frame000030_to_000031.jpg`
- `outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam09_frame000000_to_000001.jpg`
- `outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam09_frame000030_to_000031.jpg`

## 失败例 / 边界（至少 1 条）

- 该可视化是 **token 网格级别**，不是像素级光流；当视角内出现遮挡/快速运动/大形变时，best-match 往往会“跳格”或出现多对一的竞争（虽做了 greedy 去重，但仍会变稀疏/不稳定）。
- 这是 feature-space 的相似度，不等价于几何一致对应；更适合做“可解释示意”，不宜直接当作 GT correspondences。

## 下一步（若要进主线，需要换假设）

- 在 token 对应上加入几何/局部窗口约束、或使用跨视角约束（同一时刻多视角一致性），再考虑作为训练信号。
