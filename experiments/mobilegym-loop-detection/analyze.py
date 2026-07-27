#!/usr/bin/env python3
"""Compare coarse and exact-action loop alerts on MobileGym trajectories."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq


EXPECTED_DATA_SHA256 = (
    "effedfe83fff7b04c8255cd224dd1b757041823f75ef8626e63c01db612a8d31"
)
DATASET_NAME = "gray311/mobilegym-trajectories-qwen3vl4b"
DATASET_URL = "https://huggingface.co/datasets/gray311/mobilegym-trajectories-qwen3vl4b"
PAPER_URL = "https://arxiv.org/abs/2605.26114"


def action_identity(step: dict) -> str:
    action_type = step.get("action_type")
    if not isinstance(action_type, str) or not action_type:
        raise ValueError("trajectory step has no non-empty action_type")
    return (
        action_type
        + "|"
        + json.dumps(
            step.get("action_data") or {},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )


def first_repeat(steps: list[dict], *, exact_action: bool) -> int | None:
    for step in steps:
        action_type = step.get("action_type")
        if not isinstance(action_type, str) or not action_type:
            raise ValueError("trajectory step has no non-empty action_type")
    for index in range(1, len(steps)):
        previous = (
            action_identity(steps[index - 1])
            if exact_action
            else steps[index - 1]["action_type"]
        )
        current = (
            action_identity(steps[index])
            if exact_action
            else steps[index]["action_type"]
        )
        if current == previous:
            return index
    return None


def detector_rows(rows: list[dict], *, exact_action: bool) -> list[dict]:
    detected = []
    for row_number, row in enumerate(rows):
        try:
            steps = json.loads(row["steps"])
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(f"row {row_number} has invalid steps JSON") from error
        if not isinstance(steps, list):
            raise ValueError(f"row {row_number} steps must decode to a list")
        flag_index = first_repeat(steps, exact_action=exact_action)
        detected.append(
            {
                "task_id": row["task_id"],
                "loop": row["stop_reason"] == "REPETITIVE_LOOP",
                "success": bool(row["success"]),
                "flagged": flag_index is not None,
                "actions_avoided": (
                    len(steps) - flag_index - 1 if flag_index is not None else 0
                ),
            }
        )
    return detected


def metrics(rows: list[dict]) -> dict:
    true_positive = sum(row["loop"] and row["flagged"] for row in rows)
    false_positive = sum(not row["loop"] and row["flagged"] for row in rows)
    false_negative = sum(row["loop"] and not row["flagged"] for row in rows)
    true_negative = sum(not row["loop"] and not row["flagged"] for row in rows)
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    negative_count = false_positive + true_negative
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": (
            true_positive / precision_denominator if precision_denominator else 0.0
        ),
        "recall": true_positive / recall_denominator if recall_denominator else 0.0,
        "false_positive_rate": (
            false_positive / negative_count if negative_count else 0.0
        ),
        "successful_trajectories_flagged": sum(
            row["success"] and row["flagged"] for row in rows
        ),
        "actions_avoided_on_labeled_loops": sum(
            row["actions_avoided"] for row in rows if row["loop"] and row["flagged"]
        ),
    }


def clustered_bootstrap(
    baseline: list[dict],
    treatment: list[dict],
    *,
    iterations: int,
    seed: int,
) -> list[float]:
    if iterations < 1:
        raise ValueError("bootstrap iterations must be positive")
    by_task = defaultdict(list)
    for base, treat in zip(baseline, treatment, strict=True):
        if base["task_id"] != treat["task_id"]:
            raise ValueError("baseline and treatment task IDs differ")
        by_task[base["task_id"]].append((base, treat))
    if not by_task:
        raise ValueError("cannot bootstrap an empty dataset")
    task_ids = sorted(by_task)
    generator = random.Random(seed)
    deltas = []
    for _ in range(iterations):
        sampled_task_ids = [generator.choice(task_ids) for _ in task_ids]
        baseline_sample = []
        treatment_sample = []
        for task_id in sampled_task_ids:
            for base, treat in by_task[task_id]:
                baseline_sample.append(base)
                treatment_sample.append(treat)
        deltas.append(
            metrics(treatment_sample)["precision"]
            - metrics(baseline_sample)["precision"]
        )
    return sorted(deltas)


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("cannot take a percentile of an empty collection")
    index = min(len(values) - 1, max(0, math.floor(probability * len(values))))
    return values[index]


def mcnemar_exact_two_sided_p(first_only: int, second_only: int) -> float:
    discordant = first_only + second_only
    if discordant == 0:
        return 1.0
    smaller = min(first_only, second_only)
    lower_tail = sum(math.comb(discordant, k) for k in range(smaller + 1))
    return min(1.0, 2.0 * lower_tail / (2**discordant))


def run(data_path: Path, *, bootstrap: int, seed: int) -> dict:
    data_sha256 = hashlib.sha256(data_path.read_bytes()).hexdigest()
    if data_sha256 != EXPECTED_DATA_SHA256:
        raise ValueError(
            "dataset SHA-256 mismatch: "
            f"expected {EXPECTED_DATA_SHA256}, got {data_sha256}"
        )
    rows = pq.read_table(
        data_path,
        columns=["task_id", "stop_reason", "success", "steps"],
    ).to_pylist()
    if not rows:
        raise ValueError("dataset contains no trajectories")

    baseline_rows = detector_rows(rows, exact_action=False)
    treatment_rows = detector_rows(rows, exact_action=True)
    baseline = metrics(baseline_rows)
    treatment = metrics(treatment_rows)
    precision_delta = treatment["precision"] - baseline["precision"]
    bootstrap_deltas = clustered_bootstrap(
        baseline_rows,
        treatment_rows,
        iterations=bootstrap,
        seed=seed,
    )
    baseline_only_errors = sum(
        not base["loop"] and base["flagged"] and not treat["flagged"]
        for base, treat in zip(baseline_rows, treatment_rows, strict=True)
    )
    treatment_only_errors = sum(
        not treat["loop"] and treat["flagged"] and not base["flagged"]
        for base, treat in zip(baseline_rows, treatment_rows, strict=True)
    )
    claim_holds = (
        baseline["recall"] == treatment["recall"] == 1.0
        and precision_delta >= 0.10
        and treatment["successful_trajectories_flagged"] == 0
        and treatment["actions_avoided_on_labeled_loops"] > 0
    )
    return {
        "source": {
            "dataset": DATASET_NAME,
            "canonical_url": DATASET_URL,
            "paper_url": PAPER_URL,
            "license": "Apache-2.0",
            "dataset_sha256": data_sha256,
        },
        "sample_count": {
            "trajectories": len(rows),
            "unique_tasks": len({row["task_id"] for row in rows}),
            "repetitive_loop_trajectories": sum(
                row["stop_reason"] == "REPETITIVE_LOOP" for row in rows
            ),
            "non_loop_trajectories": sum(
                row["stop_reason"] != "REPETITIVE_LOOP" for row in rows
            ),
            "successful_trajectories": sum(bool(row["success"]) for row in rows),
            "clustered_bootstrap_resamples": bootstrap,
        },
        "baseline": {
            "definition": "two consecutive actions of the same action type",
            **baseline,
        },
        "treatment": {
            "definition": "two consecutive actions with the same type and exact payload",
            **treatment,
        },
        "metrics": {
            "precision_delta_percentage_points": precision_delta * 100,
            "precision_delta_task_clustered_95_ci_pp": [
                percentile(bootstrap_deltas, 0.025) * 100,
                percentile(bootstrap_deltas, 0.975) * 100,
            ],
            "false_positive_relative_reduction": (
                1 - treatment["false_positive"] / baseline["false_positive"]
            ),
            "replay_estimated_actions_avoided_on_labeled_loops": treatment[
                "actions_avoided_on_labeled_loops"
            ],
            "actions_avoided_per_labeled_loop": (
                treatment["actions_avoided_on_labeled_loops"]
                / treatment["true_positive"]
            ),
            "paired_non_loop_baseline_only_false_alerts": baseline_only_errors,
            "paired_non_loop_treatment_only_false_alerts": treatment_only_errors,
            "mcnemar_exact_two_sided_p": mcnemar_exact_two_sided_p(
                baseline_only_errors,
                treatment_only_errors,
            ),
        },
        "verdict": "BOUNDED_REPLAY_POSITIVE" if claim_holds else "CLAIM_REFUTED",
        "limitations": [
            "Offline replay does not establish online intervention or policy gains.",
            "Only one trajectory succeeds, so success-preservation evidence is weak.",
            "One policy release cannot establish cross-model transfer.",
            "Actions avoided assume termination at the alert; recovery is unknown.",
            "Exact payload identity may be brittle under interface perturbations.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--bootstrap", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20_260_727)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    result = run(
        arguments.data,
        bootstrap=arguments.bootstrap,
        seed=arguments.seed,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if arguments.out:
        arguments.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
