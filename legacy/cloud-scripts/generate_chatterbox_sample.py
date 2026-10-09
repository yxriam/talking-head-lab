import pathlib
import time

import torchaudio as ta
from chatterbox.tts import ChatterboxTTS


PROMPT = "/root/chatterbox_refs/reference.m4a"
OUT_DIR = pathlib.Path("/root/chatterbox_outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "wantanglu_voice_clone_sample.wav"

TEXT = (
    "Hello, this is a short voice cloning test generated with Chatterbox. "
    "The goal is to stay close to the reference speaker's tone and rhythm."
)


def main():
    started = time.time()
    print("loading model")
    model = ChatterboxTTS.from_pretrained(device="cuda")
    print("generating")
    wav = model.generate(
        TEXT,
        audio_prompt_path=PROMPT,
        exaggeration=0.35,
        cfg_weight=0.5,
        temperature=0.75,
    )
    if wav.ndim == 1:
        wav = wav.unsqueeze(0)
    ta.save(str(OUT), wav.cpu(), model.sr)
    print(f"saved={OUT}")
    print(f"sample_rate={model.sr}")
    print(f"seconds={wav.shape[-1] / model.sr:.2f}")
    print(f"elapsed={time.time() - started:.1f}")


if __name__ == "__main__":
    main()
