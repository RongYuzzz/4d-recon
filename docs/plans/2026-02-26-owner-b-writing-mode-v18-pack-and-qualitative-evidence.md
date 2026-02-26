# Writing Mode v18 + Qualitative Evidence Pack（Owner B）Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不使用 GPU 的前提下，把 Plan‑B 的最新证据（包含 seg200_260 与 seg400_460 的 smoke200 防守位）收敛为 **report-pack v18** + **evidence tar v18**，并把 “Plan‑B vs baseline side‑by‑side” 定性材料纳入 evidence pack（可选存在即可收录）。

**Architecture:** 不改 `protocol_v1`；不新增 full600。使用 `scripts/build_report_pack.py`/`scripts/summarize_scoreboard.py` 刷新 `outputs/report_pack/`，再用 `scripts/pack_evidence.py` 生成 `artifacts/report_packs/report_pack_2026-02-26-v18.tar.gz`，并把 tar 内的 `manifest_sha256.csv` **解包写入** `docs/report_pack/2026-02-26-v18/manifest_sha256.csv`（避免历史快照 manifest 复用导致的不一致）。

**Tech Stack:** Python、Bash、`ffmpeg`（仅用于生成 side-by-side，No‑GPU）、`scripts/pack_evidence.py`。

---

## 硬约束

1. 不改 `docs/protocols/protocol_v1.yaml` 与 canonical 数据（只做写作/打包）。
2. 不提交大文件：不 commit `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`。
3. 仅允许 No‑GPU 工具链与文档更新；全量脚本测试必须 PASS。

---

### Task B61：预检与对齐 main（15 分钟）

**Files:**
- Create: `notes/owner_b_v18_preflight.md`

**Step 1: 对齐 main**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git checkout main
git pull --ff-only origin main
```

**Step 2: 记录 provenance + 关键路径存在性**

写入 `notes/owner_b_v18_preflight.md`：
- `git rev-parse HEAD`
- 关键目录存在（只读检查）：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/`
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_600/`
  - （若 A 已完成）`outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/`

**Step 3: 回归测试**

Run:
```bash
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected: 全 PASS。

---

### Task B62：evidence pack 收录 qualitative side‑by‑side（TDD，No‑GPU）

目的：让 evidence tarball 除了每个 run 的 `traj_*.mp4` 外，还能直接给出 “baseline vs planb” 的一条 side‑by‑side mp4 + 抽帧 jpg（若存在则收录，不存在则跳过）。

**Files:**
- Modify: `scripts/pack_evidence.py`
- Modify: `scripts/tests/test_pack_evidence.py`

**Step 1: 先写失败测试（红灯）**

