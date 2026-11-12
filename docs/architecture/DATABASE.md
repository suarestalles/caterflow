# Database Architecture

**Project:** CaterFlow  
**Document version:** 0.1  
**Status:** Initial specification  
**Last updated:** November 2026

---

## 1. Purpose

This document defines the database architecture and data modeling principles for CaterFlow.

It establishes:

- Database technology and organization.
- Entity ownership and relationships.
- Multi-tenant data isolation.
- Data integrity constraints.
- Financial data representation.
- Historical data preservation.
- Indexing and query optimization.
- Migration and schema evolution practices.

The database must support the operational and financial requirements of a multi-tenant catering management SaaS.

The model should prioritize consistency, maintainability, traceability, and the ability to evolve as new business requirements emerge.

## 2. Database Technology

CaterFlow will use **PostgreSQL** as its primary relational database.

The backend will interact with PostgreSQL through:

- SQLAlchemy 2.x for ORM and database access.
- Alembic for schema migrations.
- Pydantic for request and response validation.
- Pytest for automated database and integration tests.

### 2.1 Database Organization

The initial architecture will use:

- One PostgreSQL database.
- One shared schema.
- Multiple tenants.
- Tenant ownership through `tenant_id`.
- Relational constraints to preserve data integrity.

Separate databases or schemas per tenant are not part of the MVP.

### 2.2 Database Design Principles

The database must follow these principles:

1. Tenant-owned records must have an explicit owner.
2. Relationships must preserve tenant boundaries.
3. Financial values must use exact decimal representation.
4. Historical business records must remain consistent.
5. Critical changes must be traceable.
6. Referential integrity must be enforced by the database whenever possible.
7. Business rules must not depend exclusively on frontend validation.
8. Database migrations must be version-controlled.
9. Destructive schema changes must be handled carefully.
10. The schema must support future growth without unnecessary complexity.

## 3. Naming Conventions

The database will use consistent naming conventions.

| Element | Convention | Example |
|---|---|---|
| Tables | Plural, snake_case | `customers` |
| Columns | snake_case | `created_at` |
| Primary keys | `id` | `id` |
| Foreign keys | `{entity}_id` | `customer_id` |
| Tenant ownership | `tenant_id` | `tenant_id` |
| Boolean fields | `is_` or `has_` prefix | `is_active` |
| Timestamps | `_at` suffix | `created_at` |
| Unique constraints | `uq_` prefix | `uq_customers_tenant_email` |
| Indexes | `idx_` prefix | `idx_events_tenant_date` |
| Foreign keys | `fk_` prefix | `fk_events_customer` |
| Check constraints | `ck_` prefix | `ck_payments_amount_positive` |

All table and column names should be written in English.

Database naming conventions must remain consistent across all modules.

## 4. Primary Keys and Identifiers

Each database entity must have a unique primary key.

The recommended identifier strategy is UUID.

UUIDs provide globally unique identifiers and are suitable for distributed systems, API resources, and multi-tenant applications.

PostgreSQL's native UUID type should be used.

The backend should generate identifiers using a maintained UUID implementation.

Sequential database identifiers may still be used internally for specialized technical purposes, but public business resources should use UUID identifiers consistently.

Identifiers must not be treated as authorization mechanisms. Access must always be validated independently.

## 5. Common Entity Fields

Most tenant-owned entities should include a standard set of fields.

| Field | Type | Purpose |
|---|---|---|
| id | UUID | Primary key |
| tenant_id | UUID | Owning tenant |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last modification timestamp |

Not every entity requires every field.

Historical records, immutable snapshots, and append-only records may have different update requirements.

### 5.1 Timestamps

All timestamps must be stored using PostgreSQL `TIMESTAMPTZ`.

The database should store timestamps consistently in UTC.

The application will convert timestamps to the tenant's configured timezone for display and business operations.

The default timezone is `Europe/Madrid`.

Business dates that represent calendar dates rather than moments in time should use PostgreSQL `DATE`.

