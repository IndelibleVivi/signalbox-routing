import copy
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("signalbox_validate", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SignalboxContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator()
        cls.health_contract = json.loads(
            (ROOT / "contracts" / "health-contract.json").read_text()
        )
        profiles_document = json.loads(
            (ROOT / "examples" / "mintie" / "health-profiles.json").read_text()
        )
        cls.profiles = {
            profile["kind"]: profile for profile in profiles_document["profiles"]
        }
        cls.pass_report = json.loads(
            (ROOT / "tests" / "fixtures" / "health-pass.json").read_text()
        )

    def test_repository_contracts_validate(self):
        self.assertEqual(self.validator.validate_repository(ROOT), [])

    def test_terminal_health_reports_validate(self):
        profile = self.profiles["operational"]
        for name in ("health-pass.json", "health-fail.json", "health-unknown.json"):
            report = json.loads((ROOT / "tests" / "fixtures" / name).read_text())
            with self.subTest(name=name):
                self.assertEqual(
                    self.validator.validate_health_report(
                        report, self.health_contract, profile
                    ),
                    [],
                )

    def test_stale_pass_has_effective_unknown_outcome(self):
        report = json.loads(
            (ROOT / "tests" / "fixtures" / "health-stale-pass.json").read_text()
        )
        now = datetime(2026, 8, 31, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(
            self.validator.effective_health_outcome(report, now), "unknown"
        )

    def test_generation_regression_has_effective_unknown_outcome(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        self.assertEqual(
            self.validator.effective_health_outcome(
                self.pass_report, now, minimum_generation=1002
            ),
            "unknown",
        )

    def test_profile_revision_mismatch_has_effective_unknown_outcome(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        self.assertEqual(
            self.validator.effective_health_outcome(
                self.pass_report, now, expected_profile_revision=2
            ),
            "unknown",
        )

    def test_rollup_rejects_success_when_a_dimension_failed(self):
        report = copy.deepcopy(self.pass_report)
        report["dimensions"]["transport"]["state"] = "fail"
        report["dimensions"]["transport"]["reason_code"] = "timeout"
        errors = self.validator.validate_health_report(
            report, self.health_contract, self.profiles["operational"]
        )
        self.assertTrue(any("rollup" in error for error in errors), errors)

    def test_health_report_requires_profile_dimensions(self):
        report = copy.deepcopy(self.pass_report)
        del report["dimensions"]["recovery-readiness"]
        errors = self.validator.validate_health_report(
            report, self.health_contract, self.profiles["operational"]
        )
        self.assertTrue(any("dimensions" in error for error in errors), errors)

    def test_health_report_rejects_private_durable_keys(self):
        report = copy.deepcopy(self.pass_report)
        report["dimensions"]["exit-identity"]["exit_ip"] = "192.0.2.1"
        errors = self.validator.validate_health_report(
            report, self.health_contract, self.profiles["operational"]
        )
        self.assertTrue(any("forbidden durable key" in error for error in errors), errors)

    def test_unknown_recovery_report_cannot_open_restore_gate(self):
        report = json.loads(
            (ROOT / "tests" / "fixtures" / "health-unknown.json").read_text()
        )
        profile = self.profiles["recovery-preflight"]
        report["id"] = "report-recovery-unknown-1003"
        report["profile_ref"] = profile["id"]
        report["profile_revision"] = profile["revision"]
        report["dimensions"] = {
            key: value
            for key, value in report["dimensions"].items()
            if key in profile["required_dimensions"]
        }
        self.assertEqual(
            self.validator.validate_health_report(
                report, self.health_contract, profile
            ),
            [],
        )
        now = datetime(2026, 8, 31, 12, 10, tzinfo=timezone.utc)
        self.assertFalse(self.validator.restore_gate_allows(report, profile, now))

    def test_operational_pass_cannot_open_restore_gate(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        self.assertFalse(
            self.validator.restore_gate_allows(
                self.pass_report, self.profiles["operational"], now
            )
        )

    def test_traffic_contract_rejects_direct_failure_fallback(self):
        traffic = json.loads(
            (ROOT / "contracts" / "traffic-policy.json").read_text()
        )
        roles = json.loads((ROOT / "contracts" / "roles.json").read_text())
        traffic["direct_action"]["allowed_on_proxy_failure"] = True
        errors = self.validator.validate_traffic_policy(traffic, roles)
        self.assertTrue(any("DIRECT" in error for error in errors), errors)

    def test_role_reference_must_resolve(self):
        traffic = json.loads(
            (ROOT / "contracts" / "traffic-policy.json").read_text()
        )
        roles = json.loads((ROOT / "contracts" / "roles.json").read_text())
        traffic["default_proxy_required"]["selection"]["role"] = "missing-role"
        errors = self.validator.validate_traffic_policy(traffic, roles)
        self.assertTrue(any("missing-role" in error for error in errors), errors)

    def test_protected_application_structurally_rejects_fallback(self):
        traffic = json.loads(
            (ROOT / "contracts" / "traffic-policy.json").read_text()
        )
        roles = json.loads((ROOT / "contracts" / "roles.json").read_text())
        traffic["protected_application"]["fallback_roles"] = []
        errors = self.validator.validate_traffic_policy(traffic, roles)
        self.assertTrue(any("structurally forbids" in error for error in errors), errors)

    def test_acceptance_record_cannot_upgrade_realization(self):
        claims = json.loads((ROOT / "contracts" / "claims.json").read_text())
        claims["acceptance_record"]["can_upgrade_realization_stage"] = True
        errors = self.validator.validate_claims(claims)
        self.assertTrue(any("cannot upgrade" in error for error in errors), errors)

    def test_health_profiles_require_bounded_entry_retention(self):
        profiles = json.loads(
            (ROOT / "examples" / "mintie" / "health-profiles.json").read_text()
        )
        profiles["profiles"][0]["retention"]["max_entries"] = 0
        errors = self.validator.validate_health_profiles(
            profiles, self.health_contract
        )
        self.assertTrue(any("max_entries" in error for error in errors), errors)

    def test_boundary_scan_rejects_machine_local_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "docs").mkdir()
            (root / "docs" / "bad.md").write_text(
                "local authority lives under /Users/example/private\n"
            )
            errors = self.validator.scan_portable_boundaries(root, [root / "docs"])
        self.assertTrue(any("machine-local path" in error for error in errors), errors)

    def test_doc_pair_requires_contract_ids_in_both_languages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "zh.md").write_text("SIG-01\n")
            (root / "en.md").write_text("missing\n")
            pairs = {
                "pairs": [
                    {
                        "doc_id": "sample",
                        "zh-CN": "zh.md",
                        "en": "en.md",
                        "required_contract_ids": ["SIG-01"],
                    }
                ]
            }
            errors = self.validator.validate_doc_pairs(root, pairs)
        self.assertTrue(any("SIG-01" in error and "en.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
