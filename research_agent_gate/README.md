# Research Agent Gate Kit

This is the publishable core of a larger private research workflow: deterministic gates around
untrusted research inputs and proposed public outputs. It is deliberately **not** an autonomous
research system and makes no claim to discover, reproduce, evaluate, or publish research by itself.

## What It Demonstrates

1. A source classifier admits only configured, relevant public-primary records and records why
   everything else was quarantined.
2. A release guard requires an independent evaluation, independent critic, reproduce command,
   claim boundary, and a privacy scan before a candidate can be release-ready.
3. A standalone, local-only dashboard shows the current decisions. It performs no model call,
   network request, upload, commit, or publication action.

## Run

```bash
python -m research_agent_gate.cli \
  --input research_agent_gate/examples/demo-input.json \
  --dashboard /tmp/research-agent-gate.html
```

Open `/tmp/research-agent-gate.html` in a browser. The example intentionally has no research
candidate, so the release verdict is `NOT_APPLICABLE`.

## Boundary

This reference kit does not include private prompts, local corpus paths, operational transcripts,
credentials, proprietary data, or model-provider integration. Production research needs additional
evidence retrieval, experiment execution, independent evaluation, and reproducibility work.
