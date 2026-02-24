#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <source_hf_dir> [adapted_dir] [result_dir] [gpu_id] [num_frames] [keyframe_step] [config]"
  exit 1
fi

SOURCE_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ADAPTED_DIR="${2:-$REPO_ROOT/data/gate0_adapted}"
RESULT_DIR="${3:-$REPO_ROOT/outputs/gate0_smoke}"
GPU_ID="${4:-0}"
NUM_FRAMES="${5:-24}"
KEYFRAME_STEP="${6:-5}"
CONFIG="${7:-default_keyframe_small}"

BASE_DIR="${BASE_DIR:-$REPO_ROOT/third_party/FreeTimeGsVanilla}"
ADAPTER_PYTHON="${ADAPTER_PYTHON:-$BASE_DIR/.venv/bin/python}"
MAX_STEPS="${MAX_STEPS:-300}"
RENDER_TRAJ_PATH="${RENDER_TRAJ_PATH:-fixed}"

SOURCE_DIR="$(realpath "$SOURCE_DIR")"
ADAPTED_DIR="$(realpath -m "$ADAPTED_DIR")"
RESULT_DIR="$(realpath -m "$RESULT_DIR")"

if [ "$NUM_FRAMES" -le 1 ]; then
  echo "[ERROR] num_frames must be > 1"
  exit 1
fi
if [ "$KEYFRAME_STEP" -le 0 ]; then
  echo "[ERROR] keyframe_step must be > 0"
  exit 1
fi
if [ "$KEYFRAME_STEP" -ge "$NUM_FRAMES" ]; then
  echo "[ERROR] keyframe_step ($KEYFRAME_STEP) must be < num_frames ($NUM_FRAMES)"
  exit 1
fi
if [ ! -x "$ADAPTER_PYTHON" ]; then
  echo "[ERROR] adapter python not executable: $ADAPTER_PYTHON"
  exit 1
fi

mkdir -p "$RESULT_DIR"

echo "[Gate-0] Step 1/2: adapting data + static triangulation"
"$ADAPTER_PYTHON" "$REPO_ROOT/scripts/adapt_hf_sample_to_freetime.py" \
  --source_dir "$SOURCE_DIR" \
  --output_dir "$ADAPTED_DIR" \
  --num_frames "$NUM_FRAMES" \
  --copy_mode symlink \
  --triangulation_mode static_repeat \
  --triangulation_num_frames "$NUM_FRAMES"

echo "[Gate-0] Step 2/2: running smoke pipeline"
cd "$BASE_DIR"
MAX_STEPS="$MAX_STEPS" \
EVAL_STEPS="$MAX_STEPS" \
SAVE_STEPS="$MAX_STEPS" \
RENDER_TRAJ_PATH="$RENDER_TRAJ_PATH" \
bash run_pipeline.sh \
  "$ADAPTED_DIR/triangulation" \
  "$ADAPTED_DIR" \
  "$RESULT_DIR" \
  0 "$NUM_FRAMES" "$KEYFRAME_STEP" "$GPU_ID" "$CONFIG"

echo "[Gate-0] Done."
echo "  Adapted data: $ADAPTED_DIR"
echo "  Results:      $RESULT_DIR"
