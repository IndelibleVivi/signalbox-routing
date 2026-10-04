# Signalbox Programme Plan

Status: active
Current follow-up: authorized reading-station publication, separate from network runtime
Reader follow-up: telegraph reading station and same-source content integration
Most recently integrated tranche: F2 Agent Surface and reading station via PR #3
Previous source boundary: F0.2.2 executable-authority closure
Next programme tranche after F2: F3 complete Mintie reference deployment
Canonical specification: `docs/specification.md`, revision 6
Normative companions: `contracts/*.json`, `schemas/*.schema.json`
Repository baseline: public canonical repository on `main`

## Goal and boundaries

Build the full source reference described by `ACCEPT-01` through `ACCEPT-08`.
F0.2 completed source hardening, hosted source verification, and bounded GitHub
authority settings for the already-public repository. F0.2.1 closes aggregate
time semantics, and F1 adds the complete bilingual reader surface. F0.2.2 makes
the settled safety semantics executable at one canonical evaluation boundary
and broadens the public-source gate to every path in the current Git index.
After F1 and before F2, the F0.3 underlay-observability tranche adds a
`network-underlay` subject kind and `underlay-operational` profile kind so a
degraded DIRECT underlay stays observable while control-plane and proxy-lane
reports are healthy.
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

- Faye authorized the 2026-10-03 Chat-review update as source work: close
  semantic defects, complete the F2 handoff/sequence reference, and introduce
  five F3/F4 judgment cases with paired reader paths. Additional reversible
  in-scope improvements are authorized. Standing Git closure applies to the
  existing source remote; protected-main policy still requires a source branch
  and PR. No runtime, release or license gate is widened.
- Faye authorized the 2026-10-04 discussion/kit continuation as source work:
  integrate the selected telegraph reading station, reuse the supplied visual
  assets, and foreground practical network arrangements in the existing reader
  path. Static build and local browser verification do not authorize hosted
  deployment or a live-client implementation.
- Faye authorized formal reading-station deployment on 2026-10-04: integrate
  the verified source through protected-main PRs and publish its generated static
  site on GitHub Pages. This does not authorize a router/Tailnet/VPS mutation,
  runtime installation, release or license change.

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
| `ACCEPT-01` | Normative contracts agree | F0/F0.2.1/F0.2.2/F2 contracts | Identity settled | semantic validator, JSON Schema, contract tests | F0.2.2 integrated; F2 integrated source adds typed input, freshness and reference/revision closure; full v1 pending |
| `ACCEPT-02` | Paired Human Surface teaches the complete model | F1 human guide and F2 reader projections | F0 IDs and diagrams | doc-pair parity plus manual read | F1 integrated; F2 integrated source adds progressive request-based entry, packet-path observations and five paired worked cases; full v1 pending |
| `ACCEPT-03` | Agent Surface defines implementation and evidence behavior | F2 agent reference | F0 contracts | structured chain diagnostics, concrete handoffs, sequence/restore replay and behavior tests | F2 integrated source; local and hosted implementation gates passed |
| `ACCEPT-04` | Mintie is a portable, public-safe reference deployment | F0.2/F0.2.2/F2/F3 Mintie example | F0 roles/routing/health | example validation and Git-index boundary scan | Integrated route grammar; F2 integrated source adds source/four-stage handoffs and replay judgments pulled forward from F3; full F3 pending |
| `ACCEPT-05` | Reusable failure mechanisms are retained | F0.3/F2 lessons and F4 failure depth | F0 health/evidence | failure-ID coverage and linked worked cases | Underlay and sleep-path lessons retained; F2 integrated source separates trigger, defect and repair and adds five judgments; remaining F4 depth pending |
| `ACCEPT-06` | Validation rejects meaningful contract drift | F0.2.2/F2 validator and F5 hardening | F0 contracts | positive and negative tests plus the hosted implementation gate | F2 integrated source rejects typed-input, stale-observation, handoff and sequence drift; exact receipts are owned by `docs/current-state.md`; F5 pending |
| `ACCEPT-07` | Repository surfaces agree | F0.2.2/F1/F2/F6 reconciliation | Current slice | `make verify`, links, diff review | F2 integrated source contracts, examples and human/agent projections agree; F6 whole-programme reconciliation pending |
| `ACCEPT-08` | External gates remain truthful | Every slice | Explicit owner authorization | current-state and remote readback | F2 is source-integrated; reading-station publication is separately authorized and checked; release and network-runtime gates remain separate |

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

