---
doc_id: signalbox.human.start-here
language: en
status: foundation-explanatory
authority: ../specification.md
contract_revision: 6
---

**English** · [简体中文](00-start-here.zh-CN.md)

<a id="proxy-layer-model"></a>
# Start here: three requests in one home

A phone and a laptop use Mintie, the sample router. Signalbox explains the
policy behind their requests and the evidence needed to judge it. `SIG-01`

| Request | Information Mintie needs | Chosen path | If the path cannot be established |
| --- | --- | --- | --- |
| An ordinary site outside the DIRECT allowlist | Destination and policy match | Alder, the pinned general primary | Retain the guard; no automatic DIRECT fallback |
| A protected application's matched dependencies | Protected set and transport | Hearth, the residential role | Fail closed; no general or DIRECT degradation |
| An approved private service at its canonical HTTPS origin | Origin, approved scope, dedicated gateway | Alder Private to the exact private destination | Preserve the restriction; do not invent a public fallback |

A DIRECT allowlist can deliberately select an ordinary request. It does not
cover every connection made by the same application. A request without a
usable domain match may still take the default proxy path. Walk through
[cases 1 and 2](50-worked-cases.en.md) to see overlap and IP-only connections.

The router owns transparent policy. Applications, OS proxy settings, and local
TUN interception are other places where policy can live; they need an explicit
compatibility design if they compete with router ownership.

<a id="identity-namespaces"></a>
## Give the names a job

`IDENT-02`

| Name in the story | Portable role | Meaning |
| --- | --- | --- |
| Mintie | `routing-control-plane` | Owns interception, DNS policy and enforcement |
| Alder | `general-primary` | Pinned ordinary proxy-required path |
| Rowan | `general-secondary` | Independently observable standby, no implied automatic failover |
| Hearth | `claude-residential` | Protected application egress, no fallback |
| Alder Private | `private-ingress-primary` | Dedicated gateway identity, even when hosted on Alder |

Names are sample identities; roles carry policy and capability semantics.
Endpoints, accounts and credentials are private deployment bindings outside
this repo. Sharing a host does not give ordinary egress private-origin access.

<a id="realization-and-acceptance"></a>
## A green probe, a phone that still cannot connect

The router can reach Alder while the phone fails before reaching interception.
The probe skipped part of the phone's path. Start with the
[packet path and observation points](10-architecture.en.md#actual-packet-path),
then [case 3](50-worked-cases.en.md#router-probe-versus-lan). `CLAIM-01`

```text
SOURCE -> INSTALLED -> ACTIVATED -> PATH-EVIDENCE
                                      :
                                      +--> scoped ACCEPTANCE RECORD
```

Source checks prove source. Installation readback proves file presence.
Activation readback proves loaded process and kernel state. A path probe proves
its named path at that time. A person or client may accept a scoped result;
that decision cannot upgrade the evidence or keep it fresh forever.

<a id="fail-closed"></a>
## What safe failure feels like

A protected request may stop working while management access remains available.
That is the expected guard behavior when the required path is failed or
unknown. DIRECT is allowlist-only, never a proxy-failure fallback. Maintain an
independent management or break-glass path. `ROUTE-02`

<a id="health-model"></a>
## Choose the next evidence

Health separates the control plane, each egress/private lane and the household
underlay. One subject's PASS cannot speak for another. An aggregate preserves
those outcomes without a single top-level verdict. `HEALTH-01` `HEALTH-10`

- Awake clients work but sleeping clients stall: compare the same radio at the
  same time; [case 4](50-worked-cases.en.md#awake-versus-sleeping).
- A report just published but its probes ran long ago: reject it as current
  recovery evidence; [case 5](50-worked-cases.en.md#new-report-old-observations).
- A query cannot establish state: keep `unknown`; do not call it OFF or absent.

For exact profile cardinality, publication windows, observation ages and
current-pointer identity, use [health and observability](../reference/health-and-observability.md).
For a complete agent handoff and recovery races, use the
[Agent Surface](../agent/README.md).
