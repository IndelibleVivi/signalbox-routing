---
doc_id: signalbox.human.start-here
language: en
status: foundation-explanatory
authority: ../../specification.md
contract_revision: 1
---

# Start here: move proxy selection to the router

Signalbox is not primarily about which proxy port an application should use.
It asks which layer should own proxy policy. `SIG-01`

```text
explicit application proxy
  -> operating-system proxy or PAC
  -> local TUN interception
  -> transparent router interception
  -> upstream egress role
```

Moving policy toward the network entrance means applications need less proxy
awareness. It also gives the control plane more responsibility for DNS,
routing, failure semantics, observation, and recovery. Router transparency is
valuable when that centralized policy remains understandable and verifiable.

## Keep three namespaces separate

`IDENT-02`

| Kind | Signalbox example | Deployment stability |
| --- | --- | --- |
| Portable role | `general-primary` | Stable semantics |
| Sample identity | `Alder` | Replaceable reference name |
| Private live binding | endpoint, credential, or provider outside the repo | Volatile; requires fresh readback |

Mintie is the reference deployment, not another name for Signalbox. She gives
the guide one complete topology without turning a private live network into a
portable constant.

## One green light proves one layer; acceptance is separate

`CLAIM-01`

```text
SOURCE -> INSTALLED -> ACTIVATED -> PATH-EVIDENCE
                                      :
                                      +--> ACCEPTANCE RECORD
```

- Source tests prove that the repository expresses its intended contract.
- File presence proves that a payload was installed.
- Process, loaded-config, route-table, and guard evidence prove the observed
  activated shape.
- A lane probe proves only that path evidence.
- A real browser, PWA, or device action may produce a named acceptance record,
  but that scoped decision cannot upgrade technical evidence or prove the path
  remains current forever.

If a layer cannot be queried, its outcome is `unknown`. Query failure is not
evidence that a rule is absent or a subsystem is off.

## Fail closed is a policy, not an outage shortcut

`ROUTE-02`

DIRECT serves only approved LAN, bootstrap, or direct allowlists. When
protected traffic requires a proxy and the exit, DNS, routing process, or
kernel state cannot be established, the policy fails and retains protection
instead of silently degrading to the raw WAN.

That contract also requires an independent management or break-glass path. A
diagnostic actor must not depend exclusively on the path it is repairing.

## Health is more than opening a page

`HEALTH-01`

Signalbox separates transport, exit identity, DNS, control plane, enforcement,
resources, persistence, and recovery readiness. A `HealthProfile` says what to
observe; every attempt publishes an immutable `HealthReport`. Once a successful
report passes `valid_until`, regresses in generation, or mismatches the expected
profile revision, its effective outcome is `unknown`.

A `recovery-preflight` profile asks only whether state can be queried,
reconciled, and restored safely. The `operational` profile covers the complete
path. Neither profile selects or mutates routes.

A cold-boot incident provides the key example: a route table may be logically
empty while the platform cannot query it reliably. Recovery then has no basis
to claim that runtime is `OFF`. Queryability is itself a health dimension.

Continue with [Signalbox architecture and packet paths](10-architecture.en.md).
