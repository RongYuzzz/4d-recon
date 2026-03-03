# 4D 重建项目问题解决导向讨论材料（2026-02-28，更新至 2026-03-01）

用途：这次讨论的目标是**解决问题并锁定行动**，不是进行防守式辩论。本文档用于：对照开题路线，明确当前实现与证据链的差距；把差距拆成可在 2026-03-06 前完成的最小闭环任务；并请导师/专家对“是否继续投入 stage‑2 训练、最小补实验是什么、哪些承诺需要降级/替代”做取舍拍板。

---

## 0. 本次讨论/执行的核心问题与预期产出（以解决问题为唯一目标）

### 0.0 已入库的同行/专家输入（Source of Truth）

- 同行建议（高通量并发实验 + 5 天倒排期）：`suggestions.md`
- 专家拍板（面向 2026-03-06 Code Freeze 的决策 + DoD）：`professional-decisions.md`
- 收尾执行总计划（3/6 冻结 -> 3/22 定稿）：`docs/plans/2026-03-01-project-closeout-plan.md`

> 本文件从“讨论材料”升级为“执行材料”：若导师/专家要 override 任何拍板，必须在 `professional-decisions.md` 与本文件同步记录（并明确影响哪些协议/证据链）。

### 0.1 专家已拍板的结论（不再争论，直接执行）

1. **baseline：必须加固，但只做“有限对齐论文关键点”**
   - 不做论文 FreeTimeGS 的端到端复现（ROMA 初始化、动态区域评测等短期不现实）。
   - 但必须封死会被一票否决的攻击面：`lambda_4d_reg` 量级校准、`duration_reg` 目标歧义/潜在 bug 处置、time normalization/off-by-one 风险审计（详见 §2.4.4–§2.4.6）。
2. **收敛性：600 steps 不能继续作为唯一支撑**
   - 必须做 1 次长训 `convergence sanity check`：baseline vs planb_init 各补 1 次 2k/5k（建议 5k，若能则 10k），并多 step 打点。
   - v1/v2（600 steps）证据链不回写；长训结论进入**新协议**（建议名：`protocol_v1_long` 或 `protocol_v1_convergecheck`）。
3. **Stage‑2：维持 trade-off 收口，但允许 1 次“终极衰减验证”盖棺**
   - 不再做 full600 大 sweep；也严禁宣称做过未实现的 gating。
   - 允许 1 次 feature loss “前强引导、后指数衰减到 0” 的验证：成功则形成可发表的策略；失败则作为 Failure Analysis 的铁证（详见 §6/P0 与 §8 并发计划）。
4. **泛化/反 cherry-pick：至少补一个第二场景或第二段**
   - 最低成本：跑通第二场景 `Baseline_full vs Plan‑B_full`（一行数据 + 一段视频即可显著增强说服力）。
5. **工程审计：`manifest_match: yes` 是硬门槛**
   - manifest 不一致不允许宣布冻结；必须重打 tar 并刷新 SHA256 快照到 docs（详见 §6/P1 与 §8/Day1）。

### 0.2 本轮仍需现场确认的少数未定项（只保留真正会影响执行的点）

- 第二场景选型：SelfCap 的哪一组（或 Neural3DV 的哪个片段）作为“第二场景/第二段”？
- 长训协议命名与验收点：2k/5k/10k 的 step 打点具体取哪些（建议至少包含 2k 与 5k）。
- 若要“有限对齐论文指标口径”：是否在**新协议**里补一个最小的 LPIPS(VGG) 评测，或动态区域 proxy（不回写旧结论）？

---

## 1. 当前进度（截至 2026-03-01）

### 1.1 已闭环的主证据链（阶段一）

- 协议冻结（Single Source of Truth）：`docs/protocol.yaml`（protocol_v1 的主入口；镜像存档：`docs/protocols/protocol_v1.yaml`）
- 阶段一主结论：`planb_init_600` 相对 `baseline_600` 在 test@599 显著提升（见下方“关键实验数据”与 `Progress.md`）
- 写作骨架（阶段一）：`docs/writing/planb_paper_outline.md`

### 1.2 按 2026-02-27 决议完成的“开题对齐补齐”（阶段二 / protocol_v2）

统一入口（建议导师按此顺序查证）：

