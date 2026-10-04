# ReleaseProof

**Release AI changes with evidence you can inspect.**

ReleaseProof compares a baseline and candidate evaluation run, checks quality, critical scenario coverage, latency and cost, and produces a clear **PASS** or **BLOCK** decision with case-level evidence.

Built for developers and AI product teams evaluating prompt, model or configuration changes. Runs locally with Python’s standard library: no API key, external service or third-party Python dependency required.

**Project status:** working portfolio MVP using eight synthetic example cases. Bring results from your own evaluation runner to assess a real application.

## Choose the right release-evidence tool

ReleaseProof consumes evaluation results you already have. It does not call a model, run a retrieval pipeline or generate responses. Use a separate evaluation runner to produce comparable baseline and candidate JSON, then apply the policy here.

Start with [example inputs](examples/), inspect the policy and run the CLI from the quick start. Before adopting a result, confirm that case identifiers, critical slices, latency units and cost units align across the two runs. A PASS applies to this evidence and policy; it does not guarantee behavior outside the evaluated cases.

See [FEATURES.md](FEATURES.md) for the feature inventory and [tests](tests/) for gate behavior, including blocked regressions and malformed input.

## Why it exists

An overall accuracy score can look healthy while a small, important group of scenarios gets worse. A release can also appear successful because its hardest tests were omitted.

ReleaseProof checks both the aggregate result and explicitly declared critical cohorts. Every comparison uses matching case IDs, and missing results are rejected rather than counted as successes.

### An example: good average, bad release

The included failing candidate passes seven of eight cases. Its aggregate success rate is **87.5%**, above the configured **80%** floor. But its critical safety cohort drops from **100% to 50%**.

| Measure | Baseline | Candidate | Result |
|---|---:|---:|---|
| Overall case success | 100% | 87.5% | Within aggregate policy limits |
| Critical safety cohort | 100% | 50% | Below quality floor and allowed regression |
| Release decision | — | **BLOCK** | Critical failures cannot hide in the average |

These numbers come from the supplied synthetic fixtures, not a measured production deployment.

## Quick start

Requires **Python 3.11 or newer** and Git to clone the repository. No package installation is needed.

```bash
 git clone https://github.com/MadanMohan0537/releaseproof.git
 cd releaseproof
 python -m unittest discover -s tests -v
```

Evaluate the passing candidate:

```bash
python launch_gate.py examples/baseline.json examples/candidate-good.json \
  --policy examples/policy.json \
  --report reports/good.json \
  --html reports/good.html
```

Expected console output:

```text
PASS: 8 paired cases, 0 policy findings
```

Now try the deliberately regressed candidate:

```bash
python launch_gate.py examples/baseline.json examples/candidate-bad.json \
  --policy examples/policy.json \
  --report reports/bad.json \
  --html reports/bad.html
```

Expected console output:

```text
BLOCK: 8 paired cases, 2 policy findings
```

Open `reports/good.html` or `reports/bad.html` in a browser to inspect the scorecard, cohort coverage, findings, changed outputs and evidence hashes. JSON reports support downstream tooling. The failing example intentionally exits with code 1.

## Capabilities

| Capability | What it provides |
|---|---|
| Paired comparison | Match baseline and candidate cases by ID; count improved, regressed and unchanged outcomes |
| Strict case success | Require correctness, groundedness, safety and appropriate-refusal checks to all pass |
| Critical-cohort checks | Apply quality floors and regression limits to declared high-priority scenario groups |
| Coverage debt | Block when required cohorts are absent or below their minimum case count |
| Safety rule | Block any candidate case explicitly labeled unsafe |
| Operating limits | Enforce p95 latency and cost per 1,000 evaluated requests |
| Descriptive uncertainty | Produce a reproducible, seeded paired bootstrap interval |
| Reviewable evidence | Export JSON and escaped HTML, including input and policy hashes |
| CI demonstration | Test the evaluator, confirm a good example passes, and confirm a bad example blocks |

## Evaluate your own application

1. Freeze a shared test set with stable case IDs and cohort tags.
2. Execute your baseline and candidate using an independent evaluation runner.
3. Score both runs and export the JSON format below.
4. Declare critical cohorts and policy thresholds before inspecting candidate results.
5. Run ReleaseProof and investigate any blocking findings.

ReleaseProof consumes recorded results. It does **not** call an LLM, judge arbitrary text or measure latency itself. The quality of the decision depends on the quality of the supplied labels and test set.

### Evaluation run format

```json
{
  "version": "candidate-v2",
  "cases": [
    {
      "id": "billing-001",
      "cohort": "billing",
      "correct": true,
      "grounded": true,
      "safe": true,
      "refusal_correct": true,
      "latency_ms": 420,
      "cost_usd": 0.0001,
      "output": "Your invoice includes the disclosed service fee."
    }
  ]
}
```

Both runs must contain the same unique case IDs, and each case must keep its cohort tag. The four quality labels must be booleans; latency and cost must be finite, nonnegative numbers. `output` is optional text.

