#!/usr/bin/env python3
"""Replay score-targeted process review on the public PRM800K test split."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path


DATA_SHA256 = "6b172efa884ac8341a946dd82e06947c135b7254109fb3f7aa907c715d98aaad"
SOURCE_URL = (
    "https://github.com/openai/prm800k/blob/main/prm800k/data/phase2_test.jsonl"
)
Observation = tuple[str, float, bool]


def fix_fracs(value: str) -> str:
    parts = value.split("\\frac")
    rebuilt = parts[0]
    for part in parts[1:]:
        rebuilt += "\\frac"
        if part[0] == "{":
            rebuilt += part
            continue
        if len(part) < 2:
            return value
        first, second, suffix = part[0], part[1], part[2:]
        if second != "{":
            rebuilt += "{" + first + "}{" + second + "}" + suffix
        else:
            rebuilt += "{" + first + "}" + second + suffix
    return rebuilt


def fix_slash_fraction(value: str) -> str:
    parts = value.split("/")
    if len(parts) != 2:
        return value
    try:
        numerator, denominator = int(parts[0]), int(parts[1])
    except ValueError:
        return value
    if value != f"{numerator}/{denominator}":
        return value
    return f"\\frac{{{numerator}}}{{{denominator}}}"


def fix_sqrt(value: str) -> str:
    if "\\sqrt" not in value:
        return value
    parts = value.split("\\sqrt")
    rebuilt = parts[0]
    for part in parts[1:]:
        rebuilt += "\\sqrt" + (
            part if part[0] == "{" else "{" + part[0] + "}" + part[1:]
        )
    return rebuilt


def strip_math_string(value: str) -> str:
    value = value.replace("\n", "")
    value = value.replace("\\!", "")
    value = value.replace("\\\\", "\\")
    value = value.replace("tfrac", "frac").replace("dfrac", "frac")
    value = value.replace("\\left", "").replace("\\right", "")
    value = value.replace("^{\\circ}", "").replace("^\\circ", "")
    value = value.replace("\\$", "")
    if "\\text{ " in value:
        parts = value.split("\\text{ ")
        if len(parts) != 2:
            raise AssertionError("ambiguous right-side units")
        value = parts[0]
    value = value.replace("\\%", "").replace(r"\%", "")
    value = value.replace(" .", " 0.").replace("{.", "{0.")
    if not value:
        return value
    if value[0] == ".":
        value = "0" + value
    equals_parts = value.split("=")
    if len(equals_parts) == 2 and len(equals_parts[0]) <= 2:
        value = equals_parts[1]
    value = fix_sqrt(value)
    value = value.replace(" ", "")
    value = fix_fracs(value)
    if value == "0.5":
        value = "\\frac{1}{2}"
    return fix_slash_fraction(value)


def normalize_answer(answer: str | None) -> str | None:
    if answer is None:
        return None
    value = answer.strip()
    match = re.search(r"^\\text\{(?P<text>.+?)\}$", value)
    if match is not None:
        value = match.group("text").strip()
    try:
        return strip_math_string(value)
    except (AssertionError, IndexError):
        return value


def rank_auc(rows: list[Observation]) -> float:
    positives = [score for _, score, valid in rows if valid]
    negatives = [score for _, score, valid in rows if not valid]
    if not positives or not negatives:
        raise ValueError("AUROC requires both process-valid and process-invalid rows")
    favorable = sum(
        (positive > negative) + 0.5 * (positive == negative)
        for positive in positives
        for negative in negatives
    )
    return favorable / (len(positives) * len(negatives))


def evaluate(
    rows: list[Observation], retention: float
) -> dict[str, float | int | None]:
    if not rows:
        raise ValueError("cannot evaluate an empty dataset")
    retained = sorted(rows, key=lambda item: item[1], reverse=True)
    retained_count = round(len(retained) * retention)
    if retained_count <= 0 or retained_count >= len(retained):
        raise ValueError("retention must leave non-empty retained and review pools")
    escalated = retained[retained_count:]
    retained = retained[:retained_count]
    valid_total = sum(valid for _, _, valid in rows)
    invalid_total = len(rows) - valid_total
    valid_retained = sum(valid for _, _, valid in retained)
    invalid_retained = retained_count - valid_retained
    valid_escalated = sum(valid for _, _, valid in escalated)
    invalid_escalated = len(escalated) - valid_escalated
    baseline_precision = valid_total / len(rows)
    treatment_precision = valid_retained / retained_count
    return {
        "outcome_accepted": len(rows),
        "process_valid": valid_total,
        "process_invalid": invalid_total,
        "retained": retained_count,
        "retained_process_valid": valid_retained,
        "retained_process_invalid": invalid_retained,
        "escalated_for_review": len(escalated),
        "escalated_process_valid": valid_escalated,
        "escalated_process_invalid": invalid_escalated,
        "achieved_retention": retained_count / len(rows),
        "achieved_review_budget": len(escalated) / len(rows),
        "random_expected_retained_precision": baseline_precision,
        "score_targeted_retained_precision": treatment_precision,
        "precision_delta_percentage_points": 100
        * (treatment_precision - baseline_precision),
        "process_valid_retention": (
            valid_retained / valid_total if valid_total else None
        ),
        "invalid_retention_rate": (
            invalid_retained / invalid_total if invalid_total else None
        ),
        "random_expected_invalid_retention_rate": retained_count / len(rows),
        "invalid_retention_relative_reduction_vs_random": (
            1 - (invalid_retained / invalid_total) / (retained_count / len(rows))
            if invalid_total
            else None
        ),
        "review_invalid_yield": invalid_escalated / len(escalated),
        "random_expected_review_invalid_yield": invalid_total / len(rows),
        "process_invalid_detection_recall": (
            invalid_escalated / invalid_total if invalid_total else None
        ),
        "random_expected_process_invalid_detection_recall": len(escalated) / len(rows),
    }


def bootstrap_interval(
    rows: list[Observation],
    retention: float,
    iterations: int,
    seed: int,
) -> tuple[float, float]:
    if iterations < 1:
        raise ValueError("bootstrap iterations must be positive")
    by_problem: dict[str, list[Observation]] = defaultdict(list)
    for row in rows:
        by_problem[row[0]].append(row)
    problems = sorted(by_problem)
    generator = random.Random(seed)
    deltas = []
    for _ in range(iterations):
        sample = []
        for problem in (generator.choice(problems) for _ in problems):
            sample.extend(by_problem[problem])
        metrics = evaluate(sample, retention)
        deltas.append(float(metrics["precision_delta_percentage_points"]))
    deltas.sort()
    return (
        deltas[math.floor(0.025 * iterations)],
        deltas[math.floor(0.975 * iterations)],
    )


def load_rows(path: Path) -> tuple[list[Observation], dict[str, int]]:
    rows: list[Observation] = []
    counts = {
        "dataset_records": 0,
        "eligible_process_labels": 0,
        "outcome_rejected": 0,
        "excluded_finish_reason": 0,
        "excluded_missing_score": 0,
    }
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            counts["dataset_records"] += 1
            try:
                record = json.loads(line)
                finish_reason = record["label"]["finish_reason"]
                question = record["question"]
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError(
                    f"invalid dataset record at line {line_number}"
                ) from error
            if finish_reason not in {"solution", "found_error"}:
                counts["excluded_finish_reason"] += 1
                continue
            score = question.get("pre_generated_verifier_score")
            if score is None:
                counts["excluded_missing_score"] += 1
                continue
            counts["eligible_process_labels"] += 1
            if normalize_answer(
                question.get("pre_generated_answer")
            ) != normalize_answer(question.get("ground_truth_answer")):
                counts["outcome_rejected"] += 1
                continue
            problem = question.get("problem")
            if not isinstance(problem, str) or not problem:
                raise ValueError(f"missing problem cluster at line {line_number}")
            try:
                numeric_score = float(score)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"invalid verifier score at line {line_number}"
                ) from error
            if not math.isfinite(numeric_score):
                raise ValueError(f"non-finite verifier score at line {line_number}")
            rows.append((problem, numeric_score, finish_reason == "solution"))
    return rows, counts


def run(
    data_path: Path,
    *,
    retention: float,
    bootstrap: int,
    seed: int,
) -> dict:
    if not 0 < retention < 1:
        raise ValueError("retention must be between zero and one")
    observed_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
    if observed_hash != DATA_SHA256:
        raise ValueError(
            f"data hash mismatch: expected {DATA_SHA256}, observed {observed_hash}"
        )
    rows, counts = load_rows(data_path)
    if not rows or not any(row[2] for row in rows) or all(row[2] for row in rows):
        raise ValueError("outcome accepts must include both process label classes")
    metrics = evaluate(rows, retention)
    ci_low, ci_high = bootstrap_interval(rows, retention, bootstrap, seed)
    metrics["precision_delta_problem_clustered_95_ci_pp"] = [ci_low, ci_high]
    metrics["prm_score_auroc"] = rank_auc(rows)
    passed = (
        metrics["precision_delta_percentage_points"] >= 5
        and ci_low > 0
        and metrics["process_valid_retention"] >= 0.80
    )
    return {
        "experiment_id": "prm800k-selective-process-audit-v1",
        "experiment_type": "retrospective public-dataset replay",
        "source": {
            "dataset": "PRM800K phase-2 test",
            "url": SOURCE_URL,
            "sha256": DATA_SHA256,
            "license": "MIT",
        },
        "claim": (
            "At a preregistered 80% automatic-retention target among "
            "outcome-accepted PRM800K solutions, escalating the lowest released "
            "PRM scores improves retained-pool process-valid precision by at least "
            "5 percentage points over random escalation while retaining at least "
            "80% of process-valid solutions."
        ),
        "sample_count": {
            **counts,
            "outcome_accepted": len(rows),
            "outcome_accepted_unique_problems": len({row[0] for row in rows}),
            "bootstrap_resamples": bootstrap,
        },
        "metrics": metrics,
        "verdict": "BOUNDED_REPLAY_POSITIVE" if passed else "CLAIM_REFUTED",
        "limitations": [
            "This is retrospective replay, not prospective deployment or causal evidence.",
            "The released score may reflect the iterative process that selected phase-2 data.",
            "The conservative answer normalizer can reject equivalent answers.",
            "One review budget does not establish calibration across operating points.",
            "Prior work establishes the phenomenon; this is not a novelty claim.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--retention", type=float, default=0.80)
    parser.add_argument("--bootstrap", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20_260_726)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    result = run(
        arguments.data,
        retention=arguments.retention,
        bootstrap=arguments.bootstrap,
        seed=arguments.seed,
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if arguments.out:
        arguments.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
