# Owner A 后续计划：Writing Mode（v26 冻结期）资产整理与审计（不新增训练）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner A（可用 GPU0，但本计划默认不使用 GPU；**禁止新增训练**）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`

## 0) 目标（给写作/汇报直接供弹）

在 **不新增任何训练**（含 smoke200/full600）、不改 `protocol_v1`、不改数值逻辑的前提下：

1. 把 v26 的关键证据做成“可直接贴 slide/论文”的图表与定性素材（抽帧 + 播放清单）。
2. 做一次快速审计，确保 v26 的“唯一数字口径”与离线 evidence tar 可复核、不会临场翻车。
3. 给 Owner B 写作端提供明确的可引用素材路径与一句话结论（避免口径漂移）。

## 1) 约束（必须遵守）

- 禁止新增训练：不运行任何 `run_train_*.sh`，不新增任何 smoke200/full600。
- 不改 `docs/protocols/protocol_v1.yaml`；不改训练数值逻辑。
- `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 允许入库：`docs/`、`notes/`、`scripts/`、`scripts/tests/`、`artifacts/report_packs/SHA256SUMS.txt`（仅在确需登记新 tar 的情况下）。

## 2) Task A131：v26 证据快速审计（15 分钟，No‑GPU）

**目的：** 确认“会中数字唯一真源”可复现，避免出现 metrics/manifest 与主阵地不一致。

Run：
```bash
cd /root/projects/4d-recon

# 1) v26 report-pack 四件套存在性
ls -la docs/report_pack/2026-02-26-v26/{metrics.csv,scoreboard.md,planb_anticherrypick.md,manifest_sha256.csv}

# 2) evidence tar SHA 可核验
rg -n "report_pack_2026-02-26-v26" artifacts/report_packs/SHA256SUMS.txt
sha256sum artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz

# 3) 从 outputs 重建一次 report_pack（不写入 git）
python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md
python3 scripts/summarize_planb_anticherrypick.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md
```

验收：

- `sha256sum` 输出与 `SHA256SUMS.txt` 中 v26 行一致。
- `outputs/report_pack/planb_anticherrypick.md` 中至少包含：
  - `seg300_360`、`seg400_460`、`seg1800_1860`（delta 与 v26 快照一致到小数 1e-4 级别即可）。
- 不产生任何需要入库的大文件变更。

交付（入库）：

- `notes/planb_v26_audit_owner_a.md`（记录上述 3 步的“PASS/FAIL + 关键输出摘录”，用于会前自检凭证）。

## 3) Task A132：定性素材“抽帧主图组”（No‑GPU，可并行）

**目的：** 产出可直接贴 slide/论文的主图（3 帧一组），配合 side-by-side 视频解决“绝对 PSNR 原罪”直觉攻击。

输入（已存在的 side-by-side 资产，若缺失则记录缺口，不补训练）：

- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`（canonical）
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg600_660_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4`

Run（每个视频抽 3 帧：0/30/59；若帧号越界脚本会自动回退）：
```bash
cd /root/projects/4d-recon

OUT=outputs/qualitative/planb_vs_baseline/frames_selected_v26
mkdir -p "$OUT"

for mp4 in \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg600_660_step199.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4 \
; do
  base="$(basename "$mp4" .mp4)"
  bash scripts/extract_video_frames.sh "$mp4" "$OUT/${base}_frame_000000.jpg" 0
  bash scripts/extract_video_frames.sh "$mp4" "$OUT/${base}_frame_000030.jpg" 30
  bash scripts/extract_video_frames.sh "$mp4" "$OUT/${base}_frame_000059.jpg" 59
done
```

验收：

- `frames_selected_v26/` 下每个视频至少生成 3 张 jpg。
- 文件命名带上 `segXXX_YYY` 与 `step`，便于写作端引用。

交付（入库）：

- `notes/planb_qualitative_frames_v26_owner_a.md`：列出每个 slice 的“推荐主图组”文件名 + 一句话说明（该 slice baseline 的主要伪影/planb 的改进点）。

## 4) Task A133：主表 Table‑1 数字提取（No‑GPU，可并行）

**目的：** 给写作端提供“canonical + seg200_260 full600 的 Table‑1”可直接复制粘贴版本，并明确 Δ 的定义。

Run（从 v26 快照 `metrics.csv` 提取 canonical 与 seg200_260 的 full600 行；不写脚本也可手工，但必须可复核）：
```bash
cd /root/projects/4d-recon
python3 - <<'PY'
import csv
from pathlib import Path

csv_path = Path("docs/report_pack/2026-02-26-v26/metrics.csv")
rows = list(csv.DictReader(csv_path.open()))

def pick(run_suffix: str, step: str="599", stage: str="test"):
    cands = [r for r in rows if r.get("stage")==stage and r.get("step")==step and r.get("run_dir","").endswith(run_suffix)]
    if len(cands)!=1:
        raise SystemExit(f"expected 1 row for {run_suffix}, got {len(cands)}")
    return cands[0]

def f(x): return float(x)
def fmt(x): return f"{x:.4f}"

baseline = pick("/protocol_v1/selfcap_bar_8cam60f/baseline_600")
planb    = pick("/protocol_v1/selfcap_bar_8cam60f/planb_init_600")
seg_base = pick("/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600")
seg_plan = pick("/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_600")

keys = ["psnr","ssim","lpips","tlpips"]
def delta(a,b,k): return f(b[k])-f(a[k])

print("canonical_full600")
print({k: fmt(f(baseline[k])) for k in keys})
print({k: fmt(f(planb[k])) for k in keys})
print({f"delta_{k}": fmt(delta(baseline,planb,k)) for k in keys})
print("seg200_260_full600")
print({k: fmt(f(seg_base[k])) for k in keys})
print({k: fmt(f(seg_plan[k])) for k in keys})
print({f"delta_{k}": fmt(delta(seg_base,seg_plan,k)) for k in keys})
PY
```

验收：

- 产出中 canonical 的 `ΔPSNR` 应为 `+1.4992`（允许 1e-4 级误差）。
- 输出明确 `Δ = planb - baseline`。

交付（入库）：

- `notes/planb_table1_v26_owner_a.md`：以 markdown 表格给出两段 full600（canonical + seg200_260）baseline/planb 数字与 Δ，并指向 v26 `metrics.csv` 作为可审计真源。

## 5) Task A134：handoff（给 Owner B 的写作接入点）

交付（入库）：

- `notes/handoff_planb_v26_assets_owner_a.md`，必须包含：
  - A131/A132/A133 的产物路径（含 `frames_selected_v26/` 目录与 6 个视频清单）。
  - 写作建议：会议前 5 分钟播放顺序（canonical -> seg200_260 -> 任选 1 个 smoke200 seg）。
  - 一句主叙事提醒：Plan‑B 主因是“物理速度先验打破收敛陷阱”，Mutual NN 定位为 stabilizer（对应消融与 tLPIPS 解释）。

## 6) 收尾回归（必须）

Run：
```bash
cd /root/projects/4d-recon
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

提交规范：

- 只提交 `notes/*` 与必要的 `docs/*`（本计划不应引入脚本改动）。
- 不提交 `outputs/`、`data/`、`artifacts/report_packs/*.tar.gz`。

