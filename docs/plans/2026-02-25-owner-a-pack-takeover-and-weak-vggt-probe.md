# Owner A Plan: 接管打包/报表 + Weak(VGGT Cue) 探针（两人两 GPU 版）

> 状态：待执行（Next）。本计划默认 **只用 GPU0**；GPU1 留给 Owner B。  
> 背景：Owner C 暂时无法工作，需要 A/B 覆盖 midterm 交付的“报表与证据链”维护。

## Goal

1. **接管 C 的职责**：确保在 `docs/protocol.yaml (v1)` 下，`scoreboard + report-pack + evidence` 能持续刷新且可审计。
2. 在**不修改 protocol v1** 的前提下，做一次 **Weak + VGGT cue** 的小规模“可行性探针”，判断是否值得开 `protocol_v2`（仅提出建议，不在本计划内切换 symlink）。

## Non-Goal

- 不做 strong fusion 主线推进（由 B 负责）。
- 不在本计划内升级/替换 `docs/protocol.yaml`（若需要 v2，只产出“决策建议 + 草案”）。
- 不改 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`（避免与 B 同文件冲突）。
- 不把 `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 入库。

## Parallel Safety（并发约束）

- A：GPU0 + 文档/脚本（主要写 `notes/`、`docs/report_pack/`、`artifacts/report_packs/SHA256SUMS.txt`）。
- B：GPU1 + trainer/实验（A 避免 touching trainer，减少 merge 冲突）。

---

## Task A41：建立隔离 worktree（避免污染 main）

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-a-20260225-pack-and-weak-vggt .worktrees/owner-a-20260225-pack-and-weak-vggt main
git -C .worktrees/owner-a-20260225-pack-and-weak-vggt status --porcelain=v1
```

Expected:
- worktree 干净（无输出）

---

## Task A42：接管“报表 + 证据包”刷新（不依赖新实验）

目的：即使 B 在跑实验，A 也能先把**当前主线状态**打成一份“可交付快照”（后续有新结果再滚动 v11/v12）。

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-and-weak-vggt

# 1) 刷新 report-pack（metrics.csv / scoreboard.md）
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv > outputs/report_pack/scoreboard.md

# 2) 打 evidence tar（注意：tar.gz 不入库；只登记 sha256 + 写 docs 快照）
DATE_TAG="2026-02-25-v10"
OUT_TAR="artifacts/report_packs/report_pack_${DATE_TAG}.tar.gz"
python3 scripts/pack_evidence.py --repo_root . --out_tar "$OUT_TAR"
sha256sum "$OUT_TAR" | tee -a artifacts/report_packs/SHA256SUMS.txt

# 3) 生成 docs 快照目录（只存文本快照，便于 code review）
SNAP_DIR="docs/report_pack/${DATE_TAG}"
mkdir -p "$SNAP_DIR"
cp -f outputs/report_pack/metrics.csv "$SNAP_DIR/metrics.csv"
cp -f outputs/report_pack/scoreboard.md "$SNAP_DIR/scoreboard.md"
cp -f outputs/report_pack/ablation_notes.md "$SNAP_DIR/ablation_notes.md"
cp -f outputs/report_pack/failure_cases.md "$SNAP_DIR/failure_cases.md"
cp -f outputs/report_pack/manifest_sha256.csv "$SNAP_DIR/manifest_sha256.csv"
```

验收：
- `outputs/report_pack/metrics.csv`、`outputs/report_pack/scoreboard.md` 存在且非空
- `artifacts/report_packs/report_pack_2026-02-25-v10.tar.gz` 非空
- `artifacts/report_packs/SHA256SUMS.txt` 追加 1 行（对应 v10 tarball）
- `docs/report_pack/2026-02-25-v10/` 五个快照文件齐全

提交策略：
- 仅提交：`docs/report_pack/2026-02-25-v10/*` 与 `artifacts/report_packs/SHA256SUMS.txt`（不要 `git add` tar.gz）。

