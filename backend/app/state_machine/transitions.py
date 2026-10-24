"""
Civic Dispatch — Deterministic Complaint State Machine
Enforces strict transitions, role authorization, and append-only audit history.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.extensions import db
from app.models.complaint import Complaint, ComplaintStatus
from app.models.history import ComplaintStatusHistory
from app.models.notification import Notification, NotificationType
from app.models.audit import AuditEvent

class StateTransitionError(Exception):
    """Raised when an invalid state transition or unauthorized transition is attempted."""
    pass

# Explicit Valid Transitions Matrix
# Current State -> Allowed Next States
VALID_TRANSITIONS = {
    ComplaintStatus.SUBMITTED.value: [
        ComplaintStatus.ACKNOWLEDGED.value,
        ComplaintStatus.ASSIGNED.value,
        ComplaintStatus.REJECTED.value,
    ],
    ComplaintStatus.ACKNOWLEDGED.value: [
        ComplaintStatus.ASSIGNED.value,
        ComplaintStatus.IN_PROGRESS.value,
        ComplaintStatus.REJECTED.value,
    ],
    ComplaintStatus.ASSIGNED.value: [
        ComplaintStatus.IN_PROGRESS.value,
        ComplaintStatus.ASSIGNED.value,  # Reassignment allowed
        ComplaintStatus.REJECTED.value,
    ],
    ComplaintStatus.IN_PROGRESS.value: [
        ComplaintStatus.RESOLVED.value,
        ComplaintStatus.ASSIGNED.value,  # Escalate/reassign while in progress
    ],
    ComplaintStatus.RESOLVED.value: [
        ComplaintStatus.CLOSED.value,
        ComplaintStatus.REOPENED.value,
    ],
    ComplaintStatus.CLOSED.value: [
        ComplaintStatus.REOPENED.value,
    ],
    ComplaintStatus.REOPENED.value: [
        ComplaintStatus.ASSIGNED.value,
        ComplaintStatus.IN_PROGRESS.value,
        ComplaintStatus.ACKNOWLEDGED.value,
    ],
    ComplaintStatus.REJECTED.value: [],  # Terminal state
}

# Role Authorization for Transitions
ROLE_TRANSITION_PERMISSIONS = {
    "CITIZEN": [
        (ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value),
        (ComplaintStatus.RESOLVED.value, ComplaintStatus.REOPENED.value),
        (ComplaintStatus.CLOSED.value, ComplaintStatus.REOPENED.value),
    ],
    "FIELD_OFFICER": [
        (ComplaintStatus.SUBMITTED.value, ComplaintStatus.ACKNOWLEDGED.value),
        (ComplaintStatus.ASSIGNED.value, ComplaintStatus.IN_PROGRESS.value),
        (ComplaintStatus.ACKNOWLEDGED.value, ComplaintStatus.IN_PROGRESS.value),
        (ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.RESOLVED.value),
    ],
    "DEPARTMENT_MANAGER": [
        (ComplaintStatus.SUBMITTED.value, ComplaintStatus.ACKNOWLEDGED.value),
        (ComplaintStatus.SUBMITTED.value, ComplaintStatus.ASSIGNED.value),
        (ComplaintStatus.SUBMITTED.value, ComplaintStatus.REJECTED.value),
        (ComplaintStatus.ACKNOWLEDGED.value, ComplaintStatus.ASSIGNED.value),
        (ComplaintStatus.ACKNOWLEDGED.value, ComplaintStatus.REJECTED.value),
        (ComplaintStatus.ASSIGNED.value, ComplaintStatus.ASSIGNED.value),  # Reassign
        (ComplaintStatus.ASSIGNED.value, ComplaintStatus.IN_PROGRESS.value),
        (ComplaintStatus.ASSIGNED.value, ComplaintStatus.REJECTED.value),
        (ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.RESOLVED.value),
        (ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.ASSIGNED.value),
        (ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value),
        (ComplaintStatus.REOPENED.value, ComplaintStatus.ASSIGNED.value),
    ],
    "SYSTEM_ADMIN": [
        # Full administrative authority over all valid transitions
        (curr, nxt) for curr, nexts in VALID_TRANSITIONS.items() for nxt in nexts
    ],
}

class ComplaintStateMachine:
    """Manages transactional state changes for a complaint."""

    @staticmethod
    def transition(
        complaint: Complaint,
        new_status: str,
        user: Any,
        reason: Optional[str] = None,
        resolution_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Complaint:
        """
        Executes a validated, atomic state transition.
        Records status history, audit log, and notifies relevant stakeholders.
        """
        current_status = complaint.status

        # 1. Check if next state is in explicit transition table
        allowed_next_states = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_next_states:
            raise StateTransitionError(
                f"Invalid state transition from '{current_status}' to '{new_status}'. Allowed next states: {allowed_next_states}"
            )

        # 2. Check Role Permissions
        user_role = getattr(user, "role", "CITIZEN")
        allowed_pairs = ROLE_TRANSITION_PERMISSIONS.get(user_role, [])
        if (current_status, new_status) not in allowed_pairs and user_role != "SYSTEM_ADMIN":
            raise StateTransitionError(
                f"Role '{user_role}' is not authorized to transition from '{current_status}' to '{new_status}'."
            )

        # 3. Relationship Check (Citizens can only transition their own complaints; Officers their assigned ones)
        if user_role == "CITIZEN":
            if complaint.citizen_id != user.id:
                raise StateTransitionError("Access denied: Citizens can only transition their own complaints.")
            if new_status == ComplaintStatus.REOPENED.value and not reason:
                raise StateTransitionError("A clear reason is required when reopening a complaint.")

        if user_role == "FIELD_OFFICER":
            if complaint.assigned_officer_id != user.id and new_status != ComplaintStatus.ACKNOWLEDGED.value:
                raise StateTransitionError("Access denied: Field officers can only update complaints assigned to them.")
            if new_status == ComplaintStatus.RESOLVED.value and not resolution_summary:
                raise StateTransitionError("A resolution summary is required when resolving a grievance.")

        if new_status == ComplaintStatus.REJECTED.value and not reason:
            raise StateTransitionError("A valid justification reason is mandatory when rejecting a grievance.")

        # 4. Perform Transition in Transaction
        now = datetime.now(timezone.utc)
        complaint.status = new_status
        complaint.updated_at = now

        if new_status == ComplaintStatus.RESOLVED.value:
            complaint.resolved_at = now
            if resolution_summary:
                complaint.resolution_summary = resolution_summary

        elif new_status == ComplaintStatus.CLOSED.value:
            complaint.closed_at = now

        elif new_status == ComplaintStatus.REOPENED.value:
            complaint.reopen_count += 1
            complaint.reopen_reason = reason
            complaint.resolved_at = None
            complaint.closed_at = None

        # 5. Append-only Status History
        meta_json_str = None
        if metadata:
            import json
            meta_json_str = json.dumps(metadata)

        history_entry = ComplaintStatusHistory(
            complaint_id=complaint.id,
            previous_status=current_status,
            new_status=new_status,
            acting_user_id=user.id,
            reason=reason or resolution_summary,
            metadata_json=meta_json_str,
            created_at=now,
        )
        db.session.add(history_entry)

        # 6. Audit Trail
        AuditEvent.log(
            action=f"STATE_TRANSITION_{current_status}_TO_{new_status}",
            entity_type="COMPLAINT",
            entity_id=complaint.id,
            actor_id=user.id,
            details={
                "reference_id": complaint.reference_id,
                "from": current_status,
                "to": new_status,
                "reason": reason or resolution_summary,
            }
        )

        # 7. Notify Stakeholders
        ComplaintStateMachine._send_transition_notifications(complaint, current_status, new_status, user)

        db.session.commit()
        return complaint

    @staticmethod
    def _send_transition_notifications(complaint: Complaint, old_status: str, new_status: str, actor: Any):
        """Dispatches in-app notifications without breaking transaction on failure."""
        try:
            # Notify Citizen
            if actor.id != complaint.citizen_id:
                citizen_notif = Notification(
                    user_id=complaint.citizen_id,
                    complaint_id=complaint.id,
                    title=f"Grievance {complaint.reference_id} status updated to {new_status}",
                    message=f"Your complaint regarding '{complaint.title}' has been moved to status: {new_status}.",
                    notification_type=NotificationType.STATUS_CHANGE.value,
                )
                db.session.add(citizen_notif)

            # Notify Officer if assigned and actor is not the officer
            if complaint.assigned_officer_id and actor.id != complaint.assigned_officer_id:
                officer_notif = Notification(
                    user_id=complaint.assigned_officer_id,
                    complaint_id=complaint.id,
                    title=f"Assigned Ticket {complaint.reference_id} moved to {new_status}",
                    message=f"Ticket '{complaint.title}' status changed by {actor.full_name} ({actor.role}).",
                    notification_type=NotificationType.STATUS_CHANGE.value,
                )
                db.session.add(officer_notif)

        except Exception as e:
            # Never let notification generation fail the primary state machine transition
            pass