For example:

- Event date: `DATE` when the business concept is a calendar date.
- Event start time: a local time field when appropriate.
- Payment received timestamp: `TIMESTAMPTZ`.
- Record creation timestamp: `TIMESTAMPTZ`.

Event scheduling must account for local timezone and daylight-saving transitions. The final event scheduling model must be defined during implementation.

## 6. Multi-Tenant Data Model

Tenant isolation is a fundamental database requirement.

Every tenant-owned table must contain a non-null `tenant_id`.

The tenant identifier must be assigned by the backend using the validated tenant context.

The frontend must never determine record ownership through an untrusted payload.

### 6.1 Tenant Ownership

The main entity ownership structure will be:

| Entity | Ownership |
|---|---|
| Users | Platform-level |
| Tenants | Platform-level |
| Tenant memberships | Tenant-scoped |
| Roles | Tenant-scoped or platform-defined, depending on implementation |
| Permissions | Platform-level definitions |
| Customers | Tenant-scoped |
| Employees | Tenant-scoped |
| Catalog items | Tenant-scoped |
| Menus | Tenant-scoped |
| Quotations | Tenant-scoped |
| Quotation versions | Tenant-scoped |
| Events | Tenant-scoped |
| Employee assignments | Tenant-scoped |
| Payment schedules | Tenant-scoped |
| Payments | Tenant-scoped |
| Expenses | Tenant-scoped |
| Audit records | Tenant-scoped for business operations |

Platform-level authentication and operational tables must be designed separately from tenant-owned business tables.

### 6.2 Tenant-Scoped Relationships

Relationships between tenant-owned entities must preserve the same tenant ownership.

For example:

- An event can reference only a customer from the same tenant.
- A quotation can reference only catalog items from the same tenant.
- An employee assignment can reference only employees from the same tenant.
- A payment must reference a financial obligation belonging to the same tenant.

The database should use composite foreign keys where appropriate.

A common pattern is to define a unique constraint on `(tenant_id, id)` in the referenced table and reference both columns from dependent tables.

This ensures that cross-tenant relationships cannot be created even if an application validation is missed.

## 7. Core Domain Entities

The database will be organized around the following business domains.

### 7.1 Identity and Tenant Management

Initial entities:

- `users`
- `tenants`
- `tenant_memberships`
- `roles`
- `permissions`
- `role_permissions`
- `user_sessions`
- `password_reset_tokens`
- `email_verification_tokens`

Responsibilities:

- User identity.
- Company registration.
- Membership management.
- Authentication sessions.
- Role and permission management.
- Account recovery and verification.

The detailed authentication behavior is defined in `AUTHENTICATION.md`.

### 7.2 Customers

Table: `customers`

Customers represent individuals or organizations that request catering services.

Suggested fields:

| Field | Description |
|---|---|
| id | Customer identifier |
| tenant_id | Owning tenant |
| customer_type | Individual or organization |
| name | Customer or organization name |
| email | Contact email |
| phone | Contact phone |
| tax_identifier | Optional fiscal identification |
| address | Optional primary address |
| notes | Internal notes |
| created_at | Creation timestamp |
| updated_at | Last modification |

Customer data must remain tenant-specific.

The system should support multiple quotations and events associated with the same customer.

Historical quotations and events must preserve the relevant customer information required for accurate records, even if the customer's profile changes later.

### 7.3 Employees and Workforce

Initial entities:

- `employees`
- `employee_assignments`
- `employee_time_entries`
- `compensation_rates`, if required by the final implementation.

Employees may be permanent staff or freelancers.

Suggested employee attributes:

| Field | Description |
|---|---|
| id | Employee identifier |
| tenant_id | Owning tenant |
| full_name | Employee name |
| email | Optional email |
| phone | Optional phone |
| employment_type | Permanent or freelance |
| is_active | Availability status |
| notes | Internal notes |

Employee assignments connect employees to events.

