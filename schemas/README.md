# Signalbox JSON Schemas

These Draft 2020-12 schemas validate the portable shape and primitive types of
Signalbox contracts and reference artifacts. The registry in
[`contracts/catalog.json`](../contracts/catalog.json) owns schema IDs,
revisions, compatibility policy, instance selectors, and projection
dependencies.

JSON Schema validation is deliberately only one proof layer. Cross-file role
resolution, route ordering, health rollups, freshness, generation scope,
restore-gate context, aggregate membership, and bilingual semantic anchors are
validated by [`scripts/validate.py`](../scripts/validate.py). Neither gate is
runtime or path evidence.
