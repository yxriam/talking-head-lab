from pathlib import Path
import subprocess
root=Path('/mnt/d/project/facebook/talking-head-lab/docs/showcase')
filters='fps=10,scale=360:-1:flags=lanczos,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text=AI_GENERATED_SYNTHETIC_PERSON:fontsize=13:fontcolor=white:box=1:boxcolor=black@0.6:x=10:y=h-26,split[a][b];[a]palettegen[p];[b][p]paletteuse'
subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(root/'sadtalker-original-demo.mp4'),'-filter_complex',filters,'-loop','0',str(root/'sadtalker-original-demo.gif')],check=True)
print('ORIGINAL_IMAGE_GIF_EXPORTED')
