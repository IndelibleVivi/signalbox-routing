---
doc_id: signalbox.human.routing-dns-fail-closed
language: en
status: f1-reader-path
authority: ../specification.md
contract_revision: 3
---

**English** · [简体中文](30-routing-dns-and-fail-closed.zh-CN.md)

<a id="routing-owner"></a>
# Routing, DNS, and fail-closed policy

This path is for the person designing the router control plane. The key rule is
one transparent routing owner per protected deployment scope. `ROUTE-01`

“One owner” does not mean one process. A resolver, firewall, proxy engine, and
health observer may cooperate. It means their responsibilities are explicit:
one policy decides classification and route action; no second engine silently
competes for interception, packet marks, default routes, or DNS answers.

Before implementation, record:

- captured client scope and exclusions;
- interception point for TCP, UDP, and DNS;
- portable roles and their private bindings;
- route precedence and failure action;
- enforcement owner and management exception;
- observation owner, report location, and freshness policy.

<a id="dns-ownership"></a>
## DNS is part of routing ownership

Transparent traffic policy cannot assume every client will use the router's
ordinary resolver. Clients may cache answers, use encrypted DNS, reuse
connections, or retain Service Worker state. Decide which mechanism owns each
question:

| Question | Required decision |
| --- | --- |
| Which hostname was requested? | DNS capture, protocol sniffing, or an explicit application signal |
| Which address should be dialed? | Resolver result or a bounded destination override |
| Which resolver sees the query? | One declared resolver path per policy scope |
| What happens to unsupported QUIC? | Route through a proven protected transport or reject it |

A hostname match and a destination override are different operations. For a
canonical private path, an implementation may use split DNS plus SNI sniffing
and an `override_address`-style dial target. The browser must still present the
canonical hostname and validate the canonical certificate; the private address
is a deployment binding, not the user-facing origin.

`ROUTE-05` rejects protected UDP/443 until that transport is independently
proved. Rejection is preferable to a quiet direct escape.

<a id="route-precedence"></a>
## Evaluate specific routes before general routes

`ROUTE-04` `ROUTE-06`

The Mintie reference order expresses the portable intent:

1. observe protocol and capture client DNS;
2. match approved canonical private ingress;
3. enforce protected UDP policy;
4. match the high-recall protected application set;
5. evaluate explicit private and ordinary DIRECT allowlists;
6. send everything else requiring proxy to pinned `general-primary`.

The important overlap is private ingress versus DIRECT. A broad private-address
allowlist must not consume the canonical hostname first, or the packet bypasses
the dedicated gateway identity. General egress and private-ingress capability
remain separate even when they share a host.

Protected application matching optimizes for recall. First-party, auth,
storage, telemetry, risk, and observed compatibility dependencies may share its
egress. If that role is unavailable, matched traffic fails; it does not move to
general primary, general secondary, or DIRECT.

<a id="fail-closed-enforcement"></a>
## Keep enforcement independent

`ROUTE-02` `ENFORCE-01`

The routing process chooses the intended path. The guard prevents forbidden
public DIRECT when the process or kernel state cannot be trusted. Verify both:

- process/config evidence cannot prove the guard is present;
- guard presence cannot prove an upstream route succeeds;
- a failed safe-state setup retains the guard;
- management and break-glass access remain explicitly bounded;
- recovery never uses “release direct” as an ordinary diagnostic shortcut.

An implementation-specific firewall, policy table, or mark may satisfy this
contract. Those identifiers do not become Signalbox-wide constants.

<a id="health-and-recovery"></a>
## Observe first; mutate under another contract

`HEALTH-07` `HEALTH-15`

Health reports observe the control plane and each lane separately. Query
failure remains `unknown`. A recovery-preflight report may open only the exact
restore gate bound to its operation, desired state, observed runtime generation,
and scope. Ordinary operational health never authorizes route mutation.

A deployment aggregate is a historical receipt. Its `evaluated_at` equals
`assembled_at`, and member values are named
`effective_outcome_at_assembly`. Do not re-read an old aggregate as current
health; assemble a new one from fresh member reports.

Automatic failover, if a deployment later chooses it, needs a separate state
machine with hysteresis, operation identity, rollback, and receipts. A latency
selector is not strict primary/secondary policy.

Continue with [Tailnet and VPS private ingress](40-tailnet-vps-private-ingress.en.md)
only when the deployment needs canonical private access.
