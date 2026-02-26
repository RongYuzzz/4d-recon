#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [result_dir]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PYTHON="${VENV_PYTHON:-/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python}"
DATA_DIR="${DATA_DIR:-$REPO_ROOT/data/selfcap_bar_8cam60f}"
RESULT_DIR="${1:-${RESULT_DIR:-$REPO_ROOT/outputs/protocol_v1/selfcap_bar_8cam60f/planb_init}}"

START_FRAME="${START_FRAME:-0}"
END_FRAME="${END_FRAME:-60}"
KEYFRAME_STEP="${KEYFRAME_STEP:-5}"
GPU="${GPU:-0}"
MAX_STEPS="${MAX_STEPS:-600}"
CONFIG="${CONFIG:-default_keyframe_small}"
GLOBAL_SCALE="${GLOBAL_SCALE:-6}"
RENDER_TRAJ_PATH="${RENDER_TRAJ_PATH:-fixed}"
SEED="${SEED:-42}"

# Frozen protocol defaults (camera split).
TRAIN_CAMERA_NAMES="${TRAIN_CAMERA_NAMES:-02,03,04,05,06,07}"
VAL_CAMERA_NAMES="${VAL_CAMERA_NAMES:-08}"
TEST_CAMERA_NAMES="${TEST_CAMERA_NAMES:-09}"
EVAL_ON_TEST="${EVAL_ON_TEST:-1}"
EVAL_SAMPLE_EVERY="${EVAL_SAMPLE_EVERY:-1}"
EVAL_SAMPLE_EVERY_TEST="${EVAL_SAMPLE_EVERY_TEST:-1}"

TOTAL_FRAMES=$((END_FRAME - START_FRAME))
if [ "$TOTAL_FRAMES" -le 1 ]; then
  echo "[ERROR] invalid frame range: start=$START_FRAME end=$END_FRAME"
  exit 1
fi
if [ "$KEYFRAME_STEP" -le 0 ] || [ "$KEYFRAME_STEP" -ge "$TOTAL_FRAMES" ]; then
  echo "[ERROR] keyframe_step must be in [1, total_frames-1], got $KEYFRAME_STEP"
  exit 1
fi
if [ ! -x "$VENV_PYTHON" ]; then
  echo "[ERROR] missing python: $VENV_PYTHON"
  exit 1
fi
VENV_BIN="$(dirname "$VENV_PYTHON")"
export PATH="$VENV_BIN:$PATH"
if [ ! -d "$DATA_DIR/triangulation" ]; then
  echo "[ERROR] missing triangulation dir: $DATA_DIR/triangulation"
  exit 1
fi

RESULT_DIR="$(realpath -m "$RESULT_DIR")"
mkdir -p "$RESULT_DIR"

COMBINE_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py"
TRAINER_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"
THROUGHPUT_SCRIPT="$REPO_ROOT/scripts/write_throughput_json.py"
PLANB_SCRIPT="$REPO_ROOT/scripts/init_velocity_from_points.py"

# Default: reuse the canonical baseline init if present; otherwise we will generate one.
BASELINE_INIT_NPZ="${BASELINE_INIT_NPZ:-$REPO_ROOT/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_${TOTAL_FRAMES}frames_step${KEYFRAME_STEP}.npz}"
PLANB_OUT_DIR="${PLANB_OUT_DIR:-$REPO_ROOT/outputs/plan_b/$(basename "$DATA_DIR")}"
PLANB_INIT_NPZ="${PLANB_INIT_NPZ:-$PLANB_OUT_DIR/init_points_planb_step${KEYFRAME_STEP}.npz}"

echo "[Plan-B Runner] data_dir:      $DATA_DIR"
echo "[Plan-B Runner] result_dir:    $RESULT_DIR"
echo "[Plan-B Runner] frame range:   [$START_FRAME, $END_FRAME)"
echo "[Plan-B Runner] gpu/max:       $GPU / $MAX_STEPS"
echo "[Plan-B Runner] baseline_init: $BASELINE_INIT_NPZ"
echo "[Plan-B Runner] planb_init:    $PLANB_INIT_NPZ"

if [ ! -f "$BASELINE_INIT_NPZ" ]; then
  echo "[Plan-B Runner] baseline init missing, generating via combine_frames_fast_keyframes..."
  mkdir -p "$PLANB_OUT_DIR/_baseline_init"
  BASELINE_INIT_NPZ="$PLANB_OUT_DIR/_baseline_init/keyframes_${TOTAL_FRAMES}frames_step${KEYFRAME_STEP}.npz"
  "$VENV_PYTHON" "$COMBINE_SCRIPT" \
    --input-dir "$DATA_DIR/triangulation" \
    --output-path "$BASELINE_INIT_NPZ" \
    --frame-start "$START_FRAME" \
    --frame-end "$((END_FRAME - 1))" \
    --keyframe-step "$KEYFRAME_STEP"
fi

if [ ! -f "$PLANB_INIT_NPZ" ]; then
  echo "[Plan-B Runner] planb init missing, generating via scripts/init_velocity_from_points.py..."
  mkdir -p "$PLANB_OUT_DIR"
  "$VENV_PYTHON" "$PLANB_SCRIPT" \
    --data_dir "$DATA_DIR" \
    --baseline_init_npz "$BASELINE_INIT_NPZ" \
    --frame_start "$START_FRAME" \
    --frame_end_exclusive "$END_FRAME" \
    --keyframe_step "$KEYFRAME_STEP" \
    --out_dir "$PLANB_OUT_DIR"
fi

if [ ! -f "$PLANB_INIT_NPZ" ]; then
  echo "[ERROR] planb init still missing: $PLANB_INIT_NPZ"
  exit 1
fi

CUDA_VISIBLE_DEVICES="$GPU" "$VENV_PYTHON" "$TRAINER_SCRIPT" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
  --result-dir "$RESULT_DIR" \
  --start-frame "$START_FRAME" \
  --end-frame "$END_FRAME" \
  --max-steps "$MAX_STEPS" \
  --eval-steps "$MAX_STEPS" \
  --save-steps "$MAX_STEPS" \
  --seed "$SEED" \
  --train-camera-names "$TRAIN_CAMERA_NAMES" \
  --val-camera-names "$VAL_CAMERA_NAMES" \
  --test-camera-names "$TEST_CAMERA_NAMES" \
  --eval-sample-every "$EVAL_SAMPLE_EVERY" \
  --eval-sample-every-test "$EVAL_SAMPLE_EVERY_TEST" \
  --render-traj-path "$RENDER_TRAJ_PATH" \
  --global-scale "$GLOBAL_SCALE" \
  $(if [ "$EVAL_ON_TEST" = "1" ]; then echo --eval-on-test; fi)

"$VENV_PYTHON" "$THROUGHPUT_SCRIPT" "$RESULT_DIR"

echo "[Plan-B Runner] Done: $RESULT_DIR"