在 `scripts/tests/test_pack_evidence.py` 里新增 dummy qualitative 文件：
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000000.jpg`

并把它们加入 `must_have`。

Run:
```bash
python3 scripts/tests/test_pack_evidence.py
```

Expected: FAIL（missing qualitative members）。

**Step 2: 最小实现（绿灯）**

在 `scripts/pack_evidence.py` 的 `collect_files()` 中加入（仅当文件存在时收录）：
- `outputs/qualitative/planb_vs_baseline/*.mp4`
- `outputs/qualitative/planb_vs_baseline/frames/frame_*.jpg`

Run:
```bash
python3 scripts/tests/test_pack_evidence.py
```

Expected: PASS。

**Step 3: 提交**

Run:
```bash
git add scripts/pack_evidence.py scripts/tests/test_pack_evidence.py
git commit -m "chore(evidence): include planb qualitative side-by-side outputs when present"
```

---

### Task B63：生成/刷新 canonical 与 seg2 的 side‑by‑side 资产（No‑GPU，本机产物不入库）

**Step 1: canonical**

Run:
```bash
cd /root/projects/4d-recon
bash scripts/make_side_by_side_video.sh --overwrite
bash scripts/extract_video_frames.sh \
  --video outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline/frames \
  --frames 0,30,59 \
  --overwrite
```

Expected:
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000000.jpg` 等

**Step 2: seg200_260（可选，若需要）**

若要做 seg2 的 side‑by‑side，则用 `--left/--right` 指向 seg2 的两条 `traj_*.mp4`，并输出到：
- `outputs/qualitative/planb_vs_baseline_seg200_260/`

---

### Task B64：刷新 report-pack v18（等待 A 的 seg400_460 smoke200 到位后执行）

**Files:**
- Create: `docs/report_pack/2026-02-26-v18/metrics.csv`
- Create: `docs/report_pack/2026-02-26-v18/scoreboard.md`
- Create: `docs/report_pack/2026-02-26-v18/ablation_notes.md`
- Create: `docs/report_pack/2026-02-26-v18/failure_cases.md`
- Create: `docs/report_pack/2026-02-26-v18/manifest_sha256.csv`
- Modify: `artifacts/report_packs/SHA256SUMS.txt`

**Step 1: 刷新 outputs/report_pack/**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md
```

**Step 2: 更新 outputs/report_pack/ablation_notes.md（手工编辑即可）**

要求新增一段 seg400_460（smoke200）表格（若 A 已产出）：
- baseline_smoke200 vs planb_init_smoke200 的 PSNR/LPIPS/tLPIPS + Δ

**Step 3: 生成 evidence tar v18**

Run:
```bash
cd /root/projects/4d-recon
OUT_TAR=artifacts/report_packs/report_pack_2026-02-26-v18.tar.gz
python3 scripts/pack_evidence.py --repo_root /root/projects/4d-recon --out_tar "$OUT_TAR"
sha256sum "$OUT_TAR" | tee /tmp/report_pack_2026-02-26-v18.sha256
```

**Step 4: 生成 docs 快照 v18（manifest 必须来自 tar）**

Run:
```bash
cd /root/projects/4d-recon
SNAP=docs/report_pack/2026-02-26-v18
mkdir -p "$SNAP"
cp -f outputs/report_pack/metrics.csv "$SNAP/metrics.csv"
cp -f outputs/report_pack/scoreboard.md "$SNAP/scoreboard.md"
cp -f outputs/report_pack/ablation_notes.md "$SNAP/ablation_notes.md"
cp -f outputs/report_pack/failure_cases.md "$SNAP/failure_cases.md"
tar -xOzf "$OUT_TAR" manifest_sha256.csv > "$SNAP/manifest_sha256.csv"
```

验收：
- `rg -n "seg400_460" "$SNAP/ablation_notes.md"`（若 A 完成 seg400_460）
- `rg -n "planb_init_600" "$SNAP/scoreboard.md"`

**Step 5: 登记 SHA（只改 SHA256SUMS，不提交 tar）**

将 `/tmp/report_pack_2026-02-26-v18.sha256` 的一行追加到：
- `artifacts/report_packs/SHA256SUMS.txt`

---

### Task B65：写作收口更新（v18）

**Files:**
- Modify: `notes/planb_verdict_writeup_owner_b.md`

要求：
- 在 anti‑cherrypick 防守小节补充 seg400_460 的 smoke200 证据（若已产出）。
- 明确 full600 预算已用尽，后续若继续跑 full600 必须新建决议扩预算。

---

### Task B66：提交并推送（不提交 outputs/data/tar）

Run:
```bash
cd /root/projects/4d-recon
git add notes/owner_b_v18_preflight.md \
  scripts/pack_evidence.py scripts/tests/test_pack_evidence.py \
  docs/report_pack/2026-02-26-v18 \
  artifacts/report_packs/SHA256SUMS.txt \
  notes/planb_verdict_writeup_owner_b.md
git commit -m "docs(report-pack): refresh v18 with seg400_460 smoke200 defense and qualitative evidence support"
git push origin HEAD:main
```

