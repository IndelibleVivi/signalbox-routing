# Security and private operational reports

Signalbox is a source reference system, not a hosted routing service. Security
reports may still concern a contract, example, validator, documentation path,
or repository setting that could encourage unsafe routing, leak private
operational data, or misstate an evidence boundary.

## Report privately

Use [GitHub private vulnerability reporting](https://github.com/IndelibleVivi/signalbox-routing/security/advisories/new)
for a suspected security or privacy issue. Include the affected tracked path,
the unsafe behavior or claim, and a public-safe reproduction when one exists.

Do not put live endpoints, IP addresses, credentials, private keys, router
configuration, raw router or provider readback, account data, or private
incident evidence in a public issue, pull request, discussion, or attachment.
If a safe reproduction cannot be made without those materials, describe the
class of evidence privately and wait for a bounded follow-up.

## Scope and evidence

The maintained source line is the current `main` branch. A repository fix or
passing CI run proves only tracked source. It does not prove that a private
payload is installed, activated, reachable, or accepted, and it does not
authorize access to or mutation of any live router or network.

Operational trouble on a private deployment is not automatically a public
Signalbox vulnerability. Preserve the private evidence boundary first; only a
portable, source-level mechanism belongs in this repository.
