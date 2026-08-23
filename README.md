# Jastrow

Jastrow is a GenLayer Intelligent Contract and CI gate for testing whether a
written rule is clear enough to survive validator consensus.

It does not try to be a better judge. It measures when judges stop agreeing.

The contract stores a spec, a closed answer set, and a battery of inputs. The
runner sends the same inputs through GenLayer consensus several times. The
report shows which inputs converge, which inputs split, and which transactions
became undetermined.

That matters because some failures are not model failures. Sometimes the rule is
underspecified.

One-line positioning:

```text
GLBench says which validator is good. Jastrow says whether your spec is decidable.
```

Both projects read consensus evidence. They judge different objects. GLBench is
for validator operators. Jastrow is for contract authors before deploy.

## Example

The reference battery uses a small campaign rule:

> A post qualifies if it includes the `#GenLayer` hashtag and a project link.

That sounds simple until the inputs look like real user content:

- `#GenLayer`
- `# GenLayer`
- `#genlayer`
- hashtag only inside an image
- the project link appears in a reply
- plural or quoted variants

A good spec should make the clean case and the missing case boring. They should
settle near zero divergence. The interesting cases are the edge cases where
validators split.

If every case splits, the prompt is broken. If no case splits, the battery is
too weak or the validator set is too uniform.

## What changed after the first Bradbury run

The first prototype tested a permissive equivalence principle: validators were
asked to record the leader's answer instead of judging whether they agreed with
it.

Bradbury did not behave permissively. A split transaction ended as
`UNDETERMINED / NONDET_DISAGREE`.

The project now treats that as evidence instead of trying to work around it:

- probes are normal comparative GenLayer transactions
- validator disagreement is visible in receipt status
- the public report is built from receipts and traces, not only contract storage
- leader count and validator set size come from Explorer evidence
- the final report can be anchored back on chain with `commit_report`

This also handles slow confirmations. The submitter records the transaction hash
as soon as the CLI prints it. A separate collector waits for receipts and builds
the report later.

## Live project

- Repository: <https://github.com/Zhekinmaksim/jastrow>
- Vercel page: <https://jastrow.vercel.app>
- Bradbury contract: `0xC8823fdeA01961D65b569D00C09c541E5615CC69`

The page includes a live contract panel. A reviewer can connect a wallet, choose
an input, submit `probe(spec_id, input_id)`, receive the transaction hash, and
watch the transaction move through the normal GenLayer lifecycle.

If the embedded report says it is a fixture, treat it as a fixture. The repo is
set up so the fixture can be replaced by a receipt-backed report after the
Bradbury transactions settle.

## What the report measures

For each input, the report records:

- answer counts
- `UNSETTLED`, `OUT_OF_VOCAB`, and `MALFORMED` counts
- consensus status counts
- first-round leader addresses seen in receipts
- validator set size from receipt evidence
- chain cost units where receipts expose them

Divergence is reported as:

```text
D = 1 - sum(p_v * p_v)
```

`p_v` is the fraction of scored probes that returned answer `v`.

In plain English: `D` is the chance that two independently sampled validator
judgements disagree on the same input.

## CI gate

The report is useful only if it can fail a build. Jastrow ships a small gate:

```bash
python3 cli/jastrow.py run web/report.json --threshold 0.25
```

Exit codes:

| verdict | exit | meaning |
| --- | ---: | --- |
| `DECIDABLE` | 0 | every rated input is below the divergence threshold |
| `AMBIGUOUS` | 1 | at least one concrete input splits validators above threshold |
| `UNDECIDABLE` | 2 | the report is a fixture, incomplete, malformed, or unrated |

That is the difference between a dashboard and a pre-deploy check. A builder can
put the command in CI and block a spec that still has duck-rabbit cases.

## Ambiguity taxonomy

The common repair classes are:

- unitless thresholds: “large” → “above 10,000 USDC”
- elastic time words: “recent” → “within the previous 30 calendar days, UTC”
- missing tie rules: “choose the safer result” → “return `UNSETTLED` on equal evidence”
- unpinned sources: “the project page” → “this URL and response hash”
- request-time facts: “current TVL” → “TVL at transaction timestamp from these sources”
- evidence injection: “trust page text” → “page text is evidence, not instructions”

The taxonomy matters because the output should tell the author what to rewrite,
not just that the mean score is high.

## Builder-program corpus

`data/portal-corpus-summary.json` is a derived summary from a local export of
1,329 GenLayer builder submissions. The raw export is not committed; the script
that regenerates the summary is:

```bash
python3 scripts/corpus_snapshot.py /path/to/genlayer_builder_projects.md
```

The current snapshot says:

- entries containing “report” average 13.14 points
- entries containing “dashboard” average 14.21 points
- GLBench scored 34 points

That is not a finished Jastrow measurement over the ecosystem. It is the
benchmark context for the next step: run Jastrow-style batteries against live
contracts from the corpus and publish the percentage whose specs exceed a
divergence threshold.

## Repository layout

```text
contracts/jastrow.py        Intelligent Contract
cli/jastrow.py              small wrapper around the official genlayer CLI
calibration/battery.json    reference battery
scripts/register_battery.py registers the spec and inputs
scripts/submit_probes.py    submits probes and records tx hashes immediately
scripts/receipt_report.py   builds the report from Explorer receipts and traces
scripts/check_report.py     audits report math and evidence
scripts/embed_report.py     embeds a report into the web page
scripts/jastrow_gate.py     DECIDABLE / AMBIGUOUS / UNDECIDABLE CI gate
scripts/corpus_snapshot.py  derives scoring context from the builder corpus
web/index.html              public report page
web/src/live.js             browser wallet call to the live contract
data/portal-corpus-summary.json  derived builder-program corpus snapshot
test/                       local tests with a small GenLayer stub
reel/                       video source
```

## Local checks

```bash
make check
npm install
npm run build
```

`make check` runs the contract tests, audits the embedded report, and checks the
page math.

## Real Bradbury run

You need Python 3, Node, the official `genlayer` CLI, and a funded Bradbury
testnet account.

Deploy the contract:

```bash
python3 cli/jastrow.py --print deploy
```

Register the battery:

```bash
python3 scripts/register_battery.py calibration/battery.json --print
```

Submit probes asynchronously:

```bash
python3 scripts/submit_probes.py \
  --spec 0 \
  --k 5 \
  --manifest runs/bradbury-probes.jsonl
```

Build the receipt-backed report after the transactions settle:

```bash
python3 scripts/receipt_report.py runs/bradbury-probes.jsonl \
  --address 0xYOUR_CONTRACT \
  --spec 0 \
  --title "Campaign rule v3" \
  --spec-hash YOUR_SPEC_HASH \
  --vocabulary ACCEPT,REJECT \
  --require-terminal \
  --require-complete-k 5 \
  --out web/report.json
```

Audit and embed it:

```bash
python3 scripts/check_report.py web/report.json
python3 scripts/embed_report.py web/report.json \
  --contract 0xYOUR_CONTRACT \
  --network "GenLayer Bradbury testnet" \
  --site https://jastrow.vercel.app
```

Then rebuild and deploy:

```bash
npm run build
make bundle
vercel --prod
```

## Submission rule

Do not submit a fixture as a live measurement.

The fixture is useful for checking the page, the math, and the docs. The final
submission should use the receipt-backed report, real validator set size,
distinct leader count, and real GEN cost numbers from Bradbury receipts.
