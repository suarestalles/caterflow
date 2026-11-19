
from app.db.tenant_session import TenantSession
from app.models.product import Product, ProductType
from app.models.product_category import ProductCategory
from app.models.tenant import Tenant
from app.repositories import products as repository


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


def create_product(db, tenant_id, **overrides):
    data = {
        "tenant_id": tenant_id,
        "name": "Mini sanduíche",
        "type": ProductType.PRODUCT.value,
        "unit": "unit",
        "sale_price": 2.50,
        "cost_price": 1.20,
        **overrides,
    }

    product = Product(**data)
    db.add(product)
    db.flush()
    return product


def test_get_product_by_id_returns_product(db_session):
    tenant = create_tenant(db_session)
    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    result = repository.get_product_by_id(db, product_id=product.id)

    assert result is not None
    assert result.id == product.id


def test_list_products_filters_by_search(db_session):
    tenant = create_tenant(db_session)

    create_product(db_session, tenant.id, name="Mini sanduíche")
    create_product(db_session, tenant.id, name="Suco natural")

    db = create_tenant_session(db_session, tenant.id)

    products, total = repository.list_products(
        db,
        search="sanduíche",
    )

    assert total == 1
    assert products[0].name == "Mini sanduíche"


def test_list_products_filters_by_type(db_session):
    tenant = create_tenant(db_session)

    create_product(
        db_session,
        tenant.id,
        name="Mini sanduíche",
        type="product",
    )
    create_product(
        db_session,
        tenant.id,
        name="Garçom",
        type="service",
    )

    db = create_tenant_session(db_session, tenant.id)

    products, total = repository.list_products(
        db,
        product_type=ProductType.SERVICE,
    )

    assert total == 1
    assert products[0].name == "Garçom"


def test_list_products_filters_by_category(db_session):
    tenant = create_tenant(db_session)

    category = ProductCategory(
        tenant_id=tenant.id,
        name="Alimentos",
    )
    db_session.add(category)
    db_session.flush()

    create_product(
        db_session,
        tenant.id,
        name="Mini sanduíche",
        category_id=category.id,
    )
    create_product(
        db_session,
        tenant.id,
        name="Garçom",
    )

    db = create_tenant_session(db_session, tenant.id)

    products, total = repository.list_products(
        db,
        category_id=category.id,
    )

    assert total == 1
    assert products[0].category_id == category.id


def test_list_products_filters_archived_products(db_session):
    tenant = create_tenant(db_session)

    create_product(
        db_session,
        tenant.id,
        name="Ativo",
        is_active=True,
    )
    create_product(
        db_session,
        tenant.id,
        name="Arquivado",
        is_active=False,
    )

    db = create_tenant_session(db_session, tenant.id)

    products, total = repository.list_products(db)

    assert total == 1
    assert products[0].name == "Ativo"


def test_list_products_paginates(db_session):
    tenant = create_tenant(db_session)

    for index in range(5):
        create_product(
            db_session,
            tenant.id,
            name=f"Produto {index}",
        )

    db = create_tenant_session(db_session, tenant.id)

    products, total = repository.list_products(
        db,
        offset=1,
        limit=2,
    )

    assert total == 5
    assert len(products) == 2


def test_create_product_persists_product(db_session):
    tenant = create_tenant(db_session)
    db = create_tenant_session(db_session, tenant.id)

    product = repository.create_product(
        db,
        data={
            "name": "Suco natural",
            "type": "product",
            "unit": "l",
            "sale_price": 5.00,
            "cost_price": 2.00,
        },
    )

    assert product.id is not None
    assert product.tenant_id == tenant.id
    assert product.name == "Suco natural"


def test_update_product_changes_fields(db_session):
    tenant = create_tenant(db_session)
    product = create_product(db_session, tenant.id)

    db = create_tenant_session(db_session, tenant.id)

    product = repository.get_product_by_id(
        db,
        product_id=product.id,
    )

    updated = repository.update_product(
        db,
        product=product,
        data={"sale_price": 3.50},
    )

    assert updated.sale_price == 3.50
