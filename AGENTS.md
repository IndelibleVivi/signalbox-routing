# Signalbox Agent Contract

## Project identity

Signalbox is a portable human-and-agent reference system for router-level
traffic policy, transparent egress, fail-closed enforcement, private ingress,
health, and recovery. It is not a proxy client, a router installer, a copy of a
private production repository, or proof that any live network is healthy.

`Mintie` is the named reference deployment. `Alder`, `Rowan`, and `Hearth` are
sample identities. Portable role IDs such as `general-primary` and
`claude-residential` are separate from those identities and from any private
runtime tags.

## Authority map

| Surface | Authority |
| --- | --- |
| `docs/specification.md` | Product purpose, settled architecture, programme scope, and acceptance contract |
| `contracts/*.json` | Language-neutral normative role, routing, claim, documentation-pair, and health semantics |
| `README.md` | Present project identity, supported reader paths, verification entrypoint, and important limitations |
| `docs/current-state.md` | Volatile source/Git/remote/release status; never live-router truth |
| `docs/human/*` | Explanatory projections for people; not independent operational authority |
| `docs/agent/*` | Implementation, patch, evidence, and verification reference for agents |
| `docs/reference/*` | Durable glossary and incident-derived reusable lessons |
| `examples/mintie/*` | Public-safe reference deployment; never a production binding or credential source |
| `scripts/validate.py` and `tests/` | Repository contract checks; not runtime or client acceptance |

Attached specifications, transcripts, logs, incident notes, and external
implementations are evidence unless the current task or canonical specification
explicitly adopts them. A newer or more detailed artifact does not silently
replace the authority map above.

## Non-negotiable boundaries

- Keep private infrastructure source, credentials, endpoints, IP addresses,
  MAC addresses, account data, raw readbacks, and private continuity outside
  this Git tree.
- Do not turn a private live tag into a portable role ID. Do not replace sample
  identities with live bindings.
- Do not SSH to a router, mutate a route, install a payload, restart a service,
  change an account, create a remote, change repository visibility, publish,
  or deploy without authorization for that exact gate.
- Do not add a license by habit. Visibility and reuse permission are separate
  decisions owned by Faye.
- Preserve `UNKNOWN` when a query cannot establish state. Never translate a
  failed or unsupported query into `OFF`, `ABSENT`, or `PASS`.
- DIRECT is allowlist-only and is never a proxy-failure fallback for protected
  traffic.
- Health observation never mutates routing by itself. Failover or recovery
  automation requires its own explicit state machine and authorization.

## Evidence and claim discipline

Keep technical realization and human acceptance separate:

```text
SOURCE -> INSTALLED -> ACTIVATED -> PATH-EVIDENCE
                                      :
                                      +--> ACCEPTANCE RECORD (orthogonal decision)
```

Each layer proves only itself. `UNKNOWN` is an outcome at any observed layer,
not a lower-quality synonym for failure or absence. An acceptance record may
name technical evidence but cannot upgrade its realization stage or serve as
fresh path proof. Repository validation can prove only source contracts.

## Editing workflow

Before changing the repository:

```bash
pwd -P
git rev-parse --show-toplevel
git status --short --branch
```

For a semantic change:

1. Identify the owning specification and contract IDs.
2. Update the normative JSON first when behavior changes.
3. Update human and agent projections that explain the changed contract.
4. Update the Mintie example only if its portable mapping changes.
5. Add or revise behavior-focused validation.
6. Run `make verify`, inspect the diff, and report source, Git, remote, runtime,
   and owner-acceptance states separately.

Use one canonical path. Remove superseded behavior and references in the same
change unless a current consumer or staged compatibility boundary requires
them.

## Documentation triggers

- Update `README.md` when project identity, reader entrypoints, supported
  capability, setup, verification, or durable limitation changes.
- Update `AGENTS.md` when authority, canonical paths, privacy rules, mutation
  gates, verification, or active implementation ownership changes.
- Update `docs/current-state.md` for branch, remote, candidate/release, or
  temporary blocker changes.
- Update `docs/reference/failure-catalog.md` only for a reusable mechanism. Raw
  incident chronology and private evidence remain outside Git.
- Keep paired human documents semantically aligned through
  `contracts/docs-pairs.json`; do not let translation become a second contract.

## Verification and Git closure

The ordinary repository gate is:

```bash
make verify
git diff --check
```

Before commit or push, inspect `git status --short`, the intended diff, and the
staged diff. Stage explicit paths. Keep private continuity, raw captures,
secrets, generated junk, and unrelated work out of the commit. A clean commit
or passing test does not authorize remote creation, push, publication, or live
network mutation.
