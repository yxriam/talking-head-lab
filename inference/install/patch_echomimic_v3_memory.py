"""Patch EchoMimic V3 Flash to lower CPU peak during model startup."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Unexpected {label} layout: found {count}")
    return text.replace(old, new, 1)


def main(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    backup = path.with_suffix(path.suffix + ".before-memory-fix")
    if not backup.exists():
        shutil.copy2(path, backup)

    text = original
    if "import gc\n" not in text:
        text = replace_once(text, "import os\n", "import os\nimport gc\n", "import")

    if "def release_cpu_memory():" not in text:
        text = replace_once(
            text,
            "import argparse\n\n",
            """import argparse
import ctypes


def release_cpu_memory():
    \"\"\"Return freed checkpoint pages to WSL instead of retaining them in glibc.\"\"\"
    gc.collect()
    try:
        ctypes.CDLL(\"libc.so.6\").malloc_trim(0)
    except OSError:
        pass

""",
            "memory release helper",
        )

    audio_block = """    # Load audio models
    audio_encoder = Wav2Vec2Model.from_pretrained(wav2vec_model_dir, local_files_only=True).to('cpu')
    audio_encoder.feature_extractor._freeze_parameters()
    wav2vec_feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(wav2vec_model_dir, local_files_only=True)

"""
    if audio_block in text:
        text = replace_once(
            text,
            audio_block,
            "    # Audio models are loaded after the large transformer checkpoint to lower peak RAM.\n\n",
            "audio preload",
        )

    checkpoint_cleanup = """        m, u = transformer.load_state_dict(state_dict, strict=False)
        print(f"missing keys: {len(m)}, unexpected keys: {len(u)}")
"""
    checkpoint_cleanup_new = checkpoint_cleanup + """        del state_dict
        gc.collect()
"""
    if "del state_dict\n        gc.collect()" not in text and "del state_dict\n        release_cpu_memory()" not in text:
        text = replace_once(text, checkpoint_cleanup, checkpoint_cleanup_new, "transformer checkpoint")

    transformer_loaded = """    )

    if transformer_path is not None:
"""
    early_gpu_move = """    )

    # In full-GPU mode, move the initialized transformer before reading the
    # Flash checkpoint. Otherwise the CPU briefly holds both complete copies.
    if GPU_memory_mode != "sequential_cpu_offload":
        transformer.to(device=device)
        gc.collect()

    if transformer_path is not None:
"""
    if "move the initialized transformer before reading" not in text:
        text = replace_once(text, transformer_loaded, early_gpu_move, "early transformer device move")

    text = text.replace("        transformer.to(device=device)\n        gc.collect()\n", "        transformer.to(device=device)\n        release_cpu_memory()\n", 1)
    text = text.replace("        del state_dict\n        gc.collect()\n", "        del state_dict\n        release_cpu_memory()\n", 1)
    duplicate_cleanup = """        del state_dict
        release_cpu_memory()
        del state_dict
        release_cpu_memory()
"""
    single_cleanup = """        del state_dict
        release_cpu_memory()
"""
    while duplicate_cleanup in text:
        text = text.replace(duplicate_cleanup, single_cleanup, 1)

    vae_loaded = """    ).to(weight_dtype)

    if vae_path is not None:
"""
    vae_gpu = """    ).to(weight_dtype)
    if GPU_memory_mode != "sequential_cpu_offload":
        vae.to(device=device)
        release_cpu_memory()

    if vae_path is not None:
"""
    if "vae.to(device=device)" not in text:
        text = replace_once(text, vae_loaded, vae_gpu, "early VAE device move")

    text_eval = """    text_encoder = text_encoder.eval()

    # Get Clip Image Encoder
"""
    text_gpu = """    text_encoder = text_encoder.eval()
    if GPU_memory_mode != "sequential_cpu_offload":
        text_encoder.to(device=device)
        release_cpu_memory()

    # Get Clip Image Encoder
"""
    if "text_encoder.to(device=device)" not in text:
        text = replace_once(text, text_eval, text_gpu, "early text encoder device move")

    clip_eval = """    clip_image_encoder = clip_image_encoder.eval()

    # Get Scheduler
"""
    clip_gpu = """    clip_image_encoder = clip_image_encoder.eval()
    if GPU_memory_mode != "sequential_cpu_offload":
        clip_image_encoder.to(device=device)
        release_cpu_memory()

    # Get Scheduler
"""
    if "clip_image_encoder.to(device=device)" not in text:
        text = replace_once(text, clip_eval, clip_gpu, "early CLIP device move")

    # Hybrid placement keeps the large diffusion path on GPU while Accelerate
    # pages the conditioning encoders through the remaining VRAM on demand.
    text = text.replace(
        'if GPU_memory_mode != "sequential_cpu_offload":\n        transformer.to(device=device)',
        'if GPU_memory_mode in {"gpu", "hybrid"}:\n        transformer.to(device=device)',
        1,
    )
    text = text.replace(
        'if GPU_memory_mode != "sequential_cpu_offload":\n        vae.to(device=device)',
        'if GPU_memory_mode in {"gpu", "hybrid"}:\n        vae.to(device=device)',
        1,
    )
    text = text.replace(
        'if GPU_memory_mode != "sequential_cpu_offload":\n        text_encoder.to(device=device)',
        'if GPU_memory_mode == "gpu":\n        text_encoder.to(device=device)',
        1,
    )
    text = text.replace(
        'if GPU_memory_mode != "sequential_cpu_offload":\n        clip_image_encoder.to(device=device)',
        'if GPU_memory_mode == "gpu":\n        clip_image_encoder.to(device=device)',
        1,
    )

    pipeline_mode = """    if GPU_memory_mode == "sequential_cpu_offload":
        pipeline.enable_sequential_cpu_offload()
    else:
        pipeline.to(device=device)
"""
    hybrid_mode = """    if GPU_memory_mode == "sequential_cpu_offload":
        pipeline.enable_sequential_cpu_offload()
    elif GPU_memory_mode == "hybrid":
        from accelerate import cpu_offload
        cpu_offload(pipeline.text_encoder, execution_device=device)
        cpu_offload(pipeline.clip_image_encoder, execution_device=device)
    else:
        pipeline.to(device=device)
"""
    if "cpu_offload(pipeline.text_encoder" not in text:
        text = replace_once(text, pipeline_mode, hybrid_mode, "hybrid pipeline placement")

    marker = """    coefficients = get_teacache_coefficients(model_name) if enable_teacache else None
"""
    deferred_audio = """    # Defer Wav2Vec allocation until checkpoint-backed tensors have been released.
    audio_encoder = Wav2Vec2Model.from_pretrained(wav2vec_model_dir, local_files_only=True).to('cpu')
    audio_encoder.feature_extractor._freeze_parameters()
    wav2vec_feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(wav2vec_model_dir, local_files_only=True)

"""
    if deferred_audio not in text:
        text = replace_once(text, marker, deferred_audio + marker, "deferred audio insertion")

    path.write_text(text, encoding="utf-8")
    print(f"patched {path}")
    print(f"backup {backup}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
