#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 1 ]; then
  echo "Usage: $0 [result_dir]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RESULT_TAG="${RESULT_TAG:-feature_loss_v2_gated_600}"
export VGGT_FEAT_GATING="${VGGT_FEAT_GATING:-framediff}"
export VGGT_FEAT_GATING_TOP_P="${VGGT_FEAT_GATING_TOP_P:-0.10}"

if [ "$#" -eq 1 ]; then
  exec "$SCRIPT_DIR/run_train_feature_loss_v2_selfcap.sh" "$1"
fi
exec "$SCRIPT_DIR/run_train_feature_loss_v2_selfcap.sh"
