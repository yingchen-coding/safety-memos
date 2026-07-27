# Safety Memos

[![CI](https://github.com/yingchen-coding/safety-memos/actions/workflows/ci.yml/badge.svg)](https://github.com/yingchen-coding/safety-memos/actions/workflows/ci.yml)

Short, practical research memos on agentic safety, safeguards, and evaluation failures.

The goal is not to publish another generic AI safety blog. Each memo is written to be useful to
people building or reviewing agentic systems: what fails, why the usual benchmark misses it, and
what kind of engineering gate would catch it before release.

## Why This Exists

Agent safety work often gets split into two weak forms:

- high-level essays that do not tell an engineer what to test
- benchmark reports that do not explain the underlying failure mechanism

These memos sit between the two. They turn a safety argument into a concrete design pressure for
the rest of the portfolio: stress tests, regression suites, release gates, incident replay, and
agent definition scanners.

## Contents

- [Why Single-Turn Safety Benchmarks Systematically Underestimate Agentic Risk](https://yingchen-coding.github.io/safety-memos/)
  A memo on why static, one-shot safety checks miss slow-burn failures that emerge across
  multi-turn agent trajectories.
- [Research Evolution Log](RESEARCH_EVOLUTION.md)
  A versioned record of hypotheses that failed, evidence upgrades, measured results, and claim
  boundaries. Only reproducible, public-safe milestones are included.

## How To Use

Read a memo, then follow the implementation path:

1. Use [when-rlhf-fails-quietly](https://github.com/yingchen-coding/when-rlhf-fails-quietly) to name the failure mode.
2. Use [agentic-misuse-benchmark](https://github.com/yingchen-coding/agentic-misuse-benchmark) to turn it into a measurable scenario.
3. Use [safety-harness](https://github.com/yingchen-coding/safety-harness) to stress-test, pin regressions, and gate releases.
4. Use [agentguard](https://github.com/yingchen-coding/agentguard) when the risk lives in agent definitions, tool grants, hooks, or commands.

## Related Projects

- [when-rlhf-fails-quietly](https://github.com/yingchen-coding/when-rlhf-fails-quietly) — Evaluating silent alignment failures
- [agentic-misuse-benchmark](https://github.com/yingchen-coding/agentic-misuse-benchmark) — Multi-turn misuse detection benchmark
- [safety-harness](https://github.com/yingchen-coding/safety-harness) — Closed-loop runtime safety harness: stress-testing, regression suite, release gate, simulator, and incident lab in one system
