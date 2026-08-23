#!/usr/bin/env python3
"""Measure the same battery off chain, across several models, before deploying.

This exists to answer two questions that decide whether the instrument has a
scale at all, and both of them are cheaper to answer here than on chain:

  1. Do judges ever reach for UNSETTLED, or are they too decisive for the
     signal to exist? If nothing ever comes back UNSETTLED, that column is
     dead and the report should stop implying it means something.
  2. Does the prompt produce parseable output often enough that MALFORMED
     stays a rare event rather than a category?

It deliberately imports the contract module and uses the contract's own
_build_prompt, _normalise_answer and _pair_disagreement_milli. A calibration
that reimplemented any of those would be measuring a second piece of code
rather than the one that ships.

An off-chain ensemble is NOT the same population as the validator set, so
nothing here is a substitute for a real report. It is a pre-flight check on
the instrument, not a measurement of a specification.

Usage:

    export JASTROW_MODELS='openai:gpt-4o-mini,openai:gpt-4.1-mini'
    export OPENAI_API_KEY=...
    python3 scripts/calibrate.py calibration/battery.json --k 3

    python3 scripts/calibrate.py calibration/battery.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "test"))
sys.path.insert(0, str(_ROOT / "contracts"))

import harness  # noqa: E402,F401  installs the genlayer stub before the import below
import jastrow  # noqa: E402


# ---------------------------------------------------------------------------
# Providers. Two are enough: an OpenAI compatible chat endpoint covers most
# hosts, and Anthropic's messages endpoint covers the rest.
# ---------------------------------------------------------------------------


def call_openai_compatible(model: str, prompt: str, base: str, key: str) -> str:
    request = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "max_tokens": 300,
                "temperature": 1,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8"),
        headers={"content-type": "application/json", "authorization": "Bearer " + key},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def call_anthropic(model: str, prompt: str, key: str) -> str:
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(
            {
                "model": model,
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        body = json.loads(response.read().decode("utf-8"))
    return "".join(block.get("text", "") for block in body.get("content", []))


def ask(spec: str, prompt: str) -> str:
    provider, _, model = spec.partition(":")
    provider = provider.strip().lower()
    if provider == "openai":
        return call_openai_compatible(
            model,
            prompt,
            os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            require_env("OPENAI_API_KEY"),
        )
    if provider == "anthropic":
        return call_anthropic(model, prompt, require_env("ANTHROPIC_API_KEY"))
    if provider == "compatible":
        return call_openai_compatible(
            model,
            prompt,
            require_env("JASTROW_BASE_URL"),
            require_env("JASTROW_API_KEY"),
        )
    raise SystemExit("unknown provider in " + spec + ", expected openai, anthropic or compatible")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit("set " + name + " before running the calibration")
    return value


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("battery", help="path to a battery json file")
    parser.add_argument("--k", type=int, default=3, help="samples per model per input")
    parser.add_argument("--models", help="comma separated, overrides JASTROW_MODELS")
    parser.add_argument("--out", help="write the raw per call log here")
    parser.add_argument("--dry-run", action="store_true", help="print one prompt and stop")
    args = parser.parse_args()

    battery = json.loads(pathlib.Path(args.battery).read_text())
    vocab_tokens = [t.strip().upper() for t in battery["vocabulary"].split(",") if t.strip()]
    question = jastrow._normalise_text(battery["question"])
    spec_hash = jastrow._digest(
        jastrow._canonical_spec(battery["title"], question, ",".join(vocab_tokens))
    )

    if args.dry_run:
        first = battery["inputs"][0]
        print(jastrow._build_prompt(spec_hash, question, vocab_tokens, first["payload"]))
        return 0

    models = [m.strip() for m in (args.models or os.environ.get("JASTROW_MODELS", "")).split(",") if m.strip()]
    if not models:
        raise SystemExit("no models. Set JASTROW_MODELS or pass --models.")

    print("battery " + battery["name"] + "   spec hash " + spec_hash)
    print("models: " + ", ".join(models))
    print()

    log = []
    rows = []
    unsettled_total = 0
    malformed_total = 0
    oov_total = 0
    calls_total = 0

    for item in battery["inputs"]:
        prompt = jastrow._build_prompt(spec_hash, question, vocab_tokens, item["payload"])
        counts = {token: 0 for token in vocab_tokens}
        unsettled = 0
        oov = 0
        malformed = 0

        for model in models:
            for sample in range(args.k):
                calls_total += 1
                try:
                    raw = ask(model, prompt)
                except (urllib.error.URLError, KeyError, TimeoutError) as exc:
                    print("  " + item["label"] + "  " + model + "  request failed: " + repr(exc))
                    continue
                recorded = jastrow._normalise_answer(raw, vocab_tokens)
                token = recorded["answer"]
                log.append(
                    {
                        "label": item["label"],
                        "model": model,
                        "sample": sample,
                        "answer": token,
                        "confidence": recorded["confidence"],
                        "raw": raw,
                    }
                )
                if token == jastrow.TOKEN_UNSETTLED:
                    unsettled += 1
                elif token == jastrow.TOKEN_OUT_OF_VOCAB:
                    oov += 1
                elif token == jastrow.TOKEN_MALFORMED:
                    malformed += 1
                else:
                    counts[token] += 1

        scored = sum(counts.values())
        d_milli = jastrow._pair_disagreement_milli([counts[t] for t in vocab_tokens], scored)
        rated = scored >= jastrow.MIN_SCORED_FOR_RATE
        unsettled_total += unsettled
        malformed_total += malformed
        oov_total += oov

        rows.append(
            {
                "label": item["label"],
                "d_milli": d_milli if rated else None,
                "scored": scored,
                "counts": dict(counts),
                "unsettled": unsettled,
                "out_of_vocab": oov,
                "malformed": malformed,
            }
        )
        reading = "{:.3f}".format(d_milli / 1000.0) if rated else "  -  "
        print(
            "  "
            + item["label"].ljust(12)
            + " D " + reading
            + "   " + "  ".join(t + " " + str(counts[t]) for t in vocab_tokens)
            + ("   UNSETTLED " + str(unsettled) if unsettled else "")
            + ("   OUT_OF_VOCAB " + str(oov) if oov else "")
            + ("   MALFORMED " + str(malformed) if malformed else "")
        )

    print()
    print("  " + str(calls_total) + " calls")
    print("  UNSETTLED reached for " + str(unsettled_total) + " times")
    if unsettled_total == 0:
        print("  -> the unsettled signal is dead at this prompt. Do not build the")
        print("     report around a column that never fills. Either the prompt has")
        print("     to make the option costlier to ignore, or the field goes.")
    print("  MALFORMED " + str(malformed_total) + ", OUT_OF_VOCAB " + str(oov_total))
    if malformed_total > calls_total * 0.05:
        print("  -> malformed is above five percent, which is a parsing problem")
        print("     rather than a measurement. Fix the prompt before deploying.")

    rated = [r for r in rows if r["d_milli"] is not None]
    if rated:
        spread = max(r["d_milli"] for r in rated) - min(r["d_milli"] for r in rated)
        print("  D spread across the battery: " + "{:.3f}".format(spread / 1000.0))
        if spread == 0:
            print("  -> every input measured the same. Either the battery has no")
            print("     duck-rabbits in it, or the instrument is not resolving.")

    if args.out:
        pathlib.Path(args.out).write_text(
            json.dumps(
                {
                    "battery": battery["name"],
                    "spec_hash": spec_hash,
                    "models": models,
                    "k_per_model": args.k,
                    "rows": rows,
                    "log": log,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        print("  wrote " + args.out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
