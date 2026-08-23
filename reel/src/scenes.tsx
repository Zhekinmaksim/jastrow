import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  staticFile,
  spring,
  useVideoConfig,
} from "remotion";
import { C, F, face, BEAT, BAR, bars, beats, dp } from "./theme";
import { Fade, Label, Line, Body, Plate, Scale, Mark } from "./parts";

const PAD = 130;

const Stage: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({
  children,
  style,
}) => (
  <AbsoluteFill
    style={{
      padding: PAD,
      justifyContent: "center",
      backgroundColor: C.void,
      ...style,
    }}
  >
    {children}
  </AbsoluteFill>
);

/* --------------------------------------------------------------------------
   1. Cold open, bars 0 to 2. The figure arrives before any claim does.
   ----------------------------------------------------------------------- */

export const Open: React.FC = () => {
  const frame = useCurrentFrame();
  const plate = interpolate(frame, [beats(1), beats(5)], [0, 0.9], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const drift = interpolate(frame, [0, bars(2)], [1.06, 1.0]);
  return (
    <Stage style={{ padding: 0, justifyContent: "flex-end", overflow: "hidden" }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <Plate
          src={staticFile("jastrow-1899.webp")}
          width={1500}
          opacity={plate}
          style={{ transform: `scale(${drift})` }}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(0deg, rgba(14,17,20,.94) 0%, rgba(14,17,20,.2) 42%, rgba(14,17,20,.7) 100%)",
        }}
      />
      <div style={{ position: "absolute", left: PAD, bottom: PAD }}>
        <Fade from={beats(4)}>
          <div style={{ ...face(134, 800), fontSize: 88, textTransform: "uppercase", color: C.ink }}>
            Jastrow
          </div>
        </Fade>
      </div>
    </Stage>
  );
};

/* --------------------------------------------------------------------------
   2. The problem, bars 2 to 8. The ecosystem's own documented failure.
   ----------------------------------------------------------------------- */

export const Problem: React.FC = () => (
  <Stage>
    <AbsoluteFill style={{ padding: PAD, justifyContent: "center" }}>
      <Fade from={0} out={bars(3)}>
        <Label>Asked at the community AMA</Label>
        <div style={{ marginTop: 34 }}>
          <Line size={64} max={23}>
            Why did Rally's AI jury reject submissions that followed the campaign
            requirements?
          </Line>
        </div>
      </Fade>
    </AbsoluteFill>
    <AbsoluteFill style={{ padding: PAD, justifyContent: "center" }}>
      <Fade from={bars(3) + beats(1)}>
        <Line size={58} max={26}>
          The answer named two causes. One of them was authors who did not
          specify things properly.
        </Line>
        <div style={{ marginTop: 46 }}>
          <Fade from={bars(4) + beats(2)}>
            <Body>The example given was a hashtag with a space in the middle.</Body>
          </Fade>
        </div>
      </Fade>
    </AbsoluteFill>
  </Stage>
);

/* --------------------------------------------------------------------------
   3. The failing case, bars 8 to 11.
   ----------------------------------------------------------------------- */

export const Case: React.FC = () => {
  const frame = useCurrentFrame();
  const cut = interpolate(frame, [beats(3), beats(4.2)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <Stage>
      <Fade from={0}>
        <Label>The rule</Label>
        <div style={{ marginTop: 30, fontFamily: F.data, fontSize: 42, color: C.prose, maxWidth: "42ch", lineHeight: 1.5 }}>
          A submission qualifies if the post carries the hashtag{" "}
          <span style={{ color: C.ink }}>#GenLayer</span>.
        </div>
      </Fade>
      <div style={{ marginTop: 76 }}>
        <Fade from={beats(2)}>
          <Label>The submission</Label>
          <div
            style={{
              marginTop: 26,
              fontFamily: F.data,
              fontSize: 104,
              color: C.ink,
              letterSpacing: "-0.01em",
            }}
          >
            #<span style={{ opacity: cut, color: C.dial }}>&nbsp;</span>GenLayer
          </div>
        </Fade>
      </div>
      <Fade from={beats(6)} style={{ marginTop: 54 }}>
        <Line size={54} max={30}>
          One space. Competent judges split on it, and nobody knew until the
          appeals arrived.
        </Line>
      </Fade>
    </Stage>
  );
};

/* --------------------------------------------------------------------------
   4. The figure, bars 11 to 16. The rotation is the argument.
   ----------------------------------------------------------------------- */

export const Figure: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const turn = spring({
    frame: frame - bars(2),
    fps,
    config: { damping: 22, mass: 1.1, stiffness: 60 },
  });
  const angle = turn * 90;
  const scale = interpolate(turn, [0, 0.5, 1], [1, 0.82, 0.86]);
  return (
    <Stage style={{ padding: 0 }}>
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", paddingRight: 40 }}>
        <Plate
          src={staticFile("jastrow-1899.webp")}
          width={1000}
          rotate={angle}
          style={{ transform: `rotate(${angle}deg) scale(${scale})` }}
        />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: PAD, top: PAD, width: 760 }}>
        <Fade from={0} out={bars(2) - beats(1)}>
          <Label>Munich, 23 October 1892</Label>
          <div style={{ marginTop: 22 }}>
            <Line size={56} max={22}>
              Which animals most resemble each other?
            </Line>
          </div>
        </Fade>
        <Fade from={bars(2) + beats(2)} style={{ position: "absolute", top: 0, left: 0 }}>
          <Label>The same drawing</Label>
          <div style={{ marginTop: 22 }}>
            <Line size={56} max={20}>
              The bill is a pair of ears.
            </Line>
          </div>
        </Fade>
      </div>
      <div style={{ position: "absolute", left: PAD, bottom: PAD, width: 760 }}>
        <Fade from={bars(3) + beats(2)}>
          <Line size={46} max={28} color={C.prose}>
            The ambiguity is a property of the drawing, not a defect in the
            viewer.
          </Line>
        </Fade>
      </div>
    </Stage>
  );
};

