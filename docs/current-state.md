# Current State

Last updated: 2026-09-19

<!-- signalbox:f0.3-source-integration merged-into-canonical-main -->

- F0.3 underlay observability source implementation is integrated into
  canonical `main` by the PR #1 merge commit
  `5ca593db7c4ce101ee9afcc2aaf5ce1bbde9b3a2`; the final pre-merge head was
  `0338d4f28b5a83a78ebc8a19f77845f2dd9097d6`
- F0.3 source integration claims no release or tag, no installed payload, no
  activation or live-router mutation, no live path evidence, and no owner or
  client acceptance
- Post-merge canonical-main hosted gate: [run 35388875151](https://github.com/IndelibleVivi/signalbox-routing/actions/runs/35388875151)
  succeeded for the merge commit on Python 3.11, 3.12, and 3.13 plus the
  required `signalbox-verify` context
- F0.3 review surface: [pull request #1](https://github.com/IndelibleVivi/signalbox-routing/pull/1)
  (merged; squash merge policy deletes the source branch)
- Project: Signalbox
- Programme tranche: F0.3 underlay observability is the current canonical
  source boundary, complete at source and integrated into canonical `main`;
  F0.2.2 executable-authority closure is the previous source boundary, and its
  exact receipt above remains preserved as historical record; F2 remains the
  next planned tranche and is not started
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

F0.3 adds a `network-underlay` deployment subject kind and an
`underlay-operational` profile kind so a degraded household or WAN underlay
stays observable while the control plane and proxy lanes are healthy. Its
required dimensions are `transport`, `dns`, `responsiveness`, and
`availability`; the new portable reason codes are `latency-envelope-breach`,
`recent-link-flap`, and `shaping-unverified`. PR #1 includes a
review repair that closes two validation defects: the health contract declares
each underlay dimension's allowed evidence classes and rejects any
out-of-domain observation (`dns` requires `resolver-path`, so a substituted
qdisc or kernel readback is invalid rather than rolled up), the three
domain-specific reason codes are context-bound at dimension and observation
level while generic codes stay unconstrained, and generic profile validation
accepts zero, one, or many registered network underlays with exactly one
`underlay-operational` profile per subject, leaving Mintie's reference
topology pinned by its deployment. The underlay is observation-only, never an
egress lane, and never a proxy-failure fallback route. The Mintie
example gains a public-safe underlay subject, profile, report, and aggregate
member; its seven-member aggregate keeps the control plane and every egress and
private-ingress lane at `pass` while only `underlay/mintie-wan` reports `fail`,
and `FAIL-010` records the reusable mechanism. Because the health
contract gains a required profile kind, it advances to
`signalbox.health-contract/v5`, and documentation pairs advance to revision 5
under the unchanged `signalbox.docs-pairs/v3` schema; the Mintie route
projection is unchanged. F0.3 is source-integrated into canonical `main`
through the PR #1 merge commit above; it has entered no release or tag and is
not installed, activated, deployed, or owner-accepted here. No active F0.3
feature branch remains.

Merged F0.3 source evidence, kept distinct from the preserved F0.2.2 receipt
above: the merged gate validates 30 cataloged instances, ten public reference
reports, and one staleness fixture, and the regression suite passes. Hosted run
35388875151 repeated that source gate on canonical `main` at Python 3.11, 3.12,
and 3.13 plus the required `signalbox-verify` context. These counts describe
the merged source boundary only; they are not install, activation, live-path,
or acceptance evidence.

Full v1 remains tracked in [`docs/programme-plan.md`](programme-plan.md). The
F0.3 underlay-observability tranche is complete at the source boundary and F2
remains the next planned tranche and is not started. Installation, activation,
runtime, release, license, and acceptance gates remain separate.
