# Align Opening Proposal (4D-Reconstruction.md) — Phased Alignment Plan

> **Execution Note:** 这是一个“强 timebox + 强可复核”的计划；默认只做最小闭环与最小对照，避免把任何单阶段做成无底洞。

**Goal:** 以“3–5 天一个阶段”的节奏，把当前仓库对齐到“原版开题 `4D-Reconstruction.md` × v2 现实可执行约束 `4D-Reconstruction-v2.md`”的**折中目标**：
1) **Plan‑B（速度初始化）作为阶段一主线**（工作量饱满 + 可审计 + 结论硬）；  
2) **VGGT（几何语义先验）作为阶段二主线**（优先争取指标提升；不行则产出可解释的 failure boundary）；  
3) **可编辑性（动静解耦/移除）必须可演示**；  
4) **mIoU 仅在“存在可信 GT 的公开数据集”时启用**（你可接受 **二值前景 silhouette/matte** 的 GT 作为 mIoU 口径）；否则明确不做 mIoU（写 limitation/未来工作），不让它阻塞主线推进。

**Architecture:** 不回写/不污染既有 `protocol_v1/v2` 证据链；所有“向开题原版对齐”的新增实验统一开新协议 `protocol_v3_openproposal`（或更高版本）+ 新输出目录 `outputs/protocol_v3_openproposal/...`。每阶段都有“退出条件（Gate）”，过不了就写 limitation 并止损，而不是无底洞烧卡。

**Tech Stack:** 本仓库 runners（`scripts/run_train_*.sh`）、`third_party/FreeTimeGsVanilla` fork、VGGT（推理/缓存）、聚类（k-means/谱聚类可选）、稀疏 token top‑k 对应、PyTorch loss 注入、`pytest` 合约测试、report-pack（`build_report_pack.py`/`pack_evidence.py`）。

**Protocol Hygiene:** 为避免污染既有证据链：
- 新增 `docs/protocols/protocol_v3_openproposal.yaml` 作为本计划唯一协议入口（只描述 v3 实验）；`docs/protocol.yaml` 仍保持指向 `protocol_v1` 不动。

---

## Feasibility Review（结合 `4D-Reconstruction-v2.md` 的可行性复核）

先把“能对齐/不能对齐/需要改口径”说清楚，避免按计划推进到一半才发现目标本身不成立。

### 已经在 v2 路线里基本对齐的点（不需要重复造轮子）

- “双阶段叙事”（Plan‑B 物理底座 + VGGT 软先验）：`4D-Reconstruction-v2.md:11`
- 动静解耦（static-only / dynamic-only）定性证据：`4D-Reconstruction-v2.md:71`
- VGGT 可解释材料（cue/特征 PCA/稀疏对应可视化）在 v2 证据链里已有落盘指针：`4D-Reconstruction-v2.md:78`
- “注意力/对应”在 v2 中已被**重新定义为可实现版本**（patch/token + top‑k 稀疏）：`4D-Reconstruction-v2.md:24`

> 结论：Phase 2/4 如果继续做，应当只补“原版开题强承诺里缺的那一截”（例如 instance‑level 伪掩码、loss 落地），而不是重复做 PCA/可视化。

### 与 v2 口径天然冲突、很难“完全对齐”的点（必须先决定是否真的要追）

1) **“Neural3DV/Multi‑Human + mIoU”作为主口径**  
   - 原版开题写了 `Neural3DV/Multi-Human + mIoU` 并且用“优于”措辞：`4D-Reconstruction.md:23`  
   - v2 已把评测改为 SelfCap + tLPIPS，并删除 mIoU/多数据集强承诺：`4D-Reconstruction-v2.md:29`  
   - 现实风险：公开数据集是否自带可用 **dataset-provided mask** 不确定；不过你可接受 **二值前景**（silhouette/alpha/matte）作为 mask 口径，因而不必强求 instance‑level 标注。没有 mask 就做不了“mIoU”（除非引入外部模型做伪 GT，但那会让口径更难 defend）。

2) **“VGGT 全局注意力 → 跨帧像素对应矩阵 → 对比损失”的字面实现**  
   - 原版开题写的是像素级对应矩阵与注意力引导对比损失：`4D-Reconstruction.md:38`–`4D-Reconstruction.md:39`  
   - 字面实现通常是 (HW)^2 级别，工程上很容易直接不可用；v2 选择的是 token/patch + top‑k 稀疏化作为可执行替代。  

