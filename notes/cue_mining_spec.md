# Cue Mining Spec (MVP)

日期：2026-02-24  
适用阶段：训练前预处理（不 finetune）  
默认后端：`diff`（可运行兜底）

## 1. 目标与边界

- 目标：为 SelfCap/Gate-1 数据生成可复用的 `pseudo_mask`，供训练弱融合使用。
- 边界：本轮只定义并实现 `pseudo_masks.npz` + 最小可视化产物，不做 strong fusion。

## 2. 输入契约

数据目录约定（与现有 SelfCap 目录兼容）：

- `data/<dataset>/images/<cam_name>/<frame>.jpg`
- `<cam_name>` 例如 `02,03,...`
- `<frame>` 为零填充帧号（例如 `000000.jpg`）

运行参数最小集合：

- `--data_dir`: `data/<dataset>`
- `--frame_start`: 起始帧（含）
- `--num_frames`: 帧数 `T`
- `--mask_downscale`: 掩码下采样倍率（默认 `4`）
- `--out_dir`: `outputs/cue_mining/<tag>`

## 3. 输出契约

输出根目录：`outputs/cue_mining/<tag>/`

### 3.1 `pseudo_masks.npz`（必须）

必含 keys：

- `masks`：`uint8`，shape=`[T, V, Hm, Wm]`
  - `T=num_frames`
  - `V=len(camera_names)`
  - 值域允许 `{0,1}` 或 `{0,255}`（训练端统一按 `>0` 二值化）
- `camera_names`：`str[V]`，按相机文件夹名排序（`sorted(os.listdir(images_dir))`）
- `frame_start`：`int`，与生成时参数一致
- `num_frames`：`int`，且必须等于 `T`
- `mask_downscale`：`int`，例如 `4`

### 3.2 可视化目录 `viz/`（必须）

至少输出：

- `overlay_cam02_frame000000.jpg`
- `grid_frame000000.jpg`

命名固定，便于汇报脚本和文档直接引用。

### 3.3 质量诊断 `quality.json`（必须）

必含 keys（MVP）：

- `mask_mean_per_t`：`float[T]`，每帧掩码均值，值域 `[0,1]`
- `mask_mean_per_view`：`float[V]`，每视角掩码均值，值域 `[0,1]`
- `mask_min`：全局最小值（归一化后，`[0,1]`）
- `mask_max`：全局最大值（归一化后，`[0,1]`）
- `temporal_flicker_l1_mean`：`mean(|mask[t]-mask[t-1]|)`，值域 `[0,1]`
- `all_black`：`bool`，是否全黑（止损信号）
- `all_white`：`bool`，是否全白（止损信号）

说明：
- 统计默认以掩码归一化到 `[0,1]` 后计算，兼容 `{0,1}` 与 `{0,255}` 两种存储。
- 训练/汇报脚本可用 `all_black/all_white` 做自动 stoploss 判定。

## 4. 训练样本到 Mask 索引映射（验收关键）

训练侧样本字段（来自 `FreeTimeDataset.__getitem__`）：

- `frame_offset`: 相对训练起始帧偏移（`0..total_frames-1`）
- `frame_idx`: 绝对帧号（`start_frame + frame_offset`）
- `camera_idx`: 全局相机索引（对应 parser 排序后的相机顺序）

Cue mining NPZ 元信息：

- `cm_frame_start = pseudo_masks['frame_start']`
- `cm_num_frames = pseudo_masks['num_frames']`
- `camera_names = pseudo_masks['camera_names']`（排序后）

映射规则：

1. 时间索引：
   - `t = frame_idx - cm_frame_start`
   - 要求 `0 <= t < cm_num_frames`
2. 视角索引：
   - 训练侧使用 `camera_idx` 直接索引 `V` 维
   - 前提：训练数据 `images/` 相机目录与 `camera_names` 排序一致
3. 取掩码：
   - `mask_raw = masks[t, camera_idx]`
   - 二值化：`mask = (mask_raw > 0).float()`

尺寸对齐：

- 若训练图像尺寸为 `[H,W]`，掩码为 `[Hm,Wm]`，需上采样到 `[H,W]`（推荐 `nearest`）。

## 5. 健壮性约束

- 缺 key / shape 不合法：立即报错并中止训练弱融合。
- `camera_idx` 越界：报错并打印 `V` 与 `camera_idx`。
- `t` 越界：报错并打印 `frame_idx/cm_frame_start/cm_num_frames`。
- 默认关闭弱融合时（`pseudo_mask_weight=0` 或未传 NPZ）不得影响 baseline 行为。
