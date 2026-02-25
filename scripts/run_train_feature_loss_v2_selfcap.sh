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
RESULT_TAG="${RESULT_TAG:-feature_loss_v2_600}"
RESULT_DIR="${1:-${RESULT_DIR:-$REPO_ROOT/outputs/protocol_v1/selfcap_bar_8cam60f/$RESULT_TAG}}"

START_FRAME="${START_FRAME:-0}"
END_FRAME="${END_FRAME:-60}"
KEYFRAME_STEP="${KEYFRAME_STEP:-5}"
GPU="${GPU:-1}"
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

# Feature-loss v2 defaults.
VGGT_FEAT_PHI_NAME="${VGGT_FEAT_PHI_NAME:-token_proj}"
LAMBDA_VGGT_FEAT="${LAMBDA_VGGT_FEAT:-0.05}"
VGGT_FEAT_LOSS_TYPE="${VGGT_FEAT_LOSS_TYPE:-cosine}"
VGGT_FEAT_START_STEP="${VGGT_FEAT_START_STEP:-0}"
VGGT_FEAT_RAMP_STEPS="${VGGT_FEAT_RAMP_STEPS:-200}"
VGGT_FEAT_EVERY="${VGGT_FEAT_EVERY:-8}"
VGGT_FEAT_PATCH_K="${VGGT_FEAT_PATCH_K:-0}"
VGGT_FEAT_PATCH_HW="${VGGT_FEAT_PATCH_HW:-32}"
VGGT_FEAT_USE_CONF="${VGGT_FEAT_USE_CONF:-1}"
VGGT_FEAT_GATING="${VGGT_FEAT_GATING:-none}"
VGGT_FEAT_GATING_TOP_P="${VGGT_FEAT_GATING_TOP_P:-0.10}"

# token-proj cache controls (persisted in cache/meta for audit).
TOKEN_LAYER_IDX="${TOKEN_LAYER_IDX:-23}"
TOKEN_PROJ_DIM="${TOKEN_PROJ_DIM:-32}"
TOKEN_PROJ_SEED="${TOKEN_PROJ_SEED:-20260225}"

# Cache generation (auto precompute once if missing).
TOTAL_FRAMES=$((END_FRAME - START_FRAME))
VGGT_CACHE_TAG="${VGGT_CACHE_TAG:-selfcap_bar_8cam60f_${VGGT_FEAT_PHI_NAME}_l${TOKEN_LAYER_IDX}_d${TOKEN_PROJ_DIM}_s${TOKEN_PROJ_SEED}_f${START_FRAME}_n${TOTAL_FRAMES}_cam8_ds4}"
VGGT_CACHE_OUT_DIR="${VGGT_CACHE_OUT_DIR:-$REPO_ROOT/outputs/vggt_cache/$VGGT_CACHE_TAG}"
VGGT_FEAT_CACHE_NPZ="${VGGT_FEAT_CACHE_NPZ:-$VGGT_CACHE_OUT_DIR/gt_cache.npz}"
VGGT_BACKEND="${VGGT_BACKEND:-vggt}"
VGGT_PHI_DOWNSCALE="${VGGT_PHI_DOWNSCALE:-4}"
VGGT_MODE="${VGGT_MODE:-crop}"
VGGT_CAMERA_IDS="${VGGT_CAMERA_IDS:-02,03,04,05,06,07,08,09}"
VGGT_MODEL_ID="${VGGT_MODEL_ID:-facebook/VGGT-1B}"
VGGT_MODEL_CACHE_DIR="${VGGT_MODEL_CACHE_DIR:-}"
HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"

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
if [ ! -d "$DATA_DIR/images" ]; then
  echo "[ERROR] missing images dir: $DATA_DIR/images"
  exit 1
fi

VGGT_FEAT_USE_CONF_RAW="$(echo "$VGGT_FEAT_USE_CONF" | tr '[:upper:]' '[:lower:]')"
case "$VGGT_FEAT_USE_CONF_RAW" in
  1|true|yes|on)
    VGGT_FEAT_USE_CONF_FLAG="--vggt-feat-use-conf"
    ;;
  0|false|no|off)
    VGGT_FEAT_USE_CONF_FLAG="--no-vggt-feat-use-conf"
    ;;
  *)
    echo "[ERROR] invalid VGGT_FEAT_USE_CONF=$VGGT_FEAT_USE_CONF (use 1/0/true/false)"
    exit 1
    ;;
esac

RESULT_DIR="$(realpath -m "$RESULT_DIR")"
mkdir -p "$RESULT_DIR"
mkdir -p "$VGGT_CACHE_OUT_DIR"

COMBINE_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py"
TRAINER_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"
CACHE_SCRIPT="$REPO_ROOT/scripts/precompute_vggt_cache.py"
NPZ_PATH="$RESULT_DIR/keyframes_${TOTAL_FRAMES}frames_step${KEYFRAME_STEP}.npz"

