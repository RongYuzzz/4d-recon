#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <source_hf_dir> [per_frame_sparse_dir] [adapted_dir] [result_dir] [gpu_id] [frame_start] [frame_end|-1:auto] [keyframe_step] [config]"
  exit 1
fi

SOURCE_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PER_FRAME_SPARSE_DIR="${2:-$SOURCE_DIR/sparse}"
ADAPTED_DIR="${3:-$REPO_ROOT/data/gate1_adapted}"
RESULT_DIR="${4:-$REPO_ROOT/outputs/gate1_smoke}"
GPU_ID="${5:-0}"
FRAME_START="${6:-0}"
FRAME_END="${7:--1}"
KEYFRAME_STEP="${8:-5}"
CONFIG="${9:-default_keyframe_small}"

BASE_DIR="${BASE_DIR:-$REPO_ROOT/third_party/FreeTimeGsVanilla}"
ADAPTER_PYTHON="${ADAPTER_PYTHON:-$BASE_DIR/.venv/bin/python}"
MAX_STEPS="${MAX_STEPS:-300}"
RENDER_TRAJ_PATH="${RENDER_TRAJ_PATH:-fixed}"
RENDER_TRAJ_TIME_FRAMES="${RENDER_TRAJ_TIME_FRAMES:-}"

SOURCE_DIR="$(realpath "$SOURCE_DIR")"
PER_FRAME_SPARSE_DIR="$(realpath "$PER_FRAME_SPARSE_DIR")"
ADAPTED_DIR="$(realpath -m "$ADAPTED_DIR")"
RESULT_DIR="$(realpath -m "$RESULT_DIR")"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "[ERROR] source_hf_dir does not exist: $SOURCE_DIR"
  exit 1
fi
if [ ! -d "$PER_FRAME_SPARSE_DIR" ]; then
  echo "[ERROR] per_frame_sparse_dir does not exist: $PER_FRAME_SPARSE_DIR"
  exit 1
fi
if [ ! -x "$ADAPTER_PYTHON" ]; then
  echo "[ERROR] adapter python not executable: $ADAPTER_PYTHON"
  exit 1
fi
if [ "$FRAME_START" -lt 0 ]; then
  echo "[ERROR] frame_start must be >= 0"
  exit 1
fi

if [ "$FRAME_END" = "-1" ]; then
  DETECTED_END="$("$ADAPTER_PYTHON" - "$PER_FRAME_SPARSE_DIR" "$FRAME_START" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
frame_start = int(sys.argv[2])
pat = re.compile(r"^frame_(\d+)$")
indices = []
for child in root.iterdir():
    if not child.is_dir():
        continue
    m = pat.match(child.name)
    if m:
        idx = int(m.group(1))
        if idx >= frame_start:
            indices.append(idx)
if not indices:
    print(-1)
else:
    print(max(indices) + 1)
PY
)"
  if [ "$DETECTED_END" -le "$FRAME_START" ]; then
    echo "[ERROR] cannot auto-detect frame_end from $PER_FRAME_SPARSE_DIR with frame_start=$FRAME_START"
    exit 1
  fi
  FRAME_END="$DETECTED_END"
  echo "[Gate-1] Auto-detected frame_end=$FRAME_END"
fi

if [ "$FRAME_END" -le "$FRAME_START" ]; then
  echo "[ERROR] invalid frame range: start=$FRAME_START end=$FRAME_END"
  exit 1
fi

REQUESTED_NUM_FRAMES=$((FRAME_END - FRAME_START))
if [ "$REQUESTED_NUM_FRAMES" -le 1 ]; then
  echo "[ERROR] selected frame count must be > 1 (got $REQUESTED_NUM_FRAMES)"
  exit 1
fi
if [ "$KEYFRAME_STEP" -le 0 ]; then
  echo "[ERROR] keyframe_step must be > 0"
  exit 1
fi

mkdir -p "$RESULT_DIR"

echo "[Gate-1] Step 1/2: adapting data + per-frame sparse triangulation"
"$ADAPTER_PYTHON" "$REPO_ROOT/scripts/adapt_hf_sample_to_freetime.py" \
  --source_dir "$SOURCE_DIR" \
  --output_dir "$ADAPTED_DIR" \
  --num_frames "$REQUESTED_NUM_FRAMES" \
  --copy_mode symlink \
  --triangulation_mode per_frame_sparse \
  --per_frame_sparse_dir "$PER_FRAME_SPARSE_DIR" \
  --triangulation_frame_start "$FRAME_START" \
  --triangulation_frame_end "$FRAME_END"

TRIANGULATION_DIR="$ADAPTED_DIR/triangulation"
FRAME_MANIFEST="$TRIANGULATION_DIR/frame_manifest.csv"
if [ -f "$FRAME_MANIFEST" ]; then
  TRAIN_NUM_FRAMES="$(awk 'NR>1 {n+=1} END {print n+0}' "$FRAME_MANIFEST")"
else
  TRAIN_NUM_FRAMES="$(find "$TRIANGULATION_DIR" -maxdepth 1 -name 'points3d_frame*.npy' | wc -l)"
fi

if [ "$TRAIN_NUM_FRAMES" -le 1 ]; then
  echo "[ERROR] exported triangulation frames must be > 1 (got $TRAIN_NUM_FRAMES)"
  exit 1
fi
if [ "$KEYFRAME_STEP" -ge "$TRAIN_NUM_FRAMES" ]; then
  echo "[ERROR] keyframe_step ($KEYFRAME_STEP) must be < exported triangulation frames ($TRAIN_NUM_FRAMES)"
  exit 1
fi

echo "[Gate-1] Step 2/2: running smoke pipeline"
cd "$BASE_DIR"
MAX_STEPS="$MAX_STEPS" \
EVAL_STEPS="$MAX_STEPS" \
SAVE_STEPS="$MAX_STEPS" \
RENDER_TRAJ_PATH="$RENDER_TRAJ_PATH" \
RENDER_TRAJ_TIME_FRAMES="$RENDER_TRAJ_TIME_FRAMES" \
bash run_pipeline.sh \
  "$ADAPTED_DIR/triangulation" \
  "$ADAPTED_DIR" \
  "$RESULT_DIR" \
  0 "$TRAIN_NUM_FRAMES" "$KEYFRAME_STEP" "$GPU_ID" "$CONFIG"

echo "[Gate-1] Done."
echo "  Adapted data: $ADAPTED_DIR"
echo "  Results:      $RESULT_DIR"
echo "  Source frame range: [$FRAME_START, $FRAME_END)"
echo "  Requested copied frames/camera: $REQUESTED_NUM_FRAMES"
echo "  Exported triangulation frames:  $TRAIN_NUM_FRAMES"
echo "  Remapped train range: [0, $TRAIN_NUM_FRAMES)"
