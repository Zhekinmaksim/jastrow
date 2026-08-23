#!/usr/bin/env python3
"""Audit a published report without trusting whoever published it.

Every number a Jastrow report prints is arithmetic over the answer counts it
also prints. That means a reader who has the JSON can recompute the whole thing
and find out whether the headline agrees with the evidence underneath it. This
script does that, and it deliberately reimplements nothing: it imports the
contract and uses the contract's own functions, so what it checks is the code
that runs on chain.

    python3 scripts/check_report.py web/report.json

Exit code is zero when every check passes and one when any of them does not,
so it drops into CI as is.

What it cannot check is whether the probes happened. Provenance is a separate
question, answered by the contract address and the probe log, not by
arithmetic. The script says which of the two it is looking at.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "test"))
sys.path.insert(0, str(_ROOT / "contracts"))

import harness  # noqa: E402,F401  installs the runtime stub before the import below
import jastrow  # noqa: E402


class Audit:
    """Groups checks into named sections and remembers everything that failed."""

    def __init__(self) -> None:
        self.section: list[str] = []
        self.all: list[str] = []
        self.checks = 0

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.section.append(message)
            self.all.append(message)

    def close(self, label: str) -> None:
        print("  " + ("ok  " if not self.section else "FAIL") + "  " + label)
        for failure in self.section[:8]:
            print("        " + failure)
        if len(self.section) > 8:
            print("        and " + str(len(self.section) - 8) + " more")
        self.section = []


def parse_distribution(text: str) -> dict:
    counts = {}
    for chunk in text.split("|"):
        mark = chunk.rfind(":")
        if mark == -1:
            continue
        counts[chunk[:mark]] = int(chunk[mark + 1 :])
    return counts


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("report", help="path to a report json")
    args = parser.parse_args()

    report = json.loads(pathlib.Path(args.report).read_text())
    vocab = report.get("vocabulary", [])
    rows = report.get("rows", [])

    print()
    print("  " + str(report.get("title", "untitled")))
    provenance = report.get("provenance", {})
    kind = provenance.get("kind", "unknown")
    if kind in ("chain", "chain-receipts"):
        print("  on chain, " + str(provenance.get("network", "")) +
              ", contract " + str(provenance.get("contract", "")))
    elif kind == "fixture":
        print("  fixture. The arithmetic below is still checked, but no")
        print("  validator has been asked anything, so it proves only that the")
        print("  page and the contract agree about how to divide.")
    else:
        print("  provenance not stated, so treat every number as unverified")
    print()

    audit = Audit()

    # 1. The vocabulary is closed and does not smuggle in a reserved token.
    audit.check(len(vocab) >= jastrow.MIN_VOCAB_TOKENS, "vocabulary has fewer than two tokens")
    for token in vocab:
        audit.check(token not in jastrow.RESERVED_TOKENS, "reserved token declared: " + token)
    audit.close("vocabulary is closed and free of reserved tokens")

    # 2. Every per input number follows from that input's own answer counts.
    for row in rows:
        counts = parse_distribution(row["distribution"])
        label = row["label"]

        scored = sum(counts.get(token, 0) for token in vocab)
        total = sum(counts.values())
        audit.check(scored == row["k_scored"], label + ": k_scored disagrees with the counts")
        audit.check(total == row["k_total"], label + ": k_total disagrees with the counts")

        expected_rated = scored >= report.get("min_scored_for_rate", jastrow.MIN_SCORED_FOR_RATE)
        audit.check(bool(row["rated"]) == expected_rated,
                    label + ": rated flag disagrees with the sample size")

        expected_d = jastrow._pair_disagreement_milli([counts.get(t, 0) for t in vocab], scored)
        audit.check(row["d_milli"] == (expected_d if row["rated"] else 0),
                    label + ": D is " + str(row["d_milli"]) + ", the counts give " + str(expected_d))

        # Unsettled and out of vocabulary must never have entered D. If they
        # had, D would move when they arrived, so recomputing over the declared
        # tokens alone is the test.
        for reserved, field in (
            (jastrow.TOKEN_UNSETTLED, "unsettled_milli"),
            (jastrow.TOKEN_OUT_OF_VOCAB, "oov_milli"),
            (jastrow.TOKEN_MALFORMED, "malformed_milli"),
        ):
            expected = jastrow._div_milli(counts.get(reserved, 0), total)
            audit.check(row[field] == expected,
                        label + ": " + field + " is " + str(row[field]) + ", the counts give " + str(expected))
    audit.close("every rate follows from that input's own answer counts")

    # 3. No rate is published below the minimum sample.
    floor = report.get("min_scored_for_rate", jastrow.MIN_SCORED_FOR_RATE)
    audit.check(floor >= 3, "the minimum sample for a rate is below three")
    for row in rows:
        if row["k_scored"] < floor:
            audit.check(not row["rated"], row["label"] + ": rated on too small a sample")
            audit.check(row["d_milli"] == 0, row["label"] + ": publishes a rate below the minimum sample")
    audit.close("no rate is published below the minimum sample")

    # 4. The headline figures follow from the rows.
    rated = [r for r in rows if r["rated"]]
    if rated:
        expected_mean = sum(r["d_milli"] for r in rated) // len(rated)
        audit.check(report["mean_d_milli"] == expected_mean,
                    "mean D is " + str(report["mean_d_milli"]) + ", the rows give " + str(expected_mean))
        expected_worst = max(r["d_milli"] for r in rated)
        audit.check(report["worst_d_milli"] == expected_worst,
                    "worst D is " + str(report["worst_d_milli"]) + ", the rows give " + str(expected_worst))
        audit.check(rows[0]["rated"] and rows[0]["d_milli"] == expected_worst,
                    "the rows are not sorted worst first")
    audit.check(report.get("inputs_rated") == len(rated), "inputs_rated disagrees with the rows")
    audit.check(report.get("inputs_seen") == len(rows), "inputs_seen disagrees with the rows")
    audit.check(report.get("probes_seen") == sum(r["k_total"] for r in rows),
                "probes_seen disagrees with the rows")
    audit.close("the headline figures follow from the rows")

    # 5. The report states what bounds it rather than implying independence.
    independence = report.get("independence", {})
    audit.check(bool(independence.get("note")), "the report does not state what bounds it")
    if independence.get("leader_visibility") == "unavailable":
        audit.check(independence.get("distinct_leaders") == -1,
                    "leader identity is unavailable but distinct_leaders claims a number")
    if independence.get("leader_visibility") == "explorer":
        audit.check(isinstance(independence.get("distinct_leaders"), int),
                    "Explorer leader visibility needs a numeric distinct_leaders")
        audit.check(independence.get("distinct_leaders", 0) >= 0,
                    "distinct_leaders is negative")
        audit.check(independence.get("validator_set_size", 0) > 0,
                    "Explorer report does not state validator_set_size")
    audit.close("the report states what bounds it")

    # 6. Receipt reports carry auditable transaction evidence.
    if kind == "chain-receipts":
        evidence = report.get("evidence", [])
        audit.check(isinstance(evidence, list) and len(evidence) == report.get("probes_seen"),
                    "evidence count does not match probes_seen")
        tx_hashes = []
        leaders = set()
        statuses = {"ACCEPTED": 0, "FINALIZED": 0, "SUCCESS": 0, "UNDETERMINED": 0}
        for item in evidence:
            tx_hash = item.get("tx_hash")
            audit.check(isinstance(tx_hash, str) and tx_hash.startswith("0x") and len(tx_hash) == 66,
                        "bad tx hash in evidence")
            if isinstance(tx_hash, str):
                tx_hashes.append(tx_hash.lower())
            leader = item.get("leader")
            if isinstance(leader, str) and leader:
                leaders.add(leader.lower())
            status = str(item.get("status", "")).upper()
            if status in statuses:
                statuses[status] += 1
            audit.check(item.get("observation") is not None,
                        "evidence item is missing observation field")
        audit.check(len(tx_hashes) == len(set(tx_hashes)), "duplicate tx hash in evidence")
        audit.check(independence.get("distinct_leaders") == len(leaders),
                    "distinct_leaders disagrees with evidence")
        consensus = report.get("consensus", {})
        accepted = statuses["ACCEPTED"] + statuses["FINALIZED"] + statuses["SUCCESS"]
        audit.check(consensus.get("accepted") == accepted,
                    "accepted consensus count disagrees with evidence")
        audit.check(consensus.get("undetermined") == statuses["UNDETERMINED"],
                    "undetermined consensus count disagrees with evidence")
        expected_root = sha256_hex(canonical(evidence))
        audit.check(report.get("evidence_root") == expected_root,
                    "evidence_root disagrees with evidence")
        if report.get("report_hash"):
            without_hash = {k: v for k, v in report.items() if k != "report_hash"}
            audit.check(report.get("report_hash") == sha256_hex(canonical(without_hash)),
                        "report_hash disagrees with report body")
    audit.close("receipt evidence is internally consistent")

    print()
    print("  " + str(audit.checks - len(audit.all)) + "/" + str(audit.checks) + " checks passed")
    if audit.all:
        print("  This report does not add up. Do not publish it.")
    print()
    return 1 if audit.all else 0


if __name__ == "__main__":
    raise SystemExit(main())
