# Signalbox Product and Architecture Specification

Status: canonical working specification
Revision: 2
Authority: current Faye/Cove task decisions, with earlier Mintie materials used
as evidence rather than executable instructions

## 1. Product promise

`SIG-01` — Signalbox is a portable human-and-agent reference for router-level
traffic policy, transparent egress, fail-closed enforcement, private ingress,
health, and recovery.

`SIG-02` — Signalbox extracts reusable mechanisms from real systems without
becoming a copy, public projection, installer, or second production authority.

`SIG-03` — The repository must remain independently understandable: a reader
does not need access to Faye's private infrastructure repository or live router
to understand the portable contracts and sample deployment.

## 2. Goals

- `GOAL-01` — Teach the layers between application proxy awareness, operating
  system proxy settings, local tunnel interception, router transparency,
  routing policy, and upstream egress.
- `GOAL-02` — Define stable role, routing, evidence, health, recovery, and
  update contracts that agents can inspect and validate.
- `GOAL-03` — Preserve one concrete named reference deployment, Mintie, while
  separating sample identities from portable roles and private bindings.
- `GOAL-04` — Make failure semantics, unknown state, recovery readiness,
  observability limits, and owner-acceptance boundaries first-class.
- `GOAL-05` — Preserve the advanced canonical-origin private-ingress pattern
  without making it an implicit requirement for every router deployment.

## 3. Non-goals

- `NONGOAL-01` — No credential-bearing production config, live endpoint,
  provider account, private hostname inventory, IP/MAC identity, or raw
  readback belongs in this repository.
- `NONGOAL-02` — Signalbox does not install, activate, deploy, restart, recover,
  or remotely inspect a router.
- `NONGOAL-03` — Signalbox is not a social-content pipeline, a simplified post,
  a node subscription manager, a selector UI, or a universal OpenWrt recipe.
- `NONGOAL-04` — Source validation does not claim installation, activation,
  path evidence, or client health.
- `NONGOAL-05` — No repository visibility or license decision is made by this
  specification.

## 4. Authority and identity

`AUTH-01` — `docs/specification.md` owns product meaning and programme
acceptance. `contracts/*.json` own machine-readable normative semantics.

`AUTH-02` — Explanatory prose, examples, incident narratives, transcripts, and
external implementations cannot silently widen or replace normative contracts.

`AUTH-03` — `contracts/catalog.json` maps every machine contract identifier to
its current file, JSON Schema, revision owner, compatibility posture, and
dependent projections. JSON Schema owns portable structural validation;
`scripts/validate.py` owns cross-document semantic invariants that shape alone
cannot prove.

`IDENT-01` — Signalbox is the generalized project. Mintie is a reference
deployment.

`IDENT-02` — Portable role IDs, sample identities, and private live bindings
are distinct namespaces.

`IDENT-03` — A host may co-locate more than one capability, but co-location is
not role equivalence. In particular, general egress does not imply the
server-controlled identity and exact-destination policy required by a private
ingress gateway.

## 5. Evidence model

`CLAIM-01` — The ordered technical realization stages are `source`,
`installed`, `activated`, and `path-evidence`. Human or client acceptance is a
separate decision record, not a fifth technical stage.

`CLAIM-02` — Each realization stage proves only observations at that boundary.
Evidence from one stage may justify inspecting the next but cannot replace it.
An acceptance record may reference technical evidence but cannot upgrade its
stage or become fresh path proof.

`CLAIM-03` — `unknown` is a valid observation outcome at every layer. A failed,
unsupported, stale, or ambiguous query remains unknown; it is never translated
into absence, off, pass, or healthy.

## 6. Routing and enforcement

`ROUTE-01` — One transparent routing owner controls policy interception for a
deployment. Competing owners of DNS, default routes, marks, or interception
require an explicit compatibility design.

`ROUTE-02` — DIRECT is allowlist-only. Protected proxy-required traffic never
falls back to DIRECT merely because an exit, resolver, process, or route is
unhealthy.

`ROUTE-03` — The default unknown international path uses the portable
`general-primary` role. The existence of `general-secondary` does not imply
automatic failover.