- 开题对外版（v2）：`4D-Reconstruction-v2.md`
- 阶段二 report-pack：`docs/report_pack/2026-02-27-v2/README.md`
- 决议与协议：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`、`docs/protocols/protocol_v2.yaml`

阶段二三类证据（已落盘）：

- 动静解耦导出（static-only / dynamic-only）：`notes/protocol_v2_static_dynamic_tau.md`
- VGGT 可解释材料（伪掩码 + feature PCA）：`notes/protocol_v2_vggt_cue_viz.md`、`notes/protocol_v2_vggt_feature_pca.md`
- stage‑2 试探实验与 trade-off 定性对比：`notes/protocol_v2_stage2_tradeoff_qual.md`
- 诊断：temporal diff / spatial metrics top-k 快照（见“关键实验数据”）

### 1.3 工程侧已具备的复现/审计能力（用于复现与交付）

- 可复现实验产物指针与脚本入口：`README.md`、`Progress.md`
- 指标汇总与证据打包：
  - scoreboard 生成：`scripts/summarize_scoreboard.py`（示例命令见 `docs/report_pack/2026-02-27-v2/README.md`）
  - evidence tar：`scripts/pack_evidence.py`
  - 当前存在离线包：`outputs/report_pack_2026-02-28.tar.gz`（本地 tar 内条目数 `754`）

---

## 2. 当前技术路线与推进方向（以协议为准）

### 2.1 当前技术路线（以实际实现为准）

1. 阶段一（物理运动先验）：Plan‑B 速度初始化修复“劣速/零速基底”的收敛陷阱，作为稳定底座。
2. 阶段二（几何语义先验）：在 Plan‑B 底座上引入 VGGT 的几何一致特征与稀疏对应（soft prior），做可实现、可审计的 feature metric / consistency 约束。
3. 展示（可编辑性）：通过速度阈值 `tau` 将 gaussians 分为 static/dynamic 两层导出视频，给出 object removal / 动静显式分离的定性证据。

真源文件（导师若要核对细节，以这两处为准）：

- 决议：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- protocol_v2：`docs/protocols/protocol_v2.yaml`

### 2.2 收口策略（当前已经在执行）

- 不破坏阶段一证据链：`v26 + protocol_v1` 作为最终证据保留不动。
- stage‑2 所有新增实验与结论统一归档到 `protocol_v2`（避免与 v26 数值混用）。
- 如果短期内无法形成稳定增益：需要明确是否停止新增训练，把工作转为“解释清楚为什么会 trade-off、失败边界在哪里、下一步应该怎么做”；或允许进行一次最小补实验来验证关键假设。

### 2.3 两个关键基础问题（baseline 合理性 + 短训练是否有说服力）

这两点如果不解决，后续所有结论都会被动摇，因此建议在本次讨论中优先拍板“做什么最小动作把不确定性消掉”。

#### Q1: baseline 是否合理？如果 baseline 其实是 FreeTimeGS 复现失败，那么结论是否站不住？

当前 baseline 的事实定义（以仓库实际跑法为准）：

- 本项目的 baseline（protocol_v1）是 `baseline_freetime_vanilla`（见 `docs/protocol.yaml`），其 `baseline_600` 实际跑的是 **本仓库 fork 过的 `third_party/FreeTimeGsVanilla/` + config `default_keyframe_small` + 外部 per-frame triangulation 输入**。
  - 这意味着 baseline 不是“直接 clone 上游 FreeTimeGsVanilla main 就能复现”的 vanilla，而是“本仓库协议化/可审计 fork”的 vanilla（上游不支持本仓库协议要求的 `--train/val/test camera split`、`--eval_on_test`、`tLPIPS` 等参数）。
- baseline 的关键配置（见 `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/cfg.yml`）包含若干与论文显著不同的选择，例如：
  - `lambda_4d_reg = 1e-4`（论文常见写法为 `1e-2` 量级）
  - 存在 `lambda_duration_reg > 0` 的额外正则，且在 `init_duration=-1 (auto)` 时其 target 语义可能不合理（需要确认是否构成实现偏差/bug）
  - keyframe-only 初始化与 velocity bridging（属于社区实现主路线）
  - 指标口径也不与论文 SelfCap 直接对齐（论文有“动态区域指标”与 LPIPS(VGG) 口径；本仓库当前默认是全图 `PSNR/SSIM/LPIPS(Alex)` + test 的 `tLPIPS`）。

这意味着：

- 如果你的主张是“我们复现并改进了 FreeTimeGS 论文方法”，那么当前 baseline **不足以支撑该主张**，需要做 paper-alignment 或至少做“偏差说明 + 最小校准实验”。
- 如果你的主张是“在 FreeTimeGsVanilla（社区实现）这条可复现管线下，我们提出的方法在固定协议与预算下改进了结果”，那么 baseline 仍然可以成立，但前提是：实现内部需要自洽、关键 bug 风险要清零，并且 baseline 需要经过最小校准（避免用一个明显次优的 preset 当 baseline）。

专家已拍板（见 `professional-decisions.md`）：baseline 必须做最小加固与校准，至少包含 A1，并且需要对 A2 的潜在 bug/不自洽点给出处置（修复或暂时禁用再对比）。

- A1（最快，低成本）：做一个 **baseline 校准 smoke sweep**（不改代码，改 config/flags），只回答一个问题：把关键超参拉回论文量级后，baseline 是否显著改善并改变结论？
  - 建议只扫 1 个 knob：`lambda_4d_reg`（`1e-4 -> 1e-3 -> 1e-2`），其他不动，跑 smoke200。
- A2（更关键，但可能需要重跑部分证据）：对 FreeTimeGsVanilla 的“潜在 bug/不自洽”点做一次最小修复或关闭（例如 duration_reg 的 target 语义），并复跑 baseline_smoke200 + planb_smoke200 验证结论是否稳健。
- A3（文档化 + 未来工作）：将“论文 vs 社区实现偏差”整理成附录/限制，并明确你论文的 baseline 定义是“FreeTimeGsVanilla baseline”。这条路线仍建议至少做 A1，以避免 baseline 被质疑为“没调好”。

#### Q2: protocol 一直采用极短训练（600 steps），模型未收敛，这种数据有说服力吗？

事实：

- 当前 `protocol_v1/v2` 的 full 训练步数为 `600`，并且评估点主要在 `step=599`（例如 `baseline_600`、`planb_init_600` 的 `test@599`）。
- TensorBoard 中 loss 仍在下降且存在波动（可见 `outputs/report_pack/diagnostics/convergence_curves_20260301/*_loss_curves.png`），这意味着“完全收敛”很难主张。
- 更具体地，在该预算下有若干训练 schedule 根本不会被激活：例如 `sh_degree_interval=1000` 时，600 steps 内 `sh_degree` 会一直停留在 0（等价于只学 DC 颜色），这与论文长训（SH 逐步提升）不在同一收敛阶段。

这带来的真实风险是：**你看到的提升可能是“早期收敛速度差异”，而不是最终上限差异**。

专家已拍板（见 `professional-decisions.md`）：

- 必须执行 B2（convergence sanity check）：对 baseline 与 planb_init 各补 1 次更长训练（2k/5k 起步，建议 5k，若能则 10k），并在多个 step 打点评估，回答“差距会消失还是保持/扩大”。
- B1（anytime/短预算叙事）只能作为**备选写法**，不能作为跳过长训自检的理由（因为当前研究目标不是 anytime setting）。

### 2.4 FreeTimeGS 论文 vs FreeTimeGsVanilla 偏差（用于 baseline 风险定位）

你补充的“论文 vs 社区实现”偏差非常关键，它决定了 baseline 的定义方式与我们该修什么/该校准什么。

- 偏差清单（工作底稿，含分类规则与 Top 风险）：`docs/reviews/2026-03-01/freetimegs-paper-vs-freetimegsvanilla-deviations.md`
- 用户原始详细清单（逐条保留，便于逐项核验与审计）：`docs/reviews/2026-03-01/freetimegs-paper-vs-freetimegsvanilla-deviations-user-provided.md`
- 同行补充（把三者对齐对象一次说清楚，并覆盖“论文 vs 上游 / 上游 vs fork / baseline vs 论文/上游”三层差异）：`docs/reviews/2026-03-01/baseline-paper-vanilla-deviations-peer-provided.md`
- 本次讨论建议只盯 Top-K：优先解决会直接影响 baseline 合理性与收敛结论的偏差（例如 `lambda_4d_reg` 量级、duration_reg 语义、time normalization 自洽性），其余作为 limitation/未来工作。

但考虑到该问题已经上升为“会否动摇全项目可信度”的级别，下面把**关键事实**直接展开到本讨论文档中，保证现场讨论不需要在多个文件之间跳转。

#### 2.4.1 对齐对象定义（必须先把三者“到底是什么”说清楚）

1) **论文 FreeTimeGS（arXiv:2506.05348）**

- 方法框架：Sec.3（尤其 p.4 的 3.2/3.3）+ 补充材料 p.10 的 B 节给了关键公式/超参/评测口径（本机：`/tmp/papers/freetimegs_arxiv_2506.05348.pdf`）。

2) **上游 FreeTimeGsVanilla（GitHub main）**

- 本仓库通过快照 `third_party/FreeTimeGsVanilla-main.tar.gz` 对齐上游 main。
- 它是“基于 gsplat 的最小实现”，但不等价于论文训练/评测协议（keyframe/sampling/λ/评测口径等均有差异）。

3) **本项目 baseline（protocol_v1 的 baseline_freetime_vanilla）**

- 冻结协议：`docs/protocol.yaml`（id: `selfcap_bar_8cam60f_protocol_v1`）。
- baseline 名称：`baseline_freetime_vanilla`（`docs/protocol.yaml:75`）。
- 实际入口脚本：`scripts/run_train_baseline_selfcap.sh`，跑的是**本仓库 fork + 补丁后的** `third_party/FreeTimeGsVanilla/`（不是上游原版）。
- 一个已落盘的对照实例：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/`（其 `cfg.yml` 是“这次 baseline 具体是什么”的最硬证据）。

这三者关系的“关键一句话”：

- 当前项目的 baseline 是“**协议化 fork 的 FreeTimeGsVanilla** 在 SelfCap(bar, 8x60) + 固定相机拆分 + 极短预算(600 steps) 下的表现”，而不是“论文 FreeTimeGS 的端到端复现”。

#### 2.4.2 偏差清单 A：论文 FreeTimeGS ↔ 上游 FreeTimeGsVanilla（复现层面偏差）

A1) 初始化链路（论文强调 ROMA；Vanilla 不含 ROMA）

- 论文：每帧 ROMA 多视角 2D matches → 三角化 3D 点；点+时间初始化 (µx, µt)；再用 kNN 匹配两帧 3D 点，位移作速度 v（PDF p.4 Sec.3.2）。
- Vanilla：不实现 ROMA；要求你已产出 triangulation/`points3d_frame*.npy`（见 `third_party/FreeTimeGsVanilla/README.md` Input Requirements），并用 `third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py` 做“keyframe 组合+速度估计”（例如从 `:467` 开始）。
- 关键偏差：Vanilla 的默认思路是 “keyframe-only + velocity bridging”（例如 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1312`），论文正文没有 keyframe/stride 叙事（PDF 全文检索不到 keyframe/stride）。

A2) keyframe/采样/预算策略（论文未给；Vanilla 做了工程化近似）

- Vanilla 的 combine：只取 keyframes，但速度用 keyframe 的 “下一帧 t→t+1” 的点云做 KDTree 匹配（`third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:468`、`:489`），不等于论文的“逐帧/相邻帧”叙述。
- Vanilla 的 smart sampling（密度/速度/中心加权）属于工程策略（`combine_frames_fast_keyframes.py:548` + trainer 内 `use_smart_sampling`），论文 Sec.3.2-3.3 不包含这块。

A3) 训练步数（论文 30k@300 帧；Vanilla 有多套默认）

- 论文：300 帧序列训练 30k iter（PDF p.4 Sec.3.3）。
- 上游 Vanilla：`run_pipeline.sh` 固定跑 30000（本仓库 fork 里也保留但做了可配）；但 trainer 的 `Config.max_steps` 默认是 70000（见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` 的 config 定义）。

A4) 4D regularization 权重（论文 1e-2；Vanilla 默认更小）

- 论文：`lambda_reg = 1e-2`（PDF p.4 Sec.3.3）。
- Vanilla：`lambda_4d_reg` 默认 1e-3，且代码注释明确 “Paper value 1e-2，降到 1e-3”（见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:456` 一带的 config 注释）。

A5) “只评测动态区域”的口径（论文 SelfCap 有；Vanilla 无）

- 论文（补充材料 p.10 Sec.B.1）：SelfCap 报两套指标：全图 & 仅动态区域；动态区域通过 GT background + Background Matting V2 得 mask，再按 bbox crop 并外部填黑。
- Vanilla：无动态区域评测管线；默认全图算 PSNR/SSIM/LPIPS（eval 逻辑见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` 的 `eval` 实现，例如 `:4123` 一带）。

A6) 指标/网络细节（论文表格 DSSIM、SelfCap 用 LPIPS(VGG)；Vanilla 默认 SSIM、LPIPS(Alex)）

- 论文补充材料表格描述：SelfCap 用 LPIPS VGG（p.10 Table 8）。
- Vanilla：默认 `lpips_net="alex"`（见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:734` 一带），并使用 SSIM（实现里是 `self.ssim(...)`，例如 `:4188`）。

#### 2.4.3 偏差清单 B：上游 FreeTimeGsVanilla ↔ 本仓库 third_party/FreeTimeGsVanilla（本项目 fork 补丁偏差）

同行对比上游快照 `third_party/FreeTimeGsVanilla-main.tar.gz` 与本仓库 fork，主要差异集中在 3 个文件（另有 `.venv/egg-info/__pycache__` 等本地产物），核心目的都是：让训练/评测变得**协议化、可审计、可复现**。

B1) Trainer：新增“协议化评测/相机拆分/额外 loss/审计开关”

- 显式 seed + cudnn deterministic（减少随机性）：例如 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1682`。
- 显式 train/val/test 相机名（上游主要是 `test_every`）：例如 config/arg 定义与映射逻辑（`...:314`、`...:1718`）。
- 新增 test 评测开关与 test 采样频率（使 `eval_on_test` 成为协议显式项）：`...:409`，训练循环触发 `...:4115`。
- 新增 `tLPIPS`（只在 test 且 `eval_sample_every_test=1` 时计算）：`...:4149` 到 `...:4199`。
- 新增弱/强/特征损失接口（baseline 可通过权重=0 关闭，但“代码路径存在”会影响对 baseline 的定义争议，需要在讨论里明确）：pseudo mask / temporal corr / VGGT feature metric（例如 `...:464`、`...:477`、`...:499`）。
- 新增 T0 审计退化开关（force v=0 + grad/log）：例如 `...:451`。

B2) Dataset：补齐真正的 val split（上游把 val 当 test 用/或没有严格区分）

- 本仓库：`FreeTimeDataset` 支持 `split="train/val/test"` 且有独立 `val_set`（例如 `third_party/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:528`）。
- 上游：更偏 “held-out cameras” 的单层 test_every 逻辑，无法直接对齐本仓库协议口径。

B3) Pipeline 脚本：把上游固定参数改成可控（便于协议冻结/审计）

- 本仓库 `third_party/FreeTimeGsVanilla/run_pipeline.sh` 增加 `MAX_STEPS/EVAL_STEPS/SAVE_STEPS`、T0 开关、`RENDER_TRAJ_*`、`EXTRA_TRAIN_ARGS` 等 env 覆盖，方便复现实验并做审计记录。

#### 2.4.4 偏差清单 C：本项目 baseline（协议 + wrapper）相对“论文/上游默认跑法”的偏差

这部分是“baseline 合理性”争议的核心，因为它不是“论文 vs vanilla 的偏差”，而是“我们现在声称的 baseline 到底是否被公平对待/是否被短预算严重扭曲”。

C1) 数据规模与拆分（baseline 最核心的实验分布偏差）

- baseline 固定数据：SelfCap bar，8 cams × 60 frames（`docs/protocol.yaml:38`）。
- 固定相机拆分：train=02–07 / val=08 / test=09（`docs/protocol.yaml:43`，并由 `scripts/run_train_baseline_selfcap.sh:26-33` 强制传参）。
- 上游默认拆分是 `test_every`（每 N 个相机留一个做 val/test），这会导致训练/验证相机集合不同，无法直接对齐。

C2) 训练预算（600 steps）与论文 30k 的量级不对齐

- baseline 强制 `MAX_STEPS=600`（`docs/protocol.yaml:61`，脚本 `scripts/run_train_baseline_selfcap.sh:20` + `--max-steps` 传入 `:80`）。
- 直接后果：大量“长训才会发生的机制”在 600 steps 内要么未发生，要么处于完全不同的收敛阶段（见 C3/C4）。

C3) SH 表达能力在 600 steps 下几乎没打开（非常关键，属于“预算诱导的表示偏差”）

- 代码：`sh_degree = min(step // cfg.sh_degree_interval, cfg.sh_degree)`（见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3676`）。
- 默认 `sh_degree_interval=1000`（config 默认值见 `:422`；baseline cfg 里也是 `sh_degree_interval: 1000`）。
- 因此当 `MAX_STEPS=600` 时：`step // 1000 == 0` 全程成立 → `sh_degree` 实际恒为 0 → 等价于“只学 DC 颜色”。
- 这与论文长训（SH 逐步到 3）不在同一收敛阶段，也意味着“600-step 的绝对 PSNR/LPIPS”很可能不具备论文级可比性。

C4) baseline 用的是 Vanilla 的 `default_keyframe_small` 配置（不是论文默认超参）

- baseline 指定 config：`default_keyframe_small`（`docs/protocol.yaml:58`；脚本 `scripts/run_train_baseline_selfcap.sh:21`）。
- 该 preset 的关键行为（在 600 steps 下会放大偏差）：
  - `lambda_4d_reg=1e-4`（baseline cfg 证据：`outputs/protocol_v1/.../baseline_600/cfg.yml:lambda_4d_reg: 0.0001`；比论文 1e-2 小两阶）
  - 几乎关闭标准 densification（`refine_start_iter=100000` 等），更接近 “pure relocation”（baseline cfg 证据：`strategy.refine_start_iter: 100000` 且 `max_steps=600`）
  - relocation 较激进：`densification_start_step=100`、`relocation_max_ratio=0.10`（baseline cfg 均可见）
  - `max_samples=5_000_000`（初始化预算更像“堆量保真”，但在短预算下未必能有效优化到位）
  - **潜在 bug（必须优先核验/可能需要修复后重跑）**：duration regularization 的 target 直接取 `cfg.init_duration`（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3772`），但 baseline cfg 是 `auto_init_duration: true` + `init_duration: -1.0` + `lambda_duration_reg: 1e-3`（`outputs/protocol_v1/.../baseline_600/cfg.yml`）。
    - 代码路径中看不到对 `cfg.init_duration` 的回写（auto 模式只是把 `effective_init_duration=-1.0` 传给 loader：`...:1791-1806`），因此 target 很可能一直是 `-1.0`。
    - 若 target 仍为 `-1.0`，则 `excess = clamp(exp(duration) - target, min=0)` 会**永远为正**，导致 duration_reg 全程强行把 durations 往最小值推（并与 `duration clamp` 等启发式交互），这会显著改变论文方法行为，并可能影响 baseline/planb 的相对结论。
- 结论：baseline 不是“论文 FreeTimeGS 的训练配方”，而是“Vanilla 为小显存/短预算调过的配方”。

C5) 初始化不是论文 ROMA；而是“SelfCap 适配 + keyframe combine + velocity scaling”

- SelfCap 适配：`scripts/adapt_selfcap_release_to_freetime.py`（把 release tarball 写成 Vanilla 期望格式）。
- keyframe combine：`scripts/run_train_baseline_selfcap.sh:67-72` 调用 `third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py` 生成 `*.npz` 初始化。
- duration 初值语义在 combine 与 trainer loader 间存在覆盖关系（可能影响时域可见性/收敛），需要在 baseline 校准时特别留意：
  - combine 内会写入 duration（例如 `combine_frames_fast_keyframes.py:430` 一带）
  - trainer 的 keyframe loader 会根据 metadata 与 `init_duration_multiplier` 重算/覆盖（参见 config 注释与相关代码段）
- 速度单位修正（m/frame → m/normalized_time）是 Vanilla 的关键实现细节（例如 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:888` 一带），论文没有以“工程对齐”形式展开，但对 motion 方程是否一致非常关键。
- **潜在不自洽 / off-by-one 风险（建议纳入 baseline 校准前的自检）**：time normalization 的分母在 “NPZ 生成器 / dataset / trainer 读 metadata” 之间并不一致。
  - NPZ 生成器（combine）：`total_frames = frame_end - frame_start + 1` 且 `t_normalized = (keyframe - frame_start) / total_frames`（`third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:424,507`）。
  - dataset：`time = frame_offset / (total_frames - 1)`（`third_party/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:642-645`）。
  - trainer 读 NPZ metadata：`npz_total_frames = npz_frame_end - npz_frame_start`（把 `frame_end` 当“exclusive”）（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:836-837,1371-1374`）。
  - 影响：`mu_t` 与训练/评测时刻 `t` 可能不对齐（末帧/末段尤其明显），并且 frame_range/duration 的 rescale 逻辑可能失真。这会让“短预算下的时序指标/正则/门控”更难解释，需要决定：修复对齐，或写成 limitation 并避免做 paper-level 对比。

C6) 评测口径与论文 SelfCap 口径不对齐

- baseline 指标：全图 `psnr/ssim/lpips(Alex)` + test 上 `tLPIPS`（协议：`docs/protocol.yaml:70-74`；实现：trainer eval）。
- 论文 SelfCap：额外给“动态区域指标”（补充材料 p.10 Sec.B.1），且表格用 LPIPS VGG / DSSIM。
- 这意味着：即使训练方法完全一致，也不能把本仓库的 scoreboard 直接与论文表格做强对比。

C7) baseline 虽叫 “vanilla”，但依赖 fork 扩展能力才能跑通协议

- baseline 脚本强制传 `--seed/--train-camera-names/--val-camera-names/--test-camera-names/--eval-on-test/--eval-sample-every-test`（见 `scripts/run_train_baseline_selfcap.sh:83-91`）。
- 上游 Vanilla trainer 不支持这些协议化参数 → baseline 不是“clone 上游 main 一键复现”的 vanilla，而是“本仓库协议化 fork”。

#### 2.4.5 这些偏差对当前项目结论的直接影响（必须在讨论中把风险清零）

1) **baseline 的“主张边界”必须被写死，否则所有对比都可被一票否决**

- 不能主张：“我们复现并改进了论文 FreeTimeGS”。
- 可以主张（已拍板，需在论文里明确）：在“协议化 fork 的 FreeTimeGsVanilla + SelfCap(bar,8x60) + 固定拆分 + 600-step 预算”的 setting 下，`planb_init_600` 相对 `baseline_600` 在 `test@step599` 提升 PSNR `+1.4992` dB、SSIM `+0.0417`，并降低 LPIPS `-0.0551`、tLPIPS `-0.0158`（见 §4.1；并解释 limitation）。

2) **短预算会让“绝对指标”缺乏论文级说服力，但不必然否定“相对改进”**

- 600 steps 下 SH/densification 等机制不激活，这会严重影响绝对 PSNR/LPIPS 的上限。
- 但如果 baseline 与 planb_init 在同一协议同一预算下对比，且改善幅度远超噪声带，那么“短预算 setting 下的 anytime 改进”仍可成立。
- 关键是：必须做最小的 convergence sanity check 来验证“差距不会在更长训练后消失”（已拍板必须做）；anytime 写法只能作为备选叙事，不能替代长训自检。

3) **baseline 可能被质疑为“没调好/配方太弱”**

- baseline preset 在 `lambda_4d_reg` 等关键超参上远离论文量级（1e-4 vs 1e-2），且引入额外正则/启发式。
- 因此必须做最小 baseline 校准（至少扫 `lambda_4d_reg`），否则“提升来自 baseline 太弱”无法排除。

4) **评测口径不对齐导致“无法对照论文表格”的问题不能回避**

- 如果导师要求对齐论文口径（动态区域指标、LPIPS(VGG)/DSSIM），就必须拍板是否补齐；否则应明确写成 limitation，并把论文对比改写为“setting 不同不可比，仅做方法启发”。

#### 2.4.6 必须执行的“最小闭环动作”（专家已拍板，强问题解决导向）

为避免继续在“是不是复现失败/是不是不收敛”上空转，下面 checklist 的目标是：把所有争议点变成**可执行任务 + 可验收产物**。

1) baseline 定义（已拍板写死）

- baseline 定义为“协议化 fork 的 FreeTimeGsVanilla baseline”，论文对比仅做“方法启发 + limitation”，不做 paper-level 复现主张。
- 不做（除非导师明确加预算并接受延期）：ROMA 初始化、动态区域评测的完整复现、30k 级别长训的论文级全对齐。

2) baseline 校准（必做最小动作）

- **先过自洽性 Gate（否则任何 sweep 都可能不可解释）**：
  - 核验/修复 `duration_reg target`（auto-init 时 `cfg.init_duration=-1` 的语义）：见上文 C4 的“潜在 bug”说明与代码指针（`...:3772`、`...:1791-1806`）。
  - 核验 time normalization / `frame_end` 语义的一致性：见上文 C5 的 off-by-one 风险与代码指针（`combine`/`dataset`/`trainer`）。
- 再做最小 smoke sweep（不改算法，只回答 baseline 是否“被配方拖弱”）：
  - 只扫 1 个关键 knob：`lambda_4d_reg`（`1e-4/1e-3/1e-2`），跑 smoke200。
  - （可选但强烈建议）加 1 个对照：`lambda_duration_reg=0`（或修复后的合理 target），用于排除“duration_reg bug/额外项主导”。
- 产出：一个表格回答 “baseline 是否显著改善/是否改变 planb 的优势幅度”，并据此决定 baseline 是否需要在主叙事里更换为“校准版 baseline”。

（可复制命令模板：baseline smoke200 sweep）

```bash
# From repo root.
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python
DATA_DIR=data/selfcap_bar_8cam60f
START_FRAME=0
END_FRAME=60
KEYFRAME_STEP=5
SEED=42

# Frozen protocol camera split.
TRAIN_CAMS=02,03,04,05,06,07
VAL_CAMS=08
TEST_CAMS=09

# 1) Build init NPZ once (reused across sweeps).
NPZ=outputs/tmp_baseline_calib/keyframes_${END_FRAME}frames_step${KEYFRAME_STEP}.npz
mkdir -p "$(dirname "$NPZ")"
$VENV_PYTHON third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
  --input-dir "$DATA_DIR/triangulation" \
  --output-path "$NPZ" \
  --frame-start "$START_FRAME" \
  --frame-end "$((END_FRAME - 1))" \
  --keyframe-step "$KEYFRAME_STEP"

# 2) Run smoke200. Repeat for each lambda_4d_reg.
# Note: set --lambda-duration-reg 0 to avoid the auto-init target ambiguity until fixed.
for L4D in 1e-4 1e-3 1e-2; do
  OUT=outputs/baseline_calib/smoke200_l4d${L4D}_dur0_s${SEED}
  CUDA_VISIBLE_DEVICES=0 $VENV_PYTHON third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
    --data-dir "$DATA_DIR" \
    --init-npz-path "$NPZ" \
    --result-dir "$OUT" \
    --start-frame "$START_FRAME" --end-frame "$END_FRAME" \
    --max-steps 200 --eval-steps 200 --save-steps 200 \
    --seed "$SEED" \
    --train-camera-names "$TRAIN_CAMS" --val-camera-names "$VAL_CAMS" --test-camera-names "$TEST_CAMS" \
    --eval-on-test --eval-sample-every 1 --eval-sample-every-test 1 \
    --lambda-4d-reg "$L4D" \
    --lambda-duration-reg 0
done

# Read metrics from:
#   outputs/baseline_calib/*/stats/test_step0199.json
```

3) 收敛性不确定性清零（二选一）

- B1：把研究问题锁定为 anytime/短预算 setting（把“600 steps + 协议冻结”写成贡献的一部分）。
- B2：做最小 convergence sanity check（baseline vs planb_init 各补 1 次 2k/5k 训练 + 多 step 打点），只回答“差距是否保持”。

4) 评测口径对齐拍板（二选一）

- M1：不对齐论文口径，明确 limitation，论文里不与论文表格做强对比，只陈述本协议下相对改进 + 解释。
- M2：补齐最关键的口径项（例如新增 “LPIPS(VGG) 评测” 或 “动态区域 proxy”），但必须写清与论文口径的差异与无法完全复现的原因（ROMA/背景 matting/GT background 等）。

---

## 3. 开题报告中的技术路线（原稿）与当前对齐情况

### 3.1 开题原路线（三主线）

开题原稿 `4D-Reconstruction.md`（历史存档）核心承诺：

1. 从 VGGT 中挖掘潜在实例语义/动态线索（聚类得到伪掩码）。
2. 基于全局注意力构建时空对应，并设计“注意力引导的对比损失”融入 4DGS 优化。
3. 构建动静解耦的 4DGS，并做可编辑性验证（例如 object removal）。

### 3.2 当前路线对齐（v2 版本）

当前对外提交版开题为 `4D-Reconstruction-v2.md`，核心变化：

- 叙事升级为“双阶段框架”，把 Plan‑B 写成阶段一物理底座，把 VGGT 写成阶段二几何语义先验。
- 评测定义收敛到 SelfCap + `PSNR/LPIPS/tLPIPS`，删去不现实的多数据集/mIoU 强承诺，改为更可落地的 scope/limitations（并保留未来可扩展的计划）。

对齐状态（逐条）：

- VGGT 线索挖掘：已交付 cue/伪掩码 + feature 本体 PCA 可视化（证据链较强）。
- 注意力/对应：已交付 token/patch top‑k 稀疏对应可视化（目前偏“可解释示意”，未进入主训练闭环）。
- 动静解耦：已交付 static/dynamic 导出视频与阈值选择说明（可直接写入论文/展示材料）。

需要导师确认的点（问题解决导向）：

- “对应 -> 对比损失 -> 指标收益”目前未形成稳定正增益。是否接受把它作为 future work？如果不接受，5 天内允许做到的最小闭环是什么（要求：能跑、可解释、可复现；不要求大规模指标提升）？

### 3.3 开题路线差距 -> 解决动作（5 天内最小闭环）

| 开题承诺/研究内容 | 当前已有证据（路径） | 差距（需要解决的问题） | 5 天内最小解决动作（可执行） | 需要导师拍板 |
|---|---|---|---|---|
| 1) VGGT 线索挖掘（伪掩码/语义线索） | `notes/protocol_v2_vggt_cue_viz.md`、`notes/protocol_v2_vggt_feature_pca.md` | 当前偏定性；缺少“为什么这些图能支撑语义/一致性”的更明确量化或对照 | 选 1 个轻量指标补齐（例如跨视角一致性/时间平滑度的统计），或补 1 个更清晰的 failure case 对照（同帧多视角局部放大） | 需要：是否必须补量化？还是定性+失败边界足够 |
| 2) 全局注意力/对应 -> 对比损失闭环 | 稀疏对应可视化：`notes/protocol_v2_sparse_corr_viz.md`；feature loss 尝试：`notes/protocol_v2_planb_feat_smoke200_owner_a.md` | 对应尚未进入训练闭环；feature loss 目前 trade-off，未改善 tLPIPS | 二选一：A) 明确把“对应进训练”作为 future work，并写清缺口与预计实现；B) 做一个最小实现（例如在 token 网格上做跨帧一致性 loss 的原型），只验证“信号是否合理/可解释”而不追求指标增益 | 需要：A/B 选哪个；若 B，允许的时间与预算 |
| 3) 动静解耦 + 可编辑性（object removal） | `notes/protocol_v2_static_dynamic_tau.md`（static/dynamic 导出） | 目前展示是“分层渲染”；object removal 的叙述与 demo 还可以更直接 | 补 1 个“移除动态层 = 背景保留”的短 demo（1 段视频 + 2-3 张帧图），并在文档里写清操作方式（如何选 tau） | 需要：导师认为现有 static/dynamic 是否已足够，还是必须补 removal demo |
| 4) 多数据集/分割指标（mIoU） | 当前主协议：SelfCap + `PSNR/SSIM/LPIPS/tLPIPS`（全图，固定拆分） | 开题承诺与现状不一致；论文 SelfCap 口径也不对齐（动态区域指标、LPIPS(VGG)/DSSIM），mIoU 需要 GT 或可靠 proxy | **已拍板**：不硬凑 mIoU；补 1 个第二场景/第二段的最小对照（`Baseline vs Plan‑B`，1 行指标 + 1 段视频）作为泛化性/anti-cherrypick 盾牌；其余写成 limitation/future work（可选：仅在新协议补 LPIPS(VGG) 或 dynamic proxy） | 仅需确认：第二场景选型；以及是否在新协议补最小指标对齐 |

---

## 4. 关键实验数据（可审计真源与摘要）

### 4.1 主表（test@step599，SelfCap canonical）

真源表：

- cross-protocol full600：`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
- 辅助解读（trade-off）：`notes/protocol_v2_stage2_tradeoff_qual.md`

