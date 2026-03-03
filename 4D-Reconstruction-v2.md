[toc]

# 基于多视角RGB视频的高保真4D场景重建

## 选题背景与意义

随着元宇宙、数字孪生以及沉浸式媒体技术的飞速发展，如何从现实世界多视角二维视频中实现低成本、高保真地复原动态三维场景（即4D重建），已成为计算机视觉与图形学领域亟待攻克的关键难题。这一技术在影视特效制作、虚拟现实（VR）交互、自动驾驶仿真以及数字文物保护等下游领域拥有巨大的应用潜力。然而，现有的4D重建技术在处理包含复杂非刚性形变、多物体交互及快速运动的动态场景时，仍面临巨大挑战。

目前主流的高保真4D重建方法往往较为依赖外部先验，即依赖外部的预训练2D视觉基础模型（如图像分割模型SAM以及视频跟踪模型DEVA）来提供物体掩码或运动轨迹的监督信号。这种策略带来了两个较为显著的弊端：首先，系统架构庞大，计算冗余度高，难以满足高效部署的需求；更关键的是，2D视觉模型往往缺乏显式的三维空间几何结构感知能力，在面对场景中物体相互遮挡或大幅度运动时，极容易在时序上产生不一致，而这往往导致重建结果出现轨迹断裂、伪影以及闪烁现象，严重制约了4D场景的真实性与可编辑性。

针对上述痛点，本研究提出“阶段一物理运动先验 + 阶段二几何语义先验”的双阶段4D重建范式：阶段一沿用已验证的 Plan‑B 速度初始化作为物理底座，优先修复劣速/零速基底导致的收敛陷阱；阶段二在同一可微渲染框架内引入 VGGT 几何一致特征进行软约束优化。该范式**无需外部 2D 强监督前置（如 SAM/DEVA 掩码或 tracker 轨迹）**，VGGT 特征或伪掩码仅作为冻结软先验（soft prior）以 loss/weight 形式注入。理论层面，本研究面向“长程时空对应关系”难题，通过可实现的稀疏对应与特征度量损失提升遮挡与快速运动场景下的稳定对齐；应用层面，结合动静解耦渲染输出可编辑演示（object removal），提升复杂动态场景重建的鲁棒性与可解释性。

## 研究的主要内容与预期目标

### 本文主要贡献

1. 对比 FreeTimeGS：在其线性运动建模基础上补齐 Plan‑B 速度初始化，显式修复劣速/零速基底导致的收敛陷阱，在短预算设置下力争实现更好的 tLPIPS 与训练稳定性。
2. 对比 Split4D：避免重度逐帧对比学习管线，采用更轻量且可审计的 render-and-compare 特征度量约束，降低实现复杂度并保留可复现实验路径。
3. 对比 VGGT4D：不把大模型当作 2D mask 生成器，而是将 VGGT 几何一致特征作为 4DGS 优化中的软先验，通过 loss/weight 注入实现时空一致性增强。

本研究将围绕“如何在 Plan‑B 物理底座上引入可实现的几何语义约束，驱动高保真的4D实例重建”展开以下三方面研究：

1. 基于 VGGT 的潜在语义与动态线索提取。提取多视角视频的几何一致特征，并通过 PCA/聚类形成可视化线索与软伪掩码，为 feature metric 提供可解释先验。
2. 基于稀疏对应的时空一致性优化。采用 patch/token 级别的 top‑k 稀疏对应，构建可计算、可复现的时空关联约束，避免像素级全连接导致的复杂度爆炸。
3. 基于动静解耦机制的4D重建验证。基于 4D 高斯溅射管线输出 static-only / dynamic-only 渲染结果，并通过对象移除演示验证可编辑性。

预期目标：

1. 性能目标：在 SelfCap 数据上以 PSNR/SSIM/LPIPS 与 **tLPIPS（时序稳定）** 为主指标，对标 FreeTimeGS/Plan‑B 基线，力争在短预算与 full600 设置下取得显著改善。
2. 鲁棒性目标：在快速运动与遮挡场景中，显著减轻重影与闪烁，给出可审计的失败案例与边界说明，而非做不现实的全面优于承诺。
3. 系统目标：构建无需外部 2D 强监督前置的双阶段4DGS方案，并通过动静解耦与对象移除实验验证其时空解耦表征能力与可编辑性。

