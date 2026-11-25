from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.employee import Employee
from app.models.event import Event, EventStatus
from app.models.event_staff_assignment import EventStaffAssignment
from app.models.tenant import Tenant
from app.services import event_staff_assignments as assignment_service
from app.services.event_staff_assignments import (
    AssignmentEmployeeNotFoundError,
    AssignmentEventNotFoundError,
    EventStaffAssignmentNotFoundError,
    InvalidEventStaffAssignmentDataError,
)


def create_tenant_session(db_session, tenant_id):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_tenant(db_session, name="Workforce Assignment Test Tenant"):
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_event(db_session, tenant_id, *, status="draft"):
    client = Client(
        tenant_id=tenant_id,
        name="Test Client",
        email="client@example.com",
    )
    db_session.add(client)
    db_session.flush()
    event = Event(
        tenant_id=tenant_id,
        client_id=client.id,
        name="Corporate Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status=status,
        country="ES",
    )
    db_session.add(event)
    db_session.flush()
    return event


def create_employee(db_session, tenant_id, *, archived_at=None):
    employee = Employee(
        tenant_id=tenant_id,
        name="Maria Silva",
        employment_type="employee",
        position="Waiter",
        email="maria@example.com",
        archived_at=archived_at,
    )
    db_session.add(employee)
    db_session.flush()
    return employee


def assignment_data(event_id, employee_id, **overrides):
    data = {
        "event_id": event_id,
        "employee_id": employee_id,
        "position": "Waiter",
        "planned_hours": Decimal("5.00"),
        "compensation_type": "hourly",
        "compensation_rate": Decimal("12.50"),
        "notes": None,
    }
    data.update(overrides)
    return data


def test_create_hourly_assignment_calculates_planned_compensation(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        assert assignment.tenant_id == tenant.id
        assert assignment.status == "assigned"
        assert assignment.planned_compensation == Decimal("62.50")


def test_create_fixed_assignment_uses_fixed_rate(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db,
            data=assignment_data(
                event.id,
                employee.id,
                planned_hours=Decimal("8.00"),
                compensation_type="fixed",
                compensation_rate=Decimal("150.00"),
            ),
        )
        assert assignment.planned_compensation == Decimal("150.00")


def test_create_assignment_rejects_nonexistent_employee(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(AssignmentEmployeeNotFoundError):
            assignment_service.create_event_staff_assignment(
                tenant_db, data=assignment_data(event.id, uuid4())
            )


def test_create_assignment_rejects_employee_from_another_tenant(db_session):
    tenant = create_tenant(db_session, "Tenant A")
    other_tenant = create_tenant(db_session, "Tenant B")
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, other_tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(AssignmentEmployeeNotFoundError):
            assignment_service.create_event_staff_assignment(
                tenant_db, data=assignment_data(event.id, employee.id)
            )


def test_create_assignment_rejects_archived_employee(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id, archived_at=datetime.now(UTC))
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(AssignmentEmployeeNotFoundError):
            assignment_service.create_event_staff_assignment(
                tenant_db, data=assignment_data(event.id, employee.id)
            )


def test_create_assignment_rejects_nonexistent_event(db_session):
    tenant = create_tenant(db_session)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(AssignmentEventNotFoundError):
            assignment_service.create_event_staff_assignment(
                tenant_db, data=assignment_data(uuid4(), employee.id)
            )


@pytest.mark.parametrize("status", ["completed", "cancelled"])
def test_create_assignment_rejects_final_event_status(db_session, status):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id, status=status)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(InvalidEventStaffAssignmentDataError):
            assignment_service.create_event_staff_assignment(
                tenant_db, data=assignment_data(event.id, employee.id)
            )


def test_create_assignment_rejects_duplicate_employee(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        with pytest.raises(InvalidEventStaffAssignmentDataError):
            assignment_service.create_event_staff_assignment(
                tenant_db, data=assignment_data(event.id, employee.id)
            )


def test_get_assignment_and_list_assignments(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        created = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        found = assignment_service.get_event_staff_assignment(
            tenant_db, assignment_id=created.id
        )
        items, total = assignment_service.list_event_staff_assignments(
            tenant_db, event_id=event.id
        )
        assert found.id == created.id
        assert total == 1
        assert len(items) == 1


def test_get_nonexistent_assignment_fails(db_session):
    tenant = create_tenant(db_session)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(EventStaffAssignmentNotFoundError):
            assignment_service.get_event_staff_assignment(
                tenant_db, assignment_id=uuid4()
            )


def test_update_assignment_recalculates_hourly_compensation(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        updated = assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"planned_hours": Decimal("7.50")},
        )
        assert updated.planned_hours == Decimal("7.50")
        assert updated.planned_compensation == Decimal("93.75")


def test_update_assignment_rejects_empty_data(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        with pytest.raises(InvalidEventStaffAssignmentDataError):
            assignment_service.update_event_staff_assignment(
                tenant_db, assignment_id=assignment.id, data={}
            )


def test_assignment_status_transitions_and_completion_calculation(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        assignment = assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"status": "confirmed"},
        )
        assert assignment.status == "confirmed"
        assignment = assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"actual_hours": Decimal("6.00")},
        )
        assignment = assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"status": "completed"},
        )
        assert assignment.status == "completed"
        assert assignment.actual_compensation == Decimal("75.00")


def test_complete_assignment_requires_actual_hours(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"status": "confirmed"},
        )
        assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"status": "confirmed"},
        )
        with pytest.raises(InvalidEventStaffAssignmentDataError):
            assignment_service.update_event_staff_assignment(
                tenant_db,
                assignment_id=assignment.id,
                data={"status": "completed"},
            )


def test_update_assignment_rejects_invalid_status_transition(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        with pytest.raises(InvalidEventStaffAssignmentDataError):
            assignment_service.update_event_staff_assignment(
                tenant_db,
                assignment_id=assignment.id,
                data={"status": "completed"},
            )


def test_cancel_assignment_and_prevent_later_updates(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        assignment = assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"status": "cancelled"},
        )
        assert assignment.status == "cancelled"
        with pytest.raises(InvalidEventStaffAssignmentDataError):
            assignment_service.update_event_staff_assignment(
                tenant_db,
                assignment_id=assignment.id,
                data={"notes": "Changed after cancellation"},
            )


def test_completed_assignment_cannot_be_modified(db_session):
    tenant = create_tenant(db_session)
    event = create_event(db_session, tenant.id)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        assignment = assignment_service.create_event_staff_assignment(
            tenant_db, data=assignment_data(event.id, employee.id)
        )
        assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"status": "confirmed", "actual_hours": Decimal("5.00")},
        )
        assignment_service.update_event_staff_assignment(
            tenant_db,
            assignment_id=assignment.id,
            data={"status": "completed"},
        )
        with pytest.raises(InvalidEventStaffAssignmentDataError):
            assignment_service.update_event_staff_assignment(
                tenant_db,
                assignment_id=assignment.id,
                data={"notes": "Changed after completion"},
            )
