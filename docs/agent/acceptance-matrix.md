# Acceptance Matrix

## Technical realization

| Stage | Required authority | Example evidence | Valid claim | Invalid leap |
| --- | --- | --- | --- | --- |
| Source | canonical repository | `make verify`, reviewed diff | source contract is consistent | payload is installed |
| Installed | exact target filesystem / registration | paths, modes, manifest or package readback | named payload is present | active process loaded it |
| Activated | process, loaded config, kernel enforcement | service state, rules, tables, guard, runtime generation | named active shape observed | client uses it |
| Path evidence | fresh profile- and role-specific probes | transport plus identity result | named lane observed under stated conditions | a person accepted it |

Every observed stage may be `unknown`. Missing, stale, malformed, regressed, or
unsupported evidence does not become failed, absent, or off automatically.

## Acceptance is not a fifth stage

An acceptance record names the actor class, decision, scope, referenced claims
and evidence, and decision time. It may record `accepted`, `rejected`, or
`revoked`. It cannot upgrade source to installed, installed to activated,
activated to path evidence, or old path evidence to current path evidence.

## Health evidence checks

- latest attempted generation has a terminal immutable `HealthReport`;
- report identity, profile reference/revision, producer, and attempt are present;
- timestamp order and `valid_until` are valid;
- generation has not regressed;
- all dimensions required by that profile are present;
- rollup matches dimension states;
- failure and unknown use allowed privacy-safe reason codes;
- byte, archive, and entry retention are bounded;
- forbidden durable keys are absent;
- recovery-preflight and operational profiles are not substituted for one another;
- observation remains separate from routing or recovery mutation.
