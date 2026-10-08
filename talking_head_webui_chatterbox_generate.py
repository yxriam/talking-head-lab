import argparse
import pathlib
import time

import soundfile as sf
import torch
from chatterbox.tts import ChatterboxTTS


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--temperature", type=float, default=0.55)
    parser.add_argument("--exaggeration", type=float, default=0.25)
    parser.add_argument("--cfg-weight", type=float, default=0.45)
    return parser.parse_args()


def main():
    args = parse_args()
    started = time.time()
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("loading Chatterbox")
    model = ChatterboxTTS.from_pretrained(device="cuda")
    print("generating speech")
    with torch.inference_mode():
        wav = model.generate(
            args.text,
            audio_prompt_path=args.prompt,
            exaggeration=args.exaggeration,
            cfg_weight=args.cfg_weight,
            temperature=args.temperature,
            repetition_penalty=1.18,
        )
    if wav.ndim == 2:
        wav = wav.squeeze(0)
    data = wav.detach().cpu().numpy()
    sf.write(str(out_path), data, model.sr, subtype="PCM_16")
    print(f"saved={out_path}")
    print(f"sample_rate={model.sr}")
    print(f"seconds={len(data) / model.sr:.2f}")
    print(f"elapsed={time.time() - started:.1f}")


if __name__ == "__main__":
    main()
