#!/usr/bin/env bash
set -euo pipefail
source /root/miniconda3/etc/profile.d/conda.sh

A2H_SITE=$(conda run -n a2h10 python -c 'import site; print(site.getsitepackages()[0])')
CHAT_SITE=$(conda run -n Chatterbox python -c 'import site; print(site.getsitepackages()[0])')
echo "${A2H_SITE}" > "${CHAT_SITE}/a2h10_torch.pth"
conda run -n Chatterbox python -c 'import torch, torchaudio; print(torch.__version__, torch.cuda.is_available(), torchaudio.__version__)'
