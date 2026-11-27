
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.employee import Employee
from app.models.employee_compensation_payment import (
    EmployeeCompensationPayment,
)
from app.models.event import Event
from app.models.event_staff_assignment import EventStaffAssignment
from app.models.payment import PaymentMethod
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.employee_compensation_payment import (
    EmployeeCompensationPaymentCreate,
)
from app.services import employee_compensation_payments as payment_service


def create_tenant_session(db_session, tenant_id):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_assignment(
    db_session,
    tenant,
    *,
    status="completed",
    actual_compensation=Decimal("120.00"),
):
    client = Client(
        tenant_id=tenant.id,
        name="Test Client",
        email=f"{uuid4()}@example.com",
    )
    db_session.add(client)
    db_session.flush()

    event = Event(
        tenant_id=tenant.id,
        client_id=client.id,
        name="Corporate Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status="completed",
        country="ES",
    )
    db_session.add(event)
    db_session.flush()

    employee = Employee(
        tenant_id=tenant.id,
        name="Maria Silva",
        employment_type="employee",
        position="Waiter",
    )
    db_session.add(employee)
    db_session.flush()

    assignment = EventStaffAssignment(
        tenant_id=tenant.id,
        event_id=event.id,
        employee_id=employee.id,
        position="Waiter",
        status=status,
        planned_hours=Decimal("5.00"),
        actual_hours=Decimal("6.00"),
        compensation_type="hourly",
        compensation_rate=Decimal("20.00"),
        planned_compensation=Decimal("100.00"),
        actual_compensation=actual_compensation,
    )
    db_session.add(assignment)
    db_session.flush()

    return assignment


def create_payment_data(
    assignment_id,
    amount="50.00",
):
    return EmployeeCompensationPaymentCreate(
        assignment_id=assignment_id,
        amount=Decimal(amount),
        paid_at=datetime.now(UTC),
        method=PaymentMethod.CASH,
        notes="Test compensation payment",
    )


