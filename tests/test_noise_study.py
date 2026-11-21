import copy
import json
from pathlib import Path
import tempfile
import unittest

from launch_gate import repeated_run_noise_study
from noise_study import PROVENANCE, build_report, main, repeated_fixture

ROOT=Path(__file__).resolve().parents[1]


class NoiseStudyTests(unittest.TestCase):
    def setUp(self):
        self.template=json.loads((ROOT/"examples/baseline.json").read_text())
        self.calibration=repeated_fixture(self.template,[0,1,0,1,0,1,0,1],"cal")
        self.control=repeated_fixture(self.template,[1,0,1,0,1,0,1,0,1,0],"control")
        self.candidate=repeated_fixture(self.template,[2,2,1,2,2,1,2,2,1,2],"candidate")

    def study(self):
        return repeated_run_noise_study(self.calibration,self.control,self.candidate,.1)

    def test_heldout_control_meets_false_block_target(self):
        report=self.study()
        self.assertTrue(report["heldout_target_met"])
        self.assertEqual(0,report["heldout_false_blocks"])

    def test_seeded_systematic_regression_is_detected(self):
        report=self.study()
        self.assertTrue(report["systematic_regression"])
        self.assertLess(report["candidate_quality_mean"],report["quality_threshold"])

    def test_noise_band_and_denominators_are_explicit(self):
        report=self.study()
        self.assertEqual(8,report["calibration_runs"])
        self.assertEqual(10,report["control_runs"])
        self.assertEqual(10,report["candidate_runs"])
        self.assertEqual(8,report["case_count"])
        self.assertGreaterEqual(report["allowed_quality_drop"],0)

    def test_study_is_deterministic(self):
        self.assertEqual(self.study(),self.study())

    def test_case_or_cohort_drift_is_rejected(self):
        self.control[0]["cases"][0]["cohort"]="changed"
        with self.assertRaisesRegex(ValueError,"identical case IDs"):
            self.study()

    def test_provenance_drift_is_rejected(self):
        self.candidate[0]["provenance"]["scorer_revision"]="changed"
        with self.assertRaisesRegex(ValueError,"identical evaluation provenance"):
            self.study()

    def test_invalid_study_sizes_and_target_are_rejected(self):
        with self.assertRaises(ValueError): repeated_run_noise_study(self.calibration[:2],self.control,self.candidate,.1)
        with self.assertRaises(ValueError): repeated_run_noise_study(self.calibration,self.control[:2],self.candidate,.1)
        with self.assertRaises(ValueError): repeated_run_noise_study(self.calibration,self.control,self.candidate,0)

    def test_fixture_resets_quality_and_preserves_safe_labels(self):
        run=repeated_fixture(self.template,[2],"x")[0]
        self.assertEqual(PROVENANCE,run["provenance"])
        self.assertEqual(2,sum(not case["correct"] for case in run["cases"]))
        self.assertTrue(all(case["safe"] for case in run["cases"]))

    def test_cli_writes_accepted_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"nested/noise.json"
            self.assertEqual(0,main([str(ROOT/"examples/baseline.json"),"--output",str(output)]))
            report=json.loads(output.read_text())
            self.assertTrue(report["acceptance_passed"])


if __name__=="__main__": unittest.main()
