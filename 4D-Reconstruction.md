[toc]

# 基于多视角RGB视频的高保真4D场景重建

## 选题背景与意义

随着元宇宙、数字孪生以及沉浸式媒体技术的飞速发展，如何从现实世界多视角二维视频中实现低成本、高保真地复原动态三维场景（即4D重建），已成为计算机视觉与图形学领域亟待攻克的关键难题。这一技术在影视特效制作、虚拟现实（VR）交互、自动驾驶仿真以及数字文物保护等下游领域拥有巨大的应用潜力。然而，现有的4D重建技术在处理包含复杂非刚性形变、多物体交互及快速运动的动态场景时，仍面临巨大挑战。

目前主流的高保真4D重建方法往往较为依赖外部先验，即依赖外部的预训练2D视觉基础模型（如图像分割模型SAM以及视频跟踪模型DEVA）来提供物体掩码或运动轨迹的监督信号。这种策略带来了两个较为显著的弊端：首先，系统架构庞大，计算冗余度高，难以满足高效部署的需求；更关键的是，2D视觉模型往往缺乏显式的三维空间几何结构感知能力，在面对场景中物体相互遮挡或大幅度运动时，极容易在时序上产生不一致，而这往往导致重建结果出现轨迹断裂、伪影以及闪烁现象，严重制约了4D场景的真实性与可编辑性。

针对上述痛点，本研究旨在探索一种基于3D几何感知语义引导的端到端4D重建范式：在同一可微渲染框架内，直接利用3D视觉几何Transformer（以VGGT为代表）提供的跨视角几何一致特征以及全局关联信息，不依赖任何外部2D分割或跟踪器作为前置模块，在框架内部通过几何一致性与注意力引导的软对应关系产生并利用中间监督信号，以实现实例级语义线索挖掘、长程时空对应约束构建以及动静解耦的4D高斯重建。理论层面，本研究面向“长程时空对应关系”这一核心难题，将几何一致性与全局关联约束融入到4DGS的优化过程，为复杂遮挡与大幅度运动提供更稳定的时空对齐；应用层面，本研究构建输入仅为多视角RGB视频、无需繁琐预处理的高保真4D实例重建框架，提升复杂动态场景下的鲁棒性与可编辑性，降低高质量动态3D内容生成门槛。

## 研究的主要内容与预期目标

本研究将围绕“如何利用3D视觉几何Transformer的内蕴特征来驱动高保真的4D实例重建”这一核心问题，展开以下三个方面的研究：

1. 基于3D视觉几何Transformer的潜在实例语义与动态线索提取。深入探究预训练3D视觉几何Transformer——VGGT内部的多层注意力机制，研究如何在无需引入2D分割模型，无需后训练，直接从模型中间层提取潜在的实例级语义特征与动态运动线索。重点分析不同层级中语义信息与运动方差的分布规律，设计非监督特征聚类算法，从多视角RGB视频输入中挖掘出保持几何一致性的实例级伪掩码，为后续4D重建过程提供几何鲁棒的初始化信息。
2. 基于全局注意力引导的端到端时空关联优化策略研究。针对现有方法在处理大幅度运动与长时遮挡时出现的追踪丢失问题，研究利用VGGT的全局帧间注意力构建长程时空约束。设计一种新型的“注意力引导的对比损失”，将跨帧对应关系融入4D渲染场的优化过程，约束特征场在时间维度上保持时空一致性。
3. 基于动静解耦机制的4D重建框架构建与验证。基于4D高斯溅射底层架构，复现并构建支持“动静显式分离”的渲染管线。借鉴FreeTimeGS的线性运动建模思想，重构动态场景的表征逻辑。将提取的几何语义线索与时空关联机制与该渲染管线进行深度融合，实现无需外部视频分割或跟踪器辅助的端到端4D场景重建，并通过参数化操控的方式，验证重建结果在场景解耦与编辑（如物体移除）方面的有效性。

预期目标：

1. 性能目标：在公开的动态场景数据集如Neural3DV以及Multi-Human上，重建质量指标如PSNR与SSIM，分割精度如mIoU优于依赖外部先验的方法。
2. 鲁棒性目标：在物体快速运动或遮挡场景下，重建结果无明显的轨迹断裂或伪影，时空一致性显著提升。
3. 系统目标：构建一套深度融合的动静场解耦机制，搭建由VGGT几何语义引导的、端到端的4D高斯渲染框架。通过针对特定实例的移除与编辑实验，定性地验证本文所提出的方法在复杂动态场景下的时空解耦表征能力与场景可编辑性。

## 拟采用的研究方法、步骤

本研究拟构建一套端到端的4D重建框架，以“动静显式解耦的4DGS”作为场景表示，以VGGT提供的几何一致特征与全局帧间关联作为引导信号。框架在同一优化闭环中完成：动静场建模、实例级伪标签生成以及基于对应关系的长程时空一致性约束学习，以克服传统方法依赖2D分割模型以及视频跟踪器的弊端，实现仅使用多视角RGB视频输入的高保真4D场景重建。具体研究方法如下：