`ROUTE-04` — Protected application traffic uses `claude-residential`, optimizes
for recall over precision, accepts collateral routing of shared dependencies,
and has no general or direct fallback.

`ROUTE-05` — Until a transport is independently proven for the protected lane,
protocol-specific bypasses such as direct QUIC are rejected rather than leaked.

`ROUTE-06` — Route precedence is specific before general. Canonical private
ingress is evaluated before any general private-address or approved-DIRECT
allowlist, so overlap cannot shadow the dedicated gateway action.

`ENFORCE-01` — Fail-closed enforcement is independent of the routing process
where the platform permits it. Failure to establish a safe runtime retains the
guard.

`ENFORCE-02` — Management and break-glass access must not depend exclusively on
the traffic path being repaired.

## 7. Private ingress

`PRIVATE-01` — Approved clients may reach an exact private origin while using
the same canonical HTTPS origin as the public path.

`PRIVATE-02` — Private-ingress gateway roles require dedicated authenticated
identity, server-side policy, exact approved destination access, ordinary-user
private-range denial, and independently observable health.

`PRIVATE-03` — General egress and private-ingress gateway failover are separate
policies. Latency selection is not strict ordered failover.

`PRIVATE-04` — Router activation or gateway reachability does not replace
browser, PWA, or owner acceptance on the canonical origin.

## 8. Health and observability

`HEALTH-01` — Health is multidimensional. The normative dimensions are:

- transport reachability;
- exit identity or policy conformance;
- DNS/resolver behavior;
- control-plane process and loaded state;
- enforcement/kernel state;
- resource envelope;
- persistence ownership;
- recovery readiness.

`HEALTH-02` — A `HealthProfile` declares purpose, required dimensions,
freshness, publication, privacy, and bounded retention. Every attempt publishes
an immutable `HealthReport` with profile identity and revision, producer,
monotonic generation, attempt identity, `started_at`, `completed_at`,
`published_at`, `valid_until`, terminal `outcome`, and per-dimension results.
`checking` may exist only as a transient state. Early failure still publishes a
terminal `pass`, `fail`, or `unknown` report and advances generation.

`HEALTH-03` — Consumers must evaluate freshness, generation monotonicity, and
profile revision. A report past `valid_until`, a regressed generation, or a
profile mismatch has effective state `unknown`, even when its recorded outcome
was `pass`.

`HEALTH-04` — Health dimensions use privacy-safe evidence classes, dependency
groups, and reason codes. Ordinary durable reports do not contain credentials,
full endpoints, exit IPs, client identities, or raw request histories.

`HEALTH-05` — Health history is bounded by explicit byte, archive, and entry
limits.
Resource observation includes memory availability, routing-process memory,
compressed swap when present, storage safety, load, and recent OOM evidence.

`HEALTH-06` — Health observation is not route selection or recovery mutation.
Any automatic failover or remediation requires a separate state machine,
hysteresis, operation identity, receipt, and explicit authorization.

`HEALTH-07` — Recovery readiness includes queryability. When the platform
cannot reliably observe a kernel table, rule, hook, or service state, the
result is `unknown`; recovery must not infer that the object is absent.

`HEALTH-08` — A common external probe provider cannot be the sole truth for all
lanes. Transport-neutral and role-specific evidence remain distinguishable.

`HEALTH-09` — `recovery-preflight`, `control-plane-operational`, and
`lane-operational` are different profile kinds. Recovery and control-plane
profiles observe router state; each lane profile observes exactly one egress or
private-ingress subject. None may silently substitute for another.

`HEALTH-10` — Every report binds `subject_ref` as well as profile and producer.
A deployment aggregate references immutable member report identities and
sequence positions while preserving each subject outcome; it must not flatten
partial failure into one unexplained deployment-wide health value.

`HEALTH-11` — Generation is monotonic only within the tuple
`producer_ref + subject_ref + profile_ref + generation_epoch`.
`generation_epoch` is durable across ordinary process and boot restarts and
changes only through an explicit reset or migration. Consumers treat an
unexpected epoch or a regression inside the same epoch as `unknown`.

