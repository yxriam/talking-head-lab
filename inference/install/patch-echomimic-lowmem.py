"""Apply the local low-memory loader patch to the official EchoMimic V1 checkout."""

from pathlib import Path


ROOT = Path("/opt/media-models/EchoMimic")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Expected source text was not found in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


infer = ROOT / "infer_audio2vid_acc.py"
replace_once(
    infer,
    "        config.pretrained_vae_path,\n    ).to(\"cuda\", dtype=weight_dtype)",
    "        config.pretrained_vae_path,\n        torch_dtype=weight_dtype,\n        low_cpu_mem_usage=True,\n    ).to(\"cuda\")",
)
replace_once(
    infer,
    "        subfolder=\"unet\",\n    ).to(dtype=weight_dtype, device=device)",
    "        subfolder=\"unet\",\n        torch_dtype=weight_dtype,\n        low_cpu_mem_usage=True,\n    ).to(device=device)",
)
replace_once(
    infer,
    "        torch.load(config.reference_unet_path, map_location=\"cpu\"),",
    "        torch.load(config.reference_unet_path, map_location=\"cpu\", weights_only=True, mmap=True),",
)
replace_once(
    infer,
    "            unet_additional_kwargs=infer_config.unet_additional_kwargs,\n        ).to(dtype=weight_dtype, device=device)",
    "            unet_additional_kwargs=infer_config.unet_additional_kwargs,\n            torch_dtype=weight_dtype,\n        ).to(device=device)",
)
replace_once(
    infer,
    "        torch.load(config.denoising_unet_path, map_location=\"cpu\"),",
    "        torch.load(config.denoising_unet_path, map_location=\"cpu\", weights_only=True, mmap=True),",
)
replace_once(
    infer,
    "    face_locator.load_state_dict(torch.load(config.face_locator_path))",
    "    face_locator.load_state_dict(torch.load(config.face_locator_path, map_location=\"cpu\", weights_only=True, mmap=True))",
)
replace_once(
    infer,
    "                xyxy = select_bbox[:4]\n                xyxy = np.round(xyxy).astype('int')",
    "                xyxy = np.asarray(select_bbox[:4], dtype=np.float32)\n                xyxy = np.round(xyxy).astype('int')",
)

unet = ROOT / "src/models/unet_3d_echo.py"
replace_once(
    unet,
    "        mm_zero_proj_out=False,\n    ):",
    "        mm_zero_proj_out=False,\n        torch_dtype=None,\n    ):",
)
replace_once(
    unet,
    "        model = cls.from_config(unet_config, **unet_additional_kwargs)\n        # load the vanilla weights",
    "        model = cls.from_config(unet_config, **unet_additional_kwargs)\n        if torch_dtype is not None:\n            model = model.to(dtype=torch_dtype)\n        # load the vanilla weights",
)
replace_once(
    unet,
    "                map_location=\"cpu\",\n                weights_only=True,\n            )",
    "                map_location=\"cpu\",\n                weights_only=True,\n                mmap=True,\n            )",
)
replace_once(
    unet,
    "                    motion_module_path, map_location=\"cpu\", weights_only=True\n                )",
    "                    motion_module_path, map_location=\"cpu\", weights_only=True, mmap=True\n                )",
)

print("EchoMimic low-memory loader patch is applied.")
