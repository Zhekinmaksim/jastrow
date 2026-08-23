#!/usr/bin/env python3
"""jastrow - a thin wrapper around the official genlayer CLI.

Every command here resolves to one or more `genlayer call` / `genlayer write`
invocations. Nothing is hidden: `--print` shows the exact command before it
runs, and `--dry-run` shows it instead of running it, so anyone reproducing a
published measurement can see precisely what was sent.

    jastrow deploy
    jastrow new "Campaign rule v3" --question-file q.txt --vocab ACCEPT,REJECT
    jastrow add 0 --label spaced --payload-file cases/spaced.txt
    jastrow probe 0 --k 5
    jastrow report 0 --worst 5
    jastrow battery ../calibration/battery.json --k 5

State lives in .jastrow.json next to the working directory, so the contract
address does not have to be retyped.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import re
import subprocess
import sys
import time

STATE_FILE = pathlib.Path(os.environ.get("JASTROW_STATE", ".jastrow.json"))
CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[1] / "contracts" / "jastrow.py"

RESERVED = ("UNSETTLED", "OUT_OF_VOCAB", "MALFORMED")


# ---------------------------------------------------------------------------
# State and process plumbing
# ---------------------------------------------------------------------------


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def resolve_address(args) -> str:
    address = args.address or os.environ.get("JASTROW_ADDRESS") or load_state().get("address")
    if not address:
        die("no contract address. Run `jastrow deploy` or pass --address.")
    return address


def die(message: str):
    print("jastrow: " + message, file=sys.stderr)
    raise SystemExit(2)


def run_genlayer(args, verb: str, tail: list) -> str:
    command = ["genlayer", verb] + tail
    if args.rpc:
        command += ["--rpc", args.rpc]

    if args.print_cmd or args.dry_run:
        print("  $ " + " ".join(quote(c) for c in command))
    if args.dry_run:
        return ""

    result = None
    for attempt in range(6):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            if re.search(
                r"(?:status_name:\s*'UNDETERMINED'|"
                r"txExecutionResultName:\s*'FINISHED_WITH_ERROR')",
                result.stdout,
            ):
                sys.stderr.write(result.stdout)
                die("genlayer reported a non-settling transaction")
            return result.stdout
        combined = result.stdout + result.stderr
        rate_limited = "-32005" in combined or "node is at capacity" in combined
        if not rate_limited or attempt == 5:
            break
        match = re.search(r"retry in ~?(\d+)ms", combined)
        suggested = (int(match.group(1)) / 1000.0) if match else 0.0
        delay = max(suggested + 0.25, 0.5 * (2**attempt))
        print(
            "jastrow: Bradbury is at capacity; retrying in "
            + "{:.2f}".format(delay)
            + "s",
            file=sys.stderr,
        )
        time.sleep(delay)
    assert result is not None
    sys.stderr.write(result.stdout)
    sys.stderr.write(result.stderr)
    die("genlayer " + verb + " failed with code " + str(result.returncode))


def quote(part: str) -> str:
    if part == "" or any(c in part for c in " \t\n\"'"):
        return json.dumps(part)
    return part


def extract_json(text: str):
    """Pull the value after ``Result:`` out of the CLI's chatter.

    GenLayer CLI 0.39 prints JavaScript-like values: object keys are unquoted,
    strings use single quotes, and booleans are lower case. Looking for the
    last JSON-looking array is unsafe because transaction receipts also carry
    arrays of consensus votes. Restrict parsing to the final Result block and
    accept both strict JSON and the CLI's relaxed representation.
    """
    markers = list(re.finditer(r"(?m)^Result:\s*$", text))
    if not markers:
        stripped = text.strip()
        return stripped if stripped else None
    payload = text[markers[-1].end() :]
    payload = re.split(r"\n\s*[✔✖]", payload, maxsplit=1)[0].strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        pass
    try:
        quoted = re.sub(
            r"([,{]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:",
            r'\1"\2":',
            payload,
        )
        return ast.literal_eval(_replace_js_atoms(quoted))
    except (SyntaxError, ValueError):
        return payload


def _replace_js_atoms(source: str) -> str:
    """Translate true, false and null outside strings for literal_eval."""
    out = []
    index = 0
    quote_char = ""
    escaped = False
    while index < len(source):
        char = source[index]
        if quote_char:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote_char:
                quote_char = ""
            index += 1
            continue
        if char in ("'", '"'):
            quote_char = char
            out.append(char)
            index += 1
            continue
        replaced = False
        for word, value in (("true", "True"), ("false", "False"), ("null", "None")):
            end = index + len(word)
            before = source[index - 1] if index else ""
            after = source[end] if end < len(source) else ""
            if (
                source.startswith(word, index)
                and not (before.isalnum() or before == "_")
                and not (after.isalnum() or after == "_")
            ):
                out.append(value)
                index = end
                replaced = True
                break
        if not replaced:
            out.append(char)
            index += 1
    return "".join(out)


def call(args, method: str, *params) -> object:
    tail = [resolve_address(args), method]
    if params:
        tail += ["--args"] + [str(p) for p in params]
    return extract_json(run_genlayer(args, "call", tail))


def write(args, method: str, *params) -> object:
    tail = [resolve_address(args), method]
    if params:
        tail += ["--args"] + [str(p) for p in params]
    return extract_json(run_genlayer(args, "write", tail))


def apply_account(args) -> None:
    if not args.account:
        return
    candidate = pathlib.Path(args.account)
    if not candidate.exists():
        candidate = pathlib.Path.home() / ".genlayer" / "keys" / (args.account + ".json")
    if not candidate.exists() and not args.dry_run:
        die("no keystore for account " + args.account + " at " + str(candidate))
    command = ["genlayer", "config", "set", "keyPairPath=" + str(candidate)]
    if args.print_cmd or args.dry_run:
        print("  $ " + " ".join(quote(c) for c in command))
    if not args.dry_run:
        subprocess.run(command, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def milli(value: int) -> str:
    return "{:.3f}".format(int(value) / 1000.0)


def bar(distribution: str, width: int = 28) -> str:
    """A stacked bar over the answer distribution, in text.

    Each token gets its own glyph and the legend is printed underneath, so a
    reader can see the split without the frontend.
    """
    glyphs = "#=+.:o*"
    parts = []
    for chunk in distribution.split("|"):
        token, _, count = chunk.rpartition(":")
        try:
            parts.append((token, int(count)))
        except ValueError:
            continue
    total = sum(c for _, c in parts) or 1
    out = ""
    legend = []
    used = 0
    for index, (token, count) in enumerate(parts):
        if count == 0:
            continue
        glyph = glyphs[index % len(glyphs)]
        cells = round(count * width / total)
        if index == len(parts) - 1:
            cells = max(0, width - used)
        used += cells
        out += glyph * cells
        legend.append(glyph + " " + token + " " + str(count))
    return out.ljust(width) + "   " + "  ".join(legend)


def print_report(report: dict, worst: int | None) -> None:
    print()
    print("  " + str(report.get("title", "")))
    print("  spec " + str(report.get("spec_id")) + "   hash " + str(report.get("spec_hash")))
    print("  vocabulary " + ", ".join(report.get("vocabulary", [])))
    print(
        "  "
        + str(report.get("probes_seen"))
        + " probes over "
        + str(report.get("inputs_seen"))
        + " inputs, "
        + str(report.get("inputs_rated"))
        + " of them rated"
    )
    print(
        "  mean D "
        + milli(report.get("mean_d_milli", 0))
        + "   worst D "
        + milli(report.get("worst_d_milli", 0))
        + " on input "
        + str(report.get("worst_input_id"))
    )
    resolution = report.get("resolution_at_smallest_sample") or []
    if resolution:
        print("  D can only take these values at this sample size: " + ", ".join(milli(v) for v in resolution))
    print()

    rows = report.get("rows", [])
    if worst:
        rows = rows[: int(worst)]
    for row in rows:
        head = "  " + row["label"].ljust(14)
        if row["rated"]:
            head += "D " + milli(row["d_milli"])
        else:
            head += "D  -   "
        head += "  k " + str(row["k_scored"]) + "/" + str(row["k_total"])
        print(head)
        print("      " + bar(row["distribution"]))
        flags = []
        if row["unsettled_milli"]:
            flags.append("unsettled " + milli(row["unsettled_milli"]))
        if row["oov_milli"]:
            flags.append("out of vocabulary " + milli(row["oov_milli"]))
        if row["malformed_milli"]:
            flags.append("malformed " + milli(row["malformed_milli"]))
        if not row["rated"]:
            flags.append("below the minimum sample for a rate")
        if flags:
            print("      " + ", ".join(flags))
        print()

    independence = report.get("independence") or {}
    if independence:
        print("  independence: " + str(independence.get("note", "")))
    print()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_deploy(args) -> None:
    apply_account(args)
    out = run_genlayer(args, "deploy", ["--contract", str(CONTRACT_PATH)])
    if args.dry_run:
        return
    print(out.strip())
    address = None
    match = re.search(
        r"(?:Contract Address|contractAddress)\s*['\"]?\s*:\s*['\"]?"
        r"(0x[0-9a-fA-F]{40})",
        out,
    )
    if match:
        address = match.group(1)
    if address:
        state = load_state()
        state["address"] = address
        save_state(state)
        print("saved address " + address + " to " + str(STATE_FILE))
    else:
        print("could not read an address out of the output; pass --address from here on")


def cmd_new(args) -> None:
    apply_account(args)
    question = read_text(args.question, args.question_file, "question")
    tokens = [t.strip().upper() for t in args.vocab.split(",") if t.strip()]
    if len(tokens) < 2:
        die("a vocabulary needs at least two tokens; divergence over one token is not a quantity")
    for token in tokens:
        if token in RESERVED:
            die(token + " is reserved and is added by the contract, not by you")
    result = write(args, "register_spec", args.title, question, ",".join(tokens), args.budget)
    print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result))


def cmd_add(args) -> None:
    apply_account(args)
    payload = read_text(args.payload, args.payload_file, "payload")
    result = write(args, "add_input", args.spec, args.label, payload)
    print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result))


def cmd_probe(args) -> None:
    apply_account(args)
    inputs = call(args, "get_inputs", args.spec, 0, 100) or {}
    items = inputs.get("items", []) if isinstance(inputs, dict) else []
    if args.input:
        items = [i for i in items if i["label"] == args.input]
        if not items:
            die("no input labelled " + args.input + " on spec " + str(args.spec))
    if not items and not args.dry_run:
        die("spec " + str(args.spec) + " has no inputs yet")

    total = len(items) * args.k
    print("running " + str(total) + " probe transactions, " + str(args.k) + " per input")
    done = 0
    for round_index in range(args.k):
        # Round robin rather than k in a row on one input, so that a run that
        # is cut short still leaves every input with a comparable sample.
        for item in items:
            done += 1
            print(
                "  probe "
                + str(done)
                + "/"
                + str(total)
                + "  input "
                + str(item["input_id"])
                + " "
                + item["label"]
                + "  round "
                + str(round_index + 1)
            )
            result = write(args, "probe", args.spec, item["input_id"])
            if isinstance(result, dict) and "answer" in result:
                print("    " + str(result["answer"]) + "  " + str(result.get("confidence", "")))
            if args.delay:
                time.sleep(args.delay)


def cmd_report(args) -> None:
    apply_account(args)
    if args.snapshot:
        report = write(args, "compute_report", args.spec)
    else:
        report = call(args, "preview_report", args.spec)
    if args.dry_run:
        return
    if not isinstance(report, dict):
        die("could not read a report out of the node response")
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print("wrote " + args.json)
    print_report(report, args.worst)


def cmd_prompt(args) -> None:
    print(call(args, "get_prompt", args.spec, args.input_id))


def cmd_canonical(args) -> None:
    print(call(args, "get_canonical_spec", args.spec))


def cmd_battery(args) -> None:
    apply_account(args)
    battery = json.loads(pathlib.Path(args.file).read_text())
    print("registering " + battery["title"])
    result = write(
        args,
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
        if args.dry_run:
            spec_id = 0
        else:
            die("could not read the new spec id; register manually and use `jastrow add`")
    print("spec " + str(spec_id))

    for item in battery["inputs"]:
        print("  input " + item["label"])
        write(args, "add_input", spec_id, item["label"], item["payload"])

    args.spec = spec_id
    args.input = None
    cmd_probe(args)

    args.snapshot = True
    args.worst = None
    cmd_report(args)


def read_text(inline: str | None, path: str | None, what: str) -> str:
    if inline and path:
        die("pass either --" + what + " or --" + what + "-file, not both")
    if path:
        return pathlib.Path(path).read_text()
    if inline:
        return inline
    if not sys.stdin.isatty():
        return sys.stdin.read()
    die("no " + what + " given")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jastrow", description=__doc__.split("\n")[0])
    parser.add_argument("--address", help="contract address (default: .jastrow.json)")
    parser.add_argument("--rpc", help="RPC url passed straight through to genlayer")
    parser.add_argument("--account", help="named keystore or path to one")
    parser.add_argument(
        "--print", dest="print_cmd", action="store_true", help="show each genlayer invocation"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show the invocations without running them"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("deploy", help="deploy the contract").set_defaults(func=cmd_deploy)

    new = subparsers.add_parser("new", help="register a specification")
    new.add_argument("title")
    new.add_argument("--question")
    new.add_argument("--question-file")
    new.add_argument("--vocab", required=True, help="comma separated closed answer set")
    new.add_argument("--budget", type=int, default=100)
    new.set_defaults(func=cmd_new)

    add = subparsers.add_parser("add", help="add one case to a specification")
    add.add_argument("spec", type=int)
    add.add_argument("--label", required=True)
    add.add_argument("--payload")
    add.add_argument("--payload-file")
    add.set_defaults(func=cmd_add)

    probe = subparsers.add_parser("probe", help="run k probe transactions per input")
    probe.add_argument("spec", type=int)
    probe.add_argument("--k", type=int, default=5)
    probe.add_argument("--input", help="probe only this label")
    probe.add_argument("--delay", type=float, default=0.0, help="seconds between transactions")
    probe.set_defaults(func=cmd_probe)

    report = subparsers.add_parser("report", help="print the divergence report")
    report.add_argument("spec", type=int)
    report.add_argument("--worst", type=int, help="show only the worst N inputs")
    report.add_argument(
        "--snapshot", action="store_true", help="write a snapshot on chain instead of reading live"
    )
    report.add_argument("--json", help="also write the raw report to this file")
    report.set_defaults(func=cmd_report)

    prompt = subparsers.add_parser("prompt", help="print the exact prompt a judge is given")
    prompt.add_argument("spec", type=int)
    prompt.add_argument("input_id", type=int)
    prompt.set_defaults(func=cmd_prompt)

    canonical = subparsers.add_parser("canonical", help="print the exact string that was hashed")
    canonical.add_argument("spec", type=int)
    canonical.set_defaults(func=cmd_canonical)

    battery = subparsers.add_parser("battery", help="register, probe and report a battery file")
    battery.add_argument("file")
    battery.add_argument("--k", type=int, default=5)
    battery.add_argument("--delay", type=float, default=0.0)
    battery.add_argument("--json", help="write the resulting report here")
    battery.set_defaults(func=cmd_battery)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