if [ ! -f "$VGGT_FEAT_CACHE_NPZ" ]; then
  echo "[FeatureLoss-v2] cache missing, precomputing VGGT cache first..."
  HF_HUB_OFFLINE="$HF_HUB_OFFLINE" HF_HUB_DISABLE_XET="$HF_HUB_DISABLE_XET" \
  "$VENV_PYTHON" "$CACHE_SCRIPT" \
    --data_dir "$DATA_DIR" \
    --out_dir "$VGGT_CACHE_OUT_DIR" \
    --camera_ids "$VGGT_CAMERA_IDS" \
    --frame_start "$START_FRAME" \
    --num_frames "$TOTAL_FRAMES" \
    --backend "$VGGT_BACKEND" \
    --phi_name "$VGGT_FEAT_PHI_NAME" \
    --phi_downscale "$VGGT_PHI_DOWNSCALE" \
    --token_layer_idx "$TOKEN_LAYER_IDX" \
    --token_proj_dim "$TOKEN_PROJ_DIM" \
    --token_proj_seed "$TOKEN_PROJ_SEED" \
    --framediff_top_p "$VGGT_FEAT_GATING_TOP_P" \
    --vggt_model_id "$VGGT_MODEL_ID" \
    --vggt_cache_dir "$VGGT_MODEL_CACHE_DIR" \
    --vggt_mode "$VGGT_MODE"
fi
if [ ! -f "$VGGT_FEAT_CACHE_NPZ" ]; then
  echo "[ERROR] VGGT cache missing after precompute: $VGGT_FEAT_CACHE_NPZ"
  exit 1
fi

echo "[FeatureLoss-v2] data_dir:       $DATA_DIR"
echo "[FeatureLoss-v2] result_dir:     $RESULT_DIR"
echo "[FeatureLoss-v2] feature_cache:  $VGGT_FEAT_CACHE_NPZ"
echo "[FeatureLoss-v2] frame range:    [$START_FRAME, $END_FRAME)"
echo "[FeatureLoss-v2] gpu/max:        $GPU / $MAX_STEPS"
echo "[FeatureLoss-v2] feat params:    phi=$VGGT_FEAT_PHI_NAME loss=$VGGT_FEAT_LOSS_TYPE lambda=$LAMBDA_VGGT_FEAT start=$VGGT_FEAT_START_STEP ramp=$VGGT_FEAT_RAMP_STEPS every=$VGGT_FEAT_EVERY patch_k=$VGGT_FEAT_PATCH_K patch_hw=$VGGT_FEAT_PATCH_HW conf=$VGGT_FEAT_USE_CONF_RAW gating=$VGGT_FEAT_GATING top_p=$VGGT_FEAT_GATING_TOP_P"
echo "[FeatureLoss-v2] token proj:     layer=$TOKEN_LAYER_IDX dim=$TOKEN_PROJ_DIM seed=$TOKEN_PROJ_SEED"

"$VENV_PYTHON" "$COMBINE_SCRIPT" \
  --input-dir "$DATA_DIR/triangulation" \
  --output-path "$NPZ_PATH" \
  --frame-start "$START_FRAME" \
  --frame-end "$((END_FRAME - 1))" \
  --keyframe-step "$KEYFRAME_STEP"

CUDA_VISIBLE_DEVICES="$GPU" VGGT_MODEL_ID="$VGGT_MODEL_ID" VGGT_CACHE_DIR="$VGGT_MODEL_CACHE_DIR" \
"$VENV_PYTHON" "$TRAINER_SCRIPT" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$NPZ_PATH" \
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
  --vggt-feat-cache-npz "$VGGT_FEAT_CACHE_NPZ" \
  --lambda-vggt-feat "$LAMBDA_VGGT_FEAT" \
  --vggt-feat-loss-type "$VGGT_FEAT_LOSS_TYPE" \
  --vggt-feat-start-step "$VGGT_FEAT_START_STEP" \
  --vggt-feat-ramp-steps "$VGGT_FEAT_RAMP_STEPS" \
  --vggt-feat-every "$VGGT_FEAT_EVERY" \
  --vggt-feat-phi-name "$VGGT_FEAT_PHI_NAME" \
  --vggt-feat-patch-k "$VGGT_FEAT_PATCH_K" \
  --vggt-feat-patch-hw "$VGGT_FEAT_PATCH_HW" \
  --vggt-feat-gating "$VGGT_FEAT_GATING" \
  --vggt-feat-gating-top-p "$VGGT_FEAT_GATING_TOP_P" \
  "$VGGT_FEAT_USE_CONF_FLAG" \
  $(if [ "$EVAL_ON_TEST" = "1" ]; then echo --eval-on-test; fi)

"$VENV_PYTHON" - "$RESULT_DIR" <<'PY'
import json
import re
import sys
from pathlib import Path

result_dir = Path(sys.argv[1]).resolve()
stats_dir = result_dir / "stats"
stats_files = sorted(stats_dir.glob("train_step*.json"))
if not stats_files:
    raise SystemExit(f"[ERROR] no train_step stats found under {stats_dir}")

best_path = None
best_step = -1
best_elapsed = 0.0
for path in stats_files:
    m = re.match(r"train_step(\d+)\.json$", path.name)
    if m is None:
        continue
    step = int(m.group(1))
    data = json.loads(path.read_text(encoding="utf-8"))
    elapsed = float(data.get("ellipse_time", 0.0) or 0.0)
    if elapsed <= 0:
        continue
    if step > best_step:
        best_path = path
        best_step = step
        best_elapsed = elapsed

if best_path is None:
    raise SystemExit(f"[ERROR] no valid stats with positive ellipse_time under {stats_dir}")

iter_per_sec = float(best_step + 1) / best_elapsed
throughput = {
    "source_stats": str(best_path.name),
    "step": best_step,
    "elapsed_sec": best_elapsed,
    "iter_per_sec": iter_per_sec,
}
out_path = stats_dir / "throughput.json"
out_path.write_text(json.dumps(throughput, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[FeatureLoss-v2] wrote {out_path}")
PY

echo "[FeatureLoss-v2] Done: $RESULT_DIR"