An assignment should preserve:

- Event reference.
- Employee reference.
- Assigned role or function.
- Planned hours.
- Actual hours, when available.
- Compensation method.
- Agreed compensation amount.
- Assignment status.

### 7.3.1 Compensation Snapshots

Compensation may be calculated using:

- Hourly rate.
- Fixed amount per event.

Additional methods may be introduced later.

The agreed compensation must be stored as a snapshot in the employee assignment.

Changing an employee's current compensation rate must not modify historical assignments or previously calculated event costs.

This is essential for financial accuracy.

### 7.4 Catalog and Menus

Initial entities:

- `catalog_categories`
- `catalog_items`
- `menus`
- `menu_items`
- `pricing_rules`, if required by the final pricing model.

Catalog items may represent:

- Food.
- Drinks.
- Service options.
- Additional services.
- Other configurable products or services.

Suggested catalog item fields:

| Field | Description |
|---|---|
| id | Catalog item identifier |
| tenant_id | Owning tenant |
| category_id | Category reference |
| name | Item name |
| description | Item description |
| item_type | Food, drink, service, or other |
| base_price | Optional default price |
| is_active | Availability |
| created_at | Creation timestamp |
| updated_at | Last modification |

Menu composition must support reusable items and tenant-specific configurations.

Prices must be represented using decimal types.

Catalog changes must not silently modify previously approved quotations.

### 7.5 Quotations

Initial entities:

- `quotations`
- `quotation_versions`
- `quotation_items`
- `quotation_approvals`

A quotation represents a commercial proposal sent to a customer.

A quotation should contain:

- Customer reference.
- Current quotation status.
- Event type.
- Expected event date.
- Estimated number of attendees.
- Service format.
- Internal notes.
- Current version reference, where applicable.
- Creation and modification timestamps.

### 7.5.1 Quotation Versions

Quotation versions must preserve the commercial proposal as it existed at the time of creation.

A version should contain:

- Version number.
- Quotation reference.
- Customer and event information snapshots.
- Menu and service descriptions.
- Item quantities.
- Unit prices.
- Discounts.
- Taxes, when applicable.
- Total amount.
- Payment conditions.
- Validity period.
- Creation timestamp.
- Created by user.

A quotation version must be immutable after creation.

If a proposal changes, a new version must be created.

The previous version must remain available for historical reference.

### 7.5.2 Quotation Approval

Approval must identify the exact version accepted by the customer.

The approval record should preserve:

- Quotation reference.
- Approved version reference.
- Approval timestamp.
- User or authorized actor responsible for recording the approval.
- Approval method or source, when available.
- Relevant evidence or reference, when available.

Approval must not be inferred merely from a change in quotation status.

The system must preserve the distinction between a quotation being sent, accepted, rejected, or expired.

### 7.6 Events

Table: `events`

An event represents the operational execution of an approved catering service.

An event should be linked to:

- Its originating quotation.
- The approved quotation version.
- The customer.
- Assigned employees.
- Payment schedule.
- Expenses.
- Operational information.

Suggested fields:

| Field | Description |
|---|---|
| id | Event identifier |
| tenant_id | Owning tenant |
| quotation_id | Originating quotation |
| approved_version_id | Approved quotation version |
| customer_id | Customer reference |
| title | Event name |
| event_date | Event date |
| start_time | Planned start time |
| end_time | Planned end time |
| location | Event location |
| attendee_count | Expected attendees |
| status | Operational status |
| notes | Internal notes |
| created_at | Creation timestamp |
| updated_at | Last modification |

Initial operational statuses:

- Scheduled.
- Confirmed.
- In Preparation.
- In Progress.
- Completed.
- Cancelled.

Operational status must remain independent of financial status.

An event may be completed while still having outstanding payments.

### 7.6.1 Event Creation

Converting an approved quotation into an event must be idempotent.

Repeated requests to perform the conversion must not create duplicate events.

The originating quotation and approved version must be preserved.

