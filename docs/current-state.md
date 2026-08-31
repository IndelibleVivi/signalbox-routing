# Current State

Last updated: 2026-08-31

- Project: Signalbox
- Programme tranche: F0.2.1 aggregate time-semantics closure and F1 Human
  Surface completed at the source-and-remote boundary
- Canonical branch: `main`
- Remote visibility: public GitHub repository at
  `https://github.com/IndelibleVivi/signalbox-routing`
- Published F0.2.1/F1 implementation commit:
  `da2fa0a8d28be03b6ba9300f18305c165997023c`
- Exact remote readback: local `HEAD`, `git ls-remote origin refs/heads/main`,
  and the GitHub commits API all returned that implementation commit before
  this receipt-only update
- Hosted CI: [run 33404612179](https://github.com/IndelibleVivi/signalbox-routing/actions/runs/33404612179)
  passed Python 3.11, 3.12, and 3.13 plus the required `signalbox-verify`
  context for that implementation commit
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

Current source evidence: Draft 2020-12 validation passes 26 cataloged
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

Full v1 remains tracked in [`docs/programme-plan.md`](programme-plan.md). The
next planned source tranche is F2, but it is not started by this receipt;
installation, activation, runtime, release, license, and acceptance gates
remain separate.
