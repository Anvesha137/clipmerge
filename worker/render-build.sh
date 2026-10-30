#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python - <<'PY'
import imageio_ffmpeg
print('Bundled FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())
PY
