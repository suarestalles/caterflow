# CaterFlow — System Architecture

**Version:** 0.1  
**Status:** Initial Draft  
**Architecture Style:** Modular Monolith  
**Deployment Model:** Cloud SaaS  
**Initial Market:** Spain

## 1. Architecture Overview

CaterFlow will use a modular monolithic architecture.

The platform will consist of a web frontend, a centralized backend API, a relational database and an externalized file storage layer.

The application will serve multiple independent catering companies through a shared application infrastructure and a shared PostgreSQL schema.

The architecture must prioritize:

- Maintainability.
- Tenant data isolation.
- Security.
- Business logic consistency.
- Testability.
- Operational reliability.
- Future scalability.

Microservices are not required for the initial product.

## 2. Technology Stack

### 2.1 Frontend

| Technology | Responsibility |
|---|---|
| Next.js | Web application framework |
| React | User interface |
| TypeScript | Static typing |
| Tailwind CSS | Styling |
| shadcn/ui | Reusable interface components |

The frontend will provide:

- Responsive layouts.
- Authenticated application areas.
- Role-aware navigation.
- Forms and data tables.
- Dashboard visualizations.
- Quotation and event management interfaces.
- Multilingual user interface.

### 2.2 Backend

| Technology | Responsibility |
|---|---|
| Python | Backend language |
| FastAPI | REST API framework |
| Pydantic | Data validation and serialization |
| SQLAlchemy 2.x | ORM and database access |
| Alembic | Database migrations |
| Pytest | Automated backend testing |

The backend will be responsible for:

- Authentication and authorization.
- Tenant context resolution.
- Business rule enforcement.
- Data validation.
- Financial calculations.
- Database transactions.
- Document generation.
- File storage coordination.
- Audit logging.

### 2.3 Database

PostgreSQL will be the primary relational database.

The initial architecture will use:

- One database.
- One shared schema.
- Tenant-owned records associated with tenant_id.
- Foreign key constraints.
- Appropriate indexes.
- Transactional consistency.
- Database migrations managed by Alembic.

### 2.4 File Storage

The system will use a storage abstraction layer.

Supported file categories may include:

- Company logos.
- Generated quotation PDFs.
- Event attachments.
- Expense receipts.

Local storage may be used during development.

Production storage should use a managed object storage service compatible with the application storage interface.

Business modules must not depend directly on a specific storage provider.

### 2.5 Infrastructure

The development environment will use Docker Compose where appropriate.

Production infrastructure must support:

- HTTPS.
- Secure environment configuration.
- PostgreSQL persistence.
- Application logging.
- Database backups.
- File storage.
- Health checks.
- Database migrations during controlled deployments.

Specific cloud providers will be selected separately in the deployment documentation.

## 3. High-Level System Components

### 3.1 Web Application

The frontend is responsible for presentation and user interaction.

Its responsibilities include:

- Rendering application pages.
- Managing navigation.
- Collecting user input.
- Performing client-side validation for usability.
- Calling backend API endpoints.
- Displaying API responses and errors.
- Applying language and locale preferences.

The frontend must not be trusted to enforce security or business rules.

All critical validation must also exist on the backend.

### 3.2 REST API

The backend exposes REST endpoints through FastAPI.

API responsibilities include:

- Receiving requests.
- Authenticating users.
- Resolving tenant context.
- Checking permissions.
- Validating input.
- Executing business operations.
- Managing database transactions.
- Returning structured responses.

API endpoints should follow consistent naming and response conventions.

### 3.3 Application and Domain Logic

Business rules must be separated from HTTP endpoint definitions.

The backend should distinguish:

- API layer: HTTP requests and responses.
- Application layer: use cases and orchestration.
- Domain layer: business rules and entities.
- Infrastructure layer: database, storage and external services.

This separation allows business logic to be tested independently of the web framework.

### 3.4 Persistence Layer

Database access will be handled through SQLAlchemy repositories or equivalent persistence abstractions.

Responsibilities include:

- Creating and retrieving records.
- Updating authorized records.
- Managing relationships.
- Enforcing tenant-scoped queries.
- Managing transactions.
- Preserving historical data.

The application layer must not bypass tenant isolation when accessing tenant-owned records.

## 4. Modular Backend Architecture

The backend will be organized into business modules.

### 4.1 Identity Module

Responsibilities:

- User accounts.
- Password management.
- Authentication.
- JWT token issuance and validation.
- Role and permission management.
- Tenant membership.