def create_recorder(db_session):
    user = User(
        full_name="Finance User",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_create_employee_compensation_payment(db_session):
    tenant = Tenant(name="Compensation Test Tenant")
    db_session.add(tenant)
    db_session.flush()

    assignment = create_assignment(db_session, tenant)
    user = create_recorder(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        payment = payment_service.create_employee_compensation_payment(
            tenant_db,
            create_payment_data(assignment.id, "50.00"),
            user.id,
        )

        assert payment.id is not None
        assert payment.tenant_id == tenant.id
        assert payment.assignment_id == assignment.id
        assert payment.amount == Decimal("50.00")
        assert payment.payment_method == PaymentMethod.CASH.value
        assert payment.recorded_by_user_id == user.id


def test_register_multiple_partial_payments_and_calculate_balance(
    db_session,
):
    tenant = Tenant(name="Partial Payments Tenant")
    db_session.add(tenant)
    db_session.flush()

    assignment = create_assignment(db_session, tenant)
    user = create_recorder(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        first = payment_service.create_employee_compensation_payment(
            tenant_db,
            create_payment_data(assignment.id, "70.00"),
            user.id,
        )

        first_balance = payment_service.get_employee_compensation_balance(
            tenant_db,
            assignment.id,
        )

        assert first_balance.compensation_due == Decimal("120.00")
        assert first_balance.total_paid == Decimal("70.00")
        assert first_balance.outstanding == Decimal("50.00")
        assert first_balance.status == "partially_paid"

        second = payment_service.create_employee_compensation_payment(
            tenant_db,
            create_payment_data(assignment.id, "30.00"),
            user.id,
        )

        second_balance = payment_service.get_employee_compensation_balance(
            tenant_db,
            assignment.id,
        )

        assert second_balance.total_paid == Decimal("100.00")
        assert second_balance.outstanding == Decimal("20.00")
        assert second_balance.status == "partially_paid"

        third = payment_service.create_employee_compensation_payment(
            tenant_db,
            create_payment_data(assignment.id, "20.00"),
            user.id,
        )

        final_balance = payment_service.get_employee_compensation_balance(
            tenant_db,
            assignment.id,
        )

        assert final_balance.total_paid == Decimal("120.00")
        assert final_balance.outstanding == Decimal("0.00")
        assert final_balance.status == "paid"

        payments = payment_service.list_employee_compensation_payments(
            tenant_db,
            assignment.id,
        )

        assert len(payments) == 3
        assert {payment.id for payment in payments} == {
            first.id,
            second.id,
            third.id,
        }


def test_balance_is_pending_before_any_payment(db_session):
    tenant = Tenant(name="Pending Compensation Tenant")
    db_session.add(tenant)
    db_session.flush()

    assignment = create_assignment(db_session, tenant)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        balance = payment_service.get_employee_compensation_balance(
            tenant_db,
            assignment.id,
        )

        assert balance.compensation_due == Decimal("120.00")
        assert balance.total_paid == Decimal("0")
        assert balance.outstanding == Decimal("120.00")
        assert balance.status == "pending"


def test_reject_payment_above_outstanding_balance(db_session):
    tenant = Tenant(name="Excess Payment Tenant")
    db_session.add(tenant)
    db_session.flush()

    assignment = create_assignment(db_session, tenant)
    user = create_recorder(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(HTTPException) as exc_info:
            payment_service.create_employee_compensation_payment(
                tenant_db,
                create_payment_data(assignment.id, "120.01"),
                user.id,
            )

        assert exc_info.value.status_code == 409


def test_reject_payment_when_balance_is_already_paid(db_session):
    tenant = Tenant(name="Fully Paid Tenant")
    db_session.add(tenant)
    db_session.flush()

    assignment = create_assignment(db_session, tenant)
    user = create_recorder(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        payment_service.create_employee_compensation_payment(
            tenant_db,
            create_payment_data(assignment.id, "120.00"),
            user.id,
        )

        with pytest.raises(HTTPException) as exc_info:
            payment_service.create_employee_compensation_payment(
                tenant_db,
                create_payment_data(assignment.id, "1.00"),
                user.id,
            )

        assert exc_info.value.status_code == 409


def test_reject_payment_for_assignment_not_completed(db_session):
    tenant = Tenant(name="Incomplete Assignment Tenant")
    db_session.add(tenant)
    db_session.flush()

    assignment = create_assignment(
        db_session,
        tenant,
        status="confirmed",
    )
    user = create_recorder(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(HTTPException) as exc_info:
            payment_service.create_employee_compensation_payment(
                tenant_db,
                create_payment_data(assignment.id),
                user.id,
            )

        assert exc_info.value.status_code == 409


def test_reject_payment_when_actual_compensation_is_missing(db_session):
    tenant = Tenant(name="Missing Compensation Tenant")
    db_session.add(tenant)
    db_session.flush()

    assignment = create_assignment(
        db_session,
        tenant,
        actual_compensation=None,
    )
    user = create_recorder(db_session)

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(HTTPException) as exc_info:
            payment_service.create_employee_compensation_payment(
                tenant_db,
                create_payment_data(assignment.id),
                user.id,
            )

        assert exc_info.value.status_code == 409


def test_assignment_from_another_tenant_is_not_accessible(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")
    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    assignment_b = create_assignment(db_session, tenant_b)
    user = create_recorder(db_session)

    with create_tenant_session(db_session, tenant_a.id) as tenant_db:
        with pytest.raises(HTTPException) as exc_info:
            payment_service.create_employee_compensation_payment(
                tenant_db,
                create_payment_data(assignment_b.id),
                user.id,
            )

        assert exc_info.value.status_code == 404


def test_get_nonexistent_compensation_payment(db_session):
    tenant = Tenant(name="Payment Lookup Tenant")
    db_session.add(tenant)
    db_session.flush()

    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(HTTPException) as exc_info:
            payment_service.get_employee_compensation_payment(
                tenant_db,
                uuid4(),
            )

        assert exc_info.value.status_code == 404
