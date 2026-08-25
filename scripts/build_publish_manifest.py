#!/usr/bin/env python3
"""Build a clean publish manifest from receipts that are already cached.

Bradbury's Explorer API can intermittently fail to return a receipt that it
returned in an earlier request. The publish report should not be built from
those transient failures, and it also should not count replacement transactions
on top of broken originals.

This script takes one or more JSONL manifests, keeps only transactions whose
terminal receipt is present in the collector cache, and writes exactly k rows
per input label. If any label is still short, it exits non-zero and leaves the
output untouched.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


TERMINAL_STATUSES = {"ACCEPTED", "FINALIZED", "UNDETERMINED", "SUCCESS"}


def _load_jsonl(path: pathlib.Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(str(path) + ":" + str(line_no) + ": " + str(exc))
    return rows


def _receipt_status(receipt: dict) -> str:
    return str(receipt.get("status") or receipt.get("status_name") or "").upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("manifests", nargs="+", type=pathlib.Path)
    parser.add_argument("--cache", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    cache = json.loads(args.cache.read_text())
    receipts = cache.get("receipts") or {}
    if not isinstance(receipts, dict):
        raise SystemExit("cache has no receipts object")

    by_hash = {}
    for manifest in args.manifests:
        for row in _load_jsonl(manifest):
            tx_hash = str(row.get("tx_hash", "")).lower()
            if not tx_hash or tx_hash in by_hash:
                continue
            receipt = receipts.get(row.get("tx_hash")) or receipts.get(tx_hash)
            if not isinstance(receipt, dict):
                continue
            if _receipt_status(receipt) not in TERMINAL_STATUSES:
                continue
            by_hash[tx_hash] = row

    groups: dict[str, list[dict]] = {}
    for row in by_hash.values():
        groups.setdefault(str(row["label"]), []).append(row)

    selected = []
    short = []
    for label in sorted(groups, key=lambda name: min(int(r["input_id"]) for r in groups[name])):
        rows = sorted(
            groups[label],
            key=lambda row: (
                int(row["input_id"]),
                int(row.get("round", 0)),
                int(row.get("submitted_at_unix", 0)),
                str(row["tx_hash"]),
            ),
        )
        if len(rows) < args.k:
            short.append((label, len(rows)))
            continue
        selected.extend(rows[: args.k])

    if short:
        for label, count in short:
            print(label + " has " + str(count) + "/" + str(args.k) + " terminal cached receipts", file=sys.stderr)
        return 2

    selected.sort(key=lambda row: (int(row["input_id"]), int(row.get("round", 0)), str(row["tx_hash"])))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in selected))
    print("wrote " + str(args.out) + " with " + str(len(selected)) + " rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
