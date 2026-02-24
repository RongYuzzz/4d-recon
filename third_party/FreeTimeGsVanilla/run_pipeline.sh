#!/bin/bash
# Complete pipeline: combine keyframes → train 4D Gaussians
#
# Usage:
#   bash run_pipeline.sh <input_dir> <data_dir> <result_dir> <start_frame> <end_frame> <keyframe_step> <gpu_id> [config]
#
# Example:
#   bash run_pipeline.sh \
#       /path/to/triangulation/output \
#       /path/to/undistorted \
#       /path/to/results \
#       0 61 5 1 default_keyframe_small

set -e  # Exit on error

# Parse arguments
INPUT_DIR=$1          # Directory with points3d_frameXXXXXX.npy and colors_frameXXXXXX.npy
DATA_DIR=$2           # Directory with images and COLMAP sparse reconstruction
RESULT_DIR=$3         # Output directory for training results
START_FRAME=$4        # Start frame (e.g., 0)
END_FRAME=$5          # End frame (e.g., 61)
KEYFRAME_STEP=$6      # Keyframe step (e.g., 5)
GPU_ID=$7             # GPU to use (e.g., 1)
CONFIG=${8:-default_keyframe_small}  # Config name (default: default_keyframe_small)

# Optional T0 debugging controls (env overrides)
FORCE_ZERO_VELOCITY_FOR_T0=${FORCE_ZERO_VELOCITY_FOR_T0:-0}
T0_DEBUG_INTERVAL=${T0_DEBUG_INTERVAL:-0}
T0_GRAD_LOG_PATH=${T0_GRAD_LOG_PATH:-}
MAX_STEPS=${MAX_STEPS:-30000}
EVAL_STEPS=${EVAL_STEPS:-$MAX_STEPS}
SAVE_STEPS=${SAVE_STEPS:-$MAX_STEPS}
RENDER_TRAJ_PATH=${RENDER_TRAJ_PATH:-}
RENDER_TRAJ_TIME_FRAMES=${RENDER_TRAJ_TIME_FRAMES:-}
EXTRA_TRAIN_ARGS=${EXTRA_TRAIN_ARGS:-}

# Validate arguments
if [ -z "$INPUT_DIR" ] || [ -z "$DATA_DIR" ] || [ -z "$RESULT_DIR" ] || [ -z "$START_FRAME" ] || [ -z "$END_FRAME" ] || [ -z "$KEYFRAME_STEP" ] || [ -z "$GPU_ID" ]; then
    echo "Usage: bash run_pipeline.sh <input_dir> <data_dir> <result_dir> <start_frame> <end_frame> <keyframe_step> <gpu_id> [config]"
    echo ""
    echo "Arguments:"
    echo "  input_dir     - Directory with per-frame NPY files (points3d_frameXXXXXX.npy, colors_frameXXXXXX.npy)"
    echo "  data_dir      - Directory with images and COLMAP sparse reconstruction"
    echo "  result_dir    - Output directory for training results"
    echo "  start_frame   - Start frame index (e.g., 0)"
    echo "  end_frame     - End frame index (e.g., 61)"
    echo "  keyframe_step - Step between keyframes (e.g., 5)"
    echo "  gpu_id        - GPU ID to use (e.g., 1)"
    echo "  config        - (optional) Config name: default_keyframe (15M) or default_keyframe_small (4M). Default: default_keyframe_small"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Compute total frames
TOTAL_FRAMES=$((END_FRAME - START_FRAME))

# NPZ output path
NPZ_PATH="${RESULT_DIR}/keyframes_${TOTAL_FRAMES}frames_step${KEYFRAME_STEP}.npz"

echo "========================================"
echo "FreeTimeGS Pipeline"
echo "========================================"
echo "Input dir:      $INPUT_DIR"
echo "Data dir:       $DATA_DIR"
echo "Result dir:     $RESULT_DIR"
echo "Frame range:    $START_FRAME - $END_FRAME ($TOTAL_FRAMES frames)"
echo "Keyframe step:  $KEYFRAME_STEP"
echo "GPU:            $GPU_ID"
echo "Config:         $CONFIG"
echo "NPZ output:     $NPZ_PATH"
echo "Max steps:      $MAX_STEPS"
echo "Eval steps:     $EVAL_STEPS"
echo "Save steps:     $SAVE_STEPS"
echo "T0 zero-v:      $FORCE_ZERO_VELOCITY_FOR_T0"
echo "T0 debug intv:  $T0_DEBUG_INTERVAL"
echo "T0 grad log:    ${T0_GRAD_LOG_PATH:-<disabled>}"
echo "Render traj:    ${RENDER_TRAJ_PATH:-<default>}"
echo "Render t-frames:${RENDER_TRAJ_TIME_FRAMES:-<default>}"
echo "Extra args:     ${EXTRA_TRAIN_ARGS:-<none>}"
echo "========================================"

# Create result directory
mkdir -p "$RESULT_DIR"

# Step 1: Combine keyframes with velocity
echo ""
echo "Step 1: Combining keyframes with velocity..."
echo "========================================"

python src/combine_frames_fast_keyframes.py \
    --input-dir "$INPUT_DIR" \
    --output-path "$NPZ_PATH" \
    --frame-start "$START_FRAME" \
    --frame-end "$((END_FRAME - 1))" \
    --keyframe-step "$KEYFRAME_STEP"

echo ""
echo "Step 2: Training 4D Gaussians..."
echo "========================================"

EXTRA_ARGS=()
EXTRA_TRAIN_ARGS_ARR=()
if [ "$FORCE_ZERO_VELOCITY_FOR_T0" = "1" ]; then
    EXTRA_ARGS+=(--force-zero-velocity-for-t0)
fi
if [ "$T0_DEBUG_INTERVAL" -gt 0 ] 2>/dev/null; then
    EXTRA_ARGS+=(--t0-debug-interval "$T0_DEBUG_INTERVAL")
fi
if [ -n "$T0_GRAD_LOG_PATH" ]; then
    EXTRA_ARGS+=(--t0-grad-log-path "$T0_GRAD_LOG_PATH")
fi
if [ -n "$RENDER_TRAJ_PATH" ]; then
    EXTRA_ARGS+=(--render-traj-path "$RENDER_TRAJ_PATH")
fi
if [ -n "$RENDER_TRAJ_TIME_FRAMES" ]; then
    EXTRA_ARGS+=(--render-traj-time-frames "$RENDER_TRAJ_TIME_FRAMES")
fi
if [ -n "$EXTRA_TRAIN_ARGS" ]; then
    read -r -a EXTRA_TRAIN_ARGS_ARR <<< "$EXTRA_TRAIN_ARGS"
fi

# Step 2: Train
CUDA_VISIBLE_DEVICES=$GPU_ID python src/simple_trainer_freetime_4d_pure_relocation.py $CONFIG \
    --data-dir "$DATA_DIR" \
    --init-npz-path "$NPZ_PATH" \
    --result-dir "$RESULT_DIR" \
    --start-frame "$START_FRAME" \
    --end-frame "$END_FRAME" \
    --max-steps "$MAX_STEPS" \
    --eval-steps "$EVAL_STEPS" \
    --save-steps "$SAVE_STEPS" \
    "${EXTRA_ARGS[@]}" \
    "${EXTRA_TRAIN_ARGS_ARR[@]}"

echo ""
echo "========================================"
echo "Pipeline complete!"
echo "Results saved to: $RESULT_DIR"
echo "========================================"
