# protocol_v2 Temporal Diff Diagnostics Implementation Plan (Owner A / GPU0)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 给 `protocol_v2` 的 stage‑2 trade-off（`planb_init_600 -> planb_feat_v2_full600`）补一份**可审计**的“时序不稳定发生在哪些帧”的诊断产物（CSV+图），用于答辩/写作的 failure analysis；不新增 full600。

**Architecture:** 基于现有 `renders/*_step599_*.png`（注意：文件内是 GT|Pred 横向拼接），离线计算 Pred(t) 与 Pred(t-1) 的 temporal diff time-series（先做像素域 L1/PSNR 等轻量指标；可选再补 LPIPS），输出到 `outputs/report_pack/diagnostics/`，并在 `notes/protocol_v2_stage2_tradeoff_qual.md` 引用。

**Tech Stack:** Python 3（Pillow/numpy/matplotlib）、现有渲染产物目录、`outputs/report_pack/diagnostics/`（自动随 evidence tar 打包）。

---

## Constraints / Invariants（必须遵守）

- 只做诊断，不新增 full600；不改动 `protocol_v1/v26` 的证据链。
- 产物必须落在 `outputs/report_pack/diagnostics/`（小文件，便于离线包审计）。
- 诊断脚本必须能在主阵地 `/root/autodl-tmp/projects/4d-recon` 直接跑（不依赖 `.worktrees/...`）。

---

### Task 0: Preflight（5 分钟）

**Files:**
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/`
- Read: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/`

**Step 1: 确认两份 renders 存在（至少 test_step599_0000.png）**

Run:
```bash
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders/test_step599_0000.png
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders/test_step599_0000.png
```
Expected: 两个文件都存在。

---

### Task 1: 新增诊断脚本（temporal diff time-series）（30-45 分钟）

**Files:**
- Create: `scripts/analyze_temporal_diff_from_renders.py`
- Create: `scripts/tests/test_analyze_temporal_diff_from_renders_contract.py`

**Step 1: 写一个失败单测（先红）**

目标：验证脚本能正确解析 “GT|Pred 拼接图”，并输出期望 CSV 列。

Test 要点（用临时目录造 3 张假图即可）：
- 生成 3 张 `test_step599_0000.png/0001/0002.png`，每张宽度 `2W`：
  - 左半（GT）随便填
  - 右半（Pred）让 `t=1` 与 `t=0` 不同，`t=2` 与 `t=1` 不同
- 跑脚本生成 CSV
- 断言：
  - CSV 行数为 2（因为 diff 是 pair：1-0、2-1）
  - 列包含：`pair_idx,frame_prev,frame_cur,mean_abs_diff`（至少这些）

Run:
```bash
pytest -q scripts/tests/test_analyze_temporal_diff_from_renders_contract.py
```
Expected: FAIL（脚本未实现）。

**Step 2: 实现最小脚本（让测试变绿）**

CLI 设计（最小够用）：
- `--renders_dir`（例如 `.../renders`）
- `--pattern_prefix`（默认 `test_step599_`，也允许 `val_step599_`）
- `--out_csv`
- `--split_mode`（固定为 `gt_pred_concat`，意为横向 2W 图片取右半作为 Pred）

实现逻辑（核心）：
- 按文件名排序读取 `*_0000.png ... *_0059.png`
- 对每张图取 Pred half：`img[:, W:]`
- 计算 `mean_abs_diff = mean(|pred_t - pred_{t-1}|)`（RGB，归一化到 [0,1]）
- 写 CSV

**Step 3: 跑单测变绿**

Run:
```bash
pytest -q scripts/tests/test_analyze_temporal_diff_from_renders_contract.py
```
Expected: PASS。

**Step 4: Commit（只提交脚本+测试）**

Run:
```bash
git add scripts/analyze_temporal_diff_from_renders.py scripts/tests/test_analyze_temporal_diff_from_renders_contract.py
git commit -m "feat(diagnostics): add temporal diff time-series from renders"
```

---

### Task 2: 跑诊断并落盘到 report-pack diagnostics（15-30 分钟）

**Files:**
- Create: `outputs/report_pack/diagnostics/temporal_diff_planb_init_600_test_step599.csv`
- Create: `outputs/report_pack/diagnostics/temporal_diff_planb_feat_v2_full600_test_step599.csv`
- Create: `outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv`

