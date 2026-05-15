#!/usr/bin/env bash
set -euo pipefail

host="${1:-${PHOTOPAINTER_HOST:?Set PHOTOPAINTER_HOST or pass a host as the first argument}}"
remote_image_dir="${PHOTOPAINTER_REMOTE_IMAGE_DIR:?Set PHOTOPAINTER_REMOTE_IMAGE_DIR}"
remote_python="${PHOTOPAINTER_REMOTE_PYTHON:?Set PHOTOPAINTER_REMOTE_PYTHON}"
remote_script_dir="${PHOTOPAINTER_REMOTE_SCRIPT_DIR:?Set PHOTOPAINTER_REMOTE_SCRIPT_DIR}"
remote_display_script="$remote_script_dir/photopainter-display-image.py"

printf -v remote_env_command \
  'PHOTOPAINTER_REMOTE_IMAGE_DIR=%q PHOTOPAINTER_REMOTE_PYTHON=%q PHOTOPAINTER_REMOTE_DISPLAY_SCRIPT=%q bash -s' \
  "$remote_image_dir" \
  "$remote_python" \
  "$remote_display_script"

ssh "$host" \
  "$remote_env_command" <<'REMOTE'
set -euo pipefail

image_dir="$PHOTOPAINTER_REMOTE_IMAGE_DIR"
state_file="$image_dir/.photopainter-state.json"

if [[ ! -f "$state_file" ]]; then
  echo "Missing state file: $state_file" >&2
  exit 1
fi

image_name=$("$PHOTOPAINTER_REMOTE_PYTHON" -c '
import json
import sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text())["last_image"])
' "$state_file")
image_path="$image_dir/$image_name"
if [[ ! -f "$image_path" ]]; then
  echo "State points at missing image: $image_path" >&2
  exit 1
fi

echo "Displaying current state image: $image_path"
/usr/bin/flock -n /tmp/photopainter-hokusai.lock \
  "$PHOTOPAINTER_REMOTE_PYTHON" \
  "$PHOTOPAINTER_REMOTE_DISPLAY_SCRIPT" \
  "$image_path"
cat "$state_file"
REMOTE
