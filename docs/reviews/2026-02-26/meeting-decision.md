[toc]



我看完你们两份材料后，直接给最终拍板：**Feature‑loss‑v2 主线立即 No‑Go，冻结；立刻触发 Plan‑B（3D velocity init）48h timebox；同时进入 Writing Mode**。
这不是“情绪化换方向”，是被你们的 **v15 指标**硬推出来的决策。

下面我按“拍板 → 为什么 → 怎么做 → 7 天排期 → 写作防守”给到可执行版本。

------

## 0) 最终拍板（写进 `docs/decisions/2026-02-26-*.md` 的那种）

### 主线（只能选 1 条）

- **选择：选项 B（Plan‑B：triangulation → 3D velocity initialization）**，严格 **48h timebox**。
- **Feature‑loss 主线冻结**：后续不再新增 feature-loss 的 full600；只允许做“无需 full600 的失败归因可视化/统计”。

### full600 预算（未来 7 天写死）

- **最多 N=3 次 full600**（不含 smoke200）：
  1. `planb_init_600`（必须）
  2. `seg200_260_baseline_600`（防守必须）
  3. `seg200_260_control_600`（防守建议；如果 GPU 不够，降级为 smoke200 但必须给出理由）

> 你们 meeting-pack 明确要求会议必须写死 N 值，否则会继续“能跑但结论漂”。我这里替你写死了。

### 验收口径（不改 protocol_v1，只新增一个“Plan‑B Go/No‑Go”决议）

- **不动 protocol_v1 成功线**（那是主协议）。
- 但为 Plan‑B 增加一个“48h 决议口径”（单独写入 decision 文件）：
  - **Go（任一条满足即可）**：
    - tLPIPS 下降 ≥ 5%（相对 baseline_600），且 PSNR 不劣化超过 0.2 dB
    - 或者：动态区域 ghosting 明显减少（定性），且训练稳定、指标不全线崩
  - **No‑Go**：PSNR/LPIPS/tLPIPS **三项全劣化** 或训练明显不稳（densification 发疯/损失爆炸）→ 立即停止 Plan‑B 扩展跑。

------

## 1) 为什么 Feature‑loss‑v2 必须止损（不是“再调调参”）

你们现在已经不是“效果没涨一点”，而是**全维变差**：

- `feature_loss_v2_postfix_600` 相比 `baseline_600`：
  - PSNR 从 **18.95 → 18.68**（-0.27 dB）
  - LPIPS 从 **0.4048 → 0.4219**（更差）
  - tLPIPS 从 **0.0230 → 0.0261**（更不稳）
    → **PSNR/LPIPS/tLPIPS 三杀，典型 No‑Go**。

而且你们还确认了：M1（smoke200）“看似 OK”，但 full600 会显著拖垮，这说明问题不是“写错一行代码”，而是**后期优化动力学/正则对抗**（feature prior 在后期开始压死 photometric / 追错目标）。

再补一刀：`control_weak_nocue_600 > ours_weak_600` 这个事实意味着——**你们当前 cue/注入策略在“帮倒忙或无效”**，继续在“语义先验”上加码（尤其 full600）属于低 ROI 赌博。

结论：继续 feature-loss-v2 的 full600 = 你们材料里说的“战术勤奋，战略懒惰”，这句话我同意。

------

## 2) 纠正一个危险表述：别把 Plan‑B 说成“解决零速初始化”

你们 meeting-opinions 里把问题归因成“已被证实的零速初始化”。这个表述**很容易被打穿**：

- 从你们既有产物/讨论看，baseline 的 velocity 并非严格为 0（至少不是“全 0”那种）。
- 所以更严谨的说法应该是：**“velocity prior 的质量/尺度/一致性不足（或错误），导致动态部分 ghosting / 收敛路径差”**。

Plan‑B 的定位也要改成：

> **不是从 0 引入速度，而是用更物理一致、更少噪声的 3D 点云时序差分，替换（或修正）现有 velocity 初始化。**

这样叙事稳得多，不会被一句“你速度明明不是 0”当场掀桌。

