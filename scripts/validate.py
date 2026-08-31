#!/usr/bin/env python3
"""Validate Signalbox's portable source contracts without external packages."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
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
REQUIRED_REPORT_FIELDS = {
    "schema",
    "id",
    "profile_ref",
    "profile_revision",
    "producer_ref",
    "subject_ref",
    "generation_epoch",
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
    "observations",
}
REQUIRED_OBSERVATION_FIELDS = {
    "probe_ref",
    "evidence_class",
    "dependency_group",
    "state",
    "observed_at",
}
REQUIRED_SAMPLE_ROUTE_ORDER = [
    "protocol-observation",
    "dns-capture",
    "canonical-private-ingress",
    "protected-udp-policy",
    "protected-application",
    "private-direct",
    "approved-direct",
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
    if document.get("schema") != "signalbox.traffic-policy/v2":
        errors.append("traffic-policy: unexpected schema")
    precedence = document.get("route_precedence", {})
    if precedence.get("specific_before_general") is not True:
        errors.append("traffic-policy: route precedence must be specific before general")
    if precedence.get("canonical_private_ingress_before_direct") is not True:
        errors.append("traffic-policy: canonical private ingress must precede DIRECT")
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
    if set(protected_scope.get("operational_profile_kinds", [])) != {
        "control-plane-operational",
        "lane-operational",
    }:
        errors.append("traffic-policy: operational health profile kinds drifted")
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
    if document.get("schema") != "signalbox.health-contract/v3":
        errors.append("health-contract: unexpected schema")
    if document.get("contract_revision") != 3:
        errors.append("health-contract: unexpected revision")
    if set(document.get("terminal_outcomes", [])) != {"pass", "fail", "unknown"}:
        errors.append("health-contract: terminal outcomes must be pass, fail, and unknown")
    if set(document.get("transient_outcomes", [])) != {"checking"}:
        errors.append("health-contract: checking must be the only transient outcome")
    if document.get("rollup_precedence") != ["fail", "unknown", "pass"]:
        errors.append("health-contract: rollup precedence must be fail, unknown, pass")
    if set(document.get("required_report_fields", [])) != REQUIRED_REPORT_FIELDS:
        errors.append("health-contract: required report fields drifted")
    if set(document.get("required_dimension_fields", [])) != REQUIRED_DIMENSION_FIELDS:
        errors.append("health-contract: required dimension fields drifted")
    if set(document.get("required_observation_fields", [])) != REQUIRED_OBSERVATION_FIELDS:
        errors.append("health-contract: required observation fields drifted")

    kinds = document.get("profile_kinds", {})
    expected_kinds = {
        "recovery-preflight",
        "control-plane-operational",
        "lane-operational",
    }
    if set(kinds) != expected_kinds:
        errors.append("health-contract: required profile kinds drifted")
    recovery = kinds.get("recovery-preflight", {})
    if recovery.get("may_gate_restore") is not True:
        errors.append("health-contract: recovery-preflight must be allowed to gate restore")
    if recovery.get("may_feed_deployment_aggregate") is not False:
        errors.append("health-contract: recovery reports cannot feed the deployment aggregate")
    for kind_id in ("control-plane-operational", "lane-operational"):
        kind = kinds.get(kind_id, {})
        if kind.get("may_gate_restore") is not False:
            errors.append(f"health-contract: {kind_id} cannot gate restore")
        if kind.get("may_feed_deployment_aggregate") is not True:
            errors.append(f"health-contract: {kind_id} must feed the aggregate")
        if not kind.get("required_dimensions"):
            errors.append(f"health-contract: {kind_id} dimensions are missing")
    if set(kinds.get("lane-operational", {}).get("required_dimensions", [])) != {
        "transport",
        "exit-identity",
        "dns",
    }:
        errors.append("health-contract: lane dimensions drifted")
    control_dimensions = {
        "control-plane",
        "enforcement",
        "resources",
        "persistence",
        "recovery-readiness",
    }
    for kind_id in ("recovery-preflight", "control-plane-operational"):
        if set(kinds.get(kind_id, {}).get("required_dimensions", [])) != control_dimensions:
            errors.append(f"health-contract: {kind_id} dimensions drifted")

    generation = document.get("generation", {})
    if generation.get("scope_fields") != [
        "producer_ref",
        "subject_ref",
        "profile_ref",
        "generation_epoch",
    ]:
        errors.append("health-contract: generation scope must bind producer, subject, profile, and epoch")
    if generation.get("monotonic_within_scope") is not True:
        errors.append("health-contract: generation must be monotonic within its scope")
    if generation.get("epoch_change_requires") != "explicit-reset-or-migration":
        errors.append("health-contract: generation epoch changes require reset or migration")
    if generation.get("unexpected_epoch_effective_outcome") != "unknown":
        errors.append("health-contract: unexpected generation epoch must become unknown")

    freshness = document.get("freshness", {})
    if freshness.get("basis") != "valid_until":
        errors.append("health-contract: freshness must use valid_until")
    for key in (
        "stale_effective_outcome",
        "missing_or_malformed_effective_outcome",
        "profile_revision_mismatch_effective_outcome",
    ):
        if freshness.get(key) != "unknown":
            errors.append(f"health-contract: {key} must become unknown")
    if freshness.get("maximum_formula") != (
        "valid_until <= completed_at + profile.max_report_age_seconds"
    ):
        errors.append("health-contract: profile-bound freshness formula drifted")
    if freshness.get("published_before_or_at_valid_until") is not True:
        errors.append("health-contract: publication must precede expiry")

    gate = document.get("recovery_gate", {})
    if gate.get("profile_kind") != "recovery-preflight":
        errors.append("health-contract: restore gate profile kind drifted")
    if set(gate.get("required_context_fields", [])) != {
        "operation_ref",
        "desired_state_digest",
        "observed_runtime_generation",
        "restore_scope_ref",
    }:
        errors.append("health-contract: restore gate context fields are incomplete")
    if gate.get("exact_context_match_required") is not True:
        errors.append("health-contract: restore gate context must exact-match")

    aggregate = document.get("deployment_aggregate", {})
    if aggregate.get("preserve_per_subject_outcome") is not True:
        errors.append("health-contract: deployment aggregate must preserve subject outcomes")
    if aggregate.get("top_level_outcome_forbidden") is not True:
        errors.append("health-contract: aggregate top-level outcome must be forbidden")
    if aggregate.get("recovery_preflight_members_forbidden") is not True:
        errors.append("health-contract: aggregate must exclude recovery-preflight reports")
    if aggregate.get("evaluated_at_must_equal_assembled_at") is not True:
        errors.append("health-contract: aggregate evaluation must occur at assembly")
    if aggregate.get("member_outcome_field") != "effective_outcome_at_assembly":
        errors.append("health-contract: aggregate member outcome field drifted")
    if aggregate.get("historical_receipt") is not True:
        errors.append("health-contract: aggregate must remain a historical receipt")
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
        "generation-epoch-mismatch",
        "profile-revision-mismatch",
        "gate-context-mismatch",
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
    if report.get("schema") != "signalbox.health-report/v2":
        errors.append("health report has unexpected schema")
    for field in (
        "id",
        "profile_ref",
        "producer_ref",
        "subject_ref",
        "generation_epoch",
        "attempt_id",
    ):
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

    if profile is None:
        return errors + ["health report requires its referenced profile for semantics"]
    if report.get("profile_ref") != profile.get("id"):
        errors.append("health report profile_ref does not resolve to its profile")
    if report.get("profile_revision") != profile.get("revision"):
        errors.append("health report profile_revision does not match its profile")
    if report.get("subject_ref") != profile.get("subject_ref"):
        errors.append("health report subject_ref does not match its profile")
    required_dimensions = set(profile.get("required_dimensions", []))
    if len(times) == 4:
        max_age = profile.get("freshness", {}).get("max_report_age_seconds")
        if isinstance(max_age, int) and times["valid_until"] > (
            times["completed_at"] + timedelta(seconds=max_age)
        ):
            errors.append("health report valid_until exceeds profile freshness")

    gate_fields = set(
        contract.get("recovery_gate", {}).get("required_context_fields", [])
    )
    gate_context = report.get("gate_context")
    if profile.get("kind") == "recovery-preflight":
        if not isinstance(gate_context, dict):
            errors.append("health report recovery-preflight requires gate_context")
        else:
            missing_gate = sorted(gate_fields - set(gate_context))
            if missing_gate:
                errors.append(f"health report gate_context missing {missing_gate}")
            for field in gate_fields:
                if not non_empty_string(gate_context.get(field)):
                    errors.append(f"health report gate_context {field} must be non-empty")
            digest = gate_context.get("desired_state_digest")
            if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                errors.append("health report desired_state_digest must be sha256")
            if gate_context.get("restore_scope_ref") != report.get("subject_ref"):
                errors.append("health report restore_scope_ref must match subject_ref")
    elif gate_context is not None:
        errors.append("health report non-recovery profile cannot carry gate_context")

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
    required_observation_fields = set(contract.get("required_observation_fields", []))
    allowed_reasons = set(contract.get("reason_codes", []))
    probe_requirements = profile.get("probe_requirements", {})
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
        observations = result.get("observations")
        if not isinstance(observations, list) or not observations:
            errors.append(f"health report dimension {dimension} needs observations")
            continue
        observation_states: list[str] = []
        evidence_counts: dict[str, int] = {}
        dependency_groups: set[str] = set()
        probe_refs: set[str] = set()
        for index, observation in enumerate(observations):
            if not isinstance(observation, dict):
                errors.append(
                    f"health report dimension {dimension} observation {index} must be an object"
                )
                continue
            missing_observation = sorted(required_observation_fields - set(observation))
            if missing_observation:
                errors.append(
                    f"health report dimension {dimension} observation {index} missing "
                    f"{missing_observation}"
                )
            for field in ("probe_ref", "evidence_class", "dependency_group"):
                if not non_empty_string(observation.get(field)):
                    errors.append(
                        f"health report dimension {dimension} observation {index} lacks {field}"
                    )
            probe_ref = observation.get("probe_ref")
            if probe_ref in probe_refs:
                errors.append(f"health report dimension {dimension} repeats probe_ref {probe_ref}")
            elif isinstance(probe_ref, str):
                probe_refs.add(probe_ref)
            observation_state = observation.get("state")
            observation_states.append(observation_state)
            if observation_state not in terminal:
                errors.append(
                    f"health report dimension {dimension} observation {index} is not terminal"
                )
            evidence_class = observation.get("evidence_class")
            if isinstance(evidence_class, str):
                evidence_counts[evidence_class] = evidence_counts.get(evidence_class, 0) + 1
            dependency_group = observation.get("dependency_group")
            if isinstance(dependency_group, str) and dependency_group:
                dependency_groups.add(dependency_group)
            try:
                observed_at = parse_rfc3339(observation.get("observed_at"))
                if "started_at" in times and "completed_at" in times:
                    if not times["started_at"] <= observed_at <= times["completed_at"]:
                        errors.append(
                            f"health report dimension {dimension} observation {index} "
                            "is outside the run"
                        )
            except (TypeError, ValueError) as exc:
                errors.append(
                    f"health report dimension {dimension} observation {index} observed_at: {exc}"
                )
            reason_code = observation.get("reason_code")
            if observation_state in {"fail", "unknown"} and reason_code not in allowed_reasons:
                errors.append(
                    f"health report dimension {dimension} observation {index} "
                    "needs an allowed reason_code"
                )
            if observation_state == "pass" and reason_code is not None:
                errors.append(
                    f"health report dimension {dimension} observation {index} "
                    "pass cannot carry reason_code"
                )
        if observation_states and state != expected_health_rollup(observation_states):
            errors.append(
                f"health report dimension {dimension} rollup does not match observations"
            )
        requirement = probe_requirements.get(dimension, {})
        minimum = requirement.get("minimum_observations")
        if not isinstance(minimum, int) or len(observations) < minimum:
            errors.append(f"health report dimension {dimension} lacks minimum observations")
        for evidence_class, required_count in requirement.get(
            "minimum_by_evidence_class", {}
        ).items():
            if evidence_counts.get(evidence_class, 0) < required_count:
                errors.append(
                    f"health report dimension {dimension} lacks {evidence_class} diversity"
                )
        minimum_groups = requirement.get("minimum_dependency_groups")
        if not isinstance(minimum_groups, int) or len(dependency_groups) < minimum_groups:
            errors.append(
                f"health report dimension {dimension} lacks independent dependency groups"
            )

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
    expected_generation_epoch: str | None = None,
    expected_subject_ref: str | None = None,
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
    if expected_generation_epoch is not None and report.get(
        "generation_epoch"
    ) != expected_generation_epoch:
        return "unknown"
    if expected_subject_ref is not None and report.get("subject_ref") != expected_subject_ref:
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
    report: dict[str, Any],
    profile: dict[str, Any],
    now: datetime,
    *,
    expected_gate_context: dict[str, str],
    expected_generation_epoch: str,
) -> bool:
    if profile.get("kind") != "recovery-preflight":
        return False
    if report.get("gate_context") != expected_gate_context:
        return False
    return (
        effective_health_outcome(
            report,
            now,
            expected_generation_epoch=expected_generation_epoch,
            expected_subject_ref=profile.get("subject_ref"),
            expected_profile_ref=profile.get("id"),
            expected_profile_revision=profile.get("revision"),
        )
        == "pass"
    )


def validate_health_profiles(
    document: dict[str, Any], contract: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "signalbox.health-profiles/v2":
        errors.append("health-profiles: unexpected schema")
    profiles = document.get("profiles")
    if not isinstance(profiles, list):
        return errors + ["health-profiles: profiles must be an array"]
    ids: set[str] = set()
    kind_counts: dict[str, int] = {}
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
        if kind not in contract_kinds:
            errors.append(f"health-profiles: unknown kind {kind}")
        else:
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
        missing_profile_fields = sorted(
            set(contract.get("required_profile_fields", [])) - set(profile)
        )
        if missing_profile_fields:
            errors.append(
                f"health-profiles: {profile_id} missing {missing_profile_fields}"
            )
        if not isinstance(profile.get("revision"), int) or profile.get("revision", 0) <= 0:
            errors.append(f"health-profiles: {profile_id} revision must be positive")
        if profile.get("observation_only") is not True:
            errors.append(f"health-profiles: {profile_id} must be observation-only")
        expected_dimensions = set(contract_kinds.get(kind, {}).get("required_dimensions", []))
        if set(profile.get("required_dimensions", [])) != expected_dimensions:
            errors.append(f"health-profiles: {profile_id} dimensions drifted")
        requirements = profile.get("probe_requirements")
        if not isinstance(requirements, dict) or set(requirements) != expected_dimensions:
            errors.append(f"health-profiles: {profile_id} probe requirements drifted")
        else:
            for dimension, requirement in requirements.items():
                if not isinstance(requirement.get("minimum_observations"), int) or requirement.get(
                    "minimum_observations", 0
                ) <= 0:
                    errors.append(
                        f"health-profiles: {profile_id} {dimension} minimum observations invalid"
                    )
                evidence_minimums = requirement.get("minimum_by_evidence_class")
                if not isinstance(evidence_minimums, dict) or not evidence_minimums:
                    errors.append(
                        f"health-profiles: {profile_id} {dimension} evidence minimums missing"
                    )
                elif any(
                    not isinstance(count, int) or count <= 0
                    for count in evidence_minimums.values()
                ):
                    errors.append(
                        f"health-profiles: {profile_id} {dimension} evidence minimum invalid"
                    )
                if not isinstance(requirement.get("minimum_dependency_groups"), int) or requirement.get(
                    "minimum_dependency_groups", 0
                ) <= 0:
                    errors.append(
                        f"health-profiles: {profile_id} {dimension} dependency minimum invalid"
                    )
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
        if kind in {"control-plane-operational", "recovery-preflight"} and not non_empty_string(
            profile.get("resource_threshold_owner")
        ):
            errors.append(f"health-profiles: {profile_id} lacks resource threshold owner")

        if kind in {"control-plane-operational", "lane-operational"}:
            interval = profile.get("run_interval_seconds")
            if not isinstance(interval, int) or interval <= 0:
                errors.append("health-profiles: operational interval must be positive")
            elif isinstance(max_age, int) and max_age < interval:
                errors.append("health-profiles: operational freshness must cover one interval")
        if kind == "lane-operational":
            transport = profile.get("probe_requirements", {}).get("transport", {})
            if transport.get("minimum_by_evidence_class") != {
                "transport-neutral": 1,
                "role-specific": 1,
            }:
                errors.append(
                    f"health-profiles: {profile_id} transport diversity drifted"
                )
            if transport.get("minimum_dependency_groups", 0) < 2:
                errors.append(
                    f"health-profiles: {profile_id} one provider cannot be sufficient"
                )
        if kind == "control-plane-operational":
            if set(profile.get("resource_observations", [])) != REQUIRED_RESOURCE_OBSERVATIONS:
                errors.append("health-profiles: operational resource observations are incomplete")
        if kind == "recovery-preflight" and profile.get("gate_context_required") is not True:
            errors.append("health-profiles: recovery-preflight must require gate context")
        if kind != "recovery-preflight" and "gate_context_required" in profile:
            errors.append(f"health-profiles: {profile_id} cannot require gate context")
    if kind_counts.get("recovery-preflight") != 1:
        errors.append("health-profiles: exactly one recovery-preflight profile is required")
    if kind_counts.get("control-plane-operational") != 1:
        errors.append("health-profiles: exactly one control-plane profile is required")
    if kind_counts.get("lane-operational", 0) < 1:
        errors.append("health-profiles: at least one lane profile is required")
    return errors


def validate_deployment(
    deployment: dict[str, Any], roles_document: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if deployment.get("schema") != "signalbox.reference-deployment/v2":
        errors.append("deployment: unexpected schema")
    if deployment.get("contract_revision") != 3:
        errors.append("deployment: unexpected revision")
    if deployment.get("deployment_id") != "mintie":
        errors.append("deployment: reference deployment must be mintie")
    if deployment.get("sample_only") is not True:
        errors.append("deployment: sample_only must be true")
    if deployment.get("private_live_bindings") != "external-and-absent":
        errors.append("deployment: private live bindings must be external and absent")
    if deployment.get("reference_platform") != {
        "vendor": "GL.iNet",
        "product": "Beryl 7",
        "model": "GL-MT3600BE",
        "normative": False,
    }:
        errors.append("deployment: Mintie reference platform binding drifted")
    if deployment.get("traffic_policy_ref") != "traffic-policy.json":
        errors.append("deployment: traffic policy reference drifted")
    if deployment.get("health_profiles_ref") != "health-profiles.json":
        errors.append("deployment: health profile reference drifted")
    if deployment.get("health_aggregate_ref") != "health-aggregate.json":
        errors.append("deployment: health aggregate reference drifted")
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
    expected_subjects = {
        "control-plane/mintie": ("control-plane", "mintie"),
        "role-binding/alder": ("egress-lane", "alder"),
        "role-binding/rowan": ("egress-lane", "rowan"),
        "role-binding/hearth": ("egress-lane", "hearth"),
        "gateway/alder-private": ("private-ingress-lane", "alder-private"),
        "gateway/rowan-private": ("private-ingress-lane", "rowan-private"),
    }
    subjects = deployment.get("health_subjects", {})
    if set(subjects) != set(expected_subjects):
        errors.append("deployment: health subject registry drifted")
    for subject_ref, (kind, binding_ref) in expected_subjects.items():
        subject = subjects.get(subject_ref, {})
        if subject.get("kind") != kind or subject.get("binding_ref") != binding_ref:
            errors.append(f"deployment: health subject {subject_ref} binding drifted")
    return errors


def validate_reference_traffic(
    traffic: dict[str, Any], deployment: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if traffic.get("schema") != "signalbox.reference-traffic-policy/v2":
        errors.append("reference-traffic: unexpected schema")
    if traffic.get("deployment_ref") != "deployment.json":
        errors.append("reference-traffic: deployment reference drifted")
    route_order = traffic.get("route_order", [])
    ids = [entry.get("id") for entry in route_order if isinstance(entry, dict)]
    if ids != REQUIRED_SAMPLE_ROUTE_ORDER:
        errors.append("reference-traffic: route order drifted")
    if "canonical-private-ingress" in ids:
        canonical_index = ids.index("canonical-private-ingress")
        for direct_id in ("private-direct", "approved-direct"):
            if direct_id in ids and canonical_index > ids.index(direct_id):
                errors.append(
                    f"reference-traffic: canonical private ingress must precede {direct_id}"
                )
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
    traffic: dict[str, Any],
    health_profiles: dict[str, Any],
    deployment: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    profiles = {
        profile.get("id"): profile
        for profile in health_profiles.get("profiles", [])
        if isinstance(profile, dict)
    }
    refs = traffic.get("health_profile_refs", {})
    recovery = profiles.get(refs.get("recovery_preflight"))
    if not recovery or recovery.get("kind") != "recovery-preflight":
        errors.append("reference-health: recovery_preflight must resolve")
    control = profiles.get(refs.get("control_plane"))
    if not control or control.get("kind") != "control-plane-operational":
        errors.append("reference-health: control_plane must resolve")
    expected_lanes = {
        "alder": ("role-binding/alder", "mintie-egress-alder"),
        "rowan": ("role-binding/rowan", "mintie-egress-rowan"),
        "hearth": ("role-binding/hearth", "mintie-egress-hearth"),
        "alder-private": ("gateway/alder-private", "mintie-private-alder"),
        "rowan-private": ("gateway/rowan-private", "mintie-private-rowan"),
    }
    lane_refs = refs.get("lanes", {})
    if set(lane_refs) != set(expected_lanes):
        errors.append("reference-health: lane profile reference set drifted")
    for lane_id, (subject_ref, expected_profile_id) in expected_lanes.items():
        profile = profiles.get(lane_refs.get(lane_id))
        if not profile or profile.get("id") != expected_profile_id:
            errors.append(f"reference-health: {lane_id} profile binding drifted")
            continue
        if profile.get("kind") != "lane-operational" or profile.get(
            "subject_ref"
        ) != subject_ref:
            errors.append(f"reference-health: {lane_id} profile subject drifted")
    profile_subjects = {profile.get("subject_ref") for profile in profiles.values()}
    if profile_subjects != set(deployment.get("health_subjects", {})):
        errors.append("reference-health: profiles do not cover every health subject")
    return errors


def validate_health_aggregate(
    root: Path,
    aggregate: dict[str, Any],
    deployment: dict[str, Any],
    health_profiles: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if aggregate.get("schema") != "signalbox.health-aggregate/v2":
        errors.append("health-aggregate: unexpected schema")
    if aggregate.get("deployment_ref") != "deployment.json":
        errors.append("health-aggregate: deployment reference drifted")
    if "outcome" in aggregate:
        errors.append("health-aggregate: top-level outcome is forbidden")
    try:
        assembled_at = parse_rfc3339(aggregate.get("assembled_at"))
    except (TypeError, ValueError) as exc:
        errors.append(f"health-aggregate: assembled_at {exc}")
        assembled_at = None
    try:
        evaluated_at = parse_rfc3339(aggregate.get("evaluated_at"))
    except (TypeError, ValueError) as exc:
        errors.append(f"health-aggregate: evaluated_at {exc}")
        evaluated_at = None
    if assembled_at is not None and evaluated_at != assembled_at:
        errors.append("health-aggregate: evaluated_at must equal assembled_at")
    members = aggregate.get("members")
    if not isinstance(members, list):
        return errors + ["health-aggregate: members must be an array"]
    profiles = {
        profile.get("id"): profile
        for profile in health_profiles.get("profiles", [])
        if isinstance(profile, dict)
    }
    expected_subjects = set(deployment.get("health_subjects", {}))
    seen_subjects: set[str] = set()
    outcome_counts = {"pass": 0, "fail": 0, "unknown": 0}
    sample_root = (root / "examples" / "mintie").resolve()
    for index, member in enumerate(members):
        if not isinstance(member, dict):
            errors.append(f"health-aggregate: member {index} must be an object")
            continue
        subject_ref = member.get("subject_ref")
        if subject_ref in seen_subjects:
            errors.append(f"health-aggregate: duplicate subject {subject_ref}")
        elif isinstance(subject_ref, str):
            seen_subjects.add(subject_ref)
        report_ref = member.get("report_ref")
        report_path = (sample_root / report_ref).resolve() if isinstance(report_ref, str) else None
        if report_path is None or sample_root not in report_path.parents or not report_path.is_file():
            errors.append(f"health-aggregate: member {index} report_ref does not resolve")
            continue
        try:
            report = load_json(report_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"health-aggregate: member {index} report load failed: {exc}")
            continue
        profile = profiles.get(report.get("profile_ref"))
        if profile and profile.get("kind") == "recovery-preflight":
            errors.append("health-aggregate: recovery-preflight member is forbidden")
        comparisons = {
            "subject_ref": report.get("subject_ref"),
            "report_id": report.get("id"),
            "profile_ref": report.get("profile_ref"),
            "profile_revision": report.get("profile_revision"),
            "producer_ref": report.get("producer_ref"),
            "generation_epoch": report.get("generation_epoch"),
            "generation": report.get("generation"),
        }
        for field, expected_value in comparisons.items():
            if member.get(field) != expected_value:
                errors.append(f"health-aggregate: member {index} {field} drifted")
        effective = (
            effective_health_outcome(report, evaluated_at)
            if evaluated_at is not None
            else "unknown"
        )
        if member.get("effective_outcome_at_assembly") != effective:
            errors.append(
                f"health-aggregate: member {index} assembly-time outcome drifted"
            )
        if effective in outcome_counts:
            outcome_counts[effective] += 1
    if seen_subjects != expected_subjects:
        errors.append("health-aggregate: members must preserve every deployment subject")
    expected_summary = {"member_count": len(members), **outcome_counts}
    if aggregate.get("summary") != expected_summary:
        errors.append("health-aggregate: summary does not match member outcomes")
    return errors


def validate_doc_pairs(root: Path, document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != "signalbox.docs-pairs/v2":
        errors.append("docs-pairs: unexpected schema")
    if document.get("contract_revision") != 3:
        errors.append("docs-pairs: unexpected revision")
    seen: set[str] = set()
    for pair in document.get("pairs", []):
        doc_id = pair.get("doc_id")
        if not doc_id or doc_id in seen:
            errors.append(f"docs-pairs: duplicate or missing doc_id {doc_id}")
        seen.add(doc_id)
        required_ids = pair.get("required_contract_ids", [])
        required_sections = pair.get("required_sections", [])
        if not required_sections:
            errors.append(f"docs-pairs: {doc_id} requires semantic section anchors")
        for language in ("zh-CN", "en"):
            relative = pair.get(language)
            path = root / relative if isinstance(relative, str) else None
            if path is None or not path.is_file():
                errors.append(f"docs-pairs: missing {language} file for {doc_id}: {relative}")
                continue
            text = path.read_text(encoding="utf-8")
            if f"doc_id: {doc_id}" not in text:
                errors.append(f"docs-pairs: {relative} has the wrong doc_id")
            sibling_language = "en" if language == "zh-CN" else "zh-CN"
            sibling_relative = pair.get(sibling_language)
            above_fold = "\n".join(text.splitlines()[:20])
            if relative.startswith("docs/human/") and (
                "authority: ../specification.md" not in above_fold
            ):
                errors.append(
                    f"docs-pairs: {relative} must name ../specification.md as authority"
                )
            if (
                not isinstance(sibling_relative, str)
                or Path(sibling_relative).name not in above_fold
            ):
                errors.append(
                    f"docs-pairs: {relative} must link its {sibling_language} sibling above fold"
                )
            for contract_id in required_ids:
                if contract_id not in text:
                    errors.append(f"docs-pairs: {relative} missing {contract_id}")
            for section_id in required_sections:
                marker = f'<a id="{section_id}"></a>'
                if text.count(marker) != 1:
                    errors.append(
                        f"docs-pairs: {relative} must contain one {section_id} anchor"
                    )
    return errors


def validate_catalog(root: Path, document: dict[str, Any]) -> list[str]:
    """Validate catalog ownership and instance routing without duplicating schemas."""

    errors: list[str] = []
    if document.get("schema") != "signalbox.contract-catalog/v1":
        errors.append("catalog: unexpected schema")
    if document.get("catalog_revision") != 1:
        errors.append("catalog: unexpected revision")
    entries = document.get("entries")
    if not isinstance(entries, list) or not entries:
        return errors + ["catalog: entries must be a non-empty array"]

    seen_ids: set[str] = set()
    required_fields = {
        "schema_id",
        "revision",
        "owner",
        "schema_path",
        "compatibility",
        "projection_dependencies",
        "instances",
    }
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"catalog: entry {index} must be an object")
            continue
        missing = sorted(required_fields - set(entry))
        if missing:
            errors.append(f"catalog: entry {index} missing {missing}")
        schema_id = entry.get("schema_id")
        if not non_empty_string(schema_id) or schema_id in seen_ids:
            errors.append(f"catalog: duplicate or missing schema_id {schema_id}")
        elif isinstance(schema_id, str):
            seen_ids.add(schema_id)
        if not isinstance(entry.get("revision"), int) or entry.get("revision", 0) <= 0:
            errors.append(f"catalog: {schema_id} revision must be positive")
        if entry.get("compatibility") != {
            "same_schema_id": "backward-compatible-only",
            "breaking_change": "new-schema-id-required",
        }:
            errors.append(f"catalog: {schema_id} compatibility policy drifted")

        for field in ("owner", "schema_path"):
            relative = entry.get(field)
            if not isinstance(relative, str):
                errors.append(f"catalog: {schema_id} {field} must be repo-relative")
                continue
            relative_path = Path(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                errors.append(f"catalog: {schema_id} {field} must be repo-relative")
            elif not (root / relative_path).exists():
                errors.append(f"catalog: {schema_id} {field} does not resolve")

        dependencies = entry.get("projection_dependencies")
        if not isinstance(dependencies, list):
            errors.append(f"catalog: {schema_id} projection_dependencies must be an array")
        else:
            for relative in dependencies:
                path = root / relative if isinstance(relative, str) else None
                if path is None or not path.exists():
                    errors.append(
                        f"catalog: {schema_id} projection dependency does not resolve: {relative}"
                    )

        instances = entry.get("instances")
        if not isinstance(instances, list):
            errors.append(f"catalog: {schema_id} instances must be an array")
            continue
        for instance in instances:
            if not isinstance(instance, dict) or set(instance) not in (
                {"path"},
                {"path", "pointer"},
                {"glob"},
            ):
                errors.append(f"catalog: {schema_id} has malformed instance selector")
                continue
            if "path" in instance:
                candidate = root / instance["path"]
                if not candidate.is_file():
                    errors.append(
                        f"catalog: {schema_id} instance does not resolve: {instance['path']}"
                    )
            else:
                matches = list(root.glob(instance["glob"]))
                if not matches:
                    errors.append(
                        f"catalog: {schema_id} glob has no instances: {instance['glob']}"
                    )

    expected_ids = {
        "signalbox.roles/v1",
        "signalbox.claims/v1",
        "signalbox.acceptance-record/v1",
        "signalbox.traffic-policy/v2",
        "signalbox.health-contract/v3",
        "signalbox.health-profile/v2",
        "signalbox.health-profiles/v2",
        "signalbox.health-report/v2",
        "signalbox.health-aggregate/v2",
        "signalbox.docs-pairs/v2",
        "signalbox.reference-deployment/v2",
        "signalbox.reference-traffic-policy/v2",
        "signalbox.contract-catalog/v1",
    }
    if seen_ids != expected_ids:
        errors.append(
            "catalog: schema registry drifted: "
            f"missing={sorted(expected_ids - seen_ids)} extra={sorted(seen_ids - expected_ids)}"
        )
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
        "README.zh-CN.md",
        "AGENTS.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        ".github/workflows/verify.yml",
        "docs/specification.md",
        "docs/programme-plan.md",
        "docs/current-state.md",
        "contracts/roles.json",
        "contracts/claims.json",
        "contracts/traffic-policy.json",
        "contracts/health-contract.json",
        "contracts/docs-pairs.json",
        "contracts/catalog.json",
        "schemas/catalog.schema.json",
        "examples/mintie/deployment.json",
        "examples/mintie/traffic-policy.json",
        "examples/mintie/health-profiles.json",
        "examples/mintie/health-aggregate.json",
        "examples/mintie/reports/control-plane-pass.json",
        "examples/mintie/reports/lane-alder-pass.json",
        "examples/mintie/reports/lane-rowan-pass.json",
        "examples/mintie/reports/lane-hearth-fail.json",
        "examples/mintie/reports/private-alder-pass.json",
        "examples/mintie/reports/private-rowan-unknown.json",
        "examples/mintie/reports/recovery-preflight-pass.json",
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
        catalog = load_json(root / "contracts/catalog.json")
        deployment = load_json(root / "examples/mintie/deployment.json")
        reference_traffic = load_json(root / "examples/mintie/traffic-policy.json")
        health_profiles = load_json(root / "examples/mintie/health-profiles.json")
        health_aggregate = load_json(root / "examples/mintie/health-aggregate.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"repository: JSON load failed: {exc}"]

    errors.extend(validate_roles(roles))
    errors.extend(validate_claims(claims))
    errors.extend(validate_traffic_policy(traffic, roles))
    errors.extend(validate_health_contract(health_contract))
    errors.extend(validate_catalog(root, catalog))
    errors.extend(validate_doc_pairs(root, docs_pairs))
    errors.extend(validate_deployment(deployment, roles))
    errors.extend(validate_reference_traffic(reference_traffic, deployment))
    errors.extend(validate_health_profiles(health_profiles, health_contract))
    errors.extend(
        validate_reference_health_links(reference_traffic, health_profiles, deployment)
    )
    errors.extend(
        validate_health_aggregate(root, health_aggregate, deployment, health_profiles)
    )

    profile_by_id = {
        profile.get("id"): profile
        for profile in health_profiles.get("profiles", [])
        if isinstance(profile, dict)
    }
    health_reports = [
        *sorted((root / "examples/mintie/reports").glob("*.json")),
        *sorted((root / "tests/fixtures").glob("health-*.json")),
    ]
    for fixture in health_reports:
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
        root / "README.zh-CN.md",
        root / "AGENTS.md",
        root / "SECURITY.md",
        root / "CONTRIBUTING.md",
        root / ".github",
        root / "contracts",
        root / "docs",
        root / "examples",
        root / "schemas",
    ]
    errors.extend(scan_portable_boundaries(root, portable_paths))
    errors.extend(
        validate_markdown_links(
            root,
            [
                root / "README.md",
                root / "README.zh-CN.md",
                root / "AGENTS.md",
                root / "SECURITY.md",
                root / "CONTRIBUTING.md",
                root / "docs",
                root / "examples",
                root / "schemas",
            ],
        )
    )

    specification = (root / "docs/specification.md").read_text(encoding="utf-8")
    for contract_id in (
        "SIG-01",
        "IDENT-02",
        "AUTH-03",
        "CLAIM-03",
        "ROUTE-02",
        "ROUTE-04",
        "ROUTE-06",
        "ENFORCE-01",
        "PRIVATE-01",
        "HEALTH-02",
        "HEALTH-07",
        "HEALTH-10",
        "HEALTH-14",
        "HEALTH-15",
        "DOC-05",
        "UPDATE-03",
        "ACCEPT-08",
    ):
        if contract_id not in specification:
            errors.append(f"specification: missing required contract ID {contract_id}")

    failure_catalog = (root / "docs/reference/failure-catalog.md").read_text(
        encoding="utf-8"
    )
    for failure_id in (
        "FAIL-001",
        "FAIL-002",
        "FAIL-003",
        "FAIL-004",
        "FAIL-005",
        "FAIL-006",
        "FAIL-007",
        "FAIL-008",
        "FAIL-009",
    ):
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
    report_count = len(list((ROOT / "examples/mintie/reports").glob("*.json")))
    fixture_count = len(list((ROOT / "tests/fixtures").glob("health-*.json")))
    print(
        "signalbox validation: PASS "
        f"({report_count} reference reports, {fixture_count} regression fixtures)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
