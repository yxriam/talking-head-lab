#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3-venv python3-dev ffmpeg git build-essential libgl1 libglib2.0-0 ca-certificates
python3 --version
ffmpeg -version | head -n 1
echo PREPARE_COMPLETE
