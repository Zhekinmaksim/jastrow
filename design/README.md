# Design

`Jastrow Landing.dc.html` and `jastrow-landing-standalone.html` are an earlier
Claude Design export, kept for provenance. Neither is deployed and neither is
what the page looks like now.

That export set the page as an 1892 magazine: paper ground, Bodoni masthead,
double rules, the engraving hanging as a framed plate. It was good, and it was
also the same room as AgentQuorum, which is already white paper, a serif
display, monospace labels, hairline rules and one dark red accent. Two projects
by the same person cannot both be the editorial one, so this was rebuilt.

## What it is now

An instrument case rather than a printed page. The first cut of this direction
came back reading pale, and the diagnosis had four parts, three of which the
taste skill names outright.

**The value range was compressed.** Every surface sat inside five percent of
the luminance range, so nothing had an edge to catch on. The page now has three
real depths: the room at `#0e1114`, the faceplate raised out of it at `#191d21`
with a light top edge and a dark foot, and the scale track milled below both at
`#08090b`. Ink to ground went from 12.8:1 to 17.5:1.

**Every section was the same shape.** Label, hairline, left column, four times
over. There are now six layout families: a split hero, a divided figures strip,
the readings list, a large statement over two columns of body, a pair of
plates, and stacked disclosures.

**Tracked-caps micro-labels sat above everything.** The skill caps these at one
per three sections, and there were seven. Section headings are now plain
headings at real size. The three that remain label numbers rather than
sections, which is a different job: "0.500" with no label above it is not a
reading, it is a decoration.

**The long list had a hairline under every row**, which the skill calls the
worst default for a list of more than five items. Rows are now separated by
alternating panel bands and by the milled track itself.

**The engraving was below the fold.** It is the thesis of the whole project, so
it now fills the right half of the hero at real size, inverted to white line on
the milled ground.

**One dial colour.** Amber at `#f2a93b` on the needle, the worst reading, the
open disclosure and the provenance rule. Nowhere else, so the colour means
"this is a measurement" rather than "this is important".

## What the page draws from the data

The report carries more than a number per input, and a page that prints only
the number throws the rest away. Three elements were added because the data was
already there:

**A tally strip under every reading.** One mark per probe, in the order the
vocabulary was declared: a filled square for the first answer, hollow for the
second, slashed for unsettled, crossed for a reply outside the vocabulary. The
shapes carry the meaning rather than colour, so the strip survives being
printed and amber stays reserved for readings. Five answers and fifty answers
read identically in a sentence; they do not read identically here.

**An axis in the hero** with the mean and the worst marked on it. Deliberately
without detents: a mean is derived from rows with different sample sizes, so no
single set of reachable values applies to it. Saying that with the absence of
ticks is more honest than printing ticks that do not apply.

**A resolution figure**, "what another probe would buy", showing the reachable
values at k of 3, 5, 7 and 9 with the current sample marked. `resolution_at_
smallest_sample` was sitting unused in the report JSON. The figure makes the
project's own argument visible instead of only stated: doubling the sample
roughly halves the gap between detents and doubles the bill.

## The scale

The element that carries the argument rather than the styling.

Under each input, the axis is not a bar. At five scored answers over two
tokens, D can only be 0.000, 0.320 or 0.480, so the axis carries ticks at
exactly those values and mills out the ground between them as unreachable, and
it stops at `1 - 1/n` rather than at one. A continuous bar would imply a
resolution the sample does not have, which is the quietest way for an
instrument to lie. The detents are recomputed per row, so a row with k = 4
shows a different set from a row with k = 5.

The floor is knurled rather than flat. A plain dark bar reads as a progress
track, and the whole point of that ground is that no measurement can land on
it.

`scripts/check_page_math.py` runs the page's own JavaScript under node against
the contract over every sample and vocabulary size, so the ticks drawn here are
provably the values the chain can produce.

## Two things the export had wrong

**The rabbit was rotated the wrong way.** Counterclockwise points the ears at
the floor and reads as neither animal. Ninety degrees clockwise is the rotation
that turns the bill into a pair of ears, so Plate 1b now shows the second
reading it claims to show.

**The report was hardcoded.** The page reads
`<script type="application/json" id="report-data">`, which
`scripts/embed_report.py` writes into, so a real measurement replaces the
fixture without touching the markup.

## Files

`web/index.html` is what gets deployed and keeps its assets as siblings so a
browser caches them once. `web/jastrow-standalone.html`, built by `make
bundle`, is the same page with the engraving and the fonts inlined, for handing
to a person rather than to a server.

The engraving and the font licences are in NOTICE.md.
