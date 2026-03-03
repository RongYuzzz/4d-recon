# protocol_v2 tLPIPS Curve + Offline Bundle Refresh Implementation Plan (Owner B / GPU1)

> **执行方式：** 实施时按任务逐条执行（推荐使用本仓库的 `executing-plans` 工作流）。

**Goal:** 用 GPU1 补齐一份**可审计**的 `tLPIPS` 退步“发生在哪些帧段”的诊断（per-pair tLPIPS curve + top-k），并在 A 完成像素 diff 诊断后，统一把两份诊断纳入同一个离线证据包与文档入口（report-pack README / manifest / 验收记录）。

**Architecture:** 复用现有 `renders/test_step599_*.png`（GT|Pred 横向拼接），在离线脚本里对 Pred half 计算 `LPIPS(pred_t, pred_{t-1})` time-series；实现上尽量与 trainer 的实现对齐：使用 `torchmetrics.image.lpip.LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True)`，输入范围 `[0,1]`。产物写入 `outputs/report_pack/diagnostics/`，由 `scripts/pack_evidence.py` 自动纳入 tarball。

**Tech Stack:** `third_party/FreeTimeGsVanilla/.venv/bin/python`（含 torch/torchmetrics）、Pillow/numpy/matplotlib、现有 renders 产物目录、`scripts/pack_evidence.py`、`docs/report_pack/2026-02-27-v2/*`。

---

## Constraints / Invariants（必须遵守）

- 仅使用 **GPU1**：计算脚本运行时显式 `CUDA_VISIBLE_DEVICES=1`（或脚本参数 `--device cuda`）。
- 不新增 full600；不改动 `protocol_v1/v26` 证据链。
- 诊断产物必须落在 `outputs/report_pack/diagnostics/`（小文件，便于离线包审计）。
- 若 A 同时在改 `notes/protocol_v2_stage2_tradeoff_qual.md`，B 不要抢同一段落改写；优先新增独立 note + 在 report-pack README 里引用，避免 merge 冲突。

---

### Task 0: Preflight（10 分钟）

**Files:**
- Read: `third_party/FreeTimeGsVanilla/.venv/bin/python`
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/`
- Read: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/`

**Step 1: 确认 GPU1 可用**

Run: `nvidia-smi -L`  
Expected: 存在 GPU 1（32GB）。

**Step 2: 确认 renders 存在（至少 0000 与 0059）**

Run:
```bash
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/test_step599_0000.png
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/test_step599_0059.png
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/test_step599_0000.png
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/test_step599_0059.png
```
Expected: 全部存在。

**Step 3: 确认 torchmetrics LPIPS 可用（对齐 trainer）**

Run:
```bash
PY=third_party/FreeTimeGsVanilla/.venv/bin/python
$PY - <<'PY'
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity
m = LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True)
print("ok", type(m).__name__)
PY
```
Expected: 输出 `ok LearnedPerceptualImagePatchSimilarity`。

---

### Task 1: 新增诊断脚本（per-pair tLPIPS curve from renders）（45-60 分钟）

**Files:**
- Create: `scripts/analyze_tlpips_curve_from_renders.py`
- Create: `scripts/tests/test_analyze_tlpips_curve_from_renders_contract.py`

**Step 1: 写失败单测（先红）**

目标：验证脚本能解析 `GT|Pred` 拼接图并输出期望 CSV 列。

Test 构造（临时目录造 3 张小图即可）：
- 生成 3 张 `test_step599_0000.png/0001/0002.png`，每张宽度 `2W`：
  - 左半（GT）随便填
  - 右半（Pred）让 `t=1` 与 `t=0` 不同，`t=2` 与 `t=1` 不同
- 跑脚本输出 CSV（CPU 也可，避免单测依赖 GPU）
- 断言：
  - 行数为 2（pair: 1-0, 2-1）
  - 列包含：`pair_idx,frame_prev,frame_cur,tlpips`

Run:
```bash
pytest -q scripts/tests/test_analyze_tlpips_curve_from_renders_contract.py
```
Expected: FAIL（脚本未实现）。

