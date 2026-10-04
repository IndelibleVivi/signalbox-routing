"""Focused regression matrix for portable semantic closure.

These tests pin the defects that the source gate must never regress:

* generic role/gateway/routing-owner closure before fixed Mintie mappings;
* one structured canonical-private-ingress explanation with precise codes;
* malformed-type short-circuiting to ``unknown``/``malformed-evidence``;
* standalone profile structural/semantic validation;
* observation-freshness and attempt-duration bounds;
* generic catalog revision agreement.
"""

import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import validate as validator

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

class SemanticClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roles = load_json("contracts/roles.json")
        cls.traffic = load_json("contracts/traffic-policy.json")
        cls.health_contract = load_json("contracts/health-contract.json")
        cls.profiles_document = load_json("examples/mintie/health-profiles.json")
        cls.profiles = {
            profile["id"]: profile for profile in cls.profiles_document["profiles"]
        }
        cls.deployment = load_json("examples/mintie/deployment.json")
        cls.reference_traffic = load_json("examples/mintie/traffic-policy.json")
        cls.health_report_schema = load_json("schemas/health-report.schema.json")
        cls.lane_report = load_json("examples/mintie/reports/lane-alder-pass.json")
        cls.lane_profile = cls.profiles["mintie-egress-alder"]

    # ------------------------------------------------------------------
    # 1. Generic portable role and routing-owner closure
    # ------------------------------------------------------------------
    def test_missing_role_capability_is_rejected(self):
        roles = copy.deepcopy(self.roles)
        roles["roles"]["private-ingress-primary"]["required_capabilities"] = [
            "transport-health"
        ]
        errors = validator.validate_roles(roles)
        self.assertTrue(
            any(
                "private-ingress-primary" in error and "capabilit" in error
                for error in errors
            ),
            errors,
        )

    def test_legal_role_capability_extension_is_allowed(self):
        roles = copy.deepcopy(self.roles)
        roles["roles"]["private-ingress-primary"]["required_capabilities"].append(
            "extra-portable-capability"
        )
        self.assertEqual(validator.validate_roles(roles), [])

    def test_role_kind_is_semantically_bound(self):
        roles = copy.deepcopy(self.roles)
        roles["roles"]["routing-control-plane"]["kind"] = "egress-lane"
        errors = validator.validate_roles(roles)
        self.assertTrue(any("control-plane" in error for error in errors), errors)

    def test_routing_owner_must_be_control_plane_role(self):
        traffic = copy.deepcopy(self.traffic)
        traffic["routing_owner_role"] = "general-primary"
        errors = validator.validate_traffic_policy(traffic, self.roles)
        self.assertTrue(any("routing_owner_role" in error for error in errors), errors)

    def test_routing_owner_capabilities_are_enforced(self):
        roles = copy.deepcopy(self.roles)
        roles["roles"]["routing-control-plane"]["required_capabilities"] = [
            "transparent-interception"
        ]
        errors = validator.validate_traffic_policy(self.traffic, roles)
        self.assertTrue(
            any(
                "routing owner is missing required capabilities" in error
                for error in errors
            ),
            errors,
        )

    def test_private_ingress_role_kind_is_enforced(self):
        roles = copy.deepcopy(self.roles)
        roles["roles"]["private-ingress-primary"]["kind"] = "general-egress"
        errors = validator.validate_traffic_policy(self.traffic, roles)
        self.assertTrue(
            any("private-ingress-gateway role" in error for error in errors), errors
        )

    # ------------------------------------------------------------------
    # 2. All gateways validated before the fixed Mintie mapping
    # ------------------------------------------------------------------
    def test_unused_added_gateway_with_orphan_host_is_rejected(self):
        deployment = copy.deepcopy(self.deployment)
        deployment["dedicated_gateway_identities"]["ghost-private"] = {
            "host_instance": "ghost",
            "role": "private-ingress-primary",
            "credential_scope": "dedicated",
            "general_egress_equivalent": False,
        }
        errors = validator.validate_deployment(deployment, self.roles)
        self.assertTrue(
            any("ghost-private" in error and "host" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any(
                "ghost-private" in error and "health subject" in error
                for error in errors
            ),
            errors,
        )

    def test_unused_added_gateway_with_wrong_role_kind_is_rejected(self):
        deployment = copy.deepcopy(self.deployment)
        deployment["dedicated_gateway_identities"]["new-private"] = {
            "host_instance": "alder",
            "role": "general-primary",
            "credential_scope": "dedicated",
            "general_egress_equivalent": False,
        }
        deployment["health_subjects"]["gateway/new-private"] = {
            "kind": "private-ingress-lane",
            "binding_ref": "new-private",
        }
        errors = validator.validate_deployment(deployment, self.roles)
        self.assertTrue(
            any(
                "new-private" in error and "private-ingress-gateway" in error
                for error in errors
            ),
            errors,
        )

    def test_gateway_credential_scope_and_equivalence_are_generic(self):
        deployment = copy.deepcopy(self.deployment)
        deployment["dedicated_gateway_identities"]["alder-private"][
            "credential_scope"
        ] = "shared"
        deployment["dedicated_gateway_identities"]["alder-private"][
            "general_egress_equivalent"
        ] = True
        errors = validator.validate_deployment(deployment, self.roles)
        self.assertTrue(any("dedicated credentials" in error for error in errors), errors)
        self.assertTrue(any("general egress" in error for error in errors), errors)

    # ------------------------------------------------------------------
    # 3. One structured canonical-private-ingress explanation
    # ------------------------------------------------------------------
    def test_explain_private_ingress_is_valid_for_reference_chain(self):
        result = validator.explain_private_ingress(
            self.reference_traffic,
            self.deployment,
            self.roles,
            self.profiles_document,
            self.health_contract,
        )
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["diagnostics"], [])
        self.assertEqual(result["chain"]["host"], "alder")
        self.assertTrue(result["chain"]["origin"]["canonical_https"])
        self.assertEqual(result["chain"]["role"]["id"], "private-ingress-primary")
        self.assertEqual(result["chain"]["subject"]["kind"], "private-ingress-lane")
        self.assertEqual(len(result["chain"]["profiles"]), 1)

    def test_explain_private_ingress_https_downgrade_has_distinct_code(self):
        deployment = copy.deepcopy(self.deployment)
        deployment["canonical_origins"]["sample-app"]["scheme"] = "http"
        result = validator.explain_private_ingress(
            self.reference_traffic,
            deployment,
            self.roles,
            self.profiles_document,
            self.health_contract,
        )
        self.assertFalse(result["valid"])
        codes = {item["code"] for item in result["diagnostics"]}
        self.assertIn("private-ingress-origin-not-https", codes)
        self.assertTrue(
            any(
                item["path"] == "/canonical_origins/sample-app/scheme"
                for item in result["diagnostics"]
            )
        )

    def test_explain_private_ingress_orphan_gateway_chain(self):
        deployment = copy.deepcopy(self.deployment)
        deployment["dedicated_gateway_identities"]["alder-private"][
            "host_instance"
        ] = "missing-host"
        result = validator.explain_private_ingress(
            self.reference_traffic,
            deployment,
            self.roles,
            self.profiles_document,
            self.health_contract,
        )
        codes = {item["code"] for item in result["diagnostics"]}
        self.assertIn("private-ingress-host-unresolved", codes)

    def test_explain_private_ingress_role_capability_diagnostic(self):
        roles = copy.deepcopy(self.roles)
        roles["roles"]["private-ingress-primary"]["required_capabilities"] = [
            "dedicated-authenticated-identity"
        ]
        result = validator.explain_private_ingress(
            self.reference_traffic,
            self.deployment,
            roles,
            self.profiles_document,
            self.health_contract,
        )
        codes = {item["code"] for item in result["diagnostics"]}
        self.assertIn("private-ingress-role-capability", codes)
        self.assertTrue(
            any(
                item["path"]
                == "/roles/private-ingress-primary/required_capabilities"
                for item in result["diagnostics"]
            )
        )

    def test_explain_private_ingress_profile_cardinality_diagnostic(self):
        profiles = copy.deepcopy(self.profiles_document)
        duplicate = copy.deepcopy(self.profiles["mintie-private-alder"])
        duplicate["id"] = "mintie-private-alder-duplicate"
        profiles["profiles"].append(duplicate)
        result = validator.explain_private_ingress(
            self.reference_traffic,
            self.deployment,
            self.roles,
            profiles,
            self.health_contract,
        )
        codes = {item["code"] for item in result["diagnostics"]}
        self.assertIn("private-ingress-profile-cardinality", codes)

    def test_explanation_validates_profile_contents_and_exact_subject_kind(self):
        profiles = copy.deepcopy(self.profiles_document)
        private = next(p for p in profiles["profiles"] if p["id"] == "mintie-private-alder")
        private["required_dimensions"].remove("exit-identity")
        deployment = copy.deepcopy(self.deployment)
        deployment["health_subjects"]["gateway/alder-private"]["kind"] = "egress-lane"
        result = validator.explain_private_ingress(
            self.reference_traffic, deployment, self.roles, profiles, self.health_contract
        )
        codes = {d["code"] for d in result["diagnostics"]}
        self.assertIn("private-ingress-profile-invalid", codes)
        self.assertIn("private-ingress-subject-kind", codes)
        self.assertTrue(any(d["path"] == "/health_subjects/gateway~1alder-private/kind"
                            for d in result["diagnostics"]))

    def test_explain_private_ingress_does_not_label_unrelated_route_failure(self):
        traffic = copy.deepcopy(self.reference_traffic)
        for route in traffic["route_order"]:
            if route["id"] == "protected-application":
                route["role_binding_ref"] = "alder"
        result = validator.explain_private_ingress(
            traffic,
            self.deployment,
            self.roles,
            self.profiles_document,
            self.health_contract,
        )
        self.assertFalse(result["valid"])
        chain_codes = {
            item["code"]
            for item in result["diagnostics"]
            if item["code"].startswith("private-ingress-")
        }
        self.assertEqual(chain_codes, set())
        self.assertTrue(
            any(item["code"] == "reference-traffic" for item in result["diagnostics"])
        )

    def test_explain_private_ingress_matches_validator_algorithm(self):
        mutations = (
            lambda d, r, p: d["canonical_origins"]["sample-app"].update(scheme="http"),
            lambda d, r, p: d["dedicated_gateway_identities"][
                "alder-private"
            ].update(host_instance="ghost"),
            lambda d, r, p: r["roles"]["private-ingress-primary"].update(
                required_capabilities=[]
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                deployment = copy.deepcopy(self.deployment)
                roles = copy.deepcopy(self.roles)
                profiles = copy.deepcopy(self.profiles_document)
                mutate(deployment, roles, profiles)
                result = validator.explain_private_ingress(
                    self.reference_traffic,
                    deployment,
                    roles,
                    profiles,
                    self.health_contract,
                )
                self.assertFalse(result["valid"])

    # ------------------------------------------------------------------
    # 4. Malformed evidence short-circuits to unknown
    # ------------------------------------------------------------------
    def test_report_structure_error_short_circuits_type_semantics(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        cases = {
            "outcome_list": lambda r: r.update(outcome=["pass"]),
            "dimension_state_list": lambda r: r["dimensions"]["transport"].update(
                state=["pass"]
            ),
            "dimension_state_dict": lambda r: r["dimensions"]["transport"].update(
                state={"pass": True}
            ),
            "dimension_reason_list": lambda r: r["dimensions"]["transport"].update(
                reason_code=["timeout"]
            ),
            "observation_state_list": lambda r: r["dimensions"]["transport"][
                "observations"
            ][0].update(state=["pass"]),
            "observation_reason_object": lambda r: r["dimensions"]["transport"][
                "observations"
            ][0].update(reason_code={"timeout": True}),
            "generation_bool": lambda r: r.update(generation=True),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                report = copy.deepcopy(self.lane_report)
                mutate(report)
                evaluation = validator.evaluate_health_evidence(
                    report,
                    self.health_contract,
                    self.lane_profile,
                    self.health_report_schema,
                    now,
                    expected_current_identity=validator.health_evidence_identity(
                        report
                    ),
                )
                self.assertFalse(evaluation.structurally_valid)
                self.assertEqual(evaluation.effective_outcome, "unknown")
                self.assertIn("malformed-evidence", evaluation.reason_codes)

    def test_non_object_report_never_crashes_direct_evaluator(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        for bad in ([], "x", 5, None):
            with self.subTest(bad=bad):
                evaluation = validator.evaluate_health_evidence(
                    bad,
                    self.health_contract,
                    self.lane_profile,
                    self.health_report_schema,
                    now,
                )
                self.assertEqual(evaluation.effective_outcome, "unknown")
                self.assertIn("malformed-evidence", evaluation.reason_codes)

    def test_restore_gate_rejects_malformed_inputs_without_crashing(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        recovery = load_json("examples/mintie/reports/recovery-preflight-pass.json")
        profile = self.profiles["mintie-recovery-preflight"]
        self.assertFalse(
            validator.restore_gate_allows(
                [],
                self.health_contract,
                profile,
                self.health_report_schema,
                now,
                expected_gate_context=recovery["gate_context"],
                expected_current_identity=current_identity(recovery),
            )
        )
        self.assertFalse(
            validator.restore_gate_allows(
                recovery,
                self.health_contract,
                "not-a-profile",
                self.health_report_schema,
                now,
                expected_gate_context=recovery["gate_context"],
                expected_current_identity=current_identity(recovery),
            )
        )
        self.assertFalse(
            validator.restore_gate_allows(
                recovery, [], profile, self.health_report_schema, now,
                expected_gate_context=recovery["gate_context"],
                expected_current_identity=current_identity(recovery),
            )
        )

    def test_aggregate_member_with_wrong_type_state_is_unknown_not_crash(self):
        aggregate = load_json("examples/mintie/health-aggregate.json")
        report = copy.deepcopy(self.lane_report)
        report["dimensions"]["transport"]["observations"][0]["state"] = ["pass"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for member in aggregate["members"]:
                relative = Path("examples/mintie") / member["report_ref"]
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text((ROOT / relative).read_text())
            target = root / "examples/mintie/reports/lane-alder-pass.json"
            target.write_text(json.dumps(report))
            errors = validator.validate_health_aggregate(
                root, aggregate, self.deployment, self.profiles_document,
                self.health_contract, self.health_report_schema,
            )
        self.assertTrue(any("not canonically valid" in error for error in errors), errors)

    # ------------------------------------------------------------------
    # 4b/5. Standalone profile and observation freshness
    # ------------------------------------------------------------------
    def test_deleted_profile_dimension_is_malformed_evidence(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        profile = copy.deepcopy(self.lane_profile)
        del profile["required_dimensions"][0]
        evaluation = validator.evaluate_health_evidence(
            self.lane_report,
            self.health_contract,
            profile,
            self.health_report_schema,
            now,
            expected_current_identity=current_identity(self.lane_report),
        )
        self.assertFalse(evaluation.semantically_valid)
        self.assertEqual(evaluation.effective_outcome, "unknown")
        self.assertIn("malformed-evidence", evaluation.reason_codes)

    def test_malformed_profile_is_malformed_evidence(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        for bad_profile in ("x", [], {}, {"id": "x"}):
            with self.subTest(profile=bad_profile):
                evaluation = validator.evaluate_health_evidence(
                    self.lane_report,
                    self.health_contract,
                    bad_profile,
                    self.health_report_schema,
                    now,
                )
                self.assertEqual(evaluation.effective_outcome, "unknown")
                self.assertIn("malformed-evidence", evaluation.reason_codes)

    def test_malformed_contract_is_malformed_evidence(self):
        now = datetime(2026, 8, 31, 10, 10, tzinfo=timezone.utc)
        for bad_contract in ("x", [], {"schema": "signalbox.health-contract/v6"}):
            with self.subTest(contract=bad_contract):
                evaluation = validator.evaluate_health_evidence(
                    self.lane_report,
                    bad_contract,
                    self.lane_profile,
                    self.health_report_schema,
                    now,
                )
                self.assertEqual(evaluation.effective_outcome, "unknown")
                self.assertIn("malformed-evidence", evaluation.reason_codes)

    def test_valid_until_cannot_outlive_earliest_observation(self):
        report = copy.deepcopy(self.lane_report)
        # earliest observation is 10:00:01; +1200s = 10:20:01.
        report["valid_until"] = "2026-08-31T10:20:30Z"
        errors = validator.validate_health_report(
            report, self.health_contract, self.lane_profile
        )
        self.assertTrue(
            any("earliest observation freshness expiry" in error for error in errors),
            errors,
        )

    def test_valid_until_at_earliest_observation_expiry_is_allowed(self):
        report = copy.deepcopy(self.lane_report)
        report["valid_until"] = "2026-08-31T10:20:01Z"
        errors = validator.validate_health_report(
            report, self.health_contract, self.lane_profile
        )
        self.assertEqual(errors, [])

    def test_stale_observation_beyond_age_is_rejected(self):
        report = copy.deepcopy(self.lane_report)
        report["dimensions"]["transport"]["observations"][0][
            "observed_at"
        ] = "2026-08-31T09:30:00Z"
        report["started_at"] = "2026-08-31T09:30:00Z"
        errors = validator.validate_health_report(
            report, self.health_contract, self.lane_profile
        )
        self.assertTrue(
            any(
                "stale against profile observation freshness" in error
                for error in errors
            ),
            errors,
        )

    def test_excessive_attempt_duration_is_rejected(self):
        report = copy.deepcopy(self.lane_report)
        report["completed_at"] = "2026-08-31T10:10:00Z"
        report["published_at"] = "2026-08-31T10:10:01Z"
        report["valid_until"] = "2026-08-31T10:10:02Z"
        errors = validator.validate_health_report(
            report, self.health_contract, self.lane_profile
        )
        self.assertTrue(
            any("attempt duration exceeds profile freshness" in error for error in errors),
            errors,
        )

    def test_freshness_contract_declares_all_three_bounds(self):
        freshness = self.health_contract["freshness"]
        self.assertEqual(
            freshness["maximum_formula"],
            "valid_until <= completed_at + profile.max_report_age_seconds",
        )
        self.assertEqual(
            freshness["observation_formula"],
            "valid_until <= observation.observed_at + profile.max_observation_age_seconds",
        )
        self.assertEqual(
            freshness["attempt_formula"],
            "completed_at - started_at <= profile.max_attempt_duration_seconds",
        )
        self.assertIn("profile_freshness_required_fields", self.health_contract)
        for profile in self.profiles_document["profiles"]:
            with self.subTest(profile=profile["id"]):
                for field in self.health_contract[
                    "profile_freshness_required_fields"
                ]:
                    self.assertIn(field, profile["freshness"])

    # ------------------------------------------------------------------
    # 6. Generic catalog revision agreement
    # ------------------------------------------------------------------
    def test_catalog_revision_must_match_owner_contract_revision(self):
        catalog = load_json("contracts/catalog.json")
        drifted = copy.deepcopy(catalog)
        for entry in drifted["entries"]:
            if entry["schema_id"] == "signalbox.health-contract/v6":
                entry["revision"] = 999
        errors = validator.validate_catalog(ROOT, drifted)
        self.assertTrue(
            any(
                "health-contract/v6" in error and "owner contract_revision" in error
                for error in errors
            ),
            errors,
        )

    def test_traffic_catalog_revision_mismatch_against_owner(self):
        catalog = load_json("contracts/catalog.json")
        drifted = copy.deepcopy(catalog)
        for entry in drifted["entries"]:
            if entry["schema_id"] == "signalbox.traffic-policy/v2":
                entry["revision"] = 999
        errors = validator.validate_catalog(ROOT, drifted)
        self.assertTrue(
            any(
                "traffic-policy/v2" in error and "owner contract_revision" in error
                for error in errors
            ),
            errors,
        )

    def test_reference_traffic_revision_agrees_with_owner(self):
        catalog = load_json("contracts/catalog.json")
        reference_traffic = load_json("examples/mintie/traffic-policy.json")
        self.assertEqual(
            validator.validate_reference_deployment_registration(
                self.deployment, catalog, reference_traffic
            ),
            [],
        )
        drifted = copy.deepcopy(reference_traffic)
        drifted["contract_revision"] = 999
        errors = validator.validate_reference_deployment_registration(
            self.deployment, catalog, drifted
        )
        self.assertTrue(any("reference-traffic" in error for error in errors), errors)

    def test_independent_profile_revisions_are_allowed(self):
        catalog = load_json("contracts/catalog.json")
        entries = {entry["schema_id"]: entry for entry in catalog["entries"]}
        self.assertEqual(entries["signalbox.health-profile/v3"]["revision"], 1)
        revisions = {
            profile["revision"] for profile in self.profiles_document["profiles"]
        }
        self.assertTrue(revisions - {1})

    def test_claims_and_catalog_revisions_have_no_exemption(self):
        for schema_id in ("signalbox.claims/v2", "signalbox.contract-catalog/v1"):
            catalog = load_json("contracts/catalog.json")
            next(e for e in catalog["entries"] if e["schema_id"] == schema_id)["revision"] = 999
            errors = validator.validate_catalog(ROOT, catalog)
            self.assertTrue(any(schema_id in e and "owner" in e for e in errors), errors)

    def test_additional_whole_instance_revision_must_match_catalog(self):
        catalog = load_json("contracts/catalog.json")
        traffic = copy.deepcopy(self.traffic)
        traffic["contract_revision"] = 999
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "extra.json").write_text(json.dumps(traffic))
            entry = next(e for e in catalog["entries"] if e["schema_id"] == traffic["schema"])
            entry["instances"].append({"path": "extra.json"})
            errors = validator.validate_catalog(root, catalog)
        self.assertTrue(any("instance extra.json contract_revision" in e for e in errors), errors)

    def test_current_pointer_sequencing_is_normative(self):
        for field, wrong in (("generation_allocation", "completion"),
                             ("new_attempt_invalidates_current", False),
                             ("late_completion", "replace-current"),
                             ("compare_and_decision", "separate"),
                             ("restart_continuity", "optional"),
                             ("unconfirmed_continuity_outcome", "pass")):
            contract = copy.deepcopy(self.health_contract)
            contract["sequencing"][field] = wrong
            self.assertTrue(any("sequencing" in e for e in validator.validate_health_contract(contract)))

    def test_acceptance_required_fields_must_exact_match(self):
        claims = load_json("contracts/claims.json")
        claims["acceptance_record"]["required_fields"].append("unexpected-required-field")
        self.assertTrue(any("acceptance required fields" in e for e in validator.validate_claims(claims)))

    # ------------------------------------------------------------------
    # Repository gate still closes
    # ------------------------------------------------------------------
    def test_repository_contracts_validate(self):
        self.assertEqual(validator.validate_repository(ROOT), [])

if __name__ == "__main__":
    unittest.main()
