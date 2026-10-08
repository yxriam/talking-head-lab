#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/etc/profile.d/conda.sh
conda activate /root/autodl-tmp/conda_envs/sadtalker

REF_DIR=/root/chatterbox_refs/ray_demo
OUT_BASE=/root/chatterbox_outputs/ray_demo/sadtalker_extfull_trim
AUDIO="$REF_DIR/ray_trim_16k.wav"
SOURCE_ORIG="$REF_DIR/ray2.jpg"
SOURCE_UP="$REF_DIR/ray2_upscaled_1024h.jpg"

mkdir -p "$OUT_BASE"

/usr/bin/ffmpeg -y -hide_banner -loglevel error \
  -i "$SOURCE_ORIG" \
  -vf "scale=-2:1024:flags=lanczos" \
  "$SOURCE_UP"

cd /root/autodl-tmp/SadTalker

python inference.py \
  --driven_audio "$AUDIO" \
  --source_image "$SOURCE_UP" \
  --checkpoint_dir /root/autodl-tmp/SadTalker/checkpoints \
  --result_dir "$OUT_BASE" \
  --size 512 \
  --preprocess extfull \
  --pose_style 18 \
  --expression_scale 1.15 \
  --batch_size 2

RAW=$(ls -t "$OUT_BASE"/*.mp4 | head -1)
FINAL="$OUT_BASE/ray_sadtalker_fullface_trim_ai_demo_watermarked.mp4"
PREVIEW="$OUT_BASE/ray_sadtalker_fullface_trim_preview.jpg"

/usr/bin/ffmpeg -y -hide_banner -loglevel error -i "$RAW" \
  -vf "drawtext=text=AI-GENERATED DEMO:x=18:y=18:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.45" \
  -c:v libx264 -preset veryfast -crf 18 \
  -c:a aac -b:a 128k \
  "$FINAL"

/usr/bin/ffmpeg -y -hide_banner -loglevel error \
  -ss 00:00:08 -i "$FINAL" -frames:v 1 "$PREVIEW"

echo "RAW=$RAW"
echo "FINAL=$FINAL"
echo "PREVIEW=$PREVIEW"
/usr/bin/ffprobe -v error \
  -show_entries stream=codec_type,codec_name,width,height,r_frame_rate \
  -show_entries format=duration,size \
  -of default=noprint_wrappers=1 "$FINAL"
