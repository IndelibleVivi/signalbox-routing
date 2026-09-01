# Mintie Reference Deployment

Mintie is Signalbox's complete named sample. These files demonstrate portable
role binding and policy semantics without containing a production endpoint,
credential, address, client identity, or current runtime claim.

## Reference platform

| Binding | Value | Contract meaning |
| --- | --- | --- |
| Vendor | GL.iNet | Descriptive sample metadata |
| Product | [Beryl 7](https://www.gl-inet.com/products/gl-mt3600be/) | The router used for the named Mintie reference |
| Model | `GL-MT3600BE` | Stable hardware model identifier |
| Normative | no | Signalbox does not require this device |

The platform binding makes the sample reproducible enough to understand
without turning firmware, kernel, package versions, or private runtime state
into root-project requirements. Another capable router may implement the same
portable roles and contracts.

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
- `traffic-policy.json` evaluates canonical private ingress before DIRECT,
  demonstrates protected no-fallback, preserves dedicated gateway identity,
  and binds each settled route ID to its exact action, match form, and fields.
- `health-profiles.json` defines one recovery profile, one control-plane
  operational profile, and exactly one operational profile per registered
  egress or private-ingress lane. Subject kind and profile kind cannot cross.
- `reports/` contains public-safe immutable examples for each subject plus a
  separate recovery-preflight receipt. Dimensions contain explicit observations
  so evidence-class and dependency-group diversity can be validated.
- `health-aggregate.json` references all six operational members and preserves
  their individual outcomes as evaluated at assembly. It excludes
  recovery-preflight, deliberately has no top-level outcome, and remains an
  immutable historical receipt rather than silently aging into a current view.

The sample operational interval is 15 minutes and each operational report
remains fresh for at most 20 minutes. Recovery-preflight reports remain fresh
for at most five minutes and exact-match one operation, desired-state digest,
runtime generation, restore scope, producer, subject, profile and revision,
generation epoch, exact generation, report ID, and attempt ID. Its pass is
usable only after publication and canonical structural and semantic validation.
History is bounded by a 256 KiB file limit, two archives, and 288 entries. The
numbers are sample deployment policy, not universal router requirements.

## Deliberate boundary

There is no install or apply command here. A real implementation must perform
an applicability review, supply its own private bindings, and pass source,
installed, activated, and path-evidence gates separately. Any acceptance record
is a scoped human decision, not another technical stage.
