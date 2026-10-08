# Talking Head WebUI

This WebUI wraps the existing remote Chatterbox + SadTalker pipeline.

## Server

Start:

```bash
bash /root/talking_head_webui/start.sh
```

Stop:

```bash
bash /root/talking_head_webui/stop.sh
```

The app listens on the server at:

```text
127.0.0.1:7860
```

## Windows Access

From this workspace, run:

```powershell
.\open_talking_head_webui_tunnel.ps1
```

Then open:

```text
http://127.0.0.1:7860
```

Keep the PowerShell tunnel window open while using the UI.

## Inputs

- Face image
- Voice reference audio or video
- Text to speak

The app extracts a voice prompt from the uploaded audio/video, generates speech with Chatterbox, renders full-face motion with SadTalker, and returns an MP4.

The spoken text is used as entered. The current video overlay is a configurable placeholder visual notice, defaulting to `AI`, so it can be replaced later with a stronger icon and warning layer.
