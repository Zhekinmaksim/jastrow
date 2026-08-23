# Jastrow

Jastrow is a GenLayer Intelligent Contract for finding ambiguous specs before
they turn into disputed outcomes.

The idea is simple: take one specification, run the same cases through the
validator set, and look at where independent judges split. Those cases are the
parts of the spec that need work.

This is not an AI judge that tells you the "right" answer. It is a measuring
tool. It shows where the answers stop being stable.

## Why this exists

Some failures are not caused by a bad validator or a bad model. The spec itself
can be unclear.

The example this repo uses is a campaign rule: a post qualifies if it includes
the `#GenLayer` hashtag and a project link. That sounds clear until you test
real edge cases:

- `#GenLayer`
- `# GenLayer`
- hashtag in an image
- a reply that links to the project but not in the main post
- plural or cased variants

Jastrow turns those edge cases into a report. Clean cases should converge.
Ambiguous cases should split. If everything splits, the prompt is broken. If
nothing splits, the battery is too weak or the validator set is too uniform.

## What changed after the first live run

The first version assumed that validators could be asked to record the leader's
answer even when they disagreed with it. Bradbury did not behave that way. A
comparative probe ended `UNDETERMINED / NONDET_DISAGREE`, which means validators
were not just recording the leader output.

So the project now uses the honest version:

- each probe is a normal comparative consensus transaction
- disagreement is allowed to surface as `UNDETERMINED`
- the publishable report is built from transaction receipts and traces
- leader identity and validator set size come from Explorer evidence
- the final report is anchored back on chain with `commit_report`

That makes long transaction confirmation less painful too. The runner stores a
transaction hash as soon as the CLI prints it, then a separate collector waits
for receipts and builds the report later.

## What the contract does

`contracts/jastrow.py` stores:

- a spec title and question
- a closed answer vocabulary, such as `ACCEPT,REJECT`
- the input cases to test
- accepted probe results
- report commitments

The accepted probe log is useful, but it is not the full measurement. Failed or
undetermined probes cannot be written into contract storage, so the public
report is computed from receipts.

The report counts, per input:

- how many probes returned each answer
- how often judges returned `UNSETTLED`
- how often output was malformed or outside the vocabulary
- the divergence score `D`
- consensus status counts
- distinct leaders seen in the receipt evidence
- validator set size

`D` is:

```text
D = 1 - sum(p_v * p_v)
```

where `p_v` is the fraction of scored probes that returned answer `v`.

In plain English: `D` is the chance that two independent judges give different
answers for the same input.

## Repository layout

```text
contracts/jastrow.py        Intelligent Contract
cli/jastrow.py              small wrapper around the official genlayer CLI
scripts/submit_probes.py    submits probes and records tx hashes immediately
scripts/receipt_report.py   builds the report from Explorer receipts and traces
scripts/check_report.py     audits report math and receipt evidence
scripts/embed_report.py     embeds a report into the web page
scripts/bundle.py           builds a standalone HTML copy
calibration/battery.json    reference test battery
web/index.html              public report page
web/src/live.js             browser wallet call to the live contract
reel/                       Remotion video source
test/                       no-dependency contract tests
```

## Local checks

Run this first:

```bash
make check
```

It runs:

- contract tests under a local GenLayer stub
- report audit
- page math audit

The report audit matters. It recomputes every headline number from the rows and
checks receipt evidence when the report came from chain data.

## Deploy and run

You need Python 3, Node, the official `genlayer` CLI, and a funded Bradbury
testnet account.

Deploy:

```bash
python3 cli/jastrow.py --print deploy
```

Register the reference battery and inputs:

```bash
python3 cli/jastrow.py --print battery calibration/battery.json --k 0
```

If you prefer the current CLI path, register manually with `new` and `add`.
The important part is that the expensive probe stage is submitted with the
async runner:

```bash
python3 scripts/submit_probes.py \
  --spec 0 \
  --k 5 \
  --manifest runs/bradbury-probes.jsonl
```

Build the receipt report after receipts are available:

```bash
python3 scripts/receipt_report.py runs/bradbury-probes.jsonl \
  --address 0xYOUR_CONTRACT \
  --spec 0 \
  --title "Campaign rule v3" \
  --spec-hash YOUR_SPEC_HASH \
  --vocabulary ACCEPT,REJECT \
  --out web/report.json
```

Audit it:

```bash
python3 scripts/check_report.py web/report.json
```

Embed it into the page:

```bash
python3 scripts/embed_report.py web/report.json \
  --contract 0xYOUR_CONTRACT \
  --network "GenLayer Bradbury testnet" \
  --site https://YOUR_VERCEL_URL
```

Then build the site:

```bash
npm install
npm run build
```

## Frontend

The page is not just a static report. It has a live contract panel.

With a chain report embedded, a reviewer can connect a wallet, choose an input,
call `probe(spec_id, input_id)`, get the transaction hash immediately, and watch
the lifecycle through accepted, finalized, undetermined, or error states.

That is there because GenLayer transactions can take a while. A slow receipt
should not make the UI look broken.

## Deploying this repo

The intended public repo is:

```text
https://github.com/Zhekinmaksim/jastrow
```

The intended host is Vercel. The project includes `vercel.json`; Vercel should
install dependencies, run `npm run build`, and serve `dist`.

## Known limits

This project is deliberately conservative about claims.

- A fixture report is not a measurement.
- Accepted-only contract storage is not the full report.
- `UNDETERMINED` probes are part of the evidence, not a failure to hide.
- Distinct leader counts must come from receipts until the contract runtime
  exposes leader identity directly.
- GEN costs must be filled from real receipts, not estimates.

Those limits are visible in the docs and on the page because they change how
the result should be read.
