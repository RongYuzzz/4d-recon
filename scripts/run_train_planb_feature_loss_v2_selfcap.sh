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
RESULT_TAG="${RESULT_TAG:-planb_feature_loss_v2_600}"
RESULT_DIR="${1:-${RESULT_DIR:-$REPO_ROOT/outputs/protocol_v2/selfcap_bar_8cam60f/$RESULT_TAG}}"

START_FRAME="${START_FRAME:-0}"
END_FRAME="${END_FRAME:-60}"
KEYFRAME_STEP="${KEYFRAME_STEP:-5}"
GPU="${GPU:-1}"
MAX_STEPS="${MAX_STEPS:-600}"
CONFIG="${CONFIG:-default_keyframe_small}"
GLOBAL_SCALE="${GLOBAL_SCALE:-6}"
RENDER_TRAJ_PATH="${RENDER_TRAJ_PATH:-fixed}"
SEED="${SEED:-42}"
EXTRA_TRAIN_ARGS="${EXTRA_TRAIN_ARGS:-}"
EVAL_STEPS="${EVAL_STEPS:-}"
SAVE_STEPS="${SAVE_STEPS:-}"
CKPT_PATH="${CKPT_PATH:-}"

# Frozen protocol defaults (camera split).
TRAIN_CAMERA_NAMES="${TRAIN_CAMERA_NAMES:-02,03,04,05,06,07}"
VAL_CAMERA_NAMES="${VAL_CAMERA_NAMES:-08}"
TEST_CAMERA_NAMES="${TEST_CAMERA_NAMES:-09}"
EVAL_ON_TEST="${EVAL_ON_TEST:-1}"
EVAL_SAMPLE_EVERY="${EVAL_SAMPLE_EVERY:-1}"
EVAL_SAMPLE_EVERY_TEST="${EVAL_SAMPLE_EVERY_TEST:-1}"

# Plan-B init generation defaults.
BASELINE_INIT_NPZ="${BASELINE_INIT_NPZ:-}"
PLANB_OUT_DIR="${PLANB_OUT_DIR:-$REPO_ROOT/outputs/plan_b/$(basename "$DATA_DIR")}"
PLANB_INIT_NPZ="${PLANB_INIT_NPZ:-$PLANB_OUT_DIR/init_points_planb_step${KEYFRAME_STEP}.npz}"
PLANB_MAX_MATCH_DISTANCE="${PLANB_MAX_MATCH_DISTANCE:-0.5}"
PLANB_CLIP_QUANTILE="${PLANB_CLIP_QUANTILE:-0.99}"

# VGGT feature-loss v2 defaults (conservative).
VGGT_FEAT_PHI_NAME="${VGGT_FEAT_PHI_NAME:-token_proj}"
LAMBDA_VGGT_FEAT="${LAMBDA_VGGT_FEAT:-0.01}"
VGGT_FEAT_LOSS_TYPE="${VGGT_FEAT_LOSS_TYPE:-cosine}"
VGGT_FEAT_START_STEP="${VGGT_FEAT_START_STEP:-0}"
VGGT_FEAT_RAMP_STEPS="${VGGT_FEAT_RAMP_STEPS:-400}"
VGGT_FEAT_EVERY="${VGGT_FEAT_EVERY:-8}"
VGGT_FEAT_PATCH_K="${VGGT_FEAT_PATCH_K:-0}"
VGGT_FEAT_PATCH_HW="${VGGT_FEAT_PATCH_HW:-32}"
VGGT_FEAT_USE_CONF="${VGGT_FEAT_USE_CONF:-1}"
VGGT_FEAT_GATING="${VGGT_FEAT_GATING:-none}"
VGGT_FEAT_GATING_TOP_P="${VGGT_FEAT_GATING_TOP_P:-0.10}"

# token-proj cache controls (persisted in cache/meta for audit).
TOKEN_LAYER_IDX="${TOKEN_LAYER_IDX:-17}"
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
  fi
fi

SAVE_ARGS=(--save-steps "$MAX_STEPS")
if [ -n "$SAVE_STEPS" ]; then
  mapfile -t _save_steps < <(_csv_to_steps "$SAVE_STEPS")
  if [ "${#_save_steps[@]}" -gt 0 ]; then
    SAVE_ARGS=(--save-steps "${_save_steps[@]}")
  fi
fi

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

FEATURE_NEVER_RUNS="$("$VENV_PYTHON" - "$LAMBDA_VGGT_FEAT" "$VGGT_FEAT_START_STEP" "$MAX_STEPS" <<'PY'
import sys
try:
    lam = float(sys.argv[1])
    start = int(float(sys.argv[2]))
    max_steps = int(float(sys.argv[3]))
except Exception:
    print("parse_error")
    raise SystemExit(0)
