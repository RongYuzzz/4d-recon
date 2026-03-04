# OpenProposal Phase 1 THUman4 Runbook（commands only）

> local-eval only：仅在本机执行；禁止提交 `data/`、`outputs/`，禁止将 GT 帧/GT mask 打包进 report-pack。

## 0) 变量约定（先改成你的本机路径）

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
THUMAN_SUBJECT_DIR="<ABS_PATH_TO_THUMAN_SUBJECT>"   # 需包含 images/ 与 masks/
DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f"
RESULT_ROOT="$REPO_ROOT/outputs/protocol_v3_openproposal/_waiting_thuman/thuman4_subject00_8cam60f"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
```

## 1) 盘点 raw 数据并自动生成 adapter 命令

```bash
python3 scripts/thuman4_inventory.py \
  --input_dir "$THUMAN_SUBJECT_DIR" \
  --num_cams 8 \
  --num_frames 60 \
  --frame_start 0 \
  --image_downscale 2 \
  --output_dir "$DATA_DIR"
```

NOTE:
- 请检查输出 JSON 的 `picked_cameras`，并避免使用 `cam00`（在本机 THUman4.0 的前 60 帧里存在缺帧）。
- 推荐固定使用 `cam01..cam08` → `02..09`（见下方 adapter 命令）。

## 2) 运行 adapter 生成 FreeTime 数据布局（images/ + masks/）

```bash
python3 scripts/adapt_thuman4_release_to_freetime.py \
  --input_dir "$THUMAN_SUBJECT_DIR" \
  --output_dir "$DATA_DIR" \
  --camera_ids "cam01,cam02,cam03,cam04,cam05,cam06,cam07,cam08" \
  --output_camera_ids "02,03,04,05,06,07,08,09" \
  --frame_start 0 \
  --num_frames 60 \
  --image_downscale 2 \
  --overwrite
```

## 3) COLMAP（只对每相机 1 帧参考图建 sparse/0）

```bash
REF_IMG_DIR="$DATA_DIR/_colmap_ref_images"
REF_DB="$DATA_DIR/colmap_ref.db"
rm -rf "$REF_IMG_DIR" "$REF_DB" "$DATA_DIR/sparse"
mkdir -p "$REF_IMG_DIR"

for cam in 02 03 04 05 06 07 08 09; do
  mkdir -p "$REF_IMG_DIR/$cam"
  ln -sf "$(realpath "$DATA_DIR/images/$cam/000000.jpg")" "$REF_IMG_DIR/$cam/000000.jpg"
done

colmap feature_extractor \
  --database_path "$REF_DB" \
  --image_path "$REF_IMG_DIR" \
  --ImageReader.camera_model PINHOLE \
  --ImageReader.single_camera 0 \
  --SiftExtraction.use_gpu 0

colmap exhaustive_matcher \
  --database_path "$REF_DB" \
  --SiftMatching.use_gpu 0

colmap mapper \
  --database_path "$REF_DB" \
  --image_path "$REF_IMG_DIR" \
  --output_path "$DATA_DIR/sparse"
```

## 4) 从 sparse/0 导出 triangulation/

```bash
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
```

## 5) smoke200（占位命令，结果目录固定到 protocol_v3_openproposal）

```bash
RESULT_DIR="$RESULT_ROOT/planb_init_smoke200"
DATA_DIR="$DATA_DIR" MAX_STEPS=200 GPU=0 VENV_PYTHON="$VENV_PYTHON" \
  bash scripts/run_train_planb_init_selfcap.sh "$RESULT_DIR"
```

## 6) 前景掩膜指标（`psnr_fg` / `lpips_fg`）

```bash
EVAL_PY="python3"
LPIPS_BACKEND="dummy"
if "$VENV_PYTHON" -c "import lpips" >/dev/null 2>&1; then
  EVAL_PY="$VENV_PYTHON"
  LPIPS_BACKEND="auto"
fi

OMP_NUM_THREADS=1 "$EVAL_PY" scripts/eval_masked_metrics.py \
  --data_dir "$DATA_DIR" \
  --result_dir "$RESULT_DIR" \
  --stage test \
  --step 199 \
  --mask_source dataset \
  --lpips_backend "$LPIPS_BACKEND"
```

## 7) 合规提醒（必须遵守）

- `data/`、`outputs/` 一律视为本地评估目录，禁止提交。
- report-pack 仅允许统计值、脚本和路径引用；禁止包含 GT 帧/GT mask 原始内容。