关键数字（摘录）：

| run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.00720 |
| planb_feat_v2_full600_lam0.005_start300_ramp200_every16 | 20.5725 | 0.7057 | 0.3515 | 0.00756 |

结论（以解决问题为导向的解释）：

- `baseline_600 -> planb_init_600`：显著正收益（阶段一主结论）。
- `planb_init_600 -> planb_feat_v2_full600_*`：出现 trade-off（PSNR 小幅上升，但 LPIPS/tLPIPS 轻微变差）。这说明“当前这条 feature loss 的注入方式/门控方式”还没有解决目标问题（时序稳定），需要决定：停止投入，还是做一次最小补实验来验证可解释假设。

### 4.2 stage‑2 smoke200 的噪声带（用于判断“是否真实改善”）

真源：`docs/report_pack/2026-02-27-v2/README.md`（2.6 小节）。

- 观测到 seed 间 `tLPIPS` 差异上界约 `0.000685`
- 建议“可置信改善阈值”至少 `> 0.001371`（2x 噪声带），小于该量级优先视为噪声

### 4.3 Spatial metrics top‑k（逐帧空间误差的局部劣化解释）

真源：

- 快照索引：`outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599/README.md`
- 生成脚本：`scripts/viz_spatial_metrics_topk_frames.py`

