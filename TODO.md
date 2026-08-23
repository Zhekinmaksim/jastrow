# Before final submission

The code path is ready. The remaining items need live chain data or account
access.

## Required

- Deploy the current `contracts/jastrow.py` to Bradbury.
- Register the reference battery.
- Submit probes with `scripts/submit_probes.py`.
- Build `web/report.json` with `scripts/receipt_report.py`.
- Run `python3 scripts/check_report.py web/report.json`.
- Commit the report hash and evidence root with `commit_report`.
- Embed the report into `web/index.html`.
- Fill `COSTS.md` from receipts.
- Rebuild the reel with real numbers or do not use the reel in the submission.
- Push to `https://github.com/Zhekinmaksim/jastrow`.
- Deploy the Vercel production URL.

## Do not submit if

- the page still says the report is a fixture
- `clean` or `missing` is far above zero
- `MALFORMED` is common
- costs are estimates rather than receipt values
- the submission text claims distinct leaders without receipt evidence
