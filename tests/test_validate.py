import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts import validate as validator
from scripts import validate_schemas as schema_validator


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def current_identity(report: dict) -> dict:
    return {
        "producer_ref": report["producer_ref"],
        "subject_ref": report["subject_ref"],
        "profile_ref": report["profile_ref"],
        "profile_revision": report["profile_revision"],
        "generation_epoch": report["generation_epoch"],
        "generation": report["generation"],
        "report_id": report["id"],
        "attempt_id": report["attempt_id"],
    }


def copy_tracked_tree(destination: Path) -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.split(b"\0")
    for raw_relative in tracked:
        if not raw_relative:
            continue
        relative = Path(os.fsdecode(raw_relative))
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target.symlink_to(os.readlink(source))
        else:
            shutil.copy2(source, target)
    subprocess.run(["git", "init", "-q"], cwd=destination, check=True)
    subprocess.run(["git", "add", "--all"], cwd=destination, check=True)


class SignalboxValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.health_contract = load_json("contracts/health-contract.json")
        cls.profiles_document = load_json("examples/mintie/health-profiles.json")
        cls.profiles = {
            profile["id"]: profile for profile in cls.profiles_document["profiles"]
        }
        cls.deployment = load_json("examples/mintie/deployment.json")
        cls.reference_traffic = load_json("examples/mintie/traffic-policy.json")
        cls.aggregate = load_json("examples/mintie/health-aggregate.json")
        cls.health_report_schema = load_json("schemas/health-report.schema.json")
        cls.lane_pass = load_json("examples/mintie/reports/lane-alder-pass.json")
        cls.recovery_pass = load_json(
            "examples/mintie/reports/recovery-preflight-pass.json"
        )

    def test_repository_contracts_validate(self):
        self.assertEqual(validator.validate_repository(ROOT), [])

    def test_all_reference_health_reports_validate(self):
        report_paths = sorted((ROOT / "examples/mintie/reports").glob("*.json"))
        self.assertEqual(len(report_paths), 7)
        for path in report_paths:
            report = json.loads(path.read_text(encoding="utf-8"))
            profile = self.profiles[report["profile_ref"]]
            with self.subTest(path=path.name):
                self.assertEqual(
                    validator.validate_health_report(
                        report, self.health_contract, profile
                    ),
                    [],
                )

    def test_stale_pass_has_effective_unknown_outcome(self):
        report = load_json("tests/fixtures/health-stale-pass.json")
        now = datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc)
        evaluation = validator.evaluate_health_evidence(
            report,
            self.health_contract,
            self.profiles[report["profile_ref"]],
            self.health_report_schema,
            now,
            expected_current_identity=current_identity(report),
        )
        self.assertEqual(evaluation.effective_outcome, "unknown")
        self.assertIn("stale", evaluation.reason_codes)

    def test_non_current_generation_is_unknown_even_when_newer(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        expected = current_identity(self.lane_pass)
        expected["generation"] = self.lane_pass["generation"] - 1
        evaluation = validator.evaluate_health_evidence(
            self.lane_pass,
            self.health_contract,
            self.profiles["mintie-egress-alder"],
            self.health_report_schema,
            now,
            expected_current_identity=expected,
        )
        self.assertEqual(evaluation.effective_outcome, "unknown")
        self.assertFalse(evaluation.current_identity_match)
        self.assertIn("current-evidence-mismatch", evaluation.reason_codes)

    def test_unexpected_generation_epoch_is_unknown(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        expected = current_identity(self.lane_pass)
        expected["generation_epoch"] = "sample-epoch-beta"
        evaluation = validator.evaluate_health_evidence(
            self.lane_pass,
            self.health_contract,
            self.profiles["mintie-egress-alder"],
            self.health_report_schema,
            now,
            expected_current_identity=expected,
        )
        self.assertEqual(evaluation.effective_outcome, "unknown")
        self.assertFalse(evaluation.current_identity_match)

    def test_any_current_identity_mismatch_is_unknown(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        cases = (
            ("producer_ref", "reference/other-observer"),
            ("subject_ref", "role-binding/rowan"),
            ("profile_ref", "mintie-egress-rowan"),
            ("profile_revision", 3),
            ("generation", 102),
            ("report_id", "report-other"),
            ("attempt_id", "attempt-other"),
        )
        for field, replacement in cases:
            with self.subTest(field=field):
                expected = current_identity(self.lane_pass)
                expected[field] = replacement
                evaluation = validator.evaluate_health_evidence(
                    self.lane_pass,
                    self.health_contract,
                    self.profiles["mintie-egress-alder"],
                    self.health_report_schema,
                    now,
                    expected_current_identity=expected,
                )
                self.assertEqual(evaluation.effective_outcome, "unknown")
                self.assertFalse(evaluation.current_identity_match)

    def test_unpublished_pass_is_not_yet_effective(self):
        now = datetime(2026, 8, 31, 10, 0, 8, 500000, tzinfo=timezone.utc)
        evaluation = validator.evaluate_health_evidence(
            self.recovery_pass,
            self.health_contract,
            self.profiles["mintie-recovery-preflight"],
            self.health_report_schema,
            now,
            expected_current_identity=current_identity(self.recovery_pass),
        )
        self.assertEqual(evaluation.effective_outcome, "unknown")
        self.assertIn("evidence-not-yet-published", evaluation.reason_codes)

    def test_structurally_invalid_pass_is_unknown(self):
        report = copy.deepcopy(self.recovery_pass)
        report["generation"] = True
        expected = current_identity(self.recovery_pass)
        expected["generation"] = True
        evaluation = validator.evaluate_health_evidence(
            report,
            self.health_contract,
            self.profiles["mintie-recovery-preflight"],
            self.health_report_schema,
            datetime(2026, 8, 31, 10, 1, tzinfo=timezone.utc),
            expected_current_identity=expected,
        )
        self.assertFalse(evaluation.structurally_valid)
        self.assertEqual(evaluation.effective_outcome, "unknown")
        self.assertIn("malformed-evidence", evaluation.reason_codes)

    def test_non_object_health_evidence_is_unknown_instead_of_crashing(self):
        evaluation = validator.evaluate_health_evidence(
            [],
            self.health_contract,
            self.profiles["mintie-recovery-preflight"],
            self.health_report_schema,
            datetime(2026, 8, 31, 10, 1, tzinfo=timezone.utc),
            expected_current_identity=current_identity(self.recovery_pass),
        )
        self.assertFalse(evaluation.structurally_valid)
        self.assertFalse(evaluation.semantically_valid)
        self.assertEqual(evaluation.effective_outcome, "unknown")
        self.assertIn("malformed-evidence", evaluation.reason_codes)
        self.assertFalse(
            validator.restore_gate_allows(
                [],
                self.health_contract,
                self.profiles["mintie-recovery-preflight"],
                self.health_report_schema,
                datetime(2026, 8, 31, 10, 1, tzinfo=timezone.utc),
                expected_gate_context=self.recovery_pass["gate_context"],
                expected_current_identity=current_identity(self.recovery_pass),
            )
        )

    def test_report_validity_cannot_exceed_profile_freshness(self):
        report = copy.deepcopy(self.lane_pass)
        report["valid_until"] = "2026-08-31T10:20:07Z"
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("profile freshness" in error for error in errors), errors)

    def test_report_subject_must_match_profile_subject(self):
        report = copy.deepcopy(self.lane_pass)
        report["subject_ref"] = "role-binding/rowan"
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("subject_ref" in error for error in errors), errors)

    def test_dimension_rollup_must_match_observations(self):
        report = copy.deepcopy(self.lane_pass)
        report["dimensions"]["transport"]["observations"][1]["state"] = "fail"
        report["dimensions"]["transport"]["observations"][1][
            "reason_code"
        ] = "unreachable"
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("dimension transport rollup" in error for error in errors), errors)

    def test_report_rollup_must_match_dimensions(self):
        report = copy.deepcopy(self.lane_pass)
        report["dimensions"]["dns"]["state"] = "unknown"
        report["dimensions"]["dns"]["observations"][0]["state"] = "unknown"
        report["dimensions"]["dns"]["observations"][0][
            "reason_code"
        ] = "query-failed"
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("report rollup" in error for error in errors), errors)

    def test_health_report_requires_exact_profile_dimensions(self):
        report = copy.deepcopy(self.lane_pass)
        del report["dimensions"]["dns"]
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("dimensions mismatch" in error for error in errors), errors)

    def test_health_report_rejects_forbidden_durable_keys(self):
        report = copy.deepcopy(self.lane_pass)
        report["dimensions"]["transport"]["observations"][0]["token"] = "redacted"
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("forbidden durable key token" in error for error in errors), errors)

    def test_lane_transport_requires_neutral_and_role_specific_evidence(self):
        report = copy.deepcopy(self.lane_pass)
        report["dimensions"]["transport"]["observations"][0][
            "evidence_class"
        ] = "role-specific"
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("transport-neutral diversity" in error for error in errors), errors)

    def test_lane_transport_requires_independent_dependency_groups(self):
        report = copy.deepcopy(self.lane_pass)
        report["dimensions"]["transport"]["observations"][0][
            "dependency_group"
        ] = "alder-egress-policy"
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("independent dependency groups" in error for error in errors), errors)

    def test_failed_observation_requires_reason_code(self):
        report = copy.deepcopy(self.lane_pass)
        report["dimensions"]["transport"]["state"] = "fail"
        report["dimensions"]["transport"]["observations"][1]["state"] = "fail"
        report["outcome"] = "fail"
        errors = validator.validate_health_report(
            report, self.health_contract, self.profiles["mintie-egress-alder"]
        )
        self.assertTrue(any("allowed reason_code" in error for error in errors), errors)

    def test_recovery_pass_opens_only_its_exact_restore_gate(self):
        profile = self.profiles["mintie-recovery-preflight"]
        context = copy.deepcopy(self.recovery_pass["gate_context"])
        now = datetime(2026, 8, 31, 10, 1, tzinfo=timezone.utc)
        self.assertTrue(
            validator.restore_gate_allows(
                self.recovery_pass,
                self.health_contract,
                profile,
                self.health_report_schema,
                now,
                expected_gate_context=context,
                expected_current_identity=current_identity(self.recovery_pass),
            )
        )

        for field, replacement in (
            ("operation_ref", "operation/sample-restore-002"),
            (
                "desired_state_digest",
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            ),
            ("observed_runtime_generation", "runtime/sample-042"),
            ("restore_scope_ref", "control-plane/other"),
        ):
            mismatched = copy.deepcopy(context)
            mismatched[field] = replacement
            with self.subTest(field=field):
                self.assertFalse(
                    validator.restore_gate_allows(
                        self.recovery_pass,
                        self.health_contract,
                        profile,
                        self.health_report_schema,
                        now,
                        expected_gate_context=mismatched,
                        expected_current_identity=current_identity(self.recovery_pass),
                    )
                )

    def test_recovery_gate_rejects_non_current_or_invalid_pass(self):
        profile = self.profiles["mintie-recovery-preflight"]
        now = datetime(2026, 8, 31, 10, 1, tzinfo=timezone.utc)
        cases = []
        wrong_epoch = current_identity(self.recovery_pass)
        wrong_epoch["generation_epoch"] = "sample-epoch-beta"
        cases.append((self.recovery_pass, wrong_epoch))
        wrong_producer = current_identity(self.recovery_pass)
        wrong_producer["producer_ref"] = "reference/other-observer"
        cases.append((self.recovery_pass, wrong_producer))
        malformed = copy.deepcopy(self.recovery_pass)
        del malformed["dimensions"]["resources"]
        cases.append((malformed, current_identity(self.recovery_pass)))
        for report, expected in cases:
            with self.subTest(expected=expected):
                self.assertFalse(
                    validator.restore_gate_allows(
                        report,
                        self.health_contract,
                        profile,
                        self.health_report_schema,
                        now,
                        expected_gate_context=self.recovery_pass["gate_context"],
                        expected_current_identity=expected,
                    )
                )

    def test_recovery_gate_rejects_report_before_publication(self):
        self.assertFalse(
            validator.restore_gate_allows(
                self.recovery_pass,
                self.health_contract,
                self.profiles["mintie-recovery-preflight"],
                self.health_report_schema,
                datetime(2026, 8, 31, 10, 0, 8, 500000, tzinfo=timezone.utc),
                expected_gate_context=self.recovery_pass["gate_context"],
                expected_current_identity=current_identity(self.recovery_pass),
            )
        )

    def test_operational_pass_cannot_open_restore_gate(self):
        now = datetime(2026, 8, 31, 10, 1, tzinfo=timezone.utc)
        self.assertFalse(
            validator.restore_gate_allows(
                self.lane_pass,
                self.health_contract,
                self.profiles["mintie-egress-alder"],
                self.health_report_schema,
                now,
                expected_gate_context={},
                expected_current_identity=current_identity(self.lane_pass),
            )
        )

    def test_member_preserving_health_aggregate_validates(self):
        self.assertEqual(
            validator.validate_health_aggregate(
                ROOT,
                self.aggregate,
                self.deployment,
                self.profiles_document,
                self.health_contract,
                self.health_report_schema,
            ),
            [],
        )

    def test_health_aggregate_forbids_top_level_outcome(self):
        aggregate = copy.deepcopy(self.aggregate)
        aggregate["outcome"] = "unknown"
        errors = validator.validate_health_aggregate(
            ROOT,
            aggregate,
            self.deployment,
            self.profiles_document,
            self.health_contract,
            self.health_report_schema,
        )
        self.assertTrue(any("top-level outcome" in error for error in errors), errors)

    def test_health_aggregate_must_preserve_every_subject(self):
        aggregate = copy.deepcopy(self.aggregate)
        aggregate["members"].pop()
        errors = validator.validate_health_aggregate(
            ROOT,
            aggregate,
            self.deployment,
            self.profiles_document,
            self.health_contract,
            self.health_report_schema,
        )
        self.assertTrue(any("every deployment subject" in error for error in errors), errors)

    def test_health_aggregate_member_cannot_drift_from_report(self):
        aggregate = copy.deepcopy(self.aggregate)
        aggregate["members"][0]["generation"] += 1
        errors = validator.validate_health_aggregate(
            ROOT,
            aggregate,
            self.deployment,
            self.profiles_document,
            self.health_contract,
            self.health_report_schema,
        )
        self.assertTrue(any("generation drifted" in error for error in errors), errors)

    def test_health_aggregate_evaluation_time_is_assembly_time(self):
        aggregate = copy.deepcopy(self.aggregate)
        aggregate["evaluated_at"] = "2026-08-31T10:00:11Z"
        errors = validator.validate_health_aggregate(
            ROOT,
            aggregate,
            self.deployment,
            self.profiles_document,
            self.health_contract,
            self.health_report_schema,
        )
        self.assertTrue(
            any("evaluated_at must equal assembled_at" in error for error in errors),
            errors,
        )

    def test_health_aggregate_rejects_legacy_member_outcome_field(self):
        aggregate = copy.deepcopy(self.aggregate)
        member = aggregate["members"][0]
        member["effective_outcome"] = member.pop("effective_outcome_at_assembly")
        errors = validator.validate_health_aggregate(
            ROOT,
            aggregate,
            self.deployment,
            self.profiles_document,
            self.health_contract,
            self.health_report_schema,
        )
        self.assertTrue(
            any("assembly-time outcome drifted" in error for error in errors),
            errors,
        )

    def test_health_aggregate_rejects_structurally_invalid_member_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample_root = root / "examples" / "mintie"
            shutil.copytree(ROOT / "examples" / "mintie", sample_root)
            report_path = sample_root / "reports" / "control-plane-pass.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["generation"] = True
            report_path.write_text(json.dumps(report), encoding="utf-8")
            errors = validator.validate_health_aggregate(
                root,
                self.aggregate,
                self.deployment,
                self.profiles_document,
                self.health_contract,
                self.health_report_schema,
            )
        self.assertTrue(any("not canonically valid" in error for error in errors), errors)

    def test_health_aggregate_rejects_non_object_member_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample_root = root / "examples" / "mintie"
            shutil.copytree(ROOT / "examples" / "mintie", sample_root)
            report_path = sample_root / "reports" / "control-plane-pass.json"
            report_path.write_text("[]", encoding="utf-8")
            errors = validator.validate_health_aggregate(
                root,
                self.aggregate,
                self.deployment,
                self.profiles_document,
                self.health_contract,
                self.health_report_schema,
            )
        self.assertTrue(any("not canonically valid" in error for error in errors), errors)

    def test_repository_rejects_non_object_health_report_without_crashing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_tracked_tree(root)
            report_path = (
                root / "examples" / "mintie" / "reports" / "control-plane-pass.json"
            )
            report_path.write_text("[]", encoding="utf-8")
            subprocess.run(
                ["git", "add", "examples/mintie/reports/control-plane-pass.json"],
                cwd=root,
                check=True,
            )
            errors = validator.validate_repository(root)
        self.assertTrue(any("control-plane-pass.json" in error for error in errors), errors)

    def test_private_ingress_precedence_regression_fixtures(self):
        by_id = {
            route["id"]: route for route in self.reference_traffic["route_order"]
        }
        for path in sorted((ROOT / "tests/fixtures/invalid").glob("*.json")):
            fixture = json.loads(path.read_text(encoding="utf-8"))
            traffic = copy.deepcopy(self.reference_traffic)
            traffic["route_order"] = [by_id[route_id] for route_id in fixture["route_ids"]]
            errors = validator.validate_reference_traffic(traffic, self.deployment)
            with self.subTest(path=path.name):
                self.assertTrue(
                    any(fixture["expected_error"] in error for error in errors),
                    errors,
                )

    def test_traffic_contract_rejects_direct_failure_fallback(self):
        traffic = load_json("contracts/traffic-policy.json")
        roles = load_json("contracts/roles.json")
        traffic["direct_action"]["allowed_on_proxy_failure"] = True
        errors = validator.validate_traffic_policy(traffic, roles)
        self.assertTrue(any("DIRECT" in error for error in errors), errors)

    def test_role_reference_must_resolve(self):
        traffic = load_json("contracts/traffic-policy.json")
        roles = load_json("contracts/roles.json")
        traffic["default_proxy_required"]["selection"]["role"] = "missing-role"
        errors = validator.validate_traffic_policy(traffic, roles)
        self.assertTrue(any("missing-role" in error for error in errors), errors)

    def test_protected_application_structurally_rejects_fallback(self):
        traffic = load_json("contracts/traffic-policy.json")
        roles = load_json("contracts/roles.json")
        traffic["protected_application"]["fallback_roles"] = []
        errors = validator.validate_traffic_policy(traffic, roles)
        self.assertTrue(any("structurally forbids" in error for error in errors), errors)

    def test_acceptance_record_cannot_upgrade_realization(self):
        claims = load_json("contracts/claims.json")
        claims["acceptance_record"]["can_upgrade_realization_stage"] = True
        errors = validator.validate_claims(claims)
        self.assertTrue(any("cannot upgrade" in error for error in errors), errors)

    def test_health_profiles_require_bounded_entry_retention(self):
        profiles = copy.deepcopy(self.profiles_document)
        profiles["profiles"][0]["retention"]["max_entries"] = 0
        errors = validator.validate_health_profiles(profiles, self.health_contract)
        self.assertTrue(any("max_entries" in error for error in errors), errors)

    def test_health_contract_safety_field_mutation_matrix(self):
        safety_roots = (
            ("schema",),
            ("contract_revision",),
            ("transient_outcomes",),
            ("terminal_outcomes",),
            ("rollup_precedence",),
            ("profile_kinds",),
            ("required_profile_fields",),
            ("required_report_fields",),
            ("required_dimension_fields",),
            ("required_observation_fields",),
            ("evidence_evaluation",),
            ("generation",),
            ("freshness",),
            ("recovery_gate",),
            ("deployment_aggregate",),
            ("publication",),
            ("query_failure_outcome",),
            ("observation_only",),
            ("retention_policy_required_fields",),
            ("forbidden_durable_keys",),
            ("reason_codes",),
        )

        def leaf_paths(value, prefix):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield from leaf_paths(child, (*prefix, key))
            else:
                yield prefix

        paths = []
        for root_path in safety_roots:
            value = self.health_contract
            for key in root_path:
                value = value[key]
            paths.extend(leaf_paths(value, root_path))

        for path in paths:
            with self.subTest(path=path):
                contract = copy.deepcopy(self.health_contract)
                target = contract
                for key in path[:-1]:
                    target = target[key]
                original = target[path[-1]]
                if isinstance(original, bool):
                    replacement = not original
                elif isinstance(original, int):
                    replacement = original + 1
                elif isinstance(original, str):
                    replacement = "mutated-contract-value"
                elif isinstance(original, list):
                    replacement = []
                else:
                    self.fail(f"unsupported contract leaf type at {path}")
                target[path[-1]] = replacement
                self.assertTrue(
                    validator.validate_health_contract(contract),
                    f"mutation was not rejected: {path}",
                )

    def test_reference_profiles_cover_deployment_subjects(self):
        profiles = copy.deepcopy(self.profiles_document)
        profiles["profiles"] = [
            profile
            for profile in profiles["profiles"]
            if profile["id"] != "mintie-private-rowan"
        ]
        errors = validator.validate_reference_health_links(
            self.reference_traffic,
            profiles,
            self.deployment,
            self.health_contract,
        )
        self.assertTrue(any("rowan-private" in error for error in errors), errors)

    def test_recovery_profile_must_bind_a_control_plane_subject(self):
        profiles = copy.deepcopy(self.profiles_document)
        profiles["profiles"][0]["subject_ref"] = "role-binding/alder"
        errors = validator.validate_reference_health_links(
            self.reference_traffic,
            profiles,
            self.deployment,
            self.health_contract,
        )
        self.assertTrue(any("recovery-preflight" in error for error in errors), errors)
        self.assertTrue(any("control-plane/mintie" in error for error in errors), errors)

    def test_profile_cardinality_rejects_duplicate_lane_profile(self):
        profiles = copy.deepcopy(self.profiles_document)
        duplicate = copy.deepcopy(self.profiles["mintie-egress-alder"])
        duplicate["id"] = "mintie-egress-alder-duplicate"
        profiles["profiles"].append(duplicate)
        errors = validator.validate_reference_health_links(
            self.reference_traffic,
            profiles,
            self.deployment,
            self.health_contract,
        )
        self.assertTrue(any("role-binding/alder" in error for error in errors), errors)

    def test_reference_route_action_mutation_matrix(self):
        mutations = {
            "protocol-observation": "noop",
            "dns-capture": "noop",
            "canonical-private-ingress": "noop",
            "protected-udp-policy": "noop",
            "protected-application": "noop",
            "private-direct": "route",
            "approved-direct": "route",
            "default-proxy-required": "noop",
        }
        for route_id, action in mutations.items():
            with self.subTest(route_id=route_id):
                traffic = copy.deepcopy(self.reference_traffic)
                route = next(
                    item for item in traffic["route_order"] if item["id"] == route_id
                )
                route["action"] = action
                errors = validator.validate_reference_traffic(
                    traffic, self.deployment
                )
                self.assertTrue(
                    any(route_id in error and "action" in error for error in errors),
                    errors,
                )

    def test_reference_route_grammar_rejects_fields_from_another_route(self):
        traffic = copy.deepcopy(self.reference_traffic)
        traffic["route_order"][0]["selection"] = {
            "mode": "pinned",
            "role_binding_ref": "alder",
        }
        errors = validator.validate_reference_traffic(traffic, self.deployment)
        self.assertTrue(any("protocol-observation" in error for error in errors), errors)

    def test_boundary_scan_rejects_machine_local_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "docs").mkdir()
            (root / "docs/bad.md").write_text(
                "local authority lives under /" + "Users/example/private\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/bad.md"], cwd=root, check=True)
            errors = validator.scan_tracked_source_boundaries(root)
        self.assertTrue(any("machine-local path" in error for error in errors), errors)

    def test_repository_entrypoint_scans_tracked_python_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_tracked_tree(root)
            probe = root / "scripts" / "tracked-boundary-probe.py"
            probe.write_text(
                'AUTHORITY_PATH = "/' + 'Users/example/private"\n',
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", "scripts/tracked-boundary-probe.py"],
                cwd=root,
                check=True,
            )
            errors = validator.validate_repository(root)
        self.assertTrue(
            any(
                "scripts/tracked-boundary-probe.py" in error
                and "machine-local path" in error
                for error in errors
            ),
            errors,
        )

    def test_repository_entrypoint_rejects_tracked_python_token_assignment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_tracked_tree(root)
            relative = "scripts/tracked-token-probe.py"
            probe = root / relative
            probe.write_text("to" + 'ken = "real-value"\n', encoding="utf-8")
            subprocess.run(["git", "add", relative], cwd=root, check=True)
            errors = validator.validate_repository(root)
        self.assertTrue(
            any(
                relative in error and "credential assignment" in error
                for error in errors
            ),
            errors,
        )

    def test_repository_entrypoint_rejects_tracked_json_secret_assignment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            copy_tracked_tree(root)
            relative = "examples/tracked-secret-probe.json"
            probe = root / relative
            probe.write_text(
                json.dumps({"se" + "cret": "real-value"}),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", relative], cwd=root, check=True)
            errors = validator.validate_repository(root)
        self.assertTrue(
            any(
                relative in error and "credential assignment" in error
                for error in errors
            ),
            errors,
        )

    def test_tracked_source_scanner_covers_network_identity_and_secret_literals(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            cases = {
                "ipv4.txt": "198" + ".51.100.42\n",
                "ipv6.txt": "fd00:" + ":42\n",
                "mac.txt": "aa" + ":bb:cc:dd:ee:ff\n",
                "secret.ini": "client_" + "secret = exposed-value\n",
                "api-token.ini": "api_" + "token = exposed-value\n",
                "access-token.ini": "access_" + "token = exposed-value\n",
                "refresh-token.ini": "refresh_" + "token = exposed-value\n",
                "userinfo.txt": "https://" + "sample:password@example.com/\n",
                "windows.txt": "C:" + "\\Users\\example\\private.txt\n",
                "unix-root.txt": "/" + "root/private.txt\n",
            }
            for relative, content in cases.items():
                (root / relative).write_text(content, encoding="utf-8")
            (root / "binary.bin").write_bytes(
                b"\x00binary /" + b"Users/example/private"
            )
            subprocess.run(["git", "add", "--all"], cwd=root, check=True)
            errors = validator.scan_tracked_source_boundaries(root)
        for rule in (
            "IP address literal",
            "MAC address literal",
            "credential assignment",
            "URL userinfo",
            "machine-local path",
        ):
            with self.subTest(rule=rule):
                self.assertTrue(any(rule in error for error in errors), errors)
        for relative in (
            "secret.ini",
            "api-token.ini",
            "access-token.ini",
            "refresh-token.ini",
        ):
            with self.subTest(relative=relative):
                self.assertTrue(
                    any(
                        relative in error and "credential assignment" in error
                        for error in errors
                    ),
                    errors,
                )
        self.assertFalse(any("binary.bin" in error for error in errors), errors)

    def test_tracked_source_scanner_rejects_symlink_escape_without_following_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            outside = Path(temp_dir) / "outside.txt"
            outside.write_text("private material", encoding="utf-8")
            (root / "escape.txt").symlink_to(outside)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "escape.txt"], cwd=root, check=True)
            errors = validator.scan_tracked_source_boundaries(root)
        self.assertTrue(any("symlink escapes repository" in error for error in errors), errors)

    def test_catalog_is_bootstrap_validated_before_paths_are_consumed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / "repo"
            (root / "contracts").mkdir(parents=True)
            (root / "schemas").mkdir()
            shutil.copy2(
                ROOT / "schemas/catalog.schema.json",
                root / "schemas/catalog.schema.json",
            )
            external_schema = base / "external.schema.json"
            external_schema.write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "urn:signalbox:test",
                        "type": "object",
                    }
                ),
                encoding="utf-8",
            )
            (root / "instance.json").write_text(
                json.dumps({"schema": "signalbox.test/v1"}), encoding="utf-8"
            )
            catalog = {
                "schema": "signalbox.contract-catalog/v1",
                "catalog_revision": 1,
                "entries": [
                    {
                        "schema_id": "signalbox.test/v1",
                        "revision": 1,
                        "owner": "contracts/catalog.json",
                        "schema_path": str(external_schema),
                        "compatibility": {
                            "same_schema_id": "backward-compatible-only",
                            "breaking_change": "new-schema-id-required",
                        },
                        "projection_dependencies": [],
                        "instances": [{"path": "instance.json"}],
                    }
                ],
            }
            (root / "contracts/catalog.json").write_text(
                json.dumps(catalog), encoding="utf-8"
            )
            errors, validated = schema_validator.validate_cataloged_instances(root)
        self.assertEqual(validated, 0)
        self.assertTrue(any("catalog" in error and "schema_path" in error for error in errors), errors)

    def test_catalog_semantics_reject_external_projection_dependency(self):
        catalog = load_json("contracts/catalog.json")
        catalog["entries"][0]["projection_dependencies"] = [
            str(Path("/") / "etc" / "hosts")
        ]
        errors = validator.validate_catalog(ROOT, catalog)
        self.assertTrue(any("projection dependency" in error for error in errors), errors)

    def test_docs_pair_schema_requires_repository_relative_paths(self):
        schema = load_json("schemas/docs-pairs.schema.json")
        document = {
            "schema": schema["properties"]["schema"]["const"],
            "contract_revision": 4,
            "pairs": [
                {
                    "doc_id": "sample",
                    "zh-CN": "/" + "Users/example/zh.md",
                    "en": "en.md",
                    "required_contract_ids": ["SIG-01"],
                    "required_sections": ["meaning"],
                }
            ],
        }
        errors = list(Draft202012Validator(schema).iter_errors(document))
        self.assertTrue(errors)

    def test_markdown_links_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / "repo"
            docs = root / "docs"
            docs.mkdir(parents=True)
            outside = base / "outside.md"
            outside.write_text("private", encoding="utf-8")
            source = docs / "guide.md"
            source.write_text("[outside](../../outside.md)\n", encoding="utf-8")
            errors = validator.validate_markdown_links(root, [source])
        self.assertTrue(any("escapes repository" in error for error in errors), errors)

    def test_doc_pair_requires_contract_ids_in_both_languages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "zh.md").write_text(
                "doc_id: sample\n[English](en.md)\nSIG-01\n<a id=\"meaning\"></a>\n",
                encoding="utf-8",
            )
            (root / "en.md").write_text(
                "doc_id: sample\n[Chinese](zh.md)\nmissing\n<a id=\"meaning\"></a>\n",
                encoding="utf-8",
            )
            pairs = {
                "schema": "signalbox.docs-pairs/v3",
                "contract_revision": 4,
                "pairs": [
                    {
                        "doc_id": "sample",
                        "zh-CN": "zh.md",
                        "en": "en.md",
                        "required_contract_ids": ["SIG-01"],
                        "required_sections": ["meaning"],
                    }
                ],
            }
            errors = validator.validate_doc_pairs(root, pairs)
        self.assertTrue(any("SIG-01" in error and "en.md" in error for error in errors))

    def test_doc_pair_requires_each_semantic_anchor_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for language in ("zh", "en"):
                sibling = "en.md" if language == "zh" else "zh.md"
                (root / f"{language}.md").write_text(
                    f"doc_id: sample\n[sibling]({sibling})\nSIG-01\n",
                    encoding="utf-8",
                )
            pairs = {
                "schema": "signalbox.docs-pairs/v3",
                "contract_revision": 4,
                "pairs": [
                    {
                        "doc_id": "sample",
                        "zh-CN": "zh.md",
                        "en": "en.md",
                        "required_contract_ids": ["SIG-01"],
                        "required_sections": ["meaning"],
                    }
                ],
            }
            errors = validator.validate_doc_pairs(root, pairs)
        self.assertEqual(
            sum("one meaning anchor" in error for error in errors),
            2,
            errors,
        )

    def test_doc_pair_requires_visible_sibling_links(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "zh.md").write_text(
                "doc_id: sample\nSIG-01\n<a id=\"meaning\"></a>\n",
                encoding="utf-8",
            )
            (root / "en.md").write_text(
                "doc_id: sample\n[Chinese](zh.md)\nSIG-01\n<a id=\"meaning\"></a>\n",
                encoding="utf-8",
            )
            pairs = {
                "schema": "signalbox.docs-pairs/v3",
                "contract_revision": 4,
                "pairs": [
                    {
                        "doc_id": "sample",
                        "zh-CN": "zh.md",
                        "en": "en.md",
                        "required_contract_ids": ["SIG-01"],
                        "required_sections": ["meaning"],
                    }
                ],
            }
            errors = validator.validate_doc_pairs(root, pairs)
        self.assertTrue(
            any("zh.md must link its en sibling above fold" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
