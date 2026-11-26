
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import AuthContext, get_auth_context, get_current_tenant_db
from app.core.permissions import PermissionCode
from app.db.tenant_session import TenantSession
from app.main import app
from app.models.client import Client
from app.models.event import Event
from app.models.membership import Membership
from app.models.membership_role import MembershipRole
from app.models.payment_installment import InstallmentStatus, PaymentInstallment
from app.models.payment_schedule import PaymentSchedule, PaymentScheduleStatus
from app.models.permission import Permission
from app.models.product import Product, ProductType
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant
from app.models.user import User


def create_tenant(db_session: Session) -> Tenant:
    tenant = Tenant(name="Payments Test Tenant")
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_user(db_session: Session) -> User:
    user = User(
        full_name="Payments Test User",
        email="payments@example.com",
        password_hash="test-password-hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def assign_permissions(
    db_session: Session,
    *,
    tenant: Tenant,
    membership: Membership,
    permission_codes: list[PermissionCode],
) -> None:
    role = Role(
        tenant_id=tenant.id,
        name="Payments Test Role",
        is_system=False,
    )
    db_session.add(role)
    db_session.flush()

    db_session.add(
        MembershipRole(
            tenant_id=tenant.id,
            membership_id=membership.id,
            role_id=role.id,
        )
    )

    for permission_code in permission_codes:
        code = permission_code.value
        permission = db_session.scalar(
            select(Permission).where(Permission.code == code)
        )

        if permission is None:
            permission = Permission(
                code=code,
                description=f"Permission {code}",
            )
            db_session.add(permission)
            db_session.flush()

        db_session.add(
            RolePermission(
                tenant_id=tenant.id,
                role_id=role.id,
                permission_id=permission.id,
            )
        )

    db_session.flush()

def create_payment_schedule(
    client,
    db_session,
    tenant,
):
    event, quote = create_payment_context(db_session, tenant)

    response = client.post(
        "/api/v1/payments/schedules",
        json=create_schedule_payload(event.id, quote.id),
    )

    assert response.status_code == 201

    return event, response.json()


def api_client_factory(
    db_session: Session,
    permissions: list[PermissionCode] | None = None,
):
    tenant = create_tenant(db_session)
    user = create_user(db_session)

    membership = Membership(
        user_id=user.id,
        tenant_id=tenant.id,
    )
    db_session.add(membership)
    db_session.flush()

    assign_permissions(
        db_session,
        tenant=tenant,
        membership=membership,
        permission_codes=permissions or [],
    )

    def override_auth_context():
        return AuthContext(user=user, tenant_id=tenant.id)

    def override_tenant_db():
        tenant_db = TenantSession(
            bind=db_session.connection(),
            join_transaction_mode="create_savepoint",
            tenant_id=tenant.id,
        )
        try:
            yield tenant_db
        finally:
            tenant_db.close()

    app.dependency_overrides[get_auth_context] = override_auth_context
    app.dependency_overrides[get_current_tenant_db] = override_tenant_db

    return TestClient(app), tenant, user


def create_client_for_tenant(
    db_session: Session,
    tenant: Tenant,
) -> Client:
    client = Client(
        tenant_id=tenant.id,
        name="Payments Test Client",
        email="payments-client@example.com",
    )
    db_session.add(client)
    db_session.flush()
    return client


def create_event_for_tenant(
    db_session: Session,
    tenant: Tenant,
    client: Client,
) -> Event:
    event = Event(
        tenant_id=tenant.id,
        client_id=client.id,
        name="Payments Test Event",
        starts_at=datetime(2026, 12, 15, 18, tzinfo=UTC),
        ends_at=datetime(2026, 12, 15, 23, tzinfo=UTC),
        guest_count=100,
        status="draft",
        country="ES",
    )
    db_session.add(event)
    db_session.flush()
    return event


