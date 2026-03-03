# Baseline / FreeTimeGS（论文）/ FreeTimeGsVanilla（上游 + fork）偏差补充（同行审核提供，逐条保留）

说明：
- 本文件为同行审核后补充的“三者对齐对象 + 三层偏差清单（A/B/C）”，用于回答 `mentor-discussion-brief.md` 中的两个基础可信度问题：
  - baseline 是否合理（到底在对齐论文，还是对齐社区实现，还是对齐本项目 fork + 协议）？
  - 极短训练（600 steps）下的结论是否能支撑主张（哪些 schedule 在该预算下根本不会被激活）？
- 文中引用的论文路径为本机：`/tmp/papers/freetimegs_arxiv_2506.05348.pdf`。
- 文中引用的代码路径以本仓库为准（`third_party/FreeTimeGsVanilla/...`、`scripts/...`、`docs/protocol.yaml`）。
- 该文档按同行原文尽量保留；未逐条复核的地方建议在讨论时现场打开对应文件核验。

---

## 对齐对象（先把三者“到底是什么”说清楚）

- 论文 FreeTimeGS（arXiv:2506.05348）：方法框架在 Sec.3（尤其 p.4 的 3.2/3.3）与补充材料 p.10 的 B 节给了关键公式/超参/评测口径（见 `/tmp/papers/freetimegs_arxiv_2506.05348.pdf`）。
- 开源 FreeTimeGsVanilla（上游 GitHub）：本仓库用快照 `third_party/FreeTimeGsVanilla-main.tar.gz` 对齐上游 main；它是“基于 gsplat 的最小实现”，但不等于论文训练/评测协议（比如 keyframe/sampling/λ 等）。
- 本项目 baseline：协议冻结在 `docs/protocol.yaml:11`，baseline 名为 `baseline_freetime_vanilla`（`docs/protocol.yaml:75`），实际入口脚本是 `scripts/run_train_baseline_selfcap.sh`，跑的是本仓库 `third_party/FreeTimeGsVanilla/`（注意：这里的 third_party 已对上游做了补丁）。

---

## 偏差清单 A：论文 FreeTimeGS ↔ 上游 FreeTimeGsVanilla（“复现层面”偏差）

### A1. 初始化链路（论文强调 ROMA；Vanilla 不含 ROMA）

- 论文：每帧用 ROMA 做多视角 2D matches→三角化 3D 点；点+时间初始化 (µx, µt)；再用 kNN 匹配两帧 3D 点，位移作速度 v（`/tmp/papers/...pdf` p.4 Sec.3.2）。
- Vanilla：不实现 ROMA；要求你已产出 triangulation/`points3d_frame*.npy`（`third_party/FreeTimeGsVanilla/README.md` 的 Input Requirements + Pipeline Overview），并用 `src/combine_frames_fast_keyframes.py` 做“keyframe 组合+速度估计”（`third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:467` 起）。
- 关键偏差：Vanilla 的默认思路是“keyframe-only + velocity bridging”（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1312`），论文正文没有 keyframe/stride 叙事（在 PDF 全文检索不到 keyframe/stride）。

### A2. keyframe/采样/预算策略（论文未给；Vanilla 做了工程化近似）

- Vanilla 的 combine：只取 keyframes，但速度用 keyframe 的 “下一帧 t→t+1” 的点云做 KDTree 匹配（`third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:468`、`third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:489`），这不是论文文字描述的“任意相邻两帧/逐帧”初始化。
- Vanilla 的 “Smart sampling”（密度/速度/中心加权）是纯工程策略（`third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:548`，以及 trainer 里的 `smart_sample_points/use_smart_sampling`），论文 p.4/3.2-3.3 不包含这一块。

### A3. 训练步数（论文 30k@300 帧；Vanilla 有多套默认）

- 论文：300 帧序列训练 30k iter（`/tmp/papers/...pdf` p.4 Sec.3.3）。
- 上游 Vanilla：`run_pipeline.sh` 固定跑 30000（上游快照里就是 30000；本仓库 fork 也保留但改成可配，见下文）；但 trainer 的 `Config.max_steps` 默认是 70000（上游快照 `src/simple_trainer...` 中有该默认值）。

### A4. 4D regularization 权重（论文 1e-2；Vanilla 默认更小）

- 论文：`lambda_reg = 1e-2`（`/tmp/papers/...pdf` p.4 Sec.3.3）。
- Vanilla：`lambda_4d_reg` 默认 1e-3（且注释明确 “Paper value 1e-2，降到 1e-3”），见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:456`。

