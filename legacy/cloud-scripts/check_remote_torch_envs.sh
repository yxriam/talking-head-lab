#!/usr/bin/env bash
set -u
source /root/miniconda3/etc/profile.d/conda.sh

specs=(
  "-n a2h10"
  "-n streamsub"
  "-p /root/autodl-tmp/conda_envs/echomimic"
  "-p /root/autodl-tmp/conda_envs/musetalk_fast"
  "-p /root/autodl-tmp/conda_envs/sadtalker"
  "-p /root/autodl-tmp/conda_envs/musetalk_eval_gpu"
)

for spec in "${specs[@]}"; do
  echo "=== ${spec}"
  # shellcheck disable=SC2086
  conda run ${spec} python -c "import importlib.util as u; print('has_torch', bool(u.find_spec('torch'))); import torch; print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available(), 'cuda', torch.version.cuda)" 2>&1 | head -20 || true
done
