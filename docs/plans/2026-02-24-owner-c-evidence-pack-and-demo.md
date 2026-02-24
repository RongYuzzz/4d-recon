# Evidence Pack + Demo Hardening Implementation Plan (Owner C)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把“可复现证据包”产品化：一键生成 `metrics.csv`（含 Gate-0/Gate-1/T0 的关键指标与动态/梯度摘要）+ 一键打包（排除 ckpts/tb 等大文件），并在 GPU2 上跑一条 600-step SelfCap demo 作为答辩展示用视频与 stats。

**Architecture:** 在独立 worktree 上做 3 件事：1) 强化 `scripts/build_report_pack.py`（支持参数、派生 gate/dataset 字段、可选加入 velocity 与 t0-grad 摘要）；2) 新增 `scripts/pack_evidence.py` 生成带 `manifest_sha256.csv` 的离线包；3) 用主阵地已暴露的 `data/selfcap_bar_8cam60f` 路径跑一个“可播 demo run”，把关键产物纳入 evidence pack。所有代码变更走脚本级测试（不依赖 pytest）。

**Tech Stack:** Python, `tarfile`, `hashlib`, NumPy, FreeTimeGsVanilla `.venv`, Bash

---

### Task C4: 创建隔离 Worktree（避免与 A 的 mainline 集成互相踩）

**Files:**
- None (worktree only)

**Step 1: 创建 worktree 与分支**

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-c-20260224-evidence-pack .worktrees/owner-c-20260224-evidence-pack owner-c-20260224
cd .worktrees/owner-c-20260224-evidence-pack
git status --porcelain=v1
```

Expected:
- `status` 输出为空

---

### Task C5: 给 `build_report_pack.py` 加参数与派生字段（先写测试）

**Files:**
- Modify: `scripts/build_report_pack.py`
- Create: `scripts/tests/test_build_report_pack.py`

**Step 1: 写一个失败测试（临时 outputs 目录 -> 生成 metrics.csv）**

Create: `scripts/tests/test_build_report_pack.py`

内容（最小可用示例）：
```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build_report_pack.py"


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="report_pack_test_") as td:
        root = Path(td)
        outputs = root / "outputs"
        run_dir = outputs / "gate1_selfcap_demo"  # 用路径名让脚本派生 gate/dataset
        stats_dir = run_dir / "stats"
        stats_dir.mkdir(parents=True, exist_ok=True)
        (stats_dir / "val_step0009.json").write_text(
            json.dumps({"psnr": 1.0, "ssim": 0.2, "lpips": 0.3, "num_GS": 123}),
            encoding="utf-8",
        )

        out_dir = root / "pack"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--outputs_root",
            str(outputs),
            "--out_dir",
            str(out_dir),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"build_report_pack failed:\\n{proc.stdout}\\n{proc.stderr}")

        csv_path = out_dir / "metrics.csv"
        if not csv_path.exists():
            raise AssertionError("metrics.csv missing")
        text = csv_path.read_text(encoding="utf-8")
        # 期待有派生列（gate/dataset），且 num_GS 能映射到 num_gs
        if "gate" not in text or "dataset" not in text:
            raise AssertionError(f"missing derived columns in csv header: {text.splitlines()[0]}")
        if ",123," not in text:
            raise AssertionError("expected num_gs=123 in csv rows")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: build_report_pack supports args + derived columns")
```

**Step 2: 运行测试确认失败**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/tests/test_build_report_pack.py
```

Expected:
- FAIL（当前脚本不产出到自定义 `--out_dir`，也没有派生列）

---

### Task C6: 最小实现 `build_report_pack.py` 参数化 + 派生 gate/dataset

**Files:**
- Modify: `scripts/build_report_pack.py`
- Test: `scripts/tests/test_build_report_pack.py`

**Step 1: 加 `argparse` 并保持默认行为不变**

改造点：
- 新增参数：
  - `--outputs_root`（默认：`outputs`）
  - `--out_dir`（默认：`outputs/report_pack`）
- `metrics.csv` 写入到 `<out_dir>/metrics.csv`

**Step 2: 派生列**

新增列：
- `gate`：从 `run_dir` 推断（优先规则：包含 `gate0`/`gate1`/`t0` 则填对应值，否则空）
- `dataset`：从 `run_dir` 的名字里粗略提取（例如 `gate1_selfcap_bar_8cam60f` -> `selfcap_bar_8cam60f`；提取失败则空）

保持现有列兼容：
- `num_gs` 从 stats json 的 `num_gs/num_GS/numGs` 任意 key 映射

**Step 3: 复跑测试**

Run: 同 Task C5 Step 2  
Expected: `PASS: build_report_pack supports args + derived columns`

