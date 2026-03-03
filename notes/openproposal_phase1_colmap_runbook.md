# OpenProposal Phase 1 — THUman4 COLMAP + Triangulation Runbook

> local-eval only: do not commit dataset frames/masks, and do not place GT images/masks in report-pack evidence.

## COLMAP reference sparse model (1 frame per camera)

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

## Triangulation export

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

Fallback (smoke only):

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

## Stop-loss rules

- mapper 失败时优先换参考帧（如 `000000.jpg` → 纹理更强帧）或先减到 4 cams 跑通，不做无底洞调参。
- 优先坚持 `PINHOLE`，避免引入畸变 + undistort/crop 导致 mask 与 render/GT 对齐风险。
