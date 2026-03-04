# OpenProposal Phase 1 (THUman4.0) — Dataset + Metrics Implementation Plan

> **Execution note:** 按 Task 顺序逐条落地；每个 Task 结束必须能用文件/命令复核通过再进入下一步。

**Goal:** 在 THUman4.0 的一个小子集上跑通 **“数据适配 → COLMAP/sparse → triangulation → 训练 smoke → fg-masked 指标（PSNR/LPIPS）”** 的可复核闭环，为 Phase 2–5 提供落地载体。

**Architecture:** 本 Phase 是总计划 `docs/plans/2026-03-02-align-opening-proposal-v1.md` 的 Phase 1 落地版（不得与其矛盾）。所有新实验统一走 `protocol_v3_openproposal`（不回写 `protocol_v1/v2` 证据链）。评测 **local-eval only**：不把公开数据集帧/GT mask 写入 git/PR/report-pack。

**Tech Stack:** Python (`numpy`, `Pillow`), optional `torch+lpips`（仅评测时用）, COLMAP CLI, repo scripts (`scripts/export_triangulation_from_colmap_sparse.py`, existing runners), `pytest`.

**2026-03-04 状态更新（重要）：**
- 本机 THUman4.0 `subject00` 已解压到：`data/raw/thuman4/subject00`（包含 `images/` 与 `masks/`）
- THUman 的 `masks/` 输入是 `*.jpg`（不是 `*.png`）；本 repo 的 adapter 会输出为 `masks/<cam>/<frame>.png`
- `cam00` 在前 60 帧里存在缺帧（至少 `00000020/00000044`），会导致 adapter 失败；本 Phase 1 推荐直接用 `cam01..cam08`

> 若你当前 repo 已包含 `scripts/adapt_thuman4_release_to_freetime.py` / `scripts/eval_masked_metrics.py` 等脚本，则 **Task 1–5 属于“已落地的实现过程”**，执行时可直接跳到 **Task 6**。

---

### Task 0: Preflight（环境与合规）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 确认 local-eval 规则写死**

在本 Phase 的所有文档/脚本里遵守并显式打印：
- 不提交 `data/` 与 `outputs/`（仓库已 gitignore）
- 不把 GT mask/GT 图像拼图/对比视频写进 `docs/report_pack/**`
- 允许在本机 `outputs/qualitative_local/**` 留存可视化（不入证据链）

**Step 2: 确认依赖**

Run（仅自检，不需要改代码）：
- `colmap -h | head`
- `python3 -c "import numpy, PIL; print('ok')"`
- （可选，后续评测用）`VENV_PYTHON="${VENV_PYTHON:-$(pwd)/third_party/FreeTimeGsVanilla/.venv/bin/python}"; "$VENV_PYTHON" -c "import torch; print(torch.__version__)" || true`

Expected:
- COLMAP 可用
- `numpy` / `Pillow` 可 import

**Step 3: 确认 THUman raw 已就绪（本机路径）**

Run:
```bash
test -d data/raw/thuman4/subject00/images
test -d data/raw/thuman4/subject00/masks
```

---

### Task 1: 新协议文件（仅 v3，不改动 v1/v2）

**Files:**
- Create: `docs/protocols/protocol_v3_openproposal.yaml`
- Modify: *(none)*
- Test: *(none)*

**Step 1: 添加最小协议骨架（仅描述 v3）**

新增 `docs/protocols/protocol_v3_openproposal.yaml`（先用占位路径，后续按本机真实路径补齐；但字段名必须先冻结，避免 Phase 4 “提升”不可复核）：

```yaml
id: protocol_v3_openproposal_thuman4_subject00_8cam60f
frozen_date: "2026-03-03"

dataset:
  name: thuman4.0
  # local-eval only (do NOT commit frames/masks)
  root: "data/thuman4_subject00_8cam60f"
  frames:
    start: 0
    end_exclusive: 60
  cameras:
    used: ["02", "03", "04", "05", "06", "07", "08", "09"]
    train: ["02", "03", "04", "05", "06", "07"]
    val: ["08"]
    test: ["09"]
  image_downscale: 2
  mask:
    available: true
    type: "dataset-provided foreground matte"
    binarize_threshold: 0.5

metrics:
  full_frame:
    - psnr
    - ssim
    - lpips
    - tlpips
  foreground_masked:
    # NOTE: only valid when dataset provides masks/
    - psnr_fg
    - lpips_fg
  segmentation:
    # NOTE: enable only when pred_fg source is defined (Phase 2+)
    - miou_fg

masked_eval:
  bbox_margin_px: 32
  roi_pipeline: "mask -> bbox crop (+margin) -> fill-black outside mask -> metric"
  mask_source_default: "dataset"
  pred_fg_default:
    type: "pseudo_masks.npz"
    threshold: 0.5
```

**Step 2: 轻量自检**

Run: `python3 -c "from pathlib import Path; assert Path('docs/protocols/protocol_v3_openproposal.yaml').exists(); print('ok')"`

Expected: `ok`

**Step 3: Commit**

