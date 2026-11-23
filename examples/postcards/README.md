# Postcard teaching journeys

`journeys.json` is the only authored source for the "寄往家里的信" interaction
on the reading-station home page. It contains public synthetic teaching cases:
no endpoints, live probes, health verdicts, or deployment configuration.

`scripts/build_site.py` loads and validates this file once per build. It emits
the complete readable fallback from the same records and passes the records to
the browser script, which selects a case and advances its authored steps. The
browser does not compute network reachability or permission.

The seven valid combinations are:

- a native Tailnet host with normal direct transport, blocked direct UDP, or
  service access denial;
- a client-free NAS behind a source-preserving subnet gateway with normal
  transport, blocked direct UDP, a missing LAN return route, or service access
  denial.

The missing-return-route case applies only to the source-preserving gateway.
Default SNAT does not have the same LAN return-route requirement. Its initial
packet can arrive without completing the TCP handshake. The relay stories assume
a permitted relay with its own reachable UDP path; without a peer relay, DERP may
still work. Service-denial stories have network permission but an application
refuses the identity. Relay is never
an authorization bypass and never substitutes for DIRECT or an Internet exit.

Follow the article links in each case for the relevant explanation, beginning
with [`60-travel-router`](../../docs/human/60-travel-router.zh-CN.md) and
[`70-peer-relay`](../../docs/human/70-peer-relay.zh-CN.md).