def create_product_for_tenant(
    db_session: Session,
    tenant: Tenant,
) -> Product:
    product = Product(
        tenant_id=tenant.id,
        name="Catering Service",
        description="Catering service for event",
        type=ProductType.SERVICE.value,
        unit="service",
        sale_price=Decimal("100.00"),
        cost_price=Decimal("50.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    return product


def create_accepted_quote(
    db_session: Session,
    tenant: Tenant,
    client: Client,
    event: Event,
    product: Product,
):
    from app.db.tenant_session import TenantSession
    from app.models.quote import QuoteStatus
    from app.services.quotes import create_quote

    tenant_db = TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant.id,
    )

    try:
        quote = create_quote(
            tenant_db,
            data={
                "client_id": client.id,
                "event_id": event.id,
                "title": "Corporate Catering Quote",
                "items": [
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "description": "Corporate catering",
                        "quantity": Decimal("100"),
                        "unit_price": Decimal("20.00"),
                    }
                ],
            },
        )

        quote.status = QuoteStatus.ACCEPTED

        tenant_db.commit()
        tenant_db.refresh(quote)

        assert (
            getattr(quote.status, "value", quote.status)
            == "accepted"
        )

        return quote

    finally:
        tenant_db.close()


@pytest.fixture
def api_client(db_session):
    client, tenant, user = api_client_factory(
        db_session,
        permissions=[
            PermissionCode.PAYMENTS_READ,
            PermissionCode.PAYMENTS_CREATE,
            PermissionCode.PAYMENTS_REFUND,
            PermissionCode.PAYMENTS_ADJUST,
        ],
    )

    try:
        yield client, tenant, user
    finally:
        app.dependency_overrides.clear()


def create_schedule_payload(event_id, quote_id):
    return {
        "event_id": str(event_id),
        "quote_id": str(quote_id),
        "total_amount": "1000.00",
        "currency": "EUR",
        "payment_terms_snapshot": "50% upfront and 50% before the event",
        "installments": [
            {
                "installment_number": 1,
                "installment_type": "percentage",
                "percentage": "50.00",
                "due_date": "2026-12-01",
            },
            {
                "installment_number": 2,
                "installment_type": "percentage",
                "percentage": "50.00",
                "due_date": "2026-12-10",
            },
        ],
    }


def create_payment_context(db_session: Session, tenant: Tenant):
    client = create_client_for_tenant(db_session, tenant)
    event = create_event_for_tenant(db_session, tenant, client)
    product = create_product_for_tenant(db_session, tenant)
    quote = create_accepted_quote(
        db_session,
        tenant,
        client,
        event,
        product,
    )
    return event, quote


