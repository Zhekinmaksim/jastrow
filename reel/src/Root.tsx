import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, Composition } from "remotion";
import { C, DURATION, FPS, bars, fontCss } from "./theme";
import { Open, Problem, Case, Figure, Limit, Probes, Reading, Report, Bound, Card } from "./scenes";

/* Every scene starts on a bar so no cut lands between two beats. The numbers
   below are bar indices into a 36 bar edit at 95.02 BPM. */
const CUTS: { at: number; length: number; Scene: React.FC }[] = [
  { at: 0, length: 2, Scene: Open },
  { at: 2, length: 6, Scene: Problem },
  { at: 8, length: 3, Scene: Case },
  { at: 11, length: 5, Scene: Figure },
  { at: 16, length: 3, Scene: Limit },
  { at: 19, length: 4, Scene: Probes },
  { at: 23, length: 4, Scene: Reading },
  { at: 27, length: 4, Scene: Report },
  { at: 31, length: 3, Scene: Bound },
  { at: 34, length: 2, Scene: Card },
];

export const Reel: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: C.void }}>
    <style dangerouslySetInnerHTML={{ __html: fontCss }} />
    <Audio src={staticFile("jastrow-reel.mp3")} />
    {/* Durations are the difference between two absolute bar positions, not a
        separately rounded length. Rounding each length on its own leaves a one
        frame hole at some boundaries, which reads as a blink to empty on a cut
        this dark. */}
    {CUTS.map(({ at, length, Scene }) => (
      <Sequence
        key={at}
        from={bars(at)}
        durationInFrames={bars(at + length) - bars(at)}
      >
        <Scene />
      </Sequence>
    ))}
    {/* A little tooth, so the dark is a surface rather than a fill. Same trick
        the report page uses. */}
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        opacity: 0.5,
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.045'/%3E%3C/svg%3E\")",
      }}
    />
  </AbsoluteFill>
);

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    durationInFrames={DURATION}
    fps={FPS}
    width={1920}
    height={1080}
  />
);
