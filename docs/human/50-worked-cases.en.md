---
doc_id: signalbox.human.worked-cases
language: en
status: source-reference
authority: ../specification.md
contract_revision: 6
---

**English** · [简体中文](50-worked-cases.zh-CN.md)

# Five judgments you can replay

These cases teach where a conclusion becomes justified. All inputs are
[synthetic](../../examples/scenarios/cases.json). The replay uses the canonical
route grammar and health evaluator; supplied route matches and observation
labels are models, not DNS queries, packet capture or radio diagnosis.

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
