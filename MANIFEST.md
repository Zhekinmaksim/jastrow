# Project manifest

## Contract and tests

| path | purpose |
| --- | --- |
| `contracts/jastrow.py` | Intelligent Contract |
| `contracts/non_comparative_probe.py` | older experiment, kept for evidence only |
| `test/harness.py` | local GenLayer stub |
| `test/test_jastrow.py` | contract tests |
| `calibration/battery.json` | reference input battery |

## Chain tooling

| path | purpose |
| --- | --- |
| `cli/jastrow.py` | wrapper around the official `genlayer` CLI |
| `scripts/submit_probes.py` | submits probes and records hashes immediately |
| `scripts/register_battery.py` | registers the reference battery without probes |
| `scripts/receipt_report.py` | builds a report from Explorer receipts and traces |
| `scripts/check_report.py` | audits report math and receipt evidence |
| `scripts/calibrate.py` | optional off-chain prompt calibration |

## Web

| path | purpose |
| --- | --- |
| `web/index.html` | report page |
| `web/src/live.js` | live wallet call and transaction lifecycle UI |
| `web/assets/` | image, icons, social card, fonts |
| `web/report.json` | current embedded report source |
| `scripts/embed_report.py` | embeds report JSON and site URL |
| `scripts/bundle.py` | standalone HTML build |
| `scripts/check_page_math.py` | checks page arithmetic against the contract |
| `vite.config.js` | Vite config for Vercel build |
| `vercel.json` | Vercel install/build/output settings |

## Reel

| path | purpose |
| --- | --- |
| `reel/` | Remotion source |
| `reel/out/` | generated video output, ignored by git |

## Docs

| path | purpose |
| --- | --- |
| `README.md` | human-readable project overview |
| `DEPLOY.md` | runbook |
| `SUBMISSION.md` | portal copy draft |
| `COSTS.md` | transaction arithmetic and receipt costs |
| `TODO.md` | remaining live-data tasks |
| `RUN-2026-08-23.md` | current Bradbury run status and archived first-gate evidence |
| `NOTICE.md` | third-party asset notices |
| `LICENSE` | MIT license |
