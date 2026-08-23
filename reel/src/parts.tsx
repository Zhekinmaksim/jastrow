import React from "react";
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { C, F, face, BEAT, achievable } from "./theme";

/* ---------------------------------------------------------------------------
   Motion is deliberately small: a chart recorder does not bounce. Everything
   below either fades, wipes, or snaps onto a detent, and nothing eases past
   its target.
   ------------------------------------------------------------------------ */

export const Fade: React.FC<{
  from: number;
  children: React.ReactNode;
  length?: number;
  out?: number;
  rise?: number;
  style?: React.CSSProperties;
}> = ({ from, children, length = BEAT, out, rise = 14, style }) => {
  const frame = useCurrentFrame();
  const t = frame - from;
  const opacity = interpolate(t, [0, length], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exit =
    out === undefined
      ? 1
      : interpolate(frame - out, [0, BEAT], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
  const y = interpolate(t, [0, length], [rise, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div style={{ ...style, opacity: opacity * exit, transform: `translateY(${y}px)` }}>
      {children}
    </div>
  );
};

export const Label: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({
  children,
  style,
}) => (
  <div
    style={{
      ...face(76, 600),
      fontSize: 26,
      letterSpacing: "0.2em",
      textTransform: "uppercase",
      color: C.muted,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Line: React.FC<{
  children: React.ReactNode;
  size?: number;
  color?: string;
  max?: number;
  weight?: number;
}> = ({ children, size = 58, color = C.ink, max = 26, weight = 400 }) => (
  <div
    style={{
      ...face(100, weight),
      fontSize: size,
      lineHeight: 1.28,
      color,
      maxWidth: `${max}ch`,
      letterSpacing: "-0.005em",
    }}
  >
    {children}
  </div>
);

export const Body: React.FC<{ children: React.ReactNode; size?: number; color?: string }> = ({
  children,
  size = 27,
  color = C.prose,
}) => (
  <div style={{ fontFamily: F.text, fontSize: size, lineHeight: 1.55, color, maxWidth: "46ch" }}>
    {children}
  </div>
);

/* The engraving, inverted so it reads as a plate in a dark room rather than a
   sheet of white paper dropped into the shot. */
export const Plate: React.FC<{
  src: string;
  width: number;
  rotate?: number;
  opacity?: number;
  style?: React.CSSProperties;
}> = ({ src, width, rotate = 0, opacity = 1, style }) => (
  <img
    src={src}
    alt=""
    style={{
      width,
      opacity,
      filter: "invert(1) grayscale(1) contrast(1.32)",
      mixBlendMode: "screen",
      transform: `rotate(${rotate}deg)`,
      ...style,
    }}
  />
);

/* ---------------------------------------------------------------------------
   The scale with detents. Same arithmetic as the contract: ticks only where a
   sample of this size can actually land, and the ground between them milled
   out because no reading can sit there.
   ------------------------------------------------------------------------ */

export const Scale: React.FC<{
  k: number;
  tokens: number;
  value: number | null;
  width: number;
  start: number;
  labels?: boolean;
  /* The list of readings has to fit six rows in one frame, so it draws the
     same scale at two thirds depth. The arithmetic is identical. */
  compact?: boolean;
}> = ({ k, tokens, value, width, start, labels = true, compact = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const height = compact ? 86 : 138;
  const left = 5;
  const right = width - 5;
  const baseline = compact ? 56 : 86;
  const band = compact ? 28 : 40;
  const maxMilli = Math.round((1000 * (tokens - 1)) / tokens);
  const at = (m: number) => left + (right - left) * (m / maxMilli);
  const ticks = achievable(k, tokens);

  const trackReveal = interpolate(frame - start, [0, BEAT * 1.2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tickIn = (i: number) =>
    interpolate(frame - start - BEAT * (1 + i * 0.28), [0, BEAT * 0.6], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });

  /* The needle does not glide to its value: it settles onto a detent, which is
     the whole claim the scale is making. */
  const settle = spring({
    frame: frame - start - BEAT * 2.6,
    fps,
    config: { damping: 15, mass: 0.7, stiffness: 140 },
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <defs>
        <clipPath id={`reveal-${start}`}>
          <rect x={left} y={0} width={(right - left) * trackReveal} height={height} />
        </clipPath>
        <pattern
          id={`knurl-${start}`}
          width={9}
          height={9}
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)"
        >
          <rect width={9} height={9} fill={C.milled} />
          <line x1={0} y1={0} x2={0} y2={9} stroke={C.knurl} strokeWidth={4} />
        </pattern>
      </defs>
      <g clipPath={`url(#reveal-${start})`}>
        <rect
          x={left}
          y={baseline - band}
          width={right - left}
          height={band}
          fill={`url(#knurl-${start})`}
        />
        <line
          x1={left}
          y1={baseline - band + 1}
          x2={right}
          y2={baseline - band + 1}
          stroke={C.hair}
          strokeWidth={2.6}
        />
        <line x1={left} y1={baseline} x2={right} y2={baseline} stroke={C.axis} strokeWidth={3.4} />
      </g>

      {ticks.map((m, i) => (
        <g key={m} opacity={tickIn(i)}>
          <line
            x1={at(m)}
            y1={baseline - band - 9}
            x2={at(m)}
            y2={baseline + 3}
            stroke={C.tick}
            strokeWidth={3}
          />
          {labels ? (
            <text
              x={Math.min(Math.max(at(m), left + 46), right - 46)}
              y={baseline + 42}
              textAnchor="middle"
              fill={C.tick}
              fontFamily={F.data}
              fontSize={29}
            >
              {(m / 1000).toFixed(3)}
            </text>
          ) : null}
        </g>
      ))}

      {value === null ? null : (
        <g opacity={settle > 0.02 ? 1 : 0}>
          <line
            x1={at(value)}
            y1={baseline - (compact ? 44 : 66)}
            x2={at(value)}
            y2={baseline + 5}
            stroke={C.dial}
            strokeWidth={compact ? 6 : 7}
            strokeLinecap="round"
            style={{ transform: `scaleY(${Math.min(settle, 1)})`, transformOrigin: `0 ${baseline + 5}px` }}
          />
          <polygon
            points={`${at(value) - (compact ? 10 : 13)},${baseline - (compact ? 49 : 72)} ${at(value) + (compact ? 10 : 13)},${baseline - (compact ? 49 : 72)} ${at(value)},${baseline - (compact ? 35 : 52)}`}
            fill={C.dial}
            opacity={settle}
          />
        </g>
      )}
    </svg>
  );
};

/* One mark per probe. Shape carries the meaning, not colour, so amber stays
   reserved for readings. */
export const Mark: React.FC<{
  kind: "filled" | "hollow" | "slash" | "cross";
  size?: number;
}> = ({ kind, size = 34 }) => (
  <svg width={size} height={size} viewBox="0 0 14 14" style={{ display: "block", flex: "none" }}>
    <rect
      x={0.8}
      y={0.8}
      width={12.4}
      height={12.4}
      fill={kind === "filled" ? C.mark : "none"}
      stroke={kind === "slash" ? C.tick : C.mark}
      strokeWidth={1.2}
    />
    {kind === "slash" ? (
      <line x1={3} y1={11} x2={11} y2={3} stroke={C.tick} strokeWidth={1.2} />
    ) : null}
    {kind === "cross" ? (
      <>
        <line x1={3} y1={3} x2={11} y2={11} stroke={C.mark} strokeWidth={1.2} />
        <line x1={3} y1={11} x2={11} y2={3} stroke={C.mark} strokeWidth={1.2} />
      </>
    ) : null}
  </svg>
);