### 4.2 Tenants Module

Responsibilities:

- Company registration.
- Company profile.
- Tenant settings.
- Currency and timezone configuration.
- Language preferences.
- Company branding.

### 4.3 Customers Module

Responsibilities:

- Customer registration.
- Contact information.
- Customer history.
- Customer relationships with quotations and events.

### 4.4 Catalog Module

Responsibilities:

- Dishes.
- Beverages.
- Categories.
- Menu packages.
- Optional recipes and technical information.

### 4.5 Pricing Module

Responsibilities:

- Pricing configuration.
- Price calculations.
- Discounts.
- Additional charges.
- Pricing snapshots.

### 4.6 Quotations Module

Responsibilities:

- Quotation creation.
- Quotation versions.
- Commercial snapshots.
- Approval records.
- PDF generation requests.
- Conversion into events.

### 4.7 Events Module

Responsibilities:

- Event creation.
- Event status management.
- Operational planning.
- Event information.
- Event history.

### 4.8 Workforce Module

Responsibilities:

- Fixed employee registration.
- Freelancer registration.
- Employee assignments.
- Working-hour records.
- Compensation snapshots.

### 4.9 Payments Module

Responsibilities:

- Payment configuration.
- Installment schedules.
- Payment registration.
- Partial payments.
- Outstanding balances.
- Refund and correction records.

### 4.10 Expenses Module

Responsibilities:

- Actual event expenses.
- Expense categories.
- Expense attachments.
- Expense corrections.
- Expense history.

### 4.11 Reporting Module

Responsibilities:

- Dashboard indicators.
- Event financial summaries.
- Quotation metrics.
- Payment indicators.
- Expense summaries.

Financial indicators must distinguish approved commercial amounts, received payments, outstanding balances and recorded expenses.

### 4.12 Audit Module

Responsibilities:

- Audit event registration.
- Historical traceability.
- User and timestamp identification.
- Relevant change information.

### 4.13 Storage Module

Responsibilities:

- File upload.
- File retrieval.
- File deletion according to authorized retention policies.
- Storage provider abstraction.
- File metadata management.

## 5. Request Processing Flow

A typical authenticated request must follow this sequence:

1. The frontend sends an HTTPS request.
2. The backend validates the authentication token.
3. The backend identifies the authenticated user.
4. The active tenant context is validated.
5. The user's membership and permissions are checked.
6. Request data is validated.
7. The relevant application use case is executed.
8. Database operations are performed within an appropriate transaction.
9. Audit information is recorded where required.
10. A structured response is returned to the frontend.

Tenant context must be validated on every protected request.

A tenant identifier supplied by the frontend must never be trusted without membership validation.

## 6. Multi-Tenant Architecture

CaterFlow will use a shared database and shared schema strategy.

All tenant-owned records must be associated with a tenant identifier.

Core requirements:

- Tenant-scoped database access.
- Tenant-aware service operations.
- Tenant-aware unique constraints where appropriate.
- Foreign key relationships that prevent cross-tenant associations.
- Automated isolation tests.
- Centralized tenant context handling.

Database Row-Level Security may be evaluated as an additional protection layer.

Detailed implementation rules will be documented in MULTI_TENANCY.md.

## 7. Authentication and Authorization

Authentication will use JWT-based access tokens.

The application will distinguish:

- Authentication: identifying the user.
- Authorization: determining what the user may do.
- Tenant membership: determining which companies the user may access.

Roles and permissions must be evaluated in the active tenant context.

Sensitive operations must require explicit permissions.

Detailed token management and security rules will be documented in AUTHENTICATION.md.

## 8. API Design

The backend will expose versioned REST endpoints.

Initial API prefix:

`/api/v1`

Example resource groups:

- `/auth`
- `/tenants`
- `/users`
- `/customers`
- `/catalog`
- `/pricing`
- `/quotations`
- `/events`
- `/employees`
- `/payments`
- `/expenses`
- `/reports`

API conventions:

- JSON request and response bodies.
- Consistent HTTP status codes.
- Pydantic request and response schemas.
- Pagination for collections.
- Consistent error structures.
- Explicit validation.
- OpenAPI documentation generated by FastAPI.

The API must not expose internal database models directly.

## 9. Frontend Architecture

The frontend will organize code by application features.

Expected feature areas:

- Authentication.
- Company selection.
- Dashboard.
- Customers.
- Catalog.
- Quotations.
- Events.
- Workforce.
- Payments.
- Expenses.
- Settings.

