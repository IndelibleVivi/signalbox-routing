# Agent Surface

Signalbox's Agent Surface is a deterministic route into the normative
contracts. It is not a live-router runbook and does not authorize external
mutation.

## Read order

1. `../../AGENTS.md` — repository authority and mutation boundaries.
2. `../specification.md` — product meaning and accepted programme.
3. `../../contracts/roles.json` — portable role registry.
4. `../../contracts/traffic-policy.json` — traffic actions and failure invariants.
5. `../../contracts/claims.json` — realization and acceptance grammar.
6. `../../contracts/health-contract.json` — profile and report semantics.
7. `implementation-reference.md` — cross-contract implementation map.
8. `patch-protocol.md` — update and incident-intake workflow.
9. `acceptance-matrix.md` — realization evidence and acceptance boundaries.

## Required assumptions

- Sample identities are not live bindings.
- Examples contain no credentials, endpoint addresses, client identities, or
  production state.
- `unknown` is preserved when evidence is unavailable, stale, unsupported, or
  ambiguous.
- Health observation is read-only. Selection and recovery mutation are
  separate contracts.
- Passing `make verify` proves source consistency only.

## Stop conditions

Stop before an edit if it would:

- make an example a second production authority;
- add a live identity, endpoint, credential, or machine-local path;
- introduce DIRECT fallback for protected traffic;
- equate general egress with private-ingress gateway capability;
- let a health check mutate routing;
- claim installed, activated, path, or acceptance truth from source evidence;
- select a license, create a remote, publish, install, or deploy without exact
  owner authorization.
