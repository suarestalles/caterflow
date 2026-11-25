from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.db.tenant_session import TenantSession
from app.models.employee import Employee
from app.models.tenant import Tenant
from app.services import employees as employee_service
from app.services.employees import EmployeeNotFoundError, InvalidEmployeeDataError


def create_tenant_session(db_session, tenant_id):
    return TenantSession(
        bind=db_session.connection(),
        join_transaction_mode="create_savepoint",
        tenant_id=tenant_id,
    )


def create_tenant(db_session, name="Employee Service Test Tenant"):
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def create_employee(db_session, tenant_id, **overrides):
    data = {
        "name": "Maria Silva",
        "employment_type": "employee",
        "position": "Kitchen Assistant",
        "email": "maria@example.com",
        "phone": "+34600123456",
        "notes": None,
    }
    data.update(overrides)
    employee = Employee(tenant_id=tenant_id, **data)
    db_session.add(employee)
    db_session.flush()
    return employee


def test_create_employee_service(db_session):
    tenant = create_tenant(db_session)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        employee = employee_service.create_employee(
            tenant_db,
            data={
                "name": "Maria Silva",
                "employment_type": "employee",
                "position": "Kitchen Assistant",
                "email": "maria@example.com",
            },
        )
        assert employee.id is not None
        assert employee.tenant_id == tenant.id
        assert employee.name == "Maria Silva"
        assert employee.employment_type == "employee"


def test_create_freelancer_employee_service(db_session):
    tenant = create_tenant(db_session)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        employee = employee_service.create_employee(
            tenant_db,
            data={"name": "Joao Santos", "employment_type": "freelancer"},
        )
        assert employee.employment_type == "freelancer"
        assert employee.email is None


@pytest.mark.parametrize("field", ["name", "employment_type"])
def test_create_employee_rejects_null_required_fields(db_session, field):
    tenant = create_tenant(db_session)
    data = {"name": "Maria Silva", "employment_type": "employee"}
    data[field] = None
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(InvalidEmployeeDataError):
            employee_service.create_employee(tenant_db, data=data)


def test_get_employee_service(db_session):
    tenant = create_tenant(db_session)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        result = employee_service.get_employee(tenant_db, employee_id=employee.id)
        assert result.id == employee.id
        assert result.name == "Maria Silva"


def test_get_nonexistent_employee_fails(db_session):
    tenant = create_tenant(db_session)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(EmployeeNotFoundError):
            employee_service.get_employee(tenant_db, employee_id=uuid4())


def test_get_employee_from_another_tenant_fails(db_session):
    tenant_a = create_tenant(db_session, "Tenant A")
    tenant_b = create_tenant(db_session, "Tenant B")
    employee_b = create_employee(db_session, tenant_b.id, name="Employee B")
    with create_tenant_session(db_session, tenant_a.id) as tenant_db:
        with pytest.raises(EmployeeNotFoundError):
            employee_service.get_employee(tenant_db, employee_id=employee_b.id)


def test_get_archived_employee_fails(db_session):
    tenant = create_tenant(db_session)
    employee = create_employee(db_session, tenant.id, archived_at=datetime.now(UTC))
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(EmployeeNotFoundError):
            employee_service.get_employee(tenant_db, employee_id=employee.id)


def test_list_employees_service(db_session):
    tenant = create_tenant(db_session)
    create_employee(db_session, tenant.id, name="Maria Silva")
    create_employee(db_session, tenant.id, name="Joao Santos", email="joao@example.com")
    create_employee(db_session, tenant.id, name="Archived", archived_at=datetime.now(UTC))
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        employees, total = employee_service.list_employees(tenant_db)
        assert total == 2
        assert len(employees) == 2


def test_list_employees_service_with_search(db_session):
    tenant = create_tenant(db_session)
    create_employee(db_session, tenant.id, name="Maria Silva")
    create_employee(db_session, tenant.id, name="Joao Santos", email="joao@example.com")
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        employees, total = employee_service.list_employees(tenant_db, search="Maria")
        assert total == 1
        assert employees[0].name == "Maria Silva"


def test_update_employee_service(db_session):
    tenant = create_tenant(db_session)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        updated = employee_service.update_employee(
            tenant_db,
            employee_id=employee.id,
            data={"name": "Maria Santos", "position": "Waiter"},
        )
        assert updated.name == "Maria Santos"
        assert updated.position == "Waiter"
        assert updated.email == "maria@example.com"


@pytest.mark.parametrize("field", ["name", "employment_type"])
def test_update_employee_rejects_null_required_fields(db_session, field):
    tenant = create_tenant(db_session)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(InvalidEmployeeDataError):
            employee_service.update_employee(
                tenant_db, employee_id=employee.id, data={field: None}
            )


def test_update_employee_rejects_empty_data(db_session):
    tenant = create_tenant(db_session)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(InvalidEmployeeDataError):
            employee_service.update_employee(tenant_db, employee_id=employee.id, data={})


def test_update_nonexistent_employee_fails(db_session):
    tenant = create_tenant(db_session)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(EmployeeNotFoundError):
            employee_service.update_employee(
                tenant_db, employee_id=uuid4(), data={"name": "Updated"}
            )


def test_archive_employee_service(db_session):
    tenant = create_tenant(db_session)
    employee = create_employee(db_session, tenant.id)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        employee_service.archive_employee(tenant_db, employee_id=employee.id)
        archived = tenant_db.get(Employee, employee.id)
        assert archived is not None
        assert archived.archived_at is not None


def test_archive_nonexistent_employee_fails(db_session):
    tenant = create_tenant(db_session)
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(EmployeeNotFoundError):
            employee_service.archive_employee(tenant_db, employee_id=uuid4())


def test_archive_already_archived_employee_fails(db_session):
    tenant = create_tenant(db_session)
    employee = create_employee(db_session, tenant.id, archived_at=datetime.now(UTC))
    with create_tenant_session(db_session, tenant.id) as tenant_db:
        with pytest.raises(EmployeeNotFoundError):
            employee_service.archive_employee(tenant_db, employee_id=employee.id)
