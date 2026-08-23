# Submission draft

Category: Intelligent Contract project.

## Short description

Jastrow measures where a GenLayer specification is ambiguous.

A user gives the contract a spec, a closed answer set, and test inputs. The
system runs those inputs through GenLayer validator consensus and reports where
validators split. Those are the cases most likely to create appeals or unstable
outcomes later.

It does not claim that AI found the right answer. It measures when the answer
is not stable.

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
- the collector records receipt status, leader, validator set size, and answer
- the report computes divergence from that evidence
- `commit_report` anchors the report hash and evidence root back on chain

That design also handles long confirmations. The async runner stores the
transaction hash as soon as it is printed, then the receipt collector finishes
the report later.

## What reviewers can try

The frontend is a real contract caller. With a chain report embedded, a reviewer
can connect a wallet, choose an input, call `probe(spec_id, input_id)`, get a
transaction hash immediately, and watch the lifecycle move through pending,
accepted, finalized, undetermined, or error states.

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

## Live evidence to include before final submit

- Repository: https://github.com/Zhekinmaksim/jastrow
- Vercel page: to be filled after deploy
- Contract address: to be filled after deploy
- Report hash: to be filled after receipt report
- Evidence root: to be filled after receipt report
- Validator set size: 32 was observed on Bradbury on 23 August 2026; final run
  should state the live value from receipts
- Distinct leaders: to be filled from Explorer receipt evidence
- GEN costs: to be filled from receipts in `COSTS.md`

## Limits stated up front

- A fixture report is not a measurement.
- Accepted-only contract storage is not the full report.
- `UNDETERMINED` is part of the evidence.
- Leader counts come from receipts until the contract runtime exposes leader
  identity directly.
- No GEN number should be estimated in the final submission.

## Suggested portal text

Jastrow is an ambiguity meter for GenLayer specs. It runs the same cases
through GenLayer validator consensus and reports where answers split. The goal
is to find underspecified inputs before they become appeals.

The contract stores the spec, inputs, accepted probes, and report commitments.
The published report is built from transaction receipts, so it includes
accepted and undetermined probes, first-round leader observations, validator set
size, and distinct leader count. The report hash and evidence root are then
anchored back on chain with `commit_report`.

The frontend calls the deployed contract directly. A reviewer can connect a
wallet, choose an input, submit `probe(spec_id, input_id)`, receive the
transaction hash immediately, and watch the full transaction lifecycle.
