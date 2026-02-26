# Owner B Plan (No GPU): Writing Mode 收口 + Plan‑B 证据强化 + v17 快照

日期：2026-02-26  
Owner：B  
GPU：不使用（No‑GPU）  
目标：在不改 `protocol_v1` 的前提下，围绕 **Plan‑B = 主线 Go** 做写作收口与证据强化；为最终汇报/论文产出准备可复用材料，并在 A 产出 seg2 Plan‑B 结果后刷新 report-pack **v17**。

## 0) 约束（必须遵守）

- 协议锁死：`docs/protocol.yaml`（`protocol_v1`）不改；禁止换帧段/相机子集/`global_scale`/`keyframe_step`。
- feature-loss 主线冻结：禁止新增 feature-loss full600；只允许 No‑GPU 归因分析与可视化。
- 不提交大文件：不 commit `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`；只 commit `docs/`、`notes/` 与 `artifacts/report_packs/SHA256SUMS.txt`（如需登记 SHA）。

## 1) 任务清单（B 可与 A 并行执行）

### Task B51：预检与 provenance（30 分钟）

产出：
- `notes/owner_b_planb_writing_preflight.md`

检查（全部应 PASS）：
```bash
cd /root/projects/4d-recon
git rev-parse HEAD
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

确认关键结果目录存在（只读验收）：
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/`
- `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json`
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/control_weak_nocue_600/`

### Task B52：Plan‑B 定性对比产物脚本化（No‑GPU）

目的：把“Plan‑B 在 canonical 明显更稳”的证据做成可复用命令，避免临场手工剪视频。

交付（代码+文档）：
- 新增脚本：`scripts/make_side_by_side_video.sh`（ffmpeg hstack + label）
- 新增脚本：`scripts/extract_video_frames.sh`（抽帧：000000/000030/000059）
- 新增说明：`docs/execution/2026-02-26-planb-qualitative.md`

输入默认：
- baseline：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4`
- planb：`outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/videos/traj_4d_step599.mp4`

输出目录（不入库）建议：
- `outputs/qualitative/planb_vs_baseline/`

验收：脚本在本机可运行（缺 ffmpeg 时给出明确报错与安装提示），输出 mp4 与抽帧 jpg 存在。

### Task B53：feature-loss v2 负结果“最小归因包”落盘（No‑GPU）

目的：把 feature-loss v2 的失败从“玄学调参”变成“可审计的归因链”（用于答辩/论文 negative result）。

交付（文档为主）：
- 新增：`notes/feature_loss_v2_failure_attribution_owner_b.md`

执行（复用现成工具，不跑 GPU）：
1. 使用 `scripts/export_tb_scalars.py` 导出 TB scalars（CSV）：
   - baseline_600
   - feature_loss_v2_postfix_600（或最新 v2_600 失败 run）
2. 在文档中给出：
   - 关键 tag 的曲线结论（loss/psnr/lpips/tlpips/densify 相关）
   - “已排除项”列表（token_proj 对齐已修复、cache 合同测试 PASS、吞吐 ≤2x 等）
   - “仍未知项/方法边界”与下一步（明确不会继续烧 full600）

注意：原始 CSV 放在 `outputs/diagnostics/`（不入库）；文档只写结论与可复现命令。

### Task B54：等待 A 的 seg2 Plan‑B 结果后刷新 report-pack v17（No‑GPU）

触发条件（A 完成任一即可开始刷新）：
- seg2 smoke200 产物落地：`.../baseline_smoke200/`、`.../planb_init_smoke200/`
- 或 seg2 full600 产物落地：`.../planb_init_600/`

执行：
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md
python3 scripts/pack_evidence.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/artifacts/report_packs --snapshot_dir /root/projects/4d-recon/docs/report_pack/2026-02-26-v17
```

验收：
- `docs/report_pack/2026-02-26-v17/` 5 文件齐全（metrics/scoreboard/ablation_notes/failure_cases/manifest）
- `artifacts/report_packs/SHA256SUMS.txt` 追加 v17 tar 的 SHA（tar 本体不 commit）

### Task B55：写作口径收口（Plan‑B 主线 + anti‑cherrypick 防守）

交付：
- 更新：`notes/planb_verdict_writeup_owner_b.md`（或新增 v2 版本文件）

必须写清三点（可直接贴到 slides/报告）：
1. Plan‑B 的一句话定义（triangulation→3D velocity init；只替换 init velocities，不改协议）
2. canonical 关键结论（三行指标：baseline/control/planb；强调 tLPIPS 大幅下降）
3. anti‑cherrypick 防守策略（seg200_260：baseline/control/(planb 若有)；说明该证据位定位为附录防守）

## 2) 并行性说明（与 Owner A）

- A（GPU0）负责：seg2 Plan‑B Gate +（条件）seg2 full600。
- B（No‑GPU）可同时推进：定性脚本化、feature-loss 归因、写作收口；仅在 **Task B54** 需要等 A 产物到位后做一次 v17 快照刷新。

