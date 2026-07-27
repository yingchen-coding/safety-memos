import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "experiments"
    / "prm800k-selective-audit"
    / "analyze.py"
)
SPEC = importlib.util.spec_from_file_location("prm800k_selective_audit", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Prm800kSelectiveAuditTest(unittest.TestCase):
    def test_answer_normalization(self):
        self.assertEqual(MODULE.normalize_answer("0.5"), "\\frac{1}{2}")
        self.assertEqual(MODULE.normalize_answer("x = 4"), "4")
        self.assertEqual(MODULE.normalize_answer("\\text{blue}"), "blue")
        self.assertIsNone(MODULE.normalize_answer(None))

    def test_score_targeting_improves_retained_precision(self):
        rows = [
            ("problem-a", 0.9, True),
            ("problem-a", 0.8, True),
            ("problem-b", 0.7, True),
            ("problem-b", 0.1, False),
        ]

        metrics = MODULE.evaluate(rows, 0.75)

        self.assertEqual(metrics["escalated_for_review"], 1)
        self.assertEqual(metrics["escalated_process_invalid"], 1)
        self.assertEqual(metrics["score_targeted_retained_precision"], 1.0)
        self.assertEqual(metrics["random_expected_retained_precision"], 0.75)
        self.assertEqual(metrics["process_invalid_detection_recall"], 1.0)

    def test_problem_clustered_bootstrap_is_deterministic(self):
        rows = [
            ("problem-a", 0.9, True),
            ("problem-a", 0.8, True),
            ("problem-b", 0.7, True),
            ("problem-b", 0.1, False),
            ("problem-c", 0.6, True),
            ("problem-c", 0.2, False),
        ]

        first = MODULE.bootstrap_interval(rows, 0.67, 100, 7)
        second = MODULE.bootstrap_interval(rows, 0.67, 100, 7)

        self.assertEqual(first, second)

    def test_invalid_retention_fails_loudly(self):
        with self.assertRaisesRegex(ValueError, "retention"):
            MODULE.evaluate([("problem-a", 0.9, True)], 0.80)


if __name__ == "__main__":
    unittest.main()
