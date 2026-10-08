import pathlib
import time

import soundfile as sf
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS


PROMPT = "/root/chatterbox_refs/ray_demo/ray2_british_prompt_24s.wav"
OUT_DIR = pathlib.Path("/root/chatterbox_outputs/ray_demo")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FLOAT = OUT_DIR / "ray_british_disclosed_recommendation_voice.wav"
OUT_PCM16 = OUT_DIR / "ray_british_disclosed_recommendation_voice_pcm16.wav"

TEXT = (
    "This is an AI generated demo made with Ray's consent. "
    "Ray would like to recommend a very talented student to your company, "
    "and he believes she would do a great job."
)


def main():
    started = time.time()
    print("loading model")
    model = ChatterboxTTS.from_pretrained(device="cuda")
    print("generating")
    wav = model.generate(
        TEXT,
        audio_prompt_path=PROMPT,
        exaggeration=0.25,
        cfg_weight=0.45,
        temperature=0.55,
        repetition_penalty=1.18,
    )
    if wav.ndim == 1:
        wav = wav.unsqueeze(0)
    ta.save(str(OUT_FLOAT), wav.cpu(), model.sr)
    data = wav.squeeze(0).detach().cpu().numpy()
    sf.write(str(OUT_PCM16), data, model.sr, subtype="PCM_16")
    print(f"text={TEXT}")
    print(f"prompt={PROMPT}")
    print(f"saved_float={OUT_FLOAT}")
    print(f"saved_pcm16={OUT_PCM16}")
    print(f"sample_rate={model.sr}")
    print(f"seconds={wav.shape[-1] / model.sr:.2f}")
    print(f"elapsed={time.time() - started:.1f}")


if __name__ == "__main__":
    main()
