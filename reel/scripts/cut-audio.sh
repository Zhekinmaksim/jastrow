#!/usr/bin/env bash
# Rebuild public/jastrow-reel.mp3 from the full track.
#
# 95.02 BPM measured, first beat at 0.023 s, one bar 2.525784 s.
# Segment A: 23 bars from the first beat, the track's own opening.
# Segment B: 14 bars ending at the fade, the track's own closing.
# Joined with a one bar equal power crossfade, tail lifted 1.4 dB to close a
# 4.4 dB level step. 36 bars, 90.93 s.
set -euo pipefail

SRC="${1:-Chart_Recorder.mp3}"
OUT="${2:-public/jastrow-reel.mp3}"

A_START=0.023
A_LEN=58.093
B_START=217.2404
B_LEN=35.361
XF=2.525784

ffmpeg -i "$SRC" -i "$SRC" -filter_complex "\
[0:a]atrim=start=$A_START:duration=$A_LEN,asetpts=PTS-STARTPTS[a];\
[1:a]atrim=start=$B_START:duration=$B_LEN,asetpts=PTS-STARTPTS,volume=1.18[b];\
[a][b]acrossfade=d=$XF:c1=tri:c2=tri[x];\
[x]afade=t=out:st=88.0:d=2.93,loudnorm=I=-16:TP=-1.5:LRA=11[out]" \
  -map "[out]" -c:a libmp3lame -b:a 192k -ar 48000 "$OUT" -y

ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
