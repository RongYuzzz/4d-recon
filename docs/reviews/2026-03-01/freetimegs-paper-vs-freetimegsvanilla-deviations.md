# FreeTimeGS 论文 vs FreeTimeGsVanilla（社区实现）偏差清单（用于 baseline 合理性与复现风险评估）

用途：该清单用于回答两个“基础可信度”问题：

1. 我们的 baseline（`baseline_600`）到底是在对齐 FreeTimeGS 论文方法，还是在对齐 FreeTimeGsVanilla（社区实现）？
2. 如果存在实现偏差/潜在 bug，它会不会把“方法改进”变成“实现修 bug/调参带来的改进”？

范围（覆盖）：
- 表示 / 损失 / 优化 / relocation / 初始化与采样 / 时间单位 / 数据归一化 / 评估口径

分类规则（讨论时建议使用同一套术语）：
- 论文明确写了但实现不同：**硬偏差（Hard Deviation）**
- 论文没写但实现加了：**额外启发式（Extra Heuristic）**
- 实现内部不自洽：**实现偏差/潜在 bug（Implementation Bug/Drift）**

> 备注：本文件是“问题解决导向”的工作底稿，不要求一次性修完全部偏差；目标是识别最可能影响 baseline 合理性与收敛结论的 Top-K 偏差，并决定最小校准/修复动作。
>
> 用户提供的更详细逐条清单（按原文保留，用于逐项核验）：`docs/reviews/2026-03-01/freetimegs-paper-vs-freetimegsvanilla-deviations-user-provided.md`
>
> 同行补充的“三者对齐对象 + A/B/C 三层偏差清单”（含：论文 vs 上游、上游 vs fork、baseline vs 论文/上游）：`docs/reviews/2026-03-01/baseline-paper-vanilla-deviations-peer-provided.md`

---

## 快速结论（建议优先讨论的 Top 风险）

以下条目最可能影响“baseline 是否复现失败”和“短训练是否有说服力”：

- D1（硬偏差）：`lambda_4d_reg` 量级与论文不一致（论文常见写法 `1e-2`，而 preset 可能为 `1e-4`）。
- D2/D3（额外项 + 潜在 bug）：新增 duration regularization，且在 `init_duration=-1 (auto)` 时 target 语义可能错误，导致持续把 duration 往最小 clamp 推。
- B2（潜在 bug）：时间归一化与 frame_end 语义在 “NPZ 生成器 / dataset / trainer 读 metadata” 之间可能不一致（off-by-one 风险）。
- A1/A2（硬偏差）：ROMA->三角化初始化在社区实现中缺失；keyframe-only 锚点 + bridging 是社区实现主路线（与论文叙述不同）。

对应的“最小行动建议”：

1. baseline 校准 smoke sweep（不改代码）：只扫 `lambda_4d_reg`（`1e-4/1e-3/1e-2`），确认 baseline 是否显著改善并改变结论。
2. 关闭或修复 duration_reg（若确认 D3 属实），复跑 baseline_smoke200 + planb_smoke200 做稳健性验证。
3. 做一次 time normalization / frame_end 语义的端到端一致性自检（对齐 NPZ metadata 与 dataset time）。

---

## A. 初始化与输入数据（ROMA/三角化/速度）

- A1（高｜缺失｜硬偏差）ROMA→多视图三角化的初始化在社区实现里未实现，训练完全依赖外部生成的 per-frame 点云。
  - 论文：逐帧 ROMA 匹配并三角化得到 3D 点，用于初始化 `(mu_x, mu_t)`。
  - 实现：pipeline 入口要求 `points3d_frame*.npy/colors_frame*.npy`，只做合并与 KNN 速度（例如 `third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py`）。
  - 影响：初始化质量（outlier/稀疏/漂移）主要由外部流程决定，难保证论文同等条件。