```bash
git add docs/protocols/protocol_v3_openproposal.yaml
git commit -m "docs(protocol): add protocol_v3_openproposal skeleton for THUman4.0"
```

---

### Task 2: THUman4.0 → FreeTime 数据适配脚本（TDD）

**Files:**
- Create: `scripts/adapt_thuman4_release_to_freetime.py`
- Test: `scripts/tests/test_adapt_thuman4_release_contract.py`

**Step 1: 写一个失败的 contract test（先锁 data contract）**

新增 `scripts/tests/test_adapt_thuman4_release_contract.py`：

```python
#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "adapt_thuman4_release_to_freetime.py"


def _write_rgb(path: Path, color: tuple[int, int, int]) -> None:
    arr = np.zeros((16, 20, 3), dtype=np.uint8)
    arr[..., 0] = color[0]
    arr[..., 1] = color[1]
    arr[..., 2] = color[2]
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path, quality=95)


def _write_mask(path: Path, on: bool) -> None:
    arr = np.zeros((16, 20), dtype=np.uint8)
    if on:
        arr[3:13, 4:16] = 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)


def test_adapter_builds_expected_layout() -> None:
    with tempfile.TemporaryDirectory(prefix="thuman4_adapter_") as td:
        root = Path(td)
        src = root / "thuman_subject00"
        # Expected input layout for this adapter (minimal):
        #   images/<cam>/<frame>.(jpg|png)
        #   masks/<cam>/<frame>.png
        for cam in ["c0", "c1"]:
            for t in range(3):
                _write_rgb(src / "images" / cam / f"{t:06d}.jpg", (30 + t, 50, 70))
                _write_mask(src / "masks" / cam / f"{t:06d}.png", on=(t != 0))

        out_dir = root / "out_data"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--input_dir",
            str(src),
            "--output_dir",
            str(out_dir),
            "--camera_ids",
            "c0,c1",
            "--output_camera_ids",
            "02,03",
            "--frame_start",
            "0",
            "--num_frames",
            "3",
            "--image_downscale",
            "2",
            "--copy_mode",
            "copy",
            "--overwrite",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 0, f"stdout:\\n{r.stdout}\\n\\nstderr:\\n{r.stderr}"

        # Output contract: images/<cam>/<frame>.jpg and masks/<cam>/<frame>.png
        assert (out_dir / "images" / "02" / "000000.jpg").exists()
        assert (out_dir / "images" / "03" / "000002.jpg").exists()
        assert (out_dir / "masks" / "02" / "000001.png").exists()
        assert (out_dir / "masks" / "03" / "000002.png").exists()
        assert (out_dir / "adapt_manifest.csv").exists()
        assert (out_dir / "adapt_scene.json").exists()
```

**Step 2: 运行 test，确认失败**

Run: `pytest -q scripts/tests/test_adapt_thuman4_release_contract.py -q`

Expected: FAIL（脚本不存在或返回码非 0）

**Step 3: 实现最小适配器脚本**

新增 `scripts/adapt_thuman4_release_to_freetime.py`（保持小而稳；只做 Phase 1 必需功能）：

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


def _fail(msg: str) -> None:
    raise SystemExit(f"[THUman4Adapter][ERROR] {msg}")


def _parse_csv_list(raw: str) -> list[str]:
    items = [x.strip() for x in (raw or "").split(",") if x.strip()]
    if not items:
        _fail("empty list")
    return items


