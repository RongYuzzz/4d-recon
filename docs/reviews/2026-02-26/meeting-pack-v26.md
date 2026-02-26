# 4d-recon 会议包（v26，Plan-B 主线收口与写作排期拍板）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
v26 report-pack 快照 commit：`ad63158`（`docs(report-pack): snapshot v26 aligned with template-hygiene reruns`）  
会议目标：**当场拍板**“单一路线 +（可选）新增算力预算 + 止损线 + 未来 7 天排期表”。

---

## 0) 本次会议必须当场输出（写死）

### 0.1 主线（只能选 1 条）

- 选项 A：**Plan‑B 作为唯一主线**，进入写作冲刺（默认推荐）
- 选项 B：Plan‑B 主线 + 追加极少量验证性 full600（必须写死次数与成功线）
- 选项 C：回到 feature-loss v2（需要证明“确有可修根因”，否则不讨论）

### 0.2 算力预算（写死数字）

- full600 追加预算：`N=?`（当前决议预算 `N=3` 已用尽，见 `Progress.md`）

### 0.3 验收与止损线（写入决议文件）

- 若允许新增 full600：每次 full600 的 **成功线/止损线**必须写死（见下文建议）

### 0.4 7 天排期（谁做、做几次、哪天出结论/图/稿）

---

## 1) 一页结论（可直接口头汇报）

1. `feature-loss v2`：**No‑Go 冻结**（post-fix full600 三项全劣化），只保留 No-GPU 失败归因链用于写作防守。
2. `Plan‑B`：**Go**（不改 `protocol_v1`，仅替换 init velocities），canonical full600 与 seg200_260 full600 均显著正向；多段 seg smoke200 同向，已形成 anti-cherrypick 防守链。
3. `Plan‑B + weak cue`：smoke200 证据不足，**No‑Go**，不建议为此申请新增 full600。
4. 预算：按既有决议，未来 7 天 full600 预算已用尽（剩余 0）；任何新增 full600 必须新建/升级 `docs/decisions/*`。
5. full600 已有关键证据（目录级，可审计）：canonical `baseline_600/planb_init_600`；seg200_260 `baseline_600/control_weak_nocue_600/planb_init_600`；feature-loss `feature_loss_v2_postfix_600`。

---

### 1.1 本版相对旧材料的关键增量（避免会上信息不同步）

1. `seg300_360` anti-cherrypick 证据已补齐（smoke200，且按 template hygiene：slice baseline init 做模板，仅替换 velocities）。
2. `seg400_460` 与 `seg1800_1860` 已完成 re-template 重跑，确保“模板来自 canonical”的质疑被排除后仍同向增益。
3. `scripts/summarize_planb_anticherrypick.py` 已升级：`seg600_660` 存在时仍额外显示 `seg300_360` section（不再二选一 fallback）。
4. v26 report-pack 快照已对齐 re-template 口径（以 `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md` 为准）。

---

## 2) 唯一引用口径与证据入口（会中建议统一指向这些）

协议真源（固定不动）：`docs/protocols/protocol_v1.yaml`

进度总览（含预算状态）：`Progress.md`

v26 报表快照（建议作为“唯一引用口径”）
- `docs/report_pack/2026-02-26-v26/scoreboard.md`（canonical 主表，含 v2/weak/planb）
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`（seg 防守链总表）
- `docs/report_pack/2026-02-26-v26/metrics.csv`（可追溯到每个 run_dir）
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`（证据清单，含 stats/video/qualitative）

写作入口（当前草案）
- `notes/planb_verdict_writeup_owner_b.md`
- `docs/writing/planb_paper_outline.md`

evidence tar（本地可分发，不入库）
- `artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz`
- SHA256：`43e04974f95d4628c02cc7b65e5fbf44db4fd82329e306ec082a57dd90102536`（已登记 `artifacts/report_packs/SHA256SUMS.txt`）

