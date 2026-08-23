#!/usr/bin/env python3
"""Produce a layout fixture for the report page, and label it as one.

The page has to be built before the contract is deployed, and a page needs
data to be built against. This script drives the real contract through the
off-chain harness with an invented distribution written out in plain sight
below, and stamps the result with provenance kind "fixture".

The page reads that stamp and shows a warning band across the top. Nothing in
this file has been near a validator, and the page says so in its own body
rather than in a comment nobody reads. After a real run, replace it:

    python3 cli/jastrow.py report 0 --snapshot --json web/report.json
    python3 scripts/embed_report.py web/report.json

The arithmetic is the contract's own, so the shapes the page is built against
are exactly the shapes it will receive from the chain.
"""

from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "test"))
sys.path.insert(0, str(_ROOT / "contracts"))

from harness import Address, Bench, answer_json  # noqa: E402

AUTHOR = Address("0x" + "a1" * 20)

# Invented answers. This is the only invented thing in the repository and it
# is confined to this table on purpose.
INVENTED = {
    "clean": ["ACCEPT"] * 5,
    "missing": ["REJECT"] * 5,
    "spaced": ["ACCEPT", "ACCEPT", "REJECT", "REJECT", "REJECT"],
    "cased": ["ACCEPT", "ACCEPT", "ACCEPT", "REJECT", "REJECT"],
    "in-image": ["ACCEPT", "REJECT", "REJECT", "REJECT", "UNSETTLED"],
    "in-reply": ["ACCEPT", "ACCEPT", "REJECT", "REJECT", "UNSETTLED"],
    "plural": ["ACCEPT", "REJECT", "REJECT", "REJECT", "REJECT"],
    "quoted": ["ACCEPT", "REJECT", "UNSETTLED", "UNSETTLED", "UNSETTLED"],
}


def main() -> int:
    battery = json.loads((_ROOT / "calibration" / "battery.json").read_text())

    bench = Bench()
    spec_id = bench.by(AUTHOR).register_spec(
        battery["title"], battery["question"], battery["vocabulary"], battery["probe_budget"]
    )
    for item in battery["inputs"]:
        input_id = bench.by(AUTHOR).add_input(spec_id, item["label"], item["payload"])
        for answer in INVENTED[item["label"]]:
            bench.script(answer_json(answer))
            bench.by(AUTHOR).probe(spec_id, input_id)

    report = bench.by(AUTHOR).compute_report(spec_id)
    report["provenance"] = {
        "kind": "fixture",
        "source": "scripts/fixture.py, off-chain harness, invented answers",
        "note": (
            "No validator has been asked anything. These numbers exist so the "
            "page could be built before the contract was deployed."
        ),
    }
    report["question"] = battery["question"]
    report["equivalence_principle"] = bench.c.get_equivalence_principle()
    report["prompt_example"] = bench.c.get_prompt(spec_id, 2)

    out = _ROOT / "web" / "report.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("wrote " + str(out))
    for row in report["rows"]:
        reading = "{:.3f}".format(row["d_milli"] / 1000.0) if row["rated"] else "  -  "
        print("  " + row["label"].ljust(12) + " D " + reading + "   " + row["distribution"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