/* --------------------------------------------------------------------------
   5. What cannot be done, bars 16 to 19.
   ----------------------------------------------------------------------- */

export const Limit: React.FC = () => (
  <Stage>
    <Fade from={0}>
      <Line size={72} max={22}>
        A contract cannot watch its own validators disagree.
      </Line>
    </Fade>
    <Fade from={bars(1)} style={{ marginTop: 44 }}>
      <Body size={35}>
        Disagreement surfaces as an appeal or a failed transaction, never as a
        value the contract can read.
      </Body>
    </Fade>
    <Fade from={bars(2)} style={{ marginTop: 44 }}>
      <Line size={48} max={34} color={C.dial}>
        So it is sampled instead. One probe, one transaction, one leader.
      </Line>
    </Fade>
  </Stage>
);

/* --------------------------------------------------------------------------
   6. The probes landing, bars 19 to 23. One mark per beat, on the beat.
   ----------------------------------------------------------------------- */

const PROBE_KINDS = ["filled", "hollow", "filled", "hollow", "hollow"] as const;
const PROBE_WORDS = ["accept", "reject", "accept", "reject", "reject"];

export const Probes: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Stage>
      <Fade from={0}>
        <Label>Five probes on one input</Label>
      </Fade>
      <div style={{ display: "flex", gap: 46, marginTop: 62, alignItems: "center", height: 170 }}>
        {PROBE_KINDS.map((kind, i) => {
          const at = beats(2 + i * 2);
          const shown = frame >= at;
          const pop = interpolate(frame - at, [0, 5], [0.5, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <div
              key={i}
              style={{
                opacity: shown ? 1 : 0,
                transform: `scale(${shown ? pop : 0.5})`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 18,
              }}
            >
              <Mark kind={kind} size={126} />
              <div style={{ fontFamily: F.data, fontSize: 27, color: C.muted }}>
                {PROBE_WORDS[i]}
              </div>
            </div>
          );
        })}
      </div>
      <Fade from={beats(11)} style={{ marginTop: 60 }}>
        <Line size={56} max={30}>
          Three said one thing. Two said the other. That spread is the
          measurement.
        </Line>
      </Fade>
    </Stage>
  );
};

/* --------------------------------------------------------------------------
   7. The scale, bars 23 to 27. The needle settles onto a detent.
   ----------------------------------------------------------------------- */

export const Reading: React.FC = () => {
  const frame = useCurrentFrame();
  const settled = frame > bars(1) + beats(3.4);
  return (
    <Stage>
      <Fade from={0}>
        <Label>Divergence on this input</Label>
      </Fade>
      <div style={{ marginTop: 40 }}>
        <Scale k={5} tokens={2} value={480} width={1660} start={beats(1)} />
      </div>
      <div
        style={{
          marginTop: 34,
          fontFamily: F.data,
          fontSize: 148,
          color: C.dial,
          letterSpacing: "-0.04em",
          opacity: settled ? 1 : 0,
        }}
      >
        {dp(480)}
      </div>
      <Fade from={bars(2)} style={{ marginTop: 30 }}>
        <Body size={34}>
          At five answers over two options, only three values are reachable at
          all. The reading sits on a detent, and the page says so rather than
          implying a precision the sample does not have.
        </Body>
      </Fade>
    </Stage>
  );
};

/* --------------------------------------------------------------------------
   8. The report, bars 27 to 31. Worst first, because that is the clause to fix.
   ----------------------------------------------------------------------- */