3) **“实例分割图渲染通道 + 可微监督通道”的工程量**  
   - 原版开题明确要改 rasterizer 导出实例分割图与深度图：`4D-Reconstruction.md:33`  
   - 这件事如果要做得“可微 + 可复现 + 不崩性能”，通常不是 3–5 天级别（除非你现成就有 multi-channel rasterizer/输出接口）。

4) **“物体移除（编辑）”在“无背景图”的前提下很难做到“干净的背景补全”**  
   - 你可以做“删掉某类 Gaussians 后渲染”的 removal demo，但如果背景从未被观测到，会出现洞/残影；需要提前把 limitation 写进计划与论文。

> 建议：把上述 4 点全部标记为“高风险/需先拍板的对齐目标”。如果你不愿意推翻 v2 口径，那 Phase 1/5 就应当改成“可选扩展”，否则就是计划与文档目标自相矛盾。

### 已锁定的 3 个决定（写死，避免后续摇摆）

1) **双主线：Plan‑B + VGGT**  
   - Plan‑B 作为“更硬的主结论”（更可审计/更稳）；VGGT 作为“更偏创新/更可能提升指标”的第二主线。
2) **mIoU：只在公开集自带 dataset-provided mask 时做 `miou_fg`**  
   - 允许 **二值前景**（silhouette / alpha / matte）。  
   - 公开数据集若提供的 mask 来自自动 matting/分割，也允许作为“dataset‑provided GT”，但必须在报告里写清其来源（避免误称人工标注）。
3) **注意力/对应：接受 token 相似度 / 稀疏 top‑k 替代像素全连接**  
   - 不追求 `(HW)^2` 的像素级对应矩阵；以可跑通 + 可解释的稀疏版本为准。

## Phase 1（3–5 天）：把“公开数据集 + 指标口径”跑通（先解决“对齐开题但没法评测”的根问题）

**关键对齐点：** 开题原版要求在 `Neural3DV / Multi-Human` 上做定量（含 mIoU）`4D-Reconstruction.md:23`、`4D-Reconstruction.md:46`。

**目标（人话）：** 先别谈新方法，先把“在 1 个公开场景上能复现实验、能跑指标、能写表”打通，否则后面所有方法都没落点。

**可行性警告（结合 v2）：**
- v2 的主口径并不依赖 mIoU；因此本阶段的“硬目标”应当是：**至少跑通 1 个公开数据集的训练+评测闭环**（哪怕先只做 PSNR/LPIPS/tLPIPS），而不是把 mIoU 当成硬门槛。
- mIoU 的最大风险是 **GT 不存在/不可获取** 或 **适配成本爆炸**；因此必须设置 Day2 之前的硬止损：拿不到可信 GT 就删掉 mIoU 线，继续推进 Phase 2–4。

**Deliverables（阶段交付）：**
- 公开数据集选型（至少 1 个），并写清“为什么适合本仓库”：
  - 必选：multi-view（≥4 views）+ 时间序列（能支撑 4D），且能落到 data contract（或可在 1–2 天内写 adapter）。
  - mIoU 选做：仅当 dataset 自带 **dataset-provided mask**（二值前景 silhouette/alpha/matte 即可；instance 标注更好）。
- 推荐“带 dataset-provided mask 的公开小数据”（用于 `psnr_fg/lpips_fg/miou_fg` 口径落地，而不必替换主数据线）：
  - **THUman4.0**（multi-view 视频 + 官方提供 `masks/` + `calibration.json`；`masks/` 为前景分割，数据集说明其由 BackgroundMattingV2 得到）。下载说明见其数据集仓库 README。
  - 默认建议：先选下载体量最小的 `subject00`，再裁剪成 `8 cams × 60 frames`（优先对齐 SelfCap 的 8cam60f 规模，便于算力预算与复用 runner）。
  - 备选（如果 THUman4.0 下载/协议/体积卡住）：优先找“同样带 `masks/` 的多视角视频数据”，例如 PKU‑DyMVHumans（提供 `pha/` 粗前景分割与可选相机参数）。
  - 数据合规（按你确认：**只做本地评测**）：多数人体多视角数据集对“再分发/打包上传”有严格限制；因此本计划将公开集视为 **local-eval only**，并写死以下规则：
    - 不在 git 提交/PR/report-pack 中包含原始帧与原始 masks（包括任何 GT side-by-side 视频/拼图）。
    - report-pack 只保留：指标 CSV/JSON、训练 cfg、脚本与 manifest、以及不包含 GT 画面的统计/诊断图（例如曲线、差分热力图、mask 覆盖率统计）。
    - 若需要定性对比（render vs GT），只在本机 `outputs/qualitative_local/` 留存，文档只写本地路径，不进入证据链。
