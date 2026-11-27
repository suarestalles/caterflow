
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.tenant_session import TenantSession
from app.models.client import Client
from app.models.event import Event
from app.models.financial_audit_log import FinancialAuditLog
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.financial_audit_log import (
    FinancialAuditEntityType,
    FinancialAuditLogCreate,
)
from app.services import financial_audit_logs


def create_event(
    db_session: Session,
    tenant: Tenant,
) -> Event:
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
        name="Test Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status="completed",
        country="ES",
    )
    db_session.add(event)
    db_session.flush()

    return event


def create_tenant_session(
    db_session: Session,
    tenant_id,
) -> TenantSession:
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_audit_data(
    *,
    event_id=None,
    entity_id=None,
    field_name="amount",
    old_value="100.00",
    new_value="120.00",
    reason="Correction after event completion.",
):
    return FinancialAuditLogCreate(
        event_id=event_id,
        entity_type=FinancialAuditEntityType.EXPENSE,
        entity_id=entity_id or uuid4(),
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
    )


def test_record_financial_audit_log(db_session):
    tenant = Tenant(name="Test Tenant")
    user = User(
        full_name="Test User",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    db_session.add_all([tenant, user])
    db_session.flush()

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        entity_id = uuid4()

        audit_log = financial_audit_logs.record(
            tenant_db,
            create_audit_data(
                entity_id=entity_id,
                old_value="100.00",
                new_value="150.00",
            ),
            user.id,
        )

        assert audit_log.id is not None
        assert audit_log.tenant_id == tenant.id
        assert audit_log.entity_type == "expense"
        assert audit_log.entity_id == entity_id
        assert audit_log.field_name == "amount"
        assert audit_log.old_value == "100.00"
        assert audit_log.new_value == "150.00"
        assert audit_log.reason == "Correction after event completion."
        assert audit_log.recorded_by_user_id == user.id
    finally:
        tenant_db.close()


@pytest.mark.parametrize(
    "reason",
    [
        "",
        " ",
        "   ",
    ],
)
def test_record_rejects_empty_reason(db_session, reason):
    tenant = Tenant(name="Test Tenant")
    user = User(
        full_name="Test User",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    db_session.add_all([tenant, user])
    db_session.flush()

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(HTTPException) as exc_info:
            financial_audit_logs.record(
                tenant_db,
                create_audit_data(reason=reason),
                user.id,
            )

        assert exc_info.value.status_code == 422
    finally:
        tenant_db.close()


def test_record_rejects_empty_field_name(db_session):
    tenant = Tenant(name="Test Tenant")
    user = User(
        full_name="Test User",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    db_session.add_all([tenant, user])
    db_session.flush()

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        with pytest.raises(HTTPException) as exc_info:
            financial_audit_logs.record(
                tenant_db,
                create_audit_data(field_name="   "),
                user.id,
            )

        assert exc_info.value.status_code == 422
    finally:
        tenant_db.close()


def test_list_financial_audit_logs_by_entity(db_session):
    tenant = Tenant(name="Test Tenant")
    user = User(
        full_name="Test User",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    db_session.add_all([tenant, user])
    db_session.flush()

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        entity_id = uuid4()

        first = financial_audit_logs.record(
            tenant_db,
            create_audit_data(
                entity_id=entity_id,
                field_name="amount",
            ),
            user.id,
        )

        second = financial_audit_logs.record(
            tenant_db,
            create_audit_data(
                entity_id=entity_id,
                field_name="description",
                old_value="Old description",
                new_value="New description",
            ),
            user.id,
        )

        results = financial_audit_logs.list_by_entity(
            tenant_db,
            FinancialAuditEntityType.EXPENSE,
            entity_id,
        )

        assert len(results) == 2
        assert {item.id for item in results} == {first.id, second.id}
    finally:
        tenant_db.close()


def test_list_financial_audit_logs_by_event(db_session):
    tenant = Tenant(name="Test Tenant")
    user = User(
        full_name="Test User",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    db_session.add_all([tenant, user])
    db_session.flush()

    event = create_event(db_session, tenant)
    other_event = create_event(db_session, tenant)

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        first = financial_audit_logs.record(
            tenant_db,
            create_audit_data(event_id=event.id),
            user.id,
        )

        second = financial_audit_logs.record(
            tenant_db,
            create_audit_data(
                event_id=event.id,
                field_name="actual_compensation",
            ),
            user.id,
        )

        financial_audit_logs.record(
            tenant_db,
            create_audit_data(event_id=other_event.id),
            user.id,
        )

        results = financial_audit_logs.list_by_event_id(
            tenant_db,
            event.id,
        )

        assert len(results) == 2
        assert {item.id for item in results} == {first.id, second.id}
        assert all(item.event_id == event.id for item in results)
    finally:
        tenant_db.close()


def test_financial_audit_logs_are_isolated_by_tenant(db_session):
    tenant_a = Tenant(name="Tenant A")
    tenant_b = Tenant(name="Tenant B")

    user_a = User(
        full_name="User A",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )
    user_b = User(
        full_name="User B",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    db_session.add_all([tenant_a, tenant_b, user_a, user_b])
    db_session.flush()

    entity_id = uuid4()

    tenant_a_db = create_tenant_session(db_session, tenant_a.id)

    try:
        audit_a = financial_audit_logs.record(
            tenant_a_db,
            create_audit_data(entity_id=entity_id),
            user_a.id,
        )

        results_a = financial_audit_logs.list_by_entity(
            tenant_a_db,
            FinancialAuditEntityType.EXPENSE,
            entity_id,
        )

        assert len(results_a) == 1
        assert results_a[0].id == audit_a.id
        assert results_a[0].tenant_id == tenant_a.id
    finally:
        tenant_a_db.close()

    tenant_b_db = create_tenant_session(db_session, tenant_b.id)

    try:
        audit_b = financial_audit_logs.record(
            tenant_b_db,
            create_audit_data(entity_id=entity_id),
            user_b.id,
        )

        results_b = financial_audit_logs.list_by_entity(
            tenant_b_db,
            FinancialAuditEntityType.EXPENSE,
            entity_id,
        )

        assert len(results_b) == 1
        assert results_b[0].id == audit_b.id
        assert results_b[0].tenant_id == tenant_b.id
    finally:
        tenant_b_db.close()


def test_record_does_not_commit_transaction(db_session):
    tenant = Tenant(name="Test Tenant")
    user = User(
        full_name="Test User",
        email=f"{uuid4()}@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )

    db_session.add_all([tenant, user])
    db_session.flush()

    tenant_db = create_tenant_session(db_session, tenant.id)

    try:
        audit_log = financial_audit_logs.record(
            tenant_db,
            create_audit_data(),
            user.id,
        )

        assert tenant_db.in_transaction()

        audit_log_id = audit_log.id

        tenant_db.rollback()

        persisted = db_session.scalar(
            select(FinancialAuditLog).where(
                FinancialAuditLog.id == audit_log_id,
            )
        )

        assert persisted is None
    finally:
        tenant_db.close()
