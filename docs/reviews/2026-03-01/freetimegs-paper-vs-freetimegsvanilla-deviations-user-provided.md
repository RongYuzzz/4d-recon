# FreeTimeGS 论文 vs FreeTimeGsVanilla 偏差清单（用户原始整理，逐条保留）

说明：
- 本文件为讨论中用户提供的“论文方法 vs 社区实现”的详细偏差清单，**按原文尽量保留**，用于后续逐条核验与决定“哪些必须校准/修复、哪些作为 limitation/future work”。
- 路径前缀（例如 `projects/FreeTimeGsVanilla/...`、`tmp/freetimegs/...`）来自原始记录，未必与当前仓库路径完全一致；需要核验时请映射到本仓库的 `third_party/FreeTimeGsVanilla/...` 等实际路径。

---

另补充 FreeTimeGS 论文的方法和社区开源实现 FreeTimeGsVanilla（也就是本项目的基底）之间的详细偏差：

范围

- 覆盖：表示/损失/优化/relocation/初始化与采样/时间单位/数据归一化/评估口径
- 规则：论文明确写了但实现不同＝“硬偏差”；论文没写但实现加了＝“额外启发式”；实现内部不自洽＝“实现偏差/潜在 bug”

## A. 初始化与输入数据（ROMA/三角化/速度）

- A1（高｜缺失）ROMA→多视图三角化的初始化在仓库里未实现，训练完全依赖外部生成的 per-frame 点云。
  - 论文：逐帧 ROMA 匹配并三角化得到 3D 点，用于初始化 (µx, µt)（tmp/freetimegs/src/sec/3_method.tex:107）。
  - 实现：pipeline 入口要求 points3d_frame*.npy/colors_frame*.npy，只做合并与 KNN 速度（projects/FreeTimeGsVanilla/run_pipeline.sh:13、projects/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:471）。
  - 影响：初始化质量（outlier/稀疏/漂移）主要由外部流程决定，难保证论文同等条件。
- A2（高｜偏离论文叙述）关键帧（keyframe-only）锚点 + “velocity bridging”是社区实现的主路线，论文方法描述更接近“逐帧都有锚点”。
  - 论文：“For each video frame… triangulation… initialize position and time”（tmp/freetimegs/src/sec/3_method.tex:107）。
  - 实现：默认配置强调 keyframe 采样/桥接（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3206、projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3256）。
  - 影响：时间锚点稀疏时更依赖线性速度与更宽 duration；非线性/遮挡/快运动更敏感。
- A3（中｜实现选择）速度初始化的 KNN 匹配细节（阈值/无效速度处理）不在论文里，但会显著影响效果。
  - 实现：max_distance 阈值过滤；无匹配时 velocity=0，但这些点仍被保留（projects/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:492、projects/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:502）。
  - 论文：只说用 KNN translation 作为 velocity，未给阈值/丢弃策略（tmp/freetimegs/src/sec/3_method.tex:109）。
  - 影响：大量 v=0 会更像“w/o 4d initialization”变体（论文消融项）（tmp/freetimegs/src/sec/4_experiments.tex:79）。
- A4（中｜偏差）has_velocity 虽在 NPZ 里写出，但训练器完全不读取/不区分有效无效速度。
  - 证据：NPZ 写入 has_velocity（projects/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:615）；训练器源码无 has_velocity 读取（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:637）。

## B. 时间归一化与单位（t/µt/v）

- B1（高｜实现重参数化）实现把时间归一化到 [0,1]，并把 velocity 从 m/frame 缩放到 m/normalized_time；论文未提这层单位变换。
  - 论文：直接写 µx(t)=µx+v·(t-µt)（tmp/freetimegs/src/sec/3_method.tex:38）。
  - 实现：dataset time=frame_offset/(total_frames-1)（projects/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:633）；初始化读取后显式 velocities *= total_frames（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:742、keyframe 版 projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1304）。
  - 影响：数学上可等价，但会改变速度 LR、阈值、cap 等超参含义。
- B2（高｜潜在 bug/不自洽）NPZ 生成器与训练器对 frame_end 语义、total_frames、以及 time 归一化分母存在 off-by-one/不一致。
  - 生成器：total_frames = frame_end - frame_start + 1 且 t_normalized = (...) / total_frames（projects/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:424、projects/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:507）。
  - 训练 dataset：time = frame_offset / (total_frames - 1)（projects/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:633）。
  - 训练器读取元数据：npz_total_frames = npz_frame_end - npz_frame_start（把 frame_end 当“exclusive”）（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:669）。
  - 影响：µt 与训练时刻 t 对不齐（末帧尤其明显），并且 frame_range/duration 的 rescale 逻辑可能出错或失真。
- B3（中｜实现选择）实现对 velocity 做硬截断 max_vel=10.0，论文未提。
  - 证据：max_vel = 10.0（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1410）。
  - 影响：对快运动（论文主打场景）可能抹平/削弱。

