# Implementation Reference

## Normative source map

| Concern | Normative source | Primary specification IDs |
| --- | --- | --- |
| Project and reference identity | `contracts/roles.json`, `examples/mintie/deployment.json` | `IDENT-01` to `IDENT-03` |
| Realization and acceptance boundaries | `contracts/claims.json` | `CLAIM-01` to `CLAIM-03` |
| Traffic actions and fallback | `contracts/traffic-policy.json` | `ROUTE-01` to `ROUTE-05` |
| Enforcement and restore gates | `contracts/traffic-policy.json` | `ENFORCE-01`, `ENFORCE-02` |
| Private ingress | roles plus traffic policy | `PRIVATE-01` to `PRIVATE-04` |
| Health profiles and reports | `contracts/health-contract.json` | `HEALTH-01` to `HEALTH-09` |
| Documentation parity | `contracts/docs-pairs.json` | `DOC-01` to `DOC-04` |

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
- The protected-application object structurally lacks fallback fields. Do not
  encode “none” in a field whose presence encourages consumers to implement a
  fallback mechanism.
- Default general egress is pinned; a secondary role does not activate itself.
- Private-ingress gateway capability is distinct from general egress.
- A fresh passing `recovery-preflight` report may open a restore gate.
  `operational` health cannot open that gate or mutate routing.

An implementation may use different engines, transports, firewall backends,
or policy-table identifiers. Those are deployment bindings unless a portable
contract depends on them.

## HealthProfile and HealthReport

`HealthProfile` is mutable configuration with an explicit revision. It declares
the purpose, required dimensions, schedule or triggers, freshness, publication,
privacy, retention, and resource-threshold owner.

`HealthReport` is an immutable observation conforming to
`signalbox.health-report/v1`:

```json
{
  "schema": "signalbox.health-report/v1",
  "id": "report-id",
  "profile_ref": "profile-id",
  "profile_revision": 1,
  "producer_ref": "deployment-id",
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
      "evidence_class": "transport-neutral",
      "observed_at": "RFC3339 timestamp",
      "dependency_group": "neutral-transport"
    }
  }
}
```

Every dimension required by the referenced profile is present. A failing or
unknown dimension adds a privacy-safe `reason_code`; a passing dimension must
not. Reports may add bounded coarse metrics, but never forbidden durable keys.

Rollup order is:

```text
any required fail -> outcome fail
else any unknown  -> outcome unknown
else              -> outcome pass
```

Every attempt publishes a terminal report using atomic replacement of the
current pointer. Failed and unknown attempts advance generation. After
`valid_until`, after a generation regression, or under a profile revision
mismatch, effective outcome is `unknown` regardless of recorded `outcome`.

## Recovery-readiness semantics

Recovery readiness reports whether the implementation can safely observe and
reconcile the state it intends to restore. It includes:

- queryability of policy tables, hooks, rules, and service state;
- ownership of durable desired state;
- ability to distinguish verified `OFF` from `UNKNOWN`;
- a named recovery outcome when postconditions cannot be established.

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