def test_create_payment_schedule_returns_201(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event, quote = create_payment_context(db_session, tenant)

    with client:
        response = client.post(
            "/api/v1/payments/schedules",
            json=create_schedule_payload(event.id, quote.id),
        )

    assert response.status_code == 201
    body = response.json()

    assert body["event_id"] == str(event.id)
    assert body["quote_id"] == str(quote.id)
    assert body["total_amount"] == "1000.00"
    assert body["currency"] == "EUR"
    assert len(body["installments"]) == 2

    assert body["installments"][0]["amount"] == "500.00"
    assert body["installments"][1]["amount"] == "500.00"


def test_create_payment_schedule_without_permission_returns_403(
    db_session,
):
    client, tenant, _ = api_client_factory(
        db_session,
        permissions=[PermissionCode.PAYMENTS_READ],
    )

    try:
        event, quote = create_payment_context(db_session, tenant)

        with client:
            response = client.post(
                "/api/v1/payments/schedules",
                json=create_schedule_payload(event.id, quote.id),
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions."
    finally:
        app.dependency_overrides.clear()


def test_get_payment_schedule_by_event_returns_200(
    db_session,
    api_client,
):
    client, tenant, _ = api_client
    event, quote = create_payment_context(db_session, tenant)

    with client:
        create_response = client.post(
            "/api/v1/payments/schedules",
            json=create_schedule_payload(event.id, quote.id),
        )
        assert create_response.status_code == 201

        response = client.get(
            f"/api/v1/payments/events/{event.id}/schedule"
        )

    assert response.status_code == 200
    assert response.json()["event_id"] == str(event.id)


def test_get_payment_schedule_from_another_tenant_returns_404(
    db_session,
    api_client,
):
    client, _, _ = api_client

    other_tenant = create_tenant(db_session)
    event, quote = create_payment_context(db_session, other_tenant)

    # Cria o cronograma no contexto do tenant proprietário.
    from app.db.tenant_session import TenantSession
    from app.schemas.payment_schedule import PaymentScheduleCreate
    from app.services.payment_schedules import create_payment_schedule

    tenant_db = TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=other_tenant.id,
    )

    try:
        create_payment_schedule(
            tenant_db,
            PaymentScheduleCreate(
                **create_schedule_payload(event.id, quote.id)
            ),
        )
    finally:
        tenant_db.close()

    with client:
        response = client.get(
            f"/api/v1/payments/events/{event.id}/schedule"
        )

    assert response.status_code == 404


def test_create_partial_payment_returns_201(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    _, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    installment = schedule["installments"][0]

    response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert response.status_code == 201
    assert response.json()["amount"] == "200.00"
    assert response.json()["installment_id"] == installment["id"]

    schedule_response = client.get(
        f"/api/v1/payments/schedules/{schedule['id']}"
    )

    assert schedule_response.status_code == 200

    updated_installment = next(
        item
        for item in schedule_response.json()["installments"]
        if item["id"] == installment["id"]
    )

    assert updated_installment["status"] == "partially_paid"


def test_complete_installment_with_multiple_payments(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    _, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    installment = schedule["installments"][0]

    first_payment = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert first_payment.status_code == 201

    second_payment = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "300.00",
            "received_at": "2026-11-25T11:00:00Z",
            "method": "cash",
        },
    )

    assert second_payment.status_code == 201

    schedule_response = client.get(
        f"/api/v1/payments/schedules/{schedule['id']}"
    )

    assert schedule_response.status_code == 200

    updated_installment = next(
        item
        for item in schedule_response.json()["installments"]
        if item["id"] == installment["id"]
    )

    assert updated_installment["status"] == "paid"


def test_create_payment_above_outstanding_balance_returns_409(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    _, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    installment = schedule["installments"][0]

    first_payment = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert first_payment.status_code == 201

    response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "300.01",
            "received_at": "2026-11-25T11:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert response.status_code == 409



def test_create_and_process_refund_returns_completed_status(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    _, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )
    installment = schedule["installments"][0]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert payment_response.status_code == 201
    payment_id = payment_response.json()["id"]

    refund_response = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment_id,
            "amount": "50.00",
            "refund_method": "bank_transfer",
            "reason": "Partial refund requested by client",
        },
    )

    assert refund_response.status_code == 201

    refund = refund_response.json()

    assert refund["payment_id"] == payment_id
    assert refund["amount"] == "50.00"
    assert refund["status"] == "pending"
    assert refund["processed_by_user_id"] is None
    assert refund["financial_adjustment_id"] is None

    process_response = client.post(
        f"/api/v1/payments/refunds/{refund['id']}/process"
    )

    assert process_response.status_code == 200

    processed_refund = process_response.json()

    assert processed_refund["status"] == "completed"
    assert processed_refund["processed_by_user_id"] is not None
    assert processed_refund["refunded_at"] is not None