## C. 表示与参数化（duration/opacity 等）

- C1（中｜额外启发式）temporal duration 在渲染时被 clamp：s >= 0.02，论文未提。
  - 证据：s = torch.clamp(s, min=0.02)（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1930）。
  - 影响：防塌缩更稳，但改变 duration 学习边界/稀疏性。
- C2（中｜额外启发式）combined opacity 被强制下限 1e-4（避免“黑点”），论文未提。
  - 证据：opacities = torch.clamp(opacities, min=1e-4)（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1995）。
  - 影响：改变透明度分布与梯度传播（尤其对“低 opacity 被迁移/被惩罚”的机制）。
- C3（低｜额外开关）实现允许关闭 motion（use_velocity=False），论文方法默认含 motion。
  - 证据：use_velocity: bool = True（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:449）。

## D. 损失函数与正则（核心偏差区）

- D1（高｜硬偏差）4D regularization 权重与论文不一致，且默认 preset 更“远离论文”。
  - 论文：λ_reg = 1e-2（tmp/freetimegs/src/sec/3_method.tex:122；也在消融里明确选择 1e-2（tmp/freetimegs/src/sec/4_experiments.tex:70））。
  - 实现：Config 默认 lambda_4d_reg=1e-3（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:395）；default_keyframe(_small) preset 用 1e-4（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3249、projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3293）。
  - 影响：4D 正则是论文解决 fast-motion 局部最优的关键，权重差异会直接改变“抑制高 opacity/促进时域稀疏”的强度。
- D2（高｜额外项）实现新增 duration regularization（论文未提出该项）。
  - 证据：lambda_duration_reg（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:399）与损失实现（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2371）。
  - 影响：会改变 duration 的学习目标与 temporal opacity 的宽度分布，属于方法层面改变。
- D3（高｜潜在 bug）duration regularization 的 target_duration 直接取 cfg.init_duration，但默认 preset 里 init_duration=-1.0（auto 模式），导致“永远被惩罚/推向最小值”的行为。
  - 证据：duration reg 目标 target_duration = cfg.init_duration（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2376）；preset 设置 init_duration=-1.0（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3227、projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3271）。
  - 影响：这会把“额外正则”变成一个强约束（逼 duration 收缩到 clamp 下限），与论文方法行为可能显著不同。
- D4（中｜可能偏差）论文强调“early stage penalize high opacity”，实现默认从 step 0 开始且没有 stop 机制。
  - 论文：early stage（tmp/freetimegs/src/sec/1_intro.tex:29）。
  - 实现：reg_4d_start_step = 0（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:413），无对应 reg_4d_stop_step。
  - 影响：若论文实际只在早期启用，长期启用会偏离。
- D5（中｜实现细节差异）SSIM 的具体实现使用 fused_ssim(..., padding="valid")；论文只说 SSIM loss，未规定实现细节。
  - 证据：ssim_val = fused_ssim(..., padding="valid")（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2357）。
  - 影响：loss 数值尺度/边界处理可能不同。
- D6（中｜实现选择）LPIPS 默认网络选 alex（且 normalize=True），论文未写具体 LPIPS 配置。
  - 证据：lpips_net: Literal["vgg","alex"] = "alex"（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:547）；net_type="alex", normalize=True（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1656）。
  - 影响：训练目标差异（尤其 perceptual loss 的尺度/偏好）。

## E. 优化与训练日程（速度退火/两阶段等）

- E1（高｜硬偏差）速度学习率退火公式与论文不一致。
  - 论文：λ_t = λ_0^{1-t} + λ_1^{t}（tmp/freetimegs/src/sec/3_method.tex:112）。
  - 实现：几何插值式指数退火 lr_start * (lr_end/lr_start)**progress（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2309）。
  - 影响：退火曲线形状不同会改变“早期快运动 vs 后期复杂运动”的拟合节奏。
- E2（中｜额外机制）实现引入“settling→refine”阶段：前若干步禁用 densification/relocation/pruning（论文未描述该阶段）。
  - 证据：densification_start_step（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:408）与 gating（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2421）。
  - 影响：会影响 primitive 分布演化与收敛速度。