print("1" if lam > 0.0 and start >= max_steps else "0")
PY
)"
if [ "$FEATURE_NEVER_RUNS" = "parse_error" ]; then
  echo "[ERROR] failed to parse feature-loss schedule: LAMBDA_VGGT_FEAT=$LAMBDA_VGGT_FEAT VGGT_FEAT_START_STEP=$VGGT_FEAT_START_STEP MAX_STEPS=$MAX_STEPS"
  exit 1
fi
if [ "$FEATURE_NEVER_RUNS" = "1" ]; then
  echo "[ERROR] invalid feature-loss schedule: LAMBDA_VGGT_FEAT=$LAMBDA_VGGT_FEAT but VGGT_FEAT_START_STEP=$VGGT_FEAT_START_STEP >= MAX_STEPS=$MAX_STEPS; feature loss will never run (please lower start_step or increase max_steps)."
  exit 1
fi

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
mkdir -p "$PLANB_OUT_DIR"

COMBINE_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py"
TRAINER_SCRIPT="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"
CACHE_SCRIPT="$REPO_ROOT/scripts/precompute_vggt_cache.py"
THROUGHPUT_SCRIPT="$REPO_ROOT/scripts/write_throughput_json.py"
PLANB_SCRIPT="$REPO_ROOT/scripts/init_velocity_from_points.py"

CANONICAL_DATA_DIR="$(realpath -m "$REPO_ROOT/data/selfcap_bar_8cam60f")"
DATA_DIR_REAL="$(realpath -m "$DATA_DIR")"
if [ -z "$BASELINE_INIT_NPZ" ] && [ "$DATA_DIR_REAL" = "$CANONICAL_DATA_DIR" ]; then
  # Prefer the canonical protocol_v1 baseline init as template only for canonical SelfCap dataset.
  BASELINE_INIT_NPZ="$REPO_ROOT/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_${TOTAL_FRAMES}frames_step${KEYFRAME_STEP}.npz"
fi

CKPT_ARGS=()
if [ -n "$CKPT_PATH" ]; then
  CKPT_PATH="$(realpath -m "$CKPT_PATH")"
  if [ ! -f "$CKPT_PATH" ]; then
    echo "[ERROR] missing ckpt for resume: $CKPT_PATH"
    exit 1
  fi
  if [ -f "$RESULT_DIR/cfg.yml" ]; then
    CKPT_BASE="$(basename "$CKPT_PATH")"
    SNAP_SUFFIX="$CKPT_BASE"
    case "$CKPT_BASE" in
      ckpt_*.pt)
        SNAP_SUFFIX="${CKPT_BASE%.pt}"
        ;;
    esac
    CFG_SNAPSHOT="$RESULT_DIR/cfg_before_resume_from_${SNAP_SUFFIX}.yml"
    if [ -e "$CFG_SNAPSHOT" ]; then
      CFG_SNAPSHOT="$RESULT_DIR/cfg_before_resume_from_${SNAP_SUFFIX}_$(date -u +%Y%m%dT%H%M%SZ).yml"
    fi
    cp "$RESULT_DIR/cfg.yml" "$CFG_SNAPSHOT"
    echo "[PlanB+Feat] cfg snapshot:   $CFG_SNAPSHOT"
  fi
  CKPT_ARGS=(--ckpt-path "$CKPT_PATH")
fi

if [ ! -f "$BASELINE_INIT_NPZ" ]; then
  echo "[PlanB+Feat] baseline init missing, generating via combine_frames_fast_keyframes..."
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
  echo "[PlanB+Feat] planb init missing, generating via scripts/init_velocity_from_points.py..."
  "$VENV_PYTHON" "$PLANB_SCRIPT" \
    --data_dir "$DATA_DIR" \
    --baseline_init_npz "$BASELINE_INIT_NPZ" \
    --frame_start "$START_FRAME" \
    --frame_end_exclusive "$END_FRAME" \
    --keyframe_step "$KEYFRAME_STEP" \
    --max_match_distance "$PLANB_MAX_MATCH_DISTANCE" \
    --clip_quantile "$PLANB_CLIP_QUANTILE" \
    --out_dir "$PLANB_OUT_DIR"
fi

if [ ! -f "$PLANB_INIT_NPZ" ]; then
  echo "[ERROR] planb init still missing: $PLANB_INIT_NPZ"
  exit 1
fi

if [ ! -f "$VGGT_FEAT_CACHE_NPZ" ]; then
  echo "[PlanB+Feat] VGGT cache missing, precomputing first..."
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

if [ "$VGGT_FEAT_GATING" = "framediff" ]; then
  VGGT_CACHE_META_JSON="$(dirname "$VGGT_FEAT_CACHE_NPZ")/meta.json"
  if [ -f "$VGGT_CACHE_META_JSON" ]; then
    FRAMEDIFF_TOP_P_STATUS="$("$VENV_PYTHON" - "$VGGT_CACHE_META_JSON" "$VGGT_FEAT_GATING_TOP_P" <<'PY'
