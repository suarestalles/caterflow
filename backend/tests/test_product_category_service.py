
from uuid import uuid4

import pytest

from app.db.tenant_session import TenantSession
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.tenant import Tenant
from app.services import product_categories as service
from app.services.product_categories import (
    InvalidProductCategoryDataError,
    ProductCategoryAlreadyExistsError,
    ProductCategoryInUseError,
    ProductCategoryNotFoundError,
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


def create_category(db_session, tenant_id, **overrides):
    data = {
        "tenant_id": tenant_id,
        "name": "Alimentos",
        **overrides,
    }

    category = ProductCategory(**data)
    db_session.add(category)
    db_session.flush()
    return category


def create_product(db_session, tenant_id, category_id=None):
    product = Product(
        tenant_id=tenant_id,
        category_id=category_id,
        name="Mini sanduíche",
        type="product",
        unit="unit",
        sale_price=2.50,
        cost_price=1.20,
    )
    db_session.add(product)
    db_session.flush()
    return product


def test_list_categories_returns_active_categories(db_session):
    tenant = create_tenant(db_session)

    create_category(db_session, tenant.id, name="Alimentos")
    create_category(
        db_session,
        tenant.id,
        name="Arquivada",
        is_active=False,
    )

    db = create_tenant_session(db_session, tenant.id)

    categories, total = service.list_categories(db)

    assert total == 1
    assert categories[0].name == "Alimentos"


def test_get_category_returns_category(db_session):
    tenant = create_tenant(db_session)
    category = create_category(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    result = service.get_category(db, category_id=category.id)

    assert result.id == category.id
    assert result.name == "Alimentos"


def test_get_category_raises_when_category_does_not_exist(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductCategoryNotFoundError):
        service.get_category(db, category_id=uuid4())


def test_create_category_persists_category(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    category = service.create_category(
        db,
        data={"name": "Bebidas"},
    )

    assert category.id is not None
    assert category.tenant_id == tenant.id
    assert category.name == "Bebidas"
    assert category.is_active is True


def test_create_category_rejects_duplicate_name(db_session):
    tenant = create_tenant(db_session)
    create_category(db_session, tenant.id, name="Bebidas")

    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductCategoryAlreadyExistsError):
        service.create_category(
            db,
            data={"name": "Bebidas"},
        )


def test_create_category_accepts_parent_category(db_session):
    tenant = create_tenant(db_session)
    parent = create_category(db_session, tenant.id, name="Alimentos")

    db = create_tenant_session(db_session, tenant.id)

    category = service.create_category(
        db,
        data={
            "name": "Salgados",
            "parent_id": parent.id,
        },
    )

    assert category.parent_id == parent.id


def test_create_category_rejects_inactive_parent(db_session):
    tenant = create_tenant(db_session)
    parent = create_category(
        db_session,
        tenant.id,
        name="Arquivada",
        is_active=False,
    )

    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(InvalidProductCategoryDataError):
        service.create_category(
            db,
            data={
                "name": "Salgados",
                "parent_id": parent.id,
            },
        )


def test_update_category_changes_fields(db_session):
    tenant = create_tenant(db_session)
    category = create_category(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    updated = service.update_category(
        db,
        category_id=category.id,
        data={
            "name": "Alimentos e refeições",
            "description": "Produtos alimentícios",
        },
    )

    assert updated.name == "Alimentos e refeições"
    assert updated.description == "Produtos alimentícios"


def test_update_category_rejects_missing_category(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductCategoryNotFoundError):
        service.update_category(
            db,
            category_id=uuid4(),
            data={"name": "Nova categoria"},
        )


def test_update_category_rejects_duplicate_name(db_session):
    tenant = create_tenant(db_session)
    create_category(db_session, tenant.id, name="Bebidas")
    category = create_category(db_session, tenant.id, name="Alimentos")

    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductCategoryAlreadyExistsError):
        service.update_category(
            db,
            category_id=category.id,
            data={"name": "Bebidas"},
        )


def test_update_category_rejects_parent_cycle(db_session):
    tenant = create_tenant(db_session)
    parent = create_category(db_session, tenant.id, name="Alimentos")
    child = create_category(
        db_session,
        tenant.id,
        name="Salgados",
        parent_id=parent.id,
    )

    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(InvalidProductCategoryDataError):
        service.update_category(
            db,
            category_id=parent.id,
            data={"parent_id": child.id},
        )


def test_archive_category_sets_is_active_false(db_session):
    tenant = create_tenant(db_session)
    category = create_category(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    archived = service.archive_category(
        db,
        category_id=category.id,
    )

    assert archived.id == category.id
    assert archived.is_active is False


def test_archive_category_rejects_category_with_products(db_session):
    tenant = create_tenant(db_session)
    category = create_category(db_session, tenant.id)
    create_product(db_session, tenant.id, category.id)

    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductCategoryInUseError):
        service.archive_category(
            db,
            category_id=category.id,
        )


def test_archive_category_rejects_category_with_children(db_session):
    tenant = create_tenant(db_session)
    parent = create_category(db_session, tenant.id, name="Alimentos")
    create_category(
        db_session,
        tenant.id,
        name="Salgados",
        parent_id=parent.id,
    )

    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductCategoryInUseError):
        service.archive_category(
            db,
            category_id=parent.id,
        )


def test_archive_category_rejects_missing_category(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    with pytest.raises(ProductCategoryNotFoundError):
        service.archive_category(
            db,
            category_id=uuid4(),
        )
