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
RESULT_DIR="${1:-${RESULT_DIR:-$REPO_ROOT/outputs/gate1_selfcap_bar_8cam60f_ours_weak}}"

START_FRAME="${START_FRAME:-0}"
END_FRAME="${END_FRAME:-60}"
KEYFRAME_STEP="${KEYFRAME_STEP:-5}"
GPU="${GPU:-0}"
MAX_STEPS="${MAX_STEPS:-200}"
CONFIG="${CONFIG:-default_keyframe_small}"
GLOBAL_SCALE="${GLOBAL_SCALE:-6}"
RENDER_TRAJ_PATH="${RENDER_TRAJ_PATH:-fixed}"

CUE_TAG="${CUE_TAG:-selfcap_bar_8cam60f_diff_mvp}"
CUE_BACKEND="${CUE_BACKEND:-diff}"
MASK_DOWNSCALE="${MASK_DOWNSCALE:-4}"
CUE_OUT_DIR="${CUE_OUT_DIR:-$REPO_ROOT/outputs/cue_mining/$CUE_TAG}"
PSEUDO_MASK_NPZ="${PSEUDO_MASK_NPZ:-$CUE_OUT_DIR/pseudo_masks.npz}"
PSEUDO_MASK_WEIGHT="${PSEUDO_MASK_WEIGHT:-1.0}"
PSEUDO_MASK_END_STEP="${PSEUDO_MASK_END_STEP:-200}"

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

if [ ! -f "$PSEUDO_MASK_NPZ" ]; then
  echo "[Ours-Weak] pseudo mask missing, running cue mining first..."
  CUE_PYTHON="$VENV_PYTHON" \
  OUT_DIR="$CUE_OUT_DIR" \
  bash "$REPO_ROOT/scripts/run_cue_mining.sh" \
    "$DATA_DIR" "$CUE_TAG" "$START_FRAME" "$TOTAL_FRAMES" "$CUE_BACKEND" "$MASK_DOWNSCALE"
fi
if [ ! -f "$PSEUDO_MASK_NPZ" ]; then
  echo "[ERROR] pseudo mask still missing after cue mining: $PSEUDO_MASK_NPZ"
  exit 1
fi

COMBINE_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py"
TRAINER_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"
NPZ_PATH="$RESULT_DIR/keyframes_${TOTAL_FRAMES}frames_step${KEYFRAME_STEP}.npz"

echo "[Ours-Weak] data_dir:      $DATA_DIR"
echo "[Ours-Weak] result_dir:    $RESULT_DIR"
echo "[Ours-Weak] pseudo_mask:   $PSEUDO_MASK_NPZ"
echo "[Ours-Weak] frame range:   [$START_FRAME, $END_FRAME)"
echo "[Ours-Weak] gpu/max:       $GPU / $MAX_STEPS"
echo "[Ours-Weak] weak params:   weight=$PSEUDO_MASK_WEIGHT end_step=$PSEUDO_MASK_END_STEP"

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
  --eval-steps "$MAX_STEPS" \
  --save-steps "$MAX_STEPS" \
  --render-traj-path "$RENDER_TRAJ_PATH" \
  --global-scale "$GLOBAL_SCALE" \
  --pseudo-mask-npz "$PSEUDO_MASK_NPZ" \
  --pseudo-mask-weight "$PSEUDO_MASK_WEIGHT" \
  --pseudo-mask-end-step "$PSEUDO_MASK_END_STEP"

echo "[Ours-Weak] Done: $RESULT_DIR"
