# Feature decision record

## Local deterministic FAQ adapter — shipped November 5, 2026

**Problem/trigger:** recorded quality labels had no reproducible origin, so a passing gate could not be independently reconstructed.

**Behavior:** validate a frozen corpus, rubric and complete answer set; score required facts, expected-source grounding, forbidden phrases and refusal behavior; emit a ReleaseProof-compatible run. Bind corpus, rubric and scorer source digests into provenance.

**Dependencies:** Python standard library and synthetic JSON fixtures only. No service, credential or paid API.

**Success test:** the clean six-case control scores 6/6 and passes. A seeded diagnosis/dosage answer scores 5/6 and blocks on aggregate regression, unsafe case, safety-cohort quality and safety-cohort regression. Missing answers and duplicate document IDs fail closed.

**Risks/tradeoffs:** substring scoring is inspectable but rejects some valid paraphrases and can accept carefully worded nonsense. Frozen synthetic cases demonstrate reproducibility, not production representativeness or scorer validity.

## Evaluation provenance compatibility — shipped October 20, 2026

**Problem/trigger:** identical case IDs can hide a changed scorer, rubric or dataset.
Comparing those scores as a model regression is misleading.

**Behavior:** compare three declared revisions and block mismatches or one-sided
metadata. Policy can require declarations. Legacy absent metadata is unverified.
JSON/HTML and content hashes expose the comparison context.

**Dependencies:** immutable revision naming by evaluation producers. No service or
credential dependency. Small deterministic extension.

**Success test:** matched context passes; each of three independent revision
mutations blocks perfect candidate scores; required missing context blocks.
The reproducible demo pairs one matched control with one changed-scorer treatment.

**Risks/tradeoffs:** self-declared revisions can be inaccurate; immutable artifacts
and signatures are deferred. Strict equality forces rescoring both runs after a
rubric change, increasing evaluation cost. Optional legacy support avoids breaking
existing consumers but cannot establish their comparability.

## Further additions — prioritized, not implemented

| Priority | Problem and behavior | Dependencies | Success test | Risks/tradeoffs |
|---|---|---|---|---|
| P1 | Run noise causes false blocks; compare repeated baseline/candidate batches. | Repeated-run fixtures | Predeclared false-block target on held-out simulations. | Calibration cost and correlated runs. |
| P1 | Revision claims can lie outside the local adapter; add signed execution manifests. | Signing identity, artifact manifest | Tampered artifact or manifest is rejected. | Key management and signatures still do not prove scorer validity. |
| P2 | Duplicate scenarios inflate coverage; audit scenario tags and exact duplicates. | Scenario metadata | Seeded duplicate inflation cannot clear coverage debt. | Semantic duplicates need human review. |
| P2 | Reviewers cannot track release trends; export comparable historical reports. | Provenance-compatible report store | Mixed-scorer histories are separated, never silently pooled. | Selective history can mislead. |
| P2 | Exact facts penalize valid paraphrases; add a reviewed equivalence-set scorer and disagreement queue. | Human-reviewed aliases | Held-out valid paraphrases pass without increasing seeded false accepts. | Alias lists can overfit and need governance. |
| P3 | Synthetic FAQs may not represent real traffic; evaluate a versioned public FAQ corpus by cohort. | Public corpus, usage-informed taxonomy | Holdout accuracy and critical-cohort coverage meet predeclared floors. | Public questions differ from production traffic. |

## Paired regression evidence

**User/trigger:** a release owner receives a candidate score close to baseline and needs to know which cases changed.

**MVP behavior:** pair by case ID; reject incomplete comparisons; report improved, regressed and unchanged outcomes plus a seeded descriptive bootstrap interval. Implemented in `compare` and `paired_interval`.

**Dependencies:** fixed case IDs, frozen cohort tags, trustworthy independent quality labels. Relative effort: medium beyond a metric-only baseline.

**Validation:** seeded critical-cohort regressions must block even when aggregate quality remains above its floor; reordered case lists must have identical paired statistics; repeated calls must produce identical reports. These are correctness checks, not measured reductions in human diagnosis time.

**Tradeoff:** reproducible resampling is easy to inspect, but it omits repeated model-run variability. Reject statistical-safety claims until a repeated-run study and independent scoring are available. A bootstrap interval never overrides a safety failure.

## Critical-cohort coverage debt

**User/trigger:** an evaluation owner sees a passing run after critical tests were omitted.

**MVP behavior:** policy declares critical cohort names and minima independent of the observed data. Missing cohorts have explicit debt and block the release. Implemented in `compare`.

**Dependencies:** reviewed cohort taxonomy and coverage policy. Relative effort: small beyond an aggregate baseline.

**Validation:** adding a completely absent required cohort must block perfect recorded runs. Dropping a case from only one run is invalid input; dropping it from both can still breach a declared minimum.

**Tradeoff:** counts are transparent but can be gamed with duplicate scenarios. Defer claims of broad coverage until scenario diversity is audited.

## Why these first

They address two concrete ways a release can look safe: aggregate scores conceal critical regressions, and absent cases never contribute errors. Both have falsifiable synthetic tests and integrate with the baseline release decision. A dashboard alone would not change that decision. Live execution, better scorer provenance and real representative datasets should precede further UI investment.


