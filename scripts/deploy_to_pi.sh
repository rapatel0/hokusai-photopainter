#!/usr/bin/env bash
set -euo pipefail

host="${1:-${PHOTOPAINTER_HOST:?Set PHOTOPAINTER_HOST or pass a host as the first argument}}"
remote_image_dir="${PHOTOPAINTER_REMOTE_IMAGE_DIR:?Set PHOTOPAINTER_REMOTE_IMAGE_DIR}"
remote_python="${PHOTOPAINTER_REMOTE_PYTHON:?Set PHOTOPAINTER_REMOTE_PYTHON}"
remote_script_dir="${PHOTOPAINTER_REMOTE_SCRIPT_DIR:?Set PHOTOPAINTER_REMOTE_SCRIPT_DIR}"
remote_show_script="$remote_script_dir/photopainter-show-hokusai.py"
remote_display_script="$remote_script_dir/photopainter-display-image.py"

remote_command() {
  printf '%q ' "$@"
}

if [[ ! -d photopainter_800x480_bmp ]]; then
  echo "Missing photopainter_800x480_bmp/. Run: mise run build" >&2
  exit 1
fi

ssh "$host" "$(remote_command mkdir -p "$remote_image_dir")"
rsync -a -s scripts/photopainter_show_hokusai.py "$host:$remote_show_script"
rsync -a -s scripts/photopainter_display_image.py "$host:$remote_display_script"
ssh "$host" "$(remote_command chmod +x "$remote_show_script" "$remote_display_script") && $(remote_command test -x "$remote_python")"

# Keep the frame's state file even when pruning images that no longer exist locally.
rsync -a -s --delete --exclude='.photopainter-state.json' photopainter_800x480_bmp/ "$host:$remote_image_dir/"

ssh "$host" "$(remote_command find "$remote_image_dir" -maxdepth 1 -type f -name "*.bmp") | wc -l"
