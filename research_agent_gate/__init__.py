"""Public, deterministic ingress and egress gates for bounded research workflows."""

from .gate import classify_sources, guard_public_output, render_dashboard

__all__ = ["classify_sources", "guard_public_output", "render_dashboard"]
