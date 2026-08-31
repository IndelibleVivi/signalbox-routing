import copy
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "signalbox_validate", ROOT / "scripts" / "validate.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


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
        self.assertEqual(validator.effective_health_outcome(report, now), "unknown")

    def test_generation_regression_is_unknown_within_scope(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        self.assertEqual(
            validator.effective_health_outcome(
                self.lane_pass,
                now,
                minimum_generation=102,
                expected_generation_epoch="sample-epoch-alpha",
                expected_subject_ref="role-binding/alder",
                expected_profile_ref="mintie-egress-alder",
            ),
            "unknown",
        )

    def test_unexpected_generation_epoch_is_unknown(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        self.assertEqual(
            validator.effective_health_outcome(
                self.lane_pass,
                now,
                expected_generation_epoch="sample-epoch-beta",
            ),
            "unknown",
        )

    def test_subject_or_profile_mismatch_is_unknown(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        cases = (
            {"expected_subject_ref": "role-binding/rowan"},
            {"expected_profile_ref": "mintie-egress-rowan"},
            {"expected_profile_revision": 3},
        )
        for expectation in cases:
            with self.subTest(expectation=expectation):
                self.assertEqual(
                    validator.effective_health_outcome(
                        self.lane_pass, now, **expectation
                    ),
                    "unknown",
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
                profile,
                now,
                expected_gate_context=context,
                expected_generation_epoch="sample-epoch-alpha",
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
                        profile,
                        now,
                        expected_gate_context=mismatched,
                        expected_generation_epoch="sample-epoch-alpha",
                    )
                )

    def test_recovery_gate_rejects_unexpected_epoch(self):
        profile = self.profiles["mintie-recovery-preflight"]
        now = datetime(2026, 8, 31, 10, 1, tzinfo=timezone.utc)
        self.assertFalse(
            validator.restore_gate_allows(
                self.recovery_pass,
                profile,
                now,
                expected_gate_context=self.recovery_pass["gate_context"],
                expected_generation_epoch="sample-epoch-beta",
            )
        )

    def test_operational_pass_cannot_open_restore_gate(self):
        now = datetime(2026, 8, 31, 10, 1, tzinfo=timezone.utc)
        self.assertFalse(
            validator.restore_gate_allows(
                self.lane_pass,
                self.profiles["mintie-egress-alder"],
                now,
                expected_gate_context={},
                expected_generation_epoch="sample-epoch-alpha",
            )
        )

    def test_member_preserving_health_aggregate_validates(self):
        self.assertEqual(
            validator.validate_health_aggregate(
                ROOT, self.aggregate, self.deployment, self.profiles_document
            ),
            [],
        )

    def test_health_aggregate_forbids_top_level_outcome(self):
        aggregate = copy.deepcopy(self.aggregate)
        aggregate["outcome"] = "unknown"
        errors = validator.validate_health_aggregate(
            ROOT, aggregate, self.deployment, self.profiles_document
        )
        self.assertTrue(any("top-level outcome" in error for error in errors), errors)

    def test_health_aggregate_must_preserve_every_subject(self):
        aggregate = copy.deepcopy(self.aggregate)
        aggregate["members"].pop()
        errors = validator.validate_health_aggregate(
            ROOT, aggregate, self.deployment, self.profiles_document
        )
        self.assertTrue(any("every deployment subject" in error for error in errors), errors)

    def test_health_aggregate_member_cannot_drift_from_report(self):
        aggregate = copy.deepcopy(self.aggregate)
        aggregate["members"][0]["generation"] += 1
        errors = validator.validate_health_aggregate(
            ROOT, aggregate, self.deployment, self.profiles_document
        )
        self.assertTrue(any("generation drifted" in error for error in errors), errors)

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

    def test_reference_profiles_cover_deployment_subjects(self):
        profiles = copy.deepcopy(self.profiles_document)
        profiles["profiles"] = [
            profile
            for profile in profiles["profiles"]
            if profile["id"] != "mintie-private-rowan"
        ]
        errors = validator.validate_reference_health_links(
            self.reference_traffic, profiles, self.deployment
        )
        self.assertTrue(any("rowan-private" in error for error in errors), errors)

    def test_boundary_scan_rejects_machine_local_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "docs").mkdir()
            (root / "docs/bad.md").write_text(
                "local authority lives under /Users/example/private\n",
                encoding="utf-8",
            )
            errors = validator.scan_portable_boundaries(root, [root / "docs"])
        self.assertTrue(any("machine-local path" in error for error in errors), errors)

    def test_doc_pair_requires_contract_ids_in_both_languages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "zh.md").write_text(
                "doc_id: sample\nSIG-01\n<a id=\"meaning\"></a>\n",
                encoding="utf-8",
            )
            (root / "en.md").write_text(
                "doc_id: sample\nmissing\n<a id=\"meaning\"></a>\n",
                encoding="utf-8",
            )
            pairs = {
                "schema": "signalbox.docs-pairs/v2",
                "contract_revision": 2,
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
                (root / f"{language}.md").write_text(
                    "doc_id: sample\nSIG-01\n",
                    encoding="utf-8",
                )
            pairs = {
                "schema": "signalbox.docs-pairs/v2",
                "contract_revision": 2,
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


if __name__ == "__main__":
    unittest.main()