### 2.1 快速自检命令（可选，5 分钟，避免“会上争论口径”）

1. 校验 v26 tar 的 SHA（应与 `SHA256SUMS.txt` 一致）：
```bash
cd /root/projects/4d-recon
rg -n "report_pack_2026-02-26-v26" artifacts/report_packs/SHA256SUMS.txt
sha256sum artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz
```

2. 从主阵地 `outputs/` 重新生成 `outputs/report_pack`（不需要 GPU）：
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md
python3 scripts/summarize_planb_anticherrypick.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md
```

3. 快速 spot-check（期望出现的 delta）：
- `outputs/report_pack/planb_anticherrypick.md` 中必须包含：
- `seg400_460`：ΔPSNR `+0.1845` / ΔLPIPS `-0.0481` / ΔtLPIPS `-0.0516`
- `seg1800_1860`：ΔPSNR `+0.1799` / ΔLPIPS `-0.0489` / ΔtLPIPS `-0.0549`
- `seg300_360`：ΔPSNR `+0.1811` / ΔLPIPS `-0.0497` / ΔtLPIPS `-0.0517`

### 2.2 指标与口径简表（防止会上概念不一致）

- PSNR/SSIM/LPIPS：单帧画质指标（越高/越高/越低越好）。
- tLPIPS：时序稳定性指标（test 视角的跨帧一致性；越低越好）。
- Δ 的定义：本文档所有 “Δ” 统一指 `planb - baseline`（同 slice、同 step、同 stage）。
- smoke200 vs full600：smoke200 仅用于预算中性趋势判断；full600 才是最终验收口径（canonical 与 seg200_260 已有 full600）。

### 2.3 关键代码与执行入口（若被问“怎么跑出来的”）

- Plan‑B 初始化脚本：`scripts/init_velocity_from_points.py`
- Plan‑B runner：`scripts/run_train_planb_init_selfcap.sh`
- baseline runner：`scripts/run_train_baseline_selfcap.sh`
- 执行文档（含 Gate 纪律）：`docs/execution/2026-02-26-planb.md`
- 定性 runbook：`docs/execution/2026-02-26-planb-qualitative.md`
- anti-cherrypick 汇总脚本：`scripts/summarize_planb_anticherrypick.py`
- evidence 打包脚本：`scripts/pack_evidence.py`

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

### 3.3 关键 run_dir 路径（可追溯到产物目录）

Canonical（full600）
- baseline：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/`
- planb：`outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/`
- feature-loss v2：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/`

anti-cherrypick（seg）
- seg200_260 full600：`outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/{baseline_600,planb_init_600}/`
- seg400_460 smoke200：`outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/{baseline_smoke200,planb_init_smoke200}/`
- seg600_660 smoke200：`outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/{baseline_smoke200,planb_init_smoke200}/`
- seg300_360 smoke200：`outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/{baseline_smoke200,planb_init_smoke200}/`
- seg1800_1860 smoke200：`outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/{baseline_smoke200,planb_init_smoke200}/`

Plan-B init 自检产物（Gate‑S1）
- canonical：`outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json`
- seg200：`outputs/plan_b/selfcap_bar_8cam60f_seg200_260/velocity_stats.json`
- seg300：`outputs/plan_b/selfcap_bar_8cam60f_seg300_360/velocity_stats.json`
- seg400：`outputs/plan_b/selfcap_bar_8cam60f_seg400_460/velocity_stats.json`
- seg600：`outputs/plan_b/selfcap_bar_8cam60f_seg600_660/velocity_stats.json`
- seg1800：`outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/velocity_stats.json`

### 3.4 Gate‑S1 自检摘要（用于防守“初始化是否离谱”）

来源：各 slice 的 `outputs/plan_b/*/velocity_stats.json`（字段：`counts.match_ratio_over_eligible`、`clip_threshold_m_per_frame`、`n_clipped`）。

| slice | match_ratio_over_eligible | clip_threshold_m_per_frame | clip_thr vs canonical | n_clipped |
| --- | ---: | ---: | ---: | ---: |
| canonical | 0.6029 | 0.010881 | 1.0000x | 514 |
| seg200_260 | 0.5923 | 0.010960 | 1.0072x | 507 |
| seg300_360 | 0.5956 | 0.011564 | 1.0627x | 507 |
| seg400_460 | 0.5887 | 0.011362 | 1.0442x | 498 |
| seg600_660 | 0.5863 | 0.011418 | 1.0493x | 495 |
| seg1800_1860 | 0.5791 | 0.011623 | 1.0682x | 490 |

解读（口径）：
1. match_ratio 均远高于 Gate 阈值 0.05，说明 mutual NN 匹配不是“靠侥幸”。
2. clip_threshold 与 canonical 同量级（约 1.0x~1.07x），未出现 10x 异常。

### 3.5 机制证据（组件消融，来自 `notes/planb_component_ablation_smoke200_owner_a.md`）

- 明确必要组件：**mutual NN**  
  `planb_ablate_no_mutual_smoke200` 相对 default：ΔPSNR `-0.0534` / ΔLPIPS `+0.0097` / ΔtLPIPS `+0.0135`（一致退化）。
- `drift_removal` 与 `clip`（0.99->0.95）在该 smoke200 窗口影响较小，更像鲁棒性调节项。

### 3.6 定性证据（evidence tar 已收录，可用于答辩/组会）

视频与关键帧（见 `docs/report_pack/2026-02-26-v26/manifest_sha256.csv` 中 `outputs/qualitative/planb_vs_baseline/*`）：
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`（canonical，full600）
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`（seg200_260，full600）
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg600_660_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000000.jpg`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000030.jpg`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000059.jpg`

---

## 4) 待拍板问题（需要专家/导师决策）

### 4.1 论文/答辩主目标

- 是否“必须有可量化正向提升”？若允许，Plan‑B 已满足；feature-loss 作为负结果归因链补充即可。
- 是否接受把 feature-loss 的负结果作为“方法边界/失败分析”放入附录（不再消耗预算）？

### 4.2 可接受的“证据强度”

- 现有证据：canonical full600 + seg200 full600 + 多段 seg smoke200（含 template hygiene）+ 定性视频 + 组件消融。
- 是否需要额外验证：例如 1 次额外 full600 复现、或另一个场景/数据集验证？

### 4.3 是否需要扩 full600 预算

- 当前 full600 预算为 0（见 `Progress.md` 与 `docs/decisions/2026-02-26-planb-pivot.md`）。
- 若导师要求进一步加固：必须新增决议并写死 `N` 与成功线/止损线。

### 4.4 已知瑕疵与一致性声明（避免会上被“挑文档”打断）

- v26 的权威数值口径（会议引用数字时以此为准）：
- `docs/report_pack/2026-02-26-v26/metrics.csv`
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
- `docs/report_pack/2026-02-26-v26/scoreboard.md`
- `docs/report_pack/2026-02-26-v26/ablation_notes.md`、`docs/report_pack/2026-02-26-v26/failure_cases.md` 属于写作型文本，可能存在历史标题残留；引用数字时请以上述三份为准。

---

## 5) 建议拍板方案（供会议直接选）

### 5.1 推荐方案：Plan‑B 主线 + 进入写作冲刺（不新增 full600）

- 主线：Plan‑B（v26 证据为唯一引用口径）。
- full600：不追加（除非导师明确要求）。
- 未来 7 天交付（建议）：
- 写作：论文/答辩稿 v1（结构、核心表、anti-cherrypick 附录、失败分析）。
- 图表：canonical 主表 + anti-cherrypick 表 + side-by-side 抽帧（或短视频链接）。
- 防守：template hygiene、mutual NN ablation、feature-loss 负结果归因链。

### 5.2 若必须追加 full600（强制写死纪律）

- 只允许“验证性”而非探索性跑数（否则必发散）。
- 预算上限建议：`N<=1`（最多 1 次 full600）。
- 唯一目的：复现性或跨 seed 验证 `planb_init_600`。
- 成功线（建议沿用决议口径，不改 protocol）：Go = tLPIPS 相对 baseline_600 下降 ≥ 5% 且 PSNR 不劣化超过 0.2 dB；No‑Go = PSNR/LPIPS/tLPIPS 三项全劣化或训练不稳。
- 若 No‑Go：立即停止新增训练，回到写作冲刺（把失败写清楚）。

### 5.3 仍可做的“零预算补强”（不新增 full600）

- 补齐吞吐证据覆盖：部分旧 run（如 `baseline_600`）可能缺少 `stats/throughput.json`；对缺失 run 目录运行 `python3 scripts/write_throughput_json.py <run_dir>` 即可补齐（No-GPU，不需要重训）。
- 出一版“答辩/组会图表小集合”：canonical 主表截图、anti-cherrypick 表、side-by-side mp4 的 3 帧抽帧（frame_000000/000030/000059）。
- 文档清洁（可选）：若担心“历史标题残留”被抓住，可在不改实验数值前提下生成 v27 快照，修正文稿标题与叙事引用（同时重新 pack evidence 并登记 SHA）。

---

## 6) 建议会议议程（45 分钟）

1. 5 min：对齐本次要拍板的 4 项输出（主线/预算/止损线/排期）
2. 10 min：事实快照（v26 scoreboard + anti-cherrypick 表）
3. 10 min：风险与防守（template hygiene、mutual NN ablation、feature-loss 负结果归因链）
4. 15 min：拍板（是否追加 full600、写作交付物范围、deadline）
5. 5 min：会后落地（更新/新增 `docs/decisions/*`，冻结计划并执行）

---

## 7) 会后落地要求（避免“拍板不落地”）

### 7.1 若确认“不追加 full600”

- 在决议中写明“写作冲刺期禁止新增训练”的纪律。

### 7.2 若追加 full600

必须新建/更新 `docs/decisions/*`，并写死：
- 新增 full600 的次数 `N`
- 每次 full600 对应的唯一 run 名称/seed/命令入口
- 成功线与止损线
- 结论产出截止时间（到点无论正负都收口）

---

## 8) 专家/导师常见质疑与准备回答（建议会议现场直接用）

1. Q：你们是不是 cherry-pick？  
A：canonical full600 + seg200_260 full600 是主证据；另外 seg300/400/600/1800 多段 smoke200 同向，并且 seg400/1800 做了 template hygiene re-template 后仍同向。证据：`docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`、`notes/anti_cherrypick_seg*.md`。

2. Q：Plan‑B 到底改了什么？会不会偷偷改协议？  
A：不改 `protocol_v1` 与数据分布项，只替换 init velocities 来源（triangulation -> 3D velocity init），其余训练超参/相机划分/帧数不变。证据：`docs/protocols/protocol_v1.yaml`、`docs/execution/2026-02-26-planb.md`、`scripts/run_train_planb_init_selfcap.sh`。

3. Q：Plan‑B 是不是靠“速度从 0 变成非 0”投机？  
A：我们不使用“零速陷阱已证实”的表述，严格口径是 velocity prior 的质量/尺度/一致性不足或噪声过大导致动态不稳；Plan‑B 提供更物理一致的 3D 差分速度先验。证据：`notes/planb_verdict_writeup_owner_b.md`、`docs/writing/planb_paper_outline.md`。

4. Q：提升是否以算力/速度为代价？  
A：当前 evidence tar 已能审计每个 run 的 stats/video/定性对比；吞吐证据若缺失可 No-GPU 补齐，不需要重训。建议把“是否允许补齐吞吐证据并写入写作”作为会后动作之一。
