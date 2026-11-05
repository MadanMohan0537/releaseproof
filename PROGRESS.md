# Existing-project improvement record

## 2026-11-05 — ReleaseProof

- Re-inspected source, 27 tests, CI, README, feature record, history and Project Lab extensions.
- Shipped the highest-priority unbuilt feature: a deterministic local FAQ evaluation adapter.
- Added a frozen four-document corpus, six-case rubric and clean/defective answer controls.
- Bound corpus, rubric and scorer source digests into evaluation provenance.
- Clean control: 6/6 scored cases and PASS. Seeded medical-safety defect: 5/6 and BLOCK with four findings.
- Added seven regression tests; 34 tests now pass locally.
- Next repository in the rotation: VerdictLens (#2).
- Next ReleaseProof priority: repeated-run noise calibration, followed by scenario-duplication auditing.

## 2026-10-20 — ReleaseProof

- Inspected baseline source, examples, 19 tests, CI, README, feature record and catalog.
- Shipped evaluation provenance compatibility gate; no new repository created.
- Baseline/candidate dataset, scorer and rubric revisions must match when supplied.
- Required metadata can be enforced by policy; legacy reports remain explicitly unverified.
- Added eight regression tests, including three independent context mutations.
- Next repository in the improvement rotation: VerdictLens (#2).
- Next ReleaseProof priority: representative local evaluation adapter, then repeated-run noise study.

