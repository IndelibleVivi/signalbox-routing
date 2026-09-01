# Signalbox Programme Plan

Status: active
Current execution tranche: none
Most recently completed tranche: F0.2.2 executable-authority closure
Next planned tranche: F2 complete Agent Surface
Canonical specification: `docs/specification.md`, revision 4
Normative companions: `contracts/*.json`, `schemas/*.schema.json`
Repository baseline: public canonical repository on `main`

## Goal and boundaries

Build the full source reference described by `ACCEPT-01` through `ACCEPT-08`.
F0.2 completed source hardening, hosted source verification, and bounded GitHub
authority settings for the already-public repository. F0.2.1 closes aggregate
time semantics, and F1 adds the complete bilingual reader surface. F0.2.2 makes
the settled safety semantics executable at one canonical evaluation boundary
and broadens the public-source gate to every path in the current Git index.
None of these tranches authorizes a license, release, live-router access,
installation, activation, or deployment.

## Authorization history

- F0 began as local source work and did not itself authorize a remote or public
  visibility.
- Faye separately authorized creation of the public GitHub repository on
  2026-08-31; that completed gate is recorded in `docs/current-state.md`.
- F0.2 may harden that existing public source and its repository settings. This
  later authorization does not retroactively widen the original F0 boundary.
- Faye authorized the two-review follow-up on 2026-08-31: rebalance the reader
  entrance, add paired Chinese/English guides, document the Tailnet/VPS pattern,
  and identify Mintie's reference hardware. This authorizes public source work,
  commit, and push under the standing repository workflow, not live mutation.
- Faye authorized the 2026-09-01 Pro review follow-up as F0.2.2 public source
  work. It closes the verified restore-gate and source-scanner defects plus
  same-round authority, binding, route-grammar, and hermeticity gaps. It does
  not authorize runtime pointer mutation, Tailnet/router access, or deployment.

## Dependency order