**Step 2: 实现最小脚本（让测试变绿）**

建议 CLI：
- `--renders_dir`
- `--pattern_prefix`（默认 `test_step599_`）
- `--out_csv`
- `--device`（默认 `cpu`，实际跑诊断时用 `cuda`）

实现要点：
- 读取并排序 `renders_dir/{pattern_prefix}*.png`
- 对每张图取 Pred half（右半）：`img[:, W:]`
- 转成 `torch.float32` `[1,3,H,W]`，范围 `[0,1]`
- 对每个 pair 计算 `LearnedPerceptualImagePatchSimilarity(alex, normalize=True)(pred_t, pred_{t-1})`
- 写 CSV（浮点保留足够精度）

**Step 3: 跑单测变绿**

Run:
```bash
pytest -q scripts/tests/test_analyze_tlpips_curve_from_renders_contract.py
```
Expected: PASS。

**Step 4: Commit（只提交脚本+测试）**

Run:
```bash
git add scripts/analyze_tlpips_curve_from_renders.py scripts/tests/test_analyze_tlpips_curve_from_renders_contract.py
git commit -m "feat(diagnostics): add per-pair tlpips curve from renders"
```

---

### Task 2: 生成两份曲线 + delta + top-k（GPU1，15-30 分钟）

**Files:**
- Create: `outputs/report_pack/diagnostics/tlpips_curve_planb_init_600_test_step599.csv`
- Create: `outputs/report_pack/diagnostics/tlpips_curve_planb_feat_v2_full600_test_step599.csv`
- Create: `outputs/report_pack/diagnostics/tlpips_curve_delta_planbfeat_minus_planb_test_step599.csv`
- Create: `outputs/report_pack/diagnostics/tlpips_curve_topk_planbfeat_minus_planb_test_step599.md`

**Step 1: 生成 planb_init_600 的 per-pair tLPIPS CSV（GPU1）**

Run:
```bash
PY=third_party/FreeTimeGsVanilla/.venv/bin/python
CUDA_VISIBLE_DEVICES=1 $PY scripts/analyze_tlpips_curve_from_renders.py \
  --renders_dir outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders \
  --pattern_prefix test_step599_ \
  --device cuda \
  --out_csv outputs/report_pack/diagnostics/tlpips_curve_planb_init_600_test_step599.csv
```

**Step 2: 生成 planb_feat_v2_full600 的 per-pair tLPIPS CSV（GPU1）**

Run:
```bash
PY=third_party/FreeTimeGsVanilla/.venv/bin/python
CUDA_VISIBLE_DEVICES=1 $PY scripts/analyze_tlpips_curve_from_renders.py \
  --renders_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders \
  --pattern_prefix test_step599_ \
  --device cuda \
  --out_csv outputs/report_pack/diagnostics/tlpips_curve_planb_feat_v2_full600_test_step599.csv
```

**Step 3: 生成 delta CSV + top-k（planbfeat - planb）**