- 选定 1 个“有可用 dataset-provided mask 的子任务”来承载 mIoU（若找不到 mask，直接标记本阶段 mIoU = No‑Go，不拖延）。
- 新增/完善 1 个数据适配入口（把公开数据转成仓库 data contract：`images/ + sparse/0 + triangulation/`）。
  - 推荐最稳落地：对裁剪后的 THUman 子集跑一次 COLMAP（生成 `sparse/0`），再用 `scripts/export_triangulation_from_colmap_sparse.py` 生成 `triangulation/`（先用 `static_copy` 烟雾通过，再切到 `visible_per_frame` 提升质量）。
  - 关键约束：COLMAP 的相机命名必须与 `images/<camera_folder>/...` 文件夹名逐字节一致（否则会造成 GT/render 错位；`FreeTimeParser` 会打印 mismatch 警告）。
  - 若 COLMAP 在该子集上失败：止损策略是“换子集/换相机集合/缩小帧数”，而不是无底洞调参；必要时再考虑用 dataset calibration 构造 COLMAP model 的工程化方案（作为后续增强，不阻塞 Phase 2–4）。
- 新增 1 个评测脚本：输出统一 JSON/CSV，并**写死字段名**（避免 Phase 4 “提升”不可复核）：
  - 默认实现为**离线 evaluator**（读渲染图/GT 图/mask，计算并落盘）；不改 trainer 训练/渲染逻辑，避免把 Phase 1 变成“改训练框架”。
  - full-frame：`psnr`, `ssim`, `lpips`, `tlpips`
  - dataset-provided mask（reference；若存在）：`psnr_fg`, `lpips_fg`（= foreground-masked 主结论口径；若 mask 是“动态区域”则更贴近 FreeTimeGS dynamic-region，否则就是 silhouette ROI；mask 允许二值前景 silhouette/alpha/matte）
    - 推荐：若数据集提供 alpha/matte，先保留原始 alpha，再用固定阈值（默认 0.5）派生 binary mask，用于 `miou_fg` 与 bbox 计算，避免口径漂移。
  - ROI-proxy（若无 dataset-provided mask 也要有）：`psnr_roi_proxy`, `lpips_roi_proxy`, `roi_proxy_source`（值域建议固定为 `framediff_gate|pseudo_mask`；并在表格列名中保留 `_proxy` 后缀，禁止混淆为 GT）
  - 分割指标：`miou_fg`（仅当 **dataset-provided mask 存在 + 预测 mask 定义明确** 时启用；否则写 No-Go，不用 proxy 冒充 mIoU）
    - `miou_fg` 的默认定义（避免后续争议）：  
      - `gt_fg`：数据集提供的前景 mask；若为 alpha/matte，则用阈值 0.5 转二值。  
      - `pred_fg`：Phase 2 产出的 `outputs/cue_mining/<tag>/pseudo_masks.npz:masks`；阈值 0.5 转二值（或作为 baseline 先用 `framediff_gate` 产生的 binary ROI）。  
      - 计算：逐帧逐视角 IoU 后取 mean（跳过 NaN/缺失帧）。
- 明确 masked 指标计算口径（写进 Phase 1 文档）：`mask -> bbox crop (+margin) -> mask 外填黑 -> 算 LPIPS/PSNR`（render 与 GT 同样处理）；bbox 为空则该帧 masked 指标记为 NaN 并在统计时跳过（避免“置零背景”引入边界伪差）。
- bbox crop 的 `margin` 先固定为 **32px**（可复核优先；如后续发现图像分辨率很小再改口径并重跑）。
- 注：FreeTimeGS 论文的 dynamic-region 评测（SelfCap）使用的是“先得到动态区域 mask，再用 bbox crop，并把 mask 外填黑”的口径；本计划的 `psnr_fg/lpips_fg` 采用同一精神（有 dataset-provided mask 时尽量对齐该口径）。
- 1 次 baseline（或 planb_init）短跑（smoke 级）+ 产物可审计（cfg + stats + 可播放视频）。
  - 子集冻结要求（按你确认的策略：不预猜相机命名，下载后冻结）：  
    - 在 adapter 输出目录落盘 `adapt_manifest.csv`（或等价清单），写清：`subject_id / camera_ids / frame_range / image_ext / 分辨率`  
    - 在 `notes/openproposal_phase1_dataset_and_metrics.md` 写清：`train/val/test split` 的确定性规则（默认：相机名排序后取前 6 个为 train、第 7 个为 val、第 8 个为 test），保证可复现。
  - 缺帧处理（避免训练脚本假设连续帧导致直接崩）：若原始数据存在 `missing_img_files.txt` 或部分视角缺帧，adapter 必须输出一个“冻结的 frame id 列表”，并把选中的帧重编号为连续 `000000..`（同时保证 `images/` 与 `masks/` 同步对齐）。

