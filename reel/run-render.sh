#!/bin/bash
cd /home/claude/reel
exec npx remotion render src/index.ts Reel out/jastrow-reel.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell \
  --codec=h264 --crf=18 --log=info