top‑5（按 `delta_mae` 降序，摘录）：

| rank | frame_idx | delta_mae | delta_psnr |
|---|---:|---:|---:|
| 1 | 59 | 0.00047910 | 0.01484709 |
| 2 | 58 | 0.00044495 | 0.01573841 |
| 3 | 57 | 0.00042390 | 0.01586341 |
| 4 | 56 | 0.00038259 | 0.01675260 |
| 5 | 55 | 0.00032528 | 0.02388513 |

解释要点：top‑k 多集中在末段 `52-59`，可用于回答“为什么某些帧空间误差局部变差”（与 temporal/tLPIPS 的 top‑k 帧对互补）。

### 4.4 Temporal diff top‑k（跨帧一致性变化的锚点）

真源：`notes/protocol_v2_stage2_tradeoff_qual.md`（引用了 top‑k 帧对与 delta）。

示例锚点（摘录）：

- rank1: `frame_prev=41, frame_cur=42, delta_mean_abs_diff=+0.00034195`
- rank2: `frame_prev=37, frame_cur=38, delta_mean_abs_diff=+0.00028545`

### 4.5 动静解耦阈值 tau（用于可编辑性演示）

真源：`notes/protocol_v2_static_dynamic_tau.md`

- `p50(||v||)=0.075436`，`p90(||v||)=0.138472`
- 最终选择：`tau_final=0.075436`
- 对应导出（step599）：
  - static-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
  - dynamic-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`

### 4.6 VGGT cue / feature 的可解释数据（用于“从 VGGT 挖到了什么”）

真源：

- cue/伪掩码：`notes/protocol_v2_vggt_cue_viz.md`
- feature PCA：`notes/protocol_v2_vggt_feature_pca.md`

cue 的关键数字（摘录，来自 `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json`）：

- `mask_min=0.0`，`mask_max=0.9765`
- `temporal_flicker_l1_mean=0.00212`
- `mask_mean_per_view` 约 `0.0024~0.0079`（整体较稀疏）

### 4.7 Stage‑2（VGGT Feature Loss）超参覆盖范围（回答专家 A/B/C）

真源（含完整命令与逐次 gate 判定）：

- `notes/protocol_v2_planb_feat_smoke200_owner_a.md`
- `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

