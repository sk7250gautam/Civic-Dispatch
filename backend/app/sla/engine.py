"""
Civic Dispatch — Background SLA & Automated Escalation Engine
Scans active grievances, evaluates deadlines against elapsed time,
advances escalation tiers, and notifies responsible officers/managers.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from app.extensions import db
from app.models.complaint import Complaint, ComplaintStatus
from app.models.sla import SLAEscalationEvent
from app.models.notification import Notification, NotificationType
from app.models.user import User, RoleEnum
from app.models.audit import AuditEvent

class SLAEngine:

    @staticmethod
    def run_evaluation() -> Dict[str, Any]:
        """
        Executes a complete sweep of all unresolved grievances.
        Idempotent: will not trigger duplicate events for tickets already at target tier.
        """
        now = datetime.now(timezone.utc)
        
        # Non-terminal statuses subject to SLA tracking
        active_statuses = [
            ComplaintStatus.SUBMITTED.value,
            ComplaintStatus.ACKNOWLEDGED.value,
            ComplaintStatus.ASSIGNED.value,
            ComplaintStatus.IN_PROGRESS.value,
            ComplaintStatus.REOPENED.value,
        ]

        active_complaints = Complaint.query.filter(
            Complaint.status.in_(active_statuses),
            Complaint.sla_deadline.isnot(None)
        ).all()

        stats = {
            "evaluated_count": len(active_complaints),
            "level_1_warnings": 0,
            "level_2_breaches": 0,
            "level_3_critical_escalations": 0,
            "timestamp": now.isoformat(),
        }

        for complaint in active_complaints:
            deadline = complaint.sla_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            created = complaint.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)

            total_seconds = (deadline - created).total_seconds()
            if total_seconds <= 0:
                continue

            elapsed_seconds = (now - created).total_seconds()
            progress_ratio = elapsed_seconds / total_seconds

            # Level 3: Severe Overdue (Deadline exceeded by > 24 hours or > 1.5x total time)
            grace_seconds = 24 * 3600
            if (now > deadline + timedelta(seconds=grace_seconds) or progress_ratio >= 1.5) and complaint.current_escalation_level < 3:
                complaint.current_escalation_level = 3
                event = SLAEscalationEvent(
                    complaint_id=complaint.id,
                    escalation_level=3,
                    trigger_type="CRITICAL_OVERDUE",
                    target_role=RoleEnum.SYSTEM_ADMIN.value,
                    notes=f"Grievance severely breached SLA ({round(progress_ratio*100)}% elapsed). Escalated to Municipal Admin.",
                    created_at=now,
                )
                db.session.add(event)
                SLAEngine._notify_escalation(complaint, 3, "Municipal Leadership / Admin")
                stats["level_3_critical_escalations"] += 1

            # Level 2: Overdue SLA Breach
            elif now > deadline and complaint.current_escalation_level < 2:
                complaint.current_escalation_level = 2
                event = SLAEscalationEvent(
                    complaint_id=complaint.id,
                    escalation_level=2,
                    trigger_type="OVERDUE_BREACH",
                    target_role=RoleEnum.DEPARTMENT_MANAGER.value,
                    notes=f"Resolution deadline {deadline.isoformat()} was breached. Escalated to Department Head.",
                    created_at=now,
                )
                db.session.add(event)
                SLAEngine._notify_escalation(complaint, 2, "Department Head")
                stats["level_2_breaches"] += 1

            # Level 1: Warning threshold (75% of allowed time has elapsed)
            elif progress_ratio >= 0.75 and complaint.current_escalation_level < 1:
                complaint.current_escalation_level = 1
                event = SLAEscalationEvent(
                    complaint_id=complaint.id,
                    escalation_level=1,
                    trigger_type="WARNING_THRESHOLD",
                    target_role=RoleEnum.FIELD_OFFICER.value,
                    notes=f"75% of resolution time elapsed. Approaching deadline.",
                    created_at=now,
                )
                db.session.add(event)
                SLAEngine._notify_escalation(complaint, 1, "Assigned Field Staff")
                stats["level_1_warnings"] += 1

        db.session.commit()
        return stats

    @staticmethod
    def _notify_escalation(complaint: Complaint, level: int, target_name: str):
        """Generates notifications for escalated tickets."""
        try:
            # Notify Department Manager
            if complaint.department_id:
                managers = User.query.filter_by(
                    department_id=complaint.department_id,
                    role=RoleEnum.DEPARTMENT_MANAGER.value,
                    is_active=True
                ).all()
                for mgr in managers:
                    notif = Notification(
                        user_id=mgr.id,
                        complaint_id=complaint.id,
                        title=f"SLA Tier {level} Alert: Grievance {complaint.reference_id}",
                        message=f"Ticket '{complaint.title}' has reached Escalation Tier {level} ({target_name}). Immediate action advised.",
                        notification_type=NotificationType.SLA_BREACH.value if level >= 2 else NotificationType.SLA_WARNING.value,
                    )
                    db.session.add(notif)

            # Notify Assigned Officer
            if complaint.assigned_officer_id:
                notif = Notification(
                    user_id=complaint.assigned_officer_id,
                    complaint_id=complaint.id,
                    title=f"URGENT SLA Alert: {complaint.reference_id}",
                    message=f"Your assigned ticket '{complaint.title}' has reached Tier {level} escalation.",
                    notification_type=NotificationType.SLA_BREACH.value if level >= 2 else NotificationType.SLA_WARNING.value,
                )
                db.session.add(notif)

        except Exception:
            pass
