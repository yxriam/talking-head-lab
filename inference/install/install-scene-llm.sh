#!/usr/bin/env bash
set -euo pipefail
export HF_HUB_DISABLE_TELEMETRY=1

models=/opt/media-models
llama="$models/llama.cpp"
root="$models/scene-llm"

if [[ ! -d "$llama/.git" ]]; then
    git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$llama"
fi
apt-get update -qq
apt-get install -y -qq build-essential cmake aria2 wget

# Install only NVIDIA's WSL CUDA compiler components. The Windows driver stays
# authoritative; installing Linux driver meta-packages inside WSL would break it.
if [[ ! -x /usr/local/cuda-12.8/bin/nvcc ]]; then
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb \
        -O /tmp/cuda-keyring.deb
    dpkg -i /tmp/cuda-keyring.deb
    apt-get update -qq
    apt-get install -y -qq cuda-nvcc-12-8
fi

# PyTorch already ships the matching cuBLAS runtime and headers, so reuse them
# instead of installing a second full CUDA toolkit.
cublas="$models/runtime/lib/python3.10/site-packages/nvidia/cublas"
[[ -f "$cublas/include/cublas_v2.h" ]] || { echo "Missing PyTorch cuBLAS files" >&2; exit 1; }
ln -sf "$cublas"/include/* /usr/local/cuda-12.8/include/
ln -sf "$cublas/lib/libcublas.so.12" /usr/local/cuda-12.8/lib64/libcublas.so.12
ln -sf "$cublas/lib/libcublas.so.12" /usr/local/cuda-12.8/lib64/libcublas.so
ln -sf "$cublas/lib/libcublasLt.so.12" /usr/local/cuda-12.8/lib64/libcublasLt.so.12
ln -sf "$cublas/lib/libcublasLt.so.12" /usr/local/cuda-12.8/lib64/libcublasLt.so

cmake -S "$llama" -B "$llama/build-cuda" -DGGML_NATIVE=ON -DGGML_CUDA=ON \
    -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc -DCMAKE_CUDA_ARCHITECTURES=120 \
    -DCUDAToolkit_ROOT=/usr/local/cuda-12.8 -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build "$llama/build-cuda" --config Release -j 12 --target llama-cli

mkdir -p "$root"
aria2c -c -x 16 -s 16 -k 4M --file-allocation=none --timeout=60 --connect-timeout=30 \
    --max-tries=20 --retry-wait=3 --console-log-level=warn \
    -d "$root" -o Qwen3-1.7B-Q8_0.gguf \
    https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q8_0.gguf

smoke="$root/smoke.log"
env LD_LIBRARY_PATH="/usr/local/cuda-12.8/lib64:$cublas/lib" \
    "$llama/build-cuda/bin/llama-cli" -m "$root/Qwen3-1.7B-Q8_0.gguf" \
    -ngl 99 -c 256 -n 4 -t 8 -tb 8 --temp 0 --single-turn --simple-io \
    --grammar 'root ::= "OK"' --log-disable --no-display-prompt --no-warmup \
    -p '/no_think Reply exactly OK' > "$smoke" 2>&1
grep -q 'OK' "$smoke"
rm -f "$smoke"
touch "$root/READY"
echo SCENE_LLM_READY
