#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/run_mvp_repro.sh [options]

Options:
  --gpu <id>                GPU id for smoke training (default: 2)
  --max-steps <n>           Trainer max/eval/save steps for Gate-0 smoke (default: 200)
  --start-frame <n>         Start frame for Gate-0 smoke (default: 0)
  --end-frame <n>           End frame(exclusive) for Gate-0 smoke (default: 60)
  --keyframe-step <n>       Keyframe step for Gate-0 smoke (default: 5)
  --gate0-data-dir <path>   Gate-0 dataset root, needs triangulation/ (default: data/4DGV_DeskGames)
  --result-root <path>      Output root for Gate-0 smoke (default: outputs/gate0_real_smoke)
  --selfcap-tar <path>      SelfCap release tar path (auto-detect when omitted)
  --adapter-script <path>   SelfCap adapter script (default: scripts/adapt_selfcap_release_to_freetime.py)
  --adapter-cmd <cmd>       Full adapter command to execute when adapter+tar exist
  --skip-gate0              Skip Gate-0 smoke even if data exists
  --skip-selfcap-adapter    Skip SelfCap adapter stage
  --dry-run                 Print commands without executing
  -h, --help                Show this help
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GPU=2
MAX_STEPS=200
START_FRAME=0
END_FRAME=60
KEYFRAME_STEP=5
GATE0_DATA_DIR="data/4DGV_DeskGames"
RESULT_ROOT="outputs/gate0_real_smoke"
SELFCAP_TAR=""
ADAPTER_SCRIPT="scripts/adapt_selfcap_release_to_freetime.py"
ADAPTER_CMD=""
RUN_GATE0=1
RUN_SELFCAP_ADAPTER=1
DRY_RUN=0
SELFCAP_TAR_USER_SET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu)
      GPU="$2"; shift 2 ;;
    --max-steps)
      MAX_STEPS="$2"; shift 2 ;;
    --start-frame)
      START_FRAME="$2"; shift 2 ;;
    --end-frame)
      END_FRAME="$2"; shift 2 ;;
    --keyframe-step)
      KEYFRAME_STEP="$2"; shift 2 ;;
    --gate0-data-dir)
      GATE0_DATA_DIR="$2"; shift 2 ;;
    --result-root)
      RESULT_ROOT="$2"; shift 2 ;;
    --selfcap-tar)
      SELFCAP_TAR="$2"; SELFCAP_TAR_USER_SET=1; shift 2 ;;
    --adapter-script)
      ADAPTER_SCRIPT="$2"; shift 2 ;;
    --adapter-cmd)
      ADAPTER_CMD="$2"; shift 2 ;;
    --skip-gate0)
      RUN_GATE0=0; shift ;;
    --skip-selfcap-adapter)
      RUN_SELFCAP_ADAPTER=0; shift ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1 ;;
  esac
done

run_cmd() {
  local cmd="$1"
  echo "+ $cmd"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    bash -lc "$cmd"
  fi
}

require_file() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "[error] missing required file: $path" >&2
    exit 1
  fi
}

cd "$ROOT_DIR"
require_file "scripts/build_report_pack.py"

if [[ "$SELFCAP_TAR_USER_SET" -eq 0 ]]; then
  for candidate in \
    "data/raw/selfcap/bar-release.tar.gz" \
    "data/selfcap/bar-release.tar.gz" \
    "data/raw/selfcap/selfcap_release.tar"
  do
    if [[ -f "$candidate" ]]; then
      SELFCAP_TAR="$candidate"
      break
    fi
  done
fi

if [[ -z "$SELFCAP_TAR" ]]; then
  SELFCAP_TAR="data/raw/selfcap/bar-release.tar.gz"
fi

VENV_ACTIVATE="third_party/FreeTimeGsVanilla/.venv/bin/activate"
COMBINE_SCRIPT="third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py"
TRAINER_SCRIPT="third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"

if [[ "$RUN_GATE0" -eq 1 ]]; then
  TRI_INPUT="$GATE0_DATA_DIR/triangulation"
  TOTAL_FRAMES=$((END_FRAME - START_FRAME))
  NPZ_PATH="$RESULT_ROOT/keyframes_${TOTAL_FRAMES}frames_step${KEYFRAME_STEP}.npz"

  if [[ -d "$TRI_INPUT" && -f "$VENV_ACTIVATE" && -f "$COMBINE_SCRIPT" && -f "$TRAINER_SCRIPT" ]]; then
    echo "[info] Gate-0 smoke prerequisites ready: $GATE0_DATA_DIR"
    run_cmd "mkdir -p '$RESULT_ROOT'"
    run_cmd "source '$VENV_ACTIVATE' && python '$COMBINE_SCRIPT' --input-dir '$TRI_INPUT' --output-path '$NPZ_PATH' --frame-start '$START_FRAME' --frame-end '$((END_FRAME - 1))' --keyframe-step '$KEYFRAME_STEP'"
    run_cmd "source '$VENV_ACTIVATE' && CUDA_VISIBLE_DEVICES='$GPU' python '$TRAINER_SCRIPT' default_keyframe_small --data-dir '$GATE0_DATA_DIR' --init-npz-path '$NPZ_PATH' --result-dir '$RESULT_ROOT' --start-frame '$START_FRAME' --end-frame '$END_FRAME' --max-steps '$MAX_STEPS' --eval-steps '$MAX_STEPS' --save-steps '$MAX_STEPS' --render-traj-path fixed"
  else
    echo "[warn] Skip Gate-0 smoke: prerequisites missing"
    echo "       need: $TRI_INPUT, $VENV_ACTIVATE, $COMBINE_SCRIPT, $TRAINER_SCRIPT"
  fi
fi

if [[ "$RUN_SELFCAP_ADAPTER" -eq 1 ]]; then
  if [[ -f "$ADAPTER_SCRIPT" && -f "$SELFCAP_TAR" ]]; then
    echo "[info] SelfCap adapter prerequisites ready: $ADAPTER_SCRIPT + $SELFCAP_TAR"
    if [[ -n "$ADAPTER_CMD" ]]; then
      run_cmd "$ADAPTER_CMD"
    else
      echo "[warn] adapter args are project-specific; pass --adapter-cmd to execute it"
    fi
  else
    echo "[warn] Skip SelfCap adapter: missing script or tar"
    echo "       script: $ADAPTER_SCRIPT"
    echo "       tar:    $SELFCAP_TAR"
  fi
fi

run_cmd "python3 scripts/build_report_pack.py"
echo "[done] MVP repro flow finished"
