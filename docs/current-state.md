# Current State

Last updated: 2026-10-03

<!-- signalbox:f0.3-source-integration merged-into-canonical-main -->

## Current source candidate

- F2 Agent Surface update is source-complete on `f2-agent-surface`, based on
  canonical `main` at `f70aaab7792ed025de5b64255d51ccee061b6069`.
- Scope: total gateway/role/health references, canonical HTTPS, typed evaluator
  entry, observation and attempt freshness, catalog revision agreement, actual
  claim/acceptance handoffs, synthetic start-order current-pointer/CAS, and five
  paired worked cases with progressive reader paths.
- Local verification: `make verify PYTHON=.venv/bin/python` passed 38 cataloged
  instances, ten reference reports, one historical regression fixture, concrete
  handoff validation, eight synthetic replay judgments and 130 unit tests.
  The prior baseline had 79 unit tests. These are source checks, not live evidence.
- Git/remote: the verified source candidate is prepared for the existing remote.
  Hosted CI and protected-main integration remain separate; a PR is required.
- Normative source line: specification revision 6; health-contract/v6,
  health-profile/v3, claims/v2, claim-record/v1, acceptance-record/v2 and
  handoff/v1. Report and aggregate shapes retain v2.
- Full Signalbox v1 remains incomplete. F3 complete configuration and negative
  proofs, F4 remaining failure depth, F5 historical compatibility/supply-chain
  work and F6 whole-programme reconciliation remain open in the
  [programme plan](programme-plan.md).

## Canonical integration and historical receipts

- F0.3 underlay observability is integrated into canonical `main` through
  [PR #1](https://github.com/IndelibleVivi/signalbox-routing/pull/1), merge commit
  `5ca593db7c4ce101ee9afcc2aaf5ce1bbde9b3a2`. Its canonical-main hosted gate
  [35388875151](https://github.com/IndelibleVivi/signalbox-routing/actions/runs/35388875151)
  passed Python 3.11, 3.12, 3.13 and `signalbox-verify`.
- The integration-status follow-up was merged through
  [PR #2](https://github.com/IndelibleVivi/signalbox-routing/pull/2), commit
  `3ec07264d8b804d8bd3025bb52ee5330c799be5a`; canonical-main gate
  [35428354163](https://github.com/IndelibleVivi/signalbox-routing/actions/runs/35428354163)
  passed. The later `f70aaab` source added the sleep-path and change-attribution
  failure mechanisms. These are historical source receipts.
- F0.2.2 implementation `099662a4b66f3ab1ef3b62b720e97b503fa7555d` and detector
  follow-up `2a1606659f52bd8e78a899fc4b93ebbe8265a863` remain historical; their
  hosted gates were 33467434452 and 33469011990.

## Durable repository and realization boundaries

- Existing public remote: [IndelibleVivi/signalbox-routing](https://github.com/IndelibleVivi/signalbox-routing).
- Main branch requires a PR, strict `signalbox-verify`, linear history and
  resolved conversations. Source publication is distinct from a release.
- License: none selected; no reuse grant. External contributions remain closed
  pending explicit rights terms. No release or tag is claimed.
- Installed payload, activation, router/Tailnet/VPS mutation, live path evidence
  and owner/client acceptance: neither authorized nor performed by this update.
- Handoff records, replay inputs and the in-memory publisher are synthetic.
  Their verification does not establish live health, durable pointer CAS or an
  operational recovery effect.

This page owns volatile source/Git/remote status; it never owns live-router truth.
