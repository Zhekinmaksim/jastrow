#!/usr/bin/env python3
"""Generate the favicon set and the social card.

Two marks, on purpose. The 1892 engraving is the page and the social card,
where it is large enough to read as two animals. At sixteen pixels it is mush,
so the favicon is a schematic redraw of the same figure in line art, which is
what the figure looks like when it is reduced to the part that carries the
ambiguity: two prongs, a head, an eye.

    python3 scripts/make_assets.py

Needs playwright, which is only a build dependency; nothing the site serves
depends on it.
"""

from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = _ROOT / "web"
ASSETS = WEB / "assets"

CASE = "#0e1114"
RECESS = "#191d21"
INK = "#f6f6f3"
MUTED = "#7d868d"
DIAL = "#f2a93b"

# The duck-rabbit reduced to what survives at sixteen pixels. Prongs left, head
# right, eye where both readings put one. The engraving itself is mush at that
# size, so the icon is line art on the same graphite the page uses.
MARK_PATH = (
    "M58 15 C80 5 107 11 114 30 C120 47 106 68 86 70 C70 72 58 63 51 52 "
    "C40 55 22 61 11 62 C4 62 4 54 11 52 "
    "C22 49 36 45 45 43 C36 39 22 34 11 31 "
    "C4 29 4 21 11 20 C24 17 41 16 50 17 C52 16 55 15 58 15 Z"
)

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" fill="{case}"/>
  <g transform="translate(2 26)">
    <path d="{path}" fill="none" stroke="{ink}" stroke-width="7"
          stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="86" cy="31" r="6" fill="{ink}"/>
  </g>
</svg>
""".format(case=CASE, ink=INK, path=MARK_PATH)


CARD_HTML = """<!DOCTYPE html>
<meta charset="utf-8">
<style>
  @font-face {{
    font-family: "Anybody";
    src: url("assets/fonts/anybody-var.woff2") format("woff2-variations");
    font-weight: 100 900;
    font-stretch: 50% 150%;
  }}
  @font-face {{
    font-family: "Spline Sans Mono";
    src: url("assets/fonts/spline-mono-var.woff2") format("woff2-variations");
    font-weight: 300 700;
  }}
  @font-face {{
    font-family: "Chivo";
    src: url("assets/fonts/chivo-var.woff2") format("woff2-variations");
    font-weight: 100 900;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; width: 1200px; height: 630px;
    background: {case}; color: {ink};
    font-family: "Chivo", sans-serif; overflow: hidden; position: relative;
  }}
  .plate {{
    position: absolute; right: -40px; top: 96px; width: 660px;
    filter: invert(1) grayscale(1) contrast(1.25);
    mix-blend-mode: screen;
  }}
  .pad {{ position: relative; padding: 52px 64px; height: 100%; display: flex; flex-direction: column; }}
  .mark {{
    font-family: "Anybody"; font-variation-settings: "wdth" 132, "wght" 800;
    font-size: 78px; letter-spacing: .015em; text-transform: uppercase; line-height: 1;
  }}
  .face {{
    font-family: "Anybody"; font-variation-settings: "wdth" 78, "wght" 600;
    font-size: 17px; letter-spacing: .22em; text-transform: uppercase; color: {muted};
  }}
  .rule {{ border-top: 1px solid #39424a; margin: 26px 0 0; }}
  .reading {{ margin-top: auto; display: flex; align-items: flex-end; gap: 56px; }}
  .value {{
    font-family: "Spline Sans Mono"; font-weight: 350; font-size: 132px;
    line-height: .84; letter-spacing: -.045em; font-variant-numeric: tabular-nums;
  }}
  .value.dial {{ color: {dial}; font-size: 64px; }}
  .lede {{ font-size: 25px; line-height: 1.35; max-width: 21ch; color: #c3c8ca; padding-bottom: 10px; }}
  .foot {{
    font-family: "Spline Sans Mono"; font-size: 17px; color: {muted};
    padding-top: 22px; margin-top: 26px; border-top: 1px solid #39424a;
    display: flex; justify-content: space-between;
  }}
</style>
<img class="plate" src="assets/jastrow-1899.webp" alt="">
<div class="pad">
  <div class="mark">Jastrow</div>
  <div class="face" style="margin-top:12px">Spec decidability gate &middot; GenLayer</div>
  <div class="rule"></div>
  <div class="reading">
    <div>
      <div class="face">Mean divergence</div>
      <div class="value">{mean}</div>
    </div>
    <div class="lede">Find the inputs that make validators split before the spec ships.</div>
  </div>
  <div class="foot">
    <span>measured before it ships</span>
    <span>not discovered through appeals</span>
  </div>
</div>
"""


def card_html() -> str:
    """The card carries the live headline, not a number typed into a template.

    A social card showing a figure the report no longer says is a small lie
    that travels further than the page does, so the number is read from the
    same report.json the page is built from.
    """
    mean = "0.000"
    report = _ROOT / "web" / "report.json"
    if report.exists():
        import json

        mean = "{:.3f}".format(json.loads(report.read_text()).get("mean_d_milli", 0) / 1000)
    return CARD_HTML.format(case=CASE, ink=INK, muted=MUTED, dial=DIAL, mean=mean)


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed, so the assets cannot be generated")
        return 1

    (WEB / "favicon.svg").write_text(FAVICON_SVG)
    print("wrote web/favicon.svg")

    icon_page = WEB / "_icon.html"
    card_page = WEB / "_card.html"
    icon_page.write_text(
        '<meta charset="utf-8"><style>*{margin:0}body{width:128px;height:128px}</style>' + FAVICON_SVG
    )
    card_page.write_text(card_html())

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            page = browser.new_page(viewport={"width": 128, "height": 128}, device_scale_factor=1)
            page.goto("file://" + str(icon_page))
            page.wait_for_timeout(400)
            for size in (32, 180, 512):
                page.set_viewport_size({"width": size, "height": size})
                page.evaluate(
                    "s => { const svg = document.querySelector('svg');"
                    "svg.setAttribute('width', s); svg.setAttribute('height', s);"
                    "document.body.style.width = s + 'px'; document.body.style.height = s + 'px'; }",
                    size,
                )
                page.wait_for_timeout(200)
                page.screenshot(path=str(ASSETS / ("favicon-" + str(size) + ".png")))
                print("wrote web/assets/favicon-" + str(size) + ".png")

            card = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
            card.goto("file://" + str(card_page))
            card.wait_for_timeout(1600)
            card.screenshot(path=str(ASSETS / "og-card.png"))
            browser.close()

    finally:
        icon_page.unlink(missing_ok=True)
        card_page.unlink(missing_ok=True)

    # A flat ground and one engraving need nowhere near truecolour, and a
    # social card is fetched by every scraper that sees a link.
    try:
        from PIL import Image

        card_path = ASSETS / "og-card.png"
        before = card_path.stat().st_size
        Image.open(card_path).convert("RGB").quantize(
            colors=96, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG
        ).save(card_path, optimize=True)
        print("wrote web/assets/og-card.png  " +
              str(round(before / 1024)) + " KB to " +
              str(round(card_path.stat().st_size / 1024)) + " KB")
    except ImportError:
        print("wrote web/assets/og-card.png  (pillow missing, left unoptimised)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
