#!/usr/bin/env python3
"""Fail a build when a Jastrow report says the spec is not deployable."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def _milli(value: float) -> int:
    return int(round(value * 1000))


def _dp(value: int) -> str:
    return "{:.3f}".format(value / 1000)


def _row_name(row: dict) -> str:
    return str(row.get("label") or ("input-" + str(row.get("input_id"))))


def decide(report: dict, threshold: int, malformed_limit: int, allow_fixture: bool) -> tuple[str, int, list[str]]:
    rows = list(report.get("rows") or [])
    reasons: list[str] = []

    provenance = report.get("provenance") or {}
    if provenance.get("kind") == "fixture" and not allow_fixture:
        return "UNDECIDABLE", 2, ["report is a fixture, not a chain measurement"]

    if not rows:
        return "UNDECIDABLE", 2, ["report has no input rows"]

    unrated = [row for row in rows if not row.get("rated")]
    if unrated:
        reasons.append(
            "unrated inputs: " + ", ".join(_row_name(row) for row in unrated[:5])
        )

    malformed = [
        row for row in rows if int(row.get("malformed_milli") or 0) > malformed_limit
    ]
    if malformed:
        reasons.append(
            "malformed output above "
            + _dp(malformed_limit)
            + ": "
            + ", ".join(_row_name(row) for row in malformed[:5])
        )

    if reasons:
        return "UNDECIDABLE", 2, reasons

    split = [row for row in rows if int(row.get("d_milli") or 0) >= threshold]
    if split:
        split.sort(key=lambda row: int(row.get("d_milli") or 0), reverse=True)
        return (
            "AMBIGUOUS",
            1,
            [
                "divergence at or above "
                + _dp(threshold)
                + ": "
                + ", ".join(
                    _row_name(row) + "=" + _dp(int(row.get("d_milli") or 0))
                    for row in split[:5]
                )
            ],
        )

    return "DECIDABLE", 0, ["all rated inputs are below D " + _dp(threshold)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=pathlib.Path, help="Jastrow report JSON")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.25,
        help="Divergence threshold for AMBIGUOUS. Default: 0.25",
    )
    parser.add_argument(
        "--malformed-threshold",
        type=float,
        default=0.05,
        help="Malformed-output threshold for UNDECIDABLE. Default: 0.05",
    )
    parser.add_argument(
        "--allow-fixture",
        action="store_true",
        help="allow fixture reports; useful only for local tests, not CI",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    args = parser.parse_args()

    report = json.loads(args.report.read_text())
    verdict, code, reasons = decide(
        report,
        _milli(args.threshold),
        _milli(args.malformed_threshold),
        args.allow_fixture,
    )
    payload = {
        "verdict": verdict,
        "exit_code": code,
        "threshold_milli": _milli(args.threshold),
        "malformed_threshold_milli": _milli(args.malformed_threshold),
        "reasons": reasons,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(verdict)
        for reason in reasons:
            print("  " + reason)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
