#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 6 ]; then
  echo "Usage: $0 [data_dir] [tag] [frame_start] [num_frames] [backend] [mask_downscale]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DATA_DIR="${1:-$REPO_ROOT/data/selfcap_bar_8cam60f}"
TAG="${2:-selfcap_bar_8cam60f_diff}"
FRAME_START="${3:-0}"
NUM_FRAMES="${4:-60}"
BACKEND="${5:-diff}"
MASK_DOWNSCALE="${6:-4}"
THRESHOLD_QUANTILE="${THRESHOLD_QUANTILE:-0.9}"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/outputs/cue_mining/$TAG}"

BASE_DIR="${BASE_DIR:-$REPO_ROOT/third_party/FreeTimeGsVanilla}"
CUE_PYTHON="${CUE_PYTHON:-$BASE_DIR/.venv/bin/python}"

DATA_DIR="$(realpath "$DATA_DIR")"
OUT_DIR="$(realpath -m "$OUT_DIR")"

if [ ! -x "$CUE_PYTHON" ]; then
  echo "[ERROR] cue python not executable: $CUE_PYTHON"
  exit 1
fi
if [ ! -d "$DATA_DIR/images" ]; then
  echo "[ERROR] missing dataset images dir: $DATA_DIR/images"
  exit 1
fi

echo "[CueMining] data_dir: $DATA_DIR"
echo "[CueMining] out_dir:  $OUT_DIR"
echo "[CueMining] backend:  $BACKEND"
echo "[CueMining] frames:   start=$FRAME_START num=$NUM_FRAMES"
echo "[CueMining] downscale:$MASK_DOWNSCALE"

"$CUE_PYTHON" "$REPO_ROOT/scripts/cue_mining.py" \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIR" \
  --frame_start "$FRAME_START" \
  --num_frames "$NUM_FRAMES" \
  --mask_downscale "$MASK_DOWNSCALE" \
  --backend "$BACKEND" \
  --threshold_quantile "$THRESHOLD_QUANTILE" \
  --overwrite

echo "[CueMining] Done."