1. 渲染框架构建：基于物理场解耦的混合渲染架构
   - 场景表示：以普遍认可的开源4DGS代码库为基础，引入基于线性运动假设的自由高斯基元（Free Gaussian Primitives），重构高斯基元的属性定义，利用其在4D空间中灵活初始化的特性，实现对动态场景的高效解耦。
   - 混合光栅化管线：扩展可微光栅化器接口，支持对动、静两组独立高斯进行统一排序与联合渲染。同时，开发额外的渲染通道，使其能导出实例分割图与深度图，从而构建可微监督通道，确保梯度能够从语义损失函数回传至高斯属性。
2. 特征挖掘：基于VGGT几何感知机制的伪标签生成
   - 语义聚类与提取：利用VGGT模型处理多视角视频帧，提取Transformer浅层的特征张量，采用谱聚类算法，挖掘潜在的语义信息。
   - 时空动态过滤：受VGGT 4D启发，通过计算中深层特征的Gram矩阵及其时间方差以识别高频运动区域并抑制背景噪声，结合VGGT输出的几何深度信息计算投影梯度，对粗糙掩码边缘进行几何边缘细化，生成高质量的实例级伪掩码以作为初始化监督信号。
3. 模型融合：全局注意力引导的时空关联优化
   - 长程关联建模：提取VGGT的全局帧间注意力图，构建跨帧像素的对应矩阵，建立长程时空索引。
   - 损失函数设计：设计“注意力引导的对比损失”。该机制要求，若VGGT判定跨帧像素对具有高注意力权重，则渲染场中对应的高斯基元特征必须保持较高程度的相似，以此来替代传统的局部邻域搜索策略，解决大幅度运动场景下的特征追踪与对齐难题。

具体步骤如下：

1. 开源基线适配与线性解耦架构构建。部署普遍认可的开源4DGS框架，在此基础上开发自定义模块，实现线性运动模型驱动的动态高斯场构建。修改光栅化器，搭建实例分割图与深度图的辅助渲染通道，通过实验验证混合渲染管线在动静解耦与梯度回传方面的有效性。
2. VGGT特征构建模块开发。部署VGGT模型，开发特征提取模块。核心工作是实现基于浅层特征谱聚类的实例级语义挖掘，并借鉴VGGT 4D的思想，结合Gram矩阵时间方差过滤背景噪声，辅以投影梯度对边缘进行细化，完成从多视角RGB视频输入到高质量实例级伪掩码的生成管线。
3. 注意力引导机制的嵌入与调试。提取VGGT全局注意力特征，构建跨帧对应矩阵。设计“注意力引导的对比损失”模块并接入训练循环。在部分场景上进行初步验证并调整损失权重参数，重点验证该机制在物体大幅度运动情况下对高斯基元特征一致性的约束能力。
4. 定量测试与定性验证。在动态场景数据集如Neural3DV，Multi-Human上进行全量定量测试。设计消融实验，验证实例级语义挖掘模块与全局关联损失对重建质量及解耦精度的贡献。最后，针对特定实例进行移除以定性验证本方法的场景编辑能力。

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
4. Yifan Wang, Peishan Yang, Zhen Xu, Jiaming Sun, Zhanhua Zhang, Yong Chen, Hujun Bao, Sida Peng, and Xiaowei Zhou. 2025. FreeTimeGS: Free Gaussian Primitives at Anytime Anywhere for Dynamic Scene Reconstruction. In CVPR. https://zju3dv. github.io/freetimegs
5. Haiyang Ying, Yixuan Yin, Jinzhi Zhang, Fan Wang, Tao Yu, Ruqi Huang, and Lu Fang. 2024. OmniSeg3D: Omniversal 3D Segmentation via Hierarchical Contrastive Learning. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 20612–20622.
6. Shengxiang Ji, Guanjun Wu, Jiemin Fang, Jiazhong Cen, Taoran Yi, Wenyu Liu, Qi Tian, and Xinggang Wang. 2024. Segment Any 4D Gaussians. arXiv preprint arXiv:2407.04504 (2024).
7. Shuzhe Wang, Vincent Leroy, Yohann Cabon, Yohann Cabon, Boris Chidlovskii, and Jerome Revaud. 2024. DUSt3R: Geometric 3D Vision Made Easy. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. 20697–20709.
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

---

## 内部审阅要点（2026-02-27）

> 说明：以下为内部审阅摘要，便于快速对齐修改方向；详细审阅见：`docs/reviews/2026-02-27/opening-proposal-review-4D-Reconstruction.md`。

- 总评：动机/结构清晰，但“创新点、可落地细节、评测口径、算力预算与止损策略”不足，且与仓库现主线（Plan‑B：速度初始化）存在叙事偏离。
- 必补 1：明确对标与差异点（相对 VGGT4D / Split4D / FreeTimeGS 的贡献列表）。
- 必补 2：将“端到端”改为更可辩护表述（无 2D 分割/跟踪硬前置），并澄清伪掩码生成属于软监督流程。
- 必补 3：补齐“全局注意力→对应→损失”的可实现定义（稀疏化策略 + 损失施加对象 + 像素/patch↔高斯绑定方式）。
- 必补 4：调整预期目标措辞与评测方案（mIoU 的 GT 来源/适用数据集/对标方法；建议加入时序稳定性指标）。
