CaterFlow — MVP Scope
Version: 0.2
Status: In implementation — core backend modules implemented; tenant-facing frontend and remaining MVP workflows pending
Product: CaterFlow SaaS
Initial Market: Spain
Deployment Model: Cloud SaaS (target)
Supported Languages: Portuguese, Spanish and English (frontend localization foundation implemented; complete translation coverage pending)

Last updated: November 27, 2026

## 1. MVP Objective
The objective of the CaterFlow MVP is to deliver a functional catering management platform that centralizes the essential commercial, operational and financial workflows of small and medium-sized catering companies.

The MVP is intended to provide sufficient functionality for a real catering company to manage its customers, quotations, events, employees, payments and expenses without relying on disconnected spreadsheets and paper-based processes.

The first release will prioritize reliability, usability, data security and operational efficiency.

Current implementation status: The backend foundation and initial customer, event, catalog and quotation workflows are implemented. The complete commercial-to-operational-to-financial workflow is not yet available, and the platform is not ready for pilot validation.

## 2. Target Users
The MVP is intended to support the following user profiles:
Profile	Current status
Platform Administrator	Platform authentication and administration workflows implemented; tenant and global user management available through the Platform Admin frontend.
Company Owner	Tenant, membership, permission, workforce and payment backend foundations implemented; company settings and remaining business workflows pending.
Company Administrator	Tenant-scoped RBAC implemented; complete tenant-facing user and company configuration interfaces pending.
Manager	Backend APIs available for customers, catalog, quotations, events, workforce and payments; expenses and reporting pending.
Chef	Dedicated kitchen and menu workflows pending.
Fixed Employee	Workforce backend implemented; dedicated employee-facing access and interface pending.
Freelancer	Workforce backend implemented; dedicated freelancer-facing access and interface pending.


Permissions are managed through backend role-based access control (RBAC), using permission codes rather than authorization based on role names. The permission system supports tenant-specific roles and multiple roles per membership. The complete set of user-facing workflows for every target profile is still pending.

## 3. Functional Scope
The status labels below distinguish implemented backend behavior from planned functionality. A module is not considered fully complete merely because its initial API or data model exists.

### 3.1 Tenant and Company Management
Priority: P0 — Essential
Implementation status: Partially implemented

Implemented:
- Tenant creation and persistence.
- Tenant memberships and tenant context resolution.
- Tenant-scoped database sessions and application-level data isolation.
- Backend authorization using tenant memberships and permissions.
Pending:
- Complete company profile configuration.
- Company logo, address and contact details.
- Tax identification information and related company settings.
- Default currency, language and timezone configuration.
- User invitations and complete membership management workflows.
- Tenant-specific application settings and company branding interface.
Each company must access only its own data. Application-level tenant isolation is implemented and covered by automated tests. PostgreSQL Row-Level Security (RLS) is deferred; it is not part of the current implementation.

### 3.2 Authentication and Access Control
Priority: P0 — Essential
Implementation status: Partially implemented

Implemented:
- User authentication and login foundations.
- JWT-based access authentication.
- Secure password hashing.
- Refresh-token and authentication-session foundations.
- Active tenant context and tenant-scoped authorization.
- Role-based permissions and backend permission checks.
- Platform and tenant authentication foundations.
- Automated tests for authentication, authorization and tenant isolation.
Pending or requiring completion before release:
- Password recovery workflow.
- Email verification where configured.
- Complete user invitation and account activation workflows.
- Final review of logout, token revocation and session lifecycle against the release requirements.
- Authentication rate limiting and production security hardening.

### 3.3 Customer Management
Priority: P0 — Essential
Implementation status: Backend implemented

Implemented:
- Create, list, retrieve and update customers.
- Archive customers without hard deletion.
- Store customer names and contact information.
- Support the current individual/company customer data model.
- Search and pagination.
- Associate customers with quotations and events.
- Enforce tenant isolation and customer-related permissions.
- Repository, service and API automated tests.
Pending or not yet confirmed as complete:
- Complete billing and tax-information workflows required by the initial market.
- Customer history and a consolidated customer activity view.
- Frontend customer management interface.

### 3.4 Catalog Management
Priority: P0 — Essential
Implementation status: Core catalog backend implemented; menu-related functionality pending

