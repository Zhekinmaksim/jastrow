#!/usr/bin/env python3
"""Embed a report into web/index.html so the page is one self-contained file.

    python3 cli/jastrow.py report 0 --snapshot --json web/report.json
    python3 scripts/embed_report.py web/report.json \
        --contract 0xabc... --network "GenLayer Bradbury testnet"

Passing --contract stamps the report with provenance kind "chain", which is
what turns off the warning band on the page. Without it the stamp is left
alone, so a fixture stays visibly a fixture.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = _ROOT / "web" / "index.html"
OPEN_TAG = '<script type="application/json" id="report-data">'
CLOSE_TAG = "</script>"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("report", help="path to a report json")
    parser.add_argument("--contract", help="deployed contract address")
    parser.add_argument("--live-contract", help="contract address used by the live frontend panel")
    parser.add_argument("--network", default="GenLayer Bradbury testnet")
    parser.add_argument(
        "--site",
        help="site url, e.g. https://jastrow.xyz. Makes the social card tags "
             "absolute, which most scrapers require.",
    )
    parser.add_argument("--page", default=str(PAGE))
    args = parser.parse_args()

    report = json.loads(pathlib.Path(args.report).read_text())
    if args.contract:
        provenance = report.get("provenance", {})
        if not isinstance(provenance, dict):
            provenance = {}
        provenance["kind"] = (
            "chain-receipts"
            if provenance.get("kind") == "chain-receipts"
            else "chain"
        )
        provenance["contract"] = args.contract
        provenance["network"] = args.network
        provenance["taken_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        report["provenance"] = provenance
    if args.live_contract:
        report["live_contract"] = args.live_contract

    page_path = pathlib.Path(args.page)
    page = page_path.read_text()

    if args.site:
        base = args.site.rstrip("/") + "/"
        page = page.replace(
            '<meta property="og:image" content="assets/og-card.png">',
            '<meta property="og:url" content="' + base + '">\n'
            '<meta property="og:image" content="' + base + 'assets/og-card.png">',
        )
        page = page.replace(
            '<meta property="og:image" content="' + base + 'assets/og-card.png">\n'
            '<meta property="og:image" content="' + base + 'assets/og-card.png">',
            '<meta property="og:image" content="' + base + 'assets/og-card.png">',
        )
    start = page.index(OPEN_TAG) + len(OPEN_TAG)
    end = page.index(CLOSE_TAG, start)
    body = "\n" + json.dumps(report, indent=2, sort_keys=True) + "\n"
    page_path.write_text(page[:start] + body + page[end:])

    kind = report.get("provenance", {}).get("kind", "unknown")
    print("embedded " + args.report + " into " + str(page_path) + " as provenance " + kind)
    if args.site:
        print("social card tags now point at " + args.site.rstrip("/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
