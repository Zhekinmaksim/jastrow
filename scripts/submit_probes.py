#!/usr/bin/env python3
"""Submit probe transactions without waiting for finalization.

The official CLI waits for receipts, which is the wrong unit for a 40-50 probe
measurement on Bradbury. This script reads the transaction hash as soon as the
CLI prints it, stores the probe metadata in a JSONL manifest, then stops the
local polling process. The chain transaction continues independently.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from types import SimpleNamespace

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "cli"))

import jastrow as cli  # noqa: E402


TX_RE = re.compile(r"0x[0-9a-fA-F]{64}")


def _load_manifest(path: pathlib.Path) -> set[str]:
    seen: set[str] = set()
    if not path.exists():
        return seen
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        tx_hash = row.get("tx_hash")
        if isinstance(tx_hash, str):
            seen.add(tx_hash.lower())
    return seen


def _append_jsonl(path: pathlib.Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _dummy_args(args) -> SimpleNamespace:
    return SimpleNamespace(
        address=args.address,
        rpc=args.rpc,
        print_cmd=False,
        dry_run=False,
        account=args.account,
    )


def _fetch_inputs(args) -> list[dict]:
    parsed = cli.call(_dummy_args(args), "get_inputs", args.spec, 0, 100)
    if not isinstance(parsed, dict):
        raise SystemExit("could not read get_inputs result")
    items = parsed.get("items", [])
    if args.input:
        items = [item for item in items if item.get("label") == args.input]
    if not items:
        raise SystemExit("no inputs matched")
    return items


def _submit_once(args, input_id: int, label: str, round_index: int) -> dict:
    command = [
        "genlayer",
        "write",
        args.address,
        "probe",
        "--args",
        str(args.spec),
        str(input_id),
    ]
    if args.rpc:
        command += ["--rpc", args.rpc]

    env = os.environ.copy()
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    combined = ""
    deadline = time.time() + args.hash_timeout
    tx_hash = ""
    while time.time() < deadline:
        assert proc.stdout is not None
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            time.sleep(0.1)
            continue
        combined += line
        match = TX_RE.search(line)
        if match:
            tx_hash = match.group(0)
            break

    if tx_hash:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        return {
            "tx_hash": tx_hash,
            "spec_id": int(args.spec),
            "input_id": int(input_id),
            "label": label,
            "round": int(round_index),
            "submitted_at_unix": int(time.time()),
        }

    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    raise RuntimeError("no tx hash printed for input " + label + ":\n" + combined[-2000:])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--address", default=os.environ.get("JASTROW_ADDRESS"))
    parser.add_argument("--rpc")
    parser.add_argument("--account")
    parser.add_argument("--spec", type=int, required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--input")
    parser.add_argument("--manifest", default="runs/probes.jsonl")
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--hash-timeout", type=float, default=90.0)
    args = parser.parse_args()

    if not args.address:
        args.address = cli.load_state().get("address")
    if not args.address:
        raise SystemExit("pass --address or deploy first")
    if args.account:
        cli.apply_account(_dummy_args(args))

    manifest = pathlib.Path(args.manifest)
    seen = _load_manifest(manifest)
    inputs = _fetch_inputs(args)
    total = len(inputs) * args.k
    print("submitting " + str(total) + " probes; hashes go to " + str(manifest))

    done = 0
    for round_index in range(1, args.k + 1):
        for item in inputs:
            done += 1
            row = _submit_once(args, int(item["input_id"]), str(item["label"]), round_index)
            if row["tx_hash"].lower() not in seen:
                _append_jsonl(manifest, row)
                seen.add(row["tx_hash"].lower())
            print(
                str(done)
                + "/"
                + str(total)
                + " "
                + row["label"]
                + " r"
                + str(round_index)
                + " "
                + row["tx_hash"]
            )
            if args.delay:
                time.sleep(args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
