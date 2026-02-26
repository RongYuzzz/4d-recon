#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $(basename "$0") [options]

Extract selected frame indices from a video into JPG files.

Options:
  --video PATH         Input video path (required)
  --out_dir DIR        Output directory (default: outputs/qualitative/planb_vs_baseline/frames)
  --frames LIST        Comma-separated frame indices (default: 0,30,59)
  --overwrite          Overwrite existing JPG files
  -h, --help           Show this help
USAGE
}

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg not found. 请先安装 ffmpeg（例如: sudo apt-get install -y ffmpeg）" >&2
  exit 127
fi
if ! command -v ffprobe >/dev/null 2>&1; then
  echo "ERROR: ffprobe not found. 请先安装 ffmpeg 套件（含 ffprobe）" >&2
  exit 127
fi

VIDEO=""
OUT_DIR="outputs/qualitative/planb_vs_baseline/frames"
FRAMES="0,30,59"
OVERWRITE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --video)
      VIDEO="$2"
      shift 2
      ;;
    --out_dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --frames)
      FRAMES="$2"
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

if [[ -z "$VIDEO" ]]; then
  echo "ERROR: --video is required" >&2
  usage >&2
  exit 2
fi
if [[ ! -f "$VIDEO" ]]; then
  echo "ERROR: input video missing: $VIDEO" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"

IFS=',' read -r -a frame_indices <<< "$FRAMES"
if [[ "${#frame_indices[@]}" -eq 0 ]]; then
  echo "ERROR: no frame indices provided" >&2
  exit 2
fi

total_frames="$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$VIDEO" | tr -d '\r' || true)"
if [[ ! "$total_frames" =~ ^[0-9]+$ ]]; then
  total_frames="$(ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of csv=p=0 "$VIDEO" | tr -d '\r' || true)"
fi
if [[ ! "$total_frames" =~ ^[0-9]+$ || "$total_frames" -le 0 ]]; then
  echo "ERROR: failed to detect video frame count: $VIDEO" >&2
  exit 3
fi

for raw_idx in "${frame_indices[@]}"; do
  idx="${raw_idx// /}"
  if [[ -z "$idx" ]]; then
    continue
  fi
  if [[ ! "$idx" =~ ^[0-9]+$ ]]; then
    echo "ERROR: frame index must be non-negative integer, got: $idx" >&2
    exit 2
  fi

  out_jpg="$OUT_DIR/frame_$(printf '%06d' "$idx").jpg"
  if [[ -f "$out_jpg" && "$OVERWRITE" -ne 1 ]]; then
    echo "ERROR: output exists: $out_jpg (use --overwrite to replace)" >&2
    exit 2
  fi

  actual_idx="$idx"
  if (( idx >= total_frames )); then
    actual_idx=$((total_frames - 1))
    echo "WARN: requested frame $idx exceeds max index $((total_frames - 1)); fallback to $actual_idx" >&2
  fi

  ff_flag=(-n)
  if [[ "$OVERWRITE" -eq 1 ]]; then
    ff_flag=(-y)
  fi

  ffmpeg "${ff_flag[@]}" -i "$VIDEO" -vf "select=eq(n\\,$actual_idx)" -vframes 1 -q:v 2 "$out_jpg" >/dev/null 2>&1

  if [[ ! -s "$out_jpg" ]]; then
    echo "ERROR: failed to extract frame $idx (actual=$actual_idx) from $VIDEO" >&2
    exit 3
  fi
  echo "wrote $out_jpg"
done
