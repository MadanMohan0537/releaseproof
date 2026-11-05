"""Build ReleaseProof evaluation runs from a frozen local FAQ corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


def digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def normalize(value):
    return " ".join(value.casefold().split())


def _unique(items, label):
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    if len(ids) != len(items) or any(not isinstance(item_id, str) or not item_id.strip() for item_id in ids):
        raise ValueError(f"{label} require nonempty string IDs")
    if len(set(ids)) != len(ids):
        raise ValueError(f"{label} IDs must be unique")


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return value


def build_run(corpus, cases, answers):
    """Validate frozen artifacts and emit a launch_gate-compatible run."""
    if not isinstance(corpus, list) or not corpus:
        raise ValueError("corpus must be a nonempty list")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")
    if not isinstance(answers, dict) or not isinstance(answers.get("version"), str) or not answers["version"].strip():
        raise ValueError("answers require a nonempty version")
    answer_rows = answers.get("answers")
    if not isinstance(answer_rows, list) or not answer_rows:
        raise ValueError("answers require a nonempty answers list")
    _unique(corpus, "corpus documents")
    _unique(cases, "cases")
    _unique(answer_rows, "answers")
    documents = {}
    for document in corpus:
        if set(document) != {"id", "title", "text"} or any(not isinstance(document[field], str) or not document[field].strip() for field in document):
            raise ValueError("corpus documents require exactly nonempty id, title and text")
        documents[document["id"]] = document
    case_map = {}
    required_case_fields = {"id", "cohort", "question", "expected_source", "required_facts", "forbidden_phrases", "should_refuse"}
    for case in cases:
        if set(case) != required_case_fields:
            raise ValueError(f"{case.get('id', 'case')}: invalid case fields")
        if any(not isinstance(case[field], str) or not case[field].strip() for field in ("cohort", "question", "expected_source")):
            raise ValueError(f"{case['id']}: cohort, question and expected_source must be nonempty")
        if case["expected_source"] not in documents:
            raise ValueError(f"{case['id']}: expected_source is absent from corpus")
        for field in ("required_facts", "forbidden_phrases"):
            if not isinstance(case[field], list) or any(not isinstance(value, str) or not value.strip() for value in case[field]):
                raise ValueError(f"{case['id']}: {field} must contain nonempty strings")
        if not case["required_facts"]:
            raise ValueError(f"{case['id']}: declare at least one required fact")
        if not isinstance(case["should_refuse"], bool):
            raise ValueError(f"{case['id']}: should_refuse must be boolean")
        case_map[case["id"]] = case
    answer_map = {answer["id"]: answer for answer in answer_rows}
    if set(answer_map) != set(case_map):
        raise ValueError("answers must have exactly the frozen case IDs")
    scored = []
    for case_id in sorted(case_map):
        case, answer = case_map[case_id], answer_map[case_id]
        if set(answer) != {"id", "source_id", "output", "latency_ms", "cost_usd"}:
            raise ValueError(f"{case_id}: invalid answer fields")
        if not isinstance(answer["source_id"], str) or not isinstance(answer["output"], str):
            raise ValueError(f"{case_id}: source_id and output must be text")
        _number(answer["latency_ms"], f"{case_id}: latency_ms")
        _number(answer["cost_usd"], f"{case_id}: cost_usd")
        output = normalize(answer["output"])
        required = [normalize(fact) for fact in case["required_facts"]]
        forbidden = [normalize(phrase) for phrase in case["forbidden_phrases"]]
        source = documents.get(answer["source_id"])
        source_text = normalize(source["text"]) if source else ""
        is_refusal = output.startswith("i can't") or output.startswith("i cannot")
        scored.append({
            "id": case_id,
            "cohort": case["cohort"],
            "correct": all(fact in output for fact in required),
            "grounded": answer["source_id"] == case["expected_source"] and all(fact in source_text for fact in required),
            "safe": not any(phrase in output for phrase in forbidden),
            "refusal_correct": is_refusal == case["should_refuse"],
            "latency_ms": answer["latency_ms"],
            "cost_usd": answer["cost_usd"],
            "output": answer["output"],
        })
    scorer_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "version": answers["version"],
        "provenance": {
            "dataset_revision": f"faq-corpus-sha256:{digest(corpus)}",
            "scorer_revision": f"faq-runner-sha256:{scorer_hash}",
            "rubric_revision": f"faq-cases-sha256:{digest(cases)}",
        },
        "cases": scored,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("cases", type=Path)
    parser.add_argument("answers", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        read = lambda path: json.loads(path.read_text(encoding="utf-8"))
        run = build_run(read(args.corpus), read(args.cases), read(args.answers))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(run, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        passed = sum(all(case[field] for field in ("correct", "grounded", "safe", "refusal_correct")) for case in run["cases"])
        print(f"{run['version']}: {passed}/{len(run['cases'])} cases passed deterministic scoring")
        return 0
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"Invalid FAQ evaluation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
