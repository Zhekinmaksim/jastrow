#!/usr/bin/env python3
"""Check that the page's arithmetic agrees with the contract's, exhaustively.

The report page recomputes the detent ticks in JavaScript, because it has to
draw them and cannot call a Python function to do it. That is a second
implementation of the contract's `_achievable_d` and `_pair_disagreement_milli`,
and a second implementation is a second chance to be wrong. If the two ever
drift, the page would draw a scale whose ticks are not the values the chain can
actually produce, which is exactly the kind of quiet lie the whole project is
built to avoid.

So the JavaScript is extracted from the page as it ships, run under node, and
compared against the contract over every sample size and vocabulary size the
page can be handed.

    python3 scripts/check_page_math.py

Needs node on the path. Exit code is zero when the two agree.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "test"))
sys.path.insert(0, str(_ROOT / "contracts"))

import harness  # noqa: E402,F401
import jastrow  # noqa: E402

PAGE = _ROOT / "web" / "index.html"

MAX_K = 12
MAX_TOKENS = 6


def extract(name: str) -> str:
    """Pull one function out of the page source, brace matched.

    Reading the shipped file rather than a copy is the point: a copy would
    agree with the contract forever while the page quietly drifted.
    """
    source = PAGE.read_text()
    start = source.index("function " + name + "(")
    depth = 0
    for i in range(source.index("{", start), len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[start : i + 1]
    raise SystemExit("could not find the end of " + name + " in the page")


def main() -> int:
    script = "\n".join([
        extract("dMilli"),
        extract("achievable"),
        "var out = {};",
        "for (var t = 2; t <= " + str(MAX_TOKENS) + "; t++) {",
        "  for (var k = 1; k <= " + str(MAX_K) + "; k++) {",
        "    out[t + ':' + k] = achievable(k, t);",
        "  }",
        "}",
        "console.log(JSON.stringify(out));",
    ])

    try:
        result = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, timeout=180
        )
    except FileNotFoundError:
        print("node is not on the path, so the page arithmetic cannot be checked")
        return 1
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return 1

    from_page = json.loads(result.stdout)

    mismatches = []
    compared = 0
    for tokens in range(2, MAX_TOKENS + 1):
        for k in range(1, MAX_K + 1):
            compared += 1
            expected = jastrow._achievable_d(k, tokens)
            actual = from_page[str(tokens) + ":" + str(k)]
            if expected != actual:
                mismatches.append(
                    "tokens " + str(tokens) + ", k " + str(k) +
                    ": contract " + str(expected) + ", page " + str(actual)
                )

    print()
    print("  compared " + str(compared) + " sample and vocabulary sizes")
    if mismatches:
        print("  FAIL  the page draws ticks the contract would not produce")
        for line in mismatches[:10]:
            print("        " + line)
        print()
        return 1
    print("  ok    the page draws exactly the values the contract can produce")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