The system must also retain the original commercial snapshot.

### 7.7 Payment Management

Initial entities:

- `payment_schedules`
- `payment_installments`
- `payments`

The payment model must distinguish between:

1. The amount the customer is expected to pay.
2. The scheduled payment obligations.
3. The amounts actually received.

These are different financial concepts and must not be combined into a single field.

### 7.7.1 Payment Schedule

A payment schedule represents the payment conditions associated with an approved quotation.

It should preserve:

- Approved quotation version.
- Original commercial total.
- Payment condition snapshot.
- Creation timestamp.
- Currency.
- Schedule status.

The recommended approach is to generate the payment schedule when the quotation is approved.

This ensures that the agreed payment conditions are preserved before event conversion.

This timing remains subject to final business validation.

### 7.7.2 Payment Installments

Each installment represents an amount expected on a specific date.

Suggested fields:

| Field | Description |
|---|---|
| id | Installment identifier |
| tenant_id | Owning tenant |
| payment_schedule_id | Parent schedule |
| installment_number | Sequence |
| due_date | Expected payment date |
| amount | Amount due |
| status | Installment status |
| created_at | Creation timestamp |

Payment conditions may use percentages or fixed amounts.

For percentage-based installments, the configured percentages must total exactly 100%.

For fixed-amount installments, the installment totals must reconcile with the agreed amount.

The final calculation and rounding rules must be implemented consistently.

### 7.7.3 Payments Received

Payments represent actual financial receipts.

A payment record should include:

- Customer or event financial reference.
- Installment reference, when applicable.
- Amount received.
- Payment date.
- Payment method.
- External reference, when available.
- Notes.
- Recorded by user.
- Creation timestamp.

The model should support partial payments.

Payment history must not be overwritten when a new payment is received.

Corrections must be handled through traceable adjustment or reversal operations.

### 7.8 Expenses

Table: `expenses`

Expenses represent actual costs associated with an event or other tenant business activity.

Initial expense categories:

- Food and ingredients.
- Drinks.
- Staff.
- Transportation.
- Other.

Suggested fields:

| Field | Description |
|---|---|
| id | Expense identifier |
| tenant_id | Owning tenant |
| event_id | Optional event reference |
| category | Expense category |
| description | Expense description |
| amount | Total expense amount |
| expense_date | Expense date |
| currency | Currency code |
| receipt_reference | Optional document reference |
| notes | Additional information |
| created_by | User who recorded the expense |
| created_at | Creation timestamp |
| updated_at | Last modification |

The MVP will record expenses using total amounts per category or expense entry.

It will not require individual ingredient costs, inventory management, or detailed stock movements.

### 7.8.1 Staff Cost Treatment

Staff compensation calculated through employee assignments must not be counted again as a manually entered staff expense.

The system must establish a single authoritative financial treatment for staff costs.

Recommended initial approach:

- Employee assignment compensation is the source of planned and calculated staff costs.
- Actual staff costs are recorded or reconciled against assignments.
- Manual staff expense entries must not duplicate costs already included in event calculations.

The exact distinction between planned, calculated, and actual staff costs must be finalized before implementing financial reporting.

### 7.9 Company Settings

Initial entity:

- `tenant_settings`

Company settings should support:

- Company name.
- Logo reference.
- Address.
- Phone.
- Email.
- Tax identifier.
- Default language.
- Timezone.
- Default currency.
- PDF branding preferences.
- Configurable payment conditions.
- Other tenant-level operational settings.

The system should distinguish between structured company information and flexible configuration values.

Important business settings should use validated structured fields rather than an unrestricted JSON object whenever practical.

## 8. Financial Data Modeling

Financial data requires special attention because rounding and precision errors can create incorrect quotations, payment schedules, and reports.

### 8.1 Monetary Values

Monetary values must use PostgreSQL `NUMERIC` and Python `Decimal`.

Floating-point types must not be used for financial calculations.

