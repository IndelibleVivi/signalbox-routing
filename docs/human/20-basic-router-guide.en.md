---
doc_id: signalbox.human.basic-router-guide
language: en
status: f1-reader-path
authority: ../specification.md
contract_revision: 4
---

**English** · [简体中文](20-basic-router-guide.zh-CN.md)

<a id="router-job"></a>
# The practical router guide

Signalbox can look larger than a router manual because it contains the safety
contract underneath the manual. For ordinary use, the router's job is simpler:
capture an approved client scope, classify traffic once, send each class to its
declared role, and refuse unsafe fallback. `SIG-01` `ROUTE-01`

Moving policy to the router means applications no longer need to agree on one
proxy setting. It also means the router becomes responsible for DNS ownership,
route order, failure behavior, and inspectable state. Centralization is useful
only when those four responsibilities stay explicit.

<a id="minimum-policy"></a>
## The minimum policy you need to describe

Write down five answers before touching an implementation:

| Question | Safe Signalbox answer |
| --- | --- |
| Which clients are in scope? | An explicit device, subnet, or approved client set |
| What may use DIRECT? | A named allowlist; never the default and never a proxy-failure fallback |
| Where does ordinary proxy-required traffic go? | One pinned `general-primary` role |
| Which traffic needs a protected identity? | A high-recall match set bound to its own no-fallback role |
| Is private ingress needed? | Optional; if yes, use a dedicated gateway identity and exact destination |

`ROUTE-02` makes DIRECT allowlist-only. The existence of a secondary exit does
not create automatic failover, and a protected lane does not inherit the
ordinary exit merely because it is available.

The [Mintie sample](../../examples/mintie/README.md) shows those answers with
friendly identities. The names make the policy readable; they are not endpoint
or provider requirements.

<a id="safe-failure"></a>
## What daily “fail closed” means

If a proxy-required route cannot be proved, that traffic fails instead of
escaping through raw WAN. The independent guard remains present even when the
routing process fails to start or cannot establish safe state. `ENFORCE-01`

Fail closed should be bounded, not theatrical:

- approved local management and bootstrap paths remain explicit;
- a break-glass path does not depend on the lane being repaired;
- an unqueryable rule or table becomes `unknown`, not “off”;
- diagnostics observe first and do not silently change route selection.

The visible symptom may be “this page does not open.” The policy meaning is
“this protected flow was not allowed to degrade into a less trusted path.”

<a id="what-proof-means"></a>
## Know what each green light proves

`CLAIM-01`

| Evidence | What it proves | What it does not prove |
| --- | --- | --- |
| `make verify` | tracked source agrees with its contracts | anything is installed on a router |
| file readback | a payload exists at the observed location | it is loaded or active |
| process, config, route, and guard readback | the observed runtime shape | an application path succeeds |
| exact lane probe | that path under that observation | another lane or later time |
| browser or device acceptance | a person's scoped decision | permanent technical health |

Health is therefore a collection of subject-specific receipts, not one magic
green router icon. A stored deployment aggregate records the outcomes as they
were evaluated at assembly; current truth requires current reports and a new
aggregate.

<a id="next-path"></a>
## Go deeper only when your job needs it

- Implementing interception, DNS, precedence, or guards: [Routing, DNS, and
  fail-closed](30-routing-dns-and-fail-closed.en.md).
- Preserving one app origin across public and private access: [Tailnet and VPS
  private ingress](40-tailnet-vps-private-ingress.en.md).
- Reviewing exact machine semantics: [Agent Surface](../agent/README.md).

The router guide is intentionally short. The deeper contracts exist so a
person or agent can implement the short promise without guessing at the unsafe
parts.
