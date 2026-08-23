# The reel

Ninety seconds, 1920x1080, 30 fps. Built in Remotion against the same tokens,
typefaces and engraving the landing page uses. The story now matches the
submission framing: duck-rabbit ambiguity, contract spec check, CI verdict, and
live GenLayer proof layer.

```
npm install
npx remotion studio src/index.ts          # preview and scrub
npm run render                            # writes out/jastrow-reel.mp4
```

## The audio is an edit, not the raw track

`Chart_Recorder.mp3` runs 4 minutes 13 seconds. `public/jastrow-reel.mp3` is a
36 bar cut of it made with the command in `scripts/cut-audio.sh`.

The tempo was measured rather than assumed. A spectral flux onset envelope over
the whole track, then a comb scan between 93 and 99 BPM, puts it at **95.02 BPM
with the first beat at 0.023 s**. One bar is 2.5258 s, so 36 bars is 90.93 s.

The cut takes the track's own opening (23 bars from the first beat) and its own
closing (14 bars ending at the fade), joined with a one bar equal power
crossfade. That gives the reel a sparse cold open on the number and a real
ending under the final card, rather than a hand made fade at ninety seconds.

The splice was checked before it was used: the cosine similarity between the
averaged spectra either side of the join is 0.868, against 0.898 for an
unrelated pair of points inside the same track. The join is no more of a seam
than any other two moments in the piece, which is what a harmonically static
composition buys you. Level either side differed by 4.4 dB, so the tail is
lifted 1.4 dB and the crossfade covers the rest. Output is normalised to
-16 LUFS with a true peak of -1.9 dBFS.

## Everything lands on a bar

`src/theme.ts` derives the grid from the measured tempo, and every cut in
`src/Root.tsx` is a bar index. No cut lands between two beats, and the probe
marks in scene six land one per beat rather than approximately on the beat.

| bars | seconds | scene |
| --- | --- | --- |
| 0 to 2 | 0.0 to 5.1 | the figure arrives before any claim does |
| 2 to 8 | 5.1 to 20.2 | the duck-rabbit is the failure mode |
| 8 to 11 | 20.2 to 27.8 | contract spec check and AMBIGUOUS verdict |
| 11 to 16 | 27.8 to 40.4 | one drawing / two readings becomes one input / two validator readings |
| 16 to 19 | 40.4 to 48.0 | why GenLayer is the instrument |
| 19 to 23 | 48.0 to 58.1 | five probes, one per beat |
| 23 to 27 | 58.1 to 68.2 | the failing input settles onto a detent |
| 27 to 31 | 68.2 to 78.3 | every input, worst first |
| 31 to 34 | 78.3 to 85.9 | live proof layer and receipt caveat |
| 34 to 36 | 85.9 to 90.9 | jastrow.live |

## The scale is the same arithmetic

`achievable(k, tokens)` in `src/theme.ts` is the same walk as the contract's
`_achievable_d` and the report page's. The ticks in the reel are the values the
chain can actually produce, so the reel is not illustrating the product with a
prettier fiction.

The needle uses a spring that settles rather than glides, because settling onto
a detent is the claim the scale is making. Everything else fades or wipes: a
chart recorder does not bounce.

## Numbers on screen

The readings shown are the same small demo gate used on the landing page:
`in-image=0.480`, `in-reply=0.320`, `clean=0`, `missing=0`. It is a demo of the
CI verdict flow, not a receipt-backed Bradbury measurement. The script says the
publishable report waits for terminal receipts, matching the page.

## What is in out/

`out/jastrow-reel.mp4`, 1920x1080, 30 fps, 90.99 s, 10.9 MB, h264 at crf 18
with AAC audio. `out/poster.jpg` is the final card, for anywhere that wants a
thumbnail.

Every frame was scanned for dark flashes after rendering: minimum luma across
the film is 18.0, which is the page background, so there are no black frames.
The dark runs the scan finds all sit at scene openings, where a line fades up
over a quiet bar.

One thing that scan caught and the eye would have missed: rounding each scene's
length on its own left a one frame hole at two of the ten cuts, because
`round(BAR * at) + round(BAR * len)` is not always `round(BAR * (at + len))`.
Durations are now the difference between two absolute bar positions. On a cut
this dark a single empty frame reads as a blink rather than as an edit.

## Rendering notes

Remotion downloads its own headless shell from `remotion.media` on first run.
Where that host is unavailable, point it at any Chromium already on the machine:

```
npx remotion render src/index.ts Reel out/jastrow-reel.mp4 \
  --browser-executable=/path/to/headless_shell --codec=h264 --crf=18
```

Chrome's new headless mode is not supported by Remotion's renderer, so the
binary has to be a `headless_shell` build rather than a full `chrome`.

Two practical notes from rendering this on one core. It takes about twenty
minutes, and it must be launched with `setsid` rather than `nohup`: a plain
background job dies with its parent shell when the shell is killed, taking
twenty minutes of work with it. And check that only one render is running
before walking away, because two competing for one core run six times slower
than one, which looks exactly like Remotion being slow.