Run:
```bash
python3 - <<'PY'
import csv
from pathlib import Path

a = Path("outputs/report_pack/diagnostics/tlpips_curve_planb_init_600_test_step599.csv")
b = Path("outputs/report_pack/diagnostics/tlpips_curve_planb_feat_v2_full600_test_step599.csv")
out = Path("outputs/report_pack/diagnostics/tlpips_curve_delta_planbfeat_minus_planb_test_step599.csv")
topk_md = Path("outputs/report_pack/diagnostics/tlpips_curve_topk_planbfeat_minus_planb_test_step599.md")

ra = list(csv.DictReader(a.open(newline="")))
rb = list(csv.DictReader(b.open(newline="")))
assert len(ra) == len(rb) and len(ra) > 0

rows = []
for xa, xb in zip(ra, rb, strict=True):
    da = float(xa["tlpips"])
    db = float(xb["tlpips"])
    rows.append({
        "pair_idx": int(xa["pair_idx"]),
        "frame_prev": int(xa["frame_prev"]),
        "frame_cur": int(xa["frame_cur"]),
        "tlpips_a": da,
        "tlpips_b": db,
        "delta": db - da,
    })

out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pair_idx","frame_prev","frame_cur","tlpips_a","tlpips_b","delta_tlpips"])
    for r in rows:
        w.writerow([r["pair_idx"], r["frame_prev"], r["frame_cur"], f"{r['tlpips_a']:.8f}", f"{r['tlpips_b']:.8f}", f"{r['delta']:.8f}"])

rows_sorted = sorted(rows, key=lambda r: r["delta"], reverse=True)
topk = rows_sorted[:10]
lines = [
    "# tLPIPS Pairwise Delta Top-K (planbfeat - planb)",
    "",
    "| rank | frame_prev | frame_cur | delta_tlpips |",
    "| --- | ---: | ---: | ---: |",
]
for i, r in enumerate(topk, 1):
    lines.append(f\"| {i} | {r['frame_prev']} | {r['frame_cur']} | {r['delta']:+.6f} |\")
topk_md.write_text(\"\\n\".join(lines) + \"\\n\", encoding=\"utf-8\")
print(\"wrote\", out)
print(\"wrote\", topk_md)
PY
```

**Acceptance:**
- 3 个 CSV + 1 个 top-k md 存在
- top-k 能给出明确帧段（例如 `frame_prev=X frame_cur=Y`），可作为答辩锚点

---

### Task 3: 写一个独立 note（避免与 A 冲突）（10 分钟）

**Files:**
- Create: `notes/protocol_v2_tlpips_curve_diagnostics.md`

内容要求（最小）：
- 引用 4 个诊断文件路径（2 条曲线 + delta + top-k）
- 一句话结论：delta 的 top-k 出现在什么帧段，是否与 `notes/protocol_v2_stage2_tradeoff_qual.md` 的失败片段一致/不一致

Commit:
```bash
git add notes/protocol_v2_tlpips_curve_diagnostics.md
git commit -m "docs(protocol_v2): add tlpips curve diagnostics note"
```

---

### Task 4: 等 A 完成像素域 temporal diff 诊断后，统一更新入口与打包（20-30 分钟）

**依赖 A handoff：**
- `outputs/report_pack/diagnostics/temporal_diff_*`（CSV/PNG/MD）
- `notes/protocol_v2_stage2_tradeoff_qual.md` 更新（或至少给出“top-k 帧段”一句话）

**Files:**
- Modify: `docs/report_pack/2026-02-27-v2/README.md`
- Modify: `docs/reviews/2026-02-27/acceptance-2026-02-27.md`
- Modify: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
- Modify: `outputs/report_pack_2026-02-28.tar.gz`

**Step 1: report-pack README 增补诊断指针**

在 `docs/report_pack/2026-02-27-v2/README.md` 的 stage‑2 trade-off 小节追加：
- `notes/protocol_v2_tlpips_curve_diagnostics.md`
- A 的像素 diff 诊断文件（按 A 实际产物路径）

**Step 2: 重打离线包 + 回填 manifest**

Run:
```bash
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
```

**Step 3: 抽查 tar 内包含关键新增诊断**

Run（至少各命中 1 条）：
```bash
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"outputs/report_pack/diagnostics/(tlpips_curve|temporal_diff)_\" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"notes/protocol_v2_tlpips_curve_diagnostics\\.md\"
```

**Step 4: 验收记录追加一条 intake/evidence/conclusion（PASS）**

在 `docs/reviews/2026-02-27/acceptance-2026-02-27.md` 追加小节：
- Intake：A/B 新增诊断产物
- Evidence：tarball + manifest
- Conclusion：PASS；不触发新增 full600

**Step 5: Commit（文档 + manifest 同步）**

Run:
```bash
git add docs/report_pack/2026-02-27-v2/README.md \
  docs/report_pack/2026-02-27-v2/manifest_sha256.csv \
  docs/reviews/2026-02-27/acceptance-2026-02-27.md
git commit -m "docs(protocol_v2): add temporal diagnostics pointers and refresh manifest"
```