**Step 4: 提交**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
git add scripts/build_report_pack.py scripts/tests/test_build_report_pack.py
git commit -m "feat(report-pack): add args + derive gate/dataset columns"
```

---

### Task C7: 新增 `pack_evidence.py`（可控打包 + sha256 清单）

**Files:**
- Create: `scripts/pack_evidence.py`
- Create: `scripts/tests/test_pack_evidence.py`

**Step 1: 写失败测试（只测过滤与 tar 内容，不依赖真实视频）**

Create: `scripts/tests/test_pack_evidence.py`

最小测试思路：
- 在临时目录构造一个“伪 repo”：
  - `README.md`
  - `notes/demo-runbook.md`
  - `outputs/runA/stats/val_step0001.json`
  - `outputs/runA/videos/traj_4d_step1.mp4`（写入任意字节即可）
  - `outputs/runA/ckpts/ckpt_1.pt`（应被排除）
- `subprocess.run` 调用 `pack_evidence.py --repo_root <tmp> --out_tar <tmp>/pack.tar.gz`
- 用 `tarfile` 列出 members：
  - 必须包含：`README.md`、`notes/demo-runbook.md`、`outputs/runA/stats/val_step0001.json`、`outputs/runA/videos/traj_4d_step1.mp4`
  - 必须不包含：`outputs/runA/ckpts/ckpt_1.pt`
  - 必须包含：`manifest_sha256.csv`

**Step 2: 运行测试确认失败**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/tests/test_pack_evidence.py
```

Expected:
- FAIL（脚本不存在）

**Step 3: 最小实现 `scripts/pack_evidence.py`**

要求：
- 参数：
  - `--repo_root`（默认：脚本上两级目录）
  - `--out_tar`（默认：`outputs/report_pack_<YYYY-MM-DD>.tar.gz`）
- 收集文件策略（最小但够用）：
  - 必收：`README.md`
  - 可选：`notes/*.md`（存在就收）
  - 必收：`outputs/**/stats/val_step*.json`（全部收，或只收每个 run 最新一步都可，优先做“每 run 最新”）
  - 可选：`outputs/**/videos/traj_*.mp4`（存在就收，优先收最新一步）
  - 可选：`outputs/**/t0_grad.csv`（存在就收）
  - 可选：`outputs/report_pack/*`（若存在）
- 排除目录：
  - `outputs/**/ckpts/**`
  - `outputs/**/tb/**`
  - `outputs/**/renders/**`
- 生成 `manifest_sha256.csv`（两列：`path,sha256`，路径用 repo_root 相对路径）
- `tar.gz` 内路径必须是相对路径（不允许绝对路径）

**Step 4: 复跑测试确认通过**

Expected:
- `PASS: pack_evidence excludes large dirs and writes manifest`

**Step 5: 提交**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
git add scripts/pack_evidence.py scripts/tests/test_pack_evidence.py
git commit -m "feat(evidence): add pack_evidence.py with sha256 manifest and excludes"
```

---

### Task C8: 更新 demo-runbook（只改 notes，不碰 README，避免与 A 冲突）

**Files:**
- Modify: `notes/demo-runbook.md`
- (Optional) Modify: `notes/qna.md`

**Step 1: 写入 4 条“答辩现场命令”**

在 `notes/demo-runbook.md` 增加以下结构（示例）：
1. Gate-1 数据入口（如果已存在则跳过）
2. Gate-1 训练（600 steps demo）
3. T0 审计（baseline vs zero-velocity）
4. 打包证据：`python scripts/pack_evidence.py`

**Step 2: 提交**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
git add notes/demo-runbook.md notes/qna.md 2>/dev/null || true
git commit -m "docs: update demo-runbook for evidence pack + selfcap demo"
```

---

### Task C9: GPU2 跑 600-step SelfCap demo（只产 outputs，不入库）

**Files:**
- Create: `outputs/gate1_selfcap_demo_600/*`（运行产物，不 commit）

**Step 1: 确保数据路径可见（建议在本 worktree 建软链）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
mkdir -p data
if [ ! -e data/selfcap_bar_8cam60f ]; then
  ln -s /root/projects/4d-recon/data/selfcap_bar_8cam60f data/selfcap_bar_8cam60f
fi
test -d data/selfcap_bar_8cam60f/triangulation
```

Expected:
- 最后一行退出码为 0

**Step 2: combine_frames（若已有 npz 可跳过）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
python third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
  --input-dir data/selfcap_bar_8cam60f/triangulation \
  --output-path outputs/gate1_selfcap_demo_600/keyframes_60frames_step5.npz \
  --frame-start 0 \
  --frame-end 59 \
  --keyframe-step 5
```

Expected:
- `outputs/gate1_selfcap_demo_600/keyframes_60frames_step5.npz` 存在

**Step 3: GPU2 训练 600 steps（只求稳定出视频与 stats）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
CUDA_VISIBLE_DEVICES=2 python third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
  --data-dir data/selfcap_bar_8cam60f \
  --init-npz-path outputs/gate1_selfcap_demo_600/keyframes_60frames_step5.npz \
  --result-dir outputs/gate1_selfcap_demo_600 \
  --start-frame 0 --end-frame 60 \
  --max-steps 600 --eval-steps 600 --save-steps 600 \
  --render-traj-path fixed \
  --global-scale 6
```

Expected:
- `outputs/gate1_selfcap_demo_600/videos/traj_4d_step599.mp4` 存在
- `outputs/gate1_selfcap_demo_600/stats/val_step0599.json` 存在

**Step 4: 生成 metrics.csv + 打包证据**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
$PY scripts/pack_evidence.py --repo_root . --out_tar outputs/report_pack_$(date +%F).tar.gz
```

Expected:
- `outputs/report_pack/metrics.csv` 更新
- `outputs/report_pack_YYYY-MM-DD.tar.gz` 生成且非空

