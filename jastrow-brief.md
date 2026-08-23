# Jastrow - project brief

Hand this file to a fresh chat. It contains everything needed to start.

Joseph Jastrow published the duck-rabbit in 1899: a drawing that two competent
viewers see as two different animals, where the disagreement is a property of
the drawing rather than a failure of either viewer. Wittgenstein later used it
for the same point. That is exactly what this project measures, and the figure
is the logo. Albert's closing line in the AMA was that reality is not black and
white, it is blurry; this measures the blur.

Check the name is free in the ecosystem before committing to it. Alternatives
that carry the same idea: MOIRE, the interference pattern that appears only
when two near-identical grids are laid over each other; SORITES, the heap
paradox, which is the canonical name for vagueness itself.

---

## What is being built

A pre-flight check for anyone who writes a specification that LLM validators
will have to judge against.

You submit the adjudication question you intend to ship, plus the inputs you
expect to see. Jastrow runs each input past independent validators and reports
where they disagreed. Disagreement is ambiguity, and ambiguity is the money you
will lose to appeals once your contract is on mainnet.

The output is not advice. It is a per-input divergence rate and the list of
exact inputs that split the judges, which are precisely the cases your
specification fails to cover.

## Why this, from the AMA

Three things in that half hour point at the same hole.

**Underspecification is a named, shipped failure.** Asked why Rally's AI jury
gave inconsistent results, Albert said there was something underspecified on
the Intelligent Contract that was causing the LLMs to make up an extra rule. He
then added the other half: it can also be that whoever created the campaign did
not specify things properly, and gave the example of a hashtag with a space in
the middle. So the failure happens both at the contract layer and at the
end-user layer, and in both cases nobody found out until real judgments came
back wrong.

**Simulation before staking is already the informal practice.** Talking about
validators picking models, he said you can test the result before you actually
go through the process, and simulate beforehand without putting any stake on
the line. That is exactly this product, except no one has built it as a thing
you can point at a spec.

**The founder's own framing is disambiguation.** He describes GenLayer as a
disambiguation machine and says the value is automating judgment where the
answer is ambiguous. A tool that tells you how ambiguous your question is
before you pay for judgment is the natural instrument for that machine.

## Why it cannot exist on any other chain

Measuring whether independent judges would disagree requires independent
judges. One model cannot do it: a model is self-consistent, ask it twice and it
agrees with itself, and asking it to rate its own clarity produces a number
about its confidence rather than about the population.

The measuring instrument here is the validator set itself. That is the whole
argument, and it is unusually clean: the thing being sold is a property of
GenLayer's consensus that has no analogue anywhere else.

## Why it is not "AI decides X"

The contract does not judge anything. It collects judgments and counts them.

Every probe returns a normalised answer under a deliberately permissive
equivalence principle, one that accepts any well-formed response rather than
demanding agreement. This is honest rather than a loophole: the contract is not
claiming the answer is correct, it is recording what one validator said. The
verdict Jastrow produces is arithmetic over those recordings, computed in a
deterministic stage, and it is a rate rather than an opinion.

## The key mechanic: divergence sampled across transactions

This is the part to get right before anything else is written.

A contract cannot see its own validators disagreeing. Disagreement surfaces as
an appeal or a failed transaction, not as a value the contract can read. So
divergence has to be sampled a different way.

Each probe is its own transaction, and each transaction draws a different
leader from the validator set. Run the same input k times as k separate
transactions and you get k answers from k different validators. Divergence
across those recorded answers is a direct sample of the disagreement the spec
would cause on chain.

Concretely:

- **Stage A, deterministic**: pin the spec hash, the input, and the answer
  vocabulary the judge is allowed to use.
- **Stage B, non-deterministic**: one judge call. Returns the spec hash, a
  normalised answer from the fixed vocabulary, and a hash of the reasoning.
  The equivalence principle accepts any well-formed object, so the probe
  records rather than adjudicates.
- **Stage C, deterministic**: append the answer to that input's tally.

Then a separate deterministic call computes the report: per-input divergence,
which answer split the field and how, and an overall score. No LLM touches the
report.

## Architecture sketch

State:

- `specs`: submitted specification text, its hash, its answer vocabulary, owner
- `inputs`: per spec, the cases being probed
- `probes`: every recorded answer with the spec hash and input it belongs to
- `reports`: computed divergence per input and per spec, with the sample size

Flow:

1. Submit a spec: the question, the answer vocabulary, the inputs to probe
2. Fund and run probes, k per input, each its own transaction
3. Compute the report deterministically
4. Read: which inputs split the judges, and by how much

## Probe inputs: generated or supplied

Two modes, and the second is the one that sells it.

**Supplied.** The builder brings their own edge cases. Honest, cheap, and the
right default.

**Generated.** A separate adjudicated step asks for edge cases that sit near
the boundary of the spec, then those are probed. This is more impressive and
more dangerous: generation is itself a judgment, so it needs its own consensus
and it can quietly bias the result toward cases one model finds interesting.
Build supplied first. Treat generated as a stretch goal, and if it ships, label
its output as generated so nobody mistakes it for a neutral sample.

## Known problems to solve before writing code

**Validator set size on the testnet.** The whole method assumes k transactions
draw meaningfully different leaders. On a small Bradbury validator set the
sample may be far less independent than the arithmetic implies. Check the
actual set size early. If it is small, say so in the report rather than
reporting a divergence rate that pretends to more independence than it has.
This is the single biggest threat to the project being honest, and stating it
plainly is better than being caught by a reviewer.

