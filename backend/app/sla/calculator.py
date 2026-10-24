from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from flask import has_app_context
from app.models.sla import SLAPolicy
from app.models.complaint import ComplaintCategory, ComplaintPriority

# Default fallback durations (hours) by priority if no policy matches
DEFAULT_PRIORITY_DURATIONS = {
    ComplaintPriority.CRITICAL.value: 12.0,
    ComplaintPriority.HIGH.value: 24.0,
    ComplaintPriority.MEDIUM.value: 48.0,
    ComplaintPriority.LOW.value: 72.0,
}

# Category priority baseline offsets
CATEGORY_DEFAULT_DURATIONS = {
    ComplaintCategory.DRAINAGE_FLOODING.value: 24.0,
    ComplaintCategory.WATER_SUPPLY.value: 36.0,
    ComplaintCategory.ROAD_INFRASTRUCTURE.value: 48.0,
    ComplaintCategory.SOLID_WASTE.value: 48.0,
    ComplaintCategory.STREET_LIGHTING.value: 72.0,
    ComplaintCategory.HEALTH_SANITATION.value: 36.0,
    ComplaintCategory.OTHER.value: 48.0,
}

def calculate_sla_deadline(
    category: str,
    priority: str,
    start_time: Optional[datetime] = None,
    custom_policy: Optional[SLAPolicy] = None
) -> Tuple[datetime, float, Optional[int]]:
    """
    Computes SLA resolution deadline in UTC.
    Returns: (deadline_datetime, duration_hours, policy_id)
    """
    if not start_time:
        start_time = datetime.now(timezone.utc)
    elif start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)

    policy_id = None
    duration = None

    # 1. Custom or Category-specific Active SLA Policy
    if custom_policy and custom_policy.is_active:
        duration = custom_policy.duration_hours
        policy_id = custom_policy.id
    elif has_app_context():
        try:
            # Search for exact category + priority policy in DB
            matching_policy = SLAPolicy.query.filter_by(
                category=category,
                priority=priority,
                is_active=True
            ).first()

            if not matching_policy:
                # Fallback to category-only policy
                matching_policy = SLAPolicy.query.filter_by(
                    category=category,
                    priority=None,
                    is_active=True
                ).first()

            if matching_policy:
                duration = matching_policy.duration_hours
                policy_id = matching_policy.id
        except Exception:
            pass

    if duration is None:
        # Deterministic default rule: factor both category and priority
        cat_duration = CATEGORY_DEFAULT_DURATIONS.get(category, 48.0)
        if priority == ComplaintPriority.CRITICAL.value:
            duration = min(cat_duration, 12.0)
        elif priority == ComplaintPriority.HIGH.value:
            duration = min(cat_duration, 24.0)
        elif priority == ComplaintPriority.LOW.value:
            duration = max(cat_duration, 72.0)
        else:
            duration = cat_duration

    deadline = start_time + timedelta(hours=duration)
    return deadline, duration, policy_id
