#!/usr/bin/env bash
set -euo pipefail

host="${1:-${PHOTOPAINTER_HOST:-pi-window}}"
remote_image_dir="${PHOTOPAINTER_REMOTE_IMAGE_DIR:-/home/ravi/Pictures/hokusai-photopainter}"
remote_python="${PHOTOPAINTER_REMOTE_PYTHON:-/home/ravi/photopainter-venv/bin/python}"

if [[ ! -d photopainter_800x480_bmp ]]; then
  echo "Missing photopainter_800x480_bmp/. Run: mise run build" >&2
  exit 1
fi

ssh "$host" "mkdir -p '$remote_image_dir'"
rsync -a scripts/photopainter_show_hokusai.py "$host:/home/ravi/photopainter-show-hokusai.py"
rsync -a scripts/photopainter_display_image.py "$host:/home/ravi/photopainter-display-image.py"
ssh "$host" "chmod +x /home/ravi/photopainter-show-hokusai.py /home/ravi/photopainter-display-image.py && test -x '$remote_python'"

# Keep the frame's state file even when pruning images that no longer exist locally.
rsync -a --delete --exclude='.photopainter-state.json' photopainter_800x480_bmp/ "$host:$remote_image_dir/"

ssh "$host" "find '$remote_image_dir' -maxdepth 1 -type f -name '*.bmp' | wc -l"
