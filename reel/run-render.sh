#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

args=(src/index.ts Reel out/jastrow-reel.mp4 --codec=h264 --crf=18 --log=info)

if [[ -n "${REMOTION_BROWSER_EXECUTABLE:-}" ]]; then
  args+=(--browser-executable="$REMOTION_BROWSER_EXECUTABLE")
fi

exec npx remotion render "${args[@]}"
