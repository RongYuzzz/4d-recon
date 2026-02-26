# 02-26 项目推进决议建议

**日期：** 2026-02-26

**基于文件：** `meeting-pack.md` (v15 metrics)

**当前状态判定：** Feature Loss v2 (Postfix) 验证失败 (No-Go)，必须立即止损。

------

## 1. 核心决策：路线切换 (Pivot)

**我们建议立即执行【选项 B：触发 Plan‑B】，并冻结 Feature-Loss 主线。**

### 决策依据 (Based on Evidence)

根据 `docs/report_pack/2026-02-25-v15/metrics.csv` 的数据：

1. **Feature Loss 失效**：`feature_loss_v2_postfix_600` (PSNR 18.68) 显著低于 `baseline_600` (PSNR 18.95)。证明在当前协议下，VGGT 特征约束与 4DGS 的几何优化存在对抗，导致画质劣化。
2. **Cue 引入噪声**：`control_weak_nocue_600` (PSNR 19.11) 优于 `ours_weak_600` (PSNR 19.02)。这强有力地证明了**当前 Mask/Cue 的注入方式在引入噪声而非有效引导**。

### 结论

继续在 Feature Loss v2 上微调参数是“战术勤奋，战略懒惰”。我们必须转向**物理层面的修正（Plan-B）**，即解决已被证实的“零速初始化”问题。

------

## 2. 7 天冲刺排期 (Execution Plan)

> **原则：** 停止所有“探索性”实验，只做“收口”和“防守”动作。

| **周期**          | **动作 (Action)**                  | **预期交付物 (Deliverables)**                            | **备注**                                                   |
| ----------------- | ---------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------- |
| **Day 1 (02-26)** | **执行 Plan-B (3D Velocity Init)** | `scripts/init_velocity_from_points.py` + 200-step Sanity | 基于 `triangulation/*.npy`，不改训练代码，仅做初始化注入。 |
| **Day 2 (02-27)** | **Plan-B 趋势验证 (Full600)**      | 1 次 Full Run (600 steps) + `metrics.csv`                | 核心关注 **tLPIPS** 是否改善，以及 Ghosting 是否减少。     |
| **Day 3 (02-28)** | **反 Cherry-pick (防守)**          | `seg200_260` 上的 Baseline vs Control                    | 必须跑。这是为了证明“我们的 Baseline 和评测是鲁棒的”。     |
| **Day 4-7**       | **全员转写作 (Writing Mode)**      | 失败分析 (Failure Analysis) + 实验部分初稿               | 停止新增实验。整理图表，固化证据包。                       |

------

## 3. 验收口径调整 (Narrative Shift)

建议将项目的**核心贡献 (Core Claim)** 从“SOTA 性能提升”调整为**“机制探究与物理归因”**。

- **不再承诺：** “我们提出了一种特征损失，全面超越了 Baseline。”（目前数据不支持）。
- **转而承诺：** “我们揭示了稀疏视角下 4D 重建的**‘零速陷阱’**与**‘语义先验的不稳定性’**。”
  - **证据 1 (负结果)：** 通过 Control 组实验，证明简单的 2D 语义先验 (Mask/Feature) 不足以约束 4D 几何，甚至可能引入干扰。
  - **证据 2 (正结果/尝试)：** 通过 Plan-B 证明，引入粗糙但符合物理规律的 **3D 速度初始化**，比复杂的语义 Loss 更能改善收敛轨迹（或至少改变了伪影形态）。

------

## 4. 给导师的防守话术 (Q&A Prep)

- **Q: 为什么 Feature Loss 做了这么久没效果？**
  - **A:** 这恰恰是有价值的实验发现。我们的 Control 组（无 Cue）效果反而是最好的，这排除了代码实现的 bug，直接指向了**方法论假设的边界**——在 SelfCap 这种数据分布下，2D 语义特征无法有效约束 3D 几何，反而构成了对抗。这让我们及时止损，转向了更本质的物理速度建模（Plan-B）。
- **Q: 只有这么点提升，毕设/论文怎么写？**
  - **A:** 我们有非常扎实的**消融研究 (Ablation Study)** 和 **失败分析 (Failure Analysis)**。我们量化了“零速初始化”的危害，并验证了不同 Prior 的有效性边界。这种“探究机制、排除错误路径”的工作，比单纯刷一个 PSNR 高 0.1 但不知其所以然的模型更具科学价值。

------

## 5. 立即执行项 (Immediate Actions)

1. **冻结代码库：** 将 `feature_loss` 相关代码移入 `legacy/` 或打 Tag 封存，不再占用主分支精力。
2. **编写 Plan-B 脚本：** 立即实现从 `triangulation` 读取点云并计算粗略速度的脚本。
3. **更新文档：** 在 `docs/decisions/` 中新建决议，记录“Feature Loss v2 No-Go, Switch to Plan-B”。