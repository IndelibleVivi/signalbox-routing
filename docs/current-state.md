# Current State

Last updated: 2026-09-01

- Project: Signalbox
- Programme tranche: F0.2.2 executable-authority closure completed at the
  source-and-remote boundary; the prior F0.2.1/F1 boundary remains published
- Canonical branch: `main`
- Remote visibility: public GitHub repository at
  `https://github.com/IndelibleVivi/signalbox-routing`
- Published F0.2.2 implementation commit:
  `099662a4b66f3ab1ef3b62b720e97b503fa7555d`
- Original F0.2.2 hosted CI: [run 33467434452](https://github.com/IndelibleVivi/signalbox-routing/actions/runs/33467434452)
  passed Python 3.11, 3.12, and 3.13 plus the required `signalbox-verify`
  context for that implementation commit
- Published credential-detector hardening follow-up:
  `2a1606659f52bd8e78a899fc4b93ebbe8265a863`
- Exact follow-up readback: local `HEAD`,
  `git ls-remote origin refs/heads/main`, and the GitHub commits API all
  returned that follow-up commit before this receipt-only update
- Follow-up hosted CI: [run 33469011990](https://github.com/IndelibleVivi/signalbox-routing/actions/runs/33469011990)
  passed Python 3.11, 3.12, and 3.13 plus the required `signalbox-verify`
  context for that follow-up commit
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

Published F0.2.2 source evidence: Draft 2020-12 validation
passes 26 cataloged instances; semantic validation passes seven public
reference reports and one staleness fixture; 56 unit regressions pass. The
gate includes the new validator modules in Git-index enumeration. The source
bootstraps the catalog from its fixed schema, resolves authority
paths inside the repository, and scans current worktree bytes for every textual
path listed in the Git index rather than a selected directory/suffix list. The
detector remains bounded defense in depth, not a Git-history audit or universal
secret proof. Credential assignment coverage includes API, access, and refresh
token fields plus generic quoted-literal `token` and `secret` fields; requiring
a quoted literal for the generic names avoids treating ordinary code-variable
assignments as credential material.

F0.2.1 advanced the breaking aggregate member shape to
`signalbox.health-aggregate/v2`, made `evaluated_at` equal `assembled_at`, and
stored `effective_outcome_at_assembly` in a historical receipt owned by
`signalbox.health-contract/v3`. F1 rebalanced complexity through three reader
paths while retaining the normative core, added the Tailnet/VPS canonical
private-ingress reference and negative-proof requirements, and recorded
Mintie's non-normative GL.iNet Beryl 7 (`GL-MT3600BE`) platform binding.

F0.2.2 advances the owning health contract to
`signalbox.health-contract/v4`, the Mintie traffic projection to
`signalbox.reference-traffic-policy/v3`, and documentation pairs to
`signalbox.docs-pairs/v3`. One canonical evaluator now gates restore and
aggregate membership through report structure, full semantics, publication
window, and exact current identity. Profile kind/cardinality, exact route
grammar, safety-field mutation regressions, catalog bootstrap, and contained
path resolution are part of the same published source boundary.

Full v1 remains tracked in [`docs/programme-plan.md`](programme-plan.md). The
next planned source tranche is F2, but it is not started by this receipt.
Installation, activation, runtime, release, license, and acceptance gates
remain separate.
