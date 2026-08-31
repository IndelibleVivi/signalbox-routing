#!/usr/bin/env python3
"""Validate Signalbox's portable source contracts without external packages."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ROLES = {
    "routing-control-plane",
    "general-primary",
    "general-secondary",
    "claude-residential",
    "private-ingress-primary",
    "private-ingress-secondary",
}
REQUIRED_REALIZATION_STAGES = [
    "source",
    "installed",
    "activated",
    "path-evidence",
]
REQUIRED_HEALTH_DIMENSIONS = {
    "transport",
    "exit-identity",
    "dns",
    "control-plane",
    "enforcement",
    "resources",
    "persistence",
    "recovery-readiness",
}
REQUIRED_RECOVERY_DIMENSIONS = {
    "control-plane",
    "enforcement",
    "resources",
    "persistence",
    "recovery-readiness",
}
REQUIRED_REPORT_FIELDS = {
    "schema",
    "id",
    "profile_ref",
    "profile_revision",
    "producer_ref",
    "generation",
    "attempt_id",
    "started_at",
    "completed_at",
    "published_at",
    "valid_until",
    "outcome",
    "dimensions",
}
REQUIRED_DIMENSION_FIELDS = {
    "state",
    "evidence_class",
    "observed_at",
    "dependency_group",
}
REQUIRED_SAMPLE_ROUTE_ORDER = [
    "protocol-observation",
    "dns-capture",
    "private-direct",
    "protected-udp-policy",
    "protected-application",
    "approved-direct",
    "canonical-private-ingress",
    "default-proxy-required",
]
REQUIRED_RESOURCE_OBSERVATIONS = {
    "memory-available",
    "routing-process-rss",
    "compressed-swap-state",
    "storage-free",
    "load",
    "recent-oom-evidence",
}

PORTABLE_TEXT_SUFFIXES = {".md", ".json", ".txt", ".yaml", ".yml"}
MACHINE_LOCAL_PATH = re.compile(
    r"(?:/(?:Users|home)/|[A-Za-z]:\\Users\\|~/\.codex(?:/|\b))"
)
IPV4_LITERAL = re.compile(
    r"(?<![\w.])(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\w.])"
)
SECRET_URI = re.compile(r"\b(?:trojan|hysteria2?|ss)://", re.IGNORECASE)
PRIVATE_KEY_BLOCK = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
SECRET_VALUE = re.compile(
    r'''["'](?:password|token|secret|private_key)["']\s*[:=]\s*["'][^"'$<][^"']+["']''',
    re.IGNORECASE,
)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_rfc3339(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp must be a non-empty string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an offset")
    return parsed.astimezone(timezone.utc)


def nested_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_roles(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "signalbox.roles/v1":
        errors.append("roles: unexpected schema")
    roles = document.get("roles")
    if not isinstance(roles, dict):
        return errors + ["roles: roles must be an object"]
    missing = sorted(REQUIRED_ROLES - set(roles))
    if missing:
        errors.append(f"roles: missing required roles {missing}")
    if "direct" in roles:
        errors.append("roles: DIRECT is an action, not a portable role")
    sample_names = {"mintie", "alder", "rowan", "hearth"}
    overlap = sorted(sample_names & set(roles))
    if overlap:
        errors.append(f"roles: sample identities used as portable roles {overlap}")
    protected = roles.get("claude-residential", {})
    expected_degradations = {"general-primary", "general-secondary", "direct"}
    actual_degradations = set(protected.get("forbidden_degradations", []))
    if actual_degradations != expected_degradations:
        errors.append("roles: protected egress must forbid general and direct degradation")
    if protected.get("optimization_target") != "recall":
        errors.append("roles: protected egress must optimize for recall")
    for role_id in ("private-ingress-primary", "private-ingress-secondary"):
        if roles.get(role_id, {}).get("server_control_required") is not True:
            errors.append(f"roles: {role_id} must require server control")
    return errors


def validate_claims(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "signalbox.claims/v1":
        errors.append("claims: unexpected schema")
    if set(document.get("observation_outcomes", [])) != {"pass", "fail", "unknown"}:
        errors.append("claims: outcomes must be pass, fail, and unknown")
    stages = document.get("realization_stages")
    if not isinstance(stages, list):
        return errors + ["claims: realization_stages must be an array"]
    try:
        ordered = sorted(stages, key=lambda item: item["rank"])
        ids = [item["id"] for item in ordered]
        ranks = [item["rank"] for item in ordered]
    except (KeyError, TypeError):
        return errors + ["claims: every realization stage requires id and rank"]
    if ids != REQUIRED_REALIZATION_STAGES:
        errors.append(f"claims: expected ordered stages {REQUIRED_REALIZATION_STAGES}")
    if len(ranks) != len(set(ranks)):
        errors.append("claims: realization stage ranks must be unique")
    for item in stages:
        if not item.get("authority") or not item.get("proves") or not item.get(
            "does_not_prove"
        ):
            errors.append(f"claims: incomplete boundary for {item.get('id', '<unknown>')}")

    expected_refs = {
        "installed": ["source_ref"],
        "activated": ["installed_ref", "runtime_generation"],
        "path-evidence": ["activated_ref", "health_report_ref"],
    }
    if document.get("required_realization_references") != expected_refs:
        errors.append("claims: realization reference chain drifted")

    acceptance = document.get("acceptance_record")
    if not isinstance(acceptance, dict):
        return errors + ["claims: acceptance_record must be an object"]
    if acceptance.get("schema") != "signalbox.acceptance-record/v1":
        errors.append("claims: acceptance record schema drifted")
    if set(acceptance.get("decisions", [])) != {"accepted", "rejected", "revoked"}:
        errors.append("claims: acceptance decisions are incomplete")
    if acceptance.get("can_upgrade_realization_stage") is not False:
        errors.append("claims: acceptance cannot upgrade technical realization")
    if acceptance.get("is_current_path_proof") is not False:
        errors.append("claims: acceptance cannot serve as current path proof")
    if "client-acceptance" in ids:
        errors.append("claims: acceptance must remain separate from realization stages")
    return errors


def validate_traffic_policy(
    document: dict[str, Any], roles_document: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "signalbox.traffic-policy/v1":
        errors.append("traffic-policy: unexpected schema")
    roles = set(roles_document.get("roles", {}))
    default = document.get("default_proxy_required", {})
    selection = default.get("selection", {})
    protected = document.get("protected_application", {})
    private = document.get("private_ingress", {})
    references = {
        document.get("routing_owner_role"),
        selection.get("role"),
        default.get("secondary_role"),
        protected.get("role"),
        private.get("primary_role"),
        private.get("secondary_role"),
    }
    for role in sorted(reference for reference in references if reference):
        if role not in roles:
            errors.append(f"traffic-policy: unresolved role reference {role}")

    direct = document.get("direct_action", {})
    if direct.get("allowed_match_kind") != "explicit-allowlist":
        errors.append("traffic-policy: DIRECT must be explicit-allowlist only")
    if direct.get("allowed_as_default") is not False:
        errors.append("traffic-policy: DIRECT cannot be the default action")
    if direct.get("allowed_on_proxy_failure") is not False:
        errors.append("traffic-policy: DIRECT cannot be a proxy-failure fallback")

    protected_scope = document.get("protected_scope", {})
    if protected_scope.get("failure_mode") != "fail-closed":
        errors.append("traffic-policy: protected scope must fail closed")
    if protected_scope.get("query_failure_outcome") != "unknown":
        errors.append("traffic-policy: query failure must remain unknown")
    if protected_scope.get("restore_requires_fresh_profile_kind") != "recovery-preflight":
        errors.append("traffic-policy: restore must require recovery-preflight health")
    if protected_scope.get("operational_profile_kind") != "operational":
        errors.append("traffic-policy: operational health profile kind drifted")
    for outcome in ("on_operational_fail", "on_operational_unknown"):
        if protected_scope.get(outcome) != "retain-guard":
            errors.append(f"traffic-policy: {outcome} must retain the guard")

    if selection.get("mode") != "pinned" or selection.get("role") != "general-primary":
        errors.append("traffic-policy: default proxy-required selection must pin general-primary")
    if default.get("secondary_role") != "general-secondary":
        errors.append("traffic-policy: default secondary role must be general-secondary")
    if default.get("automatic_failover") is not False:
        errors.append("traffic-policy: secondary existence must not imply automatic failover")

    if protected.get("role") != "claude-residential":
        errors.append("traffic-policy: protected application must use claude-residential")
    if protected.get("optimization_target") != "recall":
        errors.append("traffic-policy: protected application must optimize for recall")
    forbidden_fallback_fields = {
        "fallback",
        "fallback_role",
        "fallback_roles",
        "secondary_role",
        "automatic_failover",
    }
    present = sorted(forbidden_fallback_fields & set(protected))
    if present:
        errors.append(
            "traffic-policy: protected application structurally forbids fallback fields "
            f"{present}"
        )

    if private.get("dedicated_identity_required") is not True:
        errors.append("traffic-policy: private ingress requires a dedicated identity")
    if private.get("canonical_origin_preserved") is not True:
        errors.append("traffic-policy: private ingress must preserve canonical origin")
    if private.get("general_egress_role_equivalence") is not False:
        errors.append("traffic-policy: general egress cannot equal private ingress")
    if private.get("automatic_failover") is not False:
        errors.append("traffic-policy: private-ingress failover must not be implied")
    return errors


def validate_health_contract(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "signalbox.health-contract/v1":
        errors.append("health-contract: unexpected schema")
    if set(document.get("terminal_outcomes", [])) != {"pass", "fail", "unknown"}:
        errors.append("health-contract: terminal outcomes must be pass, fail, and unknown")
    if set(document.get("transient_outcomes", [])) != {"checking"}:
        errors.append("health-contract: checking must be the only transient outcome")
    if document.get("rollup_precedence") != ["fail", "unknown", "pass"]:
        errors.append("health-contract: rollup precedence must be fail, unknown, pass")
    if set(document.get("required_dimensions", [])) != REQUIRED_HEALTH_DIMENSIONS:
        errors.append("health-contract: operational dimensions drifted")
    if set(document.get("required_report_fields", [])) != REQUIRED_REPORT_FIELDS:
        errors.append("health-contract: required report fields drifted")
    if set(document.get("required_dimension_fields", [])) != REQUIRED_DIMENSION_FIELDS:
        errors.append("health-contract: required dimension fields drifted")

    kinds = document.get("profile_kinds", {})
    if set(kinds) != {"recovery-preflight", "operational"}:
        errors.append("health-contract: required profile kinds drifted")
    recovery = kinds.get("recovery-preflight", {})
    operational = kinds.get("operational", {})
    if set(recovery.get("required_dimensions", [])) != REQUIRED_RECOVERY_DIMENSIONS:
        errors.append("health-contract: recovery-preflight dimensions drifted")
    if recovery.get("may_gate_restore") is not True:
        errors.append("health-contract: recovery-preflight must be allowed to gate restore")
    if recovery.get("proves_operational_health") is not False:
        errors.append("health-contract: recovery-preflight cannot prove operational health")
    if set(operational.get("required_dimensions", [])) != REQUIRED_HEALTH_DIMENSIONS:
        errors.append("health-contract: operational profile dimensions drifted")
    if operational.get("may_gate_restore") is not False:
        errors.append("health-contract: operational profile cannot gate restore")
    if operational.get("proves_operational_health") is not True:
        errors.append("health-contract: operational profile must prove operational health")

    freshness = document.get("freshness", {})
    if freshness.get("basis") != "valid_until":
        errors.append("health-contract: freshness must use valid_until")
    for key in (
        "stale_effective_outcome",
        "missing_or_malformed_effective_outcome",
        "generation_regression_effective_outcome",
        "profile_revision_mismatch_effective_outcome",
    ):
        if freshness.get(key) != "unknown":
            errors.append(f"health-contract: {key} must become unknown")
    if document.get("query_failure_outcome") != "unknown":
        errors.append("health-contract: query failure must become unknown")
    if document.get("observation_only") is not True:
        errors.append("health-contract: health must be observation-only")

    publication = document.get("publication", {})
    if publication.get("terminal_report_required_for_every_attempt") is not True:
        errors.append("health-contract: every attempt requires a terminal report")
    if publication.get("early_failure_must_publish") is not True:
        errors.append("health-contract: early failure must publish a report")
    if publication.get("current_write") != "atomic-replace":
        errors.append("health-contract: current report publication must be atomic")
    if publication.get("failed_and_unknown_attempts_advance_generation") is not True:
        errors.append("health-contract: failed and unknown reports must advance generation")
    if publication.get("report_immutable") is not True:
        errors.append("health-contract: published reports must be immutable")
    if set(document.get("retention_policy_required_fields", [])) != {
        "max_file_bytes",
        "archive_count",
        "max_entries",
    }:
        errors.append("health-contract: bounded retention fields are incomplete")
    if not set(document.get("reason_codes", [])) >= {
        "timeout",
        "query-failed",
        "resource-pressure",
        "recovery-unready",
        "generation-regressed",
        "profile-revision-mismatch",
    }:
        errors.append("health-contract: reason-code vocabulary is incomplete")
    return errors


def expected_health_rollup(states: Iterable[str]) -> str:
    state_set = set(states)
    if "fail" in state_set:
        return "fail"
    if "unknown" in state_set:
        return "unknown"
    return "pass"


def validate_health_report(
    report: dict[str, Any],
    contract: dict[str, Any],
    profile: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["health report must be an object"]
    required = set(contract.get("required_report_fields", []))
    missing_fields = sorted(required - set(report))
    if missing_fields:
        errors.append(f"health report missing fields {missing_fields}")
    if report.get("schema") != "signalbox.health-report/v1":
        errors.append("health report has unexpected schema")
    for field in ("id", "profile_ref", "producer_ref", "attempt_id"):
        if not non_empty_string(report.get(field)):
            errors.append(f"health report {field} must be non-empty")
    if not isinstance(report.get("profile_revision"), int) or report.get(
        "profile_revision", 0
    ) <= 0:
        errors.append("health report profile_revision must be a positive integer")
    if not isinstance(report.get("generation"), int) or report.get("generation", 0) <= 0:
        errors.append("health report generation must be a positive integer")
    terminal = set(contract.get("terminal_outcomes", []))
    if report.get("outcome") not in terminal:
        errors.append("health report outcome must be terminal")

    times: dict[str, datetime] = {}
    for field in ("started_at", "completed_at", "published_at", "valid_until"):
        try:
            times[field] = parse_rfc3339(report.get(field))
        except (TypeError, ValueError) as exc:
            errors.append(f"health report {field}: {exc}")
    if len(times) == 4 and not (
        times["started_at"]
        <= times["completed_at"]
        <= times["published_at"]
        <= times["valid_until"]
    ):
        errors.append("health report timestamp order is invalid")

    if profile is not None:
        if report.get("profile_ref") != profile.get("id"):
            errors.append("health report profile_ref does not resolve to its profile")
        if report.get("profile_revision") != profile.get("revision"):
            errors.append("health report profile_revision does not match its profile")
        required_dimensions = set(profile.get("required_dimensions", []))
    else:
        required_dimensions = set(contract.get("required_dimensions", []))

    dimensions = report.get("dimensions")
    if not isinstance(dimensions, dict):
        return errors + ["health report dimensions must be an object"]
    actual_dimensions = set(dimensions)
    if actual_dimensions != required_dimensions:
        errors.append(
            "health report dimensions mismatch: "
            f"missing={sorted(required_dimensions - actual_dimensions)} "
            f"extra={sorted(actual_dimensions - required_dimensions)}"
        )

    required_dimension_fields = set(contract.get("required_dimension_fields", []))
    allowed_reasons = set(contract.get("reason_codes", []))
    states: list[str] = []
    for dimension in sorted(required_dimensions & actual_dimensions):
        result = dimensions[dimension]
        if not isinstance(result, dict):
            errors.append(f"health report dimension {dimension} must be an object")
            continue
        missing = sorted(required_dimension_fields - set(result))
        if missing:
            errors.append(f"health report dimension {dimension} missing {missing}")
        state = result.get("state")
        states.append(state)
        if state not in terminal:
            errors.append(f"health report dimension {dimension} is not terminal")
        for field in ("evidence_class", "dependency_group"):
            if not non_empty_string(result.get(field)):
                errors.append(f"health report dimension {dimension} lacks {field}")
        try:
            observed_at = parse_rfc3339(result.get("observed_at"))
            if "started_at" in times and "completed_at" in times:
                if not times["started_at"] <= observed_at <= times["completed_at"]:
                    errors.append(
                        f"health report dimension {dimension} observed_at is outside the run"
                    )
        except (TypeError, ValueError) as exc:
            errors.append(f"health report dimension {dimension} observed_at: {exc}")
        reason_code = result.get("reason_code")
        if state in {"fail", "unknown"} and reason_code not in allowed_reasons:
            errors.append(
                f"health report dimension {dimension} needs an allowed reason_code"
            )
        if state == "pass" and reason_code is not None:
            errors.append(f"health report dimension {dimension} pass cannot carry reason_code")

    if states and report.get("outcome") != expected_health_rollup(states):
        errors.append("health report rollup does not match dimension states")

    forbidden = set(contract.get("forbidden_durable_keys", []))
    present_forbidden = sorted(forbidden & set(nested_keys(report)))
    for key in present_forbidden:
        errors.append(f"health report contains forbidden durable key {key}")
    return errors


def effective_health_outcome(
    report: dict[str, Any],
    now: datetime,
    *,
    minimum_generation: int | None = None,
    expected_profile_ref: str | None = None,
    expected_profile_revision: int | None = None,
) -> str:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    try:
        generation = report["generation"]
        profile_revision = report["profile_revision"]
        valid_until = parse_rfc3339(report["valid_until"])
        outcome = report["outcome"]
    except (KeyError, TypeError, ValueError):
        return "unknown"
    if not isinstance(generation, int) or generation <= 0:
        return "unknown"
    if not isinstance(profile_revision, int) or profile_revision <= 0:
        return "unknown"
    if minimum_generation is not None and generation < minimum_generation:
        return "unknown"
    if expected_profile_ref is not None and report.get("profile_ref") != expected_profile_ref:
        return "unknown"
    if expected_profile_revision is not None and profile_revision != expected_profile_revision:
        return "unknown"
    if now.astimezone(timezone.utc) > valid_until:
        return "unknown"
    if outcome not in {"pass", "fail", "unknown"}:
        return "unknown"
    return outcome


def restore_gate_allows(
    report: dict[str, Any], profile: dict[str, Any], now: datetime
) -> bool:
    if profile.get("kind") != "recovery-preflight":
        return False
    return (
        effective_health_outcome(
            report,
            now,
            expected_profile_ref=profile.get("id"),
            expected_profile_revision=profile.get("revision"),
        )
        == "pass"
    )


def validate_health_profiles(
    document: dict[str, Any], contract: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "signalbox.health-profiles/v1":
        errors.append("health-profiles: unexpected schema")
    profiles = document.get("profiles")
    if not isinstance(profiles, list):
        return errors + ["health-profiles: profiles must be an array"]
    ids: set[str] = set()
    kinds: set[str] = set()
    contract_kinds = contract.get("profile_kinds", {})
    for profile in profiles:
        if not isinstance(profile, dict):
            errors.append("health-profiles: every profile must be an object")
            continue
        profile_id = profile.get("id")
        kind = profile.get("kind")
        if not non_empty_string(profile_id) or profile_id in ids:
            errors.append(f"health-profiles: duplicate or missing id {profile_id}")
        else:
            ids.add(profile_id)
        if kind not in contract_kinds or kind in kinds:
            errors.append(f"health-profiles: duplicate or unknown kind {kind}")
        else:
            kinds.add(kind)
        if not isinstance(profile.get("revision"), int) or profile.get("revision", 0) <= 0:
            errors.append(f"health-profiles: {profile_id} revision must be positive")
        if profile.get("observation_only") is not True:
            errors.append(f"health-profiles: {profile_id} must be observation-only")
        expected_dimensions = set(contract_kinds.get(kind, {}).get("required_dimensions", []))
        if set(profile.get("required_dimensions", [])) != expected_dimensions:
            errors.append(f"health-profiles: {profile_id} dimensions drifted")
        aggregation = profile.get("aggregation", {})
        if aggregation != {
            "pass_when": "all-required-pass",
            "fail_when": "any-required-fail",
            "unknown_when": "otherwise",
        }:
            errors.append(f"health-profiles: {profile_id} aggregation drifted")
        max_age = profile.get("freshness", {}).get("max_report_age_seconds")
        if not isinstance(max_age, int) or max_age <= 0:
            errors.append(f"health-profiles: {profile_id} max report age must be positive")
        publication = profile.get("publication", {})
        if publication.get("current_write") != "atomic-replace":
            errors.append(f"health-profiles: {profile_id} current write must be atomic")
        if publication.get("completed_attempt_must_publish") is not True:
            errors.append(f"health-profiles: {profile_id} must publish every completed attempt")
        retention = profile.get("retention", {})
        if not isinstance(retention.get("max_file_bytes"), int) or retention.get(
            "max_file_bytes", 0
        ) <= 0:
            errors.append(f"health-profiles: {profile_id} max_file_bytes must be positive")
        if not isinstance(retention.get("archive_count"), int) or retention.get(
            "archive_count", -1
        ) < 0:
            errors.append(f"health-profiles: {profile_id} archive_count must be non-negative")
        if not isinstance(retention.get("max_entries"), int) or retention.get(
            "max_entries", 0
        ) <= 0:
            errors.append(f"health-profiles: {profile_id} max_entries must be positive")
        privacy = profile.get("privacy", {})
        if privacy.get("result_detail") != "reason-code-only" or privacy.get(
            "raw_diagnostics"
        ) != "forbidden":
            errors.append(f"health-profiles: {profile_id} privacy boundary drifted")
        if not non_empty_string(profile.get("resource_threshold_owner")):
            errors.append(f"health-profiles: {profile_id} lacks resource threshold owner")

        if kind == "operational":
            interval = profile.get("run_interval_seconds")
            if not isinstance(interval, int) or interval <= 0:
                errors.append("health-profiles: operational interval must be positive")
            elif isinstance(max_age, int) and max_age < interval:
                errors.append("health-profiles: operational freshness must cover one interval")
            diversity = profile.get("probe_diversity", {})
            if diversity.get("single_provider_sufficient") is not False:
                errors.append("health-profiles: one provider cannot be sufficient")
            for key in ("transport_neutral_minimum", "role_specific_minimum"):
                if not isinstance(diversity.get(key), int) or diversity.get(key, 0) <= 0:
                    errors.append(f"health-profiles: operational {key} must be positive")
            if set(profile.get("resource_observations", [])) != REQUIRED_RESOURCE_OBSERVATIONS:
                errors.append("health-profiles: operational resource observations are incomplete")
    if kinds != {"recovery-preflight", "operational"}:
        errors.append("health-profiles: one profile of each required kind is required")
    return errors


def validate_deployment(
    deployment: dict[str, Any], roles_document: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if deployment.get("schema") != "signalbox.reference-deployment/v1":
        errors.append("deployment: unexpected schema")
    if deployment.get("deployment_id") != "mintie":
        errors.append("deployment: reference deployment must be mintie")
    if deployment.get("sample_only") is not True:
        errors.append("deployment: sample_only must be true")
    if deployment.get("private_live_bindings") != "external-and-absent":
        errors.append("deployment: private live bindings must be external and absent")
    if deployment.get("traffic_policy_ref") != "traffic-policy.json":
        errors.append("deployment: traffic policy reference drifted")
    if deployment.get("health_profiles_ref") != "health-profiles.json":
        errors.append("deployment: health profile reference drifted")
    roles = set(roles_document.get("roles", {}))
    router = deployment.get("router", {})
    if router.get("identity") != "mintie" or router.get("role") != "routing-control-plane":
        errors.append("deployment: Mintie must bind routing-control-plane")
    instances = deployment.get("instances", {})
    expected_bindings = {
        "alder": ["general-primary"],
        "rowan": ["general-secondary"],
        "hearth": ["claude-residential"],
    }
    for identity, expected_roles in expected_bindings.items():
        if instances.get(identity, {}).get("roles") != expected_roles:
            errors.append(f"deployment: {identity} role binding drifted")
    for identity, instance in instances.items():
        for role in instance.get("roles", []):
            if role not in roles:
                errors.append(f"deployment: {identity} references unknown role {role}")
    gateways = deployment.get("dedicated_gateway_identities", {})
    expected_gateways = {
        "alder-private": ("alder", "private-ingress-primary"),
        "rowan-private": ("rowan", "private-ingress-secondary"),
    }
    for identity, (host, role) in expected_gateways.items():
        gateway = gateways.get(identity, {})
        if gateway.get("host_instance") != host or gateway.get("role") != role:
            errors.append(f"deployment: {identity} gateway binding drifted")
        if gateway.get("credential_scope") != "dedicated":
            errors.append(f"deployment: {identity} must use dedicated credentials")
        if gateway.get("general_egress_equivalent") is not False:
            errors.append(f"deployment: {identity} cannot equal general egress")
        if role not in roles:
            errors.append(f"deployment: {identity} references unknown role {role}")
    origins = deployment.get("canonical_origins", {})
    if not origins or any(
        origin.get("hostname_ref") != "deployment-owned-and-absent"
        for origin in origins.values()
    ):
        errors.append("deployment: canonical origins must use absent deployment-owned bindings")
    return errors


def validate_reference_traffic(
    traffic: dict[str, Any], deployment: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if traffic.get("schema") != "signalbox.reference-traffic-policy/v1":
        errors.append("reference-traffic: unexpected schema")
    if traffic.get("deployment_ref") != "deployment.json":
        errors.append("reference-traffic: deployment reference drifted")
    route_order = traffic.get("route_order", [])
    ids = [entry.get("id") for entry in route_order if isinstance(entry, dict)]
    if ids != REQUIRED_SAMPLE_ROUTE_ORDER:
        errors.append("reference-traffic: route order drifted")
    entries = {entry.get("id"): entry for entry in route_order if isinstance(entry, dict)}

    for entry in route_order:
        if not isinstance(entry, dict) or entry.get("action") != "direct":
            continue
        match = entry.get("match")
        if not isinstance(match, dict) or match.get("kind") != "explicit-allowlist":
            errors.append(f"reference-traffic: direct action {entry.get('id')} lacks allowlist")

    protected = entries.get("protected-application", {})
    if protected.get("role_binding_ref") != "hearth":
        errors.append("reference-traffic: protected traffic must use Hearth")
    forbidden_fallback_fields = {
        "fallback",
        "fallback_instance",
        "fallback_instances",
        "secondary_binding_ref",
        "automatic_failover",
    }
    present = sorted(forbidden_fallback_fields & set(protected))
    if present:
        errors.append(
            "reference-traffic: protected traffic structurally forbids fallback fields "
            f"{present}"
        )
    udp = entries.get("protected-udp-policy", {})
    if udp.get("action") != "reject-until-verified":
        errors.append("reference-traffic: protected UDP must reject until verified")

    default = entries.get("default-proxy-required", {})
    selection = default.get("selection", {})
    if selection.get("mode") != "pinned" or selection.get("role_binding_ref") != "alder":
        errors.append("reference-traffic: default traffic must pin Alder")
    if forbidden_fallback_fields & set(default):
        errors.append("reference-traffic: default automatic fallback is not defined")

    private = entries.get("canonical-private-ingress", {})
    gateways = deployment.get("dedicated_gateway_identities", {})
    origins = deployment.get("canonical_origins", {})
    if private.get("gateway_binding_ref") not in gateways:
        errors.append("reference-traffic: private ingress must use a dedicated identity")
    if private.get("canonical_origin_ref") not in origins:
        errors.append("reference-traffic: private ingress canonical origin must resolve")
    instances = deployment.get("instances", {})
    for entry in (protected, default):
        binding = entry.get("role_binding_ref") or entry.get("selection", {}).get(
            "role_binding_ref"
        )
        if binding not in instances:
            errors.append(f"reference-traffic: unresolved instance binding {binding}")

    failure = traffic.get("failure_behavior", {})
    if failure != {
        "mode": "fail-closed",
        "on_fail": "retain-guard",
        "on_unknown": "retain-guard",
    }:
        errors.append("reference-traffic: fail-closed behavior drifted")
    if "proxy_failure_fallback" in traffic:
        errors.append("reference-traffic: proxy failure fallback field must be absent")
    return errors


def validate_reference_health_links(
    traffic: dict[str, Any], health_profiles: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    profiles = {
        profile.get("id"): profile
        for profile in health_profiles.get("profiles", [])
        if isinstance(profile, dict)
    }
    refs = traffic.get("health_profile_refs", {})
    expected = {
        "recovery_preflight": "recovery-preflight",
        "operational": "operational",
    }
    for ref_key, expected_kind in expected.items():
        profile = profiles.get(refs.get(ref_key))
        if not profile or profile.get("kind") != expected_kind:
            errors.append(f"reference-health: {ref_key} must resolve to {expected_kind}")
    return errors


def validate_doc_pairs(root: Path, document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for pair in document.get("pairs", []):
        doc_id = pair.get("doc_id")
        if not doc_id or doc_id in seen:
            errors.append(f"docs-pairs: duplicate or missing doc_id {doc_id}")
        seen.add(doc_id)
        required_ids = pair.get("required_contract_ids", [])
        for language in ("zh-CN", "en"):
            relative = pair.get(language)
            path = root / relative if isinstance(relative, str) else None
            if path is None or not path.is_file():
                errors.append(f"docs-pairs: missing {language} file for {doc_id}: {relative}")
                continue
            text = path.read_text(encoding="utf-8")
            if f"doc_id: {doc_id}" not in text:
                errors.append(f"docs-pairs: {relative} has the wrong doc_id")
            for contract_id in required_ids:
                if contract_id not in text:
                    errors.append(f"docs-pairs: {relative} missing {contract_id}")
    return errors


def iter_portable_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix in PORTABLE_TEXT_SUFFIXES:
            yield path
        elif path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if candidate.is_file() and candidate.suffix in PORTABLE_TEXT_SUFFIXES:
                    yield candidate


def scan_portable_boundaries(root: Path, paths: Iterable[Path]) -> list[str]:
    errors: list[str] = []
    checks = (
        (MACHINE_LOCAL_PATH, "machine-local path"),
        (IPV4_LITERAL, "IP address literal"),
        (SECRET_URI, "credential-bearing URI"),
        (PRIVATE_KEY_BLOCK, "private key material"),
        (SECRET_VALUE, "credential value"),
    )
    for path in iter_portable_files(paths):
        text = path.read_text(encoding="utf-8")
        try:
            label = path.relative_to(root)
        except ValueError:
            label = path
        for pattern, description in checks:
            if pattern.search(text):
                errors.append(f"portable-boundary: {label} contains {description}")
    return errors


def validate_markdown_links(root: Path, paths: Iterable[Path]) -> list[str]:
    errors: list[str] = []
    for path in iter_portable_files(paths):
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            clean = target.strip().strip("<>")
            if clean.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = clean.split("#", 1)[0]
            if not clean:
                continue
            resolved = (path.parent / clean).resolve()
            if not resolved.exists():
                errors.append(f"links: {path.relative_to(root)} points to missing {target}")
    return errors


def validate_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    required_files = [
        "README.md",
        "AGENTS.md",
        "docs/specification.md",
        "docs/programme-plan.md",
        "docs/current-state.md",
        "contracts/roles.json",
        "contracts/claims.json",
        "contracts/traffic-policy.json",
        "contracts/health-contract.json",
        "contracts/docs-pairs.json",
        "examples/mintie/deployment.json",
        "examples/mintie/traffic-policy.json",
        "examples/mintie/health-profiles.json",
    ]
    for relative in required_files:
        if not (root / relative).is_file():
            errors.append(f"repository: missing required file {relative}")
    if errors:
        return errors

    try:
        roles = load_json(root / "contracts/roles.json")
        claims = load_json(root / "contracts/claims.json")
        traffic = load_json(root / "contracts/traffic-policy.json")
        health_contract = load_json(root / "contracts/health-contract.json")
        docs_pairs = load_json(root / "contracts/docs-pairs.json")
        deployment = load_json(root / "examples/mintie/deployment.json")
        reference_traffic = load_json(root / "examples/mintie/traffic-policy.json")
        health_profiles = load_json(root / "examples/mintie/health-profiles.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"repository: JSON load failed: {exc}"]

    errors.extend(validate_roles(roles))
    errors.extend(validate_claims(claims))
    errors.extend(validate_traffic_policy(traffic, roles))
    errors.extend(validate_health_contract(health_contract))
    errors.extend(validate_doc_pairs(root, docs_pairs))
    errors.extend(validate_deployment(deployment, roles))
    errors.extend(validate_reference_traffic(reference_traffic, deployment))
    errors.extend(validate_health_profiles(health_profiles, health_contract))
    errors.extend(validate_reference_health_links(reference_traffic, health_profiles))

    profile_by_id = {
        profile.get("id"): profile
        for profile in health_profiles.get("profiles", [])
        if isinstance(profile, dict)
    }
    for fixture in sorted((root / "tests/fixtures").glob("health-*.json")):
        try:
            report = load_json(fixture)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"health fixture {fixture.name}: JSON load failed: {exc}")
            continue
        profile = profile_by_id.get(report.get("profile_ref"))
        if profile is None:
            errors.append(
                f"health fixture {fixture.name}: unresolved profile {report.get('profile_ref')}"
            )
            continue
        for error in validate_health_report(report, health_contract, profile):
            errors.append(f"health fixture {fixture.name}: {error}")

    portable_paths = [
        root / "README.md",
        root / "AGENTS.md",
        root / "contracts",
        root / "docs",
        root / "examples",
    ]
    errors.extend(scan_portable_boundaries(root, portable_paths))
    errors.extend(
        validate_markdown_links(
            root,
            [root / "README.md", root / "AGENTS.md", root / "docs", root / "examples"],
        )
    )

    specification = (root / "docs/specification.md").read_text(encoding="utf-8")
    for contract_id in (
        "SIG-01",
        "IDENT-02",
        "CLAIM-03",
        "ROUTE-02",
        "ROUTE-04",
        "ENFORCE-01",
        "PRIVATE-01",
        "HEALTH-02",
        "HEALTH-07",
        "UPDATE-03",
        "ACCEPT-08",
    ):
        if contract_id not in specification:
            errors.append(f"specification: missing required contract ID {contract_id}")

    failure_catalog = (root / "docs/reference/failure-catalog.md").read_text(
        encoding="utf-8"
    )
    for failure_id in ("FAIL-001", "FAIL-002", "FAIL-003", "FAIL-004", "FAIL-005"):
        if failure_id not in failure_catalog:
            errors.append(f"failure-catalog: missing {failure_id}")
    return errors


def main() -> int:
    errors = validate_repository(ROOT)
    if errors:
        print("signalbox validation: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    fixture_count = len(list((ROOT / "tests/fixtures").glob("health-*.json")))
    print(f"signalbox validation: PASS ({fixture_count} health fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