def test_cancel_refund_returns_cancelled_status(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    _, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )
    installment = schedule["installments"][0]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "cash",
        },
    )

    assert payment_response.status_code == 201

    refund_response = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment_response.json()["id"],
            "amount": "80.00",
            "refund_method": "cash",
            "reason": "Refund cancelled by request",
        },
    )

    assert refund_response.status_code == 201

    refund_id = refund_response.json()["id"]

    cancel_response = client.post(
        f"/api/v1/payments/refunds/{refund_id}/cancel"
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"
    assert cancel_response.json()["refunded_at"] is None
    assert cancel_response.json()["processed_by_user_id"] is None


def test_cancelled_refund_does_not_block_new_refund(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    _, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )
    installment = schedule["installments"][0]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    payment_id = payment_response.json()["id"]

    first_refund = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment_id,
            "amount": "150.00",
            "refund_method": "bank_transfer",
            "reason": "First refund",
        },
    )

    assert first_refund.status_code == 201

    cancel_response = client.post(
        f"/api/v1/payments/refunds/{first_refund.json()['id']}/cancel"
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    second_refund = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment_id,
            "amount": "200.00",
            "refund_method": "bank_transfer",
            "reason": "Replacement refund",
        },
    )

    assert second_refund.status_code == 201
    assert second_refund.json()["status"] == "pending"


def test_refund_cannot_exceed_original_payment_amount(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    _, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )
    installment = schedule["installments"][0]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    payment_id = payment_response.json()["id"]

    refund_response = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment_id,
            "amount": "200.01",
            "refund_method": "bank_transfer",
            "reason": "Exceeds original payment",
        },
    )

    assert refund_response.status_code == 409


def test_pending_refund_reserves_original_payment_balance(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    _, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )
    installment = schedule["installments"][0]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    payment_id = payment_response.json()["id"]

    first_refund = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment_id,
            "amount": "150.00",
            "refund_method": "bank_transfer",
            "reason": "First pending refund",
        },
    )

    assert first_refund.status_code == 201

    second_refund = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment_id,
            "amount": "60.00",
            "refund_method": "bank_transfer",
            "reason": "Exceeds remaining refundable amount",
        },
    )

    assert second_refund.status_code == 409


def test_create_additional_charge_creates_new_installment(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    event, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    original_installment = schedule["installments"][0]

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "additional",
            "amount": "150.00",
            "reason": "Additional catering services",
            "due_date": "2027-01-15",
        },
    )

    assert response.status_code == 201, response.text

    adjustment = response.json()

    assert adjustment["adjustment_type"] == "additional"
    assert adjustment["amount"] == "150.00"
    assert adjustment["created_installment_id"] is not None
    assert adjustment["allocations"] == []

    schedule_response = client.get(
        f"/api/v1/payments/schedules/{schedule['id']}"
    )

    assert schedule_response.status_code == 200

    updated_installments = schedule_response.json()["installments"]

    assert len(updated_installments) == 3

    original = next(
        item
        for item in updated_installments
        if item["id"] == original_installment["id"]
    )

    additional = next(
        item
        for item in updated_installments
        if item["id"] == adjustment["created_installment_id"]
    )

    assert original["amount"] == original_installment["amount"]
    assert additional["installment_number"] == 3
    assert additional["amount"] == "150.00"
    assert additional["installment_type"] == "fixed"
    assert additional["due_date"] == "2027-01-15"
    assert additional["status"] == "pending"


def test_discount_is_allocated_to_outstanding_installment(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    event, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    latest_installment = schedule["installments"][1]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": schedule["installments"][0]["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert payment_response.status_code == 201

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "discount",
            "amount": "100.00",
            "reason": "Commercial discount",
        },
    )

    assert response.status_code == 201

    adjustment = response.json()

    assert adjustment["adjustment_type"] == "discount"
    assert adjustment["amount"] == "100.00"
    assert adjustment["created_installment_id"] is None
    assert len(adjustment["allocations"]) == 1

    allocation = adjustment["allocations"][0]

    assert allocation["installment_id"] == latest_installment["id"]
    assert allocation["allocated_amount"] == "100.00"


