# Mintie Reference Deployment

Mintie is Signalbox's complete named sample. These files demonstrate portable
role binding and policy semantics without containing a production endpoint,
credential, address, client identity, or current runtime claim.

## Identity map

| Sample identity | Portable role | Notes |
| --- | --- | --- |
| Mintie | `routing-control-plane` | Owns transparent policy for the sample protected scope |
| Alder | `general-primary` | Default proxy-required egress |
| Rowan | `general-secondary` | Independent standby; no automatic failover implied |
| Hearth | `claude-residential` | High-recall protected residential egress; no fallback |
| Alder Private | `private-ingress-primary` | Dedicated identity co-located with Alder |
| Rowan Private | `private-ingress-secondary` | Dedicated identity co-located with Rowan |

The dedicated gateway identities are separate even when their hosts are
co-located with Alder or Rowan. General egress credentials never inherit
private-origin access.

```mermaid
flowchart LR
  DEVICE[Approved device]
  MINTIE[Mintie<br/>routing-control-plane]
  ALDER[Alder<br/>general-primary]
  ROWAN[Rowan<br/>general-secondary]
  HEARTH[Hearth<br/>claude-residential]
  APRIV[Alder Private<br/>dedicated gateway identity]
  ORIGIN[Exact private origin<br/>canonical HTTPS]

  DEVICE --> MINTIE
  MINTIE -->|default proxy-required| ALDER
  MINTIE -.->|manual or explicit selection only| ROWAN
  MINTIE -->|protected application| HEARTH
  MINTIE -->|approved canonical origin| APRIV
  APRIV --> ORIGIN
```

## Files

- `deployment.json` binds sample identities to portable roles.
- `traffic-policy.json` demonstrates route order, protected no-fallback, and
  dedicated private-ingress identity.
- `health-profiles.json` separates recovery-preflight from operational health
  and configures report freshness, atomic publication, bounded retention, probe
  diversity, resource observation, and recovery-readiness observation.

The sample operational interval is 15 minutes and its report remains fresh for
20 minutes. Recovery-preflight reports remain fresh for five minutes. History
is bounded by a 256 KiB file limit, two archives, and 288 entries. The numbers
are sample deployment policy, not universal router requirements.

## Deliberate boundary

There is no install or apply command here. A real implementation must perform
an applicability review, supply its own private bindings, and pass source,
installed, activated, and path-evidence gates separately. Any acceptance record
is a scoped human decision, not another technical stage.
