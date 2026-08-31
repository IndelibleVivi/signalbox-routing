# Signalbox Programme Plan

Status: active
Current execution tranche: Foundation 0.1 source closure
Canonical specification: `docs/specification.md`, revision 1
Normative companions: `contracts/*.json`
Repository baseline: local Git repository initialized on 2026-08-31

## Goal and boundaries

Build the full source reference described by `ACCEPT-01` through `ACCEPT-08`.
This programme does not authorize a Git remote, public visibility, license,
release, live-router access, installation, activation, or deployment.

## Dependency order

```text
identity and authority
  -> machine contracts
  -> validation model
  -> Human and Agent projections
  -> Mintie reference deployment
  -> incident and private-ingress depth
  -> whole-source reconciliation
```

Definition, source enforcement, production adoption, and live activation are
different phases. This plan ends at verified Signalbox source.

## Complete coverage ledger

| Acceptance | Intended outcome | Owning slice | Dependency / gate | Verification evidence | Status |
| --- | --- | --- | --- | --- | --- |
| `ACCEPT-01` | Normative contracts agree | F0 contracts | Identity settled | `scripts/validate.py`, contract tests | foundation-verified |
| `ACCEPT-02` | Paired Human Surface teaches the complete model | F1 human guide | F0 IDs and diagrams | doc-pair parity plus manual read | planned |
| `ACCEPT-03` | Agent Surface defines implementation and evidence behavior | F2 agent reference | F0 contracts | required-ID and link validation | in-progress |
| `ACCEPT-04` | Mintie is a portable, public-safe reference deployment | F3 Mintie example | F0 roles/routing/health | example validation and boundary scan | in-progress |
| `ACCEPT-05` | Reusable failure mechanisms are retained | F4 failure depth | F0 health/evidence | failure-ID coverage | in-progress |
| `ACCEPT-06` | Validation rejects meaningful contract drift | F0 validator and F5 hardening | F0 contracts | positive and negative unit tests | foundation-verified; F5 depth planned |
| `ACCEPT-07` | Repository surfaces agree | F6 reconciliation | F1-F5 | `make verify`, links, diff review | foundation-verified; v1 reconciliation planned |
| `ACCEPT-08` | External gates remain truthful | Every slice | Explicit owner authorization | current-state and final report | verified at current boundary |

## Implementation slices

### F0 — Foundation 0.1 (source complete)

Deliver repository identity and authority, canonical specification, complete
programme ledger, role/claim/routing/health/doc-pair contracts, dependency-free
validator, regression fixtures, README, AGENTS, and current state.

Stopping point reached: source contracts and entrypoints are usable and freshly
verified. This is not full Signalbox v1; F1 is the next programme slice.

### F1 — Complete Human Surface

Expand the paired Chinese/English reader path into the full proxy-layer mental
model, packet flow, DNS ownership, routing roles, fail-closed semantics,
health/recovery, and canonical-origin private ingress. Keep operational commands
out of explanatory authority.

### F2 — Complete Agent Surface

Finish exact implementation-reference, patch protocol, state/report grammar,
source map, stop conditions, compatibility handling, and acceptance matrix.

### F3 — Mintie reference deployment

Grow Mintie from a role/health mapping into a complete public-safe sample with
portable configuration fragments, dedicated gateway identities, expected
reports, and failure walkthroughs. Never copy production bindings.

### F4 — Failure and health depth

Cover cold-boot queryability, stale success, resource pressure, common-probe
failure, DHCP identity drift, and selection/failover confusion. Add recovery
readiness examples without turning health observation into mutation.

### F5 — Validator hardening

Add only checks justified by stable contracts: internal links, stronger schema
shape, report compatibility fixtures, and sample config relationships. Avoid
building a general-purpose router validator.

### F6 — v1 source reconciliation

Read every authoritative surface, reconcile the ledger, run the full source
gate, and update current state. Any remote, license, publication, installation,
or live acceptance remains a separate owner decision.

## Scope and order deltas

No accepted product scope has been removed. The earlier proposal to place the
documentation system inside a private infrastructure repository is superseded
by the accepted independent Signalbox identity. The SSH readback procedure
remains private implementation evidence and is not an execution tranche here.

## Full acceptance

Programme completion is the verified closure of every `ACCEPT-*` row, not the
completion of Foundation 0.1. Each tranche reports its own stopping point.
