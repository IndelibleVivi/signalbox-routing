# Glossary

- **binding** — A replaceable deployment-specific association between an
  identity, role, transport, endpoint, or host.
- **acceptance record** — A scope- and actor-bound accepted, rejected, or
  revoked decision that references evidence without upgrading it.
- **health profile** — Versioned observation policy defining purpose,
  one subject, dimensions, observation diversity, freshness, publication,
  privacy, and retention.
- **health report** — An immutable, generation-bound terminal observation tied
  to one subject and profile revision, with dimensions rolled up from explicit
  observations.
- **generation epoch** — Durable identity that scopes a report sequence across
  ordinary process and boot restarts; it changes only through explicit reset or
  migration.
- **health aggregate** — A deployment receipt that preserves each operational
  subject's report identity, sequence, and effective outcome without emitting a
  top-level health verdict.
- **observation** — One probe result with evidence class, dependency group,
  state, and observation time inside a health dimension.
- **fail closed** — Preserve protection and fail the protected path when safe
  routing cannot be established; do not degrade to DIRECT.
- **private ingress** — Approved canonical-origin traffic reaching an exact
  private origin through a dedicated gateway identity.
- **route precedence** — The ordered specific-before-general contract under
  which canonical private ingress is evaluated before DIRECT allowlists.
- **portable role** — Stable capability and policy semantics independent of a
  provider, endpoint, protocol, or friendly sample name.
- **recovery readiness** — The ability to query prior state, apply intended
  state, verify postconditions, and expose an explicit recovery outcome.
- **reference deployment** — A complete public-safe example that demonstrates
  contracts without becoming production authority.
- **realization stage** — One of source, installed, activated, or path-evidence;
  acceptance remains orthogonal.
- **sample identity** — A friendly name used inside a reference deployment.
- **underlay** — The household or wide-area network path that DIRECT traffic
  depends on, observed as its own `network-underlay` subject with an
  `underlay-operational` profile; never an egress lane and never a
  proxy-failure fallback route.
- **profile envelope** — A deployment-owned threshold band, such as a
  responsiveness or resource limit, that a profile judges against instead of a
  universal router constant.
- **unknown** — Evidence could not establish pass, fail, presence, absence, on,
  or off. Unknown is preserved rather than guessed.
