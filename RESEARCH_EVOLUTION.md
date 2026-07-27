# Research Evolution Log

**Owner:** Ying Chen

This log makes the path to a final research artifact visible. It is not a daily activity feed.
An entry is promoted only when it changes a measured conclusion, closes a documented evidence
gap, or ships reproducible new behavior.

## Promotion Standard

Each promoted iteration must improve on the strongest prior iteration along at least one named
axis:

- evidence realism
- sample scale
- uncertainty quantification
- baseline strength
- reproducibility
- novelty assessment
- verified useful behavior

A rerun that only reproduces an existing result is verification, not progress. A failed
hypothesis belongs in the log when it changes the next experiment.

## Entry Contract

Every future entry must include:

1. the bounded question and failure condition
2. the prior strongest result
3. the exact improvement axis
4. the experiment and comparison baseline
5. sample counts and uncertainty
6. the result artifact and reproduce command
7. limitations, privacy boundary, and publication decision

Entries without a reproducible public artifact remain private until those requirements are met.
Private paths, transcripts, personal data, unpublished work context, and raw operational logs are
never copied into this repository.

## Evolution

| Version | Public artifact | Measured improvement | Decision |
|---|---|---|---|
| 0 | Evolution contract and automated validator | Replaces final-result-only publishing with versioned, evidence-gated history | Accepted as the public tracking baseline |
| 1 | [MobileGym loop-detection replay](experiments/mobilegym-loop-detection/) | Exact action identity reduces false alerts from 24 to 4 at matched recall | Accepted as a bounded offline milestone |

## Version 0: Evidence-Gated Tracking

### Problem

A final paper or tool hides the failed hypotheses, evidence upgrades, and claim corrections that
produced it. Commit history alone records file changes but does not explain why the research
direction changed.

### Change

This version introduces a stable public entry contract and an automated validator. Later research
milestones must compare themselves with the strongest accepted version rather than merely claiming
to be newer.

### Verification

```bash
python scripts/verify_research_evolution.py
```

The validator checks the required structure and blocks private paths, personal contact details,
and unbounded progress language.

### Boundary

Version 0 improves research traceability, not a scientific result. It makes no model-performance,
novelty, or general-capability claim.

## Version 1: Payload-Specific Loop Alerts

### Problem

Two consecutive actions of the same type are not necessarily a loop. A mobile agent may
legitimately tap different controls in succession, so an action-type-only stop rule can interrupt
progress.

### Change

The first public experiment evaluates exact action identity against the coarse type-only rule on a
frozen, public MobileGym trajectory release. This advances evidence realism, sample scale,
uncertainty quantification, and reproducibility beyond Version 0's process-only contract.

### Result

Across 116 trajectories and 57 task IDs, both detectors identify all 84 trajectories labeled
`REPETITIVE_LOOP`. Exact action identity raises precision from 77.78% to 95.45%, a +17.68
percentage-point difference with a task-clustered bootstrap 95% interval of [+10.59, +25.15]. It
reduces false alerts from 24 to 4. Stopping at its first replay alert would remove 100 later actions
on labeled loops.

### Verification

```bash
python -m unittest discover -s tests
python scripts/verify_research_evolution.py
```

The [experiment artifact](experiments/mobilegym-loop-detection/) provides the frozen result,
dataset hash, dependency version, analysis code, and full-data reproduce command.

### Boundary

This is a bounded offline replay result, not a novelty, online success, policy-learning, or
cross-model claim. The release contains one successful trajectory, so it cannot establish success
preservation. No raw trajectory text, screenshots, prompts, or reasoning are published.