### A5. “只评测动态区域”的口径（论文 SelfCap 有；Vanilla 无）

- 论文（补充材料）：SelfCap 报两套指标：全图 & 仅动态区域；动态区域通过 GT background + Background Matting V2 得 mask，再按 bbox crop 并外部填黑（`/tmp/papers/...pdf` p.10 Sec.B.1）。
- Vanilla：无“动态区域评测”管线；默认直接全图算 PSNR/SSIM/LPIPS（见 eval 实现 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:4123`）。

### A6. 指标/网络细节（论文表格用 DSSIM、SelfCap 用 LPIPS(VGG)；Vanilla 默认 SSIM、LPIPS(Alex)）

- 论文补充材料表格：SelfCap 用 LPIPS VGG（`/tmp/papers/...pdf` p.10 Table 8 描述）。
- Vanilla：默认 `lpips_net="alex"`（上游也如此；本仓库 fork 同样默认），见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:734`；并用 ssim 而不是表格里的 DSSIM（实现里是 `self.ssim(...)`，见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:4188`）。

---

## 偏差清单 B：上游 FreeTimeGsVanilla ↔ 本仓库 third_party/FreeTimeGsVanilla（“本项目 fork 补丁”偏差）

同行使用 `diff -qr` 对比上游快照 `third_party/FreeTimeGsVanilla-main.tar.gz` 与本仓库 fork，主要改了 3 个文件（另有 `.venv/egg-info/__pycache__` 等本地产物）：

### B1. Trainer：新增“协议化评测/相机拆分/额外 loss/审计开关”

- 显式 seed + cudnn deterministic：`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1682`。
- 显式 train/val/test 相机名（上游只有 test_every）：`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:314`，以及映射逻辑 `...:1718`。
- 新增 test 评测开关与 test 采样频率：`...:409`（`eval_sample_every_test/eval_on_test`），并在训练循环里触发（`...:4115`）。
- 新增 tLPIPS（只在 test 且 `sample_every_test=1` 时计算）：`...:4149` 到 `...:4199`。
- 新增弱/强/特征损失接口（baseline 通过权重=0 关闭，但代码已存在）：
  - pseudo mask：`...:464`
  - temporal corr：`...:477`
  - VGGT feature metric：`...:499`
- 新增 T0 审计/退化开关（force v=0 + grad/日志）：`...:451`。

### B2. Dataset：补齐真正的 val split（上游把 val 当 test 用）

- 本仓库：`FreeTimeDataset` 支持 `split="train/val/test"` 且独立 `val_set`（`third_party/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:528`）。
- 上游：只有 `test_set`，trainer 里 valset 实际等同“held-out cameras”，没有独立 test。

### B3. Pipeline 脚本：把上游固定参数改成可控（便于协议冻结/审计）

- 本仓库 `third_party/FreeTimeGsVanilla/run_pipeline.sh` 增加 `MAX_STEPS/EVAL_STEPS/SAVE_STEPS`、T0 开关、`RENDER_TRAJ_*`、`EXTRA_TRAIN_ARGS` 等 env 覆盖（文件 diff 里已体现）。

---

## 偏差清单 C：本项目 baseline（协议 + wrapper）相对“论文/上游默认跑法”的偏差

### C1. 数据规模与拆分（baseline 最核心的“实验分布偏差”）

- 本项目 baseline 固定数据：SelfCap bar，8 cams×60 frames（`docs/protocol.yaml:38`）。
- 相机拆分固定为 train=02–07 / val=08 / test=09（`docs/protocol.yaml:43`；脚本传参 `scripts/run_train_baseline_selfcap.sh:26`）。
- 上游默认拆分是 `test_every`（每 N 个相机留一个做 val/test），会导致“训练/验证相机集合不同”，不可直接对齐（上游逻辑在快照里）。

### C2. 训练预算（600 steps）与论文 30k 的量级不对齐

- baseline 强制 `MAX_STEPS=600`（`docs/protocol.yaml:61`，脚本 `scripts/run_train_baseline_selfcap.sh:20` + `--max-steps` 传入 `scripts/run_train_baseline_selfcap.sh:74`）。
- 这会引出一串“隐含偏差”（见 C3-C5）。

### C3. SH 表达能力在 baseline 里几乎没打开

- SH 退火：`sh_degree = min(step // sh_degree_interval, sh_degree)`（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3675`）。
- 默认 `sh_degree_interval=1000`（上游也如此），所以跑 600 steps 时 `sh_degree` 全程为 0 → 等价于“只学 DC 颜色”，与论文长训（会逐步到 3）不对齐。

### C4. baseline 用的是 Vanilla 的 `default_keyframe_small` 配置（不是论文默认超参）

- baseline 指定 config：`default_keyframe_small`（`docs/protocol.yaml:58`；脚本 `scripts/run_train_baseline_selfcap.sh:21`）。
- 该 config 的关键取值（直接决定行为）：
  - `max_samples=5_000_000`（初始化预算更像“堆量保真”，`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:4769`）
  - `lambda_4d_reg=1e-4`（比论文 1e-2 小两阶，`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:4805`）
  - “关闭标准 densification”（`refine_start_iter=100_000` 等），改为“pure relocation”（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:4787`、`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:4795`）
  - relocation 更激进：`densification_start_step=100`、`relocation_max_ratio=0.10`（同上配置段）
- 结论：baseline 不是“论文 FreeTimeGS 的训练配方”，而是“Vanilla 为小显存/短预算调过的配方”。

### C5. 初始化不是论文 ROMA；而是“SelfCap 适配 + keyframe combine + velocity scaling”

- SelfCap 适配：`scripts/adapt_selfcap_release_to_freetime.py`（把 release tarball 写成 Vanilla 期望格式）。
- keyframe combine：`scripts/run_train_baseline_selfcap.sh:67` 调用 `third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py`。
- combine 的 duration 初值是 3x gap（`third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:430`），但在 keyframe loader 里会被覆盖成 `gap * init_duration_multiplier(=2)`（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1411`、`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1547`）。
- 速度单位修正（m/frame→m/normalized_time）是 Vanilla 的关键实现细节：`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:888`（论文里没有以“工程 bugfix”形式展开，但对对齐 motion 方程很关键）。

### C6. 评测口径与论文 SelfCap 口径不对齐

- baseline 指标：全图 psnr/ssim/lpips + test 上 tLPIPS（`docs/protocol.yaml:70`；实现见 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:4149`）。
- 论文 SelfCap：额外给“动态区域指标”（`/tmp/papers/...pdf` p.10 Sec.B.1），且表格用 LPIPS VGG（`/tmp/papers/...pdf` p.10 Table 8 描述）；baseline 默认 LPIPS Alex（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:734`）。

### C7. baseline 虽叫 “vanilla”，但依赖 fork 扩展能力才能跑通协议

- baseline 脚本强制传 `--seed/--train-camera-names/--val-camera-names/--test-camera-names/--eval-on-test/--eval-sample-every-test`（见 `scripts/run_train_baseline_selfcap.sh:83` 到 `scripts/run_train_baseline_selfcap.sh:91`），这些参数上游 Vanilla trainer 不支持（因此 baseline 不是“直接 clone 上游 main 就能复现”的那个 vanilla）。