Implemented:
- Unified catalog model for physical products and services, differentiated by type.
- Product and service creation, listing, retrieval and updating.
- Product and service descriptions.
- Product categories and hierarchical subcategories.
- Optional category association.
- SKU uniqueness within each tenant when a SKU is provided.
- Standardized units for the initial release.
- Sale and cost prices using decimal monetary values.
- Active/inactive state through logical archiving.
- Tenant isolation, RBAC permissions, migrations and automated tests.
- Optional association between catalog products/services and quotation items.
Pending:
- Menu and menu-package management.
- Menu categories and composition of menu packages from catalog items.
- Recipe and technical information, if confirmed as necessary for the MVP.
- Frontend catalog and menu management interfaces.
The current catalog is intentionally based on one Product model for both products and services. Ingredient-level costing and inventory control remain excluded from the MVP.

### 3.5 Pricing Configuration
Priority: P0 — Essential
Implementation status: Partially implemented

Implemented:
- Sale and cost prices on catalog products/services.
- Decimal monetary storage and calculations.
- Manual negotiated unit prices on quotation items.
- Quotation subtotal, discount, tax and total calculations.
- Preservation of the commercial values stored in quotation items when catalog values change.
Pending:
- Configurable pricing rules per company.
- Different service formats and event types as pricing dimensions.
- Menu-package pricing.
- Quantity-based or tiered pricing rules beyond the current item calculation.
- Optional additional charges and reusable commercial pricing configurations.
- Frontend pricing configuration.
Pricing adjustments made on a quotation do not update the catalog price.

### 3.6 Quotation Management
Priority: P0 — Essential
Implementation status: Core quotation backend implemented; approval, versioning and document workflows pending

Implemented:
- Create quotations for registered customers.
- Optional association with an existing event.
- List and retrieve quotations with filtering and pagination.
- Update draft quotations.
- Calculate subtotal, discount, tax and total amounts in the backend.
- Generate sequential quotation numbers within each tenant.
- Store multiple quotation items.
- Create items manually or link them to catalog products/services.
- Use catalog values as initial item data while allowing negotiated prices.
- Preserve item snapshots, including name, description, unit and unit price.
- Prevent products from other tenants or products that are not available for new quotations from being selected.
- Send quotations and duplicate quotations as independent drafts.
- Preserve catalog links and commercial snapshots when duplicating quotations.
- Enforce tenant isolation and quotation permissions.
- Repository, service and API automated tests for current workflows.
Pending:
- Dedicated customer approval and rejection workflows.
- Complete quotation versioning and version history. Updating a draft is not equivalent to version management.
- Conversion of an approved quotation into an event.
- Quotation PDF generation and company branding.
- Event type, date, location, guest count and service-format workflows as quotation inputs, where required by the final business flow.
- Staffing requirements and staff-cost estimates in quotations.
- Multiple commercial proposals or alternatives within a quotation workflow.
- Frontend quotation editor and customer-facing approval experience.
Historical integrity rule: quotation items store their own commercial snapshots. Changing or archiving a catalog product must not rewrite existing quotation item names, descriptions, units or prices. Catalog association is optional so manually defined items remain supported.

### 3.7 Event Management
Priority: P0 — Essential
Implementation status: Basic event management backend implemented; quotation conversion and workforce workflows pending

Implemented:
- Create, list, retrieve and update events.
- Associate events with customers.
- Store event scheduling information, guest count, address and notes.
- Manage event statuses and validated status transitions.
- Cancel events through the application workflow.
- Enforce tenant isolation and event permissions.
- Repository, service and API automated tests.
Current event statuses include draft, confirmed, in progress, completed and cancelled.

Pending:
- Create events from approved quotations.
- Calendar interface and calendar-based event views.
- Workforce assignment and employee responsibilities.
- Planned and actual working hours.
- Complete event history/audit timeline.
- Frontend event management and operational planning interface.

### 3.8 Employee and Workforce Management

Priority: P0 — Essential

Implementation status: Backend implemented; frontend pending.

Implemented:
- Workforce data management.
- Support for fixed employees and freelancers.
- Employee-related information and compensation configuration.
- Event workforce assignments.
- Compensation information associated with assignments.
- Preservation of historical compensation information where applicable.
- Tenant-scoped access control and backend permission enforcement.
- Automated backend tests for the implemented workforce functionality.

Pending:
- Complete tenant-facing employee management interface.
- Complete event staffing interface.
- Dedicated employee and freelancer access workflows.
- Any additional workforce rules identified during operational validation.

Historical event compensation must not be silently changed when default employee compensation settings are updated.

### 3.9 Payment Management

Priority: P0 — Essential

Implementation status: Backend implemented; frontend pending.

Implemented:
- Payment-related persistence and business logic.
- Payment installment management.
- Payment registration.
- Tracking of payment amounts and outstanding balances.
- Payment status handling.
- Tenant-scoped access control and backend permission enforcement.
- Automated backend tests for the implemented payment functionality.