def test_discount_can_fully_settle_installment(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    event, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    latest_installment = schedule["installments"][1]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": schedule["installments"][0]["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert payment_response.status_code == 201

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "discount",
            "amount": "500.00",
            "reason": "Full installment discount",
        },
    )

    assert response.status_code == 201

    adjustment = response.json()

    assert len(adjustment["allocations"]) == 1
    assert adjustment["allocations"][0]["installment_id"] == (
        latest_installment["id"]
    )
    assert adjustment["allocations"][0]["allocated_amount"] == "500.00"

    schedule_response = client.get(
        f"/api/v1/payments/schedules/{schedule['id']}"
    )

    assert schedule_response.status_code == 200

    updated_installment = next(
        item
        for item in schedule_response.json()["installments"]
        if item["id"] == latest_installment["id"]
    )

    assert updated_installment["status"] == "paid"


def test_discount_exceeding_outstanding_balance_creates_pending_refund(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    event, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    first_installment = schedule["installments"][0]
    latest_installment = schedule["installments"][1]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": first_installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert payment_response.status_code == 201

    payment_id = payment_response.json()["id"]

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "discount",
            "amount": "900.00",
            "reason": "Discount exceeding outstanding balance",
        },
    )

    assert response.status_code == 201

    adjustment = response.json()

    assert adjustment["amount"] == "900.00"
    assert adjustment["created_installment_id"] is None
    assert len(adjustment["allocations"]) == 2

    allocations = {
        item["installment_id"]: item["allocated_amount"]
        for item in adjustment["allocations"]
    }

    assert allocations[latest_installment["id"]] == "500.00"
    assert allocations[first_installment["id"]] == "300.00"

    refunds_response = client.get(
        f"/api/v1/payments/{payment_id}/refunds"
    )

    assert refunds_response.status_code == 200

    refunds = refunds_response.json()

    assert len(refunds) == 1
    assert refunds[0]["amount"] == "100.00"
    assert refunds[0]["status"] == "pending"
    assert refunds[0]["financial_adjustment_id"] == adjustment["id"]


def test_discount_refund_cannot_exceed_unreserved_payment_amount(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    event, schedule = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    installment = schedule["installments"][0]

    payment_response = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "50.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )

    assert payment_response.status_code == 201

    payment_id = payment_response.json()["id"]

    existing_refund = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment_id,
            "amount": "40.00",
            "refund_method": "bank_transfer",
            "reason": "Existing pending refund",
        },
    )

    assert existing_refund.status_code == 201

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "discount",
            "amount": "1000.00",
            "reason": "Discount requiring unavailable refund balance",
        },
    )

    assert response.status_code == 422

    adjustments_response = client.get(
        f"/api/v1/payments/events/{event.id}/adjustments"
    )

    assert adjustments_response.status_code == 200
    assert adjustments_response.json() == []

    refunds_response = client.get(
        f"/api/v1/payments/{payment_id}/refunds"
    )

    assert refunds_response.status_code == 200
    assert len(refunds_response.json()) == 1
    assert refunds_response.json()[0]["id"] == existing_refund.json()["id"]


def test_additional_charge_requires_due_date(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    event, _ = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "additional",
            "amount": "100.00",
            "reason": "Additional service without due date",
        },
    )

    assert response.status_code == 422


def test_discount_rejects_due_date(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    event, _ = create_payment_schedule(
        client,
        db_session,
        tenant,
    )

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "discount",
            "amount": "100.00",
            "reason": "Discount with invalid due date",
            "due_date": "2027-01-15",
        },
    )

    assert response.status_code == 422


def test_adjustment_without_payment_schedule_returns_404(
    api_client,
    db_session,
):
    client, tenant, _ = api_client

    event, _ = create_payment_context(db_session, tenant)

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "additional",
            "amount": "100.00",
            "reason": "Event without payment schedule",
            "due_date": "2027-01-15",
        },
    )

    assert response.status_code == 404

