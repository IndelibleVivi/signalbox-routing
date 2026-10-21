---
doc_id: signalbox.human.worked-cases
language: en
status: source-reference
authority: ../specification.md
contract_revision: 6
---

**English** · [简体中文](50-worked-cases.zh-CN.md)

# Seven judgments worth reading closely

synthetic replay originally supplied five replayable judgments; two explanatory
cases below examine external mechanisms. The replay inputs are
[synthetic](../../examples/scenarios/cases.json). The replay uses the canonical
route grammar and health evaluator; supplied route matches and observation
labels are models, not DNS queries, packet capture or radio diagnosis.

Cases 6 and 7 cover Tailscale 4via6 and prefix failover. They are not entries in
`examples/scenarios/cases.json` and do not call the replay evaluator: they use
public documentation to explain routing mechanics and produce no live or
synthetic PASS/FAIL conclusion.

```bash
.venv/bin/python -m scripts.replay
.venv/bin/python -m scripts.replay --case canonical-direct-overlap
```

Each JSON result contains `expected`, `actual` and `passed`. The same scenarios
run in [agent surface tests](../../tests/test_agent_surface.py).

<a id="canonical-direct-overlap"></a>
## 1. Canonical hostname also matches DIRECT

**Symptom:** an approved private-service hostname belongs to both the private
origin set and a broad DIRECT allowlist. `ROUTE-06` `PRIVATE-01` `PRIVATE-02`

**Known / unknown:** the synthetic matches include canonical private ingress
and both DIRECT rules. The source supplies Alder Private, its Alder host,
private-ingress role and lane profile. Actual private bindings and reachability
remain unknown.

**Path and observation:** client → origin policy → Alder Private → exact private
destination. Inspect the selected route, then follow the complete gateway
chain with `.venv/bin/python -m scripts.policy`.

**Input / result:** `canonical-direct-overlap` selects
`canonical-private-ingress`, action `private-ingress`, binding `alder-private`.
Policy diagnostics identify the precise broken reference if the host, role,
capabilities, HTTPS origin or health coverage is changed.

**Wrong inference / disproof:** “It is in a DIRECT set, so direct is equivalent.”
The earlier canonical match selects a dedicated identity. Move DIRECT earlier
or replace the action and source validation rejects the policy.

**Allowed conclusion:** source precedence protects the dedicated path. This
does not prove private connectivity, server authorization or browser acceptance.

<a id="domain-versus-ip-only"></a>
## 2. Domain DIRECT, same application's IP-only request proxy-required

**Symptom:** one application appears to use two paths. `ROUTE-02` `ROUTE-07`

**Known / unknown:** the domain request matches `approved-direct`; a second
connection has no usable domain match and only matches the default. Whether a
real deployment recovers the hostname through DNS ownership or sniffing is
still unknown.

**Path and observation:** domain evidence → allowlist → DIRECT; IP-only
destination → default → Alder. Observe each connection's available match
information, not only the application name.

**Input / result:** `domain-versus-ip-only` returns domain route
`approved-direct`, IP route `default-proxy-required`, and
`same_application_implies_same_route: false`.

**Wrong inference / disproof:** “A domain rule covers the whole application.”
The IP-only connection lacks that match. Connection-level selection evidence
can disprove the application-wide claim.

**Allowed conclusion:** both selections obey the reference. Protected traffic
still requires its high-recall set; this case grants no protected bypass.

<a id="router-probe-versus-lan"></a>
## 3. Router-local lane probes pass, LAN client fails

**Symptom:** a lane probe is green while a phone cannot connect. `CLAIM-02`
`HEALTH-10` `ENFORCE-01`

**Known / unknown:** egress transport passed. LAN admission, interception,
mark/policy routing and local delivery were not observed.