**Cost.** Every probe is a transaction. Twenty inputs at five probes each is a
hundred transactions for one report. Work out the number and put it in the
submission before a reviewer asks. The counterargument is real and should be
made explicitly: this is cheaper than discovering the same ambiguity through
appeals on mainnet. It also aligns with the developer fee, since Albert said
builders take 10 to 20 percent of the gas they generate, and this design
generates a lot of it.

**Prompt injection through the submitted spec.** The spec is user-supplied and
goes into the prompt. Fence it, label it as material under examination, and
carry the same defence as before: an injection has to move the answer
identically across independent validators or it merely shows up as divergence,
which is the thing being measured anyway. This project is unusually resistant
here, and that is worth one sentence in the submission.

**Answer vocabulary discipline.** Divergence is only meaningful over a closed
vocabulary. Free text answers cannot be counted. Force the submitter to declare
the enum, and refuse specs that do not have one.

## Scope for one week

- Intelligent Contract: specs, inputs, probes, deterministic report
- Supplied inputs only; generated inputs only if there is time left
- CLI to submit a spec, run probes, and print the report
- Page showing a report: the divergence bar per input, the split of answers,
  and the inputs sorted worst first

The frontend must be minimal but working. A read-only report page that renders
one real measurement beats a half-built interactive one.

## Before writing any code

Check the current SDK at `https://sdk.genlayer.com/main/_static/ai/api.txt` and
confirm `gl.nondet.exec_prompt`, `gl.eq_principle.prompt_comparative`, storage
types, and whether the testnet runner is still on the 0.2.x API or has moved to
0.3. The Nomic repo has the compatibility notes and they carry over directly.

Reuse from Nomic rather than rewriting: the three-stage shape, the fencing
helper, the verdict normaliser, the off-chain harness that stubs the runtime,
and `scripts/calibrate.py`, which already builds real prompts and measures
cross-model disagreement. Jastrow is essentially that script turned into a
product and moved on chain, which is why it is a week of work and not a month.

## Token economics, and why this project needs no token

Every number below is stated by the CEO in the AMA. They are worth quoting in
the submission because they turn the pitch from a nice idea into arithmetic.

- **Builders take 10 to 20 percent of the gas they generate.** So a design that
  runs a hundred transactions per report is not an embarrassment about cost, it
  is the revenue model. Say this out loud rather than apologising for the
  transaction count.
- **Appeals are paid for in GEN, and slashing is real**: roughly 5 percent for
  a deterministic violation, meaning a validator caught cheating, and 1 percent
  for idleness, split 80/20 between the validator's self-stake and delegated
  stake. The transcript garbles the exact cheating figure, so cite it loosely or
  check it against the papers when they land.
- **The 42 GEN delegation minimum is anti-spam and nothing else**, so do not
  build any economic story on it.
- **The validator set is capped near 1000 and may go to 1500.** This matters
  directly: it is the population being sampled, and the reason a divergence rate
  means anything at all.

Jastrow itself should not have a token. It sells a measurement, it holds no
value, and it settles no disputes, so a token would be decoration. Portal
reviewers see a lot of decoration. Saying plainly that the project needs no
token, and that its economics are entirely the developer fee on gas it
genuinely generates, is a differentiator rather than a gap.

## Timing

As of the AMA, a run of papers was promised within days, including tokenomics
as roughly the fifth of them, plus a refreshed white paper and simulation code.
Those had not appeared at the time of writing this brief, and the public blog
had gone quiet for months, so treat the timeline as slipping alongside Clark.

Two consequences. First, do not build anything that depends on numbers the
papers will fix. Second, the day those papers drop is the single best
distribution window this ecosystem will offer for a while, and a same-day
technical read of them costs a few hours and does not compete with build time.

## Submission

Category: Projects.

Open with the measurement, not with the problem. Two sentences that a reviewer
reads first:

> Ambiguity in a specification is invisible until validators disagree about it,
> and by then it has already cost you appeals. Jastrow measures it beforehand,
> by asking independent validators the same question and counting how often
> they part company, which is a measurement only this chain can take.

Then the Rally example, in one line, because it is the ecosystem's own
documented instance of the failure.

Portal constraints in force: two project submissions per user per week;
milestones open only to highlighted projects, so highlighting is the goal;
demo videos and live demos earn points and speed review; generic AI-written
intros slow review down.

## Style constraints

- Short dashes only, never em-dashes or en-dashes, in code, docs and copy
- All code, documentation and public-facing material in English
- First person singular for a solo project
- Pick a project-appropriate aesthetic. Not the Dry Ink system, that belongs to
  the Utexo Frontier Field Notes series. Not the VT100 terminal either, that is
  now Nomic's. A measurement instrument wants its own look, and the duck-rabbit
  gives it one that needs no explaining
- For frontend work follow the frontend-design skill at
  /mnt/skills/public/frontend-design/SKILL.md and the anti-AI-slop principles
  from impeccable.style

## Context worth carrying over

- Nomic is built and awaiting deploy; see its DEPLOY.md before starting anything
  new, since a deployed project beats a second undeployed one
- The three-stage adjudication pattern comes from `acp-adjudicator` and was
  reused in Nomic. Jastrow reuses the shape, not the code
- GenLayer is releasing a run of papers within days of this AMA, including
  tokenomics, plus a refreshed white paper. Mainnet is still targeted at Q4,
  Bradbury ships before Clark
