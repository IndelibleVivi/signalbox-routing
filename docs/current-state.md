# Current State

Last updated: 2026-08-31

- Project: Signalbox
- Programme tranche: F0.2 remote and semantic hardening completed at the
  source-and-remote-governance boundary; full v1 is not complete
- Canonical branch: `main`
- Remote visibility: public GitHub repository at
  `https://github.com/IndelibleVivi/signalbox-routing`
- Published F0.2 source commit:
  `2cd265dbd75a6c77dbaa1f0bd5c39cb0e6a82342`
- Hosted CI: [run 33395382682](https://github.com/IndelibleVivi/signalbox-routing/actions/runs/33395382682)
  passed Python 3.11, 3.12, and 3.13 plus the required `signalbox-verify`
  context for that commit
- Branch policy: pull request required with strict `signalbox-verify`; linear
  history and resolved conversations required; force push and branch deletion
  disabled; administrators retain an explicit bypass
- Repository documentation surfaces: Wiki and Projects disabled
- Merge policy: squash only; merged branches are deleted
- Private vulnerability reporting: enabled
- License: none selected; no reuse grant
- External contributions: not currently accepted pending explicit rights terms
- Release or tag: none
- Installed payload: not applicable / not created
- Live router or network activation: not authorized and not performed
- Owner or client acceptance: not applicable to this source tranche

F0.2 source evidence: Draft 2020-12 validation passes 26 cataloged instances;
semantic validation passes seven public reference reports and one staleness
regression fixture; 32 unit regressions pass. The hosted gate repeats the full
source check and confirms that verification leaves the worktree unchanged.

Foundation 0.2 repairs private-ingress precedence, separates operational health
by subject, scopes report generation and restore gates, makes probe diversity
machine-verifiable, publishes JSON Schemas and a catalog, strengthens bilingual
section parity, and protects the hosted source gate. Full v1 Human and Agent
depth remains tracked in [`docs/programme-plan.md`](programme-plan.md); later
tranches require their own execution decisions.
