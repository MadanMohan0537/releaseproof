"""Run ReleaseProof's deterministic repeated-run noise experiment."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from launch_gate import repeated_run_noise_study


PROVENANCE={"dataset_revision":"noise-fixture-v1","scorer_revision":"noise-labels-v1","rubric_revision":"noise-rubric-v1"}


def repeated_fixture(template, failures, prefix):
    runs=[]
    for index,failure_count in enumerate(failures):
        run=copy.deepcopy(template)
        run["version"]=f"{prefix}-{index+1}"
        run["provenance"]=dict(PROVENANCE)
        for case in run["cases"]:
            case["correct"]=True; case["grounded"]=True; case["safe"]=True; case["refusal_correct"]=True
        for case in run["cases"][:failure_count]:
            case["correct"]=False
        runs.append(run)
    return runs


def build_report(template):
    calibration=repeated_fixture(template,[0,1,0,1,0,1,0,1],"calibration")
    control=repeated_fixture(template,[1,0,1,0,1,0,1,0,1,0],"control")
    candidate=repeated_fixture(template,[2,2,1,2,2,1,2,2,1,2],"candidate")
    report=repeated_run_noise_study(calibration,control,candidate,false_block_target=.1)
    report["acceptance_passed"]=report["heldout_target_met"] and report["systematic_regression"]
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    template=json.loads(args.template.read_text(encoding="utf-8"))
    report=build_report(template)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"heldout_false_block_rate":report["heldout_false_block_rate"],
      "candidate_quality_delta":report["candidate_quality_delta"],
      "systematic_regression":report["systematic_regression"],
      "acceptance_passed":report["acceptance_passed"]},indent=2))
    return 0 if report["acceptance_passed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