`HEALTH-12` — A producer cannot self-issue arbitrary freshness. Every report
must satisfy `valid_until <= completed_at + max_report_age_seconds` from the
exact referenced profile, and `published_at <= valid_until`.

`HEALTH-13` — A recovery-preflight report carries an exact `gate_context`
binding the operation, desired-state digest, observed runtime generation, and
restore scope. Restore opens only when the expected context exactly matches a
fresh effective `pass` from the required profile.

`HEALTH-14` — A dimension contains one or more explicit observations. Each
observation records probe identity, evidence class, dependency group, state,
and observation time. Dimension state rolls up those observations, and profile
requirements define minimum observations, evidence classes, and independent
dependency groups so probe diversity is machine-verifiable.

## 9. Incident-derived portable lessons

`INCIDENT-01` — Cold-boot query failure showed that a logically empty policy
table may still be unqueryable on a particular platform. The portable contract
is to verify recovery queryability before state restoration and preserve
`unknown` when it cannot be established. Platform-specific warm-up is an
example implementation, not the generalized requirement.

`INCIDENT-02` — Memory pressure showed that endpoint reachability is
insufficient health evidence. Runtime memory policy, compressed swap, OOM
evidence, storage bounds, and recovery persistence belong to the health model.

`INCIDENT-03` — Success-only status publication showed that an old successful
report can impersonate current health. Terminal report publication and
freshness enforcement are normative.

## 10. Documentation architecture

`DOC-01` — Human and Agent Surfaces intentionally differ in form while sharing
role IDs, contract IDs, evidence vocabulary, and normative JSON.

`DOC-02` — Chinese and English human documents are sibling files. Paired files
must retain the required contract IDs and semantic section coverage.

`DOC-03` — Human documents explain causality, packet paths, failure stories,
and tradeoffs. Agent documents provide exact authority, input, state,
validation, stop, patch, and claim rules.

`DOC-04` — Incident chronology and private raw evidence remain outside Git.
Only a reusable, redacted mechanism enters the failure catalog.

`DOC-05` — Paired Chinese and English documents declare stable semantic section
anchors in `contracts/docs-pairs.json`. Parity validation checks both contract
IDs and required section coverage without depending on translated heading text.

## 11. Update protocol

`UPDATE-01` — A semantic change updates normative contracts first, then every
affected human, agent, example, and test projection.

`UPDATE-02` — A lesson flows from a real implementation into Signalbox only
after private/live specifics are removed and the portable mechanism is named.

`UPDATE-03` — A Signalbox improvement flows back to a private implementation
only through applicability review and separate source, installation,
activation, and path-evidence gates plus an orthogonal acceptance decision.

`UPDATE-04` — Source, commit, push, release, installation, activation,
deployment, runtime, and owner acceptance are separate authorizations and
claims.

## 12. Programme acceptance

Signalbox v1 source is complete when:

- `ACCEPT-01` — the normative role, claim, routing, health, documentation, JSON
  Schema, and catalog contracts validate together;
- `ACCEPT-02` — the Human Surface explains the complete mental model in paired
  Chinese and English documents;
- `ACCEPT-03` — the Agent Surface defines implementation, patch, evidence,
  recovery, and acceptance protocols;
- `ACCEPT-04` — Mintie demonstrates portable identity/role separation,
  specific-before-general fail-closed routing, per-subject health reports,
  member-preserving deployment aggregation, and private-ingress capability
  without private live data;
- `ACCEPT-05` — the failure catalog covers queryability, stale-success,
  resource-pressure, common-probe, and failover-semantic failures;
- `ACCEPT-06` — local and hosted validation reject broken references, unsafe
  route precedence, forbidden fallback, invalid observation/report rollups,
  generation or gate-context misuse, overlong freshness, unbounded retention,
  bilingual drift, unresolved structured identities, and machine-local paths
  without embedding private live-value denylists;
- `ACCEPT-07` — README, AGENTS, current state, examples, and contracts do not
  contradict one another;
- `ACCEPT-08` — repository license, remote, release, runtime, and owner
  acceptance are reported truthfully and never inferred.
