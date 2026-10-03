"""Executable reference sequencing; all state and decisions are synthetic."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import RLock
from typing import Any

from .validate import evaluate_health_evidence, health_evidence_identity, restore_gate_allows


class ReferencePublisher:
    """One producer/subject/profile/epoch sequence with an in-memory lock.

    A deployment must supply durable reservations and put its actual restore
    effect in the same serialized transaction. This object only emits decisions.
    A newer start invalidates old current evidence; every completion is retained,
    but late completion cannot overwrite the newest started attempt.
    """

    def __init__(self, contract: dict, profile: dict, report_schema: dict,
                 producer_ref: str, generation_epoch: str, generation: int = 0):
        self.contract = deepcopy(contract)
        self.profile = deepcopy(profile)
        self.report_schema = deepcopy(report_schema)
        self.producer_ref = producer_ref
        self.generation_epoch = generation_epoch
        self.generation = generation
        self._lock = RLock()
        self._reservations: dict[str, dict] = {}
        self._reports: dict[str, dict] = {}
        self._latest_attempt: str | None = None
        self._current_id: str | None = None
        self._continuity_confirmed = True

    def begin(self, attempt_id: str, started_at: datetime) -> dict[str, Any]:
        with self._lock:
            if not self._continuity_confirmed:
                raise ValueError("Generation continuity is unknown; explicit reset/migration is required.")
            if attempt_id in self._reservations:
                raise ValueError("Attempt identity is already reserved.")
            if started_at.tzinfo is None:
                raise ValueError("started_at must be timezone-aware")
            self.generation += 1
            reservation = {
                "producer_ref": self.producer_ref,
                "subject_ref": self.profile["subject_ref"],
                "profile_ref": self.profile["id"],
                "profile_revision": self.profile["revision"],
                "generation_epoch": self.generation_epoch,
                "generation": self.generation,
                "attempt_id": attempt_id,
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
            }
            self._reservations[attempt_id] = reservation
            self._latest_attempt = attempt_id
            self._current_id = None
            return deepcopy(reservation)

    def publish(self, report: dict, evaluated_at: datetime) -> dict[str, Any]:
        with self._lock:
            evaluation = evaluate_health_evidence(report, self.contract, self.profile, self.report_schema, evaluated_at)
            if not evaluation.structurally_valid or not evaluation.semantically_valid:
                return {"published": False, "current": False, "effective_outcome": "unknown", "reason_codes": list(evaluation.reason_codes)}
            if "evidence-not-yet-published" in evaluation.reason_codes:
                return {"published": False, "current": False, "effective_outcome": "unknown", "reason_codes": list(evaluation.reason_codes)}
            if not self._continuity_confirmed:
                return {"published": False, "current": False, "effective_outcome": "unknown", "reason_codes": ["generation-epoch-mismatch"]}
            reservation = self._reservations.get(report["attempt_id"])
            if reservation is None or any(report.get(k) != v for k, v in reservation.items()):
                return {"published": False, "current": False, "effective_outcome": "unknown", "reason_codes": ["current-evidence-mismatch"]}
            if report["id"] in self._reports or any(r["attempt_id"] == report["attempt_id"] for r in self._reports.values()):
                raise ValueError("Terminal reports and attempt results are immutable.")
            # Completion is archived regardless of whether it wins current.
            self._reports[report["id"]] = deepcopy(report)
            current = report["attempt_id"] == self._latest_attempt
            if current:
                self._current_id = report["id"]
            return {"published": True, "current": current, "effective_outcome": evaluation.effective_outcome,
                    "reason_codes": list(evaluation.reason_codes)}

    def read_current(self) -> dict[str, Any] | None:
        with self._lock:
            if not self._continuity_confirmed or self._current_id is None:
                return None
            return deepcopy(health_evidence_identity(self._reports[self._current_id]))

    def decide_restore(self, expected_identity: dict, expected_context: dict,
                       evaluated_at: datetime) -> dict[str, Any]:
        """Compare current and decide under the SAME lock; never perform restore."""
        with self._lock:
            if not self._continuity_confirmed:
                return {"allowed": False, "action": "retain-guard", "effective_outcome": "unknown", "reason_codes": ["generation-epoch-mismatch"]}
            current = self.read_current()
            if current is None or current != expected_identity:
                return {"allowed": False, "action": "abort-and-reread-current-pointer", "effective_outcome": "unknown", "reason_codes": ["current-evidence-mismatch"]}
            report = self._reports[self._current_id]
            evaluation = evaluate_health_evidence(report, self.contract, self.profile, self.report_schema,
                                                  evaluated_at, expected_current_identity=expected_identity)
            allowed = restore_gate_allows(report, self.contract, self.profile, self.report_schema,
                                          evaluated_at, expected_gate_context=expected_context,
                                          expected_current_identity=expected_identity)
            reasons = list(evaluation.reason_codes)
            if report.get("gate_context") != expected_context:
                reasons.append("gate-context-mismatch")
            return {"allowed": allowed, "action": "permit-authorized-restore" if allowed else "retain-guard",
                    "effective_outcome": "unknown" if "gate-context-mismatch" in reasons else evaluation.effective_outcome,
                    "reason_codes": reasons}

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy({"generation": self.generation, "generation_epoch": self.generation_epoch,
                             "reservations": self._reservations, "reports": self._reports,
                             "latest_attempt": self._latest_attempt, "current_id": self._current_id})

    @classmethod
    def resume(cls, contract: dict, profile: dict, report_schema: dict, producer_ref: str,
               snapshot: dict, *, continuity_confirmed: bool) -> ReferencePublisher:
        """Trusted snapshot recovery is explicit; a bigger number is no proof."""
        instance = cls(contract, profile, report_schema, producer_ref, snapshot["generation_epoch"], snapshot["generation"])
        instance._reservations = deepcopy(snapshot["reservations"])
        instance._reports = deepcopy(snapshot["reports"])
        instance._latest_attempt = snapshot["latest_attempt"]
        instance._current_id = snapshot["current_id"]
        instance._continuity_confirmed = continuity_confirmed
        return instance