const ROWS = [
  { label: "in-reply", k: 4, value: 500 },
  { label: "spaced", k: 5, value: 480 },
  { label: "cased", k: 5, value: 480 },
  { label: "in-image", k: 4, value: 375 },
  { label: "plural", k: 5, value: 320 },
  { label: "clean", k: 5, value: 0 },
];

export const Report: React.FC = () => {
  const frame = useCurrentFrame();
  const mean = Math.round(
    interpolate(frame - bars(2), [0, beats(3)], [0, 307], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  return (
    <Stage style={{ justifyContent: "center" }}>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 60 }}>
        <Fade from={0}>
          <Label>Every input, worst first</Label>
          <div style={{ marginTop: 18 }}>
            <Body size={30}>
              The worst input is the clause to rewrite. Now it has a name and a
              number.
            </Body>
          </div>
        </Fade>
        <Fade from={bars(2)} style={{ textAlign: "right" }}>
          <Label style={{ textAlign: "right" }}>Mean divergence</Label>
          <div
            style={{
              fontFamily: F.data,
              fontSize: 104,
              color: C.ink,
              letterSpacing: "-0.045em",
              marginTop: 6,
              lineHeight: 1,
            }}
          >
            {dp(mean)}
          </div>
        </Fade>
      </div>
      <div style={{ marginTop: 40, display: "grid", gap: 5 }}>
        {ROWS.map((row, i) => (
          <div
            key={row.label}
            style={{
              display: "grid",
              gridTemplateColumns: "360px 1fr",
              alignItems: "center",
              gap: 30,
              background: i % 2 ? "#15181c" : C.face,
              padding: "8px 30px",
              opacity: frame >= beats(1 + i * 0.9) ? 1 : 0,
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 20 }}>
              <div style={{ ...face(92, 700), fontSize: 30, color: C.ink }}>{row.label}</div>
              <div
                style={{
                  fontFamily: F.data,
                  fontSize: 40,
                  color: row.value ? C.dial : C.muted,
                  letterSpacing: "-0.03em",
                }}
              >
                {dp(row.value)}
              </div>
            </div>
            <Scale
              k={row.k}
              tokens={2}
              value={row.value}
              width={1160}
              start={beats(1 + i * 0.9)}
              labels={false}
              compact
            />
          </div>
        ))}
      </div>
    </Stage>
  );
};

/* --------------------------------------------------------------------------
   9. What it will not claim, bars 31 to 34.
   ----------------------------------------------------------------------- */

export const Bound: React.FC = () => (
  <Stage>
    <Fade from={0}>
      <Label>What it will not claim</Label>
    </Fade>
    <Fade from={beats(1)} style={{ marginTop: 34 }}>
      <Line size={62} max={26}>
        Every rate is an upper bound on the independence of the sample, not a
        measurement of it.
      </Line>
    </Fade>
    <Fade from={bars(1) + beats(2)} style={{ marginTop: 44 }}>
      <Body size={34}>
        The runtime does not expose the leader identity, so the report says so in
        its own body rather than in a footnote somebody can crop out.
      </Body>
    </Fade>
  </Stage>
);

/* --------------------------------------------------------------------------
   10. The card, bars 34 to 36.
   ----------------------------------------------------------------------- */

export const Card: React.FC = () => {
  const frame = useCurrentFrame();
  const plate = interpolate(frame, [0, beats(3)], [0, 0.55], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const rule = interpolate(frame, [beats(2), beats(4)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <Stage style={{ padding: 0, justifyContent: "center", overflow: "hidden" }}>
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center" }}>
        <Plate
          src={staticFile("jastrow-1899.webp")}
          width={1180}
          opacity={plate}
          style={{ marginRight: -180 }}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(90deg, rgba(14,17,20,.97) 0%, rgba(14,17,20,.8) 44%, rgba(14,17,20,.1) 100%)",
        }}
      />
      <div style={{ position: "absolute", left: PAD, top: "50%", transform: "translateY(-50%)" }}>
        <Fade from={0} length={beats(1.4)}>
          <div style={{ ...face(134, 800), fontSize: 128, textTransform: "uppercase", color: C.ink }}>
            Jastrow
          </div>
        </Fade>
        <div
          style={{
            height: 2,
            background: C.edge,
            width: `${rule * 640}px`,
            margin: "30px 0 30px",
          }}
        />
        <Fade from={beats(3)}>
          <div style={{ fontFamily: F.data, fontSize: 66, color: C.dial, letterSpacing: "0.01em" }}>
            jastrow.quest
          </div>
          <div style={{ marginTop: 26 }}>
            <Body size={33} color={C.muted}>
              Measure the ambiguity before it ships, not after the appeals.
            </Body>
          </div>
        </Fade>
      </div>
    </Stage>
  );
};
