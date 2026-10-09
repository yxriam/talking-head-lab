# Three portrait/video examples

[中文](EXAMPLES.md) · [English](EXAMPLES.en.md) · [Back to home](../../../README.en.md)

All three people are fictional synthetic inputs. Every video is an actual SadTalker output. The examples share the same synthetic driving audio to compare results across different photographs.

| Example | Input download | Video with sound | Actual duration | Video job time |
|---|---|---|---|---|
| 1: woman | [PNG](../synthetic-input.png) | [MP4](../sadtalker-original-demo.mp4) | 4.736 s | 61.9 s |
| 2: man | [PNG](portrait-02.png) | [MP4](video-02.mp4) | 4.736 s | 64.3 s |
| 3: older woman | [PNG](portrait-03.png) | [MP4](video-03.mp4) | 4.736 s | 57.6 s |

[Driving audio: actual Chatterbox output, 4.68 s](../generated-voice.wav) · [Reference voice: system synthesis](../reference-voice.wav)

Spoken text: Welcome to Talking Head Lab. This is an AI generated demonstration.

## Try it with fewer steps

1. Before installing anything, open a voiced MP4 or watch the GIFs on the home page.
2. With model services ready, download any original portrait and the driving audio, upload both in “AI Portrait Video,” select SadTalker and generate.
3. To change the words, upload the reference voice in “Voice Cloning,” generate new speech and send it to video.

No Facebook collection is needed. The [setup guide](../../guides/SETUP.en.md) covers model preparation and startup.

## Sources and limitations

- Inputs: example 1 uses the existing imagegen portrait. Examples 2/3 were each generated once by the built-in imagegen tool without real-person references. These are inputs, not outputs of the project's video model.
- Outputs: example 1 reuses the accepted original-image run; examples 2/3 each ran once. The original PNG goes directly to the model, without background replacement. Native model cropping/resizing remains enabled.
- Presentation: JPEGs are thumbnails only. Each GIF is derived from its MP4, at 240px/8fps, with a synthetic label and no sound. Original PNGs and voiced MP4s remain unmodified.
- Timings describe these local jobs, not general model performance. No detection was rerun for this update, and old background-replacement outputs are excluded from the three examples.

[Jobs, input/output SHA256 and media metadata](manifest.json) · [Full asset provenance](../PROVENANCE.md) · [Run and publication record](../../change-records/2026-10-09-progressive-gallery/记录.md)
