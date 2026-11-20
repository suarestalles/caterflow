CaterFlow — System Architecture
Version: 0.2
Status: Implementation-aligned architecture; backend core in development
Architecture Style: Modular Monolith
Deployment Model: Cloud SaaS (target architecture)
Initial Market: Spain
Last updated: November 20, 2026
1. Architecture Overview
CaterFlow uses a modular monolith as its target and current backend architecture. The backend is a single FastAPI application organized into business modules and shared infrastructure. The application uses PostgreSQL through SQLAlchemy and exposes versioned REST endpoints.

The intended product architecture consists of:
- A web frontend, planned with Next.js, React and TypeScript.
- A centralized backend API built with FastAPI.
- A shared PostgreSQL database and schema for all tenants.
- An application-level tenant isolation mechanism.
- Alembic-managed database migrations.
- A storage abstraction for future file-based features.
The backend foundation and several core business modules have been implemented. The complete frontend, remaining operational and financial modules, document generation, and production deployment are still pending. This document distinguishes the implemented architecture from planned components.

The architecture prioritizes:
- Maintainability and clear module boundaries.
- Tenant data isolation.
- Server-side security and authorization.
- Consistent business rules.
- Exact financial calculations.
- Testability and controlled schema evolution.
- Operational reliability without premature infrastructure complexity.
Microservices are not required for the MVP.
2. Technology Stack
2.1 Frontend
Planned stack; not yet considered a completed application layer.
Technology	Intended responsibility	Status
Next.js	Web application framework	Planned
React	User interface	Planned
TypeScript	Static typing	Planned
Tailwind CSS	Styling	Planned
shadcn/ui	Reusable interface components	Planned


The frontend is expected to provide responsive layouts, authenticated application areas, role-aware navigation, forms, data tables, dashboards, quotation management and event management. It must communicate with the backend through the documented API rather than accessing PostgreSQL directly.

Frontend implementation and its test strategy must be tracked separately from the currently implemented backend modules.
2.2 Backend
Technology	Responsibility	Status
Python 3.12	Backend language/runtime	Implemented
FastAPI	REST API framework	Implemented
Pydantic v2	Request validation and response serialization	Implemented
SQLAlchemy 2.x	ORM and database access	Implemented
Alembic	Database schema migrations	Implemented
Pytest	Automated backend tests	Implemented
Ruff	Python linting and formatting checks	Configured and used in development
uv	Python environment and dependency management	Used in development


The backend is responsible for:
- Authentication and authorization.
- Tenant context resolution and tenant-scoped data access.
- Business rule enforcement.
- Request validation and response serialization.
- Financial calculations using decimal arithmetic.
- Database transactions and persistence.
- The current customer, event, catalog and quotation workflows.
Document generation, file storage coordination, centralized audit logging and external service integrations are planned responsibilities, not completed capabilities.
2.3 Database
PostgreSQL is the primary relational database. The current development environment uses PostgreSQL 17, with the database run through Docker.

The architecture uses:
- One database.
- One shared schema.
- Multiple tenants.
- A tenant_id ownership column on tenant-scoped records.
- Relational constraints, including composite foreign keys where tenant boundaries must be preserved.
- Alembic migrations for schema evolution.
Separate databases or PostgreSQL schemas per tenant are outside the current MVP architecture.
2.4 File Storage
A storage abstraction is part of the target architecture, but a production storage adapter is not yet implemented.

Future file categories may include:
- Company logos.
- Generated quotation PDFs.
- Event attachments.
- Expense receipts.
Local storage may be used during development when file features are introduced. Production storage should use a managed object storage provider behind an application-level interface. Business modules must not depend directly on a specific provider.
2.5 Infrastructure
Current development infrastructure includes a local Python environment, Docker-based PostgreSQL and a separate test database.

The production target must support:
- HTTPS.
- Secure environment configuration and secrets.
- Persistent PostgreSQL storage.
- Application logging and monitoring.
- Database backups and tested restoration procedures.
- File storage when required by released features.
- Health checks.
- Controlled Alembic migration execution during deployment.
Cloud providers, production topology and CI/CD provider remain to be selected and validated in the deployment phase. Production deployment is not yet complete.
3. High-Level System Components
3.1 Web Application
Status: Planned.