Recommended initial database representation:

```sql
NUMERIC(14, 2)
```

This supports amounts with two decimal places and sufficient range for the expected initial business operations.

The exact precision must be reviewed if future requirements include higher-value transactions or additional currency conventions.

### 8.2 Currency

The initial platform currency is EUR.

Financial records should store an explicit ISO 4217 currency code where appropriate.

Example:

```text
EUR
```

Although the MVP uses EUR by default, the database should avoid hardcoding currency symbols into stored financial values.

Future multi-currency support would require explicit exchange-rate and conversion policies.

### 8.3 Rounding

Financial calculations must use a consistent decimal rounding strategy.

The application must define:

- When rounding occurs.
- Which precision is used for intermediate calculations.
- How percentage-based installments are reconciled.
- How discounts and taxes are calculated.
- How displayed totals are derived.

The chosen rounding policy must be covered by automated tests.

### 8.4 Financial Snapshots

Historical financial records must preserve the values agreed at the time of the transaction.

Examples:

- Approved quotation prices.
- Payment conditions.
- Installment amounts.
- Employee compensation.
- Discounts.
- Applicable tax values.

Changes to current catalog prices, payment conditions, or employee rates must not silently modify historical records.

## 9. Historical Preservation and Soft Deletion

CaterFlow must preserve important business history.

Financial records, approved quotations, completed events, payments, and audit records must not be silently deleted through ordinary application operations.

### 9.1 Soft Deletion

Soft deletion may be used for records that can be deactivated or removed from active business workflows.

Possible fields:

- `deleted_at`
- `deleted_by`

Examples may include:

- Customers.
- Catalog items.
- Employees.
- Menus.

The exact use of soft deletion must be defined per entity.

### 9.2 Historical Records

Approved quotations and financial records must preserve their historical meaning.

When a related entity is deactivated or its current information changes, historical records must remain understandable.

For example, an old quotation must not display a new catalog price simply because the catalog item was updated.

### 9.3 Deletion and Retention

Deletion policies must account for:

- Applicable legal retention requirements.
- Contractual obligations.
- Privacy obligations.
- Financial auditability.
- Backup retention.

The platform must not retain personal information indefinitely without a valid purpose, but it must also not remove records that are required to satisfy legal or contractual obligations.

The final retention policy will be defined in the security and operational documentation.

## 10. Audit Data

Critical business operations must generate audit records.

Initial table:

`audit_logs`

Suggested fields:

| Field | Description |
|---|---|
| id | Audit identifier |
| tenant_id | Owning tenant |
| actor_user_id | User responsible for the action, when applicable |
| action | Operation performed |
| resource_type | Affected entity type |
| resource_id | Affected entity identifier |
| occurred_at | Event timestamp |
| metadata | Relevant non-sensitive contextual information |

Audit records should support investigation of important business changes.

Examples:

- Quotation approval.
- Quotation version creation.
- Event cancellation.
- Payment recording.
- Expense modification.
- Employee assignment changes.
- Role changes.
- Membership changes.

Audit records must not store passwords, access tokens, refresh tokens, or other secrets.

The audit system should be append-only from the perspective of ordinary application users.

## 11. Indexing Strategy

Indexes must support common application queries and preserve acceptable performance as tenant data grows.

### 11.1 Tenant Indexes

All tenant-owned tables should have an index strategy that supports tenant-scoped queries.

The system should avoid creating unnecessary indexes on every column.

Indexes must be selected according to actual query patterns.

### 11.2 Recommended Initial Indexes

Examples include:

| Table | Index |
|---|---|
| customers | `(tenant_id, name)` |
| customers | `(tenant_id, email)` where appropriate |
| employees | `(tenant_id, is_active)` |
| catalog_items | `(tenant_id, category_id)` |
| quotations | `(tenant_id, status, created_at)` |
| quotation_versions | `(tenant_id, quotation_id, version_number)` |
| events | `(tenant_id, event_date)` |
| events | `(tenant_id, status, event_date)` |
| employee_assignments | `(tenant_id, event_id)` |
| payment_installments | `(tenant_id, due_date, status)` |
| payments | `(tenant_id, payment_date)` |
| expenses | `(tenant_id, event_id, expense_date)` |
| audit_logs | `(tenant_id, occurred_at)` |