def test_completed_refund_increases_installment_outstanding_balance(
    api_client,
    db_session,
):
    client, tenant, _ = api_client
    event, schedule = create_payment_schedule(client, db_session, tenant)

    installment = schedule["installments"][1]

    payment = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )
    assert payment.status_code == 201

    refund = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment.json()["id"],
            "amount": "50.00",
            "refund_method": "bank_transfer",
            "reason": "Partial refund",
        },
    )
    assert refund.status_code == 201

    processed = client.post(
        f"/api/v1/payments/refunds/{refund.json()['id']}/process"
    )
    assert processed.status_code == 200
    assert processed.json()["status"] == "completed"

    adjustment = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "discount",
            "amount": "350.00",
            "reason": "Settle remaining balance",
        },
    )

    assert adjustment.status_code == 201
    assert adjustment.json()["allocations"][0]["installment_id"] == (
        installment["id"]
    )
    assert adjustment.json()["allocations"][0]["allocated_amount"] == "350.00"

def test_pending_refund_does_not_reduce_installment_balance(
    api_client,
    db_session,
):
    client, tenant, _ = api_client
    event, schedule = create_payment_schedule(client, db_session, tenant)

    installment = schedule["installments"][1]

    payment = client.post(
        "/api/v1/payments/",
        json={
            "installment_id": installment["id"],
            "amount": "200.00",
            "received_at": "2026-11-25T10:00:00Z",
            "method": "bank_transfer",
        },
    )
    assert payment.status_code == 201

    refund = client.post(
        "/api/v1/payments/refunds",
        json={
            "payment_id": payment.json()["id"],
            "amount": "50.00",
            "refund_method": "bank_transfer",
            "reason": "Pending refund",
        },
    )
    assert refund.status_code == 201

    adjustment = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "discount",
            "amount": "300.00",
            "reason": "Settle outstanding balance",
        },
    )

    assert adjustment.status_code == 201
    assert adjustment.json()["allocations"][0]["installment_id"] == (
        installment["id"]
    )
    assert adjustment.json()["allocations"][0]["allocated_amount"] == "300.00"


def test_discount_skips_cancelled_installments(
    api_client,
    db_session,
):
    client, tenant, _ = api_client
    event, schedule = create_payment_schedule(client, db_session, tenant)

    cancelled_installment = schedule["installments"][1]
    eligible_installment = schedule["installments"][0]

    tenant_db = TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant.id,
    )

    try:
        installment = tenant_db.get(
            PaymentInstallment,
            UUID(cancelled_installment["id"]),
        )
        assert installment is not None

        installment.status = InstallmentStatus.CANCELLED
        tenant_db.commit()
    finally:
        tenant_db.close()

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "discount",
            "amount": "100.00",
            "reason": "Discount excluding cancelled installment",
        },
    )

    assert response.status_code == 201

    allocations = response.json()["allocations"]

    assert len(allocations) == 1
    assert allocations[0]["installment_id"] == eligible_installment["id"]
    assert allocations[0]["allocated_amount"] == "100.00"
    

def test_adjustment_rejects_cancelled_payment_schedule(
    api_client,
    db_session,
):
    client, tenant, _ = api_client
    event, schedule = create_payment_schedule(client, db_session, tenant)

    tenant_db = TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant.id,
    )

    try:
        payment_schedule = tenant_db.get(
            PaymentSchedule,
            UUID(schedule["id"]),
        )
        assert payment_schedule is not None

        payment_schedule.status = PaymentScheduleStatus.CANCELLED
        tenant_db.commit()
    finally:
        tenant_db.close()

    response = client.post(
        "/api/v1/payments/adjustments",
        json={
            "event_id": str(event.id),
            "adjustment_type": "additional",
            "amount": "100.00",
            "reason": "Additional charge",
            "due_date": "2027-01-15",
        },
    )

    assert response.status_code == 409