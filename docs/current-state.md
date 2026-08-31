# Current State

Last updated: 2026-08-31

- Project: Signalbox
- Programme tranche: F0.2 remote and semantic hardening, source candidate
- Canonical branch: `main`
- Remote visibility: public GitHub repository at
  `https://github.com/IndelibleVivi/signalbox-routing`
- Published commit: `d5376e381bc234662e265c4e0957b60c726f27ae`
  (Foundation 0.1; the F0.2 candidate is not yet published)
- Hosted CI: workflow authored in the F0.2 candidate; no hosted result exists
  for that unpublished candidate yet
- Branch policy: F0.2 protection not yet applied
- GitHub documentation surfaces: Wiki and Projects remain enabled until the
  F0.2 remote-settings gate
- License: none selected; no reuse grant
- External contributions: not currently accepted pending explicit rights terms
- Release or tag: none
- Installed payload: not applicable / not created
- Live router or network activation: not authorized and not performed
- Owner or client acceptance: not applicable to this source tranche

Current local candidate evidence: Draft 2020-12 validation passes 26 cataloged
instances; semantic validation passes seven public reference reports and one
staleness regression fixture; 32 unit regressions pass; `git diff --check`
passes. These results prove only the uncommitted source candidate until an exact
commit is published and the hosted gate succeeds.

Foundation 0.2 repairs private-ingress precedence, separates operational health
by subject, scopes report generation and restore gates, makes probe diversity
machine-verifiable, publishes JSON Schemas and a catalog, strengthens bilingual
section parity, and adds the hosted verification contract. Full v1 Human and
Agent depth remains tracked in [`docs/programme-plan.md`](programme-plan.md).
