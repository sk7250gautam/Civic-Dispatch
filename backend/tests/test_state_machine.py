import pytest
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User, RoleEnum
from app.state_machine.transitions import ComplaintStateMachine, StateTransitionError

def test_valid_lifecycle_transitions(app):
    with app.app_context():
        citizen = User.query.filter_by(role=RoleEnum.CITIZEN.value).first()
        officer = User.query.filter_by(role=RoleEnum.FIELD_OFFICER.value).first()
        manager = User.query.filter_by(role=RoleEnum.DEPARTMENT_MANAGER.value).first()

        complaint = Complaint(
            citizen_id=citizen.id,
            title="Pothole in sector 4",
            description="Large pothole damaging cars",
            latitude=12.97,
            longitude=77.59,
            status=ComplaintStatus.SUBMITTED.value
        )
        from app.extensions import db
        db.session.add(complaint)
        db.session.commit()

        # Manager acknowledges ticket
        ComplaintStateMachine.transition(complaint, ComplaintStatus.ACKNOWLEDGED.value, manager)
        assert complaint.status == ComplaintStatus.ACKNOWLEDGED.value

        # Manager assigns ticket
        complaint.assigned_officer_id = officer.id
        ComplaintStateMachine.transition(complaint, ComplaintStatus.ASSIGNED.value, manager)
        assert complaint.status == ComplaintStatus.ASSIGNED.value

        # Officer starts work
        ComplaintStateMachine.transition(complaint, ComplaintStatus.IN_PROGRESS.value, officer)
        assert complaint.status == ComplaintStatus.IN_PROGRESS.value

        # Officer resolves ticket with mandatory summary
        ComplaintStateMachine.transition(complaint, ComplaintStatus.RESOLVED.value, officer, resolution_summary="Asphalt poured and sealed.")
        assert complaint.status == ComplaintStatus.RESOLVED.value
        assert complaint.resolution_summary == "Asphalt poured and sealed."

        # Citizen closes ticket
        ComplaintStateMachine.transition(complaint, ComplaintStatus.CLOSED.value, citizen)
        assert complaint.status == ComplaintStatus.CLOSED.value

def test_invalid_state_transition_fails(app):
    with app.app_context():
        citizen = User.query.filter_by(role=RoleEnum.CITIZEN.value).first()
        complaint = Complaint(
            citizen_id=citizen.id,
            title="Broken tap",
            description="Water leaking",
            latitude=12.97,
            longitude=77.59,
            status=ComplaintStatus.SUBMITTED.value
        )
        from app.extensions import db
        db.session.add(complaint)
        db.session.commit()

        # Cannot jump directly from SUBMITTED to RESOLVED
        with pytest.raises(StateTransitionError):
            ComplaintStateMachine.transition(complaint, ComplaintStatus.RESOLVED.value, citizen)

def test_unauthorized_role_transition_fails(app):
    with app.app_context():
        citizen = User.query.filter_by(role=RoleEnum.CITIZEN.value).first()
        complaint = Complaint(
            citizen_id=citizen.id,
            title="Streetlight out",
            description="Dark area",
            latitude=12.97,
            longitude=77.59,
            status=ComplaintStatus.SUBMITTED.value
        )
        from app.extensions import db
        db.session.add(complaint)
        db.session.commit()

        # Citizen cannot acknowledge their own ticket
        with pytest.raises(StateTransitionError):
            ComplaintStateMachine.transition(complaint, ComplaintStatus.ACKNOWLEDGED.value, citizen)