**Exit Criteria（过闸门才能进 Phase 2）：**
- 新数据场景能通过最小训练（例如 200/600 steps）并生成 `stats/test_step*.json`。
- 若 dataset-provided mask 存在：`psnr_fg/lpips_fg` 跑通且口径写清（bbox crop + margin）。
- 若计划启用 `miou_fg`：必须写清 “预测 mask 来自哪里/如何生成”，并让 `miou_fg` evaluator 对该预测源跑通；否则把 `miou_fg` 标记为本阶段 No‑Go/Pending（不阻塞 Phase 2–4）。
- 写 1 页短文档：`notes/openproposal_phase1_dataset_and_metrics.md`（解释：数据来源、GT 从哪来、为什么指标合理）。

---

## Phase 2（3–5 天）：把“VGGT 实例线索/伪掩码挖掘”做成开题口径（先做证据图，再做收益）

**关键对齐点：** 开题原版的第 1 条主线：VGGT 特征→聚类→实例级伪掩码，并有“动态过滤/边缘细化”描述 `4D-Reconstruction.md:17`、`4D-Reconstruction.md:34`–`4D-Reconstruction.md:36`。

**目标（人话）：** 让你能在答辩时拿出一组图说清楚：VGGT 里确实有“跨视角更一致的实例线索”，并且伪掩码不是拍脑袋。

**Deliverables（阶段交付）：**
- 新增一个“开题口径”的 cue mining 模块（建议先 k‑means；谱聚类作为可选增强，严格 timebox）：
  - 输入：多视角多帧图像（沿用现有 VGGT cache/推理接口）。
  - 输出：`pseudo_masks.npz`（至少满足二值前景/动态 ROI；instance K 类作为可选增强，不要让它阻塞 Phase 3/4）。
  - 输出格式必须与 trainer 的 pseudo-mask contract 对齐（`masks/camera_names/frame_start/num_frames/mask_downscale`，形状 `[T,V,Hm,Wm]`，值域 `[0,1]`）。
- 动态过滤（最小可实现版）：用特征/深度的时间方差或相邻帧差做动态抑制/增强（要可视化）。
- 边缘细化（最小可实现版）：基于 depth/梯度做边界收缩/扩张或引导滤波（不追“论文级”，追“可复现可解释”）。
- 产出一套固定的可解释图（3–5 帧 × 2–3 个视角）：overlay、簇图、失败例。

**Exit Criteria：**
- `outputs/cue_mining/<tag>/viz/` 下有可检查的 overlay/cluster 图；且质量统计（全黑/全白/噪声）不触发止损。
- `pseudo_masks.npz` 必须通过最小 QA（写 `outputs/cue_mining/<tag>/stats/mask_summary.json` 并在文档里引用）：
  - 全局/逐相机：mask 平均覆盖率不退化为全 0 或全 1（例如 `mean in (0.001, 0.999)`，且空/满帧占比接近 0）
  - 逐帧：随机抽样 overlay 不出现“整屏噪点/花屏”；失败例必须落盘并解释
- 若 Phase 1 已具备 dataset-provided mask：额外做一次 `miou_fg` 体检（不设硬阈值，但禁止退化到“接近随机”），并在 Phase 2 文档中记录：
  - `miou_fg(pred=pseudo_masks_vggt, gt=dataset_mask)`
  - `miou_fg(pred=pseudo_masks_diff, gt=dataset_mask)`（作为 cheap baseline 参照）
- 写 1 页短文档：`notes/openproposal_phase2_vggt_pseudomask.md`（说明：算法、参数、失败例、为什么它算“实例线索挖掘”）。

