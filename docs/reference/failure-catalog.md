# Failure Catalog

This catalog stores redacted reusable mechanisms, not raw incident chronology
or current live-system truth.

## `FAIL-001` — Unqueryable state mistaken for absence

- First broken boundary: recovery-readiness / enforcement observation.
- Pattern: a platform query fails for a logically empty but not-yet-instantiated
  kernel object.
- Unsafe interpretation: convert query failure to `OFF` or continue teardown.
- Portable response: report `unknown`, retain fail-closed protection, and make
  queryability a precondition for restore.
- Implementation-specific example: initialize then clear the relevant kernel
  object before reconciliation.
- Protecting contracts: `CLAIM-03`, `HEALTH-07`, `ENFORCE-01`.

## `FAIL-002` — Stale success survives a failed health run

- First broken boundary: status publication.
- Pattern: the health process exits early and only writes a report after total
  success, leaving the previous success file in place.
- Unsafe interpretation: newest file equals newest attempted generation.
- Portable response: every attempt atomically publishes a terminal immutable
  report, advances generation, and consumers enforce `valid_until` plus profile
  and generation continuity.
- Protecting contracts: `HEALTH-02`, `HEALTH-03`, `HEALTH-09`.

## `FAIL-003` — Endpoint green hides resource pressure

- First broken boundary: resource envelope.
- Pattern: transport probes pass while routing-process memory, compressed swap,
  storage, or OOM history approaches failure.
- Unsafe interpretation: reachable endpoint means healthy control plane.
- Portable response: observe resource and OOM evidence separately, declare an
  owner-defined envelope, and bound persistent logs.
- Protecting contract: `HEALTH-05`.

## `FAIL-004` — One external probe becomes whole-system truth

- First broken boundary: evidence independence.
- Pattern: every lane uses one provider for reachability and exit identity.
- Unsafe interpretation: provider failure means all transports failed.
- Portable response: distinguish transport-neutral and role-specific probes;
  preserve common-mode uncertainty.
- Protecting contract: `HEALTH-08`.

## `FAIL-005` — Standby existence presented as automatic failover

- First broken boundary: selection semantics.
- Pattern: an independently healthy secondary or latency test is described as
  strict ordered failover.
- Unsafe interpretation: health observation implies route mutation.
- Portable response: keep selection manual unless a separate state machine
  defines hysteresis, dwell, switch receipt, and rollback.
- Protecting contracts: `ROUTE-03`, `HEALTH-06`, `PRIVATE-03`.

## `FAIL-006` — Client identity drifts away from route scope

- First broken boundary: deployment binding.
- Pattern: a source IP changes owners while guard and routing components rely
  on different observations of IP/MAC/lease identity.
- Unsafe interpretation: a current DHCP address is a stable client identity.
- Portable response: reserve identity, seal the binding for an operation, and
  revalidate it before mutation. Keep exact identities outside Signalbox.
- Protecting contracts: `IDENT-02`, `UPDATE-03`.
