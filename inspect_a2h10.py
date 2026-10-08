import importlib.util as u
import sys

print(sys.version)
for module in ["torch", "torchaudio", "transformers", "diffusers", "librosa", "soundfile", "numpy"]:
    print(module, bool(u.find_spec(module)))
try:
    import torch

    print("torch", torch.__version__, "cuda", torch.cuda.is_available(), torch.version.cuda)
except Exception as exc:
    print("torch_error", repr(exc))
