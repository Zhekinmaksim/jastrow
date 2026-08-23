#!/usr/bin/env python3
"""Register a battery spec and inputs without submitting probes."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from types import SimpleNamespace

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "cli"))

import jastrow as cli  # noqa: E402


def _args(args) -> SimpleNamespace:
    return SimpleNamespace(
        address=args.address,
        rpc=args.rpc,
        print_cmd=args.print_cmd,
        dry_run=args.dry_run,
        account=args.account,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("file", type=pathlib.Path)
    parser.add_argument("--address")
    parser.add_argument("--rpc")
    parser.add_argument("--account")
    parser.add_argument("--print", dest="print_cmd", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    battery = json.loads(args.file.read_text())
    base = _args(args)
    if args.account:
        cli.apply_account(base)

    result = cli.write(
        base,
        "register_spec",
        battery["title"],
        battery["question"],
        battery["vocabulary"],
        battery.get("probe_budget", 100),
    )
    spec_id = result if isinstance(result, int) else None
    if spec_id is None and isinstance(result, dict):
        spec_id = result.get("spec_id")
    if spec_id is None:
        spec_id = 0 if args.dry_run else None
    if spec_id is None:
        raise SystemExit("could not read spec id from register_spec result")

    print("spec " + str(spec_id))
    for item in battery["inputs"]:
        print("input " + item["label"])
        cli.write(base, "add_input", spec_id, item["label"], item["payload"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
