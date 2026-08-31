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

## `FAIL-007` — General DIRECT shadows canonical private ingress

- First broken boundary: ordered route precedence.
- Pattern: a private-address or approved-direct allowlist is evaluated before
  the more specific canonical-origin private-ingress match.
- Unsafe interpretation: independently reasonable sets are assumed never to
  overlap, so rule order does not matter.
- Portable response: evaluate canonical private ingress before every DIRECT
  class and retain overlap/order negative tests.
- Protecting contracts: `ROUTE-02`, `ROUTE-06`, `PRIVATE-01`.

## `FAIL-008` — One deployment report hides a broken lane

- First broken boundary: observation subject identity.
- Pattern: one transport and exit result is labelled as health for a deployment
  containing several independent egress and private-ingress lanes.
- Unsafe interpretation: one green lane means all lanes are green, or one
  failure becomes an unexplained deployment-wide red bit.
- Portable response: bind reports to one control plane or lane and aggregate by
  immutable member reference without a top-level outcome.
- Protecting contracts: `HEALTH-09`, `HEALTH-10`.

## `FAIL-009` — A fresh PASS escapes its sequence or restore scope

- First broken boundary: evidence identity and recovery authorization.
- Pattern: generation is compared globally, producer chooses unbounded
  `valid_until`, or a recovery pass for one desired state is reused for another.
- Unsafe interpretation: a larger number or recent timestamp makes any report
  current and authorizes restore.
- Portable response: scope generation by producer, subject, profile, and durable
  epoch; bind freshness to the profile; exact-match restore gate context.
- Protecting contracts: `HEALTH-11`, `HEALTH-12`, `HEALTH-13`.
