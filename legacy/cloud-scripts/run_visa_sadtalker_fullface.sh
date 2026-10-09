#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/etc/profile.d/conda.sh
conda activate /root/autodl-tmp/conda_envs/sadtalker

cd /root/autodl-tmp/SadTalker

OUT_BASE=/root/chatterbox_outputs/sadtalker_visa_fullface_extfull_demo
mkdir -p "$OUT_BASE"

python inference.py \
  --driven_audio /root/chatterbox_outputs/visa_synthetic_demo_voice_pcm16.wav \
  --source_image /root/chatterbox_refs/visa.jpg \
  --checkpoint_dir /root/autodl-tmp/SadTalker/checkpoints \
  --result_dir "$OUT_BASE" \
  --size 512 \
  --preprocess extfull \
  --pose_style 18 \
  --expression_scale 1.25 \
  --batch_size 2

RAW=$(ls -t "$OUT_BASE"/*.mp4 | head -1)
FINAL="$OUT_BASE/visa_sadtalker_fullface_ai_demo_watermarked.mp4"
PREVIEW="$OUT_BASE/preview_frame.jpg"

/usr/bin/ffmpeg -y -hide_banner -loglevel error -i "$RAW" \
  -vf "drawtext=text=AI-GENERATED DEMO:x=18:y=18:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.45" \
  -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 128k "$FINAL"

/usr/bin/ffmpeg -y -hide_banner -loglevel error -ss 00:00:04 -i "$FINAL" -frames:v 1 "$PREVIEW"

echo "RAW=$RAW"
echo "FINAL=$FINAL"
echo "PREVIEW=$PREVIEW"
/usr/bin/ffprobe -v error \
  -show_entries stream=codec_type,codec_name,width,height,r_frame_rate \
  -show_entries format=duration,size \
  -of default=noprint_wrappers=1 "$FINAL"