- E3（中｜实现选择）SH degree 采用分段递增 schedule（论文未提）。
  - 证据：sh_degree_interval（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:361）、训练时 sh_degree = min(step // interval, ...)（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2320）。
- E4（中｜实现假设）batch_size>1 时把 batch 内不同时间直接取 mean，等价于“同一时刻渲染去拟合多时刻 GT”，与论文设定不匹配（虽然默认 batch_size=1）。
  - 证据：t = data["time"].to(device).mean().item()（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2299）。

## F. Periodic relocation（实现细节与论文差异/未说明部分）

- F1（中｜实现差异）sampling score 中的 ∇g 来自“跨步累积的 position 梯度范数”，并做了归一化；论文只给公式未说明“累积/归一化”。
  - 论文：s = λ_g ∇_g + λ_o σ（tmp/freetimegs/src/sec/3_method.tex:99）。
  - 实现：累积/平均/再除以 max 归一化（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2075），并在每步累计 grad（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2396）。
- F2（中｜实现选择）relocation 的“搬运”不是几何意义的移动，而是“从高分源 gaussian 复制参数到 dead gaussian + 加噪声 + opacity 重置 + optimizer state 清零”。
  - 证据：means 加噪（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2106）、opacity=0.8×source（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2112）、opt state reset（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2121）。
  - 影响：会改变 time/velocity/duration 的分布（因为也会被复制），论文未说明是否允许 “µt 被重采样”。
- F3（中｜实现差异）dead 判定使用 base opacity 阈值，且每次 relocation 有比例上限 relocation_max_ratio；论文只说“低 opacity 迁移”，未提 cap。
  - 证据：dead_mask（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2042）、cap（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2053）、参数（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:475）。
- F4（中｜额外机制）relocation 只在 step>=densification_start_step 的 refine 阶段执行，并可被 relocation_stop_iter 截断；论文只说“每 N=100 iter”。
  - 证据：gating（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2421）、stop 条件（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2425）、论文 relocation 频率描述（tmp/freetimegs/src/sec/3_method.tex:103、tmp/freetimegs/src/sec/3_method.tex:125）。
- F5（中｜实现选择）实现宣称的操作顺序 “relocation→strategy→prune” 是代码约定，论文未给出该顺序。
  - 证据：注释（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2414）。
- F6（低｜偏离）社区 preset 明确把 DefaultStrategy densification 几乎禁用（refine_start_iter 设很大），转为“pure relocation”；论文消融里把 “w/o relocation” 定义为“改用 3DGS densify”，暗示论文实现内部 densify/relocation 的组合方式可能不同于这里的 preset。
  - 证据：论文消融定义（tmp/freetimegs/src/sec/4_experiments.tex:73）；preset 禁用 densify（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3233）。

## G. 采样/预算/过滤（论文未提但会改变训练分布）

- G1（中｜额外机制）实现提供多种“下采样策略”（smart/stratified/keyframe），论文未描述任何采样/预算策略。
  - 证据：use_smart_sampling（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:302）、use_stratified_sampling（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:290）、use_keyframe_sampling（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:307）。
  - 影响：不同策略会明显改变哪些点被初始化成 gaussians（尤其动态区域覆盖）。
- G2（低｜额外机制）初始化后按距离过滤点云（max_dist=5*scene_scale），论文未提。
  - 证据：过滤逻辑（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1623）。

## H. 场景/相机归一化（论文未提）

- H1（中｜额外机制）实现对相机与点云做相似变换归一化 + PCA 主轴对齐；论文未说明这一坐标处理。
  - 证据：similarity_from_cameras 与 align_principle_axes（projects/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:381、projects/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:385）。
  - 影响：改变空间尺度（影响 velocity cap、KNN 阈值、初始化尺度等）。

## I. 评估/实验复现口径差异（论文实验 vs repo）

- I1（中｜缺失）论文报告 DSSIM（两种 data range）+ LPIPS；repo 不实现 DSSIM 指标/动态区域评估管线。
  - 论文指标：PSNR/DSSIM/LPIPS（tmp/freetimegs/src/sec/4_experiments.tex:20、tmp/freetimegs/src/sec/4_experiments.tex:23）；动态区域评估细节（tmp/freetimegs/src/sec/X_suppl.tex:44）。
  - 实现：无 DSSIM 相关代码（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2347 仅含 SSIM loss/log）；也无 matting/crop 评估脚本。
  - 影响：即使训练方法一致，指标口径也难直接对齐论文表格。

## J. 后处理/可视化（非论文方法核心，但会影响“看起来像不像”）

- J1（低｜额外机制）viewer 默认做 temporal/base opacity 阈值裁剪 + 空间 percentile 裁剪；论文未提这种推理时过滤。
  - 证据：temporal_opacity_threshold/base_opacity_threshold/spatial_filter_percentile（projects/FreeTimeGsVanilla/src/viewer_4d.py:35、projects/FreeTimeGsVanilla/src/viewer_4d.py:41）。

---

默认配置与论文“最关键的硬差异”汇总（便于你快速对齐）

- λ_reg：论文 1e-2（tmp/freetimegs/src/sec/3_method.tex:122） vs preset 1e-4（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3249）
- velocity LR 退火公式：论文（tmp/freetimegs/src/sec/3_method.tex:112） vs 实现（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2309）
- 新增 duration 正则 + 可能的 target_duration=-1 bug：实现（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:2376）+ preset（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3271）
- 时间归一化/元数据语义不一致：生成器（projects/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:424） vs dataset（projects/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:633） vs 训练器读 metadata（projects/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:669）
- 初始化关键路径 ROMA/三角化缺失：论文（tmp/freetimegs/src/sec/3_method.tex:107） vs repo（projects/FreeTimeGsVanilla/run_pipeline.sh:13）