## 拟采用的研究方法、步骤

本研究拟构建一套“物理底座 + 语义先验”联合优化框架：以动静显式解耦的4DGS作为场景表示，以 Plan‑B 速度初始化提供稳定起点，以 VGGT 提供的几何一致特征与稀疏对应提供时空一致性约束。框架不依赖外部 2D 强监督前置，VGGT 输出仅作为软先验。具体研究方法如下：

1. 渲染框架构建：基于物理场解耦的混合渲染架构
   - 场景表示：以普遍认可的开源4DGS代码库为基础，引入基于线性运动假设的自由高斯基元（Free Gaussian Primitives），重构高斯基元的属性定义，利用其在4D空间中灵活初始化的特性，实现对动态场景的高效解耦。
   - 混合光栅化管线：扩展可微光栅化器接口，支持对动、静两组独立高斯进行统一排序与联合渲染。同时，开发额外的渲染通道，使其能导出实例分割图与深度图，从而构建可微监督通道，确保梯度能够从语义损失函数回传至高斯属性。
2. 特征挖掘：基于 VGGT 几何感知机制的软先验生成
   - 语义聚类与提取：利用 VGGT 处理多视角视频帧，提取特征张量并做 PCA/聚类，输出可解释的实例线索图。
   - 软先验注入：将 VGGT 特征或伪掩码作为冻结 soft prior 注入训练，不作为外部硬监督前置模块。
3. 模型融合：稀疏对应引导的时空一致优化
   - 高斯特征定义：为每个 Gaussian 增加可学习特征向量 \(f_i\)，通过 splatting 渲染形成2D特征图 \(F_{render}\)。
   - 像素/patch 与高斯绑定：通过 rasterizer 的 splatting 权重 \(w_i(p)\) 完成天然绑定，即 \(F_{render}(p)=\sum_i w_i(p)f_i\)。
   - 稀疏对应构建：在 patch/token 级别提取 VGGT 特征，采用 top‑k 匹配构建对应集合，仅在稀疏集合上施加一致性损失，避免 \(O((HW)^2)\) 的像素级全连接复杂度。
   - 损失函数设计：优先采用可复现的 feature metric（蒸馏式）作为主实现，并以稀疏 attention 对应作为加分项或后续扩展。

具体步骤如下：

1. 开源基线适配与线性解耦架构构建。部署普遍认可的开源4DGS框架，在此基础上开发自定义模块，实现线性运动模型驱动的动态高斯场构建。修改光栅化器，搭建实例分割图与深度图的辅助渲染通道，通过实验验证混合渲染管线在动静解耦与梯度回传方面的有效性。
2. VGGT特征构建模块开发。部署 VGGT 特征提取模块，输出多视角 PCA/聚类可视化及 soft prior 缓存，明确可用性与失败边界。
3. 稀疏一致性模块嵌入与调试。先接入 feature metric（warmup + ramp），再逐步尝试 patch/top‑k 稀疏对应，验证其对时序稳定性的贡献。
4. 定量测试与定性验证。在 SelfCap 数据上完成 smoke200 与 full600 的分级评测，记录 PSNR/SSIM/LPIPS/tLPIPS，并通过 static/dynamic 分层渲染验证可编辑性。

## 资源约束与止损策略

1. 预算口径：full600 的训练耗时、吞吐与资源占用以 `stats/throughput.json` 为准并落盘；smoke200 作为低成本趋势检查，不与 full600 数值混用。
2. 模块分级：
   - MVP 必做：Plan‑B 速度初始化 + SelfCap 主指标（含 tLPIPS）+ 动静解耦 demo。
   - 加分项：VGGT feature metric（warmup + ramp + 可审计超参）。
   - 高风险项：attention 对应/对比学习（仅限 patch/top‑k 稀疏版本并严格 timebox）。
