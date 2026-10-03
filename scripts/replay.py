"""Replay portable routing, evidence-coverage and current-pointer scenarios."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

from .reference_workflow import ReferencePublisher
from .validate import (evaluate_health_evidence, expected_health_rollup,
                       health_evidence_identity, parse_rfc3339,
                       restore_gate_allows, validate_reference_traffic)


ROOT = Path(__file__).resolve().parents[1]


def load(root: Path, path: str):
    return json.loads((root / path).read_text())


def select_route(traffic: dict, deployment: dict, matched_route_ids: list[str], *,
                 roles: dict, health_profiles: dict, health_contract: dict) -> dict:
    """Select from supplied synthetic matches; this is not a DNS or packet engine."""
    errors = validate_reference_traffic(traffic, deployment, roles, health_profiles, health_contract)
    if errors:
        return {"route_id": None, "action": "retain-guard", "diagnostics": errors}
    for route in traffic["route_order"]:
        if route["id"] in matched_route_ids or route.get("match") == "otherwise":
            return {"route_id": route["id"], "action": route["action"],
                    **{k: route[k] for k in ("gateway_binding_ref", "role_binding_ref", "selection") if k in route}}
    return {"route_id": None, "action": "retain-guard"}


def assess_coverage(required: list[str], observations: dict[str, object]) -> dict:
    missing = [boundary for boundary in required if boundary not in observations]
    states = []
    for boundary in required:
        state = observations.get(boundary)
        states.append(state if isinstance(state, str) and state in {"pass", "fail", "unknown"} else "unknown")
    return {"effective_outcome": expected_health_rollup(states),
            "unobserved_boundaries": missing}


def replay_case(case: dict, root: Path = ROOT) -> dict:
    deployment = load(root, "examples/mintie/deployment.json")
    traffic = load(root, "examples/mintie/traffic-policy.json")
    context = {"roles": load(root, "contracts/roles.json"),
               "health_profiles": load(root, "examples/mintie/health-profiles.json"),
               "health_contract": load(root, "contracts/health-contract.json")}
    data = case["input"]
    if case["kind"] == "routing":
        return select_route(traffic, deployment, data["matched_route_ids"], **context)
    if case["kind"] == "routing-pair":
        domain = select_route(traffic, deployment, data["domain_request"], **context)
        ip_only = select_route(traffic, deployment, data["ip_only_request"], **context)
        return {"domain_route": domain["route_id"], "ip_route": ip_only["route_id"],
                "same_application_implies_same_route": False}
    if case["kind"] == "coverage":
        return assess_coverage(data["required_boundaries"], data["observations"])
    if case["kind"] == "client-comparison":
        awake = assess_coverage(data["required_boundaries"], data["awake"])
        sleeping = assess_coverage(data["required_boundaries"], data["sleeping"])
        localized = (data["awake"].get("ap-client-delivery") == "pass"
                     and data["sleeping"].get("ap-client-delivery") == "fail"
                     and data["awake"].get("ap-upstream") == data["sleeping"].get("ap-upstream") == "pass")
        return {"awake_outcome": awake["effective_outcome"], "sleeping_outcome": sleeping["effective_outcome"],
                "fault_boundary": "client-radio-interaction" if localized else "unknown", "root_cause": "unknown"}

    report = load(root, "examples/mintie/reports/recovery-preflight-pass.json")
    contract = load(root, "contracts/health-contract.json")
    profile = next(p for p in load(root, "examples/mintie/health-profiles.json")["profiles"] if p["id"] == report["profile_ref"])
    schema = load(root, "schemas/health-report.schema.json")
    now = parse_rfc3339(report["published_at"])
    if case["kind"] == "stale-observations":
        old = (now - timedelta(seconds=data["observation_age_seconds"])).isoformat().replace("+00:00", "Z")
        report["started_at"] = old
        for dimension in report["dimensions"].values():
            for observation in dimension["observations"]:
                observation["observed_at"] = old
        evaluation = evaluate_health_evidence(report, contract, profile, schema, now,
                                              expected_current_identity=health_evidence_identity(report))
        allowed = restore_gate_allows(report, contract, profile, schema, now,
                                      expected_gate_context=report["gate_context"],
                                      expected_current_identity=health_evidence_identity(report))
        return {"effective_outcome": evaluation.effective_outcome, "restore_allowed": allowed,
                "diagnostics": list(evaluation.errors)}

    publisher = ReferencePublisher(contract, profile, schema, report["producer_ref"], report["generation_epoch"], 41)
    attempts: dict[str, dict] = {}
    identities: dict[str, dict] = {}
    result = {}
    for event in data["events"]:
        if event["op"] == "begin":
            attempts[event["attempt"]] = publisher.begin(event["attempt"], parse_rfc3339(report["started_at"]))
        elif event["op"] == "publish":
            candidate = deepcopy(report)
            candidate.update(attempts[event["attempt"]])
            candidate["id"] = "report/sample-" + event["attempt"]
            receipt = publisher.publish(candidate, now)
            result["late_current"] = receipt["current"]
        elif event["op"] == "read":
            identities[event["as"]] = publisher.read_current()
        elif event["op"] == "restart":
            publisher = ReferencePublisher.resume(contract, profile, schema, report["producer_ref"], publisher.snapshot(),
                                                  continuity_confirmed=event["continuity_confirmed"])
        elif event["op"] == "decide":
            result.update(publisher.decide_restore(identities[event["identity"]], report["gate_context"], now))
    current = publisher.read_current()
    result["current_generation"] = current["generation"] if current else None
    result["archived_reports"] = len(publisher.snapshot()["reports"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Scenario ID; omit to replay every scenario.")
    parser.add_argument("--summary", action="store_true", help="Print a compact gate result when all scenarios pass.")
    args = parser.parse_args()
    cases = load(ROOT, "examples/scenarios/cases.json")
    selected = [case for case in cases if args.case is None or case["id"] == args.case]
    if not selected:
        parser.error("Unknown scenario ID")
    results = []
    for case in selected:
        actual = replay_case(case)
        passed = all(actual.get(key) == value for key, value in case["expected"].items())
        results.append({"id": case["id"], "passed": passed, "expected": case["expected"], "actual": actual})
    if args.summary and all(result["passed"] for result in results):
        print(f"signalbox scenario replay: PASS ({len(results)} synthetic judgments)")
    else:
        print(json.dumps(results, indent=2))
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