结论归类：

- 更接近 **C**：不仅跑了多组配置，还尝试了门控/降频/稀疏采样/关 conf 等变体；整体仍指向 **mixed trend / trade-off**，未出现“PSNR 与 tLPIPS 双赢且跨 seed 显著超过噪声带”的稳定候选。
- 备注：目前尝试过的 gating 主要是 `VGGT_FEAT_GATING=framediff`（top‑p 选择），尚未实现/尝试“按速度阈值只在 dynamic 区域加 loss”的版本；`gating=cue` 在 trainer 里标注但当前未实现（会 fallback to none）。

本轮已覆盖的超参范围（以实际跑过的 run 为准）：

| knob | 覆盖范围（已跑过） | 说明 |
|---|---|---|
| warmup / start step (`VGGT_FEAT_START_STEP`) | `100`, `150`, `300` | smoke200 的 `start=200` 变体被发现会导致 feature loss **不生效**（`MAX_STEPS=200` 时最后一步是 `step=199`），仅作为噪声参考，不纳入对比结论 |
| ramp steps (`VGGT_FEAT_RAMP_STEPS`) | `50`, `100`, `200`, `400` | `ramp` 从 `start_step` 起线性爬升到目标 λ |
| loss weight (`LAMBDA_VGGT_FEAT`) | `0`, `0.002`, `0.005`, `0.01` | `0` 用作可比性 sanity（feature loss 关闭） |
| feature loss frequency (`VGGT_FEAT_EVERY`) | `8`, `16` | 每 N step 才计算一次 feature loss（降低干扰/开销） |
| loss type (`VGGT_FEAT_LOSS_TYPE`) | `cosine` | 本轮固定，未再切回 `l1` |
| phi (`VGGT_FEAT_PHI_NAME`) | `token_proj` | 本轮固定（`l17, d32`），减少混杂因素 |
| confidence weighting (`VGGT_FEAT_USE_CONF`) | `1` / `0` | `noconf` 变体用于检验“conf map 是否带来负面权重偏置” |
| gating (`VGGT_FEAT_GATING`) | `none` / `framediff` | framediff 使用 cache 中的 `gate_framediff` 做 top‑p mask |
| framediff top‑p (`VGGT_FEAT_GATING_TOP_P`) | `0.10`, `0.02` | `0.02` 为更激进稀疏门控（只保留更少高变化区域） |
| patch sampling (`VGGT_FEAT_PATCH_K`, `VGGT_FEAT_PATCH_HW`) | `patch_k=0`（全图） / `patch_k=4, patch_hw=3` | 仅做过 1 个稀疏 patch 采样点，结果 gate fail（smoke200 三项全劣化） |

