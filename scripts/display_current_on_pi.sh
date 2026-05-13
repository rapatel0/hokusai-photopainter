#!/usr/bin/env bash
set -euo pipefail

host="${1:-${PHOTOPAINTER_HOST:-pi-window}}"

ssh "$host" 'set -euo pipefail
image_dir="$HOME/Pictures/hokusai-photopainter"
state_file="$image_dir/.photopainter-state.json"

if [[ ! -f "$state_file" ]]; then
  echo "Missing state file: $state_file" >&2
  exit 1
fi

image_name=$("$HOME/photopainter-venv/bin/python" -c '"'"'
import json
import sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text())["last_image"])
'"'"' "$state_file")
image_path="$image_dir/$image_name"
if [[ ! -f "$image_path" ]]; then
  echo "State points at missing image: $image_path" >&2
  exit 1
fi

echo "Displaying current state image: $image_path"
/usr/bin/flock -n /tmp/photopainter-hokusai.lock \
  "$HOME/photopainter-venv/bin/python" \
  "$HOME/photopainter-display-image.py" \
  "$image_path"
cat "$state_file"
'
