#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [result_dir]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
DATA_DIR="${DATA_DIR:-$REPO_ROOT/data/selfcap_bar_8cam60f}"
RESULT_DIR="${1:-${RESULT_DIR:-$REPO_ROOT/outputs/gate1_selfcap_bar_8cam60f_baseline}}"

START_FRAME="${START_FRAME:-0}"
END_FRAME="${END_FRAME:-60}"
KEYFRAME_STEP="${KEYFRAME_STEP:-5}"
GPU="${GPU:-0}"
MAX_STEPS="${MAX_STEPS:-600}"
EVAL_STEPS="${EVAL_STEPS:-}"
SAVE_STEPS="${SAVE_STEPS:-}"
CONFIG="${CONFIG:-default_keyframe_small}"
GLOBAL_SCALE="${GLOBAL_SCALE:-6}"
RENDER_TRAJ_PATH="${RENDER_TRAJ_PATH:-fixed}"
SEED="${SEED:-42}"
EXTRA_TRAIN_ARGS="${EXTRA_TRAIN_ARGS:-}"
EVAL_STEPS_PRINT="$MAX_STEPS"
SAVE_STEPS_PRINT="$MAX_STEPS"

# Split EXTRA_TRAIN_ARGS into an argv array, preserving shell-style spacing.
EXTRA_TRAIN_ARGS_ARR=()
if [ -n "$EXTRA_TRAIN_ARGS" ]; then
  # shellcheck disable=SC2206
  EXTRA_TRAIN_ARGS_ARR=($EXTRA_TRAIN_ARGS)
fi

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
NPZ_PATH="$RESULT_DIR/keyframes_${TOTAL_FRAMES}frames_step${KEYFRAME_STEP}.npz"

_csv_to_steps() {
  local csv="${1:-}"
  csv="${csv// /}"
  if [ -z "$csv" ]; then
    return 0
  fi
  IFS=',' read -ra _parts <<< "$csv"
  for _p in "${_parts[@]}"; do
    if [ -n "$_p" ]; then
      printf '%s\n' "$_p"
    fi
  done
}

EVAL_ARGS=(--eval-steps "$MAX_STEPS")
if [ -n "$EVAL_STEPS" ]; then
  mapfile -t _eval_steps < <(_csv_to_steps "$EVAL_STEPS")
  if [ "${#_eval_steps[@]}" -gt 0 ]; then
    EVAL_ARGS=(--eval-steps "${_eval_steps[@]}")
    EVAL_STEPS_PRINT="${_eval_steps[*]}"
  fi
fi

SAVE_ARGS=(--save-steps "$MAX_STEPS")
if [ -n "$SAVE_STEPS" ]; then
  mapfile -t _save_steps < <(_csv_to_steps "$SAVE_STEPS")
  if [ "${#_save_steps[@]}" -gt 0 ]; then
    SAVE_ARGS=(--save-steps "${_save_steps[@]}")
    SAVE_STEPS_PRINT="${_save_steps[*]}"
  fi
fi

EVAL_ON_TEST_ARGS=()
if [ "$EVAL_ON_TEST" = "1" ]; then
  EVAL_ON_TEST_ARGS=(--eval-on-test)
fi

echo "[Baseline] data_dir:    $DATA_DIR"
echo "[Baseline] result_dir:  $RESULT_DIR"
echo "[Baseline] frame range: [$START_FRAME, $END_FRAME)"
echo "[Baseline] gpu/max:     $GPU / $MAX_STEPS"
echo "[Baseline] eval/save:   $EVAL_STEPS_PRINT / $SAVE_STEPS_PRINT"
echo "[Baseline] extra args:  ${EXTRA_TRAIN_ARGS:-<none>}"

"$VENV_PYTHON" "$COMBINE_SCRIPT" \
  --input-dir "$DATA_DIR/triangulation" \
  --output-path "$NPZ_PATH" \
  --frame-start "$START_FRAME" \
  --frame-end "$((END_FRAME - 1))" \
  --keyframe-step "$KEYFRAME_STEP"

CUDA_VISIBLE_DEVICES="$GPU" "$VENV_PYTHON" "$TRAINER_SCRIPT" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$NPZ_PATH" \
  --result-dir "$RESULT_DIR" \
  --start-frame "$START_FRAME" \
  --end-frame "$END_FRAME" \
  --max-steps "$MAX_STEPS" \
  "${EVAL_ARGS[@]}" \
  "${SAVE_ARGS[@]}" \
  --seed "$SEED" \
  --train-camera-names "$TRAIN_CAMERA_NAMES" \
  --val-camera-names "$VAL_CAMERA_NAMES" \
  --test-camera-names "$TEST_CAMERA_NAMES" \
  --eval-sample-every "$EVAL_SAMPLE_EVERY" \
  --eval-sample-every-test "$EVAL_SAMPLE_EVERY_TEST" \
  --render-traj-path "$RENDER_TRAJ_PATH" \
  --global-scale "$GLOBAL_SCALE" \
  "${EVAL_ON_TEST_ARGS[@]}" \
  "${EXTRA_TRAIN_ARGS_ARR[@]}"

"$VENV_PYTHON" "$THROUGHPUT_SCRIPT" "$RESULT_DIR"

echo "[Baseline] Done: $RESULT_DIR"