代表性配置（用于导师快速理解“我们到底扫到哪里”）：

- smoke200：
  - `lam=0.005, start=100, ramp=100, every=8, gating=none`
  - `lam=0.01, start=100, ramp=100, every=8, gating=none`
  - `lam=0.005, start=150, ramp=50, every=16, gating=none`（晚开 + 降频）
  - `lam=0.005, start=150, ramp=50, every=16, gating=none, use_conf=0`（noconf）
  - `lam=0.005/0.002, start=100, ramp=100, every=8, gating=framediff(top_p=0.10)`
- full600（仅两次，按预算纪律收口）：
  - `lam=0.005, start=100, ramp=400, every=8, gating=none`（触发 stoploss：PSNR/LPIPS/tLPIPS 全劣于 `planb_init_600`）
  - `lam=0.005, start=300, ramp=200, every=16, gating=none`（trade-off：PSNR↑，LPIPS/tLPIPS↑）

---

## 5. 关键实验代码（入口、职责、最小复现）

### 5.1 训练/导出入口（实验主线）

- 协议 v1（阶段一）训练入口（脚本清单见 `Progress.md`）：
  - `scripts/run_train_baseline_selfcap.sh`
  - `scripts/run_train_planb_init_selfcap.sh`
- 协议 v2（阶段二）训练入口：
  - `scripts/run_train_planb_feature_loss_v2_selfcap.sh`
