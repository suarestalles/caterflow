from uuid import uuid4

import pytest

from app.db.tenant_session import TenantSession
from app.models.product import Product, ProductType
from app.models.tenant import Tenant
from app.services import products as service
from app.services.products import (
    InvalidProductDataError,
    ProductNotFoundError,
    ProductSKUAlreadyExistsError,
)


def create_tenant(db_session):
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_tenant_session(db_session, tenant_id):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_product(db_session, tenant_id, **overrides):
    data = {
        "tenant_id": tenant_id,
        "name": "Mini sanduíche",
        "type": ProductType.PRODUCT.value,
        "unit": "unit",
        "sku": None,
        "sale_price": 2.50,
        "cost_price": 1.20,
        **overrides,
    }

    product = Product(**data)
    db_session.add(product)
    db_session.flush()
    return product


def product_data(**overrides):
    return {
        "name": "Suco natural",
        "type": "product",
        "unit": "l",
        "sku": None,
        "sale_price": 5.00,
        "cost_price": 2.00,
        **overrides,
    }


def test_list_products_returns_active_products(db_session):
    tenant = create_tenant(db_session)

    create_product(db_session, tenant.id, name="Mini sanduíche")
    create_product(
        db_session,
        tenant.id,
        name="Arquivado",
        is_active=False,
    )

    db = create_tenant_session(db_session, tenant.id)

    products, total = service.list_products(db)

    assert total == 1
    assert products[0].name == "Mini sanduíche"


def test_get_product_returns_product(db_session):
    tenant = create_tenant(db_session)
    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    result = service.get_product(db, product_id=product.id)

    assert result.id == product.id
    assert result.name == "Mini sanduíche"


def test_get_product_raises_when_product_does_not_exist(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductNotFoundError):
        service.get_product(db, product_id=uuid4())


def test_create_product_persists_product(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    product = service.create_product(
        db,
        data=product_data(),
    )

    assert product.id is not None
    assert product.tenant_id == tenant.id
    assert product.name == "Suco natural"
    assert product.sale_price == 5.00
    assert product.is_active is True


def test_create_product_rejects_duplicate_sku(db_session):
    tenant = create_tenant(db_session)

    create_product(
        db_session,
        tenant.id,
        sku="SAND-001",
    )

    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductSKUAlreadyExistsError):
        service.create_product(
            db,
            data=product_data(sku="SAND-001"),
        )


def test_update_product_changes_fields(db_session):
    tenant = create_tenant(db_session)
    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    updated = service.update_product(
        db,
        product_id=product.id,
        data={"name": "Mini sanduíche especial", "sale_price": 3.50},
    )

    assert updated.name == "Mini sanduíche especial"
    assert updated.sale_price == 3.50


def test_update_product_rejects_missing_product(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductNotFoundError):
        service.update_product(
            db,
            product_id=uuid4(),
            data={"name": "Produto inexistente"},
        )


def test_update_product_rejects_archived_product(db_session):
    tenant = create_tenant(db_session)
    product = create_product(
        db_session,
        tenant.id,
        is_active=False,
    )

    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(InvalidProductDataError):
        service.update_product(
            db,
            product_id=product.id,
            data={"name": "Novo nome"},
        )


def test_archive_product_sets_is_active_false(db_session):
    tenant = create_tenant(db_session)
    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    archived = service.archive_product(
        db,
        product_id=product.id,
    )

    assert archived.id == product.id
    assert archived.is_active is False


def test_archive_product_rejects_missing_product(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductNotFoundError):
        service.archive_product(
            db,
            product_id=uuid4(),
        )


