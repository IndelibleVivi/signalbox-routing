---
doc_id: signalbox.human.tailnet-vps-private-ingress
language: en
status: f1-reader-path
authority: ../specification.md
contract_revision: 6
---

**English** · [简体中文](40-tailnet-vps-private-ingress.zh-CN.md)

<a id="canonical-origin"></a>
# Let the VPS join the Tailnet, so the phone switches VPNs less

A phone needs a private application, but using it should not require closing
its everyday network tool, starting Tailscale, and switching back afterward.
This arrangement lets a VPS join the Tailnet. An authenticated dedicated
gateway dials only the approved HTTPS service; the phone does not need its own
Tailscale client on the path covered by the router.

The reference gives **Mintie ownership of the application's routing and DNS
policy**. The VPS holds Tailnet membership, while the application keeps its
login and authorization. Moving these responsibilities reduces terminal work
without granting the phone access to the whole Tailnet.

<a id="phone-vpn-slot"></a>
## Check which access path this guide covers

| Your arrangement | Supported conclusion |
| --- | --- |
| Mintie actually classifies the application's traffic and sends it to the dedicated gateway | The phone need not start Tailscale; declared routes handle ordinary access and the named private service separately |
| An existing phone VPN encapsulates the traffic and sends it elsewhere | Do not assume Mintie can identify the inner hostname; establish routing ownership and compatibility first |
| A phone on cellular data should keep using its existing proxy client | This needs supported outbound protocol, hostname rules, DNS, gateway authentication and separate path acceptance; the current reference does not deliver that complete client arrangement |

Tailscale's [VPN coexistence guide](https://tailscale.com/docs/reference/faq/other-vpns)
describes the iOS/Android restriction to one active VPN. Moving Tailnet
membership to the VPS removes that terminal responsibility; membership alone
does not create the phone-to-gateway path.

