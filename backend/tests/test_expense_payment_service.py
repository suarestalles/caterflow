
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.db.tenant_session import TenantSession
from app.models.payment import PaymentMethod
from app.schemas.expense import ExpenseCreate, ExpensePaymentStatus
from app.schemas.expense_payment import ExpensePaymentCreate
from app.services import expenses as expense_service
from app.services import expense_payments as payment_service


@pytest.fixture
def tenant_db(db_session, tenant_factory):
    tenant = tenant_factory()

    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant.id,
    )


@pytest.fixture
def recorder(user_factory):
    return user_factory()


@pytest.fixture
def expense(tenant_db, recorder):
    return expense_service.create(
        tenant_db,
        ExpenseCreate(
            category="food",
            description="Food supplies",
            amount=Decimal("300.00"),
            incurred_at=date(2026, 11, 27),
        ),
        recorder.id,
    )


def make_payment_data(expense_id, amount):
    return ExpensePaymentCreate(
        expense_id=expense_id,
        amount=Decimal(amount),
        paid_at=datetime.now(timezone.utc),
        method=PaymentMethod.CASH,
    )


def test_create_expense_payment_returns_created_payment(
    tenant_db,
    recorder,
    expense,
):
    payment = payment_service.create(
        tenant_db,
        make_payment_data(expense.id, "100.00"),
        recorder.id,
    )

    assert payment.id is not None
    assert payment.expense_id == expense.id
    assert payment.amount == Decimal("100.00")
    assert payment.recorded_by_user_id == recorder.id


def test_create_partial_payments(
    tenant_db,
    recorder,
    expense,
):
    first = payment_service.create(
        tenant_db,
        make_payment_data(expense.id, "100.00"),
        recorder.id,
    )

    second = payment_service.create(
        tenant_db,
        make_payment_data(expense.id, "150.00"),
        recorder.id,
    )

    assert first.amount == Decimal("100.00")
    assert second.amount == Decimal("150.00")

    balance = payment_service.get_balance(
        tenant_db,
        expense.id,
    )

    assert balance["total_paid"] == Decimal("250.00")
    assert balance["outstanding"] == Decimal("50.00")
    assert balance["status"] == ExpensePaymentStatus.PARTIALLY_PAID


def test_create_payment_that_fully_pays_expense(
    tenant_db,
    recorder,
    expense,
):
    payment_service.create(
        tenant_db,
        make_payment_data(expense.id, "300.00"),
        recorder.id,
    )

    balance = payment_service.get_balance(
        tenant_db,
        expense.id,
    )

    assert balance["total_paid"] == Decimal("300.00")
    assert balance["outstanding"] == Decimal("0.00")
    assert balance["status"] == ExpensePaymentStatus.PAID


def test_create_payment_rejects_amount_above_outstanding(
    tenant_db,
    recorder,
    expense,
):
    with pytest.raises(HTTPException) as exc:
        payment_service.create(
            tenant_db,
            make_payment_data(expense.id, "350.00"),
            recorder.id,
        )

    assert exc.value.status_code == 409


def test_create_payment_rejects_payment_after_fully_paid(
    tenant_db,
    recorder,
    expense,
):
    payment_service.create(
        tenant_db,
        make_payment_data(expense.id, "300.00"),
        recorder.id,
    )

    with pytest.raises(HTTPException) as exc:
        payment_service.create(
            tenant_db,
            make_payment_data(expense.id, "10.00"),
            recorder.id,
        )

    assert exc.value.status_code == 409


def test_create_payment_returns_404_when_expense_not_found(
    tenant_db,
    recorder,
):
    from uuid import uuid4

    with pytest.raises(HTTPException) as exc:
        payment_service.create(
            tenant_db,
            make_payment_data(uuid4(), "50.00"),
            recorder.id,
        )

    assert exc.value.status_code == 404


def test_list_payments_returns_expense_payments(
    tenant_db,
    recorder,
    expense,
):
    payment_service.create(
        tenant_db,
        make_payment_data(expense.id, "100.00"),
        recorder.id,
    )

    payments = payment_service.list_by_expense_id(
        tenant_db,
        expense.id,
    )

    assert len(payments) == 1
    assert payments[0].expense_id == expense.id


def test_get_payment_returns_404_when_not_found(tenant_db):
    from uuid import uuid4

    with pytest.raises(HTTPException) as exc:
        payment_service.get(tenant_db, uuid4())

    assert exc.value.status_code == 404
