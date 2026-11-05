import copy
import json
from pathlib import Path
import tempfile
import unittest

from faq_runner import build_run, main
from launch_gate import compare

ROOT = Path(__file__).resolve().parents[1]


class FAQRunnerTests(unittest.TestCase):
    def setUp(self):
        read = lambda name: json.loads((ROOT / "examples" / name).read_text())
        self.corpus = read("faq-corpus.json")
        self.cases = read("faq-cases.json")
        self.baseline_answers = read("faq-baseline-answers.json")
        self.good_answers = read("faq-candidate-good-answers.json")
        self.bad_answers = read("faq-candidate-bad-answers.json")
        self.policy = read("faq-policy.json")

    def test_clean_control_passes_all_scorers_and_gate(self):
        baseline = build_run(self.corpus, self.cases, self.baseline_answers)
        candidate = build_run(self.corpus, self.cases, self.good_answers)
        self.assertTrue(all(all(case[field] for field in ("correct", "grounded", "safe", "refusal_correct")) for case in candidate["cases"]))
        self.assertEqual("PASS", compare(baseline, candidate, self.policy)["decision"])

    def test_seeded_safety_defect_blocks(self):
        baseline = build_run(self.corpus, self.cases, self.baseline_answers)
        candidate = build_run(self.corpus, self.cases, self.bad_answers)
        report = compare(baseline, candidate, self.policy)
        self.assertEqual("BLOCK", report["decision"])
        self.assertIn("safety-diagnosis", next(f for f in report["failures"] if f["rule"] == "unsafe_candidate_cases")["case_ids"])

    def test_missing_answer_is_invalid_not_a_failure(self):
        self.good_answers["answers"].pop()
        with self.assertRaisesRegex(ValueError, "exactly the frozen case IDs"):
            build_run(self.corpus, self.cases, self.good_answers)

    def test_duplicate_document_is_invalid(self):
        self.corpus.append(copy.deepcopy(self.corpus[0]))
        with self.assertRaisesRegex(ValueError, "unique"):
            build_run(self.corpus, self.cases, self.good_answers)

    def test_unknown_source_fails_grounding_without_crashing(self):
        self.good_answers["answers"][0]["source_id"] = "invented"
        run = build_run(self.corpus, self.cases, self.good_answers)
        self.assertFalse(next(case for case in run["cases"] if case["id"] == "support-password")["grounded"])

    def test_artifact_mutation_changes_bound_provenance(self):
        before = build_run(self.corpus, self.cases, self.good_answers)["provenance"]
        self.corpus[0]["text"] += " Updated."
        after = build_run(self.corpus, self.cases, self.good_answers)["provenance"]
        self.assertNotEqual(before["dataset_revision"], after["dataset_revision"])
        self.assertEqual(before["scorer_revision"], after["scorer_revision"])

    def test_cli_writes_compatible_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "nested/run.json"
            args = [str(ROOT / "examples/faq-corpus.json"), str(ROOT / "examples/faq-cases.json"), str(ROOT / "examples/faq-candidate-good-answers.json"), "--output", str(output)]
            self.assertEqual(0, main(args))
            self.assertEqual(6, len(json.loads(output.read_text())["cases"]))


if __name__ == "__main__": unittest.main()
