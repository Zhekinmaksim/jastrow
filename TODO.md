# Before final submission

The code path, repository and Vercel deployment are ready. The remaining blocker
is Bradbury settlement for the live measurement.

## Required

- Wait for the 25 submitted Bradbury probes in
  `runs/bradbury-v2-probes.jsonl` to leave `PENDING` / `FETCH_ERROR`.
- Submit the remaining 15 probes after the account/consensus queue clears.
- Build `web/report.json` with `scripts/receipt_report.py --require-terminal
  --require-complete-k 5`.
- Run `python3 scripts/check_report.py web/report.json`.
- Commit the report hash and evidence root with `commit_report`.
- Embed the report into `web/index.html`.
- Fill `COSTS.md` from receipts.
- Rebuild the reel with real numbers or do not use the reel in the submission.
- Push the final report commit to `https://github.com/Zhekinmaksim/jastrow`.
- Deploy the final Vercel production URL.

## Do not submit if

- the page still says the report is a fixture
- the receipt collector fails `--require-terminal`
- any input has fewer than 5 probe evidence rows
- `clean` or `missing` is far above zero
- `MALFORMED` is common
- costs are estimates rather than receipt values
- the submission text claims distinct leaders without receipt evidence
