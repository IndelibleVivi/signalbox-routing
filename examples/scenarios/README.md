# Synthetic judgment scenarios

`cases.json` contains five human judgments and three current-pointer timelines.
Inputs have no live bindings. Run from the repository root:

```bash
.venv/bin/python -m scripts.replay
.venv/bin/python -m scripts.replay --case older-attempt-finishes-last
```

Routing scenarios supply matched route IDs; they do not compute DNS or packet
matches. Coverage scenarios preserve unobserved boundaries as unknown; they do
not diagnose hardware. Health and restore scenarios use the canonical
evaluator. Sequencing uses an in-memory reference publisher, not a durable or
live current pointer. Every result compares actual against expected behavior.
The ordinary `make verify` includes replay and behavior tests.

Read the [worked cases](../../docs/human/50-worked-cases.en.md) and
[agent workflow](../../docs/agent/workflow.md) for conclusions and boundaries.
