"""Validate synthetic, scoped claims and historical acceptance records."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .repository_paths import RepositoryPathError, resolve_repository_path
from .validate import evaluate_health_evidence, expected_health_rollup, parse_rfc3339


ROOT = Path(__file__).resolve().parents[1]


def evaluate_handoff(
    root: Path, document: Any, evaluated_at: datetime
) -> dict[str, Any]:
    """Structure first; bundle IDs and repository artifacts are separate namespaces.

    An actor decision is historical. Technical claims are evaluated at the
    requested time, so a past acceptance cannot renew a current path claim.
    This validates a public-safe synthetic reference, never live realization.
    """
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must be timezone-aware")
    diagnostics: list[dict[str, str]] = []

    def reject(code: str, path: str, message: str) -> None:
        diagnostics.append({"code": code, "path": path, "message": message})

    schema = json.loads((root / "schemas/handoff.schema.json").read_text())
    for error in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document):
        reject("malformed-handoff", "/" + "/".join(map(str, error.absolute_path)), error.message)
    if diagnostics:
        return {"valid": False, "claim_outcomes": {}, "diagnostics": diagnostics}

    scope = document["scope_ref"]
    evidence: dict[str, dict[str, Any]] = {}
    claims: dict[str, dict[str, Any]] = {}
    records: set[str] = set()
    for group, identifier, target in (
        ("evidence", "id", evidence), ("claims", "claim_id", claims)
    ):
        for index, item in enumerate(document[group]):
            path = f"/{group}/{index}"
            if item[identifier] in target:
                reject("duplicate-id", path + "/" + identifier, item[identifier])
            target[item[identifier]] = item
            if item["scope_ref"] != scope:
                reject("scope-mismatch", path + "/scope_ref", "Scope must exact-match the handoff.")
    for index, item in enumerate(document["acceptance_records"]):
        if item["record_id"] in records:
            reject("duplicate-id", f"/acceptance_records/{index}/record_id", item["record_id"])
        records.add(item["record_id"])

    def available(item: dict[str, Any], at: datetime, path: str) -> None:
        if parse_rfc3339(item["observed_at"]) > at:
            reject("evidence-not-yet-available", path, "Observation is later than the decision.")
        if "valid_until" in item:
            expiry = parse_rfc3339(item["valid_until"])
            if expiry < parse_rfc3339(item["observed_at"]):
                reject("invalid-evidence-window", path, "Evidence expires before its observation.")
            if expiry < at:
                reject("stale-evidence", path, "Evidence had expired at the requested decision time.")

    for index, item in enumerate(document["evidence"]):
        try:
            resolve_repository_path(root, item["artifact_ref"], expected_kind="file")
        except RepositoryPathError as exc:
            reject("unresolved-artifact", f"/evidence/{index}/artifact_ref", str(exc))

    contract = json.loads((root / "contracts/health-contract.json").read_text())
    profiles = {p["id"]: p for p in json.loads((root / "examples/mintie/health-profiles.json").read_text())["profiles"]}
    report_schema = json.loads((root / "schemas/health-report.schema.json").read_text())
    requirements = {
        "source": {},
        "installed": {"source_ref": "source"},
        "activated": {"installed_ref": "installed"},
        "path-evidence": {"activated_ref": "activated"},
    }
    outcomes: dict[str, str] = {}
    for index, claim in enumerate(document["claims"]):
        path = f"/claims/{index}"
        stage = claim["stage"]
        observed = parse_rfc3339(claim["observed_at"])
        if observed > evaluated_at:
            reject("claim-not-yet-available", path + "/observed_at", "Claim is later than evaluation.")
        states = []
        cited_report_paths: set[Path] = set()
        for ref in claim["evidence_refs"]:
            item = evidence.get(ref)
            if item is None:
                reject("unresolved-evidence", path + "/evidence_refs", ref)
                continue
            if item["stage"] != stage:
                reject("stage-mismatch", path + "/evidence_refs", "Evidence cannot upgrade realization.")
            available(item, observed, path + "/evidence_refs")
            if stage == "path-evidence":
                available(item, evaluated_at, path + "/evidence_refs")
                if item["stage"] == "path-evidence":
                    try:
                        cited_report_paths.add(resolve_repository_path(root, item["artifact_ref"], expected_kind="file"))
                    except RepositoryPathError:
                        pass  # The artifact diagnostic above already rejects this reference.
            states.append(item["outcome"])
        expected_fields = set(requirements[stage])
        if stage == "activated":
            expected_fields.add("runtime_generation")
        if stage == "path-evidence":
            expected_fields.update(("health_report_ref", "current_health_identity"))
        reference_fields = {"source_ref", "installed_ref", "runtime_generation", "activated_ref", "health_report_ref", "current_health_identity"}
        if set(claim) & reference_fields != expected_fields:
            reject("realization-reference-grammar", path, f"Stage {stage} requires exactly {sorted(expected_fields)}.")
        for field, required_stage in requirements[stage].items():
            previous = claims.get(claim.get(field))
            if previous is None:
                reject("unresolved-claim", path + "/" + field, str(claim.get(field)))
            elif previous["stage"] != required_stage or previous["scope_ref"] != scope:
                reject("realization-chain-mismatch", path + "/" + field, "Prior claim stage/scope differs.")
            elif parse_rfc3339(previous["observed_at"]) > observed:
                reject("claim-order-mismatch", path + "/" + field, "Prior stage was observed later.")

        if stage == "path-evidence" and "health_report_ref" in claim:
            try:
                report_path = resolve_repository_path(root, claim["health_report_ref"], expected_kind="file")
                if report_path not in cited_report_paths:
                    reject("uncited-health-report", path + "/health_report_ref", "The evaluated report must be cited by path-evidence references.")
                report = json.loads(report_path.read_text())
            except (RepositoryPathError, OSError, json.JSONDecodeError) as exc:
                reject("unresolved-health-report", path + "/health_report_ref", str(exc))
            else:
                profile = profiles.get(report.get("profile_ref")) if isinstance(report, dict) and isinstance(report.get("profile_ref"), str) else None
                if profile is None:
                    reject("unresolved-health-profile", path + "/health_report_ref", "Report profile is not registered.")
                elif "current_health_identity" in claim:
                    if report.get("subject_ref") != scope:
                        reject("health-scope-mismatch", path + "/scope_ref", "Path claim scope must exact-match the report subject.")
                    for instant in (observed, evaluated_at):
                        evaluation = evaluate_health_evidence(report, contract, profile, report_schema, instant, expected_current_identity=claim["current_health_identity"])
                        states.append(evaluation.effective_outcome)
                        if not evaluation.structurally_valid or not evaluation.semantically_valid:
                            reject("malformed-path-evidence", path + "/health_report_ref", "; ".join(evaluation.errors))
                        if "evidence-not-yet-published" in evaluation.reason_codes:
                            reject("unpublished-path-evidence", path + "/health_report_ref", "The report must be published at claim and evaluation times, including for unknown claims.")
                        if claim["outcome"] != evaluation.effective_outcome:
                            reject("unusable-path-evidence", path + "/health_report_ref", "; ".join(evaluation.reason_codes) or f"Canonical report outcome is {evaluation.effective_outcome}.")
        expected = expected_health_rollup(states) if states else "unknown"
        outcomes[claim["claim_id"]] = expected
        if claim["outcome"] != expected:
            reject("claim-outcome-mismatch", path + "/outcome", f"Supported outcome is {expected}.")

    for index, record in enumerate(document["acceptance_records"]):
        path = f"/acceptance_records/{index}"
        decided = parse_rfc3339(record["decided_at"])
        if record["scope_ref"] != scope:
            reject("scope-mismatch", path + "/scope_ref", "Acceptance scope must exact-match.")
        if decided > evaluated_at:
            reject("decision-not-yet-available", path + "/decided_at", "Decision is later than evaluation.")
        cited_evidence: set[str] = set()
        for ref in record["claim_refs"]:
            claim = claims.get(ref)
            if claim is None:
                reject("unresolved-claim", path + "/claim_refs", ref)
            else:
                cited_evidence.update(claim["evidence_refs"])
                if claim["scope_ref"] != scope or parse_rfc3339(claim["observed_at"]) > decided:
                    reject("acceptance-claim-mismatch", path + "/claim_refs", "Claim scope/time does not support this decision.")
        if not cited_evidence.issubset(set(record["evidence_refs"])):
            reject("acceptance-evidence-incomplete", path + "/evidence_refs", "Acceptance must cite each named claim's evidence.")
        for ref in record["evidence_refs"]:
            item = evidence.get(ref)
            if item is None:
                reject("unresolved-evidence", path + "/evidence_refs", ref)
            else:
                available(item, decided, path + "/evidence_refs")
    return {"valid": not diagnostics, "claim_outcomes": outcomes, "diagnostics": diagnostics}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default="examples/mintie/handoff.json")
    parser.add_argument("--evaluated-at", required=True, help="Explicit RFC3339 evaluation time; samples are historical.")
    parser.add_argument("--summary", action="store_true", help="Print a compact source-gate result on success.")
    args = parser.parse_args()
    path = resolve_repository_path(ROOT, args.file, expected_kind="file")
    result = evaluate_handoff(ROOT, json.loads(path.read_text()), parse_rfc3339(args.evaluated_at))
    if args.summary and result["valid"]:
        print(f"signalbox handoff: PASS ({len(result['claim_outcomes'])} synthetic claims)")
    else:
        print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
