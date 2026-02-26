# Owner B 计划：失败归因最小包补齐 + Writing Mode v20（No‑GPU）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner B（No‑GPU）  
并行约束：Owner A 使用 GPU0 做 Plan‑B 组件消融 smoke200，本计划可并行推进；仅在 **v20 打包**步骤需要等 A 的新 smoke200 产物落地到主仓 `outputs/`。

## 0. 目标（面向“完成项目”）

1. 把 `docs/reviews/2026-02-26/meeting-decision.md` 要求的 **feature‑loss 失败归因最小包**补到“可审计、可引用”的程度（不新增 full600，不追求修好 feature‑loss）。  
2. 在 A 产出 Plan‑B 组件消融 smoke200 后，刷新 report-pack/evidence 到 **v20**，让“Plan‑B 机制解释”材料进入证据链。

## 1. 不可违反的纪律

- 不使用 GPU（所有任务 CPU/IO）。
- 不新增任何训练（尤其 full600）；只做分析/统计/写作/打包。
- `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库；只提交 `docs/`、`notes/`、`scripts/`、`scripts/tests/`。

## 2. 交付物（可验收）

入库交付（必须）：
- 新增失败归因工具脚本与测试：
  - `scripts/analyze_vggt_gate_framediff.py`
  - `scripts/analyze_phi_shift_sensitivity.py`
  - `scripts/tests/test_analyze_vggt_gate_framediff.py`
  - `scripts/tests/test_analyze_phi_shift_sensitivity.py`
- 更新失败归因最小包文档（把“待补”变为“已补/证据路径”）：
  - `notes/feature_loss_failure_attribution_minpack.md`
- v20 文本快照（包含 Plan‑B 组件消融结论入口）：
  - `docs/report_pack/2026-02-26-v20/{metrics.csv,scoreboard.md,ablation_notes.md,failure_cases.md,manifest_sha256.csv}`
- 更新 SHA 登记：
  - `artifacts/report_packs/SHA256SUMS.txt`（新增 `report_pack_2026-02-26-v20.tar.gz` 的 sha256 行）

不入库但必须生成（用于 evidence tar 收录）：
- `outputs/report_pack/diagnostics/` 下的 csv/png（来自脚本输出）

## 3. 任务分解

### B71. 预检与对齐（10 分钟）

```bash
cd /root/projects/4d-recon
git fetch origin
git status -sb
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
```

验收：测试全 PASS，工作区干净或仅包含计划内改动。

### B72. 实现失败归因工具 1：gate_framediff 命中率统计与热图（TDD）

目的：对应 meeting-decision 最小包第 (4) 项，回答“gating 到底在正则哪里/是否均匀撒背景”。

输入：任意 `gt_cache.npz`（包含 `gate_framediff`）。  
输出（默认写到 `outputs/report_pack/diagnostics/`）：
- `gate_framediff_mean_by_frame.csv`（每帧均值）
- `gate_framediff_mean_by_view.csv`（每视角均值）
- `gate_framediff_heatmap.png`（frame×view 热图）

实现文件：
- `scripts/analyze_vggt_gate_framediff.py`
- `scripts/tests/test_analyze_vggt_gate_framediff.py`（用小 tensor dummy npz 先红后绿）

建议使用的数据源（现成，不依赖 GPU）：
- `.worktrees/owner-a-20260226-v2-postfix/outputs/vggt_cache/*token_proj*/gt_cache.npz`

### B73. 实现失败归因工具 2：phi 的 shift sensitivity（TDD）

目的：对应 meeting-decision 最小包第 (3) 项的“无训练版近似”，证明 feature loss 对轻微错位可能非常敏感。

口径（写死，避免争论）：
- 这是 **phi-space** 的 shift sensitivity：对缓存 `phi[T,V,C,Hf,Wf]` 做空间平移（dx/dy in [-2,2]），计算 cosine/L1 差异统计。
- 不声称等价于 image-space shift，只作为“对齐误差会被放大”的佐证。

输出：
- `phi_shift_sensitivity.csv`（dx,dy -> loss_mean/loss_p90 等）
- `phi_shift_sensitivity.png`（热图/曲线）

实现文件：
- `scripts/analyze_phi_shift_sensitivity.py`
- `scripts/tests/test_analyze_phi_shift_sensitivity.py`（dummy phi 验证输出 shape 与数值单调性）

### B74. 更新失败归因最小包文档（补齐“待补”项）

更新：`notes/feature_loss_failure_attribution_minpack.md`

把以下两项改成“已完成”并给出证据路径（哪怕证据文件不入库也要可定位）：
- (3) shift sensitivity：指向 `outputs/report_pack/diagnostics/phi_shift_sensitivity.*`
- (4) gating heatmap：指向 `outputs/report_pack/diagnostics/gate_framediff_*`

### B75. v20 report-pack/evidence 刷新（等待 A 的 smoke200 产物落地）

触发条件（来自 A handoff）：
- canonical `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_*_smoke200/` 三条 run 已生成；
- A 的结论 notes 已入库：
  - `notes/planb_component_ablation_smoke200_owner_a.md`
  - `notes/handoff_planb_component_ablation_owner_a.md`

执行：

```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py

# 生成 v20 evidence（不入库 tar.gz，本地生成 + SHA 登记 + docs 快照入库）
python3 scripts/pack_evidence.py --repo_root /root/projects/4d-recon --out_tar artifacts/report_packs/report_pack_2026-02-26-v20.tar.gz
sha256sum artifacts/report_packs/report_pack_2026-02-26-v20.tar.gz >> artifacts/report_packs/SHA256SUMS.txt

mkdir -p docs/report_pack/2026-02-26-v20
cp -a outputs/report_pack/metrics.csv outputs/report_pack/scoreboard.md \\
  outputs/report_pack/ablation_notes.md outputs/report_pack/failure_cases.md \\
  outputs/report_pack/manifest_sha256.csv docs/report_pack/2026-02-26-v20/

# 确保 docs 快照的 manifest 来自 tar（避免“复制旧文件”错位）
tar -xzf artifacts/report_packs/report_pack_2026-02-26-v20.tar.gz -O manifest_sha256.csv > docs/report_pack/2026-02-26-v20/manifest_sha256.csv
```

验收：
- `docs/report_pack/2026-02-26-v20/metrics.csv` 行数增加（包含 planb_ablate_* smoke200 的 test@199 行）。
- `outputs/report_pack/ablation_notes.md` 中出现 “Plan‑B 组件消融（smoke200）” 小节，引用 A 的结论（不要求把数值全手抄，但要有一句“哪个补丁必要”）。
- `artifacts/report_packs/SHA256SUMS.txt` 新增 v20 行且格式正确。

### B76. 提交与推送

只提交代码/文档（不提交 tar.gz 与 outputs/data）：

```bash
cd /root/projects/4d-recon
git status -sb
git add scripts/ scripts/tests/ notes/ docs/report_pack/2026-02-26-v20 artifacts/report_packs/SHA256SUMS.txt
git commit -m \"docs(report-pack): refresh v20 incl planb ablation + failure attribution plots\"
git push origin HEAD:main
```

## 4. 并行性说明（给项目管理用）

- B71-B74 完全不依赖 A，可立即开始。
- B75-B76 仅依赖 A 的 smoke200 产物与 notes handoff；一旦 A 完成，B 在 30 分钟内可完成 v20 刷新与推送。

