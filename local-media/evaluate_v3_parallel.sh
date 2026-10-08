#!/usr/bin/env bash
set -euo pipefail

run=${1:-/mnt/d/project/NZ/cv/benchmark-results/2026-09-24-multi-sample-v2}
model_root=${2:-/opt/media-models}
workers=${3:-4}
parts="$run/visual-v3-parts"

mkdir -p "$parts"
find "$run/cases" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \
  | sort \
  | xargs -P "$workers" -I '{}' bash -c '
      case_id="$1"
      run="$2"
      model_root="$3"
      parts="$4"
      OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 EVAL_FRAME_STRIDE=6 \
        /opt/media-models/InstantID/.venv/bin/python \
        /mnt/d/project/NZ/cv/local-media/evaluate_v3_case.py \
        "$run/cases/$case_id" "$model_root" "$parts/$case_id.json"
    ' _ '{}' "$run" "$model_root" "$parts"
