# Health and Observability

Normative source: `contracts/health-contract.json`
Sample profiles: `examples/mintie/health-profiles.json`

Health answers “what can be established now, at which boundary?” It does not
answer “which route should be selected next?” and does not repair the system.

## Profile and report

A `HealthProfile` is versioned observation policy. `recovery-preflight` covers
only the dimensions needed to decide whether restore can proceed safely.
`operational` covers the complete path. A recovery-preflight pass therefore
does not claim operational health.

Every attempt emits an immutable `HealthReport`. The current report pointer is
atomically replaced, and pass, fail, and unknown attempts all advance the
monotonic generation. An early failure cannot leave yesterday's PASS as the
newest apparent truth.

## Dimensions

| Dimension | Question |
| --- | --- |
| `transport` | Can the lane complete the intended transport? |
| `exit-identity` | Does observed egress satisfy its role policy and differ from forbidden direct egress? |
| `dns` | Are local, direct, and proxied resolver paths behaving under their own ownership? |
| `control-plane` | Is the routing process running with the expected loaded state? |
| `enforcement` | Are interception, policy rules, and fail-closed enforcement observable? |
| `resources` | Is memory, swap, storage, load, and OOM evidence inside the deployment envelope? |
| `persistence` | Are boot, hotplug, scheduling, and durable-state owners present and inspectable? |
| `recovery-readiness` | Can prior state be queried and reconciled safely after boot or failure? |

## Outcome lifecycle and freshness

```text
checking -> pass | fail | unknown
```

`checking` is transient. Recorded and effective outcomes differ when evidence
is no longer usable:

```text
recorded pass + now <= valid_until + generation/profile match -> effective pass
recorded pass + stale, regressed, malformed, or mismatch       -> effective unknown
```

`unknown` cannot open a restore gate. A passing operational report also cannot
open it; only the named current `recovery-preflight` profile may do so.

## Privacy, dependency groups, and retention

Durable reports use coarse reason codes and bounded metrics. Exact exit
addresses, client identities, raw URLs, raw responses, and credentials do not
belong in ordinary reports. Each dimension names a dependency group so a shared
provider or subsystem can be recognized as common-mode evidence rather than
counted as several independent successes.

History declares maximum file size, archive count, and entry count. Resource
thresholds belong to the deployment envelope, not a universal router constant.

## Probe diversity

A shared trace service can help observe egress identity, but cannot be the sole
availability truth for every lane. Keep transport-neutral evidence and
role-specific evidence separate so one provider outage does not collapse the
entire health model into one false system-wide failure.
