import importlib.util
import json
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "experiments"
    / "mobilegym-loop-detection"
    / "analyze.py"
)
SPEC = importlib.util.spec_from_file_location("mobilegym_loop_detection", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def row(task_id, stop_reason, success, steps):
    return {
        "task_id": task_id,
        "stop_reason": stop_reason,
        "success": success,
        "steps": json.dumps(steps),
    }


class MobileGymLoopDetectionTest(unittest.TestCase):
    def test_exact_action_avoids_different_payload_false_alert(self):
        rows = [
            row(
                "task-a",
                "MAX_STEPS",
                False,
                [
                    {"action_type": "tap", "action_data": {"x": 1, "y": 2}},
                    {"action_type": "tap", "action_data": {"x": 3, "y": 4}},
                ],
            ),
            row(
                "task-b",
                "REPETITIVE_LOOP",
                False,
                [
                    {"action_type": "tap", "action_data": {"x": 5, "y": 6}},
                    {"action_type": "tap", "action_data": {"y": 6, "x": 5}},
                    {"action_type": "wait", "action_data": {}},
                ],
            ),
        ]

        baseline = MODULE.metrics(MODULE.detector_rows(rows, exact_action=False))
        treatment = MODULE.metrics(MODULE.detector_rows(rows, exact_action=True))

        self.assertEqual(baseline["false_positive"], 1)
        self.assertEqual(treatment["false_positive"], 0)
        self.assertEqual(baseline["true_positive"], 1)
        self.assertEqual(treatment["true_positive"], 1)
        self.assertEqual(treatment["actions_avoided_on_labeled_loops"], 1)

    def test_invalid_step_fails_loudly(self):
        rows = [
            row(
                "task-a",
                "MAX_STEPS",
                False,
                [{"action_data": {"x": 1, "y": 2}}],
            )
        ]

        with self.assertRaisesRegex(ValueError, "action_type"):
            MODULE.detector_rows(rows, exact_action=True)

    def test_mcnemar_exact_two_sided_probability(self):
        self.assertEqual(MODULE.mcnemar_exact_two_sided_p(0, 0), 1.0)
        self.assertAlmostEqual(
            MODULE.mcnemar_exact_two_sided_p(20, 0),
            1.9073486328125e-06,
        )


if __name__ == "__main__":
    unittest.main()