- A2（高｜偏离论文叙述｜硬偏差）关键帧（keyframe-only）锚点 + “velocity bridging”是社区实现主路线，论文方法描述更接近“逐帧都有锚点”。
  - 论文：对每个视频帧都有对应三角化点并初始化。
  - 实现：默认强调 keyframe 采样/桥接（见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` 的 keyframe sampling 分支）。
  - 影响：时间锚点稀疏时更依赖线性速度与更宽 duration；非线性/遮挡/快运动更敏感。
- A3（中｜实现选择｜额外启发式）速度初始化的 KNN 匹配细节（阈值/无效速度处理）论文未写，但会显著影响效果。
  - 实现：存在 max_distance 阈值过滤；无匹配时 velocity=0 且点仍保留（需检查 `combine_frames_fast_keyframes.py` 的匹配与写出逻辑）。
  - 论文：只写 KNN translation 作为 velocity，未给阈值/丢弃策略。
  - 影响：大量 v=0 会更像论文消融 “w/o 4d initialization” 变体。
- A4（中｜偏差｜实现 drift）`has_velocity` 虽在 NPZ 里写出，但训练器可能不读取/不区分有效无效速度。
  - 影响：无效 velocity 的点仍进入优化，可能带来退化或掩盖初始化质量差异。

---

## B. 时间归一化与单位（t / mu_t / v）

- B1（高｜实现重参数化｜额外启发式）实现把时间归一化到 `[0,1]`，并把 velocity 从 `m/frame` 缩放到 `m/normalized_time`；论文未显式描述这层单位变换。
  - 影响：数学上可等价，但会改变速度 LR、阈值、cap 等超参含义。
- B2（高｜潜在 bug｜实现不自洽）NPZ 生成器与训练器对 `frame_end` 语义、`total_frames`、以及 time 归一化分母存在 off-by-one/不一致风险。
  - 风险：`mu_t` 与训练时刻 `t` 对不齐（末帧尤其明显），并且 frame_range/duration 的 rescale 逻辑可能出错或失真。
- B3（中｜实现选择｜额外启发式）实现对 velocity 做硬截断 `max_vel`，论文未提。
  - 影响：对快运动（论文主打场景）可能抹平/削弱。

---

## C. 表示与参数化（duration/opacity 等）

- C1（中｜额外启发式）temporal duration 在渲染时被 clamp（例如 `s >= 0.02`），论文未提。
  - 影响：防塌缩更稳，但改变 duration 学习边界/稀疏性。
- C2（中｜额外启发式）combined opacity 被强制下限（避免“黑点”），论文未提。
  - 影响：改变透明度分布与梯度传播。
- C3（低｜额外开关）实现允许关闭 motion（`use_velocity=False`），论文方法默认含 motion。

---

## D. 损失函数与正则（核心偏差区）

- D1（高｜硬偏差）4D regularization 权重与论文不一致，且默认 preset 更“远离论文”。
  - 论文：`lambda_reg ~ 1e-2`（常见写法）。
  - 实现：Config 默认与 preset 可能为 `1e-3` 或 `1e-4`（例如 `outputs/protocol_v1/.../cfg.yml` 中可见 `lambda_4d_reg=1e-4`）。
  - 影响：4D 正则是论文解决 fast-motion 局部最优的关键，权重差异会直接改变“抑制高 opacity/促进时域稀疏”的强度。
- D2（高｜额外项）实现新增 duration regularization（论文未提出该项）。
  - 影响：改变 duration 的学习目标与 temporal opacity 的宽度分布，属于方法层面改变。
- D3（高｜潜在 bug）duration regularization 的 target_duration 取自 `cfg.init_duration`；但 preset 里 `init_duration=-1.0`（auto 模式）时，这个 target 语义可能不成立。
  - 影响：额外正则可能变成强约束，把 duration 持续推向最小 clamp，导致行为显著偏离论文。
- D4（中｜实现细节差异）论文强调 “early stage penalize high opacity”，实现默认从 step 0 开始且没有 stop 机制（需要确认是否与论文一致）。
- D5（中｜实现细节差异）SSIM 的具体实现与 padding 细节论文未规定；可能导致 loss 数值尺度不同。
- D6（中｜实现选择）LPIPS 默认网络（alex/vgg）与 normalize 等细节论文未写；可能影响训练目标尺度。

---

## E. 优化与训练日程（速度退火/两阶段等）

- E1（高｜硬偏差）速度学习率退火公式与论文不一致（论文形式 vs 代码实现形式）。
- E2（中｜额外机制）实现引入“settling→refine”阶段：前若干步禁用 densification/relocation/pruning（论文未描述该阶段）。
- E3（中｜实现选择）SH degree 采用分段递增 schedule（论文未提）。
- E4（中｜实现假设）batch_size>1 时对 batch 内不同时间取 mean（默认 batch_size=1 时不触发，但属于潜在不自洽点）。

---

## F. Periodic relocation（实现细节与论文差异/未说明部分）

- F1（中｜实现差异）sampling score 中的梯度项来自“跨步累积的 position 梯度范数”并归一化；论文只给公式未说明累积/归一化细节。
- F2（中｜实现选择）relocation 的“搬运”是复制参数到 dead gaussian + 加噪声 + opacity 重置 + optimizer state 清零；论文未说明允许的操作集合。
- F3（中｜实现差异）dead 判定阈值与 relocation cap（`relocation_max_ratio`）属于实现选择，论文未提。
- F4（中｜额外机制）relocation 只在 refine 阶段执行并可被 stop_iter 截断；论文只说每 N iter。
- F5（中｜实现选择）操作顺序 “relocation→strategy→prune” 属于代码约定，论文未给。
- F6（低｜偏离）社区 preset 实际上几乎禁用 densify，转为“pure relocation”；论文与消融定义可能不同。

---

## G. 采样/预算/过滤（论文未提但会改变训练分布）

- G1（中｜额外机制）实现提供多种下采样策略（smart/stratified/keyframe），论文未描述。
- G2（低｜额外机制）初始化后按距离过滤点云（依赖 scene_scale），论文未提。

---

## H. 场景/相机归一化（论文未提）

- H1（中｜额外机制）实现对相机与点云做相似变换归一化 + PCA 主轴对齐；论文未说明。
  - 影响：改变空间尺度，进而影响 velocity cap、KNN 阈值、初始化尺度等。

---

## I. 评估/实验复现口径差异（论文实验 vs repo）

- I1（中｜缺失）论文报告 DSSIM（两种 data range）+ LPIPS；repo 未实现 DSSIM 指标/动态区域评估管线。
  - 影响：即使训练方法一致，指标口径也难直接对齐论文表格。

---

## J. 后处理/可视化（影响“看起来像不像”的主观感受）

- J1（低｜额外机制）viewer 侧的 temporal/base opacity 阈值裁剪 + 空间 percentile 裁剪，论文未提。
