# Exact Action Identity Reduces False Loop Alerts in MobileGym Replay

This reproducibility note tests a narrow runtime-safety question: when a mobile GUI agent repeats
an action type, does matching the complete action payload avoid false loop alerts without missing
trajectories labeled `REPETITIVE_LOOP`?

## Result

On 116 public MobileGym trajectories, an action-type-only detector reached 77.78% precision at
100% recall. Requiring the same action type and exact payload reached 95.45% precision at the same
recall. The precision difference was +17.68 percentage points, with a task-clustered bootstrap 95%
interval of [+10.59, +25.15].

| Metric | Action type only | Exact action |
|---|---:|---:|
| True loop alerts | 84 | 84 |
| False loop alerts | 24 | 4 |
| Precision | 77.78% | 95.45% |
| Recall | 100.00% | 100.00% |
| False-positive rate | 75.00% | 12.50% |

The exact-action detector reduced false alerts by 83.33%. In replay, stopping at its first alert
would remove 100 later actions across the 84 labeled-loop trajectories, or 1.19 actions per labeled
loop. This is an accounting estimate, not evidence that an online agent would recover or complete
more tasks.

## Experiment

The source is the Apache-2.0
[MobileGym Qwen3-VL-4B rollout release](https://huggingface.co/datasets/gray311/mobilegym-trajectories-qwen3vl4b),
which contains 116 trajectories from 57 task IDs. Eighty-four trajectories end with
`REPETITIVE_LOOP`, 32 have another stop reason, and only one succeeds.

Two deterministic alerts are compared:

1. **Action-type baseline:** alert on two consecutive actions with the same `action_type`.
2. **Exact-action treatment:** alert only when both `action_type` and canonical JSON
   `action_data` match.

The precision interval resamples task IDs rather than individual trajectories. On the 32 non-loop
trajectories, exact matching corrects 20 baseline false alerts and introduces none
(two-sided exact McNemar p = 1.91e-6). The frozen aggregate output is in
[result.json](result.json).

## Reproduce

Python 3.12 was used for the recorded run.

```bash
python -m pip install -r experiments/mobilegym-loop-detection/requirements.txt
curl -L \
  'https://huggingface.co/datasets/gray311/mobilegym-trajectories-qwen3vl4b/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet' \
  -o mobilegym-qwen3vl4b.parquet
shasum -a 256 mobilegym-qwen3vl4b.parquet
python experiments/mobilegym-loop-detection/analyze.py \
  --data mobilegym-qwen3vl4b.parquet \
  --out reproduced.json
diff -u experiments/mobilegym-loop-detection/result.json reproduced.json
```

The expected dataset SHA-256 is
`effedfe83fff7b04c8255cd224dd1b757041823f75ef8626e63c01db612a8d31`. The script refuses a
different input instead of silently mixing dataset versions.

## Prior Art

[MobileGym](https://arxiv.org/abs/2605.26114) reports a real-device failure case in which a base
agent repeatedly presses a disabled control until exhausting its step budget.
[HyMobileAgent](https://arxiv.org/abs/2607.14548) includes explicit dead-loop detection in a
planning-and-reflection system. [Predicting Web-Agent Failure Risk from Trajectory
Prefixes](https://openreview.net/pdf?id=lqNDwH3zTG) uses canonical-action repetition and loop
features for learned failure prediction. [SpecRA](https://openreview.net/forum?id=xVO4BqmzVD)
detects broader degenerative text repetition.

This experiment does not claim that repeated-action detection is new. Its contribution is a small,
reproducible calibration showing that action identity matters even for a two-step rule: collapsing
different payloads into one action type creates many avoidable alerts on this release.

## Boundaries

- This is offline replay, not an online early-stop intervention.
- One successful trajectory is not enough to establish success preservation.
- One policy release is not enough to establish cross-model or cross-environment transfer.
- Exact coordinate identity may break under small interface or policy perturbations.
- The action-type baseline is intentionally simple; stronger state-aware or learned baselines may
  perform better.
- No raw prompts, reasoning, screenshots, or trajectories are republished here.
