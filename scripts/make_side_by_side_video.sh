#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $(basename "$0") [options]

Create side-by-side comparison video (baseline vs planb) with labels.

Options:
  --left PATH          Left video input (default: baseline step599 video)
  --right PATH         Right video input (default: planb step599 video)
  --out_dir DIR        Output directory (default: outputs/qualitative/planb_vs_baseline)
  --out_name NAME      Output filename (default: planb_vs_baseline_step599.mp4)
  --left_label TEXT    Left label text (default: baseline_600)
  --right_label TEXT   Right label text (default: planb_init_600)
  --overwrite          Overwrite output if exists
  -h, --help           Show this help
USAGE
}

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg not found. 请先安装 ffmpeg（例如: sudo apt-get install -y ffmpeg）" >&2
  exit 127
fi

LEFT="outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4"
RIGHT="outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/videos/traj_4d_step599.mp4"
OUT_DIR="outputs/qualitative/planb_vs_baseline"
OUT_NAME="planb_vs_baseline_step599.mp4"
LEFT_LABEL="baseline_600"
RIGHT_LABEL="planb_init_600"
OVERWRITE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --left)
      LEFT="$2"
      shift 2
      ;;
    --right)
      RIGHT="$2"
      shift 2
      ;;
    --out_dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --out_name)
      OUT_NAME="$2"
      shift 2
      ;;
    --left_label)
      LEFT_LABEL="$2"
      shift 2
      ;;
    --right_label)
      RIGHT_LABEL="$2"
      shift 2
      ;;
    --overwrite)
      OVERWRITE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$LEFT" ]]; then
  echo "ERROR: left input video missing: $LEFT" >&2
  exit 2
fi
if [[ ! -f "$RIGHT" ]]; then
  echo "ERROR: right input video missing: $RIGHT" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
OUT_PATH="$OUT_DIR/$OUT_NAME"

if [[ -f "$OUT_PATH" && "$OVERWRITE" -ne 1 ]]; then
  echo "ERROR: output already exists: $OUT_PATH (use --overwrite to replace)" >&2
  exit 2
fi

# Escape drawtext meta chars for robust label rendering.
escape_drawtext() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//:/\\:}"
  s="${s//\'/\\\\\'}"
  printf '%s' "$s"
}

LEFT_ESCAPED="$(escape_drawtext "$LEFT_LABEL")"
RIGHT_ESCAPED="$(escape_drawtext "$RIGHT_LABEL")"

FILTER="[0:v]setpts=PTS-STARTPTS,scale=960:-2,drawtext=text='${LEFT_ESCAPED}':x=20:y=20:fontcolor=white:fontsize=34:box=1:boxcolor=black@0.55[v0];[1:v]setpts=PTS-STARTPTS,scale=960:-2,drawtext=text='${RIGHT_ESCAPED}':x=20:y=20:fontcolor=white:fontsize=34:box=1:boxcolor=black@0.55[v1];[v0][v1]hstack=inputs=2[v]"

FFMPEG_OVERWRITE=(-n)
if [[ "$OVERWRITE" -eq 1 ]]; then
  FFMPEG_OVERWRITE=(-y)
fi

ffmpeg "${FFMPEG_OVERWRITE[@]}" -i "$LEFT" -i "$RIGHT" \
  -filter_complex "$FILTER" \
  -map "[v]" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  "$OUT_PATH"

echo "wrote $OUT_PATH"
