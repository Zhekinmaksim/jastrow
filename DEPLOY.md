# Deploying Jastrow

This is the order to use for a real submission run.

The important change from the first prototype: do not wait for every probe to
finalize before submitting the next one. Bradbury confirmations can be slow.
Submit hashes first, collect receipts later.

## 0. Local checks

```bash
make check
npm install
npm run build
```

Do not deploy if either check fails.

## 1. Deploy the contract

```bash
python3 cli/jastrow.py --print deploy
```

The address is saved in `.jastrow.json`.

Confirm it responds:

```bash
genlayer call 0xYOUR_CONTRACT get_overview
```

## 2. Register the battery

Register the spec and add the inputs from `calibration/battery.json`.

You can use the CLI wrapper or run the commands manually. For a manual run,
use:

```bash
python3 cli/jastrow.py --print new "Campaign rule v3" \
  --question-file /tmp/jastrow-question.txt \
  --vocab ACCEPT,REJECT \
  --budget 100

python3 cli/jastrow.py --print add 0 --label clean --payload "..."
```

After inputs are registered:

```bash
python3 cli/jastrow.py report 0 --worst 8
```

This should show the inputs even before probes exist.

## 3. Submit probes asynchronously

```bash
python3 scripts/submit_probes.py \
  --spec 0 \
  --k 5 \
  --manifest runs/bradbury-probes.jsonl
```

The script writes one JSON line per transaction:

```json
{"tx_hash":"0x...","spec_id":0,"input_id":2,"label":"spaced","round":1}
```

If the process stops, rerun it with a new manifest or inspect the old manifest
before continuing. Do not guess which transactions were sent.

## 4. Build the receipt report

Get the spec hash:

```bash
genlayer call 0xYOUR_CONTRACT get_spec --args 0
```

Then collect receipts:

```bash
python3 scripts/receipt_report.py runs/bradbury-probes.jsonl \
  --address 0xYOUR_CONTRACT \
  --spec 0 \
  --title "Campaign rule v3" \
  --spec-hash YOUR_SPEC_HASH \
  --vocabulary ACCEPT,REJECT \
  --out web/report.json
```

If some transactions are still pending, wait and rerun the collector. The
manifest is the source of truth.

## 5. Sanity check the result

Before publishing:

- `clean` should be near zero
- `missing` should be near zero
- at least one ambiguous input should be clearly above zero
- `MALFORMED` should be rare
- `UNDETERMINED` should be reported, not hidden
- `validator_set_size` and `distinct_leaders` should be present when receipts
  expose them

Then run:

```bash
python3 scripts/check_report.py web/report.json
```

## 6. Commit the report on chain

Use the `report_hash`, `evidence_root`, and consensus counts printed by
`receipt_report.py`:

```bash
genlayer write 0xYOUR_CONTRACT commit_report \
  --args 0 REPORT_HASH EVIDENCE_ROOT https://YOUR_VERCEL_URL/report.json 40 ACCEPTED_COUNT UNDETERMINED_COUNT
```

## 7. Embed the report in the page

```bash
python3 scripts/embed_report.py web/report.json \
  --contract 0xYOUR_CONTRACT \
  --network "GenLayer Bradbury testnet" \
  --site https://YOUR_VERCEL_URL
```

Then rebuild:

```bash
npm run build
make bundle
```

## 8. Fill costs

Fill `COSTS.md` from receipts. Do not use estimates for the final submission.

## 9. Push and deploy

```bash
git remote add origin https://github.com/Zhekinmaksim/jastrow.git
git push -u origin main
vercel --prod
```

If Vercel is connected to the GitHub repo, a push to `main` can deploy
automatically. The project uses `vercel.json`: install command `npm install`,
build command `npm run build`, output directory `dist`.