def _index_numeric_frames(dir_path: Path) -> dict[int, Path]:
    frame_map: dict[int, Path] = {}
    if not dir_path.is_dir():
        _fail(f"missing dir: {dir_path}")
    for p in dir_path.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() not in {\".jpg\", \".jpeg\", \".png\"}:
            continue
        try:
            idx = int(p.stem)
        except ValueError:
            continue
        frame_map[idx] = p
    return frame_map


def _resize_rgb(im: Image.Image, downscale: int) -> Image.Image:
    if downscale <= 1:
        return im
    w, h = im.size
    out_w = max(1, w // downscale)
    out_h = max(1, h // downscale)
    return im.resize((out_w, out_h), resample=Image.Resampling.BILINEAR)


def _resize_mask(im: Image.Image, downscale: int) -> Image.Image:
    if downscale <= 1:
        return im
    w, h = im.size
    out_w = max(1, w // downscale)
    out_h = max(1, h // downscale)
    return im.resize((out_w, out_h), resample=Image.Resampling.NEAREST)


@dataclass(frozen=True)
class ManifestRow:
    input_cam: str
    output_cam: str
    input_frame: int
    output_frame: int
    input_image: str
    output_image: str
    input_mask: str
    output_mask: str


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Adapt THUman4.0 subject to FreeTime-compatible layout (local-eval only).")
    ap.add_argument(\"--input_dir\", required=True, help=\"THUman subject dir (expects images/ and masks/)\")
    ap.add_argument(\"--output_dir\", required=True, help=\"Output data dir under repo data/\")
    ap.add_argument(\"--camera_ids\", required=True, help=\"Comma-separated input camera folder names\")
    ap.add_argument(\"--output_camera_ids\", required=True, help=\"Comma-separated output camera ids (same length)\")
    ap.add_argument(\"--frame_start\", type=int, default=0)
    ap.add_argument(\"--num_frames\", type=int, default=60)
    ap.add_argument(\"--image_downscale\", type=int, default=2)
    ap.add_argument(\"--copy_mode\", choices=[\"copy\"], default=\"copy\")
    ap.add_argument(\"--overwrite\", action=\"store_true\")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    if output_dir.exists() and not args.overwrite:
        _fail(f\"output_dir exists (use --overwrite): {output_dir}\")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    in_cams = _parse_csv_list(args.camera_ids)
    out_cams = _parse_csv_list(args.output_camera_ids)
    if len(in_cams) != len(out_cams):
        _fail(f\"camera_ids length mismatch: {len(in_cams)} vs {len(out_cams)}\")

    frame_start = int(args.frame_start)
    num_frames = int(args.num_frames)
    if num_frames <= 0:
        _fail(\"num_frames must be > 0\")
    image_downscale = int(args.image_downscale)
    if image_downscale <= 0:
        _fail(\"image_downscale must be >= 1\")

    images_in_root = input_dir / \"images\"
    masks_in_root = input_dir / \"masks\"
    if not images_in_root.is_dir():
        _fail(f\"missing images/: {images_in_root}\")
    if not masks_in_root.is_dir():
        _fail(f\"missing masks/: {masks_in_root}\")

    images_out_root = output_dir / \"images\"
    masks_out_root = output_dir / \"masks\"
    images_out_root.mkdir(parents=True, exist_ok=True)
    masks_out_root.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[ManifestRow] = []
    selected_frames = [frame_start + i for i in range(num_frames)]

    for in_cam, out_cam in zip(in_cams, out_cams):
        in_img_dir = images_in_root / in_cam
        in_msk_dir = masks_in_root / in_cam
        img_map = _index_numeric_frames(in_img_dir)
        msk_map = _index_numeric_frames(in_msk_dir)
        for local_i, frame_idx in enumerate(selected_frames):
            if frame_idx not in img_map:
                _fail(f\"missing image frame {frame_idx} in {in_img_dir}\")
            if frame_idx not in msk_map:
                _fail(f\"missing mask frame {frame_idx} in {in_msk_dir}\")
            img_p = img_map[frame_idx]
            msk_p = msk_map[frame_idx]

            out_img_dir = images_out_root / out_cam
            out_msk_dir = masks_out_root / out_cam
            out_img_dir.mkdir(parents=True, exist_ok=True)
            out_msk_dir.mkdir(parents=True, exist_ok=True)

            out_frame = local_i
            out_img_path = out_img_dir / f\"{out_frame:06d}.jpg\"
            out_msk_path = out_msk_dir / f\"{out_frame:06d}.png\"

            with Image.open(img_p) as im:
                rgb = im.convert(\"RGB\")
                rgb = _resize_rgb(rgb, image_downscale)
                rgb.save(out_img_path, quality=95)
            with Image.open(msk_p) as im:
                m = im.convert(\"L\")
                m = _resize_mask(m, image_downscale)
                m.save(out_msk_path)

            manifest_rows.append(
                ManifestRow(
                    input_cam=in_cam,
                    output_cam=out_cam,
                    input_frame=int(frame_idx),
                    output_frame=int(out_frame),
                    input_image=str(img_p),
                    output_image=str(out_img_path),
                    input_mask=str(msk_p),
                    output_mask=str(out_msk_path),
                )
            )

    (output_dir / \"adapt_scene.json\").write_text(
        json.dumps(
            {
                \"input_dir\": str(input_dir),
                \"output_dir\": str(output_dir),
                \"input_cameras\": in_cams,
                \"output_cameras\": out_cams,
                \"frame_start\": frame_start,
                \"num_frames\": num_frames,
                \"image_downscale\": image_downscale,
            },
            indent=2,
        )
        + \"\\n\",
        encoding=\"utf-8\",
    )

    with (output_dir / \"adapt_manifest.csv\").open(\"w\", encoding=\"utf-8\", newline=\"\") as f:
        w = csv.writer(f)
        w.writerow(
            [
                \"input_cam\",
                \"output_cam\",
                \"input_frame\",
                \"output_frame\",
                \"input_image\",
                \"output_image\",
                \"input_mask\",
                \"output_mask\",
            ]
        )
        for row in manifest_rows:
            w.writerow(
                [
                    row.input_cam,
                    row.output_cam,
                    row.input_frame,
                    row.output_frame,
                    row.input_image,
                    row.output_image,
                    row.input_mask,
                    row.output_mask,
                ]
            )

    print(f\"[THUman4Adapter] wrote: {output_dir}\")
    print(f\"[THUman4Adapter] cameras: {len(out_cams)} {out_cams}\")
    print(f\"[THUman4Adapter] frames: {num_frames} (start={frame_start})\")
    print(\"[THUman4Adapter] NOTE: local-eval only; do NOT commit data/ outputs/\")


if __name__ == \"__main__\":
    main()
```

**Step 4: 运行 test，确认通过**

Run: `pytest -q scripts/tests/test_adapt_thuman4_release_contract.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/adapt_thuman4_release_to_freetime.py scripts/tests/test_adapt_thuman4_release_contract.py
git commit -m "feat(data): add THUman4.0 adapter to FreeTime layout (local-eval)"
```

---

### Task 3: THUman 子集上跑 COLMAP + triangulation（runbook 级）

**Files:**
- Modify: *(none)*
- Create: `notes/openproposal_phase1_colmap_runbook.md`
- Test: *(none)*

**Step 1: 写 runbook 文档（只写命令与期望输出）**

新增 `notes/openproposal_phase1_colmap_runbook.md`，包含如下命令模板（把 `<DATA_DIR>` 替换成你的本机输出目录，例如 `data/thuman4_subject00_8cam60f`）：

```bash
# 0) paths
DATA_DIR="<DATA_DIR>"  # contains images/ and masks/
# IMPORTANT:
# - Do NOT run COLMAP on "$DATA_DIR/images" (8 cams × 60 frames). FreeTimeParser assumes sparse/0 has
#   exactly ONE image per camera folder; otherwise camera_names length != camera folder count and training will crash.
# - We therefore build a reference-image subset (1 frame per cam) for COLMAP, but still keep "$DATA_DIR/images"
#   as the training images.

REF_IMG_DIR="$DATA_DIR/_colmap_ref_images"  # local scratch (not committed)
REF_DB="$DATA_DIR/colmap_ref.db"

rm -rf "$REF_IMG_DIR" "$REF_DB" "$DATA_DIR/sparse"
mkdir -p "$REF_IMG_DIR"

# 0.1) Reference images: 1 frame per cam (symlink) so COLMAP sparse/0 has 8 images total.
# NOTE: Camera folder names MUST match "$DATA_DIR/images/<cam>/..." exactly (byte-by-byte).
for cam in 02 03 04 05 06 07 08 09; do
  mkdir -p "$REF_IMG_DIR/$cam"
  ln -sf "$(realpath "$DATA_DIR/images/$cam/000000.jpg")" "$REF_IMG_DIR/$cam/000000.jpg"
done

# 1) COLMAP database + features
colmap feature_extractor \
  --database_path "$REF_DB" \
  --image_path "$REF_IMG_DIR" \
  --ImageReader.camera_model PINHOLE \
  --ImageReader.single_camera 0 \
  --SiftExtraction.use_gpu 1

# 2) matching (exhaustive; if too slow, shrink frames/cams; do NOT tune forever)
colmap exhaustive_matcher \
  --database_path "$REF_DB" \
  --SiftMatching.use_gpu 1

# 3) mapping -> outputs models under $DATA_DIR/sparse/{0,1,...}
colmap mapper \
  --database_path "$REF_DB" \
  --image_path "$REF_IMG_DIR" \
  --output_path "$DATA_DIR/sparse"

test -f "$DATA_DIR/sparse/0/cameras.bin"
test -f "$DATA_DIR/sparse/0/images.bin"
test -f "$DATA_DIR/sparse/0/points3D.bin"
```

并补一段止损规则（与总计划一致）：
- 如果 mapper 失败：优先 **换参考帧**（例如把 `000000.jpg` 换成更清晰/纹理更足的帧）或减少 cams（先 4 cams 跑通），而不是无底洞调参。
- 约束：优先坚持 `PINHOLE`（避免引入畸变→undistort/crop，导致 mask 与 render/GT 对齐风险）。

**Step 2: Commit**

```bash
git add notes/openproposal_phase1_colmap_runbook.md
git commit -m "docs(notes): add THUman4 Phase1 COLMAP runbook"
```

---

### Task 4: 导出 triangulation（复用现有脚本）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 从 sparse/0 导出逐帧点（先用 visible_per_frame）**

NOTE:
- 由于 Task 3 的 `sparse/0` 是“每相机 1 帧”的参考重建，`visible_per_frame` 预期只会导出 **极少帧**（通常只有 `frame000000`）。这对 Phase 1 的 smoke 足够；不要在本阶段强求 60 帧都具备 triangulation。

Run:
```bash
DATA_DIR="<DATA_DIR>"
python3 scripts/export_triangulation_from_colmap_sparse.py \
  --colmap_data_dir "$DATA_DIR" \
  --out_dir "$DATA_DIR/triangulation" \
  --mode visible_per_frame \
  --frame_start 0 \
  --frame_end 60 \
  --max_points 200000 \
  --seed 0 \
  --keyframe_step 1 \
  --keyframe_emit all
test -f "$DATA_DIR/triangulation/points3d_frame000000.npy"
```

Expected:
- `triangulation/points3d_frame000000.npy` 存在

**Step 2: 失败时的止损切换（只做 smoke）**

如果 `visible_per_frame` 因 points 过少或异常失败，先切到：
```bash
python3 scripts/export_triangulation_from_colmap_sparse.py \
  --colmap_data_dir "$DATA_DIR" \
  --out_dir "$DATA_DIR/triangulation" \
  --mode static_copy \
  --frame_start 0 \
  --frame_end 60 \
  --max_points 200000 \
  --seed 0 \
  --keyframe_step 1 \
  --keyframe_emit all
```

---

### Task 5: fg-masked 指标离线评测脚本（TDD，可在无 torch 环境跑 dummy）

**Files:**
- Create: `scripts/eval_masked_metrics.py`
- Test: `scripts/tests/test_eval_masked_metrics_contract.py`

**IMPORTANT（避免踩坑）：**
- `simple_trainer_freetime_4d_pure_relocation.py` 保存的 `renders/*.png` 是 **GT|Pred 横向拼接**（宽度 `2W`）。
- 本 evaluator 必须以该拼接图为输入并先 split（左半 GT、右半 Pred），不要直接把 render 当成 Pred 去和 `data_dir/images` 比。

**Step 1: 写失败的 contract test**

新增 `scripts/tests/test_eval_masked_metrics_contract.py`：

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "eval_masked_metrics.py"


def _write_rgb(path: Path, seed: int) -> None:
    rng = np.random.default_rng(seed)
    arr = (rng.random((32, 40, 3)) * 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)


def _write_mask(path: Path) -> None:
    arr = np.zeros((32, 40), dtype=np.uint8)
    arr[8:24, 10:30] = 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)


def _write_canvas_concat_gt_pred(path: Path, seed_gt: int, seed_pred: int) -> None:
    rng_gt = np.random.default_rng(seed_gt)
    rng_pd = np.random.default_rng(seed_pred)
    gt = (rng_gt.random((32, 40, 3)) * 255).astype(np.uint8)
    pd = (rng_pd.random((32, 40, 3)) * 255).astype(np.uint8)
    canvas = np.concatenate([gt, pd], axis=1)  # [H, 2W, 3]
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(canvas).save(path)


def test_eval_masked_metrics_emits_required_fields() -> None:
    with tempfile.TemporaryDirectory(prefix="eval_masked_metrics_") as td:
        root = Path(td)
        data_dir = root / "data_scene"
        cam = "09"
        for t in range(3):
            _write_rgb(data_dir / "images" / cam / f"{t:06d}.jpg", seed=100 + t)
            _write_mask(data_dir / "masks" / cam / f"{t:06d}.png")

        result_dir = root / "run"
        (result_dir / "stats").mkdir(parents=True, exist_ok=True)
        (result_dir / "renders").mkdir(parents=True, exist_ok=True)
        # Minimal cfg.yml scalars used by the evaluator.
        (result_dir / "cfg.yml").write_text(
            "\\n".join(
                [
                    f"start_frame: 0",
                    f"end_frame: 3",
                    f"test_camera_names: {cam}",
                    f"eval_sample_every_test: 1",
                ]
            )
            + "\\n",
            encoding="utf-8",
        )
        # Trainer stats file (we just need it to exist).
        (result_dir / "stats" / "test_step0599.json").write_text(
            json.dumps({"psnr": 1.0, "ssim": 0.1, "lpips": 0.9, "tlpips": 0.01}) + "\\n",
            encoding="utf-8",
        )
        # Fake renders: mimic trainer output (GT|Pred concatenated along width).
        for i in range(3):
            _write_canvas_concat_gt_pred(
                result_dir / "renders" / f"test_step599_{i:04d}.png",
                seed_gt=200 + i,
                seed_pred=300 + i,
            )

        out_json = result_dir / "stats_masked" / "test_step0599.json"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir",
            str(data_dir),
            "--result_dir",
            str(result_dir),
            "--stage",
            "test",
            "--step",
            "599",
            "--mask_source",
            "dataset",
            "--bbox_margin_px",
            "4",
            "--lpips_backend",
            "dummy",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 0, f"stdout:\\n{r.stdout}\\n\\nstderr:\\n{r.stderr}"
        assert out_json.exists()

        obj = json.loads(out_json.read_text(encoding="utf-8"))
        for key in ("psnr", "ssim", "lpips", "tlpips", "psnr_fg", "lpips_fg", "mask_source"):
            assert key in obj, f"missing key: {key}"
        assert obj["mask_source"] == "dataset"
        assert obj["num_fg_frames"] > 0
```

**Step 2: 运行 test，确认失败**

Run: `pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q`

Expected: FAIL（脚本不存在或返回码非 0）

**Step 3: 实现离线 evaluator（字段名冻结）**

新增 `scripts/eval_masked_metrics.py`：

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _fail(msg: str) -> None:
    raise SystemExit(f"[EvalMaskedMetrics][ERROR] {msg}")


def _load_rgb01(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    return arr


def _load_mask01(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        arr = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    return np.clip(arr, 0.0, 1.0)


def _psnr(a01: np.ndarray, b01: np.ndarray) -> float:
    diff = (a01.astype(np.float32) - b01.astype(np.float32)).reshape(-1)
    mse = float(np.mean(diff * diff))
    if mse <= 1e-12:
        return 99.0
    return 10.0 * math.log10(1.0 / mse)


class _LPIPS:
    def __init__(self, backend: str):
        self.backend = backend
        self._model = None
        self._torch = None
        self._device = "cpu"

        if backend == "none":
            return
        if backend == "dummy":
            return
        if backend != "auto":
            _fail(f"unsupported lpips_backend: {backend}")

        try:
            import torch  # type: ignore
            import lpips  # type: ignore
        except Exception as exc:  # noqa: BLE001
            _fail(f"lpips_backend=auto requires torch+lpips installed: {exc}")

        self._torch = torch
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = lpips.LPIPS(net="alex").to(self._device).eval()

    def __call__(self, a01: np.ndarray, b01: np.ndarray) -> float | None:
        if self.backend == "none":
            return None
        if self.backend == "dummy":
            return float(np.mean(np.abs(a01.astype(np.float32) - b01.astype(np.float32))))

        assert self._torch is not None and self._model is not None
        torch = self._torch
        a = torch.from_numpy(a01.transpose(2, 0, 1)[None, ...]).to(self._device)
        b = torch.from_numpy(b01.transpose(2, 0, 1)[None, ...]).to(self._device)
        a = a * 2.0 - 1.0
        b = b * 2.0 - 1.0
        with torch.no_grad():
            v = self._model(a, b)
        return float(v.detach().float().cpu().item())


def _read_cfg_scalars(cfg_path: Path) -> dict[str, str]:
    scalars: dict[str, str] = {}
    for line in cfg_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("- "):
            continue
        if raw.startswith("!!python"):
            continue
        if raw[0].isspace():
            continue
        if ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        k = k.strip()
        v = v.strip()
        if not k or not v:
            continue
        scalars[k] = v
    return scalars


@dataclass(frozen=True)
class _BBox:
    x0: int
    y0: int
    x1: int
    y1: int


def _bbox_from_mask(mask01: np.ndarray, thr: float, margin: int) -> _BBox | None:
    m = mask01 > float(thr)
    if not bool(np.any(m)):
        return None
    ys, xs = np.where(m)
    y0 = int(ys.min())
    y1 = int(ys.max()) + 1
    x0 = int(xs.min())
    x1 = int(xs.max()) + 1
    y0 = max(0, y0 - margin)
    x0 = max(0, x0 - margin)
    y1 = min(int(mask01.shape[0]), y1 + margin)
    x1 = min(int(mask01.shape[1]), x1 + margin)
    if x1 <= x0 or y1 <= y0:
        return None
    return _BBox(x0=x0, y0=y0, x1=x1, y1=y1)


_RENDER_RE = re.compile(r"^(val|test)_step(\d+)_([0-9]{4})\\.png$")


def _list_renders(renders_dir: Path, stage: str, step: int) -> list[Path]:
    prefix = f"{stage}_step{step}_"
    files = [p for p in renders_dir.iterdir() if p.is_file() and p.name.startswith(prefix) and p.suffix.lower() == ".png"]
    def key(p: Path) -> int:
        m = _RENDER_RE.match(p.name)
        if not m:
            return 10**9
        return int(m.group(3))
    return sorted(files, key=key)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Compute foreground-masked PSNR/LPIPS from trainer renders + dataset masks.")
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--result_dir", required=True)
    ap.add_argument("--stage", choices=["val", "test"], required=True)
    ap.add_argument("--step", type=int, required=True, help="Trainer step, e.g. 599")
    ap.add_argument("--mask_source", choices=["dataset", "pseudo_mask", "none"], default="dataset")
    ap.add_argument("--pred_mask_npz", default="", help="pseudo_masks.npz (required when mask_source=pseudo_mask or when computing miou_fg)")
    ap.add_argument("--bbox_margin_px", type=int, default=32)
    ap.add_argument("--mask_thr", type=float, default=0.5, help="Threshold to derive binary mask for bbox+fill-black")
    ap.add_argument("--lpips_backend", choices=["auto", "dummy", "none"], default="auto")
    ap.add_argument("--compute_miou", action="store_true", help="Compute miou_fg when both GT and pred masks are available")
    return ap.parse_args()


def _load_pred_mask_tv(pred_npz: Path, camera: str, t_local: int) -> np.ndarray:
    with np.load(pred_npz, allow_pickle=True) as z:
        masks = np.asarray(z["masks"])
        cams = [str(x) for x in z["camera_names"].tolist()]
        frame_start = int(z["frame_start"])
        if t_local < 0 or t_local >= int(z["num_frames"]):
            _fail(f"t_local out of range for pred masks: {t_local}")
        if camera not in cams:
            _fail(f"camera '{camera}' not found in pred mask npz cameras={cams}")
        v = cams.index(camera)
        m = masks[t_local, v]
        m01 = m.astype(np.float32)
        if float(m01.max()) > 1.0:
            m01 = m01 / 255.0
        return np.clip(m01, 0.0, 1.0)


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    result_dir = Path(args.result_dir).resolve()
    stage = str(args.stage)
    step = int(args.step)
    margin = int(args.bbox_margin_px)

    cfg_path = result_dir / "cfg.yml"
    if not cfg_path.exists():
        _fail(f"missing cfg.yml: {cfg_path}")
    cfg = _read_cfg_scalars(cfg_path)

    start_frame = int(cfg.get("start_frame", "0"))
    end_frame = int(cfg.get("end_frame", "0"))
    if end_frame <= start_frame:
        _fail(f"invalid frame range in cfg.yml: start={start_frame} end={end_frame}")
    num_frames = end_frame - start_frame

    if stage == "test":
        cam = cfg.get("test_camera_names", "").strip()
        sample_every = int(cfg.get("eval_sample_every_test", "1"))
    else:
        cam = cfg.get("val_camera_names", "").strip()
        sample_every = int(cfg.get("eval_sample_every", "1"))
    if not cam or "," in cam:
        _fail(f"evaluator expects single {stage} camera; got: '{cam}'")
    if sample_every <= 0:
        _fail(f"invalid eval_sample_every: {sample_every}")

    gt_msk_dir = data_dir / "masks" / cam
    renders_dir = result_dir / "renders"
    stats_in = result_dir / "stats" / f"{stage}_step{step:04d}.json"

    render_files = _list_renders(renders_dir, stage=stage, step=step)
    frame_indices = list(range(start_frame, end_frame, sample_every))
    if len(render_files) != len(frame_indices):
        _fail(
            f"render count mismatch: renders={len(render_files)} vs expected_frames={len(frame_indices)} "
            f"(start={start_frame} end={end_frame} every={sample_every})"
        )

    lpips_fn = _LPIPS(args.lpips_backend)
    psnr_list: list[float] = []
    lpips_list: list[float] = []
    iou_list: list[float] = []

    pred_npz = Path(args.pred_mask_npz).resolve() if args.pred_mask_npz else None
    if args.mask_source == "pseudo_mask" and not pred_npz:
        _fail("--pred_mask_npz required when --mask_source=pseudo_mask")

    for _, (frame_idx, render_path) in enumerate(zip(frame_indices, render_files)):
        frame_offset = int(frame_idx - start_frame)
        canvas = _load_rgb01(render_path)
        if canvas.shape[1] % 2 != 0:
            _fail(f"expected concat render canvas (GT|Pred) with even width; got {canvas.shape} at {render_path}")
        w = int(canvas.shape[1] // 2)
        gt = canvas[:, :w, :]
        pred = canvas[:, w:, :]
        if gt.shape != pred.shape:
            _fail(f"unexpected split shapes gt={gt.shape} pred={pred.shape} for {render_path}")

        if args.mask_source == "none":
            continue

        if args.mask_source == "dataset":
            m_path = gt_msk_dir / f"{frame_offset:06d}.png"
            if not m_path.exists():
                _fail(f"missing GT mask: {m_path}")
            mask01 = _load_mask01(m_path)
        else:
            assert pred_npz is not None
            mask01_small = _load_pred_mask_tv(pred_npz, camera=cam, t_local=frame_offset)
            # Upsample pred mask to image resolution
            mask_img = Image.fromarray((mask01_small * 255.0).astype(np.uint8), mode="L")
            mask_img = mask_img.resize((gt.shape[1], gt.shape[0]), resample=Image.Resampling.BILINEAR)
            mask01 = np.asarray(mask_img, dtype=np.float32) / 255.0
        if mask01.shape[:2] != gt.shape[:2]:
            _fail(f"mask/gt shape mismatch: mask={mask01.shape} gt={gt.shape} (did you downscale masks with images?)")

        bbox = _bbox_from_mask(mask01, thr=float(args.mask_thr), margin=margin)
        if bbox is None:
            continue
        gt_c = gt[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1].copy()
        pred_c = pred[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1].copy()
        m_c = mask01[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1]
        keep = (m_c > float(args.mask_thr)).astype(np.float32)[..., None]
        gt_c *= keep
        pred_c *= keep

        psnr_list.append(_psnr(pred_c, gt_c))
        v_lpips = lpips_fn(pred_c, gt_c)
        if v_lpips is not None:
            lpips_list.append(float(v_lpips))

        if args.compute_miou:
            if pred_npz is None:
                _fail("--pred_mask_npz required when --compute_miou")
            if args.mask_source != "dataset":
                _fail("--compute_miou requires --mask_source=dataset (GT mask provides gt_fg)")
            # IoU between pred_fg (pseudo mask) and dataset-provided gt_fg (full-frame).
            gt_bin = (mask01 > float(args.mask_thr))
            pred01_small = _load_pred_mask_tv(pred_npz, camera=cam, t_local=frame_offset)
            pred_img = Image.fromarray((pred01_small * 255.0).astype(np.uint8), mode="L")
            pred_img = pred_img.resize((gt.shape[1], gt.shape[0]), resample=Image.Resampling.BILINEAR)
            pred01 = np.asarray(pred_img, dtype=np.float32) / 255.0
            pred_bin = (pred01 > float(args.mask_thr))
            inter = float(np.logical_and(gt_bin, pred_bin).sum())
            union = float(np.logical_or(gt_bin, pred_bin).sum())
            if union > 0:
                iou_list.append(inter / union)

    base_stats: dict[str, Any] = {}
    if stats_in.exists():
        try:
            base_stats = json.loads(stats_in.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            base_stats = {}

    out = {
        "stage": stage,
        "step": step,
        "mask_source": args.mask_source,
        "bbox_margin_px": margin,
        "mask_thr": float(args.mask_thr),
        "psnr": base_stats.get("psnr", ""),
        "ssim": base_stats.get("ssim", ""),
        "lpips": base_stats.get("lpips", ""),
        "tlpips": base_stats.get("tlpips", ""),
        "psnr_fg": float(np.mean(psnr_list)) if psnr_list else float("nan"),
        "lpips_fg": float(np.mean(lpips_list)) if lpips_list else float("nan"),
        "num_fg_frames": int(len(psnr_list)),
        "num_frames": int(num_frames),
    }
    if iou_list:
        out["miou_fg"] = float(np.mean(iou_list))

    out_dir = result_dir / "stats_masked"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stage}_step{step:04d}.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"[EvalMaskedMetrics] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4: 运行 test，确认通过**

Run: `pytest -q scripts/tests/test_eval_masked_metrics_contract.py -q`

Expected: PASS（dummy LPIPS）

**Step 5: Commit**

```bash
git add scripts/eval_masked_metrics.py scripts/tests/test_eval_masked_metrics_contract.py
git commit -m "feat(eval): add fg-masked PSNR/LPIPS evaluator (local-eval)"
```

---

### Task 6: 在 THUman 子集上跑一次最小训练 + masked eval（smoke）

**Files:**
- Create: `notes/openproposal_phase1_dataset_and_metrics.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: 下载并适配数据（本机路径，不入库）**

Run（本机直接可用；`cam00` 前 60 帧缺帧，故不选）：
```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
THUMAN_SUBJECT_DIR="$REPO_ROOT/data/raw/thuman4/subject00"
OUT_DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f"

# NOTE:
# - --camera_ids 必须与 "$THUMAN_SUBJECT_DIR/images/<camera_id>/" 的子目录名一致。
# - 本机 `subject00` 实际相机名是 `cam00..cam23`。
# - `cam00` 在 [0,60) 内缺帧（至少 20/44），因此这里用 cam01..cam08。

python3 scripts/adapt_thuman4_release_to_freetime.py \
  --input_dir "$THUMAN_SUBJECT_DIR" \
  --output_dir "$OUT_DATA_DIR" \
  --camera_ids "cam01,cam02,cam03,cam04,cam05,cam06,cam07,cam08" \
  --output_camera_ids "02,03,04,05,06,07,08,09" \
  --frame_start 0 \
  --num_frames 60 \
  --image_downscale 2 \
  --copy_mode copy \
  --overwrite
```

Expected:
- `data/thuman4_subject00_8cam60f/images/02/000000.jpg` 存在
- `data/thuman4_subject00_8cam60f/masks/02/000000.png` 存在（注意：raw 的 mask 是 jpg，但 adapter 输出为 png）

**Step 2: 跑 COLMAP + triangulation（按 Task 3/4 runbook）**

Expected:
- `data/thuman4_subject00_8cam60f/sparse/0/{cameras,images,points3D}.bin` 存在
- `data/thuman4_subject00_8cam60f/triangulation/points3d_frame000000.npy` 存在

**Step 3: 跑 planb_init smoke200（先快跑，确认闭环；如需再扩到 600）**

Run:
```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f" \
RESULT_DIR="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_smoke200" \
GPU=0 MAX_STEPS=200 EVAL_STEPS=199 SAVE_STEPS=199 VENV_PYTHON="$VENV_PYTHON" \
bash scripts/run_train_planb_init_selfcap.sh "$RESULT_DIR"
```

Expected:
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_smoke200/stats/test_step0199.json`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_smoke200/renders/test_step199_0000.png`

（可选）如需把 smoke 扩到 600（更接近后续 Phase 的对照尺度）：
```bash
DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f" \
RESULT_DIR="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600" \
GPU=0 MAX_STEPS=600 EVAL_STEPS=599 SAVE_STEPS=599 VENV_PYTHON="$VENV_PYTHON" \
bash scripts/run_train_planb_init_selfcap.sh "$RESULT_DIR"
```

**Step 4: 跑 fg-masked eval（dataset mask）**

Run:
```bash
python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_smoke200 \
  --stage test \
  --step 199 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend auto
```

Expected:
- `.../stats_masked/test_step0199.json` 存在，包含 `psnr_fg`/`lpips_fg`

（可选）若你的环境没有 torch+lpips，先用 dummy 跑通 contract：
```bash
python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_smoke200 \
  --stage test \
  --step 199 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend dummy
```

**Step 5: 写 1 页说明文档（Phase 1 总结）**

新增 `notes/openproposal_phase1_dataset_and_metrics.md`，至少包含：
- 数据来源与许可（local-eval only）
- mask 来源/类型（binary 或 alpha；本 repo 用阈值 0.5 转二值）
- 指标定义（尤其是 fg-masked：bbox+fill-black）
- 本 Phase 的 Gate 是否通过（能训练/能评测/能复现）

**Step 6: Commit（仅文档，不包含数据/输出）**

```bash
git add notes/openproposal_phase1_dataset_and_metrics.md
git commit -m "docs(notes): Phase1 THUman dataset+masked-metrics ready"
```