`refusal_correct` means the response handled refusal appropriately: answering a benign request can earn `true`, just as refusing an unsafe request can. It is not a flag indicating whether a refusal occurred.

See [the baseline fixture](examples/baseline.json) for a complete example.

### Release policy

The supplied [example policy](examples/policy.json) is:

```json
{
  "minimum_quality": 0.8,
  "maximum_quality_drop": 0.15,
  "maximum_p95_latency_ms": 600,
  "maximum_cost_per_1000_usd": 0.5,
  "critical_cohorts": {"billing": 2, "safety": 2},
  "bootstrap_samples": 2000,
  "seed": 7
}
```

A `maximum_quality_drop` of `0.15` allows a decline of at most **15 percentage points**. The quality floor and drop limit apply globally and to each declared critical cohort. Any unsafe candidate case blocks regardless of these allowances.

Declare at least one critical cohort with a positive integer minimum. Unknown policy fields are rejected so a misspelled setting cannot silently disable a check. Quality thresholds must be between 0 and 1; cost and latency ceilings must be nonnegative. Bootstrap samples default to 2,000 and must be between 100 and 10,000; the seed defaults to 0.

## Reports and exit codes

| Exit code | Meaning | Suggested CI handling |
|---|---|---|
| `0` | Recorded evaluation satisfies the policy | Continue |
| `1` | One or more policy checks block the candidate | Stop release and inspect findings |
| `2` | Inputs are invalid, unreadable, or a report cannot be written | Fix the evaluation pipeline; do not promote |

Each successful comparison exports aggregate metrics, paired statistics, cohort counts and coverage debt, blocking findings, case differences and SHA-256 hashes of the parsed inputs and policy.

The [included workflow](.github/workflows/evaluate.yml) runs the tests, exercises both example decisions and uploads reports as artifacts. To gate your application, generate its actual baseline/candidate runs and execute the same CLI in your release workflow. The example workflow demonstrates evaluator behavior; it does not evaluate a live application.

## Design and repository layout

The processing path is: validate inputs, pair case IDs, calculate metrics, apply policy, then export evidence. All evaluation logic is in [launch_gate.py](launch_gate.py); its filename is retained as the stable CLI entry point.

| Path | Purpose |
|---|---|
| `launch_gate.py` | Validation, metrics, policy decisions, CLI and HTML rendering |
| `examples/` | Synthetic baseline, passing/failing candidates and policy |
| `tests/test_launch_gate.py` | Unit and CLI behavior checks |
| `.github/workflows/evaluate.yml` | Automated tests and evidence artifacts |
| [FEATURES.md](FEATURES.md) | Feature rationale, validation criteria and tradeoffs |

### Metric interpretation

- **Case success:** all four supplied quality checks pass.
- **Latency p95:** linear interpolation of sorted observed latencies.
- **Cost per 1,000:** mean per-case cost multiplied by 1,000; this is an evaluation-set estimate, not a traffic-weighted production forecast.
- **Paired interval:** resample candidate-minus-baseline success differences by case and report the 2.5th and 97.5th percentiles. This interval is descriptive and does not override policy failures.
- **Evidence hashes:** identify parsed input content. They do not authenticate the scorer or execution environment. Case-list order affects hashes, while ID-paired statistics remain order-independent.

## Verification

**19 local tests pass.** Coverage includes critical regressions hidden by aggregate results, absent cohorts, removed and duplicate cases, changed tags, malformed labels, invalid numbers, policy typos, cost/latency breaches, order-independent pairing, deterministic reports, HTML escaping and CLI exit codes.

Run the suite with:

```bash
python -m unittest discover -s tests -v
```

The passing and blocking examples are reproducible fixtures, not evidence that the policy has been calibrated for a real product.

## Limits and next steps

A PASS means the supplied recorded evaluation met the supplied policy. It does not certify production safety.

The small synthetic dataset demonstrates control flow. Case counts do not establish scenario diversity, and repeated model-run variation, label uncertainty and correlated cases are not modeled. Small or uniform samples can yield misleadingly narrow bootstrap intervals. Use representative data and independently validated scorers before relying on release decisions.

| Status | Scope |
|---|---|
| Implemented | Paired outcomes, descriptive bootstrap evidence, critical-cohort coverage debt, policy checks, reports and example CI |
| Next | Live evaluation adapter, scorer/configuration provenance, representative test corpus and repeated-run noise study |
| Proposed | Scenario diversity checks, failure minimization, baseline promotion, release trends and PR summaries |

Only public or synthetic fixtures belong in this public repository. Original catalog reference: **AI PM Project Lab, idea #1 — Launch Gate**. The built product is **ReleaseProof**.

## Contributing

Open an issue with a concrete evaluation failure, expected behavior and a minimal synthetic example. For a pull request, explain which decision it improves, add a meaningful regression test when behavior changes, and run the existing suite. Keep new dependencies justified and separate implemented capabilities from proposals.
