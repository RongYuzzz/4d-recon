# OpenProposal (THUman4.0 未就绪) — Preflight + Code-Only Tasks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 THUman4.0 还没下载完成时，先把“后续必需但不依赖 THUman”的环境/依赖/代码合约测试全部跑通，让 Phase 1/2 一旦数据到位即可立即开跑。

**Architecture:** 不回写/不污染既有 `protocol_v1/v2` 证据链；本计划只做 **env preflight + dataset-independent tooling/tests**。所有下载/缓存仅放本机 cache（不入库）。

**Tech Stack:** `third_party/FreeTimeGsVanilla/.venv`、`pytest`、Torch、LPIPS、VGGT(HF cache)、轻量 NPZ 工具脚本。

---

### Task 0: Preflight（确认 venv 与基础依赖）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 固定 venv python（避免脚本默认路径漂移）**

Run:
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
test -x "$VENV_PYTHON"
"$VENV_PYTHON" -V
```

Expected: `test -x` 通过，并打印 Python 版本。

**Step 2: 关键 import 自检**

Run:
```bash
"$VENV_PYTHON" -c "import torch; import torchvision; import vggt; print('torch', torch.__version__); print('ok')"
```

Expected: 打印 torch 版本与 `ok`。

---

### Task 1: 安装/验证 LPIPS（为后续 `lpips_fg` 做准备）

> 说明：当前机上该 venv 通常缺 `lpips`；若你后续要用 `--lpips_backend auto`（真实 LPIPS），这里必须补齐。

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 安装 lpips 到 FreeTimeGsVanilla venv**

Run:
```bash
"$VENV_PYTHON" -m pip install -U pip
"$VENV_PYTHON" -m pip install lpips
```

Expected: 安装成功（exit code 0）。

**Step 2: import 自检（并确认 AlexNet 权重可用）**

Run:
```bash
"$VENV_PYTHON" - <<'PY'
import lpips
import torch
print("lpips", getattr(lpips, "__version__", "<no-version>"))
m = lpips.LPIPS(net="alex").eval()
print("model_ok", type(m))
print("cuda", torch.cuda.is_available())
PY
```

Expected: 打印 `model_ok ...`。

---

### Task 2: VGGT 离线预热（确保不会在训练中途卡下载）

> 说明：本机通常已缓存 `facebook/VGGT-1B`；这里要做到 **HF_HUB_OFFLINE=1 仍可加载**。

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 离线加载自检**

Run:
```bash
export VGGT_MODEL_ID="facebook/VGGT-1B"
export VGGT_CACHE_DIR="/root/autodl-tmp/cache/vggt"
mkdir -p "$VGGT_CACHE_DIR"

HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" -c "from vggt.models.vggt import VGGT; VGGT.from_pretrained('$VGGT_MODEL_ID', cache_dir='$VGGT_CACHE_DIR'); print('ok')"
```

Expected: 打印 `ok`（且不触发下载）。

---

### Task 3: 实现 `pseudo_masks.npz` 取反工具（Phase 3 weak-fusion 必需的 dataset-independent 前置）

> 目的：trainer 的 weak-fusion 默认把 mask 解释为 dynamicness 并做 `w = 1 - alpha * mask`。  
> 如果你后续希望“相对强调动态/前景”，常见做法是把输入 mask 取反（≈ staticness），从而下调静态背景权重。

**Files:**
- Create: `scripts/invert_pseudo_masks_npz.py`
- Test: `scripts/tests/test_invert_pseudo_masks_npz_contract.py`

**Step 1: 写失败的 contract test**

Create `scripts/tests/test_invert_pseudo_masks_npz_contract.py`：
```python
#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "invert_pseudo_masks_npz.py"


def test_invert_npz_preserves_contract_and_inverts_values() -> None:
    with tempfile.TemporaryDirectory(prefix="invert_npz_") as td:
        root = Path(td)
        in_npz = root / "in.npz"
        out_npz = root / "out.npz"

        masks = np.zeros((2, 3, 4, 5), dtype=np.uint8)
        masks[0, 0, 1, 2] = 255
        masks[1, 2, 3, 4] = 7
        np.savez_compressed(
            in_npz,
            masks=masks,
            camera_names=np.asarray(["02", "03", "09"]),
            frame_start=np.int32(0),
            num_frames=np.int32(2),
            mask_downscale=np.int32(4),
        )

        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--in_npz", str(in_npz), "--out_npz", str(out_npz), "--overwrite"],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"stdout:\\n{r.stdout}\\n\\nstderr:\\n{r.stderr}"
        assert out_npz.exists()

        obj = np.load(out_npz, allow_pickle=True)
        for key in ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale"):
            assert key in obj.files
        out = obj["masks"]
        assert out.dtype == np.uint8
        assert out.shape == masks.shape
        assert int(out[0, 0, 1, 2]) == 0  # 255 -> 0
        assert int(out[1, 2, 3, 4]) == 248  # 7 -> 248
```

**Step 2: 运行 test，确认失败**

Run: `pytest -q scripts/tests/test_invert_pseudo_masks_npz_contract.py -q`

Expected: FAIL（`invert_pseudo_masks_npz.py` 不存在）。

**Step 3: 实现脚本（最小功能）**

Create `scripts/invert_pseudo_masks_npz.py`：
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def _fail(msg: str) -> None:
    raise SystemExit(f"[InvertPseudoMasks][ERROR] {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Invert uint8 pseudo masks in a cue_mining pseudo_masks.npz.")
    ap.add_argument("--in_npz", required=True, help="Input pseudo_masks.npz")
    ap.add_argument("--out_npz", required=True, help="Output npz path")
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    in_npz = Path(args.in_npz).resolve()
    out_npz = Path(args.out_npz).resolve()
    if not in_npz.exists():
        _fail(f"missing in_npz: {in_npz}")
    if out_npz.exists() and not args.overwrite:
        _fail(f"out_npz exists: {out_npz} (use --overwrite)")
    out_npz.parent.mkdir(parents=True, exist_ok=True)

    with np.load(in_npz, allow_pickle=True) as obj:
        missing = [k for k in ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale") if k not in obj]
        if missing:
            _fail(f"npz missing keys: {missing}")
        masks = np.asarray(obj["masks"])
        if masks.dtype != np.uint8:
            _fail(f"expected masks dtype=uint8, got {masks.dtype}")
        out_masks = (255 - masks).astype(np.uint8)

        np.savez_compressed(
            out_npz,
            masks=out_masks,
            camera_names=np.asarray(obj["camera_names"]),
            frame_start=np.int32(int(obj["frame_start"])),
            num_frames=np.int32(int(obj["num_frames"])),
            mask_downscale=np.int32(int(obj["mask_downscale"])),
        )

    print(f"[InvertPseudoMasks] wrote: {out_npz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: 运行 test，确认通过**

Run: `pytest -q scripts/tests/test_invert_pseudo_masks_npz_contract.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/invert_pseudo_masks_npz.py scripts/tests/test_invert_pseudo_masks_npz_contract.py
git commit -m "feat(cue-mining): add invert tool for pseudo_masks.npz"
```

---

### Task 4: 全量单测（防止后续“数据到了才发现脚本坏了”）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: `scripts/tests/*`

**Step 1: 跑单测**

Run: `pytest -q`

Expected: PASS（若有失败，先修到只剩与 THUman 下载无关的部分）。