- 动静解耦导出：trainer export + velocity filter（说明见 `notes/protocol_v2_static_dynamic_tau.md`）

### 5.2 报表/证据链（写作与审计必需）

- 生成 `outputs/report_pack/metrics.csv`：`scripts/build_report_pack.py`
- 生成 scoreboard：`scripts/summarize_scoreboard.py`
- 打包离线证据 tar：`scripts/pack_evidence.py`

### 5.3 关键诊断/可视化（对齐开题、支撑论文/讨论解释）

- spatial metrics top‑k 快照：`scripts/viz_spatial_metrics_topk_frames.py`
- token/patch temporal top‑k 稀疏对应可视化：`scripts/viz_tokenproj_temporal_topk.py`
- VGGT cache PCA 可视化：`scripts/viz_vggt_cache_pca.py`

### 5.4 关键测试（契约级，避免“脚本能跑但不可审计”）

- spatial top‑k 脚本契约：`scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py`
- report-pack/pack-evidence 相关：`scripts/tests/test_pack_evidence*.py`、`scripts/tests/test_summarize_scoreboard_protocol_v2.py`

---

## 6. 遇到的、亟待解决的问题（按优先级，解决问题导向）

### P0（不解决会影响项目收尾质量与后续推进）

1. 工程审计硬门槛：`manifest_match: yes`（不对齐不允许宣布冻结）
   - 当前状态：`docs/report_pack/2026-02-27-v2/manifest_sha256.csv` 与 `outputs/report_pack_2026-02-28.tar.gz` 内 `manifest_sha256.csv` 不一致（见 §6/P1-1 的 diff 说明）。
   - 目标：Day1 清零（重打 tar + 刷新 snapshot），并把“最终 tar 的路径 + git rev + manifest_match 复核命令”写死到文档里。
2. baseline 必须加固（避免被一票否决为“欠拟合/配方错误/实现 bug”）
   - 必做：`lambda_4d_reg` smoke200 sweep（`1e-4/1e-3/1e-2`）选出“校准版 baseline”。
   - blocking gate：先核验/处置 `duration_reg target` 在 auto-init 下的歧义/潜在 bug；再核验 time normalization 的 off-by-one 不一致（combine/dataset/trainer 三处语义）。
   - 输出：校准版 baseline 的 result_dir + cfg + stats + 结论（是否改变 planb 优势幅度）。
3. 收敛性不确定性必须清零：长训 convergence sanity check（强制）
   - 必做：baseline 与 planb_init 各补 1 次 2k/5k（建议 5k，若能则 10k）长训，并在多个 step 打点评估。
   - 工程纪律：v1/v2（600 steps）证据链不回写；长训结论进入新协议（建议 `protocol_v1_long` 或 `protocol_v1_convergecheck`），避免口径混用。
   - 输出：loss 曲线 + 多 step scoreboard（至少包含 2k 与 5k）+ 结论（差距是否保持/扩大/消失）。
4. 泛化/反 cherry-pick：至少补一个“第二场景或第二段”
   - 必做：第二场景（SelfCap 另一组或 Neural3DV 片段）跑通 `Baseline_full vs Plan‑B_full`。
   - 输出：一行定量 + 一段定性视频（作为论文附录/anti-cherrypick 盾牌）。
5. Stage‑2 盖棺（不再 sweep，但要把 trade-off 写硬）
   - 专家拍板：不再追加 full600 大扫参，也严禁宣称做过未实现的 gating。
   - 允许 1 次“终极衰减验证”（feature loss 前 1/4 强引导，后 3/4 指数衰减到 0）：成功则形成策略；失败则作为 Failure Analysis 铁证并停止投入。
6. scope 文案统一（避免开题承诺与交付口径打架）
   - 多数据集/mIoU 不硬凑；用“第二场景/第二段 + limitation/future work”闭环开题差距，并与 `4D-Reconstruction-v2.md`/Q&A 同步一致。

### P1（影响可复现/可审计质量，可能造成交付被质疑）

1. 离线证据包与 manifest 快照需要稳定对齐（`manifest_match` 必须以脚本复核为准），避免出现“tar 与 docs 快照不一致”的审计风险。
   - 现状（本工作区复核）：`docs/report_pack/2026-02-27-v2/manifest_sha256.csv` 与 `outputs/report_pack_2026-02-28.tar.gz` 内的 `manifest_sha256.csv` **不一致**（例如 `README.md`、`docs/README.md` 的 sha 不同，且 tar 内清单包含的文件集合也有差异）。
2. GitHub HTTPS 连接在部分环境会出现 443 timeout（A/B 之前曾阻塞）。建议保留可离线交付路径（bundle/patch）并把 checklist 固化在文档里。
3. doc/notes 之间存在“更新不同步”的风险（例如某些 note 需要补 `How to run` 的最小命令段），需要收尾期统一梳理入口与复现命令。

---

## 7. 待确定的实现细节、代码细节（请导师/同行重点评审）

1. feature metric loss 的最终可复现/可写入论文定义：
   - loss 施加对象：rendered feature vs GT feature？按像素、按 patch，还是按可见 gaussians 加权？
   - warmup/ramp 与 lambda 候选：当前 schedule 是否合理，是否需要更保守的 ramp 或 region mask？
2. 对应（correspondence）的可实现闭环：
   - 目前有 token temporal top‑k 可视化，但未进入训练主线。
   - 若要进入主线，如何加入几何约束/窗口约束，避免“噪声对比学习”？
3. patch/token 到 gaussians 的绑定方式：
   - 候选：利用 rasterizer splatting 权重完成像素-高斯自然绑定；或导出 gaussian-id map 再做 hard assignment。
   - 需要明确实现选择与复杂度（显存/速度）评估。
4. 动静解耦与 object removal 的展示定义：
   - `tau` 是否固定全局，还是每段/每 ckpt 自适应？
   - “慢动目标被分到 static”如何作为失败边界解释，是否需要补 1 个更直观的 removal demo？
5. “显著改善”的统计准则：
   - smoke200 的 seed 噪声带如何写入实验章节（避免把噪声当收益）？
   - 是否需要固定“至少 2 seeds 同向改善 + 幅度超过噪声带阈值”作为宣称条件？