The frontend will be responsible for presentation and user interaction:
- Rendering application pages and navigation.
- Collecting user input.
- Performing client-side validation for usability.
- Calling backend API endpoints.
- Displaying API responses and errors.
- Applying language and locale preferences.
The frontend must not be trusted to enforce security, tenant isolation or business rules. Critical validation must remain in the backend.
3.2 REST API
Status: Implemented for the current backend modules.

FastAPI exposes versioned REST endpoints under /api/v1.

The API layer is responsible for:
- Receiving and validating HTTP requests.
- Resolving authenticated user and tenant context through dependencies.
- Applying permission requirements.
- Calling the relevant service operation.
- Translating business exceptions into appropriate HTTP responses.
- Serializing responses through Pydantic schemas.
Current business endpoint groups include authentication, tenant/platform operations, clients, events, products, product categories and quotes. The exact route inventory is defined by the routers and endpoint modules in the codebase.
3.3 Application and Business Logic
Status: Implemented through service modules for the current business domains.

Business rules are kept out of HTTP endpoint functions. Service modules coordinate validation, repositories, domain models and transaction boundaries.

The current codebase does not implement a separate, formal domain-model package. SQLAlchemy models represent persisted entities, while service functions implement use cases and business rules. This is the actual architecture and should not be described as a fully separate domain layer.
3.4 Persistence Layer
Status: Implemented.

SQLAlchemy models define persisted entities, relationships, constraints and indexes. Repository modules provide controlled database operations for business services.

The current separation is:
- API: HTTP routing, dependency injection and HTTP error mapping.
- Schemas: Pydantic request and response contracts.
- Services: business rules, orchestration and transaction handling.
- Repositories: database queries and persistence operations.
- Models: SQLAlchemy mappings and relational constraints.
- Database infrastructure: engine/session configuration and tenant-aware sessions.
Repositories generally flush changes but do not commit. Services own the transaction boundary for their use cases and commit or roll back as appropriate.
4. Modular Backend Architecture
The backend is organized as a modular monolith under backend/app/, with shared modules for API, core configuration/security, database infrastructure, models, schemas, repositories and services.
4.1 Identity and Access Module
Status: Implemented backend foundation.

Current responsibilities and capabilities include:
- User records and password hashing.
- Authentication and access-token handling.
- Refresh-token persistence/lifecycle support.
- Tenant memberships.
- Roles and permissions.
- Permission checks for protected operations.
Password recovery, email verification and other account lifecycle flows must be treated as pending unless implemented and tested in the repository.
4.2 Tenants Module
Status: Core tenant and membership foundation implemented; full company configuration pending.

Implemented responsibilities include tenant records, tenant memberships, tenant context resolution and tenant-scoped database access.

Company profile settings, branding, tenant-level currency/language/timezone configuration and a complete membership administration interface remain planned.
4.3 Clients Module
Status: Backend CRUD implemented.

The codebase uses the domain term Client and the database table clients (rather than the conceptual name customers). The module supports tenant-scoped customer records, retrieval, listing, updates and logical archiving, with contact/address information and validation.
4.4 Events Module
Status: Backend CRUD and lifecycle rules implemented; commercial conversion workflow pending.

The current Event model is associated with a Client through a tenant-scoped relationship. Implemented capabilities include event creation, listing, retrieval, updating and cancellation, together with status validation.

Current event statuses are:
- draft
- confirmed
- in_progress
- completed
- cancelled
Creating an event directly from an approved quotation, event staffing, workforce planning, calendar UI and full event closure workflow are not yet implemented.
4.5 Products and Services Catalog Module
Status: Backend CRUD implemented.

The catalog uses one Product model for both physical products and services, differentiated by the type field. It includes:
- Product/service categories with optional parent-child hierarchy.
- Optional category assignment to products.
- Product names and descriptions.
- Static, code-defined units for the current MVP.
- Optional SKU with tenant-scoped uniqueness.
- Sale and cost prices represented using numeric decimal columns.
- Active/inactive state and logical archiving.
- Tenant-scoped queries and authorization permissions.
Menu packages, menu composition, recipe management, ingredient costing and inventory are not implemented in this module.
4.6 Quotations Module
Status: Core backend quotation workflow implemented; version approval and document generation pending.

