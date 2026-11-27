
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.db.tenant_session import TenantSession
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services import expenses as expense_service


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
def expense_data():
    return ExpenseCreate(
        category="food",
        description="Food supplies",
        amount=Decimal("300.00"),
        incurred_at=date(2026, 11, 27),
        supplier_name="Local Supplier",
    )


def test_create_expense_returns_created_expense(
    tenant_db,
    recorder,
    expense_data,
):
    expense = expense_service.create(
        tenant_db,
        expense_data,
        recorder.id,
    )

    assert expense.id is not None
    assert expense.amount == Decimal("300.00")
    assert expense.category == "food"
    assert expense.recorded_by_user_id == recorder.id


def test_get_expense_returns_existing_expense(
    tenant_db,
    recorder,
    expense_data,
):
    created = expense_service.create(
        tenant_db,
        expense_data,
        recorder.id,
    )

    expense = expense_service.get(tenant_db, created.id)

    assert expense.id == created.id


def test_get_expense_returns_404_when_not_found(tenant_db):
    from uuid import uuid4

    with pytest.raises(HTTPException) as exc:
        expense_service.get(tenant_db, uuid4())

    assert exc.value.status_code == 404


def test_list_expenses_returns_records_and_total(
    tenant_db,
    recorder,
    expense_data,
):
    expense_service.create(tenant_db, expense_data, recorder.id)

    expenses, total = expense_service.list_all(tenant_db)

    assert len(expenses) == 1
    assert total == 1


def test_update_expense_changes_fields(
    tenant_db,
    recorder,
    expense_data,
):
    created = expense_service.create(
        tenant_db,
        expense_data,
        recorder.id,
    )

    updated = expense_service.update(
        tenant_db,
        created.id,
        ExpenseUpdate(
            description="Updated food supplies",
            amount=Decimal("350.00"),
        ),
    )

    assert updated.description == "Updated food supplies"
    assert updated.amount == Decimal("350.00")


def test_update_expense_returns_404_when_not_found(tenant_db):
    from uuid import uuid4

    with pytest.raises(HTTPException) as exc:
        expense_service.update(
            tenant_db,
            uuid4(),
            ExpenseUpdate(description="Updated"),
        )

    assert exc.value.status_code == 404


def test_expense_balance_starts_as_pending(
    tenant_db,
    recorder,
    expense_data,
):
    expense = expense_service.create(
        tenant_db,
        expense_data,
        recorder.id,
    )

    balance = expense_service.get_balance(tenant_db, expense.id)

    assert balance["expense_amount"] == Decimal("300.00")
    assert balance["total_paid"] == Decimal("0")
    assert balance["outstanding"] == Decimal("300.00")
    assert balance["status"] == "pending"