3. 止损与回退：
   - 若 Plan‑B + feature metric 在 smoke200 或 full600 出现全线劣化，按止损线回退至 Plan‑B 保底配置并记录 failure analysis。
   - 阶段二（protocol_v2）失败不影响阶段一（v26 + protocol_v1）交付；两阶段证据链严格隔离，避免数值混用。

## 阶段二产物落盘与回填（protocol_v2）

### 动静解耦验证/可编辑性

- static-only 参考产物：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
- dynamic-only 参考产物：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`
- 以上路径用于支撑“动静分离 + 对象移除可编辑性”定性证据，后续可按阈值 \(\tau\) 扩展多组对照。
- τ 选择依据与失败例：`notes/velocity_stats_planb_init_600.md`、`notes/protocol_v2_static_dynamic_tau.md`

### VGGT 特征约束可落地性/资源约束

- VGGT cache：
  - `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
  - `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/meta.json`
- 可解释材料（答辩可直接引用）：
  - cue/伪掩码证据包：`notes/protocol_v2_vggt_cue_viz.md`（`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json` + `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/`）
  - token_proj PCA(3D)->RGB：`notes/protocol_v2_vggt_feature_pca.md`（`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/viz_pca/`）
  - 稀疏对应（token top‑k）：`notes/protocol_v2_sparse_corr_viz.md`（`outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/`）
