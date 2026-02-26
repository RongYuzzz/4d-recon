# 4d-recon 会议包（v26，Plan-B 主线收口与写作排期拍板）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
当前主线 commit：`ad63158`（`docs(report-pack): snapshot v26 aligned with template-hygiene reruns`）  
会议目标：**当场拍板**“单一路线 +（可选）新增算力预算 + 止损线 + 未来 7 天排期表”。

---

## 0) 本次会议必须当场输出（写死）

1. 主线（只能选 1 条）
- 选项 A：**Plan‑B 作为唯一主线**，进入写作冲刺（默认推荐）
- 选项 B：Plan‑B 主线 + 追加极少量验证性 full600（必须写死次数与成功线）
- 选项 C：回到 feature-loss v2（需要证明“确有可修根因”，否则不讨论）

2. 算力预算（写死数字）
- full600 追加预算：`N=?`（当前决议预算 `N=3` 已用尽，见 `Progress.md`）

3. 验收与止损线（写入决议文件）
- 若允许新增 full600：每次 full600 的 **成功线/止损线**必须写死（见下文建议）

4. 7 天排期（谁做、做几次、哪天出结论/图/稿）

---

## 1) 一页结论（可直接口头汇报）

1. `feature-loss v2`：**No‑Go 冻结**（post-fix full600 三项全劣化），只保留 No-GPU 失败归因链用于写作防守。
2. `Plan‑B`：**Go**（不改 `protocol_v1`，仅替换 init velocities），canonical full600 与 seg200_260 full600 均显著正向；多段 seg smoke200 同向，已形成 anti-cherrypick 防守链。
3. `Plan‑B + weak cue`：smoke200 证据不足，**No‑Go**，不建议为此申请新增 full600。
4. 预算：按既有决议，未来 7 天 full600 预算已用尽（剩余 0）；任何新增 full600 必须新建/升级 `docs/decisions/*`。

---

## 2) 唯一引用口径与证据入口（会中建议统一指向这些）

1. 协议真源（固定不动）：`docs/protocols/protocol_v1.yaml`
2. 进度总览（含预算状态）：`Progress.md`
3. v26 报表快照（建议作为“唯一引用口径”）
- `docs/report_pack/2026-02-26-v26/scoreboard.md`（canonical 主表，含 v2/weak/planb）
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`（seg 防守链总表）
- `docs/report_pack/2026-02-26-v26/metrics.csv`（可追溯到每个 run_dir）
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`（证据清单，含 stats/video/qualitative）
4. 写作入口（当前草案）
- `notes/planb_verdict_writeup_owner_b.md`
- `docs/writing/planb_paper_outline.md`
5. evidence tar（本地可分发，不入库）
- `artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz`
- SHA256：`43e04974f95d4628c02cc7b65e5fbf44db4fd82329e306ec082a57dd90102536`（已登记 `artifacts/report_packs/SHA256SUMS.txt`）

---

## 3) 关键结果（v26，核心数字）

### 3.1 Canonical（full600，test@599，来自 `docs/report_pack/2026-02-26-v26/scoreboard.md`）

| Run | PSNR | SSIM | LPIPS | tLPIPS | 相对 baseline_600 |
| --- | ---: | ---: | ---: | ---: | --- |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 | — |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 | ΔPSNR `+1.4992` / ΔLPIPS `-0.0551` / ΔtLPIPS `-0.0158` |
| feature_loss_v2_postfix_600 | 18.6752 | 0.6562 | 0.4219 | 0.0261 | ΔPSNR `-0.2744` / ΔLPIPS `+0.0172` / ΔtLPIPS `+0.0031`（No‑Go） |

补充风险信号（weak）：`control_weak_nocue_600` 的 LPIPS 优于 `ours_weak_600`（cue 注入存在负增益风险）。

### 3.2 anti-cherrypick（来自 `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`）

| Slice | 预算 | 指标步数 | ΔPSNR | ΔLPIPS | ΔtLPIPS |
| --- | --- | ---: | ---: | ---: | ---: |
| Canonical | full600 | 599 | +1.4992 | -0.0551 | -0.0158 |
| seg200_260 | full600 | 599 | +1.9950 | -0.0604 | -0.0156 |
| seg400_460 | smoke200 | 199 | +0.1845 | -0.0481 | -0.0516 |
| seg600_660 | smoke200 | 199 | +0.1905 | -0.0488 | -0.0525 |
| seg300_360 | smoke200 | 199 | +0.1811 | -0.0497 | -0.0517 |
| seg1800_1860 | smoke200 | 199 | +0.1799 | -0.0489 | -0.0549 |

