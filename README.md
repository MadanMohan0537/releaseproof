# Launch Gate

A dependency-free release evaluator for recorded LLM test runs. Compare a baseline and candidate on exactly the same cases, apply a versioned policy, and produce JSON plus an HTML evidence report. A healthy overall score cannot hide a missing or regressed critical cohort.

**Status:** working portfolio MVP with synthetic fixtures. This is an evaluation comparison engine, not an LLM serving app or a production safety certification.

## Run

Requires Python 3.11 or newer. No installation, API key, model download or paid service is required.

```bash
python -m unittest discover -s tests -v
python launch_gate.py examples/baseline.json examples/candidate-good.json \
  --policy examples/policy.json --report reports/good.json --html reports/good.html
python launch_gate.py examples/baseline.json examples/candidate-bad.json \
  --policy examples/policy.json --report reports/bad.json --html reports/bad.html
```

Open either HTML report locally in your browser. The good fixture exits **0**; the deliberately bad fixture exits **1**. Invalid or unreadable inputs exit **2**. The bad candidate's aggregate success is 87.5%, above the 80% floor, but its critical safety cohort falls from 100% to 50%, so the gate blocks it.

## What is implemented

- Case-ID pairing with rejection of dropped cases, duplicate IDs and changed cohort tags.
- Deterministic aggregation of supplied correctness, groundedness, safety and appropriate-refusal labels. A case succeeds only if all four checks pass. `refusal_correct` means the response handled refusal appropriately, including answering benign requests; it is not a raw refusal flag.
- Global and critical-cohort quality floors and maximum quality drops.
- A hard block for any candidate case labeled unsafe.
- Required critical-cohort case counts and an explicit coverage-debt ledger, including completely absent declared cohorts.
- p95 latency and cost per 1,000 requests limits.
- Improved/regressed/unchanged case counts and a seeded paired bootstrap interval.
- Escaped side-by-side output differences, input/policy SHA-256 hashes and reproducible reports.
- A GitHub Actions workflow running tests, checking a passing example, proving a failing example exits 1, and uploading evidence artifacts.

## Input contract

Each run is a JSON object with `version` and a nonempty `cases` list. Each case requires a unique `id`, fixed `cohort`, four boolean quality fields, nonnegative finite `latency_ms` and `cost_usd`, and optional text `output`. See `examples/baseline.json` for the complete schema.

Your independent evaluation runner must execute the model and supply quality labels, latency and cost. This MVP does **not** fabricate judgments from output text. Label provenance and calibration are your responsibility. Use public or synthetic data in public repositories.

The policy requires quality thresholds in [0, 1], nonnegative latency/cost ceilings, and at least one explicitly declared critical cohort with a positive integer minimum. Unknown policy keys are rejected so a typo cannot silently disable a rule. Bootstrap samples default to 2,000, bounded between 100 and 10,000; the random seed defaults to 0.

## Architecture and design

`versioned run files → validation → case-ID pairing → global/cohort metrics → policy decisions → JSON/HTML evidence`

All logic is local and standard-library Python. The paired interval resamples case-level candidate-minus-baseline success differences with replacement, then reports the interpolated 2.5th and 97.5th percentiles. It is descriptive evidence, not an automatic significance gate. The policy uses explicit quality and coverage criteria rather than treating an interval crossing zero as proof of safety.

Latency p95 uses linear interpolation of the observed sorted values. Cost per 1,000 is the mean per-case cost multiplied by 1,000; it is not a traffic-weighted production estimate. SHA-256 hashes identify parsed input content, not authenticated execution. JSON object key order does not affect hashes; case-list order does, while ID-paired statistics are order-independent.

## Validation and limitations

The test suite covers safety failures hidden by aggregate metrics, completely absent critical cohorts, mismatched cases, invalid numbers/labels, policy typos, latency/cost breaches, pairing order, reproducibility, HTML escaping, and CLI exit codes/artifacts.

The eight synthetic cases demonstrate control flow, not benchmark representativeness. Small samples and all-identical labels can give misleadingly narrow bootstrap intervals. Correlated cases, uncertain labels and repeated model-run variation are not modeled. Critical-cohort counts measure quantity, not scenario diversity. Calibration, live model adapters, a production golden set, repeated-run noise estimates, persistent release trends, baseline promotion and PR comments remain backlog items. Nothing here establishes clinical, legal or production safety.

## New feature extensions

1. **Paired regression evidence — implemented at MVP scope:** paired outcomes and a reproducible case bootstrap. Next validate on repeated, independently scored runs and compare triage decisions against unpaired aggregate reports.
2. **Coverage debt ledger — implemented at MVP scope:** declared critical cohorts and mandatory minimum counts. Next add deduplication and scenario diversity so duplicated cases cannot inflate confidence.
3. **Regression minimizer — proposed:** reduce a failing conversation while preserving the failure across repeated reruns. Defer until the model-run adapter exists; nondeterminism can invalidate a minimized example.
4. **Evaluation provenance manifest — proposed:** bind labels to scorer versions, execution settings and data licenses. Validate by changing one dependency and checking that old evidence becomes stale.

## Daily project series

This is project 1 of the AI PM Project Lab series. Each project receives a separate public repository and a bounded tested MVP before additional scope. A daily increment is not a claim that an original multiweek platform is production-complete. The feature backlog above distinguishes implemented from proposed work.
