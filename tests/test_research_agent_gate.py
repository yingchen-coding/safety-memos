from __future__ import annotations

import unittest

from research_agent_gate.gate import classify_sources, guard_public_output, render_dashboard


class ResearchAgentGateTest(unittest.TestCase):
    def test_classifier_allows_relevant_public_primary_source(self) -> None:
        result = classify_sources(
            [
                {
                    "id": "safe",
                    "topic": "agent-safety",
                    "title": "Prompt injection auditing for tool-using agents",
                    "url": "https://arxiv.org/abs/2401.00001",
                }
            ]
        )
        self.assertEqual(result["verdict"], "ALLOW")
        self.assertEqual(len(result["eligible_sources"]), 1)

    def test_classifier_quarantines_irrelevant_or_non_primary_source(self) -> None:
        result = classify_sources(
            [
                {
                    "topic": "agent-safety",
                    "title": "Disk encryption hardware case study",
                    "url": "https://arxiv.org/abs/2401.00002",
                },
                {
                    "topic": "agent-safety",
                    "title": "Agent prompt injection auditing",
                    "url": "file:///private/source.txt",
                },
            ]
        )
        self.assertEqual(result["verdict"], "NO_RESEARCH_INPUT")
        self.assertEqual(len(result["quarantined_sources"]), 2)

    def test_release_guard_requires_evidence_and_redacts_dashboard(self) -> None:
        release = guard_public_output(
            {
                "evaluation_verdict": "PASS",
                "critic_verdict": "KEEP",
                "reproduce_command": "python analysis.py",
                "claim_boundary": "Offline replay only.",
                "artifact": "/" + "Users/private/result.json",
            }
        )
        self.assertEqual(release["verdict"], "BLOCK")
        page = render_dashboard(
            {"verdict": "ALLOW", "eligible_sources": [], "quarantined_sources": []},
            release,
        )
        self.assertNotIn("/" + "Users/", page)

    def test_no_candidate_is_not_release_ready(self) -> None:
        self.assertEqual(guard_public_output(None)["verdict"], "NOT_APPLICABLE")

    def test_complete_public_candidate_passes_release_gate(self) -> None:
        release = guard_public_output(
            {
                "evaluation_verdict": "PASS",
                "critic_verdict": "KEEP",
                "reproduce_command": "python analysis.py --frozen-input",
                "claim_boundary": "Offline replay only; no deployment claim.",
            }
        )
        self.assertEqual(release["verdict"], "PASS")

    def test_dashboard_escapes_source_content(self) -> None:
        page = render_dashboard(
            {
                "verdict": "ALLOW",
                "quarantined_sources": [],
                "eligible_sources": [
                    {"title": "<script>alert(1)</script>", "url": "https://arxiv.org/abs/2401.00001"}
                ],
            },
            guard_public_output(None),
        )
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)


if __name__ == "__main__":
    unittest.main()
