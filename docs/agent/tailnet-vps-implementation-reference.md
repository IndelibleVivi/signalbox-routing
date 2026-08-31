# Tailnet/VPS Canonical Private-Ingress Implementation Reference

Status: public-safe source reference; not an install, activation, or live-health
claim.

Normative IDs: `ROUTE-01`, `ROUTE-05`, `ROUTE-06`, `PRIVATE-01` to
`PRIVATE-04`, `CLAIM-01` to `CLAIM-03`.

## Scope and authority

Implement this reference only when the deployment explicitly requires an
approved client to reach an exact private service through a dedicated gateway
while retaining the same canonical HTTPS origin as the public path.

The normative owners remain:

- product meaning: `../specification.md`;
- roles and identity separation: `../../contracts/roles.json`;
- precedence and failure semantics: `../../contracts/traffic-policy.json`;
- public-safe bindings: `../../examples/mintie/deployment.json` and
  `../../examples/mintie/traffic-policy.json`;
- health/evidence semantics: `../../contracts/health-contract.json`.

This file maps those contracts to an implementation shape. It does not own
live hostnames, addresses, credentials, Tailnet policy, certificates, or
router-specific commands.

## Required private inputs

Keep the following outside Signalbox and bind them only in the deployment's
private authority:

| Input | Required property |
| --- | --- |
| canonical origin | one deployment-owned HTTPS hostname |
| approved client scope | explicit device, subject, or network scope |
| private origin target | exact private service and port |
| primary/secondary gateway | distinct private-ingress identities and credentials |
| Tailnet identities | narrowly owned gateway and origin selectors |
| certificate path | browser-trusted certificate for the canonical hostname |
| application auth | unchanged application-level authentication and authorization |
| rollback source | exact prior state or artifact identity for every mutated owner |

Do not derive these values from friendly sample identities such as `Alder` or
`Rowan`.

## Responsibility map

| Owner | Must do | Must not do |
| --- | --- | --- |
| Client/router policy | match approved client + canonical hostname + intended transport | expose a general Tailnet/private-route exception |
| Mintie routing owner | evaluate canonical private ingress before DIRECT and bind a dedicated identity | install a competing routing/DNS owner without a compatibility contract |
| Gateway | authenticate as private-ingress and permit the exact origin service | let ordinary egress credentials or arbitrary destinations reuse the lane |
| Tailnet policy | grant the gateway selector only the named origin capability | assume a narrow new rule subtracts older broad access |
| Origin | bind the intended listener/firewall/TLS/app-auth shape | treat Tailnet membership as application authorization |
| Observer | publish one report per subject and preserve `unknown` | mutate route selection from a health probe |

## Router decision order

The active implementation should have one canonical path equivalent to:

```text
observe protocol
capture or classify DNS/hostname
if approved client + canonical origin:
    select dedicated private-ingress identity
elif protected UDP/443 and transport is unproved:
    reject
elif protected application set:
    select protected no-fallback role
elif explicit DIRECT allowlist:
    direct
else:
    select pinned general-primary
```

The canonical private-ingress match must precede all private-address and other
DIRECT allowlists. A general route to private ranges is not an acceptable
substitute. The negative path must also deny Tailnet/private destinations when
the selected identity is ordinary general egress.

## Hostname and TLS binding

The implementation must preserve three distinct values:

```text
browser origin     = canonical HTTPS hostname
policy match       = the same canonical hostname plus approved client scope
dial destination   = exact private origin binding
```

Split DNS may supply the private destination. Where clients can bypass or cache
DNS, pair it with protocol/SNI observation and a bounded destination override.
The TLS handshake still uses the canonical hostname and validates a
browser-trusted certificate for it.

If the accepted private lane proves only TCP, reject UDP/443 for the exact
canonical scope. Do not create a global QUIC ban and do not allow unproved
direct QUIC to bypass the private policy.

## Tailnet authorization review

Use a dedicated gateway tag or identity and grant only the exact origin service
required by the application. Review the complete Tailnet policy, not only the
new block: matching Grants contribute a union of capabilities, more specific
Grants do not override broader ones, and legacy ACLs may coexist.

At minimum, policy tests or equivalent readback must establish:

- the dedicated gateway selector can reach the exact origin service;
- the same selector cannot reach a neighboring private service;
- ordinary egress, unrelated users, devices, and tags cannot reach the origin;
- the intended origin selector cannot be broadened by a stale host/group/tag;
- removing or changing the new rule does not reveal an older broad grant that
  still authorizes the path.

The origin sees the gateway's Tailnet identity rather than the original client.
Keep that identity narrow and include it in origin-side authorization/logging.

## Ordered gateway behavior

`private-ingress-primary` and `private-ingress-secondary` are capabilities, not
an automatic selector. If strict failover is later authorized, implement a
separate bounded state machine with:

- explicit primary and secondary states;
- lane-specific health against the real private origin;
- hysteresis and minimum dwell time;
- operation identity and desired-state digest;
- atomic apply, postcondition verification, rollback, and receipt;
- failure that retains the private guard rather than falling to public DIRECT.

Do not use a latency-based selector as evidence of strict primary/backup order.

## Verification ledger

### Positive proof

1. Source validation proves route precedence, identity separation, and sample
   consistency.
2. Installed readback proves the exact candidate reached each intended owner.
3. Activated readback proves loaded router policy, gateway service, Tailnet
   identity/policy, origin listener/firewall, and certificate state.
4. Path evidence proves the canonical request traverses the intended gateway
   and reaches the exact origin with valid TLS and expected application auth.
5. Named client acceptance proves the intended browser/PWA behavior only for
   that client and decision scope.

### Negative proof

Exercise at least these denied paths after the final relevant activation:

- unapproved client to canonical private policy;
- ordinary egress identity to Tailnet/private destination;
- dedicated gateway identity to a neighboring private destination;
- unrelated Tailnet subject to the exact origin service;
- protected canonical UDP/443 when only TCP is accepted;
- stale or failed private lane attempting automatic public/DIRECT degradation.

Record `unknown` when a boundary cannot be queried. Absence of positive traffic
is not proof that the negative policy rejected it for the intended reason.

## Stop conditions

Stop before mutation when any of these is unresolved:

- no exact canonical hostname/client/destination scope;
- no independent management or rollback path;
- gateway identity is shared with ordinary egress;
- existing Tailnet grants/ACLs have not been audited;
- canonical TLS at the private origin is unavailable;
- ordinary identity or neighboring-destination denial is untestable;
- the requested action authorizes source work but not installation, activation,
  Tailnet policy change, origin change, or client acceptance.

Signalbox source completion never crosses those gates automatically.