说明：
- `seg400_460` 与 `seg1800_1860` 已完成 template hygiene（slice 自己的 baseline init 做模板，仅替换 velocities）后仍同向增益。
- 以上切片的定性 side-by-side（mp4/jpg）已被 v26 evidence 收录（见 `manifest_sha256.csv` 中 `outputs/qualitative/planb_vs_baseline/*`）。

### 3.3 机制证据（组件消融，来自 `notes/planb_component_ablation_smoke200_owner_a.md`）

- 明确必要组件：**mutual NN**  
  `planb_ablate_no_mutual_smoke200` 相对 default：ΔPSNR `-0.0534` / ΔLPIPS `+0.0097` / ΔtLPIPS `+0.0135`（一致退化）。
- `drift_removal` 与 `clip`（0.99->0.95）在该 smoke200 窗口影响较小，更像鲁棒性调节项。

---

## 4) 当前最大的不确定性（需要专家/导师拍板）

1. 论文/答辩主目标
- 是否“必须有可量化正向提升”？若允许，Plan‑B 已满足；feature-loss 作为负结果归因链补充即可。
- 是否可以把 feature-loss 的负结果作为“方法边界/失败分析”放入附录（不再消耗预算）？

2. 可接受的“证据强度”
- 现有证据：canonical full600 + seg200 full600 + 4 段 seg smoke200（含 template hygiene）+ 定性视频 + 组件消融。
- 需要额外验证吗：例如 **1 次额外 full600 复现**或 **另一个场景/数据集**验证？

3. 是否需要扩 full600 预算
- 当前 full600 预算为 0（见 `Progress.md` 与 `docs/decisions/2026-02-26-planb-pivot.md`）。
- 若导师要求进一步加固：必须新增决议并写死 `N` 与成功线/止损线。

---

## 5) 建议拍板方案（供会议直接选）

### 推荐方案（默认）：Plan‑B 主线 + 进入写作冲刺（不新增 full600）

1. 主线：Plan‑B（v26 证据为唯一引用口径）
2. full600：不追加（除非导师明确要求）
3. 未来 7 天交付：
- 写作：完成论文/答辩稿 v1（结构、核心表、anti-cherrypick 附录、失败分析）
- 图表：canonical 主表 + anti-cherrypick 表 + side-by-side 关键帧（或短视频链接）
- 防守：template hygiene、mutual NN ablation、feature-loss 负结果归因链

### 若必须追加 full600（强制写死纪律）

只允许“验证性”而非探索性跑数（否则必发散）：
- 预算上限建议：`N<=1`（最多 1 次 full600）
- 唯一目的：复现性或跨 seed 验证 `planb_init_600`
- 成功线（建议沿用决议口径，不改 protocol）：
  - Go：tLPIPS 相对 baseline_600 下降 ≥ 5%，且 PSNR 不劣化超过 0.2 dB
  - No‑Go：PSNR/LPIPS/tLPIPS 三项全劣化或训练不稳
- 若 No‑Go：立即停止新增训练，回到写作冲刺（把失败写清楚）

---

## 6) 建议会议议程（45 分钟）

1. 5 min：对齐本次要拍板的 4 项输出（主线/预算/止损线/排期）
2. 10 min：事实快照（v26 scoreboard + anti-cherrypick 表）
3. 10 min：风险与防守（template hygiene、mutual NN ablation、feature-loss 负结果归因链）
4. 15 min：拍板（是否追加 full600、写作交付物范围、deadline）
5. 5 min：会后落地（更新/新增 `docs/decisions/*`，冻结计划并执行）

---

## 7) 会后落地要求（避免“拍板不落地”）

1. 若确认“不追加 full600”：在决议中写明“写作冲刺期禁止新增训练”的纪律。
2. 若追加 full600：必须新建/更新 `docs/decisions/*`，写死：
- 新增 full600 的次数 `N`
- 每次 full600 对应的唯一 run 名称/seed/命令入口
- 成功线与止损线
- 结论产出截止时间（到点无论正负都收口）