- smoke200 统计：
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100/stats/test_step0199.json`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.01_warm100/stats/test_step0199.json`
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0_sanity/stats/test_step0199.json`（可比性检查）
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16/stats/test_step0199.json`（通过 smoke gate）
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100/stats/test_step0199.json`（未通过 smoke gate）
- full600 统计：
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_warm100_ramp400/stats/test_step0599.json`（触发止损）
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/stats/test_step0599.json`（未触发硬止损；PSNR 单点改善）
- 审计记录（含命令、对照与 gate/止损判定）：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`
- 当前口径：stage‑2 已出现“非全线劣化”的最小趋势，但仍未形成全指标稳定增益，后续以失败机理分析与可解释材料为主，不做夸大承诺。
- scoreboard 落盘：
  - v2 内部：`docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`、`docs/report_pack/2026-02-27-v2/scoreboard.md`
  - 跨协议对比：`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
- stage‑2 trade-off 定性证据（side-by-side）：
  - baseline vs planb：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
  - planb vs planb+feat：`outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_step599.mp4`
  - baseline vs planb+feat：`outputs/qualitative/planb_vs_baseline/baseline_vs_planbfeat_full600_step599.mp4`

### 阶段二结论收口（2026-02-27）

- 本轮阶段二已完成“可审计训练结果 + 可解释材料 + side-by-side 定性证据”三条证据链补齐。
- 当前观察到的趋势是混合型：`PSNR` 有单点改善，但 `LPIPS/tLPIPS` 未同步改善，尚不能宣称稳定收益。
- 预算闸门结论：C2(noconf) 新增 full600 预算未批准，故未执行该 full600；最终按 smoke200 趋势 + full600 trade-off 证据收口。
- 失败机理假设：feature loss 在细节纹理上提升重建锐度，但在跨帧一致性上引入额外漂移；后续优先做权重调度/区域选择的机理验证，而非盲目增加 full600 sweep。

## 研究的总体安排与进度

1. 第1周：文献调研与环境配置
2. 第2-3周：开源基线适配与线性解耦架构构建
3. 第4-6周：VGGT特征构建模块开发
4. 第7-9周：注意力引导机制嵌入与模型调试
5. 第10-11周：全量基准测试与消融实验
6. 第12周：解耦验证与编辑演示制作
7. 第13-14周：论文撰写与查重

## 参考文献

1. Jianyuan Wang, Minghao Chen, Nikita Karaev, Andrea Vedaldi, Christian Rupprecht, and David Novotny. 2025. VGGT: Visual Geometry Grounded Transformer. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 5294–5306.
2. Yu Hu, Chong Cheng, Sicheng Yu, Xiaoyang Guo, and Hao Wang. 2025. VGGT4D: Mining Motion Cues in Visual Geometry Transformers for 4D Scene Reconstruction. arXiv preprint arXiv:2511.19971 (2025).
3. Yongzhen Hu, Yihui Yang, Haotong Lin, Yifan Wang, Junting Dong, Yifu Deng, Xinyu Zhu, Fan Jia, Hujun Bao, Xiaowei Zhou, and Sida Peng. 2025. Split4D: Decomposed 4D Scene Reconstruction Without Video Segmentation. ACM Transactions on Graphics (TOG) 44, 6 (2025), 1–15.
4. Yifan Wang, Peishan Yang, Zhen Xu, Jiaming Sun, Zhanhua Zhang, Yong Chen, Hujun Bao, Sida Peng, and Xiaowei Zhou. 2025. FreeTimeGS: Free Gaussian Primitives at Anytime Anywhere for Dynamic Scene Reconstruction. In CVPR. https://zju3dv.github.io/freetimegs
5. Haiyang Ying, Yixuan Yin, Jinzhi Zhang, Fan Wang, Tao Yu, Ruqi Huang, and Lu Fang. 2024. OmniSeg3D: Omniversal 3D Segmentation via Hierarchical Contrastive Learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 20612–20622.
6. Shengxiang Ji, Guanjun Wu, Jiemin Fang, Jiazhong Cen, Taoran Yi, Wenyu Liu, Qi Tian, and Xinggang Wang. 2024. Segment Any 4D Gaussians. arXiv preprint arXiv:2407.04504 (2024).
7. Shuzhe Wang, Vincent Leroy, Yohann Cabon, Boris Chidlovskii, and Jerome Revaud. 2024. DUSt3R: Geometric 3D Vision Made Easy. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 20697–20709.
8. Maxime Oquab, Timothée Darcet, Théo Moutakanni, Huy Vo, Marc Szafraniec, Vasil Khalidov, Pierre Fernandez, Daniel Haziza, Francisco Massa, Alaaeldin El-Nouby, et al. 2023. DINOv2: Learning Robust Visual Features without Supervision. arXiv preprint arXiv:2304.07193 (2023).
9. Alexander Kirillov, Eric Mintun, Nikhila Ravi, Hanzi Mao, Chloe Rolland, Laura Gustafson, Tete Xiao, Spencer Whitehead, Alexander C Berg, Wan-Yen Lo, et al. 2023. Segment Anything. In Proceedings of the IEEE/CVF international conference on computer vision. 4015–4026.
10. Ho Kei Cheng, Seoung Wug Oh, Brian Price, Alexander Schwing, and Joon-Young Lee. 2023. Tracking Anything with Decoupled Video Segmentation. In Proceedings of the IEEE/CVF International Conference on Computer Vision. 1316–1326.
11. Albert Pumarola, Enric Corona, Gerard Pons-Moll, and Francesc Moreno-Noguer. 2021. D-NeRF: Neural Radiance Fields for Dynamic Scenes. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition. 10318–10327.
12. Guanjun Wu, Taoran Yi, Jiemin Fang, Lingxi Xie, Xiaopeng Zhang, Wei Wei, Wenyu Liu, Qi Tian, and Xinggang Wang. 2024. 4D Gaussian Splatting for Real-Time Dynamic Scene Rendering. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition. 20310–20320.
13. Jiazhong Cen, Jiemin Fang, Chen Yang, Lingxi Xie, Xiaopeng Zhang, Wei Shen, and Qi Tian. 2025. Segment Any 3D Gaussians. In Proceedings of the AAAI Conference on Artificial Intelligence. 1971–1979.
14. Ben Mildenhall, Pratul P Srinivasan, Matthew Tancik, Jonathan T Barron, Ravi Ramamoorthi, and Ren Ng. 2021. NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis. Commun. ACM 65, 1 (2021), 99–106.
15. Runsong Zhu, Shi Qiu, Zhengzhe Liu, Ka-Hei Hui, Qianyi Wu, Pheng-Ann Heng, and Chi-Wing Fu. 2025. Rethinking End-to-End 2D to 3D Scene Segmentation in Gaussian Splatting. arXiv preprint arXiv:2503.14029 (2025).
16. Zeyu Yang, Hongye Yang, Zijie Pan, and Li Zhang. 2023. Real-time Photorealistic Dynamic Scene Representation and Rendering with 4D Gaussian Splatting. arXiv preprint arXiv:2310.10642 (2023).
17. Zhiyang Guo, Wengang Zhou, Li Li, Min Wang, and Houqiang Li. 2024. Motionaware 3D Gaussian Splatting for Efficient Dynamic Scene Reconstruction. IEEE Transactions on Circuits and Systems for Video Technology (2024).
18. Bernhard Kerbl, Georgios Kopanas, Thomas Leimkühler, and George Drettakis. 2023. 3D Gaussian Splatting for Real-Time Radiance Field Rendering. ACM Trans. Graph. 42, 4 (2023), 139–1.
19. Zhicheng Lu, Xiang Guo, Le Hui, Tianrui Chen, Min Yang, Xiao Tang, Feng Zhu, and Yuchao Dai. 2024. 3D Geometry-aware Deformable Gaussian Splatting for Dynamic View Synthesis. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 8900–8910.
20. Keunhong Park, Utkarsh Sinha, Jonathan T Barron, Sofien Bouaziz, Dan B Goldman, Steven M Seitz, and Ricardo Martin-Brualla. 2021a. Nerfies: Deformable Neural Radiance Fields. In Proceedings of the IEEE/CVF international conference on computer vision. 5865–5874.
21. Keunhong Park, Utkarsh Sinha, Peter Hedman, Jonathan T Barron, Sofien Bouaziz, Dan B Goldman, Ricardo Martin-Brualla, and Steven M Seitz. 2021b. HyperNeRF: A Higher-Dimensional Representation for Topologically Varying Neural Radiance Fields. ACM Transactions on Graphics (TOG) 40, 6 (2021), 1–12.
22. Gal Fiebelman, Tamir Cohen, Ayellet Morgenstern, Peter Hedman, and Hadar AverbuchElor. 2025. 4-LEGS: 4D Language Embedded Gaussian Splatting. In Computer Graphics Forum. Wiley Online Library, e70085.
23. Isaac Labe, Noam Issachar, Itai Lang, and Sagie Benaim. 2024. DGD: Dynamic 3D Gaussians Distillation. In European Conference on Computer Vision. Springer, 361378.
24. Yun-Jin Li, Mariia Gladkova, Yan Xia, and Daniel Cremers. 2024b. SADG: Segment Any Dynamic Gaussian Without Object Trackers. arXiv preprint arXiv:2411.19290 (2024).
25. Lei Han, Tian Zheng, Lan Xu, and Lu Fang. 2020. OccuSeg: Occupancy-aware 3D Instance Segmentation. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition. 2940–2949.
26. Qingyong Hu, Bo Yang, Linhai Xie, Stefano Rosa, Yulan Guo, Zhihua Wang, Niki Trigoni, and Andrew Markham. 2020. RandLA-Net: Efficient Semantic Segmentation of LargeScale Point Clouds. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition. 11108–11117.
27. Wenhao Hu, Wenhao Chai, Shengyu Hao, Xiaotong Cui, Xuexiang Wen, Jenq-Neng Hwang, and Gaoang Wang. 2025. Pointmap Association and Piecewise-Plane Constraint for Consistent and Compact 3D Gaussian Segmentation Field. arXiv preprint arXiv:2502.16303 (2025).
28. 任皓, 李少波, 弓茂, 王博. 基于特征点引导干扰物识别的神经辐射场重建[J]. 图学学报, 1-8.
29. 吴佳昂, 刘渭滨, 邢薇薇. 基于结构化4DGS模型的单目动态场景重建[J]. 计算机辅助设计与图形学学报, 1-11.