import json
import sys

meta_path = sys.argv[1]
try:
    requested = float(sys.argv[2])
except Exception:
    print("parse_error")
    raise SystemExit(0)

try:
    meta = json.load(open(meta_path, encoding="utf-8"))
except Exception:
    print("meta_read_error")
    raise SystemExit(0)

cache_top_p = meta.get("framediff_top_p")
if cache_top_p is None:
    print("missing")
    raise SystemExit(0)

try:
    cache_top_p_val = float(cache_top_p)
except Exception:
    print("meta_parse_error")
    raise SystemExit(0)

if abs(cache_top_p_val - requested) > 1e-12:
    print(f"mismatch:{cache_top_p_val}")
else:
    print("match")
PY
)"
    case "$FRAMEDIFF_TOP_P_STATUS" in
      mismatch:*)
        CACHE_TOP_P="${FRAMEDIFF_TOP_P_STATUS#mismatch:}"
        echo "[WARN] framediff top-p mismatch: VGGT_FEAT_GATING_TOP_P=$VGGT_FEAT_GATING_TOP_P but cache meta framediff_top_p=$CACHE_TOP_P ($VGGT_CACHE_META_JSON). For strict top-p comparisons, generate a new cache with matching framediff_top_p."
        ;;
      missing)
        echo "[WARN] framediff gating enabled but cache meta has no framediff_top_p ($VGGT_CACHE_META_JSON). For strict top-p comparisons, regenerate cache with explicit framediff_top_p."
        ;;
      parse_error|meta_read_error|meta_parse_error)
        echo "[WARN] unable to verify framediff_top_p from cache meta ($VGGT_CACHE_META_JSON); continue without blocking."
        ;;
    esac
  fi
fi

echo "[PlanB+Feat] data_dir:       $DATA_DIR"
echo "[PlanB+Feat] result_dir:     $RESULT_DIR"
echo "[PlanB+Feat] planb_init:     $PLANB_INIT_NPZ"
echo "[PlanB+Feat] feature_cache:  $VGGT_FEAT_CACHE_NPZ"
echo "[PlanB+Feat] frame range:    [$START_FRAME, $END_FRAME)"
echo "[PlanB+Feat] gpu/max:        $GPU / $MAX_STEPS"
if [ -n "$CKPT_PATH" ]; then
  echo "[PlanB+Feat] resume ckpt:    $CKPT_PATH"
fi
if [ -n "$EVAL_STEPS" ]; then
  echo "[PlanB+Feat] eval_steps:     $EVAL_STEPS"
fi
if [ -n "$SAVE_STEPS" ]; then
  echo "[PlanB+Feat] save_steps:     $SAVE_STEPS"
fi
if [ -n "$EXTRA_TRAIN_ARGS" ]; then
  echo "[PlanB+Feat] extra_args:     $EXTRA_TRAIN_ARGS"
fi
echo "[PlanB+Feat] planb params:   max_dist=$PLANB_MAX_MATCH_DISTANCE clip_q=$PLANB_CLIP_QUANTILE"
echo "[PlanB+Feat] feat params:    phi=$VGGT_FEAT_PHI_NAME loss=$VGGT_FEAT_LOSS_TYPE lambda=$LAMBDA_VGGT_FEAT start=$VGGT_FEAT_START_STEP ramp=$VGGT_FEAT_RAMP_STEPS every=$VGGT_FEAT_EVERY patch_k=$VGGT_FEAT_PATCH_K patch_hw=$VGGT_FEAT_PATCH_HW conf=$VGGT_FEAT_USE_CONF_RAW gating=$VGGT_FEAT_GATING top_p=$VGGT_FEAT_GATING_TOP_P"
echo "[PlanB+Feat] token proj:     layer=$TOKEN_LAYER_IDX dim=$TOKEN_PROJ_DIM seed=$TOKEN_PROJ_SEED"

CUDA_VISIBLE_DEVICES="$GPU" VGGT_MODEL_ID="$VGGT_MODEL_ID" VGGT_CACHE_DIR="$VGGT_MODEL_CACHE_DIR" \
"$VENV_PYTHON" "$TRAINER_SCRIPT" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
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
  "${CKPT_ARGS[@]}" \
  $(if [ "$EVAL_ON_TEST" = "1" ]; then echo --eval-on-test; fi) \
  ${EXTRA_TRAIN_ARGS}

"$VENV_PYTHON" "$THROUGHPUT_SCRIPT" "$RESULT_DIR"

echo "[PlanB+Feat] Done: $RESULT_DIR"
