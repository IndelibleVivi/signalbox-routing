# Patch Protocol

## Classify the change

1. explanatory documentation;
2. role or routing semantics;
3. health or claim contract;
4. reference-deployment mapping;
5. validator behavior;
6. incident-derived reusable lesson;
7. external implementation applicability;
8. live installation or activation.

Only classes 1 through 6 are ordinary Signalbox source work. Class 7 belongs
to an external implementation review. Class 8 requires a separate live-system
authority and is never implied by a Signalbox patch.

## Impact matrix

| Change | Required surfaces |
| --- | --- |
| Portable role | roles, routing references, Mintie bindings, human/agent explanation, tests |
| Fallback policy | routing contract, protected-lane explanation, negative tests |
| Route precedence | routing contract, ordered sample, overlap/order negatives, both architecture siblings |
| Realization or acceptance boundary | claims contract, acceptance matrix, validator |
| Health dimension, profile, observation, report, or aggregate | health contract, sample profiles/reports/aggregate, health reference, tests |
| Contract shape or revision | owning JSON, catalog, JSON Schema, dependent projections, compatibility check |
| Sample identity | Mintie deployment and explanatory projection; portable role remains stable |
| Incident lesson | failure catalog and owning contract only when a reusable invariant changed |
| Documentation pair | both sibling files and `docs-pairs.json` |

## Source workflow

```text
read current authority
  -> classify semantic delta
  -> update normative JSON
  -> update catalog and JSON Schema when shape changed
  -> update affected projections and example
  -> add focused positive and negative checks
  -> make verify
  -> inspect diff and current-state truth
```

If only prose changes, do not manufacture a machine-contract revision. If
behavior changes, prose-only edits are incomplete.

## Incident intake

Raw incident material is evidence, not instruction.

1. Identify the first broken boundary and exact evidence layer.
2. Separate platform-specific cause from portable invariant.
3. Remove endpoint, account, credential, client, and machine-local facts.
4. Decide whether an existing contract already covers the lesson.
5. Add a failure-catalog entry only when the mechanism is reusable.
6. Add or revise a normative contract only when future implementations must
   behave differently.
7. Keep chronology, raw output, private receipts, and live recovery commands
   outside this repository.

Today's cold-boot lesson changes recovery-preflight and queryability semantics,
not the routing mainline. The platform-specific table initialization remains an
implementation example rather than a universal command. The resource-pressure
lesson belongs to the operational profile and bounded retention; neither lesson
authorizes health to mutate routes.