Unique indexes and foreign-key indexes must also be considered.

The final index set should be validated against real query plans.

## 12. Constraints and Data Integrity

The database must enforce important data integrity rules.

Examples:

- Non-null tenant ownership.
- Valid foreign-key relationships.
- Unique business identifiers within a tenant.
- Positive monetary amounts where appropriate.
- Valid attendee counts.
- Valid installment numbers.
- Valid status values.
- Valid date and time relationships.
- Valid percentage ranges.
- Tenant-scoped relationships.

Business rules that require multiple database records or complex calculations should be enforced within application transactions, with database constraints providing additional protection wherever practical.

The database must not rely exclusively on frontend validation.

## 13. Transaction Management

Critical business operations must execute within database transactions.

Examples:

### 13.1 Quotation Approval

The operation may need to:

1. Validate the quotation.
2. Validate the selected version.
3. Record approval.
4. Preserve the approved version reference.
5. Generate the payment schedule according to the agreed business policy.
6. Record audit information.

The operation must either complete consistently or roll back.

### 13.2 Event Conversion

The operation may need to:

1. Validate quotation approval.
2. Verify that the event does not already exist.
3. Create the event.
4. Associate the approved quotation version.
5. Initialize related operational records when required.
6. Record the conversion.
7. Commit the transaction.

Idempotency must be enforced so retries do not create duplicate events.

### 13.3 Payment Recording

The operation may need to:

1. Validate the installment or financial reference.
2. Validate the received amount.
3. Create the payment record.
4. Update derived installment status.
5. Record audit information.
6. Commit the transaction.

Partial payments must be supported without losing previous payment history.

## 14. Data Consistency and Derived Values

The database should distinguish between authoritative records and derived values.

For example:

- Payments received are authoritative financial records.
- Outstanding balance is calculated from financial obligations and receipts.
- Installment status can be derived from due amounts, receipts, and dates.
- Dashboard totals are calculated from underlying business records.

Derived values must not become independent sources of truth without a clear reason.

If caching or materialized reporting data is introduced, it must be possible to reconcile it with authoritative records.

Financial calculations must have a single consistent implementation in the backend.

## 15. Data Modeling and ORM Practices

SQLAlchemy models must reflect the database constraints and relationships.

Recommended practices:

- Use SQLAlchemy 2.x typed declarative mappings.
- Use explicit relationships.
- Define foreign keys and unique constraints clearly.
- Avoid excessive implicit relationship loading.
- Avoid N+1 query patterns.
- Use explicit transaction boundaries.
- Keep database models separate from API request and response schemas.
- Avoid placing complex business logic inside ORM models.
- Use repositories or controlled data access services for tenant-scoped queries.

The ORM must not become the only source of data integrity.

Important constraints must also exist in PostgreSQL.

## 16. Migration Strategy

Alembic will manage database schema migrations.

Every schema change must be version-controlled.

### 16.1 Migration Rules

- Migrations must have clear descriptions.
- Migrations must be reviewed before deployment.
- Migrations must preserve existing data.
- Destructive operations require special care.
- Production migrations must be backed by an appropriate recovery plan.
- Schema changes must be tested against a representative database.
- Migration execution must be part of the deployment process.

### 16.2 Backward-Compatible Changes

Whenever practical, schema changes should follow an expand-and-contract strategy.

For example:

1. Add a new nullable column.
2. Deploy code that supports both old and new structures.
3. Populate existing records.
4. Enforce the new constraint.
5. Remove obsolete structures only after compatibility is confirmed.

This reduces deployment risk as the platform evolves.

## 17. Backup and Recovery