**Path and observation:** follow the
[TProxy packet path](10-architecture.en.md#actual-packet-path). The explicit
router-local probe starts at egress; the phone traverses admission and
PREROUTING interception, mark-to-table routing and the transparent socket.
Forwarding guards and local-delivery admission must be checked at their actual
deployment hooks.

**Input / result:** `router-probe-versus-lan` supplies only egress PASS. Required
client-path coverage yields `unknown` and lists the four skipped boundaries.
Adding all four passing observations permits a coverage PASS; an observed
failure yields FAIL. These are evidence-coverage outcomes, not health reports.

**Wrong inference / disproof:** “The lane passed, therefore the phone reached
it.” A synchronized client attempt with admission/interception/local-delivery
readback can locate the first boundary it failed to cross.

**Allowed conclusion:** upstream reachability is established only for the
probe. The next useful evidence distinguishes admission, interception, local
delivery and dial-out; a service restart alone does not make that distinction.

<a id="awake-versus-sleeping"></a>
## 4. Awake devices work, sleeping devices stall

**Symptom:** sleeping clients show delays while awake clients on the same AP
remain responsive. `CLAIM-03` `HEALTH-06`

**Known / unknown:** synchronized synthetic AP-to-client observations pass for
awake clients and fail for sleeping clients; AP-to-upstream controls pass for
both. Device class and sleep behavior are observed variables. The exact driver,
buffering, wake timing or interference cause remains unknown.

**Path and observation:** compare the AP-to-client delivery path at the same
radio and time against an AP-to-upstream control. Keep observations scoped to
the affected client class.

**Input / result:** `awake-versus-sleeping` returns awake PASS, sleeping FAIL,
fault boundary `client-radio-interaction`, root cause `unknown`. If the upstream
control also fails, that localization is withdrawn.

**Wrong inference / disproof:** “The awake client proves the radio is healthy”
or “the changed client must contain the defect.” Sleep-path observations
disprove the first. A client change can expose a latent AP defect; change
trigger, failure mechanism and best repair location may differ.

**Allowed conclusion:** prioritize controlled sleep/delivery comparisons.
Firmware/config history adjusts experimental priority; it cannot exclude a
latent infrastructure defect. See `FAIL-011` and `FAIL-012` in the
[failure catalog](../reference/failure-catalog.md). Tests do not authorize a
radio, firmware or client configuration change.

<a id="new-report-old-observations"></a>
## 5. Just-published report, expired internal evidence

**Symptom:** a new completion timestamp appears to permit restore despite old
checks. `HEALTH-12` `HEALTH-16` `HEALTH-20`

**Known / unknown:** identity and gate context are unchanged; completion and
publication remain at the sample time. Start and all observations move 61 days
earlier. Current kernel state was never re-observed.

**Path and observation:** observer → timed observations → immutable report →
canonical evaluator → exact restore decision.

```text
old probe ---- observation expiry ........ new completion / publication
                    authority ended              cannot renew it
```

**Input / result:** `new-report-old-observations` returns effective `unknown`
and `restore_allowed: false`. Profile limits bound attempt duration and every
required observation, as well as report age. The earliest required evidence
expiry caps `valid_until`.

**Wrong inference / disproof:** “The report just completed, so all checks are
fresh.” Compare actual observation times to the referenced profile limits.
The canonical evaluator rejects the stale-evidence wrapper.

**Allowed conclusion:** retain the guard and perform a new authorized
preflight. Publication alone cannot renew evidence or restore authority.

For generation 42→43, late completion and restart uncertainty, replay the three
[agent recovery races](../agent/workflow.md#recovery-sequencing).

<a id="4via6-site-identity"></a>
## 6. The same IPv4 range, two site identities

**Symptom:** home and office use the same private IPv4 range. Looking only at
`site A LAN ↔ site B LAN`, the routers seem to belong to "the same network,"
yet they are distinct sites and their old devices may share an IPv4 address.

**This is not an executable replay.** It is an explanatory case about an external
mechanism and is not added to `examples/scenarios/cases.json`. It does not compute
subnet routes, probe nodes, or issue a live or synthetic PASS/FAIL conclusion.

**Mechanism:** a bare IPv4 subnet route cannot distinguish two sites from one
identical prefix alone. Tailscale's
[4via6 subnet documentation](https://tailscale.com/docs/features/subnet-routers/4via6-subnets)
encodes a site identity into a unique IPv6 mapping, so the existing IPv4
addresses can stay unchanged while "the LAN at site A" and "the LAN at site B"
remain distinct.

```text
IPv4 prefix P at site A --site A mapping--> Tailnet reachability
IPv4 prefix P at site B --site B mapping--> different Tailnet reachability
                 same P                              distinct identity
```

**Redundancy for one site:** if two routers use the same site ID and mapping,
they can advertise the same prefix for the same site and provide redundancy.
Using that same site ID for another site would collapse two different
destinations into one identity.

**Version check before deployment:** the official 4via6 page, read on 2026-10-22,
says to upgrade routers to Tailscale 1.102.3 or later for security and links the
relevant advisory. A site mapping is not evidence that an older release is safe
to deploy. For ordinary IPv4 subnet SNAT and return paths, see the
[travel-router article](60-travel-router.en.md#subnet-path).

**Allowed conclusion:** 4via6 expresses the identity of overlapping IPv4 sites.
It neither renumbers devices nor proves policy, DNS, firewall, or path health.
The deployment still needs named path evidence.

<a id="prefix-failure-vs-redundancy"></a>
## 7. A failed specific prefix does not fall through to a broader route

**Symptom:** configuration contains a broader route and a more specific prefix;
the router behind the specific route goes offline. It is tempting to assume the
broader route will take over after the page fails.

**This is not an executable replay.** Like case 6, it explains an external
product mechanism and is not added to the eight canonical scenarios. The text
path is not route-table readback or evidence of any node's current state.

```text
specific prefix ---- offline router ---- X
                    no automatic fallthrough
broader prefix  ---- other router ----> separate candidate only
```

**Mechanism:** Tailscale's
[overlapping subnet route failover
documentation](https://tailscale.com/docs/reference/troubleshooting/network-configuration/overlapping-subnet-route-failover)
distinguishes exact-prefix failover from less-specific fallback: a more specific
route does not automatically use a broader route merely because its router
is unavailable. A `via` filter chooses which routers are eligible; it does
not assign an ordered automatic fallback.

**Redundancy at the same prefix:** multiple eligible routers for one exact prefix
provide a set of repeated candidates. Their actual availability, advertisements,
and policy selection still require readback.

**Wrong inference / disproof:** "a broader prefix is a fallback." Observe the
selected route and the exact-prefix candidates; the broader path was not selected
automatically. A routing layer also cannot decide application authorization.

**Allowed conclusion:** retain fail or `UNKNOWN` when the specific route fails and
check whether the same exact prefix really has redundancy. Do not claim that a
broader route took over. See [peer relay and
transport](70-peer-relay.en.md#blocked-direct) and [travel routers and
client-free devices](60-travel-router.en.md#subnet-path).