If running Tailscale directly on the phone is sufficient, another gateway may
not justify its upkeep. For VPS management, SSH or service deployment basics,
start with [Infra Field Guide](https://indeliblevivi.github.io/infra-field-guide/),
which also covers private access for remote workers managing machines. This
guide follows terminal access to applications.

## Keep using the same HTTPS address

This arrangement preserves one browser origin across two ingress routes:

- a public client uses the public authentication and tunnel path;
- an approved private client uses Mintie, a dedicated VPS gateway identity,
  the Tailnet, and the exact private origin.

Both open the same canonical HTTPS hostname. Cookies, localStorage, IndexedDB,
Service Workers, PWA identity, and application URLs therefore remain attached
to one origin. A raw Tailnet address or a second Tailnet-only hostname would
solve reachability while splitting browser identity. `PRIVATE-01`

For example, the browser opens `https://notes.example.com` on both paths.
The entrypoint, the VPS's actual dial destination and the browser URL are
different locations. A Tailnet backend does not require a private address in
the browser. One origin preserves storage ownership; application login, cookie
policy and public/private authentication still need separate verification.

<!-- mermaid:id=canonical_private_ingress -->
```mermaid
flowchart LR
  accTitle: Canonical private ingress
  accDescr: An approved client is captured by Mintie and uses a dedicated gateway identity through the Tailnet to the exact origin. A public client uses the public edge. Ordinary egress identities are denied access to private ranges.
  approved["Approved client"]
  mintie["Mintie routing owner"]
  gateway["Dedicated gateway identity"]
  tailnet["Tailnet grant"]
  origin["Exact private origin :443"]
  public_client["Public client"]
  public_edge["Public auth and tunnel"]
  ordinary["Ordinary egress identity"]
  deny["Deny private ranges"]
  approved -->|canonical hostname| mintie
  mintie -->|dedicated credential| gateway
  gateway -->|exact destination only| tailnet
  tailnet -->|TCP 443| origin
  public_client -->|canonical hostname| public_edge
  public_edge -->|public path| origin
  ordinary -.->|Tailnet or private target| deny
```

<a id="private-path"></a>
## The private packet path

The portable reference flow is:

1. An approved client requests the canonical hostname.
2. Mintie captures the hostname inside its declared protected scope.
3. A rule more specific than every DIRECT allowlist selects a dedicated
   private-ingress identity, not the ordinary proxy identity. `ROUTE-06`
4. The VPS gateway authenticates under its private-ingress role and may dial
   only the declared origin service.
5. The gateway crosses the Tailnet under a narrowly owned tag or identity.
6. The private origin accepts that gateway identity on the exact service and
   presents a browser-trusted certificate for the canonical hostname.
7. Application authentication still applies. Network reachability is not an
   application login.

In this reference pattern, the VPS gateways join the Tailnet while Mintie
remains the sole routing and DNS policy owner. Adding another routing engine to
the router would require a separate compatibility design rather than becoming
an incidental setup step.

<a id="implementation-map"></a>
## Put each input where it actually operates

Align these locations before implementation. The files are portable source
examples, not installable runtime configuration. Endpoints, credentials, real
client identities and readbacks remain in the private implementation.

| Location | Inputs to establish | Current source reference | Observable result to confirm |
| --- | --- | --- | --- |
| Mintie | approved client scope, canonical hostname, transport, dedicated gateway binding | [Traffic policy](../../examples/mintie/traffic-policy.json) and [deployment](../../examples/mintie/deployment.json) | private precedence over DIRECT; only approved requests select the private identity |
| VPS gateway | separate inbound credential, private-ingress role, exact origin service | [Role capabilities](../../contracts/roles.json) and deployment gateway bindings | successful authentication can dial only that service; ordinary credentials and neighboring destinations are denied |
| Tailnet policy | gateway identity/tag allowed to the origin service | the authority table below and [agent implementation reference](../agent/tailnet-vps-implementation-reference.md) | the complete additive policy is reviewed, including existing broad grants |
| Private origin | exact listener/firewall, canonical SNI, trusted certificate | hostname and transport constraints below | canonical TLS and application authentication work; no extra public or private listener appears |
| Observation and acceptance | per-subject profiles, positive and negative path evidence | [Health profiles](../../examples/mintie/health-profiles.json) and [acceptance matrix](../agent/acceptance-matrix.md) | evidence names the path, current scope and valid window; peer presence alone is insufficient |

The canonical hostname, gateway binding, origin service and transport must
correspond across these locations. For a first source judgment, run
`.venv/bin/python -m scripts.policy` and follow origin → gateway → host →
role/capabilities → subject/profile. Success establishes source consistency;
engine-specific installation configuration and client access remain implementation work.

<a id="authorization-boundaries"></a>
## Bound access at every authority

`PRIVATE-02`

| Boundary | Positive allow | Required negative proof |
| --- | --- | --- |
| Client/router policy | approved client + exact canonical hostname + intended transport | an unapproved client or hostname cannot select the private identity |
| Gateway credential | dedicated private-ingress identity | ordinary egress credentials cannot reach Tailnet or private destinations |
| Gateway destination policy | exact origin service only | the same identity cannot reach neighboring private services |
| Tailnet policy | tagged gateway to named origin service | unrelated users, devices, and tags remain denied |
| Origin listener/firewall | expected gateway path to HTTPS service | no unintended public or Tailnet-wide listener is created |
| Application | normal app authentication and authorization | network membership alone does not become application authority |

Tailscale Grants are additive: if several Grants match, their capabilities are
unioned and a more specific Grant does not override a broader one. Grants and
legacy ACLs may also coexist. Audit the whole policy before concluding that a
new narrow rule removed old access; see Tailscale's official [Grants syntax
reference](https://tailscale.com/docs/reference/syntax/grants).

The private origin normally sees the gateway identity, not the original phone
or laptop. That is useful for stable policy, but it makes narrow gateway tags,
destination controls, and origin-side logs essential.

<a id="dns-and-quic"></a>
## Bind hostname, destination, and transport together

Split DNS alone is not enough. A client may use encrypted DNS, cache a public
answer, reuse a connection, or retain Service Worker state. The accepted
private path therefore combines:

- exact canonical-hostname matching;
- protocol or SNI observation where the engine supports it;
- a bounded destination override to the private origin;
- canonical SNI and certificate validation at the origin; and
- scoped UDP/443 rejection when only the TCP private path is proven.

`ROUTE-05` does not ban QUIC universally. It says a protected flow may not use
an unproved direct QUIC escape. Once the deployment proves an equivalent
protected UDP path, it may adopt that transport through an explicit contract
change.

Ordinary general egress must still deny Tailnet and private destination space.
The canonical rule is evaluated earlier only for the approved hostname/client
scope; it is not a broad exception that turns a proxy VPS into a subnet router.

<a id="evidence-and-fallback"></a>
## Evidence, failure, and what is not claimed

`PRIVATE-03` `PRIVATE-04` `CLAIM-01`

Keep the proof layers separate:

| Layer | Minimum useful evidence |
| --- | --- |
| Source | route order, dedicated identity, exact destination, negative policy, and public-safe tests |
| Installed | exact payload/config identity on Mintie, gateways, Tailnet policy, and origin |
| Activated | loaded router rules, gateway process, Tailnet membership/grants, listener, firewall, and certificate state |
| Path | positive canonical request plus negative ordinary-identity and neighboring-destination probes |
| Client acceptance | canonical URL, trusted TLS, expected app auth, and PWA/browser behavior on the named device |

The public and private paths have independent health. A healthy public tunnel
does not prove Tailnet ingress, and a reachable Tailnet peer does not prove the
canonical TLS/application path.

No automatic public fallback is implied. If the accepted private lane fails,
its matched flow fails closed. Deliberately switching a client back to the
public path is a separate policy or user action. Likewise, a primary and backup
gateway do not create strict failover by existing; latency selection is not
ordered primary/secondary behavior.

<a id="client-checklist"></a>
## Return to the phone and check the result

After an authorized installation and activation in your own deployment, use
the same named device to finish:

1. The phone does not additionally run Tailscale, and the declared routing
   owner really captures this application's traffic.
2. Open the canonical HTTPS URL and verify trusted TLS, normal application
   login and the required browser/PWA behavior.
3. Ordinary requests retain their declared routes; ordinary egress credentials
   cannot enter the private service through this arrangement.
4. The private identity cannot access neighboring services. If the private
   lane fails, the approved flow stops without automatic DIRECT or public
   fallback. Fault injection requires separate authorization too.
5. To withdraw the arrangement, preserve independent management access, follow
   your deployment's authorized rollback procedure for routing, gateway
   allows and Tailnet grants, and recheck access scope. This guide supplies no
   apply or rollback script.

Successful observations support scoped acceptance for this named client and
occasion, not a guarantee for every phone, cellular access or a future time.

This document is a source reference, not a claim that any Tailnet, VPS, router,
origin, or client is installed, activated, or healthy. Agents implementing the
pattern should continue with the [Tailnet/VPS implementation
reference](../agent/tailnet-vps-implementation-reference.md).
