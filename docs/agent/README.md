# Agent Surface

Signalbox's Agent Surface is a deterministic route into the normative
contracts. It is not a live-router runbook and does not authorize external
mutation.

## Choose the reference for your task

| Task | Entry | Canonical implementation |
| --- | --- | --- |
| Explain a source private-ingress chain | [Executable workflow](workflow.md), [implementation reference](implementation-reference.md) | [Policy CLI](../../scripts/policy.py) calls `explain_private_ingress` in [the semantic validator](../../scripts/validate.py) |
| Evaluate a claim and its historical acceptance | [Handoff walkthrough](workflow.md#replay-a-historical-handoff), [acceptance matrix](acceptance-matrix.md) | [Handoff evaluator](../../scripts/handoff.py); path reports use the canonical health evaluator |
| Understand stale probes, pointer races or restart uncertainty | [Scenario reference](../../examples/scenarios/README.md), [recovery sequence](workflow.md#recovery-sequencing) | [Replay harness](../../scripts/replay.py) and [in-memory publisher](../../scripts/reference_workflow.py) |
| Change a normative contract or its projections | [Patch protocol](patch-protocol.md) | [Catalog](../../contracts/catalog.json), owning contract, schema, examples and behavior checks |

CLI entrypoints consume registered public examples. For integration inputs,
use the named functions and their documented trusted-input requirements; these
commands are not arbitrary deployment-config loaders. A replay's `passed`
means the expected judgment matched, including expected fail/unknown outcomes.

## Task entry

Begin with [从事实到可校验交接](workflow.md) for a complete executable task.
It connects policy explanation, source verification, actual claim/acceptance
records and eight scenario replays. Use the normative read order below when a
relation or diagnostic needs inspection. The workflow does not authorize live
network work.

## Read order

1. [AGENTS.md](../../AGENTS.md) — repository authority and mutation boundaries.
2. [Specification](../specification.md) — product meaning and accepted programme.
3. [Catalog](../../contracts/catalog.json) — schema ownership, compatibility, instance,
   and projection registry.
4. [Roles](../../contracts/roles.json) — portable role registry.
5. [Traffic policy](../../contracts/traffic-policy.json) — traffic actions and failure invariants.
6. [Claims](../../contracts/claims.json) — realization and acceptance grammar.
7. [Health contract](../../contracts/health-contract.json) — profile, observation, report, and
   aggregate semantics.
8. [Schemas](../../schemas/README.md) — structural contracts consumed through the catalog.
9. [Implementation reference](implementation-reference.md) — cross-contract implementation map.
10. [Tailnet/VPS implementation reference](tailnet-vps-implementation-reference.md) — advanced canonical private
    ingress mapping and negative-proof requirements.
11. [Patch protocol](patch-protocol.md) — update and incident-intake workflow.
12. [Acceptance matrix](acceptance-matrix.md) — realization evidence and acceptance boundaries.

## Required assumptions

- Sample identities are not live bindings.
- Examples contain no credentials, endpoint addresses, client identities, or
  production state.
- `unknown` is preserved when evidence is unavailable, stale, unsupported, or
  ambiguous.
- Health observation is read-only. Selection and recovery mutation are
  separate contracts.
- A health report observes one subject. Aggregates preserve member outcomes
  at assembly, remain historical receipts, and never manufacture a
  deployment-wide verdict.
- Passing `make verify` proves source consistency only.

## Stop conditions

Stop before an edit if it would:

- make an example a second production authority;
- add a live identity, endpoint, credential, or machine-local path;
- introduce DIRECT fallback for protected traffic;
- place a general DIRECT rule before canonical private ingress;
- equate general egress with private-ingress gateway capability;
- let a health check mutate routing;
- claim installed, activated, path, or acceptance truth from source evidence;
- select a license, create a remote, publish, install, or deploy without exact
  owner authorization.