---

## Task A43：VGGT cue mining 探针（GPU0，小成本判断是否值得开 protocol_v2）

目的：解决目前 `control_weak_nocue_600` 优于 `ours_weak_600` 的风险提示。  
策略：不动 protocol v1 的 canonical cue（`selfcap_bar_8cam60f_v1`），另起 tag 做对比探针。

Run（1）VGGT cue 生成：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-and-weak-vggt

GPU=0 \
OUT_DIR=outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe \
bash scripts/run_cue_mining.sh data/selfcap_bar_8cam60f selfcap_bar_8cam60f_vggt_probe 0 60 vggt 4

cat outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json
ls -la outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz | head
```

验收：
- `quality.json` 显示 `all_black=false` 且 `all_white=false`
- `viz/overlay_cam02_frame000000.jpg` 与 `viz/grid_frame000000.jpg` 存在（以及按 A24b 扩展的 per-cam overlay）

Run（2）写一页对比记录（只写事实，不做结论拉踩）：
- 新增：`notes/cue_mining_vggt_probe_selfcap_bar.md`
内容至少包含：
  - diff(v1) 与 vggt(probe) 的 `mask_min/max`、`mean`、`temporal_flicker_l1_mean`
  - overlay 截图引用路径（不要粘图，写路径即可）
  - “是否满足 protocol_v2 候选”判断（YES/NO + 1 句理由）

---

## Task A44：Weak + VGGT cue 训练探针（GPU0，先 200-step 后 600-step，均为实验区）

目的：回答“VGGT cue 是否真的比 diff cue 更有用”，但**不污染** `outputs/protocol_v1/`。

约束：
- 固定 seed=42、相机划分与帧段不变（对齐 protocol v1）
- 只改 Weak 特有参数（`PSEUDO_MASK_WEIGHT` / `PSEUDO_MASK_END_STEP`），且控制 run 数量（先 1 个候选）

Run（200-step sanity，带 test@199 以看 tLPIPS 趋势）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-and-weak-vggt

GPU=0 MAX_STEPS=200 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_s200 \
PSEUDO_MASK_NPZ=outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks.npz \
PSEUDO_MASK_WEIGHT=0.3 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_weak_selfcap.sh
```

Run（若 200-step 不异常，再跑 600-step full probe）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-and-weak-vggt

GPU=0 MAX_STEPS=600 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_600 \
PSEUDO_MASK_NPZ=outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks.npz \
PSEUDO_MASK_WEIGHT=0.3 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_weak_selfcap.sh
```

验收：
- 两个 run 均产出：
  - `videos/traj_4d_step*.mp4`
  - `stats/val_step*.json`
  - `stats/test_step*.json`（应含 `tlpips` 字段）
- 新增记录：`notes/weak_vggt_probe_selfcap_bar.md`
  - 对比：`baseline_600` / `control_weak_nocue_600` / `ours_weak_600`（protocol v1） vs `ours_weak_vggt_*`（probe）
  - 结论只回答：是否值得开 `protocol_v2`（YES/NO），以及如果 YES 需要重跑哪些 baseline（明确成本）

止损线（立刻停）：
- probe 指标明显退化（例如 PSNR -1dB 级别）或 tLPIPS 明显上升，且 overlay 显示 cue 近似噪声。

---

## Task A45：合入 main（只合文档/脚本，不合产物）

当 A42-A44 产出完成后：

1. 提交（建议拆成 2 个 commit）：
   - docs/evidence：`docs/report_pack/2026-02-25-v10/*` + `artifacts/report_packs/SHA256SUMS.txt`
   - notes：`notes/cue_mining_vggt_probe_selfcap_bar.md`、`notes/weak_vggt_probe_selfcap_bar.md`
2. 运行最小测试（防止报表链路回归）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-and-weak-vggt
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_summarize_scoreboard.py
```

验收：
- 测试 PASS
- `git status --porcelain=v1` 干净