---

## Phase 3（3–5 天）：把“伪掩码真正用进训练闭环”（弱监督先闭环，别一上来做强对比学习）

**关键对齐点：** 开题原版强调“在框架内部产生并利用中间监督信号”，而不是只做离线可视化 `4D-Reconstruction.md:11`。

**目标（人话）：** 伪掩码要么能带来可观察收益（哪怕很小），要么形成清晰的 failure analysis；两者都算“对齐”，但不能停留在“我画了几张图”。

**Deliverables：**
- 在 `protocol_v3_openproposal` 下跑 1 个最小对照：
  - baseline/planb_init（不开伪掩码）
  - weak‑mask 注入（用 Phase 2 的 instance mask 做权重或初始化约束）
- 输出：同一场景同一步数的指标对照表 + 1 段 side‑by‑side 定性视频（指出哪里变好/变坏）。
- 预期管理（写进结论）：本仓库的 weak fusion（当前实现）本质是 **对重建损失做 reweight**，并不等价于“显式分割监督”；因此本阶段的硬交付是“闭环 + 可解释结论”，而不是承诺必然带来指标提升。
- 若无收益/指标变差：写清楚“为什么没收益”（mask 质量/时序不稳/约束方向不对/权重调度问题），并给出下一步改法；严格 timebox，**不让 Phase 3 把 Phase 4 拖死**。

**Exit Criteria：**
- 至少得到一个可辩护结论：`weak 用/不用` 的差异（正/负都可，但要可审计）。
- 写 1 页短文档：`notes/openproposal_phase3_weak_supervision_result.md`（含路径与结论）。

---

## Phase 4（3–5 天）：落地“注意力/对应 → 对比损失”（先做稀疏可算版本，严格控制复杂度）

**关键对齐点：** 开题原版第 2 条主线：VGGT 全局注意力→跨帧对应→注意力引导对比损失 `4D-Reconstruction.md:18`–`4D-Reconstruction.md:39`。

**目标（人话）：** 做出一个“跑得动、算得清、可视化能自证不是噪声”的对比学习/一致性约束，并且**优先尝试提升 LPIPS/PSNR**（不提升就产出可解释的 failure boundary + 排查记录），而不是写一个 (HW)^2 的不可实现设计。

**Deliverables：**
- 稀疏对应（最小可实现定义写死）：
  - token/patch 级（不是像素级）
  - 相邻帧优先（t 与 t+1），每个 token 取 top‑k（k=1~4）正样本
  - 负样本：同帧其他 token 或跨帧低相似 token（写清楚）
- 对比/一致性损失（两条二选一，先易后难）：
  - A) 对渲染出来的 feature map 做 token‑level consistency（最稳）
  - B) InfoNCE（更贴近“对比损失”，但更容易不稳）
- 实现顺序建议：**优先 VGGT feature metric loss**（仓库已支持、闭环最稳）把闭环跑通并争取 `LPIPS/PSNR` 改善；只有在它明确不够用时，再考虑 temporal corr / InfoNCE（避免把 Phase 4 变成“新框架研发”）。
- 环境准备：允许下载并缓存 VGGT 权重；建议显式设置 `VGGT_MODEL_ID=facebook/VGGT-1B` 与 `VGGT_CACHE_DIR=<path>`，并在 Phase 4 开始前做一次 warmup 下载，避免训练中途卡住。
- 对应质量可视化：随机抽样 + top‑k overlay（必须有，否则无法答辩“你在对齐谁”）。
- 指标导向的最小对照（只做 1–2 组，不开无底洞 sweep）：
  - 对照：`planb_init` vs `planb_init + corr/contrastive`
  - 优先看：`LPIPS/PSNR`（full-frame + foreground-masked；后者是主结论口径）
  - Guardrail：同时看 `tLPIPS`（或等价的时序稳定 proxy）。如果 `LPIPS/PSNR` 变好但 `tLPIPS` 明显恶化，只能作为 trade-off 展示，不能当“纯提升”结论。
  - 若指标不动：按下述排查清单做“原因归因”，并给出 stop/next 的明确决策

