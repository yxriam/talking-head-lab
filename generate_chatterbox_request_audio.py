import pathlib
import time

import soundfile as sf
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS


PROMPT = "/root/chatterbox_refs/reference.m4a"
OUT_DIR = pathlib.Path("/root/chatterbox_outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FLOAT = OUT_DIR / "visa_fundraising_voice.wav"
OUT_PCM16 = OUT_DIR / "visa_fundraising_voice_pcm16.wav"

TEXT = (
    "Hi, I'm currently facing some difficult time. "
    "If you are kind, please give me some money to help me go through this moment."
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
    ta.save(str(OUT_FLOAT), wav.cpu(), model.sr)
    data = wav.squeeze(0).detach().cpu().numpy()
    sf.write(str(OUT_PCM16), data, model.sr, subtype="PCM_16")
    print(f"saved_float={OUT_FLOAT}")
    print(f"saved_pcm16={OUT_PCM16}")
    print(f"sample_rate={model.sr}")
    print(f"seconds={wav.shape[-1] / model.sr:.2f}")
    print(f"elapsed={time.time() - started:.1f}")


if __name__ == "__main__":
    main()
