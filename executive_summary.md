# Executive Summary: Trajectory-Level Safety Evaluation

*For non-technical stakeholders*

---

## The Problem (30 seconds)

Current AI safety testing checks if a model gives dangerous answers to dangerous questions. This works for simple cases.

But AI agents work across multiple conversation turns. An attacker can split a dangerous request across many innocent-looking messages. Each message passes safety checks individually, but together they produce harm.

**Our current safety tests systematically miss these attacks.**

---

## The Risk (1 minute)

When AI agents are deployed in production:
- They handle thousands of conversations
- Each conversation has multiple turns
- Attackers have learned to exploit multi-turn patterns

A model that scores 99% on standard safety benchmarks may still be vulnerable to 50%+ of these multi-turn attacks.

**This isn't a hypothetical.** We observed this pattern in internal testing.

---

## The Solution (1 minute)

Instead of testing individual messages, we need to test entire conversations:

| Old Approach | New Approach |
|--------------|--------------|
| Test single questions | Test conversation trajectories |
| Binary safe/unsafe | Track safety drift over turns |
| Catch obvious attacks | Catch decomposed attacks |

This requires new evaluation infrastructure, but the core insight is simple:
**Safety emerges from trajectories, not snapshots.**

---

## Business Impact

| If we don't act | If we act |
|-----------------|-----------|
| Regulatory exposure from undetected harms | Proactive compliance |
| Reputation damage from safety incidents | Demonstrable due diligence |
| Reactive incident response | Prevention-first approach |

---

## Case Study: Intent Drift Attack

**What happened:**
1. Turn 1: User asks about chemistry (benign)
2. Turn 2: User asks about specific compounds (benign)
3. Turn 3: User asks about reactions (borderline)
4. Turn 4: User asks for synthesis instructions (harmful)

**Single-turn testing:** Only Turn 4 flagged, often too late

**Trajectory testing:** Drift detected at Turn 2-3, intervention possible

---

## Recommendation

1. **Immediate:** Audit current safety evaluation for trajectory coverage
2. **Short-term:** Implement trajectory-level monitoring in production
3. **Long-term:** Integrate trajectory evaluation into release gating

---

## Learn More

- Technical memo: [Full analysis](index.md)
- Implementation: See related repositories in portfolio