Pending:
- Complete payment management interface.
- Integration with the final quotation approval and event-conversion workflow.
- Financial reconciliation across payments, expenses and event results.
- External payment provider integrations, which remain outside the initial MVP.

Payment records must preserve financial history. Payment status must remain independent from event operational status.

### 3.10 Event Expense Management

Priority: P0 — Essential

Implementation status: Not started — next backend module.

Planned scope:
- Record actual event expenses.
- Categorize expenses.
- Record descriptions, amounts and dates.
- Associate expenses with events.
- Associate expenses with responsible users where applicable.
- Support optional receipt attachments when storage infrastructure is available.

### 3.11 Dashboard and Basic Reports
Priority: P1 — Important
Implementation status: Not implemented

Planned scope:
- Display upcoming events and event counts.
- Display quotation statuses and total quotation values.
- Display paid and outstanding amounts.
- Display recorded expenses.
- Display estimated versus actual event results.
Financial indicators must clearly distinguish estimated values from recorded actual values. Dashboard values must be derived from tenant-scoped source records.

### 3.12 Audit History
Priority: P0 — Essential
Implementation status: Not implemented as a dedicated audit-history module

Planned scope:
- Record important changes to quotations.
- Record quotation approvals.
- Record event status changes.
- Record payment updates.
- Record expense creation and updates.
- Associate changes with users and timestamps.
The presence of standard created_at and updated_at timestamps does not satisfy the audit-history requirements above.

## 4. Internationalization
Priority: P0 — Essential
Implementation status: Not implemented in the user interface

The MVP must support:
- Portuguese.
- Spanish.
- English.
Requirements:
- All interface text must use a translation system.
- Language selection must be available to users.
- Company-specific language preferences must be supported where appropriate.
- Dates, numbers and monetary values must follow locale conventions.
- Generated PDFs must support the selected document language.
- Translation keys must be centralized and maintainable.
The initial market is Spain. EUR is the intended initial default currency, with currency configuration designed to support future markets. Current decimal monetary storage does not, by itself, constitute multi-currency support or locale-aware formatting.

## 5. Cloud Deployment
Priority: P0 — Essential
Implementation status: Local development foundation exists; production cloud deployment pending

Implemented foundations:
- PostgreSQL database for development.
- SQLAlchemy data access and Alembic migrations.
- Environment-based application configuration.
- Local development and test configuration.
- Application-level tenant data isolation.
Pending:
- Centralized cloud-hosted application.
- Production backend and frontend deployment.
- Managed production PostgreSQL or equivalent hosted database.
- HTTPS and production domain configuration.
- Automated migration execution as part of the deployment process.
- Production backup and recovery strategy.
- Centralized application logging and monitoring.
- Production file storage abstraction and secure document retrieval.
- Production environment and secrets configuration.
- Responsive web application accessible through modern desktop and mobile browsers.

## 6. MVP Exclusions
The following capabilities are not required for the initial release unless pilot validation changes their priority:
Feature	Reason
Public marketplace	Requires a separate commercial and customer acquisition strategy
Customer self-service portal	Not essential for internal operations
Integrated payment processing	Adds financial and provider integration complexity
WhatsApp integration	Can be considered after core workflows are validated
Native mobile applications	Responsive web interface is sufficient initially
Advanced inventory management	Outside the initial operational scope
Automated fiscal integrations	Requires additional legal and technical validation
Banking integrations	Not essential for the first release
AI recommendations	Future enhancement
Advanced analytics	Basic business indicators are sufficient
Custom code per tenant	The product must remain a shared SaaS platform


Ingredient-level costing and inventory movements remain outside the current MVP scope. The menu/recipe scope must be finalized before implementation; it must not be interpreted as a requirement for advanced inventory management.

## 7. Priority Definitions
- P0 — Essential: Required for the MVP to be considered operational.
- P1 — Important: Strongly recommended for the first commercial release, but can be delivered after core workflows.
- P2 — Future: Not required for the MVP.
Priority indicates business importance, not implementation status. A P0 feature may still be pending.

