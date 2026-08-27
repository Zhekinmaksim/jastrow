# Submission draft

Category: Intelligent Contract project.

## Short description

Jastrow is a pre-deploy ambiguity gate for GenLayer specs.

A user gives the contract a spec, a closed answer set, and test inputs. Jastrow
runs those inputs through GenLayer validator consensus, reports where validators
split, and exposes a CLI gate that returns `DECIDABLE`, `AMBIGUOUS`, or
`UNDECIDABLE` with CI-friendly exit codes.

It does not claim that AI found the right answer. It measures when the answer
is not stable.

One-line positioning against the closest neighbor:

```text
GLBench says which validator is good. Jastrow says whether your spec is decidable.
```

GLBench is for validator operators. Jastrow is for contract authors.

## Problem

Many contract failures are framed as model failures, but sometimes the real
problem is the spec. If the rule is underspecified, competent validators can
read the same input differently.

The reference battery uses the kind of edge case already seen in GenLayer
campaign judging: a required hashtag and project link, then inputs such as
`#GenLayer`, `# GenLayer`, image-only hashtags, replies, casing, and plural
variants.

Clean inputs should converge. Ambiguous inputs should split. If `clean` or
`missing` splits, the prompt is broken. If nothing splits, the battery is too
weak or the validator set is too uniform.

## How it works

Each probe is a normal comparative GenLayer transaction.

The first prototype tried to make validators accept the leader's answer even
when they disagreed. Bradbury rejected that assumption: a split probe ended
`UNDETERMINED / NONDET_DISAGREE`. Jastrow now treats that as evidence instead
of trying to hide it.

The publishable report is built from transaction receipts and traces:

- the contract pins the spec hash, input, vocabulary, and prompt
- the leader observation is emitted in trace output
- the collector records receipt status, leader, observed committee size, and answer
- the report computes divergence from that evidence
- `commit_report` anchors the report hash and evidence root back on chain

That design also handles long confirmations. The async runner stores the
transaction hash as soon as it is printed, then the receipt collector finishes
the report later.

The source contract also has a bonded challenge loop. A sponsor stakes GEN on
the claim that a spec is below a divergence threshold. A challenger points to a
specific input; if the contract-computed report shows that input crossing the
threshold, the challenger receives the bond. If the report is fully rated and
below threshold, the sponsor can release the bond.

## What reviewers can try

The frontend is a real contract caller. With a chain report embedded, a reviewer
can connect a wallet, choose an input, call `probe(spec_id, input_id)`, get a
transaction hash immediately, and watch the lifecycle move through pending,
accepted, finalized, undetermined, or error states.

The CLI gate can be run locally:

```bash
python3 cli/jastrow.py run web/report.json --threshold 0.25
```

Exit code `0` means `DECIDABLE`. Exit code `1` means `AMBIGUOUS`. Exit code `2`
means `UNDECIDABLE` because the run is incomplete, malformed, unrated, or still
a fixture.

## What is measured

For each input, Jastrow reports the answer distribution and:

```text
D = 1 - sum(p_v * p_v)
```

where `p_v` is the fraction of scored probes that returned answer `v`.

`D` is the chance that two independently drawn judges disagree on the same
input. `UNSETTLED`, `OUT_OF_VOCAB`, and `MALFORMED` are reported separately
because each one needs a different fix.

## Why this belongs on GenLayer

A single model cannot measure validator disagreement. An off-chain model
ensemble measures the ensemble chosen by the author, not the population that
will judge the contract.

Jastrow uses GenLayer's own validator set as the instrument.

The local builder-program corpus was used only for positioning, not as a
submitted ecosystem measurement. The final submission does not claim a completed
run over live contracts from that corpus, because the full address list and
per-contract receipts are not committed here. Jastrow follows the GLBench shape
at the product level: the object being measured is not the validator, it is the
builder's specification.

## Live evidence to include before final submit

- Repository: https://github.com/Zhekinmaksim/jastrow
- Vercel page: https://jastrow.vercel.app
- Contract address: `0xC8823fdeA01961D65b569D00C09c541E5615CC69`
- Deploy tx: [`0x1bb7db3c…d61ef0`](https://explorer-bradbury.genlayer.com/transactions/0x1bb7db3c0c2c2f1d639ca742cc36e8e5f0f17b58cc8642b88ef0e85186d61ef0)
- Current embedded report: receipt-backed live Bradbury measurement
- Live probe manifest: `runs/bradbury-v2-publish.jsonl`, 40/40 usable terminal
  receipts, five observations per input
- Example probe receipt: [`0x819eb381…bd0b2`](https://explorer-bradbury.genlayer.com/transactions/0x819eb3812d37d70bc4d3b5d36ee974eaf624e5cd5c6a6a670211de8a6ddbd0b2)
- Report hash:
  `83a6862538fdb05dda7725819dd9c5bbd2b24859768f3ee8bacfc834cfb9b4b2`
- Evidence root:
  `93b17d1ba86dcdfbb72b930c0186dc70846fbda1dd1bf82e622d66ce5306d792`
- Observed validator committee sizes: 5, 11, 12, 17
- Distinct first-round leaders across receipts: 23
- No single validator set size is claimed for the whole 40-transaction sample
- Consensus status: 40/40 terminal `FINALIZED` receipts, with execution
  results `FINISHED_WITH_RETURN` 12, `NONDET_DISAGREE` 23, and `TIMEOUT` 5
- The live gate result is `UNDECIDABLE` / exit `2`: 7 of 8 inputs are rated and
  `in-reply` has only 1 of 5 answers scored; the run also records malformed
  output for `quoted` and `in-reply`
- GEN probe cost: 0.12573950147854495 GEN across 40 probe transactions
- Challenge-market methods are present in source and local tests. Deploy them
  only if restarting the live contract is acceptable, because the current
  Bradbury report manifest belongs to the address above.

## Limits stated up front

- The report is a receipt-backed measurement, not the earlier fixture.
- The 40-line publish manifest is committed with the submission so the receipt
  report can be regenerated from public transaction hashes.
- The report hash is locally recomputable from those receipts; no on-chain
  `commit_report` transaction is claimed until its receipt is included here.
- Accepted-only contract storage is not the full report.
- `UNDETERMINED` is part of the evidence.
- Leader counts come from receipts until the contract runtime exposes leader
  identity directly.
- No GEN number should be estimated in the final submission.

## Suggested portal text

Jastrow is a pre-deploy ambiguity gate for GenLayer specs. GLBench says which
validator is good; Jastrow says whether your spec is decidable. It runs the same
cases through GenLayer validator consensus and reports the concrete inputs where
answers split. Those are the clauses to rewrite before a contract takes user
value.

The contract stores the spec, inputs, accepted probes, and report commitments.
The published report is built from transaction receipts, so it includes
accepted and undetermined probes, first-round leader observations, observed
committee sizes, and distinct leader count. The report hash and evidence root
can be anchored back on chain with `commit_report`.

The source contract also includes bonded spec challenges: a sponsor stakes GEN
that a spec is below a divergence threshold, and a challenger can win the bond
by pointing to a concrete splitting input. That is the protocol version of the
same measurement.

The frontend calls the deployed contract directly. A reviewer can connect a
wallet, choose an input, submit `probe(spec_id, input_id)`, receive the
transaction hash immediately, and watch the full transaction lifecycle.

The repo also includes a CI gate:

```bash
python3 cli/jastrow.py run web/report.json --threshold 0.25
```

It returns `DECIDABLE`, `AMBIGUOUS`, or `UNDECIDABLE` with non-zero exit codes
for specs that should not be deployed unchanged.