The current Quote and QuoteItem models support:
- Tenant-scoped quote creation and retrieval.
- Client association and optional Event association.
- Per-tenant sequential quote numbers.
- Draft updates and quote sending.
- Quote duplication into an independent draft.
- Item quantities, prices and calculated totals.
- Discounts and tax amounts.
- Optional catalog product/service association through QuoteItem.product_id.
- Snapshot preservation of item name, description, unit and negotiated unit price.
When a catalog item is selected, the service resolves the current catalog data and stores a snapshot in the quote item. A manually supplied unit price can override the catalog sale price. Historical quote item values are not recalculated when the catalog later changes.

The current quote status set includes draft, sent, accepted, rejected, expired and cancelled. The existence of a status value does not mean that its complete workflow exists. In particular, quotation versioning, approval recording, customer approval evidence, conversion into events and PDF generation remain pending.
4.7 Workforce Module
Status: Planned.

Future responsibilities include fixed employee and freelancer records, event assignments, working-hour records, compensation configuration and compensation snapshots. No complete workforce business module is currently implemented.
4.8 Payments Module
Status: Planned.

Future responsibilities include payment schedules, installments, payment registration, partial payments, outstanding balances, reversals and refunds. These capabilities are not currently implemented.
4.9 Expenses Module
Status: Planned.

Future responsibilities include event expense records, categories, receipts, corrections and expense history. This module is not currently implemented.
4.10 Reporting Module
Status: Planned.

Future responsibilities include operational dashboards, quotation metrics, payment indicators, expense summaries and event financial results. No reporting/dashboard module is currently implemented.
4.11 Audit Module
Status: Planned.

A centralized, append-oriented audit log for important business operations is part of the target architecture but is not yet implemented as a complete module.
4.12 Storage and Document Module
Status: Planned.

Future responsibilities include file upload/retrieval, storage provider abstraction, quotation PDF generation and secure tenant-scoped document access.
5. Request Processing Flow
A typical protected request follows this sequence:
1. The client sends a request to the FastAPI application.
2. Authentication dependencies validate the access token and resolve the user.
3. The active tenant context is resolved and validated.
4. Permission dependencies verify that the user has the required permission code in that tenant context.
5. Pydantic validates the request payload and query parameters.
6. The endpoint calls the relevant service function.
7. The service applies business rules and calls repositories as needed.
8. Tenant-aware SQLAlchemy sessions scope ORM access to the active tenant.
9. The service commits the transaction or rolls it back on failure.
10. The endpoint returns a schema-validated response or maps a known service exception to an HTTP error.
A tenant identifier supplied in an untrusted request payload must never be used as proof of authorization or record ownership. Tenant ownership is derived from the validated authenticated context.
6. Multi-Tenant Architecture
Status: Application-level tenant isolation implemented; PostgreSQL RLS deferred.

CaterFlow uses a shared PostgreSQL database and schema. Tenant-owned models use the TenantScoped mixin, which provides a UUID tenant_id foreign key to the tenant table.

The current isolation approach uses:
- TenantSession for tenant-scoped ORM database access.
- ORM execution criteria to restrict tenant-scoped queries to the active tenant.
- Flush-time validation to ensure tenant ownership on inserts, updates and deletes.
- Restrictions on unsafe Core/text/bulk insert paths in tenant sessions.
- Composite foreign keys for relationships where both records must belong to the same tenant.
- Service-level authorization and validation.
- Automated tenant isolation tests.
Composite tenant-aware relationships are used where appropriate, including relationships between Events and Clients, Products and Product Categories, Quotes and Clients/Events, and Quote Items and their parent Quote or associated Product.

PostgreSQL Row-Level Security (RLS) is explicitly postponed. It must not be described as enabled or relied upon by the current application. The current security boundary is implemented by backend application logic, tenant-aware sessions and database constraints.

Detailed rules are documented in MULTI_TENANCY.md.
7. Authentication and Authorization
Status: Backend implementation present; full product account and user-management experience pending.