------

## 3) Plan‑B（triangulation → 3D velocity init）怎么做：我给你“最小可行、最不容易炸”的实现规格

你们 meeting-pack 已经把 Plan‑B 的纪律写得很对：不改 data、不改 protocol_v1、输出隔离、必须自检。
我在此基础上，给出**脚本应当怎么写**（让它在 48h 内可落地）。

### 3.1 输入 / 输出（必须兼容你们现有 trainer）

**输入：**

- `data/selfcap_bar_8cam60f/triangulation/points3d_frameXXXXXX.npy`
- `.../colors_frameXXXXXX.npy`（可选，用于匹配过滤）

**输出（建议）：**

- `outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
  并且**不要覆盖 baseline 的 init**。

### 3.2 速度估计：不要做“聪明但易炸”的 scene flow，做“粗糙但稳定”的 3D matching

用 keyframe_step=5（与你们协议一致）：

对每个 keyframe `t`：

1. 取 `P_t` 和 `P_{t+step}`（点云都在同一世界坐标系里）
2. KDTree 做最近邻：`nn(P_t -> P_{t+step})`
3. **互为最近邻（mutual NN）+ 距离阈值**过滤匹配（减少乱配）
4. velocity：
   - 如果你们时间 `t` 在训练里是归一化到 `[0,1]`：
     - `Δt = step / (T-1)`
     - `v = (p' - p) / Δt = (p' - p) * (T-1)/step`
   - 如果训练里用帧索引当时间：`v = (p' - p)/step`
     **必须在脚本里打印并落盘“采用了哪一种”**（否则一定会踩单位坑）。
5. unmatched 点：`v=0`（不要瞎猜）

### 3.3 必须做的“鲁棒性补丁”（不然你会得到一坨速度噪声）

**补丁 A：global drift removal**

- 对所有匹配的位移 `d_i = p'_i - p_i`，取 median(d) 作为全局偏移（理想应接近 0）
- `d_i <- d_i - median(d)`
  用途：去掉 per-frame triangulation 的系统性漂移（否则你会把漂移当运动）

**补丁 B：速度裁剪（clip）**

- 用 p99（或 p95）裁剪 `||v||`，防止少数乱配把优化炸掉
- 这一步不是“调参”，是工程安全阀。

### 3.4 Plan‑B 脚本自检（必须落盘，写作也需要）

脚本跑完必须生成 `outputs/plan_b/.../velocity_stats.json`，包含：

- `mean/p50/p90/p99/max(||v||)`
- `ratio(||v||<1e-4)`
- `Δt` 的定义（normalized 或 frame-based）
- 裁剪阈值（p99 的数值）
- 匹配率（matched / total）

这点 meeting-pack 其实已经写了“必须自检并落盘”，我这里只是把字段说死。

------

## 4) 48 小时执行 Gate（Plan‑B 也要 Gate，不然又漂）

你们已经用 M1–M4 gate 约束过 feature-loss，现在对 Plan‑B 也照样要 Gate。

### Gate‑B1（Day1）：200-step sanity（不许跳）

交付物：

- `init_points_planb_step5.npz`
- smoke200：baseline_init vs planb_init（同 protocol_v1，除了 init 不同）
- 对比：throughput、loss 曲线、渲染视频片段（至少 test cam）

**Day1 直接 No‑Go 的条件：**

- 训练明显不稳定（loss 爆 / 渲染发散）
- planb 的 `||v||` 分布离谱（max 巨大、p99 巨大、matched rate 极低）
- 或者 smoke200 就已经全线变差且画面明显更糟

### Gate‑B2（Day2）：仅 1 次 full600（Go/No‑Go）

- 只跑 1 次 full600
- 跑完直接对比 `baseline_600` 的 PSNR/LPIPS/tLPIPS
- 达不到 Go 就 stop（Plan‑B 不允许变成新主线）。

------

## 5) anti‑cherrypick：我同意必须做，但别把它做成“新协议漂移”

meeting-opinions 里 Day3 强调必须跑 `seg200_260` 防 cherry‑pick，我同意。
但纪律要这样写：

- `seg200_260` **只作为附录协议**（例如 `protocol_seg2.yaml`），不替代 `protocol_v1`
- 只做 **baseline vs control**（不要再引入 ours/feature-loss），目的就是证明：
  - baseline 的排名不是挑段挑出来的
  - control 现象在另一段仍成立/或至少趋势一致
    这与 meeting-pack 的“只补最少防守证据”完全一致。

------

## 6) 写作叙事：从“SOTA 提升”转为“机制归因 + 负结果”是对的，但要更硬、更可审计

你们 meeting-opinions 的 narrative shift 我同意：不要再承诺“特征损失全面超越 baseline”，因为数据不支持；转而承诺“机制探究与边界”。

我建议写作把贡献写成 3 条（每条都能被证据包支撑）：

1. **协议与证据链贡献**（工程但可审计）：
   - protocol_v1 冻结 + evidence pack + throughput 统计 + 单测锁死对齐 bug
     （这是你们能稳过答辩的护城河）
2. **负结果贡献（重要）**：
   - 在 canonical 协议下，feature-loss-v2（postfix）导致 PSNR/LPIPS/tLPIPS 全维退化
   - control 优于 ours-weak，说明 naive cue/注入方式可能引入噪声/破坏优化
     这不是“失败”，是“方法假设边界”的实证。
3. **Plan‑B 作为物理修正尝试（可正可负都能写）**：
   - 若有效：证明“物理一致的 motion init”比语义正则更影响收敛路径
   - 若无效：也能写成“per-frame sparse triangulation 的 correspondence 不足以提供稳定 scene flow prior”，这是很合理的失败归因

**答辩 Q&A** 你们 meeting-opinions 给的版本基本能用，但我要求你把“zero speed trap”那句话换成“velocity prior quality/scale inconsistency”。

------

## 7) 最后：你现在该怎么在会上说（一句话版）

- “我们已经按 Gate 把 feature-loss-v2 推到 full600，且 postfix 后仍全维退化，因此主线 No‑Go 并冻结；接下来 48h timebox 执行 Plan‑B（triangulation→3D velocity init），只跑 1 次 full600 给 Go/No‑Go；同时补 seg200_260 的 baseline vs control 防 cherry‑pick；其余时间进入写作与失败分析收口。”

------

如果你愿意我再进一步“把关到代码接口级别”，你把你们当前 trainer 读取 init 的字段名（`npz` 里到底叫 `velocities` 还是 `v`、有没有 `times`/`duration`）贴出来，我可以把 Plan‑B 脚本的**输出 schema**写成严格对齐你们 pipeline 的版本，避免你们 Day1 在数据格式上翻车。

## 8) Q&A

### Q

选 Plan B 是否会影响论文的整体目标（工作量饱满+一点创新+很好的写作）？是否需要对 feature-loss 进行全面透彻的失败归因，以避免细节错误导致的指标全面下降？如果你需要我补充更多的项目信息和实验细节，随时告知我。

### A

结论先拍死：**选 Plan‑B 不会毁掉你论文“工作量饱满 + 一点创新 + 很好写作”的目标，反而更容易把项目收口成一个可辩护的 thesis**。但前提是两件事必须同时做：

1. **Plan‑B 作为“唯一主线”推进**（48h timebox，按你们会议包的 Gate 纪律走）。
2. **Feature‑loss 做“足够强”的失败归因（但不是“全面透彻到重跑 full600”）**，目的只有一个：**排除“细节错误/实现 bug”导致三项指标全维下降的可能性**，让你 pivot 合法、写作站得住。

下面我分两问回答。

------

#### 1) 选 Plan‑B 会不会影响论文整体目标？

##### 1.1 不会；你只需要把“目标/贡献”从“刷 SOTA”换成“机制探究 + 可审计证据链 + 物理先验尝试”

你们会议包已经把现实钉死了：在 canonical protocol_v1 下，`feature_loss_v2_postfix_600` 相对 `baseline_600` **PSNR/LPIPS/tLPIPS 三项全劣化**，属于明确 No‑Go；继续盲跑 full600 是低 ROI。
同行意见包也给了同样结论，并要求 pivot。

所以论文的“主贡献”必须改口径（这不丢人，反而像研究）：

- **贡献 A（工程/方法论贡献，最稳）**：
  你们把协议冻结、证据链（report_pack、throughput、单测锁死对齐）做成可复现体系，这在毕设答辩里非常能防守。你们甚至已经明确“哪些显性工程坑排除了”：`token_proj` 与 cache downscale 对齐 bug 已修复并用单测锁死，吞吐也可审计。
- **贡献 B（负结果贡献，能写出“像论文”的部分）**：
  你们不只是“失败了”，而是通过 control 组量化出了一个关键风险信号：**`control_weak_nocue_600` 的 PSNR/LPIPS 更好，说明 cue 注入路径可能在引入噪声或破坏优化**。
  这不是“调参没调好”，这是“假设边界”——可以写成结论。
- **贡献 C（一点创新，Plan‑B 的正当性）**：
  Plan‑B 不是“换个 init”，而是**利用你们数据契约里最稀缺的资产：per‑frame triangulation 点云**，构造一个“物理一致的 motion prior / velocity initialization”，去修正动态收敛路径（ghosting、漂移、时序不稳）。
  这条创新虽然不 SOTA，但**可解释、可审计、可消融**——对毕设最重要。

##### 1.2 你需要立刻改掉一个危险叙事：别把 Plan‑B 说成“解决已证实的零速陷阱”

同行意见包里写了“已被证实的‘零速初始化’问题”“零速陷阱”。
这句话**很容易被答辩专家一枪打穿**（因为你们并没有在会议包里给出“速度几乎全 0”的严谨证据；而且你们之前也统计过 velocity 并非全零）。

更稳的表述应该是：

> Plan‑B 解决的不是“速度为 0”，而是 **velocity prior 的质量/尺度/一致性不足或噪声过大**，导致动态部分 ghosting 与时序不稳；我们用 triangulation 的跨帧 3D 差分提供更物理一致的初始 motion。

这个说法不会被“抓字眼”打掉。

##### 1.3 工作量会不会不饱满？不会，你反而更饱满

你现在最怕的是“换 Plan‑B 之后看起来像换个 init 不够研究”。
解决办法：把 Plan‑B 写成一个**完整实验闭环**，而不是一行改动：

- 一个可复现脚本（init_velocity_from_points.py）
- 一个 sanity（200-step）
- 一个 full600（Go/No-Go）
- 一页 velocity stats（p50/p90/p99、匹配率、裁剪阈值、时间尺度解释）
- 一个消融：baseline_init vs planb_init（只变 init，不改协议分布项）
  这些全是“工作量”，而且都是能进 evidence pack 的。

------

#### 2) feature‑loss 是否需要“全面透彻失败归因”来避免细节错误？

##### 2.1 需要失败归因，但**不需要“全面透彻到重跑/大扫参”**

你要的不是“把 feature‑loss 修好”，而是回答答辩里最致命的问题：

> 你这个 feature‑loss 失败，是因为方法论不成立，还是因为你实现细节错了？

如果你不能证明“不是细节错误”，别人会默认你代码有坑，然后你的 negative result 价值直接归零。

所以你必须做一个**“最小失败归因包（Failure Attribution Minimum Pack）”**，全部都应当是**无需新增 full600**就能完成的诊断（你们会议包也明确建议从关键未知里选 3 条，用无需 full600 的验证方式判断方向）。

##### 2.2 我替你拍板：失败归因只做 5 项，做完就封存 feature‑loss（不再追加 full600）

下面 5 项就是“足够强”的归因，做完就能很硬地说：**我们排除了实现级 bug，失败来自 optimization 对抗/假设边界**。

###### (1) Loss 量级曲线：L_feat 是否在后期主导、压死 photometric？

你们会议包把这条列为最可能假设 #1。
做法：用已有 full600 日志直接画（不需要重跑）：

- `mean(L_photo)` vs `mean(L_feat)` 随 step 的曲线（每 50 step 平均）
- 看是否出现“后期 L_feat >> L_photo”或者梯度量级反转

判定：

- **如果 L_feat 后期主导**：这是方法/日程问题（schedule/权重），不是“实现写错”。
- **如果 L_feat 全程很小还三项全崩**：更可能是对齐/梯度链/phi 选择导致的“惩罚坐标误差”。

###### (2) Cache round-trip 一致性：phi(I_gt) 离线 cache 与在线一致吗？

会议包把“cache round-trip 与在线一致性”作为假设 #2 的快速验证之一。
做法：你们已经有工具/单测基础（token_proj 对齐 bug 已修复并锁死）。
这里再做一次 end-to-end 检查：同一张 GT 图像：

- 离线 cache 特征 vs 在线 forward 特征 → 差值应接近数值误差
- 如果差距大：就是实现/预处理不一致（细节 bug）

这项是“堵嘴神器”。

###### (3) 1–2px 平移敏感性：phi 对轻微错位是否极端敏感？

会议包建议“对 GT 做 1~2 px 平移的敏感性曲线（无需训练）”。
做法：

- 对 `I_gt` 做 (dx,dy) 的小平移
- 计算 `L_feat(shifted, original)`
  如果 1px 就引起巨大 loss：说明 feature loss 在你们当前 4DGS early stage（对齐误差必然存在）会系统性惩罚错位 → 很可能就是“方法对抗”的根因（不是代码 bug）。

###### (4) Gating/patch 命中率热图：你到底在正则哪里？

会议包把这条列为假设 #3。
做法：导出 60 帧的 gated patch 空间分布热图，看它是不是：

- 集中在动态物体/遮挡边界（合理）
  还是
- 均匀撒在背景纹理/噪声（无效甚至有害）

这能解释“为什么 M1 看着 ok，M2 崩”。

###### (5) 梯度链检查：∥∂L_feat/∂render_rgb∥ 与 ∥∂L_feat/∂gaussian_params∥ 是否非 0？

会议包列为假设 #4。
只需要 10 step 小跑打印 norm：

- 如果梯度为 0 或极小：说明你 feature loss 没在驱动任何东西（实现问题）
- 如果梯度正常但指标更差：说明这是“优化对抗/目标冲突”，不是“没回传”

> 做完这 5 项，你就有资格在论文里写：“我们排除了对齐/缓存/梯度链等实现错误，负结果反映的是方法假设边界。”

##### 2.3 什么时候才允许“为 feature‑loss 再跑 1 次 full600”？

只有一种情况：在上述 5 项里，你发现了**明确的、可修复的实现级错误**（比如 cache 不一致、梯度链断、gating 命中明显错位），并且修复成本 < 半天。

否则一律不再跑 feature-loss full600——这就是 Gate 纪律，不然你们会回到“能跑但结论漂”。

------

#### 3) 你现在不需要补充信息也能继续推进；但如果你要我“帮你拍死 bug 归因”，给我 3 样东西就够

你说“需要就告诉你”，我不强制你现在提供。
但如果你希望我进一步把 feature-loss 的失败归因直接“钉死到实现层”，你只需要贴这三项（无需额外描述）：

1. `feature_loss_v2_postfix_600` 的 loss log 里：`L_photo/L_feat`（或能推出来的字段）
2. 你们 cache meta（phi_name/phi_size/normalize/stride）+ round-trip 对比结果
3. 10 step 的梯度 norm 打印（对 render_rgb 和对 gaussian params）

这三样一来，我可以直接判断“是实现 bug 还是方法对抗”，并告诉你是否值得为 feature-loss 再花那唯一一次 full600 预算。

------

#### 最终一句话（你可以直接拿去跟导师对齐）

- **Plan‑B 不会伤论文，反而能让你把项目写成“可复现体系 + 负结果机制归因 + 物理先验修正尝试”的完整闭环。**
- **feature‑loss 需要做“5 项最小失败归因包”来排除细节错误，但不需要全面透彻到继续烧 full600。**