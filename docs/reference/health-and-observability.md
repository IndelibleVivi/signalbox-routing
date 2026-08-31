# Health and Observability

- Normative source: [`contracts/health-contract.json`](../../contracts/health-contract.json)
- Sample profiles: [`examples/mintie/health-profiles.json`](../../examples/mintie/health-profiles.json)
- Sample aggregate: [`examples/mintie/health-aggregate.json`](../../examples/mintie/health-aggregate.json)

Health answers “what can be established now, for exactly which subject and
evidence scope?” It does not answer “which route should be selected next?” and
does not repair the system.

## Profile topology

| Profile kind | Subject cardinality | May gate restore | Aggregate member |
| --- | --- | --- | --- |
| `recovery-preflight` | one control plane | yes, exact context only | no |
| `control-plane-operational` | one control plane | no | yes |
| `lane-operational` | one egress or private-ingress lane | no | yes |

A deployment registers its health subjects explicitly. Every profile binds one
`subject_ref`; every report must match that profile and subject. A recovery
pass therefore cannot stand in for operational evidence, and one lane cannot
stand in for another.

## Dimensions and observations

| Dimension | Question |
| --- | --- |
| `transport` | Can this exact lane complete the intended transport? |
| `exit-identity` | Does observed egress satisfy this role policy and differ from forbidden direct egress? |
| `dns` | Is this lane's resolver path behaving under its declared ownership? |
| `control-plane` | Is the routing process running with the expected loaded state? |
| `enforcement` | Are interception, policy rules, and fail-closed enforcement observable? |
| `resources` | Is memory, swap, storage, load, and OOM evidence inside the deployment envelope? |
| `persistence` | Are boot, hotplug, scheduling, and durable-state owners present and inspectable? |
| `recovery-readiness` | Can prior state be queried and reconciled safely after boot or failure? |

A dimension contains an `observations` array. Each observation names its probe,
evidence class, dependency group, terminal state, observation time, and a
privacy-safe reason code when state is `fail` or `unknown`. Dimension state is
computed from those observations; report state is computed from required
dimensions:

```text
any required fail -> fail
else any unknown  -> unknown
else              -> pass
```

Profile requirements make diversity testable. For example, a lane transport
pass requires both transport-neutral and role-specific evidence across at
least two dependency groups. Two labels backed by one provider do not become
independent evidence.

## Report identity, sequence, and freshness

Every attempt emits an immutable terminal `HealthReport`. The current pointer
is atomically replaced, and pass, fail, and unknown attempts all advance the
sequence so an early failure cannot leave yesterday's PASS as apparent current
truth.

Generation is monotonic only within:

```text
producer_ref + subject_ref + profile_ref + generation_epoch
```

The epoch is durable across ordinary process and boot restarts and changes only
through explicit reset or migration. A same-epoch regression or unexpected
epoch becomes effective `unknown`.

`valid_until` is bounded by the referenced profile:

```text
valid_until <= completed_at + profile.max_report_age_seconds
published_at <= valid_until
```

Recorded and effective outcomes therefore differ when evidence is stale,
malformed, regressed, or mismatched:

```text
recorded pass + fresh + expected scope/revision/epoch -> effective pass
recorded pass + unusable evidence                     -> effective unknown
```

## Member-preserving aggregate

The deployment aggregate is a receipt over current operational member reports.
It preserves each subject, report ID, profile revision, producer, epoch,
generation, and effective outcome. It excludes recovery-preflight and has no
top-level `outcome`; partial failure remains visible instead of collapsing into
an unexplained “network unhealthy” bit.

## Exact recovery gate

Only `recovery-preflight` may gate restore. Its `gate_context` binds:

- `operation_ref`;
- `desired_state_digest`;
- `observed_runtime_generation`; and
- `restore_scope_ref`.

The expected context and epoch must exact-match a fresh effective `pass`.
`unknown` cannot open the gate, and a pass for one operation, desired state,
runtime generation, or scope cannot authorize another.

## Privacy and retention

Durable reports use coarse reason codes and bounded metrics. Exact exit
addresses, client identities, raw URLs, raw responses, and credentials do not
belong in ordinary reports. History declares maximum file size, archive count,
and entry count. Resource thresholds belong to the deployment envelope, not a
universal router constant.

All profiles, reports, and aggregates are observation-only. Automated failover
or repair requires a separate mutation state machine, hysteresis, operation
identity, authorization, rollback, and its own receipt.