## 8. MVP Acceptance Criteria
The MVP will be considered ready for pilot validation only when all applicable criteria below have been implemented and verified:
#	Acceptance criterion	Current status
1	A company can register and configure its tenant.	Partially met: tenant and membership foundations exist; complete company configuration remains pending.
2	Company users can authenticate securely.	Partially met: core authentication and RBAC exist; account lifecycle and release hardening remain pending.
3	Tenant data is isolated and tested.	Implemented in the backend application layer and covered by automated tests; RLS is deferred.
4	Customers can be registered and managed.	Backend functionality implemented; complete frontend and customer-history experience pending.
5	Dishes, beverages and menu packages can be configured.	Partially met: generic products/services and categories exist; menu packages are pending.
6	A manager can create and revise a quotation.	Partially met: creation and draft updates exist; formal version management is pending.
7	A quotation PDF can be generated using company branding.	Pending.
8	An approved quotation can become an event.	Pending.
9	Fixed employees and freelancers can be assigned to events.	Backend implemented; tenant-facing interface and complete operational validation pending.
10	Payment installments can be configured and tracked.	Backend implemented; frontend and complete end-to-end financial validation pending.
11	Actual event expenses can be recorded.	Pending — Expenses module not started.
12	Basic financial indicators can be displayed.	Pending.
13	Important operations are recorded in the audit history.	Pending: no dedicated audit-history module exists yet.
14	The interface supports Portuguese, Spanish and English.	Pending.
15	The application can be accessed through its cloud deployment.	Pending.
16	Automated tests validate critical business workflows and tenant isolation.	Partially met: backend module and integration tests exist; full MVP and end-to-end acceptance coverage remains pending.


The MVP must not be declared ready for pilot validation until the remaining P0 acceptance criteria have been completed or explicitly re-scoped and approved.

## 9. Pilot Validation
Implementation status: Not started

The first pilot should involve a real catering company operating in Spain.

The pilot should validate:
- Customer registration.
- Quotation creation and revision.
- PDF proposal generation.
- Customer approval recording.
- Event creation and planning.
- Employee assignment.
- Payment tracking.
- Actual expense recording.
- Financial result visibility.
Feedback from the pilot will determine the next development priorities. Pilot validation should begin only after the critical end-to-end workflows and production safeguards are ready.

## 10. Future Development
After MVP validation, potential improvements include:
- Customer self-service portal.
- Digital quotation approval.
- WhatsApp integration.
- Advanced reports.
- Inventory and purchasing management.
- External payment integrations.
- Public catering marketplace.
- Additional currencies and regional configurations.
- Subscription management and automated SaaS billing.
- Advanced employee scheduling.
Future features must be evaluated against feedback from real catering operations and must not delay completion of the core MVP workflows.

## 11. Current Implementation Snapshot
As of November 20, 2026, the following backend capabilities have been implemented and have dedicated automated tests:
Area	Implemented capabilities	Remaining work
Authentication and authorization	Authentication foundations, tenant context, RBAC and permission enforcement	Complete account lifecycle, invitations, recovery and production hardening
Multi-tenancy	Tenant-scoped sessions, application-level isolation and cross-tenant tests	Final production review; RLS remains deferred
Customers	Customer CRUD, search, pagination and logical archiving	Frontend and complete customer-history/billing workflows
Events	Event CRUD, customer association, scheduling fields, status rules and cancellation	Quote conversion, calendar, workforce and full operational history
Products and services	Unified catalog, categories, hierarchy, SKU, units, prices and archiving	Menus, menu packages and frontend
Quotations	CRUD-oriented workflows, calculations, numbering, sending, duplication and item snapshots	Formal approval/versioning, PDFs, event conversion and frontend
Catalog-to-quotation integration	Optional product association, negotiated prices, historical snapshots and link preservation during duplication	Additional workflow validation as adjacent modules are implemented
Payments and expenses	Not implemented	Entire modules
Dashboard and audit history	Not implemented	Reporting and dedicated audit module
Frontend and deployment	Not established as complete by the current backend implementation	User-facing workflows, cloud deployment and production operations


The backend has an established automated test suite covering the implemented modules. The full suite must be rerun after subsequent changes, and frontend, end-to-end and production acceptance tests remain future work.

## 12. Pilot Readiness Principles
Before pilot deployment, CaterFlow must demonstrate the complete workflow from customer and catalog setup through quotation, approval, event execution and financial tracking.

The following principles apply:
1. Security and data integrity take precedence over feature breadth.
2. Every tenant-owned resource must remain isolated at the application layer and be covered by tests.
3. Financial calculations must use decimal monetary values and be independently tested.
4. Historical commercial and financial records must preserve the values that applied when they were created or approved.
5. Important operational changes must become auditable before real business use.
6. Production backups must be configured and restoration must be tested.
7. Deployment and restart procedures must not perform destructive schema recreation; production schema changes must be managed through reviewed Alembic migrations.
8. A module is complete only when its backend behavior, permissions, tests, documentation and required user workflow are verified.
Document status: Updated implementation scope. The backend foundation and initial commercial modules are implemented, but the complete MVP remains in development and is not yet ready for pilot validation.