Reusable components should be centralized.

API communication should use a consistent client layer.

Authentication and active tenant context must be handled consistently across protected pages.

## 10. Internationalization

The application will support:

- Portuguese.
- Spanish.
- English.

Internationalization must cover:

- Interface messages.
- Validation messages.
- Dates and times.
- Numbers.
- Monetary values.
- Generated documents.

The application will use locale-aware formatting.

The initial Spanish market will use EUR as the default currency and Europe/Madrid as the default timezone.

Tenant and user preferences must be handled according to the product's localization rules.

## 11. Financial Architecture

Financial operations must use decimal arithmetic.

The system must preserve:

- Approved quotation snapshots.
- Payment schedule snapshots.
- Payment transaction history.
- Employee compensation snapshots.
- Actual expense records.

Reporting logic must distinguish financial concepts rather than treating all monetary values as revenue.

The financial result calculations will be centralized in the backend.

## 12. Document Generation

Quotation PDFs must be generated by the backend.

The document generation process must:

- Retrieve the appropriate quotation version.
- Use the company's branding.
- Apply the selected language.
- Format dates and monetary values according to locale.
- Preserve the commercial information represented by that version.
- Store generated files through the storage abstraction.

PDF generation must not modify the original quotation data.

## 13. Transaction Management

Operations involving multiple related records must use database transactions.

Examples include:

- Creating an approved quotation and its payment schedule.
- Converting a quotation into an event.
- Registering a payment and updating its related balances.
- Recording event expense information.
- Replacing an employee assignment.

Operations must avoid partially completed business transactions.

Where external services are involved, the system must define appropriate retry and failure-handling strategies.

## 14. Error Handling and Observability

The backend must provide consistent error responses.

Expected categories include:

- Authentication errors.
- Authorization errors.
- Tenant access errors.
- Validation errors.
- Business rule violations.
- Resource not found.
- Unexpected internal errors.

Logs should contain sufficient technical context for troubleshooting without exposing passwords, access tokens or unnecessary personal data.

The application should expose health checks for deployment monitoring.

## 15. Testing Strategy

The architecture must support automated testing.

Backend testing:

- Unit tests.
- Service and use-case tests.
- API integration tests.
- Database integration tests.
- Tenant isolation tests.
- Financial calculation tests.

Frontend testing:

- Component tests.
- Form validation tests.
- Feature tests.
- Critical user journey tests.

End-to-end testing should cover important workflows such as quotation approval, event creation and payment registration.

Detailed testing standards will be documented in TESTING.md.

## 16. Deployment Architecture

The production application will run in a cloud environment.

The initial production architecture should include:

- Web frontend deployment.
- Backend API deployment.
- Managed or reliably hosted PostgreSQL.
- Object storage.
- HTTPS.
- Application monitoring.
- Automated database backups.

Frontend and backend may be deployed independently while remaining part of the same product.

Deployment configuration must use environment variables and secure secret management.

Detailed infrastructure decisions will be documented in DEPLOYMENT.md.

## 17. Scalability Strategy

The initial system will remain a modular monolith.

Future scaling options may include:

- Horizontal API scaling.
- Database query optimization.
- Connection pooling.
- Caching.
- Background task processing.
- Separate worker processes.
- Dedicated reporting infrastructure.

These capabilities should only be introduced when justified by actual workload or product requirements.

Microservices are not part of the initial architecture.

## 18. Architecture Principles

The following principles must guide implementation:

1. Business rules belong in the backend.
2. Tenant isolation is mandatory.
3. Financial calculations use decimal arithmetic.
4. Historical commercial information must be preserved.
5. Modules should have clear responsibilities.
6. External infrastructure must be accessed through abstractions.
7. Critical operations must be transactional.
8. Security must be enforced server-side.
9. Automated tests must cover critical business rules.
10. Complexity should only be introduced when justified.

## 19. Open Technical Decisions

The following decisions require further specification:

1. Exact cloud hosting provider.
2. Exact PostgreSQL hosting strategy.
3. Object storage provider.
4. JWT refresh-token lifecycle and revocation strategy.
5. Whether Row-Level Security will be enabled.
6. PDF generation library and rendering strategy.
7. Whether background workers are needed in the first release.
8. Email delivery provider.
9. Frontend authentication and token storage strategy.
10. Production monitoring and error tracking provider.

---

**Document status:** Initial architecture specification. Detailed implementation decisions will be documented in the corresponding architecture and development documents.