**排查清单（当 LPIPS/PSNR 不提升时，按顺序排查，严格 timebox）：**
1) **评测对齐**：确认同一 `eval/save step list`、同一渲染配置、同一帧采样；同时看 full-frame 与 fg-masked，避免“背景主导导致看不出提升”。
2) **对应质量**：看 top‑k overlay 是否像对应；统计相似度分布/命中率；过滤 out-of-view/遮挡/无效 token。
3) **loss 标度与归一化**：检查 feature 是否 `L2 norm`、temperature、loss 归一化项；确保辅助 loss 梯度不压过 photometric/geometry 主损失。
4) **调度与门控**：`start_step / ramp / every_n` 是否太早太强（导致 PSNR 掉）或太晚太弱（无效）。
5) **稀疏度**：top‑k（1~4）与 token 网格分辨率（ds/patch）是否过稀/过密；先固定一个稳定组合再谈 sweep。
6) **正负样本定义**：避免正样本“自匹配”或负样本过易；必要时把负样本限制在同视角/同时间窗口，减少噪声。
7) **稳定性**：出现 NaN/爆显存/发散就先降 `lambda_*` 或增大 warmup；必要时加 grad clip（但要写清理由）。
8) **解释性证据**：挑选 top‑ΔLPIPS/ΔPSNR 帧做 side‑by‑side 图 + temporal diff/误差热力图，证明“loss 在约束什么”。
9) **止损**：最多 2 轮“改一个变量”的迭代仍无改善 → 写 failure boundary（在哪些场景/设置下无效）并停在 Phase 4（不要拖到 Phase 5）。

**Exit Criteria：**
- 训练能稳定跑过 smoke 预算（不爆显存、不 NaN）；对应可视化“看起来像对应”，而不是满屏乱连。
- 至少给出一个“可审计的指标结论”：
  - A) 争取 **同时提升** `lpips_fg`（↓）与 `psnr_fg`（↑）；若无法两者同时提升，则必须给出“trade-off + 归因证据”，并锁定配置/路径；或
  - B) 明确“未提升”的 failure boundary + 归因证据（对应质量/权重调度/归一化/采样等），并写清止损点。
- Guardrail：如出现 `tLPIPS` 明显恶化（默认阈值可先参考 smoke200 的 `ΔtLPIPS <= +0.01`），必须在结论里标红并给出原因归因；不允许把它写成“单调提升”。
- 写 1 页短文档：`notes/openproposal_phase4_attention_contrastive.md`（定义、复杂度、指标结果、失败例、排查与下一步）。

---

## Phase 5（3–5 天）：补齐“实例/深度通道 + mIoU + 可编辑性（物体移除）”的最终闭环

**关键对齐点：** 开题原版第 3 条主线：动静显式分离 + 编辑（物体移除），并以“分割精度 mIoU”等评测支撑 `4D-Reconstruction.md:19`、`4D-Reconstruction.md:23`。

**目标（人话）：** 让“mIoU/可编辑性”不再是口号：给出一个明确的预测对象（mask/instance field）、明确的 GT、明确的计算方式，以及一个可播放的编辑 demo。

**可行性拆分建议（避免 Phase 5 过载）：**
- Phase 5A（优先做，3–5 天内更现实）：**可编辑性 demo**（instance removal）+ limitation（无背景图→可能有洞）。
- Phase 5B（只有 GT 明确时再做）：**mIoU 闭环**（否则会卡在 GT/标注，导致整阶段失效）。
  - 明确：**不把 multi-channel rasterizer（实例/深度可微通道）当作 Phase 5 必做**；它属于 stretch goal（若现有代码路径已支持导出非可微通道，则可作为加分项补齐开题措辞，但不作为 gate）。

**Deliverables：**
- 定义并实现一个“可评测的 mask 输出”：
  - 最小版本：**前景 vs 背景二值 mask（你已接受）**（或 K 类 instance mask，取决于 Phase 2/3 输出）
  - 输出方式：渲染/投影得到 per-pixel mask（不要求完美，但要确定义）
- `miou_fg`（二值前景 IoU；GT 允许 silhouette/alpha/matte）：
  - 写清 GT 来源（数据自带 / mesh 投影 / 少量人工标注），并把生成脚本纳入仓库。
- 编辑 demo：
  - 最小可交付：按 instance id 或 mask 选择一类 Gaussians 做“删除并渲染背景”视频（不要求 inpaint，但要说明局限）。
- 最终汇总 1 张表 + 1 段视频 + 1 张解释图（对齐开题“可验证交付”）。

**Exit Criteria：**
- 在至少 1 个公开场景上产出：`miou_fg` 数值 + 编辑视频 + 复现命令（runbook）。
