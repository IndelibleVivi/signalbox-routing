# Implementation Reference

## Normative source map

| Concern | Normative source | Primary specification IDs |
| --- | --- | --- |
| Project and reference identity | `contracts/roles.json`, `examples/mintie/deployment.json` | `IDENT-01` to `IDENT-03` |
| Realization and acceptance boundaries | `contracts/claims.json` | `CLAIM-01` to `CLAIM-03` |
| Traffic actions, precedence, and fallback | `contracts/traffic-policy.json`, `examples/mintie/traffic-policy.json` | `ROUTE-01` to `ROUTE-07` |
| Enforcement and restore gates | `contracts/traffic-policy.json` | `ENFORCE-01`, `ENFORCE-02` |
| Private ingress | roles plus traffic policy | `PRIVATE-01` to `PRIVATE-04` |
| Health profiles, observations, reports, and aggregates | `contracts/health-contract.json` | `HEALTH-01` to `HEALTH-17` |
| Documentation parity | `contracts/docs-pairs.json` | `DOC-01` to `DOC-05` |
| Structural schemas and compatibility routing | `contracts/catalog.json`, `schemas/` | `AUTH-03` to `AUTH-05` |

## Role binding and action rules

An implementation binds an instance identity to one or more portable roles.
Each binding is evaluated independently. Co-location may share a host but may
not share credential scope or silently inherit capabilities.

```text
routing-control-plane -> owns transparent policy
general-primary       -> pinned default proxy-required path
general-secondary     -> independent standby; no implied auto-failover
claude-residential    -> protected high-recall path; no fallback field
private-ingress-*     -> dedicated server-controlled identities
DIRECT                -> explicit-allowlist action; never a role or fallback
```

## TrafficPolicy invariants

- Exactly one role owns transparent policy for a deployment.
- Protected scope failure mode is `fail-closed`.
- Query failure produces `unknown`.
- DIRECT cannot be a default or proxy-failure fallback.
- Canonical private ingress is evaluated before every DIRECT allowlist. A broad
  private or approved-direct set may overlap but cannot shadow the more
  specific gateway action.
- The protected-application object structurally lacks fallback fields. Do not
  encode “none” in a field whose presence encourages consumers to implement a
  fallback mechanism.
- Default general egress is pinned; a secondary role does not activate itself.
- Private-ingress gateway capability is distinct from general egress.
- The Mintie reference projection binds all eight settled route IDs to exact
  actions, match forms, and field sets. An implementation may translate that
  grammar into its own engine, but the source projection cannot silently swap
  an action or retain an extra field.
- A fresh passing `recovery-preflight` report may open only the exact restore
  gate named by its operation, desired-state digest, runtime generation, and
  restore scope. Operational health cannot open that gate or mutate routing.

An implementation may use different engines, transports, firewall backends,
or policy-table identifiers. Those are deployment bindings unless a portable
contract depends on them.

## HealthProfile and HealthReport

`HealthProfile` is mutable configuration with an explicit revision. It declares
the purpose, required dimensions, schedule or triggers, freshness, publication,
privacy, retention, and resource-threshold owner.

Profile topology is total and type-safe: each registered control-plane subject
has exactly one `recovery-preflight` and one `control-plane-operational`
profile, and each registered egress or private-ingress lane has exactly one
`lane-operational` profile. A wrong-kind, missing, duplicate, or orphan binding
is invalid. `HEALTH-17`

`HealthReport` is an immutable, single-subject observation conforming to
`signalbox.health-report/v2`:

```json
{
  "schema": "signalbox.health-report/v2",
  "id": "report-id",
  "profile_ref": "profile-id",
  "profile_revision": 1,
  "producer_ref": "observer-id",
  "subject_ref": "role-binding/example",
  "generation_epoch": "durable-epoch-id",
  "generation": 42,
  "attempt_id": "attempt-id",
  "started_at": "RFC3339 timestamp",
  "completed_at": "RFC3339 timestamp",
  "published_at": "RFC3339 timestamp",
  "valid_until": "RFC3339 timestamp",
  "outcome": "pass | fail | unknown",
  "dimensions": {
    "transport": {
      "state": "pass | fail | unknown",
      "observations": [
        {
          "probe_ref": "neutral-https",
          "evidence_class": "transport-neutral",
          "dependency_group": "neutral-connectivity",
          "state": "pass | fail | unknown",
          "observed_at": "RFC3339 timestamp"
        },
        {
          "probe_ref": "role-path",
          "evidence_class": "role-specific",
          "dependency_group": "role-policy",
          "state": "pass | fail | unknown",
          "observed_at": "RFC3339 timestamp"
        }
      ]
    }
  }
}
```

Every dimension required by the referenced profile is present. Its state rolls
up explicit observations. Failing or unknown observations add a privacy-safe
`reason_code`; passing observations do not. Profile requirements enforce
minimum observations, evidence classes, and dependency groups. Reports may add
bounded coarse metrics, but never forbidden durable keys.

Rollup order is:

```text
any required fail -> outcome fail
else any unknown  -> outcome unknown
else              -> outcome pass
```

Every attempt publishes a terminal report using atomic replacement of the
current pointer. Failed and unknown attempts advance generation. Generation is
monotonic only inside `producer_ref + subject_ref + profile_ref +
generation_epoch`; an epoch changes only through explicit reset or migration.
The canonical evidence evaluator first validates the report schema and all
report/profile semantics, then requires
`published_at <= evaluated_at <= valid_until`. When a decision expects current
evidence, it exact-matches `producer_ref`, `subject_ref`, `profile_ref`,
`profile_revision`, `generation_epoch`, `generation`, report `id`, and
`attempt_id`. Unpublished or expired evidence, a same-epoch regression, an
unexpected epoch, any identity mismatch, or any invalid shape or semantic
rollup yields effective `unknown` regardless of recorded `outcome`. A higher
generation also mismatches: abort the decision and re-read the current pointer
instead of interpreting it as “new enough.” `HEALTH-16`

Operational profiles bind the control plane and each lane separately. A
`signalbox.health-aggregate/v2` receipt references immutable report identity
and generation for every subject, excludes recovery-preflight, and has no
top-level `outcome`. Every member passes through the canonical evidence
evaluator at `assembled_at`, while aggregate validation exact-checks its
recorded member identity fields. Its `evaluated_at` equals `assembled_at`, and
each member stores `effective_outcome_at_assembly`. Treat it as immutable
historical evidence. Build a new aggregate when a current view is required;
never age or rewrite the stored member outcomes in place. `HEALTH-15`

## Recovery-readiness semantics

Recovery readiness reports whether the implementation can safely observe and
reconcile the state it intends to restore. It includes:

- queryability of policy tables, hooks, rules, and service state;
- ownership of durable desired state;
- ability to distinguish verified `OFF` from `UNKNOWN`;
- a named recovery outcome when postconditions cannot be established.

Its `gate_context` binds `operation_ref`, `desired_state_digest`,
`observed_runtime_generation`, and `restore_scope_ref`. The gate also
exact-matches the full expected current report identity listed above. Only a
canonically valid, published, fresh pass for that one context and identity may
open the gate. A newer report forces an abort and current-pointer re-read; it
does not inherit authorization from an older expectation.

This repository implements the source decision contract, not the runtime
current-pointer CAS/lock protocol. A deployment must still make its read and
mutation state machine race-safe and emit its own receipt.

Platform-specific table warm-up, module loading, or listener initialization
may satisfy the contract, but those mechanisms do not become portable
requirements merely because one deployment needed them.

## Claims and acceptance

Use the narrowest technical stage the evidence supports:

```text
SOURCE_VERIFIED
INSTALLED_OBSERVED
ACTIVATED_OBSERVED
PATH_EVIDENCE_OBSERVED
UNKNOWN_AT_<STAGE>
```

An `AcceptanceRecord` is orthogonal. It records `accepted`, `rejected`, or
`revoked` for a named actor, scope, claims, and evidence at a decision time. It
does not upgrade a realization stage and is not current path proof. Never
compress several stages or a decision into the word `healthy`.
