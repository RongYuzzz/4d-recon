#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <triangulation_input_dir> <colmap_data_dir> [out_dir] [start_frame] [end_frame|-1:auto] [keyframe_step] [gpu_id] [config]"
  exit 1
fi

TRI_INPUT="$1"
COLMAP_DATA="$2"
OUT_DIR="${3:-/root/projects/4d-recon/outputs/t0_zero_velocity}"
START_FRAME="${4:-0}"
END_FRAME="${5:--1}"
KEYFRAME_STEP="${6:-5}"
GPU_ID="${7:-0}"
CONFIG="${8:-default_keyframe_small}"

BASE_DIR="/root/projects/4d-recon/third_party/FreeTimeGsVanilla"
mkdir -p "$OUT_DIR/baseline" "$OUT_DIR/zero_velocity"

# Auto-detect end_frame from triangulation files if END_FRAME == -1
if [ "$END_FRAME" = "-1" ]; then
  LAST_FILE="$(ls "$TRI_INPUT"/points3d_frame*.npy 2>/dev/null | sort | tail -n 1 || true)"
  if [ -z "$LAST_FILE" ]; then
    echo "[ERROR] Cannot auto-detect end_frame: no points3d_frame*.npy in $TRI_INPUT"
    exit 1
  fi
  LAST_BASENAME="$(basename "$LAST_FILE")"
  LAST_IDX="$(echo "$LAST_BASENAME" | sed -E 's/points3d_frame([0-9]{6})\.npy/\1/')"
  END_FRAME="$((10#$LAST_IDX + 1))"
  echo "[T0] Auto-detected end_frame=$END_FRAME from $LAST_BASENAME"
fi

if [ "$END_FRAME" -le "$START_FRAME" ]; then
  echo "[ERROR] Invalid frame range: start_frame=$START_FRAME, end_frame=$END_FRAME"
  exit 1
fi

cd "$BASE_DIR"

echo "[T0] Run baseline..."
FORCE_ZERO_VELOCITY_FOR_T0=0 \
T0_DEBUG_INTERVAL=200 \
T0_GRAD_LOG_PATH="$OUT_DIR/baseline/t0_grad.csv" \
bash run_pipeline.sh \
  "$TRI_INPUT" "$COLMAP_DATA" "$OUT_DIR/baseline" \
  "$START_FRAME" "$END_FRAME" "$KEYFRAME_STEP" "$GPU_ID" "$CONFIG"

echo "[T0] Run zero-velocity..."
FORCE_ZERO_VELOCITY_FOR_T0=1 \
T0_DEBUG_INTERVAL=200 \
T0_GRAD_LOG_PATH="$OUT_DIR/zero_velocity/t0_grad.csv" \
bash run_pipeline.sh \
  "$TRI_INPUT" "$COLMAP_DATA" "$OUT_DIR/zero_velocity" \
  "$START_FRAME" "$END_FRAME" "$KEYFRAME_STEP" "$GPU_ID" "$CONFIG"

echo "[T0] Done. Compare outputs under: $OUT_DIR"
