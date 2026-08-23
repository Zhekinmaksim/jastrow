import { staticFile } from "remotion";

/* The track was measured, not assumed: 95.02 BPM, first beat at 0.023 s, and
   the edit is exactly 36 bars long. Everything in the reel is placed in bars
   so a cut never lands between two beats. */
export const BPM = 95.02;
export const FPS = 30;
export const BEAT = (60 / BPM) * FPS; // 18.943 frames
export const BAR = BEAT * 4; // 75.774 frames
export const TOTAL_BARS = 36;
export const DURATION = Math.round(BAR * TOTAL_BARS); // 2728 frames, 90.93 s

export const bars = (n: number) => Math.round(BAR * n);
export const beats = (n: number) => Math.round(BEAT * n);

/* The same tokens the report page uses. The reel and the site have to look
   like the same instrument or the reel is advertising something else. */
export const C = {
  void: "#0e1114",
  face: "#191d21",
  milled: "#08090b",
  hair: "#262c32",
  edge: "#39424a",
  ink: "#f6f6f3",
  prose: "#b9c0c4",
  muted: "#7d868d",
  dial: "#f2a93b",
  mark: "#c9cfd3",
  tick: "#a4adb4",
  axis: "#6c757c",
  knurl: "#1a2026",
};

export const F = {
  sans: '"Anybody", system-ui, sans-serif',
  text: '"Chivo", system-ui, sans-serif',
  data: '"Spline Sans Mono", ui-monospace, monospace',
};

export const face = (wdth: number, wght: number) => ({
  fontFamily: F.sans,
  fontVariationSettings: `"wdth" ${wdth}, "wght" ${wght}`,
});

export const fontCss = `
@font-face {
  font-family: "Anybody";
  src: url("${staticFile("fonts/anybody-var.woff2")}") format("woff2-variations");
  font-weight: 100 900;
  font-stretch: 50% 150%;
}
@font-face {
  font-family: "Chivo";
  src: url("${staticFile("fonts/chivo-var.woff2")}") format("woff2-variations");
  font-weight: 100 900;
  font-style: normal;
}
@font-face {
  font-family: "Chivo";
  src: url("${staticFile("fonts/chivo-var-italic.woff2")}") format("woff2-variations");
  font-weight: 100 900;
  font-style: italic;
}
@font-face {
  font-family: "Spline Sans Mono";
  src: url("${staticFile("fonts/spline-mono-var.woff2")}") format("woff2-variations");
  font-weight: 300 700;
}
`;

/* Same walk as the contract's _achievable_d and the report page's. Every value
   D can take at this sample size over this many answers. */
export const achievable = (k: number, tokens: number): number[] => {
  const seen: Record<number, true> = {};
  const walk = (remaining: number, slots: number, parts: number[]) => {
    if (slots === 0) {
      if (remaining === 0) {
        const squares = parts.reduce((sum, c) => sum + c * c, 0);
        seen[Math.round((1000 * (k * k - squares)) / (k * k))] = true;
      }
      return;
    }
    for (let take = remaining; take >= 0; take--) {
      walk(remaining - take, slots - 1, [...parts, take]);
    }
  };
  walk(k, tokens, []);
  return Object.keys(seen)
    .map(Number)
    .sort((a, b) => a - b);
};

export const dp = (milli: number) => (milli / 1000).toFixed(3);