```text
identity and authority
  -> machine contracts
  -> validation model
  -> remote and semantic hardening
  -> executable authority closure
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
| `ACCEPT-01` | Normative contracts agree | F0/F0.2.1/F0.2.2 contracts | Identity settled | semantic validator, JSON Schema, contract tests | F0.2.2 source and remote boundary complete; full v1 pending |
| `ACCEPT-02` | Paired Human Surface teaches the complete model | F1 human guide | F0 IDs and diagrams | doc-pair parity plus manual read | F1 source and remote boundary complete; full v1 pending |
| `ACCEPT-03` | Agent Surface defines implementation and evidence behavior | F2 agent reference | F0 contracts | required-ID and link validation | Tailnet reference added; full F2 pending |
| `ACCEPT-04` | Mintie is a portable, public-safe reference deployment | F0.2/F0.2.2/F3 Mintie example | F0 roles/routing/health | example validation and Git-index boundary scan | exact reference route grammar and broader source scan are published; full F3 pending |
| `ACCEPT-05` | Reusable failure mechanisms are retained | F4 failure depth | F0 health/evidence | failure-ID coverage | F0.2 mechanisms added; F4 pending |
| `ACCEPT-06` | Validation rejects meaningful contract drift | F0.2.2 validator and F5 hardening | F0 contracts | positive and negative tests plus hosted gate | 54 regressions and the hosted implementation gate pass; F5 pending |
| `ACCEPT-07` | Repository surfaces agree | F0.2.2/F1/F6 reconciliation | Current slice | `make verify`, links, diff review | F0.2.2 projections are reconciled and published; F6 pending |
| `ACCEPT-08` | External gates remain truthful | Every slice | Explicit owner authorization | current-state and remote readback | F0.2.2 implementation readback complete; later gates remain separate |

## Implementation slices

### F0 — Foundation 0.1 (`completed-at-source-boundary`)

Deliver repository identity and authority, canonical specification, complete
programme ledger, role/claim/routing/health/doc-pair contracts, repository
validators, regression fixtures, README, AGENTS, and current state.

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

### F0.2.1 — Aggregate time-semantics closure (`completed-at-source-and-remote-boundary`)

Replace the ambiguous aggregate member field with
`effective_outcome_at_assembly`, require `evaluated_at == assembled_at`, and
define the aggregate as an immutable historical receipt. Because the member
shape breaks compatibility, advance `signalbox.health-aggregate` to v2 and its
owning health contract to v3 rather than creating an in-place dual path.

Stopping point: machine contracts, schemas, sample, validator, regressions, and
human/agent projections agree. Exact published commit and hosted evidence are
owned by `docs/current-state.md`.

### F0.2.2 — Executable-authority closure (`completed-at-source-and-remote-boundary`)

Route restore and aggregation through one canonical health-evidence evaluator:
Draft 2020-12 structure, full report/profile semantics, publication and expiry
window, and exact current identity. Bind profile kinds to compatible subject
kinds with exactly-one cardinality. Lock the Mintie route projection to exact
route ID/action/match/field grammar. Validate the catalog through a fixed
bootstrap schema, resolve authority paths hermetically, and scan current
worktree bytes for every textual path listed in the Git index instead of
selected directories and suffixes.

Protect those safety-bearing fields with a contract-mutation matrix.

Stopping point reached: implementation, schemas, samples, regressions, and
documentation passed the local source gate. Implementation commit
`099662a4b66f3ab1ef3b62b720e97b503fa7555d` passed hosted Python
3.11/3.12/3.13 verification and the required aggregate check in run
`33467434452`; exact remote and GitHub API readback agreed before the receipt.
Runtime current-pointer CAS/lock and report-set sequencing, metrics-key
whitelists, validator modularization, historical compatibility fixtures, and
supply-chain policy remain deliberately assigned to F2/F5 rather than being
smuggled into this defect closure.

### F1 — Complete Human Surface (`completed-at-source-and-remote-boundary`)

Expand the paired Chinese/English reader path into the full proxy-layer mental
model, packet flow, DNS ownership, routing roles, fail-closed semantics,
health/recovery, and canonical-origin private ingress. Keep operational commands
out of explanatory authority.

Delivered reader paths: a lightweight root README pair, a basic router guide,
a routing/DNS/fail-closed guide, and an advanced Tailnet/VPS canonical
private-ingress guide. Depth remains in the normative core; the public entrance
now exposes it progressively. Exact published commit and hosted evidence are
owned by `docs/current-state.md`.

### F2 — Complete Agent Surface

Finish exact implementation-reference, patch protocol, state/report grammar,
source map, stop conditions, compatibility handling, and acceptance matrix.
Specify the deployment-side race-safe current-pointer read/CAS contract and
report-set sequencing without pretending the source evaluator activates it.

### F3 — Mintie reference deployment

Grow Mintie from a role/health mapping into a complete public-safe sample with
portable configuration fragments, dedicated gateway identities, expected
reports, destination-policy negative proofs, authorization-boundary evidence,
and failure walkthroughs. Never copy production bindings.

### F4 — Failure and health depth

Cover cold-boot queryability, stale success, resource pressure, common-probe
failure, DHCP identity drift, and selection/failover confusion. Add recovery
readiness examples without turning health observation into mutation.

### F5 — Validator hardening

Add only checks justified by stable contracts: metrics-key whitelists,
historical report compatibility fixtures, validator modularization, and deeper
sample relationships. Avoid building a general-purpose router validator.
Evaluate supply-chain hardening separately—immutable action pins,
dependency-update policy, and transitive hash locking are candidates, not
blockers retrofitted onto a bounded defect closure.

### F6 — v1 source reconciliation

Read every authoritative surface, reconcile the ledger, run the full source
gate, and update current state. Any remote, license, publication, installation,
or live acceptance remains a separate owner decision.

## Scope and order deltas

No accepted product scope has been removed. The earlier proposal to place the
documentation system inside a private infrastructure repository is superseded
by the accepted independent Signalbox identity. The SSH readback procedure
remains private implementation evidence and is not an execution tranche here.
The F1 reader rebalance changes exposure order, not normative depth: basic
readers enter through three bounded paths while contracts, schemas, and the
Agent Surface retain the complete implementation model.

## Full acceptance

Programme completion is the verified closure of every `ACCEPT-*` row, not the
completion of Foundation 0.1. Each tranche reports its own stopping point.
