#!/usr/bin/env python3
"""Build a publishable Jastrow report from transaction receipts and traces."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "contracts"))
sys.path.insert(0, str(_ROOT / "test"))

import harness  # noqa: E402,F401
import jastrow  # noqa: E402


RESERVED = (
    jastrow.TOKEN_UNSETTLED,
    jastrow.TOKEN_OUT_OF_VOCAB,
    jastrow.TOKEN_MALFORMED,
)
OBS_RE = re.compile(r"JASTROW_OBSERVATION=(\{.*?\})(?:\n|$)")


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(value) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_jsonl(path: pathlib.Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(str(path) + ":" + str(line_no) + ": " + str(exc))
    return rows


def _fetch_json(url: str, timeout: float) -> dict:
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _receipt(explorer: str, tx_hash: str, timeout: float) -> dict:
    return _fetch_json(explorer.rstrip("/") + "/api/v1/transactions/" + tx_hash, timeout)


def _trace(tx_hash: str, rpc: str | None, timeout: float) -> str:
    command = ["genlayer", "trace", tx_hash, "--round", "0"]
    if rpc:
        command += ["--rpc", rpc]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    return result.stdout + result.stderr


def _observation_from_trace(text: str) -> tuple[dict, str]:
    match = OBS_RE.search(text)
    if not match:
        return {}, "missing JASTROW_OBSERVATION marker"
    try:
        return json.loads(match.group(1)), ""
    except json.JSONDecodeError as exc:
        return {}, "bad JASTROW_OBSERVATION marker: " + str(exc)


def _status(receipt: dict) -> str:
    raw = receipt.get("status") or receipt.get("status_name") or ""
    return str(raw).upper()


def _leader(receipt: dict) -> str:
    leader = receipt.get("leader")
    if isinstance(leader, str):
        return leader
    rounds = ((receipt.get("enrichment_data") or {}).get("rounds") or [])
    if rounds and isinstance(rounds[0], dict):
        leader = rounds[0].get("leader") or rounds[0].get("leader_address")
        if isinstance(leader, str):
            return leader
    return ""


def _validator_count(receipt: dict) -> int:
    validators = receipt.get("validators")
    if isinstance(validators, list):
        return len(validators)
    rounds = ((receipt.get("enrichment_data") or {}).get("rounds") or [])
    if rounds and isinstance(rounds[0], dict):
        validators = rounds[0].get("validators")
        if isinstance(validators, list):
            return len(validators)
    return 0


def _chain_cost(receipt: dict) -> int:
    for key in ("chain_total_cost", "total_cost", "cost"):
        value = receipt.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return 0


def _normalised_answer(obs: dict, vocab: list[str]) -> tuple[str, str]:
    answer = obs.get("answer")
    confidence = obs.get("confidence")
    allowed = vocab + list(RESERVED)
    if not isinstance(answer, str) or answer not in allowed:
        answer = jastrow.TOKEN_MALFORMED
    if confidence not in ("high", "low"):
        confidence = "low"
    return answer, confidence


def _distribution(counts: dict[str, int], vocab: list[str]) -> str:
    return "|".join(token + ":" + str(counts.get(token, 0)) for token in vocab + list(RESERVED))


def _row(label: str, input_id: int, counts: dict[str, int], vocab: list[str]) -> dict:
    total = sum(counts.values())
    scored = sum(counts.get(token, 0) for token in vocab)
    rated = scored >= jastrow.MIN_SCORED_FOR_RATE
    d_milli = jastrow._pair_disagreement_milli([counts.get(t, 0) for t in vocab], scored)
    modal_token = ""
    modal_count = 0
    for token in vocab:
        if counts.get(token, 0) > modal_count:
            modal_token = token
            modal_count = counts[token]
    return {
        "input_id": input_id,
        "label": label,
        "k_total": total,
        "k_scored": scored,
        "rated": rated,
        "d_milli": d_milli if rated else 0,
        "modal_token": modal_token,
        "modal_milli": jastrow._div_milli(modal_count, scored),
        "unsettled_milli": jastrow._div_milli(counts.get(jastrow.TOKEN_UNSETTLED, 0), total),
        "oov_milli": jastrow._div_milli(counts.get(jastrow.TOKEN_OUT_OF_VOCAB, 0), total),
        "malformed_milli": jastrow._div_milli(counts.get(jastrow.TOKEN_MALFORMED, 0), total),
        "low_confidence_milli": 0,
        "distribution": _distribution(counts, vocab),
    }


def _build_report(args, manifest: list[dict], evidence: list[dict]) -> dict:
    vocab = [token.strip().upper() for token in args.vocabulary.split(",") if token.strip()]
    buckets: dict[int, dict] = {}
    for row in manifest:
        input_id = int(row["input_id"])
        buckets.setdefault(
            input_id,
            {
                "input_id": input_id,
                "label": str(row["label"]),
                "counts": {token: 0 for token in vocab + list(RESERVED)},
            },
        )

    low_conf = {int(row["input_id"]): 0 for row in manifest}
    for item in evidence:
        input_id = int(item["input_id"])
        answer, confidence = _normalised_answer(item.get("observation") or {}, vocab)
        buckets[input_id]["counts"][answer] = buckets[input_id]["counts"].get(answer, 0) + 1
        if confidence == "low":
            low_conf[input_id] = low_conf.get(input_id, 0) + 1

    rows = []
    for bucket in buckets.values():
        row = _row(bucket["label"], bucket["input_id"], bucket["counts"], vocab)
        row["low_confidence_milli"] = jastrow._div_milli(
            low_conf.get(bucket["input_id"], 0), row["k_total"]
        )
        rows.append(row)
    rows.sort(key=lambda r: (0 if r["rated"] else 1, -r["d_milli"], -r["k_total"], r["input_id"]))

    rated = [r for r in rows if r["rated"]]
    mean_d = sum(r["d_milli"] for r in rated) // len(rated) if rated else 0
    worst = rated[0] if rated else {"input_id": 0, "d_milli": 0}
    sample_sizes = sorted({r["k_scored"] for r in rated})
    smallest = sample_sizes[0] if sample_sizes else 0

    accepted = sum(1 for e in evidence if e["status"] in ("ACCEPTED", "FINALIZED", "SUCCESS"))
    undetermined = sum(1 for e in evidence if e["status"] == "UNDETERMINED")
    leaders = sorted({e.get("leader", "") for e in evidence if e.get("leader")})
    validator_sizes = [e.get("validator_set_size", 0) for e in evidence if e.get("validator_set_size")]
    costs = [e.get("chain_total_cost", 0) for e in evidence]

    report = {
        "spec_id": int(args.spec),
        "title": args.title,
        "spec_hash": args.spec_hash,
        "vocabulary": vocab,
        "snapshot": True,
        "computed_at_seq": 0,
        "probes_seen": len(evidence),
        "inputs_seen": len(rows),
        "inputs_rated": len(rated),
        "mean_d_milli": mean_d,
        "worst_input_id": worst["input_id"],
        "worst_d_milli": worst["d_milli"],
        "min_scored_for_rate": jastrow.MIN_SCORED_FOR_RATE,
        "resolution_at_smallest_sample": (
            jastrow._achievable_d(smallest, min(len(vocab), 6)) if smallest else []
        ),
        "independence": {
            "leader_visibility": "explorer",
            "distinct_leaders": len(leaders),
            "validator_set_size": max(validator_sizes) if validator_sizes else 0,
            "note": (
                "Leader identity is measured from Explorer receipts. Rates are "
                "over first-round leader observations, and consensus status is "
                "reported separately."
            ),
        },
        "consensus": {
            "accepted": accepted,
            "undetermined": undetermined,
            "other": len(evidence) - accepted - undetermined,
        },
        "chain_cost": {
            "total_cost_units": sum(costs),
            "samples_with_cost": sum(1 for c in costs if c),
        },
        "rows": rows,
        "evidence": evidence,
        "provenance": {
            "kind": "chain-receipts",
            "network": args.network,
            "contract": args.address,
            "manifest": str(args.manifest),
            "explorer": args.explorer,
        },
        "equivalence_principle": jastrow.EQUIVALENCE_PRINCIPLE,
    }
    report["evidence_root"] = _sha256_hex(_canonical(evidence))
    report["report_hash"] = _sha256_hex(_canonical({k: v for k, v in report.items() if k != "report_hash"}))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("manifest", type=pathlib.Path)
    parser.add_argument("--out", default="web/report.json")
    parser.add_argument("--address", required=True)
    parser.add_argument("--spec", type=int, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--spec-hash", required=True)
    parser.add_argument("--vocabulary", required=True)
    parser.add_argument("--network", default="GenLayer Bradbury testnet")
    parser.add_argument("--explorer", default="https://explorer-bradbury.genlayer.com")
    parser.add_argument("--rpc")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    manifest = _load_jsonl(args.manifest)
    evidence = []
    for index, row in enumerate(manifest, 1):
        tx_hash = row["tx_hash"]
        try:
            receipt = _receipt(args.explorer, tx_hash, args.timeout)
        except Exception as exc:
            receipt = {"fetch_error": str(exc)}
        trace_text = ""
        trace_error = ""
        status = _status(receipt) if not receipt.get("fetch_error") else "FETCH_ERROR"
        terminal = status in ("ACCEPTED", "FINALIZED", "UNDETERMINED", "SUCCESS")
        if terminal:
            try:
                trace_text = _trace(tx_hash, args.rpc, args.timeout)
            except (subprocess.SubprocessError, TimeoutError) as exc:
                trace_error = str(exc)
        observation, parse_error = _observation_from_trace(trace_text)
        item = {
            "tx_hash": tx_hash,
            "spec_id": int(row["spec_id"]),
            "input_id": int(row["input_id"]),
            "label": str(row["label"]),
            "round": int(row.get("round", 0)),
            "status": status,
            "execution_result": str(receipt.get("execution_result") or receipt.get("txExecutionResultName") or ""),
            "leader": _leader(receipt),
            "validator_set_size": _validator_count(receipt),
            "chain_total_cost": _chain_cost(receipt),
            "observation": observation,
            "parse_error": parse_error or trace_error or ("" if terminal else "transaction not terminal"),
        }
        evidence.append(item)
        print(str(index) + "/" + str(len(manifest)) + " " + tx_hash + " " + item["status"], flush=True)

    report = _build_report(args, manifest, evidence)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("wrote " + str(out))
    print("report_hash " + report["report_hash"])
    print("evidence_root " + report["evidence_root"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