**Step 1: 生成 planb_init_600 的 time-series CSV**

Run:
```bash
python3 scripts/analyze_temporal_diff_from_renders.py \
  --renders_dir outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders \
  --pattern_prefix test_step599_ \
  --out_csv outputs/report_pack/diagnostics/temporal_diff_planb_init_600_test_step599.csv
```

**Step 2: 生成 planb_feat_v2_full600 的 time-series CSV**

Run:
```bash
python3 scripts/analyze_temporal_diff_from_renders.py \
  --renders_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders \
  --pattern_prefix test_step599_ \
  --out_csv outputs/report_pack/diagnostics/temporal_diff_planb_feat_v2_full600_test_step599.csv
```

**Step 3: 生成 delta CSV（planbfeat - planb）**

Run:
```bash
python3 - <<'PY'
import csv
from pathlib import Path

a = Path("outputs/report_pack/diagnostics/temporal_diff_planb_init_600_test_step599.csv")
b = Path("outputs/report_pack/diagnostics/temporal_diff_planb_feat_v2_full600_test_step599.csv")
out = Path("outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv")

ra = list(csv.DictReader(a.open(newline="")))
rb = list(csv.DictReader(b.open(newline="")))
assert len(ra) == len(rb) and len(ra) > 0
fieldnames = ["pair_idx","frame_prev","frame_cur","mean_abs_diff_a","mean_abs_diff_b","delta_mean_abs_diff"]
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for xa, xb in zip(ra, rb, strict=True):
        da = float(xa["mean_abs_diff"])
        db = float(xb["mean_abs_diff"])
        w.writerow({
            "pair_idx": xa["pair_idx"],
            "frame_prev": xa["frame_prev"],
            "frame_cur": xa["frame_cur"],
            "mean_abs_diff_a": f"{da:.8f}",
            "mean_abs_diff_b": f"{db:.8f}",
            "delta_mean_abs_diff": f"{(db-da):.8f}",
        })
print("wrote", out)
PY
```

**Acceptance:**
- 三个 CSV 文件存在且可读
- `delta_mean_abs_diff` 的 top-k 峰值能定位到 1-2 个代表性帧段（用于答辩锚点）

---

### Task 3: 出图（top-k 峰值 + 全序列曲线）（20-30 分钟）

**Files:**
- Create: `outputs/report_pack/diagnostics/temporal_diff_curve_planb_vs_planbfeat_test_step599.png`
- Create: `outputs/report_pack/diagnostics/temporal_diff_topk_table_planbfeat_minus_planb_test_step599.md`

**Step 1: 画曲线（A/B 两条 + delta）**

实现方式任选其一：
- 在 `scripts/analyze_temporal_diff_from_renders.py` 增加 `--out_png`（推荐，复用 CLI）
- 或写一个一次性 `python3 - <<'PY' ...` 脚本读取 CSV 并用 matplotlib 画图

图要求（最小）：
- x：pair/frame index
- y：mean_abs_diff
- A/B 两条线 + delta（可用第二 y 轴或单独子图）

**Step 2: 导出 top-k 表格（Markdown）**

输出格式（建议）：
`| rank | frame_prev | frame_cur | delta_mean_abs_diff |`

---

### Task 4: 写作/审计引用（10 分钟）

**Files:**
- Modify: `notes/protocol_v2_stage2_tradeoff_qual.md`

**Step 1: 在 note 里补充“诊断产物指针”**

在 “代表性失败片段” 处追加引用：
- `outputs/report_pack/diagnostics/temporal_diff_curve_planb_vs_planbfeat_test_step599.png`
- `outputs/report_pack/diagnostics/temporal_diff_topk_table_planbfeat_minus_planb_test_step599.md`

并把“约 1.13s / frame 34”这种描述改成更审计友好的：
- “top‑k delta pair 在 `frame_prev=X frame_cur=Y`，见 top‑k 表格”

---

## Handoff（给 Owner B）

完成后给 B 三个东西即可（用于重打离线包与更新 report-pack README，如需）：
- 新增诊断目录文件：
  - `outputs/report_pack/diagnostics/temporal_diff_*`
- 更新后的 note：
  - `notes/protocol_v2_stage2_tradeoff_qual.md`
- 结论一句话（写给 README 的）：哪个帧段 delta 最大、是否与现有 failure anchor 一致。

