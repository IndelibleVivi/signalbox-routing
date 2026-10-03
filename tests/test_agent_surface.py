import copy
import json
import shutil
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Event

from scripts.handoff import evaluate_handoff
from scripts.reference_workflow import ReferencePublisher
from scripts.replay import assess_coverage, replay_case, select_route
from scripts.validate import parse_rfc3339


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


class AgentSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.bundle = load("examples/mintie/handoff.json")
        self.at = parse_rfc3339("2026-10-03T00:00:03Z")
        self.report = load("examples/mintie/reports/recovery-preflight-pass.json")
        self.contract = load("contracts/health-contract.json")
        self.profile = next(p for p in load("examples/mintie/health-profiles.json")["profiles"] if p["id"] == self.report["profile_ref"])
        self.schema = load("schemas/health-report.schema.json")
        self.now = parse_rfc3339(self.report["published_at"])
        self.publisher = ReferencePublisher(self.contract, self.profile, self.schema, self.report["producer_ref"], self.report["generation_epoch"], 41)

    def begin_report(self, attempt):
        reservation = self.publisher.begin(attempt, parse_rfc3339(self.report["started_at"]))
        result = copy.deepcopy(self.report)
        result.update(reservation)
        result["id"] = "report/" + attempt
        return result

    def test_actual_handoff_and_historical_acceptance_validate(self):
        result = evaluate_handoff(ROOT, self.bundle, self.at)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["claim_outcomes"], {"claim/source-contract": "pass"})
        later = evaluate_handoff(ROOT, self.bundle, self.at + timedelta(days=30))
        self.assertTrue(later["valid"], later)

    def test_handoff_rejects_broken_scope_refs_stage_and_time(self):
        mutations = [
            ("unresolved-evidence", lambda d: d["claims"][0].update(evidence_refs=["missing"])),
            ("unresolved-claim", lambda d: d["acceptance_records"][0].update(claim_refs=["missing"])),
            ("scope-mismatch", lambda d: d["evidence"][0].update(scope_ref="other-scope")),
            ("stage-mismatch", lambda d: d["claims"][0].update(stage="installed", source_ref="claim/source-contract")),
            ("evidence-not-yet-available", lambda d: d["evidence"][0].update(observed_at="2026-10-03T00:00:02Z")),
            ("stale-evidence", lambda d: d["evidence"][0].update(valid_until="2026-10-03T00:00:01Z")),
            ("unresolved-artifact", lambda d: d["evidence"][0].update(artifact_ref="../outside.json")),
            ("acceptance-evidence-incomplete", lambda d: d["acceptance_records"][0].update(evidence_refs=["missing"])),
        ]
        for expected, mutate in mutations:
            with self.subTest(code=expected):
                bundle = copy.deepcopy(self.bundle)
                mutate(bundle)
                result = evaluate_handoff(ROOT, bundle, self.at)
                self.assertFalse(result["valid"])
                self.assertIn(expected, [d["code"] for d in result["diagnostics"]])

    def test_acceptance_cannot_inject_realization_or_skip_actor(self):
        for field in ("actor_ref", "scope_ref", "decided_at", "evidence_refs"):
            with self.subTest(field=field):
                bundle = copy.deepcopy(self.bundle)
                del bundle["acceptance_records"][0][field]
                self.assertFalse(evaluate_handoff(ROOT, bundle, self.at)["valid"])
        bundle = copy.deepcopy(self.bundle)
        bundle["acceptance_records"][0]["stage"] = "path-evidence"
        self.assertFalse(evaluate_handoff(ROOT, bundle, self.at)["valid"])

    def test_full_path_handoff_requires_fresh_same_subject_current_evidence(self):
        bundle = load("examples/mintie/path-handoff.json")
        at = parse_rfc3339(bundle["claims"][-1]["observed_at"])
        self.assertTrue(evaluate_handoff(ROOT, bundle, at)["valid"])
        stale = evaluate_handoff(ROOT, bundle, at + timedelta(days=1))
        self.assertFalse(stale["valid"])
        self.assertIn("unusable-path-evidence", [d["code"] for d in stale["diagnostics"]])
        for mutation, code in (
            (lambda b: b["claims"][-1]["current_health_identity"].update(generation=999), "unusable-path-evidence"),
            (lambda b: b["claims"][-1].update(health_report_ref="missing.json"), "unresolved-health-report"),
            (lambda b: b.update(scope_ref="entire-network"), "scope-mismatch"),
        ):
            with self.subTest(code=code):
                changed = copy.deepcopy(bundle)
                mutation(changed)
                result = evaluate_handoff(ROOT, changed, at)
                self.assertFalse(result["valid"])
                self.assertIn(code, [d["code"] for d in result["diagnostics"]])
        for item in [*bundle["claims"], *bundle["evidence"], *bundle["acceptance_records"]]:
            item["scope_ref"] = "entire-network"
        bundle["scope_ref"] = "entire-network"
        result = evaluate_handoff(ROOT, bundle, at)
        self.assertIn("health-scope-mismatch", [d["code"] for d in result["diagnostics"]])

    def test_replay_all_five_cases_and_three_races(self):
        cases = load("examples/scenarios/cases.json")
        self.assertEqual(len(cases), 8)
        for case in cases:
            with self.subTest(case=case["id"]):
                actual = replay_case(case)
                for key, expected in case["expected"].items():
                    self.assertEqual(actual[key], expected, actual)

    def test_handoff_cannot_crash_or_accept_unknown_with_malformed_report(self):
        bundle = load("examples/mintie/path-handoff.json")
        at = parse_rfc3339(bundle["claims"][-1]["observed_at"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("contracts", "schemas", "examples"):
                shutil.copytree(ROOT / folder, root / folder)
            report_path = root / bundle["claims"][-1]["health_report_ref"]
            report = json.loads(report_path.read_text())
            del report["subject_ref"]
            report["dimensions"]["transport"]["state"] = ["pass"]
            report_path.write_text(json.dumps(report))
            bundle["claims"][-1]["outcome"] = "unknown"
            bundle["evidence"][-1]["outcome"] = "unknown"
            result = evaluate_handoff(root, bundle, at)
        self.assertFalse(result["valid"], result)
        self.assertIn("malformed-path-evidence", [d["code"] for d in result["diagnostics"]])

    def test_coverage_only_passes_after_all_required_boundaries_observed(self):
        required = ["admission", "interception", "local-delivery", "egress"]
        self.assertEqual(assess_coverage(required, {"egress": "pass"})["effective_outcome"], "unknown")
        complete = dict.fromkeys(required, "pass")
        self.assertEqual(assess_coverage(required, complete)["effective_outcome"], "pass")
        complete["admission"] = "fail"
        self.assertEqual(assess_coverage(required, complete)["effective_outcome"], "fail")

    def test_invalid_route_grammar_cannot_be_replayed_as_direct(self):
        traffic = load("examples/mintie/traffic-policy.json")
        traffic["route_order"][2]["action"] = "direct"
        result = select_route(
            traffic, load("examples/mintie/deployment.json"), ["canonical-private-ingress"],
            roles=load("contracts/roles.json"), health_profiles=load("examples/mintie/health-profiles.json"),
            health_contract=load("contracts/health-contract.json"))
        self.assertEqual(result["action"], "retain-guard")

    def test_unsupported_coverage_states_never_count_as_pass(self):
        for state in ("checking", "pas", None, [], {}, True):
            with self.subTest(state=state):
                self.assertEqual(assess_coverage(["admission"], {"admission": state})["effective_outcome"], "unknown")
        self.assertEqual(assess_coverage(["a", "b"], {"a": "checking", "b": "fail"})["effective_outcome"], "fail")

    def test_path_claim_must_cite_the_report_actually_evaluated(self):
        bundle = load("examples/mintie/path-handoff.json")
        at = parse_rfc3339(bundle["claims"][-1]["observed_at"])
        bundle["evidence"][-1]["artifact_ref"] = "contracts/traffic-policy.json"
        result = evaluate_handoff(ROOT, bundle, at)
        self.assertFalse(result["valid"], result)
        self.assertIn("uncited-health-report", [d["code"] for d in result["diagnostics"]])

    def test_resume_cannot_change_generation_scope(self):
        candidate = self.begin_report("A")
        self.publisher.publish(candidate, self.now)
        snapshot = self.publisher.snapshot()
        for field in ("producer", "subject", "profile"):
            with self.subTest(field=field):
                profile = copy.deepcopy(self.profile)
                producer = candidate["producer_ref"]
                if field == "producer":
                    producer = "reference/other-producer"
                else:
                    profile["subject_ref" if field == "subject" else "id"] = "other-scope"
                with self.assertRaises(ValueError):
                    ReferencePublisher.resume(self.contract, profile, self.schema, producer, snapshot, continuity_confirmed=True)

    def test_new_attempt_blocks_old_pass_while_checking(self):
        first = self.begin_report("A")
        self.publisher.publish(first, self.now)
        old = self.publisher.read_current()
        self.begin_report("B")
        self.assertIsNone(self.publisher.read_current())
        self.assertFalse(self.publisher.decide_restore(old, first["gate_context"], self.now)["allowed"])

    def test_interleaved_completion_preserves_new_current_and_both_reports(self):
        first = self.begin_report("A")
        second = self.begin_report("B")
        done = Event()

        def late_completion():
            self.assertTrue(done.wait(5))
            return self.publisher.publish(first, self.now)

        def new_completion():
            receipt = self.publisher.publish(second, self.now)
            done.set()
            return receipt

        with ThreadPoolExecutor(max_workers=2) as pool:
            older = pool.submit(late_completion)
            newer = pool.submit(new_completion)
            self.assertTrue(newer.result()["current"])
            self.assertFalse(older.result()["current"])
        self.assertEqual(self.publisher.read_current()["generation"], 43)
        self.assertEqual(len(self.publisher.snapshot()["reports"]), 2)

    def test_terminal_fail_and_unknown_advance_sequence_and_retain_guard(self):
        for state in ("fail", "unknown"):
            candidate = self.begin_report(state)
            candidate["outcome"] = state
            for dimension in candidate["dimensions"].values():
                dimension["state"] = state
                dimension["reason_code"] = "query-failed"
                for observation in dimension["observations"]:
                    observation["state"] = state
                    observation["reason_code"] = "query-failed"
            receipt = self.publisher.publish(candidate, self.now)
            self.assertTrue(receipt["published"], receipt)
            self.assertEqual(self.publisher.read_current()["generation"], candidate["generation"])
            self.assertFalse(self.publisher.decide_restore(self.publisher.read_current(), candidate["gate_context"], self.now)["allowed"])

    def test_report_immutability_and_exact_gate_context(self):
        candidate = self.begin_report("A")
        self.publisher.publish(candidate, self.now)
        with self.assertRaises(ValueError):
            self.publisher.publish(candidate, self.now)
        identity = self.publisher.read_current()
        self.assertTrue(self.publisher.decide_restore(identity, candidate["gate_context"], self.now)["allowed"])
        context = {**candidate["gate_context"], "operation_ref": "other-operation"}
        result = self.publisher.decide_restore(identity, context, self.now)
        self.assertFalse(result["allowed"])
        self.assertIn("gate-context-mismatch", result["reason_codes"])
        self.assertEqual(result["effective_outcome"], "unknown")

    def test_malformed_publication_does_not_revive_old_current(self):
        first = self.begin_report("A")
        self.publisher.publish(first, self.now)
        old = self.publisher.read_current()
        invalid = self.begin_report("B")
        invalid["outcome"] = []
        receipt = self.publisher.publish(invalid, self.now)
        self.assertFalse(receipt["published"])
        self.assertEqual(receipt["effective_outcome"], "unknown")
        self.assertIsNone(self.publisher.read_current())
        self.assertFalse(self.publisher.decide_restore(old, first["gate_context"], self.now)["allowed"])

    def test_restart_with_verified_snapshot_preserves_sequence(self):
        candidate = self.begin_report("A")
        self.publisher.publish(candidate, self.now)
        snapshot = self.publisher.snapshot()
        resumed = ReferencePublisher.resume(self.contract, self.profile, self.schema, candidate["producer_ref"], snapshot, continuity_confirmed=True)
        self.assertEqual(resumed.read_current(), self.publisher.read_current())
        self.assertEqual(resumed.begin("B", self.now)["generation"], 43)
        unknown = ReferencePublisher.resume(self.contract, self.profile, self.schema, candidate["producer_ref"], snapshot, continuity_confirmed=False)
        with self.assertRaises(ValueError):
            unknown.begin("B", self.now)
        snapshot["generation"] = 999
        self.assertFalse(unknown.decide_restore(self.publisher.read_current(), candidate["gate_context"], self.now)["allowed"])


if __name__ == "__main__":
    unittest.main()