The architecture distinguishes:
- Authentication: identifying the user.
- Authorization: determining which actions the user may perform.
- Tenant membership: determining which tenant contexts the user may access.
The current RBAC design uses permission codes rather than role names as the authorization contract. Roles are tenant-scoped; permission definitions are global; membership-role assignments and role-permission assignments preserve tenant ownership. A membership may have multiple roles, and effective permissions are the union of permissions granted by those roles.

Protected endpoints use backend permission dependencies. JWT contents are not treated as the source of current permissions; authorization is evaluated by the backend using the active tenant context.

The detailed token lifecycle is documented in AUTHENTICATION.md, and security controls are documented in SECURITY.md.
8. API Design
The backend exposes versioned REST endpoints under:

/api/v1

Implemented resource groups include:
- Authentication and platform/tenant operations.
- /clients
- /events
- /products
- /product-categories
- /quotes
Other resource groups in the initial product concept (for example employees, payments, expenses, reports and settings) remain planned.

API conventions include:
- JSON request and response bodies.
- Pydantic request and response schemas.
- Explicit input validation.
- Pagination for collection endpoints where applicable.
- Appropriate HTTP status codes.
- Backend permission checks.
- Service exception mapping at the HTTP boundary.
- OpenAPI documentation generated by FastAPI.
API endpoints must not expose SQLAlchemy models as request contracts. Response schemas may serialize ORM objects through Pydantic's attribute support.
9. Frontend Architecture
Status: Planned.

The intended frontend will be organized by application features, including:
- Authentication.
- Company/tenant context.
- Dashboard.
- Clients.
- Catalog.
- Quotations.
- Events.
- Workforce.
- Payments.
- Expenses.
- Settings.
Reusable components and a consistent API client should be centralized. Authentication and active tenant context must be managed consistently across protected pages.

The frontend must not connect directly to PostgreSQL or reproduce backend authorization as its only security control.
10. Internationalization
Status: Product requirement; full application implementation pending.

The product scope identifies Portuguese, Spanish and English as target languages. Internationalization must eventually cover interface messages, validation messages, dates, times, numbers, monetary values and generated documents.

The initial market is Spain. EUR is the initial default currency and Europe/Madrid is the default timezone. Tenant-specific currency, language and timezone configuration is part of the planned company settings capability and must not be represented as fully implemented unless verified in the application.
11. Financial Architecture
Status: Monetary foundations implemented in Quotes; broader financial modules planned.

The current quotation implementation uses Python Decimal and PostgreSQL NUMERIC columns for monetary values. Quote item totals and quote totals are calculated in the backend, with explicit two-decimal rounding.

Catalog sale and cost prices also use numeric decimal columns. A quotation item stores its own item description, unit and unit price, preserving a commercial snapshot independent of later catalog changes.

The broader financial architecture must eventually preserve:
- Approved quotation snapshots.
- Payment schedule and installment snapshots.
- Payment transaction history.
- Employee compensation snapshots.
- Actual expense records.
Payments, installments, expenses and financial reporting are not yet implemented. The architecture must distinguish commercial value, cash received, outstanding balance, estimated costs and actual expenses when those modules are introduced.
12. Document Generation
Status: Planned.

Quotation PDF generation is not currently implemented. When introduced, the backend document workflow must:
- Retrieve the relevant quotation data/version.
- Use company branding.
- Apply the selected document language.
- Format dates and monetary values appropriately.
- Preserve the commercial information represented by the document.
- Store generated files through the storage abstraction.
- Enforce tenant-scoped access to generated documents.
Document generation must not modify the underlying quotation or its historical item snapshots.
13. Transaction Management
Critical business operations use database transactions. Current services generally perform their writes through repositories, flush changes and commit at the service boundary; exceptions trigger rollback.

Implemented transactional use cases include current client, event, product/category and quotation operations.

Future multi-record workflows will also require transactional handling, including:
- Recording quotation approval and its approved snapshot.
- Converting an approved quotation into an event.
- Generating payment schedules and installments.
- Registering payments and updating derived balances.
- Recording expenses.
- Replacing employee assignments while preserving history.
Operations involving external services will require explicit retry, idempotency and failure-handling strategies when those integrations are introduced.
14. Error Handling and Observability
The current API maps known authentication, authorization, not-found and business-validation failures to appropriate HTTP responses. Unexpected errors must not expose secrets or unnecessary internal details to clients.

