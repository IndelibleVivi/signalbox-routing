# Current State

Last updated: 2026-08-31

- Project: Signalbox
- Programme tranche: F0.2.1 aggregate time-semantics closure and F1 Human
  Surface implemented as the current source candidate; exact remote and hosted
  receipt pending
- Canonical branch: `main`
- Remote visibility: public GitHub repository at
  `https://github.com/IndelibleVivi/signalbox-routing`
- Current source candidate: this working tree; commit identity pending
- Last confirmed F0.2 implementation commit:
  `2cd265dbd75a6c77dbaa1f0bd5c39cb0e6a82342`
- Last confirmed F0.2 hosted CI: [run 33395382682](https://github.com/IndelibleVivi/signalbox-routing/actions/runs/33395382682)
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
- Live router, Tailnet, VPS, or origin activation: not authorized and not
  performed
- Owner or client acceptance: not applicable to this source tranche

Current local source evidence: Draft 2020-12 validation passes 26 cataloged
instances; semantic validation passes seven public reference reports and one
staleness regression fixture; 35 unit regressions pass. The documentation
contract covers the paired root README plus five paired Human Surface guides,
requires visible sibling links, and validates semantic anchors, internal links,
and public-safe boundaries.

F0.2.1 advances the breaking aggregate member shape to
`signalbox.health-aggregate/v2`, makes `evaluated_at` equal `assembled_at`, and
stores `effective_outcome_at_assembly` in a historical receipt owned by
`signalbox.health-contract/v3`. F1 rebalances complexity through three reader
paths while retaining the normative core, adds the Tailnet/VPS canonical
private-ingress reference and negative-proof requirements, and records Mintie's
non-normative GL.iNet Beryl 7 (`GL-MT3600BE`) platform binding.

The next closure action is to commit and push the candidate, wait for the exact
hosted gate, read back the remote commit, then replace the pending receipt above
with that evidence. Full v1 remains tracked in
[`docs/programme-plan.md`](programme-plan.md); later installation, activation,
runtime, release, license, and acceptance gates remain separate.
