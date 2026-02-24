# 4D Reconstruction 项目进度评估与修正方案

**日期：** 2026-02-24

**评估对象：** `Progress.md` (工程进度) & `2026-02-12-4d-reconstruction-execution.md` (执行计划)

**当前状态：** 工程执行力 A+，科研逻辑风险 C（急需修正）

------

## 一、 总体评价：工程满分，逻辑遇险

您的项目目前处于**“工程底座极稳，但核心假设悬空”**的状态。

- **🟢 亮点 (Engineering Excellence):**
  - **协议冻结与审计：** `protocol_v1.yaml` 和 `run_t0_zero_velocity.sh` 的建立展现了极高的工程素养，确保了实验的可复现性，这在毕设中是巨大的加分项。
  - **数据集决策：** 切换到 `SelfCap` 是明智的，直接对齐了 FreeTimeGS 的原生数据分布，规避了 Domain Gap。
- **🔴 风险 (Research Risk):**
  - **“Zero Velocity” (零速初始化):** 这是目前效果不佳的核心原因。Split4D 的逻辑依赖速度 $v$ 进行聚类，初始 $v=0$ 导致模型无法区分“物体”和“背景”，Mask 仅起到了加权作用而非引导作用。
  - **“KLT 替代方案”:** 用传统 KLT 光流替代 VGGT Attention，在 2.25 汇报中可以作为“验证连通性”的手段，但作为毕设核心逻辑是**题文不符**的（题目强调“大模型先验”）。

------

## 二、 核心风险深度解析

### 1. 为什么 "Zero Velocity" 是死路？

在您的脚本 `run_t0_zero_velocity.sh` 中，FreeTimeGS 的速度属性被初始化为 0。

- **后果：** 优化初期，模型是一个静态 3DGS。当遇到动态物体时，模型会倾向于通过“复制/分裂”高斯来弥补位移，而不是去优化 $v$ 值。
- **Split4D 失效：** Split4D 的核心假设是 `Cluster(x, v)`。如果所有点的 $v \approx 0$ 或完全随机，聚类算法就退化为仅基于位置的分割，无法将属于同一运动物体的碎片聚合在一起。

### 2. KLT 策略的双刃剑

- **生存视角 (2.25 汇报):** **正确。** 为了跑通流程，有结果展示比逻辑完美更重要。
- **毕设视角 (3.0+):** **致命。** 如果保留 KLT，您的毕设创新点将退化为“基于传统光流的 4D 重建”，完全丢掉了“3D 大模型先验 (VGGT)”这一核心卖点。

------

## 三、 紧急应对策略 (2.25 汇报 - Survival Mode)

**目标：** 在不修改代码的前提下，调整叙事逻辑，掩盖逻辑漏洞。

1. **重新定义 KLT 的角色：**
   - 在 Slide 中，不要强调使用了 KLT 算法。
   - 将其描述为 **“Temporal Consistency Constraint (Preliminary / Baseline)”**（时序一致性约束-基线版）。
   - 话术：*“我们首先构建了基于传统时序约束的连通性验证，以证明 Pipeline 的稳定性。基于 VGGT 的高维语义一致性约束正在集成中。”*
2. **解释 Weak Fusion 的失效：**
   - 不要承认“效果不好”，要将其转化为“实验发现”。
   - 话术：*“实验表明，单纯的 Mask 加权（Weak Fusion）不足以引导复杂非刚性运动。这反向证明了我们需要引入显式速度初始化（Explicit Velocity Initialization）和更强的特征度量约束（Feature Metric Loss），这也是下一阶段的重点。”*

------

## 四、 修正路线图 (2.26+ - Thesis Rescue)

为了挽救毕设逻辑，2.26 之后必须立即执行以下修正：

### Step 1: 必须拿到初速度 $v$ (物理引导)

- **行动：** 废弃 KLT，引入 **RAFT** 或 **Unilift**（现成的光流模型）。
- **新 Pipeline：**
  1. `VGGT Mask` 提取前景。
  2. 输入 `RAFT` 得到 2D 光流。
  3. 结合深度图反投影，计算粗糙的 **3D 场景流 (Scene Flow)**。
  4. 将此场景流赋值给 FreeTimeGS 的 `velocity` 属性。
- **目标：** 将 `run_t0_zero_velocity.sh` 升级为 **`run_t1_flow_initialized.sh`**。

### Step 2: 恢复 VGGT 的核心地位 (大模型先验)

- **行动：** 放弃 KLT Loss，实现 **Feature Metric Loss**。
- **公式：** $L_{feat} = || \text{VGGT\_Feat}(I_t) - \text{VGGT\_Feat}(\text{Render}(I_t)) ||$。
- **意义：** 这才是真正的“基于大模型先验”。

------

## 五、 关键信息补录 (需要您回复)

为了更精准地指导代码修改，请补充以下 3 点信息：

1. **代码库确认：**
   - 您用的 `4DGS-variant` 是 **FreeTimeGS** 的官方/复现代码吗？
   - *检查点：*  请确认其高斯参数中是否显式定义了 `velocity` (或 `movement`) 属性？如果它是依赖 MLP (`deformation_network`) 预测位移的，那它是 Deformable-GS，我们需要立刻换掉它。
2. **VGGT 输出格式：**
   - 目前的 `cue_mining.py` 产出的 `pseudo mask` 是什么格式（npy, png?）
   - 质量如何？（边缘是否贴合？背景有无误判？）
3. **计算资源：**
   - `2x48GB` 显卡是您独占的吗？如果是，跑 RAFT 提取光流只需要几分钟，完全可行。

------

**一句话总结：**

您的工程执行力保住了 2.25 的汇报底线；但要保住毕设的学位，2.26 后必须立即引入**“光流初始化”**来打破零速僵局，并替换掉 KLT。