
from app.db.tenant_session import TenantSession
from app.models.product_category import ProductCategory
from app.models.tenant import Tenant
from app.repositories import product_categories as repository


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


def create_category(db, tenant_id, **overrides):
    data = {
        "tenant_id": tenant_id,
        "name": "Alimentos",
        **overrides,
    }

    category = ProductCategory(**data)
    db.add(category)
    db.flush()
    return category


def test_get_category_by_id_returns_category(db_session):
    tenant = create_tenant(db_session)
    category = create_category(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    result = repository.get_category_by_id(
        db,
        category_id=category.id,
    )

    assert result is not None
    assert result.id == category.id


def test_list_categories_filters_by_search(db_session):
    tenant = create_tenant(db_session)

    create_category(db_session, tenant.id, name="Alimentos")
    create_category(db_session, tenant.id, name="Bebidas")

    db = create_tenant_session(db_session, tenant.id)

    categories, total = repository.list_categories(
        db,
        search="Alimentos",
    )

    assert total == 1
    assert categories[0].name == "Alimentos"


def test_list_categories_filters_by_parent(db_session):
    tenant = create_tenant(db_session)

    parent = create_category(db_session, tenant.id)

    create_category(
        db_session,
        tenant.id,
        name="Salgados",
        parent_id=parent.id,
    )
    create_category(
        db_session,
        tenant.id,
        name="Bebidas",
    )

    db = create_tenant_session(db_session, tenant.id)

    categories, total = repository.list_categories(
        db,
        parent_id=parent.id,
    )

    assert total == 1
    assert categories[0].name == "Salgados"


def test_list_categories_paginates(db_session):
    tenant = create_tenant(db_session)

    for index in range(5):
        create_category(
            db_session,
            tenant.id,
            name=f"Categoria {index}",
        )

    db = create_tenant_session(db_session, tenant.id)

    categories, total = repository.list_categories(
        db,
        offset=1,
        limit=2,
    )

    assert total == 5
    assert len(categories) == 2


def test_create_category_persists_category(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    category = repository.create_category(
        db,
        data={"name": "Bebidas"},
    )

    assert category.id is not None
    assert category.tenant_id == tenant.id
    assert category.name == "Bebidas"


def test_update_category_changes_fields(db_session):
    tenant = create_tenant(db_session)
    category = create_category(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    category = repository.get_category_by_id(
        db,
        category_id=category.id,
    )

    updated = repository.update_category(
        db,
        category=category,
        data={"description": "Categoria de bebidas e sucos"},
    )

    assert updated.description == "Categoria de bebidas e sucos"
