# Signalbox Programme Plan

Status: active
Current execution tranche: none
Most recently completed tranche: F0.2 remote and semantic hardening
Next planned tranche: F1 complete Human Surface (not started or authorized)
Canonical specification: `docs/specification.md`, revision 2
Normative companions: `contracts/*.json`, `schemas/*.schema.json`
Repository baseline: public canonical repository on `main`

## Goal and boundaries

Build the full source reference described by `ACCEPT-01` through `ACCEPT-08`.
F0.2 completed source hardening, hosted source verification, and bounded GitHub
authority settings for the already-public repository. It did not authorize a
license, release, live-router access, installation, activation, or deployment.

## Authorization history

- F0 began as local source work and did not itself authorize a remote or public
  visibility.
- Faye separately authorized creation of the public GitHub repository on
  2026-08-31; that completed gate is recorded in `docs/current-state.md`.
- F0.2 may harden that existing public source and its repository settings. This
  later authorization does not retroactively widen the original F0 boundary.

## Dependency order

```text
identity and authority
  -> machine contracts
  -> validation model
  -> remote and semantic hardening
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
| `ACCEPT-01` | Normative contracts agree | F0/F0.2 contracts | Identity settled | semantic validator, JSON Schema, contract tests | F0.2 hardening complete; v1 pending |
| `ACCEPT-02` | Paired Human Surface teaches the complete model | F1 human guide | F0 IDs and diagrams | doc-pair parity plus manual read | planned |
| `ACCEPT-03` | Agent Surface defines implementation and evidence behavior | F2 agent reference | F0 contracts | required-ID and link validation | F0.2 reconciled; F2 pending |
| `ACCEPT-04` | Mintie is a portable, public-safe reference deployment | F0.2/F3 Mintie example | F0 roles/routing/health | example validation and boundary scan | F0.2 baseline complete; F3 pending |
| `ACCEPT-05` | Reusable failure mechanisms are retained | F4 failure depth | F0 health/evidence | failure-ID coverage | F0.2 mechanisms added; F4 pending |
| `ACCEPT-06` | Validation rejects meaningful contract drift | F0.2 validator and F5 hardening | F0 contracts | positive and negative tests plus hosted gate | F0.2 gate complete; F5 pending |
| `ACCEPT-07` | Repository surfaces agree | F0.2/F6 reconciliation | Current slice | `make verify`, links, diff review | F0.2 reconciled; F6 pending |
| `ACCEPT-08` | External gates remain truthful | Every slice | Explicit owner authorization | current-state and remote readback | F0.2 readback complete; future gates separate |

## Implementation slices

### F0 — Foundation 0.1 (`completed-at-source-boundary`)

Deliver repository identity and authority, canonical specification, complete
programme ledger, role/claim/routing/health/doc-pair contracts, dependency-free
validator, regression fixtures, README, AGENTS, and current state.

Stopping point reached: source contracts and entrypoints are usable and freshly
verified and published. This was not full Signalbox v1.

### F0.2 — Remote and semantic hardening (`completed-at-source-and-remote-boundary`)

Protect the public source gate with hosted CI and a minimal `main` policy;
repair publication-state authority; enforce specific-before-general private
ingress; make health reports subject-scoped, sequence-scoped, restore-bound,
and observation-complete; publish consumable JSON Schemas and a contract
catalog; strengthen bilingual section parity; and remove unused GitHub
documentation surfaces that could compete with repository authority.

Stopping point reached: exact F0.2 source passed local and hosted verification,
public `main` requires the named gate, GitHub settings match the authority
contract, and exact remote readback agrees. This does not complete or authorize
F1 through F6.

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
