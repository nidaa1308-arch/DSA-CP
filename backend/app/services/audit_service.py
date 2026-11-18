"""
Cryptographic Tamper-Evident SHA-256 Audit & Review Ledger Service.
Guarantees append-only serialized transaction records and provides dual-chain verification.
"""

from __future__ import annotations
import datetime
import hashlib
import json
from typing import Any, Optional
from sqlalchemy.orm import Session
from ..models.database import AuditLog, ReviewDecision


def _sha256(prev_hash: str, payload: dict[str, Any]) -> str:
    """Computes SHA-256 hash chaining previous row hash with canonical JSON payload."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content = f"{prev_hash}|{serialized}".encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class AuditService:
    @staticmethod
    def get_latest_hash(db: Session, model_class: Any) -> str:
        """Fetch the row_hash of the most recent record or return 64 zeros genesis hash."""
        last_entry = db.query(model_class).order_by(model_class.timestamp.desc()).first()
        return last_entry.row_hash if last_entry and last_entry.row_hash else "0" * 64

    @classmethod
    def record_audit(
        cls,
        db: Session,
        action: str,
        user_id: str,
        user_name: str,
        details: str,
        log_type: str = "system",
        investigation_id: Optional[str] = None,
    ) -> AuditLog:
        """Atomically record an audit entry into the hash chain."""
        prev_hash = cls.get_latest_hash(db, AuditLog)
        now_ts = datetime.datetime.utcnow().isoformat() + "Z"
        log_id = f"aud-{int(datetime.datetime.utcnow().timestamp() * 1000)}"

        row_data = {
            "id": log_id,
            "investigation_id": investigation_id,
            "action": action,
            "user_id": user_id,
            "user_name": user_name,
            "details": details,
            "type": log_type,
            "timestamp": now_ts,
        }
        row_hash = _sha256(prev_hash, row_data)

        entry = AuditLog(
            id=log_id,
            investigation_id=investigation_id,
            action=action,
            user=user_name,
            user_id=user_id,
            user_name=user_name,
            details=details,
            type=log_type,
            timestamp=now_ts,
            prev_hash=prev_hash,
            row_hash=row_hash,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @classmethod
    def record_decision(
        cls,
        db: Session,
        case_id: str,
        parcel_id: str,
        decision: str,
        reviewer_id: str,
        reviewer_name: str,
        note: str,
        ai_recommendation: Optional[str] = None,
        investigation_id: Optional[str] = None,
    ) -> ReviewDecision:
        """Record an official revenue review decision into the tamper-evident review hash chain."""
        prev_hash = cls.get_latest_hash(db, ReviewDecision)
        now_ts = datetime.datetime.utcnow().isoformat() + "Z"

        # Compute next version number for this parcel
        last_version = (
            db.query(ReviewDecision.version)
            .filter(ReviewDecision.parcel_id == parcel_id)
            .order_by(ReviewDecision.version.desc())
            .first()
        )
        next_version = (last_version[0] + 1) if last_version else 1

        row_data = {
            "investigation_id": investigation_id,
            "case_id": case_id,
            "parcel_id": parcel_id,
            "decision": decision,
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "note": note,
            "ai_recommendation": ai_recommendation,
            "version": next_version,
            "timestamp": now_ts,
        }
        row_hash = _sha256(prev_hash, row_data)

        record = ReviewDecision(
            investigation_id=investigation_id,
            case_id=case_id,
            parcel_id=parcel_id,
            decision=decision,
            reviewer=reviewer_name,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            note=note,
            ai_recommendation=ai_recommendation,
            version=next_version,
            created_at=now_ts,
            timestamp=now_ts,
            prev_hash=prev_hash,
            row_hash=row_hash,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # Cross-record into system audit trail
        cls.record_audit(
            db=db,
            action=f"REVIEW_{decision.upper()}",
            user_id=reviewer_id,
            user_name=reviewer_name,
            details=f"Parcel {parcel_id}: Decision '{decision}' recorded (v{next_version}). Note: {note}",
            log_type="decision",
            investigation_id=investigation_id,
        )
        return record

    @staticmethod
    def verify_audit_chain(db: Session) -> dict[str, Any]:
        """Recompute and verify the cryptographic integrity of the audit_logs hash chain."""
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.asc()).all()
        prev_hash = "0" * 64

        for log in logs:
            row_data = {
                "id": log.id,
                "investigation_id": log.investigation_id,
                "action": log.action,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "details": log.details,
                "type": log.type,
                "timestamp": log.timestamp,
            }
            expected_hash = _sha256(prev_hash, row_data)
            if log.row_hash != expected_hash:
                return {
                    "chain_valid": False,
                    "chain_name": "audit_logs",
                    "tampered_at": log.id,
                    "total_entries": len(logs),
                }
            prev_hash = log.row_hash

        return {
            "chain_valid": True,
            "chain_name": "audit_logs",
            "tampered_at": None,
            "total_entries": len(logs),
        }

    @staticmethod
    def verify_review_chain(db: Session) -> dict[str, Any]:
        """Recompute and verify the cryptographic integrity of the review_decisions hash chain."""
        decisions = db.query(ReviewDecision).order_by(ReviewDecision.timestamp.asc()).all()
        prev_hash = "0" * 64

        for dec in decisions:
            row_data = {
                "investigation_id": dec.investigation_id,
                "case_id": dec.case_id,
                "parcel_id": dec.parcel_id,
                "decision": dec.decision,
                "reviewer_id": dec.reviewer_id,
                "reviewer_name": dec.reviewer_name,
                "note": dec.note,
                "ai_recommendation": dec.ai_recommendation,
                "version": dec.version,
                "timestamp": dec.timestamp,
            }
            expected_hash = _sha256(prev_hash, row_data)
            if dec.row_hash != expected_hash:
                return {
                    "chain_valid": False,
                    "chain_name": "review_decisions",
                    "tampered_at": dec.id,
                    "total_entries": len(decisions),
                }
            prev_hash = dec.row_hash

        return {
            "chain_valid": True,
            "chain_name": "review_decisions",
            "tampered_at": None,
            "total_entries": len(decisions),
        }