The target production architecture should include:
- Structured application logs.
- Correlation/request identifiers where appropriate.
- Health checks.
- Error monitoring.
- Operational metrics.
- Alerts for critical failures.
A complete production observability stack is not yet deployed.
15. Testing Strategy
Status: Backend automated tests implemented across current modules.

The backend test suite includes tests for:
- Authentication and security behavior.
- Tenant authentication and tenant-scoped sessions.
- Permissions and RBAC.
- Client repositories, services and API endpoints.
- Event repositories, services and API endpoints.
- Product and category repositories, services and API endpoints.
- Quote repositories, services and API endpoints.
- Tenant isolation and relevant database constraints.
The current test database is separate from the development database and is guarded by a database-name check. The test fixture currently rebuilds its schema from SQLAlchemy metadata using drop_all() and create_all() after that guard. This is test-only behavior; it is not part of application startup or production deployment.

Production and shared development schema changes must be applied through Alembic migrations. Improving the test fixture to apply Alembic migrations is a future testing-infrastructure improvement, not a reason to run destructive schema operations in application startup.

Frontend component, feature and end-to-end tests remain pending with the frontend implementation.

Detailed testing standards are documented in TESTING.md.
16. Deployment Architecture
Status: Production deployment pending.

The target production architecture includes:
- Web frontend deployment.
- Backend API deployment.
- Managed or reliably hosted PostgreSQL.
- Object storage when file features are released.
- HTTPS and domain configuration.
- Secure environment variables and secrets.
- Controlled Alembic migration execution.
- Automated backups and tested restoration.
- Application monitoring and logging.
The API process must not call Base.metadata.drop_all() or Base.metadata.create_all() as part of application startup. Production schema changes are managed through reviewed Alembic migrations. Test-only fixture code must remain isolated from the production application.

Detailed infrastructure decisions belong in DEPLOYMENT.md.
17. Scalability Strategy
The initial system remains a modular monolith. Future scaling options may include:
- Horizontal API scaling.
- Database query and index optimization.
- Connection pooling.
- Caching where justified.
- Background task processing.
- Separate worker processes.
- Dedicated reporting infrastructure.
These capabilities should be introduced only when justified by real workload or product requirements. Microservices, message brokers and distributed infrastructure are not part of the current MVP architecture.
18. Architecture Principles
The following principles guide implementation:
1. Business rules belong in backend services, not only in HTTP endpoints or frontend code.
2. Tenant isolation is mandatory and must be enforced server-side.
3. Tenant-scoped relationships must preserve tenant ownership.
4. Financial calculations use decimal arithmetic.
5. Historical commercial snapshots must be preserved.
6. Repositories handle persistence; services own business orchestration and transaction boundaries.
7. Critical operations must be transactional.
8. Authorization uses explicit permission codes and backend checks.
9. Database schema changes are managed through Alembic migrations.
10. Automated tests must cover critical business rules and tenant isolation.
11. External infrastructure must be accessed through abstractions where appropriate.
12. Complexity should only be introduced when justified by product requirements or actual workload.
19. Open Technical Decisions
The following decisions remain open or require further validation:
1. Production cloud hosting provider and topology.
2. Production PostgreSQL hosting strategy.
3. Object storage provider and file lifecycle policy.
4. Final refresh-token lifecycle, revocation and recovery flows as the authentication product evolves.
5. Whether PostgreSQL Row-Level Security will be introduced; currently deferred.
6. PDF generation library and rendering strategy.
7. Whether background workers are needed for the first release.
8. Email delivery provider.
9. Frontend authentication and token storage strategy.
10. Production monitoring and error-tracking provider.
11. Full tenant company-settings model and configuration interface.
12. Migration-based setup for the automated test database.
Document status: Updated to reflect the implemented backend architecture and the remaining planned components. The modular monolith and shared-schema SaaS architecture remain the target. Implementation status must be reviewed as additional modules are completed.