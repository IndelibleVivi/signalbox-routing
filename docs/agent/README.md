# Agent Surface

Signalbox's Agent Surface is a deterministic route into the normative
contracts. It is not a live-router runbook and does not authorize external
mutation.

## Read order

1. `../../AGENTS.md` — repository authority and mutation boundaries.
2. `../specification.md` — product meaning and accepted programme.
3. `../../contracts/catalog.json` — schema ownership, compatibility, instance,
   and projection registry.
4. `../../contracts/roles.json` — portable role registry.
5. `../../contracts/traffic-policy.json` — traffic actions and failure invariants.
6. `../../contracts/claims.json` — realization and acceptance grammar.
7. `../../contracts/health-contract.json` — profile, observation, report, and
   aggregate semantics.
8. `../../schemas/` — structural contracts consumed through the catalog.
9. `implementation-reference.md` — cross-contract implementation map.
10. `patch-protocol.md` — update and incident-intake workflow.
11. `acceptance-matrix.md` — realization evidence and acceptance boundaries.

## Required assumptions

- Sample identities are not live bindings.
- Examples contain no credentials, endpoint addresses, client identities, or
  production state.
- `unknown` is preserved when evidence is unavailable, stale, unsupported, or
  ambiguous.
- Health observation is read-only. Selection and recovery mutation are
  separate contracts.
- A health report observes one subject. Aggregates preserve member outcomes
  and never manufacture a deployment-wide verdict.
- Passing `make verify` proves source consistency only.

## Stop conditions

Stop before an edit if it would:

- make an example a second production authority;
- add a live identity, endpoint, credential, or machine-local path;
- introduce DIRECT fallback for protected traffic;
- place a general DIRECT rule before canonical private ingress;
- equate general egress with private-ingress gateway capability;
- let a health check mutate routing;
- claim installed, activated, path, or acceptance truth from source evidence;
- select a license, create a remote, publish, install, or deploy without exact
  owner authorization.
