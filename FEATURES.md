# Feature decision record

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
