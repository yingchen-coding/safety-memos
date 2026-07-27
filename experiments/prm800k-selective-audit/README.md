# PRM800K Replay: Targeting a Fixed Process-Review Budget

This reproducibility note asks a bounded operational question: after a final-answer checker accepts
a mathematical solution, can the released PRM score target a 20% process-review budget better than
random escalation?

## Result

The outcome-only gate accepts 597 solutions across 278 MATH problems. Human process labels identify
124 of those 597 as containing an error despite the matching final answer.

Escalating the bottom-scored 119 solutions, a 19.93% review budget, finds 70 of the 124
process-invalid outcome accepts:

| Metric | Random expectation | Score-targeted replay |
|---|---:|---:|
| Review-queue invalid yield | 20.77% | 58.82% |
| Process-invalid detection recall | 19.93% | 56.45% |
| Retained-pool process-valid precision | 79.23% | 88.70% |
| Process-valid solutions retained | 80.07% expected | 89.64% |

The retained-pool precision difference is +9.47 percentage points. A paired bootstrap that
resamples MATH problems gives a 95% interval of [+7.34, +11.21] percentage points. The targeted
queue reduces process-invalid automatic retentions by 45.61% relative to the matched random
expectation. The released score has an AUROC of 0.848 within the outcome-accepted subset.

These are retrospective operating-point measurements. They do not show that the same threshold
would transfer to another model, dataset, or deployment.

## Method

The experiment uses the official MIT-licensed
[PRM800K phase-2 test split](https://github.com/openai/prm800k/blob/main/prm800k/data/phase2_test.jsonl).
It applies the released conservative MATH answer normalization to
`pre_generated_answer` and `ground_truth_answer`, then retains only exact normalized matches.

Human `finish_reason` supplies the process label:

- `solution`: process-valid
- `found_error`: process-invalid
- other finish reasons: excluded

The baseline randomly escalates the same 119-solution budget in expectation. The treatment
escalates the bottom scores by `pre_generated_verifier_score`. The preregistered 80% retention
target realizes a 19.93% review budget. Its criterion requires the retained pool to improve
process-valid precision by at least five percentage points, have a problem-clustered 95% bootstrap
interval above zero, and retain at least 80% of process-valid solutions.

## Reproduce

The recorded run used Python 3.12 and only the standard library.

```bash
curl -L \
  'https://media.githubusercontent.com/media/openai/prm800k/main/prm800k/data/phase2_test.jsonl' \
  -o phase2_test.jsonl
shasum -a 256 phase2_test.jsonl
python experiments/prm800k-selective-audit/analyze.py \
  --data phase2_test.jsonl \
  --out reproduced.json
diff -u experiments/prm800k-selective-audit/result.json reproduced.json
```

The expected dataset SHA-256 is
`6b172efa884ac8341a946dd82e06947c135b7254109fb3f7aa907c715d98aaad`. The script rejects any
other input hash.

## Prior Art

[Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) introduces PRM800K and establishes the
process-supervision framing. [The Lessons of Developing Process Reward Models in Mathematical
Reasoning](https://arxiv.org/abs/2501.07301) directly documents correct-answer, flawed-process
trajectories and the resulting evaluation mismatch. [PRISM](https://arxiv.org/abs/2606.09078)
studies PRM false positives and argues for ranking-oriented evaluation because false positives can
steer downstream selection toward flawed reasoning.

This replay does not introduce a new PRM, process benchmark, or ranking method. It exposes one
auditable operating point in the original public release: how many flawed outcome accepts a fixed
review queue captures, and what remains in the automatically retained pool.

## Boundaries

- The score and labels come from the same released collection pipeline; this is not an independent
  PRM evaluation.
- Phase-2 collection used earlier PRMs to choose later samples, so selection effects may influence
  the observed ranking.
- The conservative answer normalizer is less lenient than the repository's optional symbolic
  grader and can reject mathematically equivalent answers.
- Human `finish_reason` is treated as process ground truth; no new adjudication was performed.
- Only one review budget is tested.
- No problem text, solution text, labels, labeler identifiers, or timestamps are republished.

The answer-normalization functions are adapted from the MIT-licensed PRM800K release; the required
license notice is preserved in [THIRD_PARTY_LICENSE](THIRD_PARTY_LICENSE).
