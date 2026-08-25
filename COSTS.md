# What a report costs

Every probe is a transaction. That is the design, not an accident, and the
number belongs in the open rather than buried.

## Transaction arithmetic

For a specification with `i` inputs at `k` probes each:

```
transactions = 1 registration + i input additions + (i * k) probes + 1 report commitment
```

Only the probes carry inference. Registration, input additions and the commitment
are deterministic and touch no model.

| specification | inputs | k | probes | total transactions |
| --- | --- | --- | --- | --- |
| reference battery | 8 | 5 | 40 | 50 |
| reference battery, thorough | 8 | 9 | 72 | 82 |
| a real campaign rule | 20 | 5 | 100 | 122 |
| a real campaign rule, thorough | 20 | 9 | 180 | 202 |

Reading costs nothing. The receipt report is a JSON artifact that anyone can
audit locally with `scripts/check_report.py`. `commit_report` exists only to
anchor that report hash and evidence root on chain, and it is one transaction
however large the specification is.

## Why the transaction count is the point

The alternative to a hundred probe transactions is discovering the same
ambiguity through appeals on mainnet, with bonds posted, disputes to answer and
users who already got the wrong verdict. Appeals are paid for in GEN and
slashing is real. A hundred probes bought in advance is the cheap end of that
trade.

It also aligns with the network rather than apologising to it. The AMA states
that builders take 10 to 20 percent of the gas they generate, so a design that
generates gas honestly is the revenue model rather than an embarrassment about
cost. Jastrow needs no token for the same reason: it sells a measurement, holds
no value and settles no disputes, and its economics are entirely the developer
fee on gas it genuinely generates.

## Where the cost can be cut, and where it cannot

**k is the honest lever and it is expensive.** The resolution of D at small k
is coarse, and the coarseness is arithmetic rather than opinion. Over two
tokens:

| k | values D can take |
| --- | --- |
| 3 | 0.000, 0.444 |
| 4 | 0.000, 0.375, 0.500 |
| 5 | 0.000, 0.320, 0.480 |
| 7 | 0.000, 0.245, 0.408, 0.490 |
| 9 | 0.000, 0.198, 0.346, 0.444, 0.494 |

Doubling k roughly halves the gap between detents and doubles the bill. k = 5
is the default because it distinguishes "unanimous" from "split" and from
"badly split", which is what an author needs in order to know which clause to
rewrite. Anyone who needs to tell 0.32 from 0.40 has to pay for k = 9, and the
report publishes the achievable values so nobody spends that money by accident.

**Screening is the cheap lever.** Run the whole battery at k = 3, which cannot
publish a rate but can tell unanimous apart from split, then spend the rest of
the budget only on the inputs that moved. The probe command takes `--input` for
exactly this.

**Rerunning is not a lever.** The same input probed twice in one transaction
would draw one leader and produce one draw, which is why the contract refuses
to batch. The transaction count is the sample size; they are the same number.

## GEN figures

The live Bradbury report is built from `runs/bradbury-v2-publish.jsonl`, a clean
40-transaction publish manifest with exactly five usable receipt-backed
observations for each of the eight inputs. The report hash is
`480bb949d6576b7b2900826ce03684942b3ebffb61a1113d7a72eb941fd3187b`.

The probe cost below is read from `web/report.json`:

| item | transactions | GEN |
| --- | ---: | ---: |
| probe, one transaction, mean over this run | 1 | 0.00314348753696362375 |
| reference probe battery | 40 | 0.12573950147854495 |

This is the probe battery only. It does not claim a registration, input-addition
or `commit_report` cost unless that transaction is present in the receipt
evidence. No number in this section is extrapolated from an estimate.

The earlier gate run below is archived evidence from the first mechanism. These
numbers are receipt data, not estimates:

| item | transaction | GEN |
| --- | --- | ---: |
| rejected deploy using the archive's invalid runner | `0x9162…b7af` | 0.0093431834464675 |
| Jastrow deployment | `0x9a1e…b55c` | 0.00935535174506265 |
| `register_spec` | `0xd122…782a7` | 0.00081354990003075 |
| `add_input` | `0xb412…4fafd` | 0.0007872319271808 |
| comparative probe, ending `NONDET_DISAGREE` | `0x5c94…ae0` | 0.0030255926619977 |
| non-comparative gate deployment | `0x1b24…45ff` | 0.0014623065092118 |

Do not extrapolate the failed comparative probe into a battery estimate: it did
not settle and therefore is not the unit cost of a successful sample.