The reading-station follow-up builds these same Markdown sources into a
telegraph-themed surface with manuals, diagrams, cases and existing synthetic
workbench receipts. The Tailnet/VPS entrance now starts with reducing phone
VPN switching and names the exact Mintie coverage and client-access limits.
It adds a reading projection, not a new operational authority or a claim that
F3's engine-specific configurations and live negative proofs are complete.

### F0.3 — Underlay observability (`completed-at-source-boundary`)

Make a degraded household or WAN underlay observable even when control-plane
and proxy-lane reports are healthy. Add the `network-underlay` deployment
subject kind and `underlay-operational` profile kind with required dimensions
`transport`, `dns`, `responsiveness`, and `availability`; add the portable
`latency-envelope-breach`, `recent-link-flap`, and `shaping-unverified` reason
codes; extend the Mintie reference example with a public-safe underlay subject,
profile, report, and aggregate member; and add `FAIL-010` for green proxy lanes
hiding a degraded DIRECT underlay. The underlay is observation-only, never an
egress lane, and never a proxy-failure fallback route, while SQM/shaping
activation and live enforcement stay control-plane evidence.

Stopping point reached: machine contracts, schemas, validator, behavior tests,
sample, and human/agent/reference projections agree and the local source gate
passed. Because the owning health contract gains a required profile kind, it
advances to `signalbox.health-contract/v5`, and the paired documentation
contract advances to revision 5 under its existing `signalbox.docs-pairs/v3`
schema. The tranche is source-integrated into canonical `main` by the PR #1
merge commit `5ca593db7c4ce101ee9afcc2aaf5ce1bbde9b3a2`, which passed the
post-merge hosted gate in run `35388875151`. No release or tag, installation,
activation, runtime mutation, or owner/client acceptance is claimed, and no
active F0.3 feature branch remains. F2 is the current source update; the F0.3
integration receipt remains historical.

### F2 — Complete Agent Surface (`source-integrated`)

Deliver one executable task entrance, exact implementation/source map, patch
protocol, compatibility handling, stop rules, actual claim/acceptance/handoff
objects, structured private-ingress chain diagnostics, and a synthetic
start-order current-pointer/CAS reference. The canonical evaluator validates
standalone profiles and malformed nested reports and rejects observation-age
or attempt-duration violations. Catalog revisions agree with their applicable
owners/instances independently of profile configuration revisions.

Source acceptance includes legal capability extensions and broken
host/role/health links, HTTPS downgrade, malformed report/profile types,
stale-observation wrapping, exact compare races, late completion, uncertain
restart, and concrete handoff reference/scope/time failures. Five paired
judgment cases are pulled forward from F3/F4 to exercise this same boundary.
The source model emits decisions using an in-memory lock; durable pointer
storage, cross-process CAS and actual recovery effects belong to separately
authorized deployments. Full F3 configuration/negative-proof material and F5
historical compatibility/supply-chain work remain pending.

Status: source-integrated through PR #3; local repository verification and Git
closure are recorded in `docs/current-state.md`. No release, installation,
activation, live network mutation or owner acceptance is implied.

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

The 2026-10-04 discussion corrected a proposed network-reasoning textbook
direction toward useful arrangements for everyday devices. The adopted
reading station leads with those arrangements and retains exact mechanism and
evidence references underneath. A new Mesh return-route laboratory is not an
execution tranche: it was superseded as the proposed centre of the work.
Full mobile-client access recipes, concrete engine configuration and deployment
acceptance remain F3/implementation work; visual navigation cannot establish them.

## Full acceptance

Programme completion is the verified closure of every `ACCEPT-*` row, not the
completion of Foundation 0.1. Each tranche reports its own stopping point.
