# Signalbox JSON Schemas

These Draft 2020-12 schemas validate the portable shape and primitive types of
Signalbox contracts and reference artifacts. The registry in
[`contracts/catalog.json`](../contracts/catalog.json) owns schema IDs,
revisions, compatibility policy, instance selectors, and projection
dependencies.

[`scripts/validate_schemas.py`](../scripts/validate_schemas.py) first validates
that catalog against the fixed canonical catalog schema before consuming any
catalog-declared path. Both validation layers use the shared contained-path
resolver in [`scripts/repository_paths.py`](../scripts/repository_paths.py), so
an absolute path, Windows-style path, forbidden parent traversal, or symlink
escape cannot redirect authority outside the repository.

JSON Schema validation is deliberately only one proof layer. Cross-file role
resolution, exact reference-route grammar, health rollups, canonical report
evaluation, freshness, exact current identity, restore-gate context, aggregate
membership, network-underlay subject/profile binding, and bilingual semantic
anchors are validated by
[`scripts/validate.py`](../scripts/validate.py). Neither gate is runtime or path
evidence.


Active F2 shapes are health-contract/v6, health-profile/v3, claims/v2,
claim-record/v1, acceptance-record/v2 and handoff/v1. The acceptance schema now
validates actual decisions rather than a required-field descriptor. Reports
and aggregates retain v2 because their shapes are unchanged. Profile config
revisions are independent of catalog contract revisions. See the
[compatibility and task entry](../docs/agent/workflow.md).
Concrete claim/handoff semantics are owned by
[`scripts/handoff.py`](../scripts/handoff.py); freshness and report semantics
remain in the canonical health evaluator.