6. baseline 与评测口径的最终写法（会直接影响“baseline 是否合理”的争议是否闭环）：
   - baseline 的正式定义是否写为“本仓库协议化 fork 的 FreeTimeGsVanilla”（而不是“论文 FreeTimeGS 复现”）？
   - 是否需要（或可在 5 天内）补齐论文 SelfCap 的动态区域评测口径、以及 LPIPS(VGG)/DSSIM 等指标对齐？若不补齐，limitation/future work 如何写才算“问题被解决”？

---

## 8. 详细规划：未来 5 天收尾（2026-03-01 至 2026-03-05），确保 2026-03-06 前“基本完成项目”

目标定义（专家已拍板，见 `professional-decisions.md`）：到 2026-03-06 结束时，项目必须满足“证据链可审计 + 关键风险清零 + 可写可答辩 + 可复现交付”。

### 8.1 2026-03-06 Code Freeze DoD（写死，不满足不允许宣布冻结）

1. 一张主表（scoreboard）：包含 baseline / planb_init /（若有）stage‑2 封棺 run /（若有）第二场景对照的最小集合，并清楚标注协议与 step。
2. 一段定性视频：必须包含动静解耦 / object removal（或等价演示），并能在现场解释“做了什么/没做什么”。
3. 一页解释性图：trade-off/Pareto/失败边界（即使是负结果也必须能解释“为什么会这样”）。
4. 一份 SHA256 锁定的证据包（tar + `manifest_sha256.csv` + `git_rev.txt`）。
5. **硬门槛**：`manifest_match: yes`（tar 内 manifest 与 docs 快照一致）。否则冻结无效。
6. 一页 Runbook：复现命令 + 预期输出（用于导师抽查与现场演示）。

### 8.2 3 GPU / 3 人并发执行表（3/1–3/5，按 `suggestions.md` + `professional-decisions.md`）

#### Day 1（3/1）：工程审计清零 + 为三条战线开工

- Owner C（GPU-2/CPU）：重打 evidence tar + 刷新 `docs/report_pack/.../manifest_sha256.csv`，把 `manifest_match: yes` 清零。
- Owner A（GPU-0）：baseline 加固前置自检（`duration_reg` 处置方案、time normalization/off-by-one 自检脚本/打印），准备校准 sweep 的 init NPZ 复用。
- Owner B（GPU-1）：第二场景选型与数据适配，先跑通 baseline（先把 pipeline 跑起来）。

#### Day 2（3/2）：baseline 校准 sweep + 新协议骨架落盘

- Owner A（GPU-0）：做 baseline smoke200 sweep（`lambda_4d_reg=1e-4/1e-3/1e-2`，并明确 `duration_reg` 处置），产出“校准版 baseline”。
- Owner C（CPU）：完成 time normalization/off-by-one 风险的端到端自检结论，决定“是否修复到新协议”（不回写旧证据链）。
- Owner B（GPU-1）：第二场景 baseline 继续跑通到可评测（至少拿到 `stats/test_*.json` + 1 段视频）。

#### Day 3–4（3/3–3/4）：三条并发主战（长训收敛 + 第二场景 + Stage‑2 封棺）

- GPU-0（Owner A）：跑 `Baseline_long vs Plan‑B_long`（5k 起步，能到 10k 更好），并在多个 step 打点评估。
- GPU-1（Owner B）：第二场景跑 `Baseline_full vs Plan‑B_full`，输出一行数据 + 定性视频（附录/反 cherry-pick 盾牌）。
- GPU-2（Owner C）：执行 1 次“指数衰减权重”的 Stage‑2 终极试探（可先 smoke200 看趋势再 full600；full600 只有在 smoke200 趋势成立才触发）。无论成功/失败，都要产出可写的证据材料。

#### Day 5（3/5）：收口与冻结准备

- Owner C（CPU）：重打一份最终证据包，锁定 SHA256；把 Runbook 写成 1 页；同步入口文档路径。
- Owner A（GPU-0）：输出长训的收敛曲线与多 step 对照表，并给出“是否保持优势”的结论句（用于论文与答辩）。
- Owner B（GPU-1）：输出第二场景的对照表与关键帧/视频，并把 limitation/scope 写法与开题 v2/Q&A 对齐。

---

## 9. 论文时间表（你提供的节奏，补充具体产出）

### 2026-03-06 至 2026-03-11：边写边补实验

- 目标：完成 Method/Experiment 框架与主要图表插入；仅补“导师明确要求”的最小实验。

### 2026-03-12：初稿

- 目标：形成可读通稿（包含：动机、方法、实验、结论、局限）。

### 2026-03-13 至 2026-03-21：润色与补实验（若需要）

- 目标：压缩不必要的承诺、强化可审计证据链叙事；补实验必须服务于“解决 3.3 中被拍板的差距/关键问题”，不做发散探索。

### 2026-03-22：定稿

- 目标：文本、图表、引用路径、复现命令完全一致。

---

## 10. 建议找同行/专家/导师的原因与讨论议程

建议：需要尽快找一次讨论/对齐（越早越好）。专家已拍板大方向（见 `professional-decisions.md`），本次会议的目标不再是“防守式辩论”，而是把剩余未定项变成可执行任务，并明确验收标准与失败止损。

原因（仍需要人来“确认即可执行”的点）：

- 第二场景/第二段的选型与可用性（影响泛化性与 anti-cherrypick 的最小闭环）。
- 长训协议（`protocol_v1_long`）的 step 打点与资源预算（影响“600 steps 不收敛”的致命质疑能否被彻底封死）。
- Stage‑2 “终极衰减验证”的参数与触发规则（避免变成新一轮扫参）。
- 工程交付（manifest/tar 对齐、离线 fallback）是否按 DoD 清零。

建议议程（30-45 分钟，以“明确行动计划与验收”为输出）：

1. 对照 §0.2 的未定项逐项确认：第二场景选哪个、长训打点评估点取哪些、是否补最小指标口径对齐（仅限新协议）。
2. 对照 §8.1 的 DoD：确认 3/6 冻结时必须交付哪些产物、谁负责、怎么验收。
3. 对照 §8.2 的并发执行表：确认 Owner A/B/C 的任务边界与止损规则（尤其 Stage‑2 只允许 1 次封棺 run）。
4. 针对工程交付：确认最终证据包的 source-of-truth 与 `manifest_match` 复核命令。

---

## 11. 关键参考文件（导师若要追溯，可直接按路径打开）

- 同行建议（并发作战表）：`suggestions.md`
- 专家拍板（DoD + 决策）：`professional-decisions.md`
- 进度总览：`Progress.md`
- 对外开题（v2）：`4D-Reconstruction-v2.md`
- 决议：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- 协议：`docs/protocols/protocol_v2.yaml`
- report-pack 入口：`docs/report_pack/2026-02-27-v2/README.md`
- 主表：`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
- baseline/论文/上游/fork 偏差（同行补充）：`docs/reviews/2026-03-01/baseline-paper-vanilla-deviations-peer-provided.md`
- baseline 风险定位（工作底稿）：`docs/reviews/2026-03-01/freetimegs-paper-vs-freetimegsvanilla-deviations.md`
- 动静解耦：`notes/protocol_v2_static_dynamic_tau.md`
- VGGT cue：`notes/protocol_v2_vggt_cue_viz.md`
- VGGT feature PCA：`notes/protocol_v2_vggt_feature_pca.md`
- 稀疏对应：`notes/protocol_v2_sparse_corr_viz.md`
- stage‑2 trade-off 说明：`notes/protocol_v2_stage2_tradeoff_qual.md`
- spatial top‑k 快照索引：`outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599/README.md`
