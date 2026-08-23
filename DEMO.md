# Demo recording runbook

Use this path for the submission video. It shows the killer feature without
waiting for Bradbury confirmations, then shows the live contract path as proof
that the frontend really calls GenLayer.

## 1. Open with the contract check

Show the landing page:

```text
https://jastrow.vercel.app
```

Start at “Contract spec check”. Say:

```text
Jastrow checks whether a GenLayer contract spec is decidable before deploy.
It returns the concrete inputs that split validators, not just an average.
```

Tie the name to the product:

```text
Jastrow is named after the duck-rabbit illusion: one drawing, two valid
readings. Contract specs can fail the same way: one input, two validator
readings. Jastrow finds those duck-rabbit inputs before deploy.
```

Run the instant demo command:

```bash
python3 cli/jastrow.py run examples/demo-ambiguous-report.json --threshold 0.25
```

Expected output:

```text
AMBIGUOUS
  divergence at or above 0.250: in-image=0.480, in-reply=0.320
```

This exercises the same CI gate used for real receipt-backed reports. The file
is explicitly marked as demo evidence, so do not present it as chain evidence.

## 2. Show the real report surface

Scroll to “Every input, worst first”.

Point out:

- clean and missing should be boring;
- the top row is the clause to rewrite;
- `MALFORMED`, `OUT_OF_VOCAB`, and `UNSETTLED` are separate failure classes.

If the page still says fixture, say that the live Bradbury receipt collection
is still settling and the final publishable report is gated by
`--require-terminal --require-complete-k 5`.

## 3. Show the live contract call

Use the “Live contract call” panel:

1. Connect wallet.
2. Pick an input.
3. Click “Run probe”.
4. Show that the UI returns a transaction hash immediately.

Do not wait on camera for finalization. The point is that the frontend calls the
contract and handles the lifecycle; GenLayer settlement can take time.

## 4. Show what makes it different

Scroll to:

- “Not GLBench”: GLBench judges validators; Jastrow judges the spec.
- “Put GEN behind the claim”: bonded challenge loop in source.
- “Why specs split”: taxonomy of repair classes.
- “The ecosystem benchmark”: 1,249 GitHub repositories and 826 contract
  addresses extracted for the next corpus run.

## 5. Do not claim these yet

Do not say:

- the embedded page report is the final live measurement while it is still a fixture;
- the current Bradbury address has challenge-market methods;
- the full 1,329-project corpus has already been measured by Jastrow.

Say instead:

```text
The product is ready. The remaining live-data step is waiting for Bradbury
receipts, then replacing the fixture with the receipt-backed report.
```