The production database must have an explicit backup and recovery strategy.

The strategy must define:

- Backup frequency.
- Backup retention.
- Backup encryption.
- Recovery Point Objective (RPO).
- Recovery Time Objective (RTO).
- Restoration procedures.
- Backup access restrictions.
- Periodic restoration tests.

Backups must be protected with access controls and must not be publicly accessible.

A backup is not considered reliable until restoration has been tested.

Specific infrastructure providers and backup mechanisms will be selected in the deployment documentation.

## 18. Testing Requirements

Database tests must verify both structure and behavior.

### 18.1 Integrity Tests

- Required fields cannot be null.
- Foreign keys reject invalid references.
- Unique constraints work correctly.
- Monetary values preserve decimal precision.
- Invalid status values are rejected where constrained.

### 18.2 Tenant Isolation Tests

- Tenant A cannot reference Tenant B's customers.
- Tenant A cannot associate employees from Tenant B with its events.
- Tenant A cannot access Tenant B's payments.
- Tenant A cannot create cross-tenant relationships.
- Tenant-scoped unique constraints behave correctly.

### 18.3 Financial Tests

- Quotation totals are calculated consistently.
- Quotation versions preserve historical prices.
- Employee compensation snapshots remain unchanged.
- Installment calculations reconcile with the approved total.
- Partial payments are supported.
- Outstanding balances are calculated correctly.
- Staff costs are not double-counted.
- Reversals preserve financial history.

### 18.4 Migration Tests

- Migrations can create a clean database.
- Sequential migrations reach the expected schema.
- Existing data remains valid after migrations.
- Rollback procedures work where supported.
- Production migration procedures are tested before release.

## 19. Initial Database Module Organization

The database schema should reflect the main application domains.

Recommended conceptual organization:

```text
Identity and Access
├── users
├── user_sessions
├── password_reset_tokens
├── email_verification_tokens
├── tenants
├── tenant_memberships
├── roles
├── permissions
└── role_permissions

Customers
└── customers

Workforce
├── employees
├── employee_assignments
└── employee_time_entries

Catalog
├── catalog_categories
├── catalog_items
├── menus
└── menu_items

Quotations
├── quotations
├── quotation_versions
├── quotation_items
└── quotation_approvals

Events
└── events

Payments
├── payment_schedules
├── payment_installments
└── payments

Expenses
└── expenses

Tenant Configuration
└── tenant_settings

Audit
└── audit_logs
```

This is a logical grouping, not a requirement to create separate PostgreSQL schemas.

The final entity list may change as implementation details are refined.

## 20. Open Decisions

The following decisions must be finalized during detailed modeling:

| Decision | Status |
|---|---|
| UUID generation strategy | Recommended |
| Exact field definitions and data types | Open |
| Event date and timezone representation | Open |
| Final quotation item snapshot structure | Open |
| Payment schedule creation timing | Proposed |
| Staff cost reconciliation model | Open |
| Tax calculation and fiscal requirements | Open |
| Soft deletion policy per entity | Open |
| Audit metadata structure | Open |
| PostgreSQL RLS adoption | Open |
| Backup provider and retention | Open |
| Materialized reporting data | Future consideration |

These decisions should be documented through Architecture Decision Records when finalized.

## 21. Architectural Principles

The following principles are mandatory:

1. PostgreSQL is the authoritative relational database.
2. Tenant ownership must be explicit and enforced.
3. Tenant-scoped relationships must be protected by database constraints.
4. Financial values must use exact decimal types.
5. Historical commercial and financial snapshots must be preserved.
6. Critical business operations must use transactions.
7. Repeated operations must be idempotent where required.
8. Audit records must preserve critical business history.
9. Schema changes must be managed through Alembic.
10. Database access must be tested for tenant isolation and financial consistency.
11. Backup and restoration procedures must be established before production.
12. The database schema must evolve deliberately rather than through uncontrolled changes.

---

**End of document.**