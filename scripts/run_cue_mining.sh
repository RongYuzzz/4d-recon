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
VGGT_MODEL_ID="${VGGT_MODEL_ID:-facebook/VGGT-1B}"
VGGT_CACHE_DIR="${VGGT_CACHE_DIR:-}"
VGGT_MODE="${VGGT_MODE:-crop}"
GPU="${GPU:-0}"
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
echo "[CueMining] gpu:      $GPU"

CUDA_VISIBLE_DEVICES="$GPU" "$CUE_PYTHON" "$REPO_ROOT/scripts/cue_mining.py" \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIR" \
  --frame_start "$FRAME_START" \
  --num_frames "$NUM_FRAMES" \
  --mask_downscale "$MASK_DOWNSCALE" \
  --backend "$BACKEND" \
  --threshold_quantile "$THRESHOLD_QUANTILE" \
  --vggt_model_id "$VGGT_MODEL_ID" \
  --vggt_cache_dir "$VGGT_CACHE_DIR" \
  --vggt_mode "$VGGT_MODE" \
  --overwrite

QUALITY_JSON="$OUT_DIR/quality.json"
if [ -f "$QUALITY_JSON" ]; then
  QUALITY_LINE="$("$CUE_PYTHON" - "$QUALITY_JSON" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
q = json.loads(p.read_text(encoding="utf-8"))

mt = q.get("mask_mean_per_t") or []
mv = q.get("mask_mean_per_view") or []
mean_t = float(sum(mt) / len(mt)) if mt else 0.0
mean_v = float(sum(mv) / len(mv)) if mv else 0.0

print(
    "[CueMining][Quality] "
    f"mean_t_avg={mean_t:.6f} mean_v_avg={mean_v:.6f} "
    f"min={float(q.get('mask_min', 0.0)):.6f} "
    f"max={float(q.get('mask_max', 0.0)):.6f} "
    f"flicker_l1={float(q.get('temporal_flicker_l1_mean', 0.0)):.6f} "
    f"all_black={bool(q.get('all_black', False))} "
    f"all_white={bool(q.get('all_white', False))}"
)
PY
)"
  echo "$QUALITY_LINE"
else
  echo "[CueMining][WARN] quality.json not found: $QUALITY_JSON"
fi

echo "[CueMining] Done."
