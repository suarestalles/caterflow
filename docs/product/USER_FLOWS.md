CaterFlow — User Flows
Version: 0.2
Status: Updated against current backend implementation
Product: CaterFlow SaaS
Initial market: Spain
Last updated: November 20, 2026
1. Purpose
This document describes the main user journeys and operational workflows planned for CaterFlow and records their current implementation status.

It establishes how users interact with the platform, how business processes progress, and how information moves between the commercial, operational and financial areas.

These flows guide interface design, backend implementation and database modeling.
1.1 Implementation status convention
The status shown in this document describes the current implementation, not only the intended product behavior:
- Implemented — Backend: the corresponding backend models, business rules and API capabilities are implemented and covered by automated tests. This does not imply that a frontend screen is available.
- Partially implemented — Backend: some of the workflow is implemented, but one or more important steps or business transitions remain unavailable.
- Planned: the workflow is part of the product direction but has not yet been implemented.
- Decision pending: the workflow requires a business decision before implementation.
The current development has prioritized the backend. Unless explicitly stated otherwise, this document does not claim that the frontend user interface, production deployment or end-to-end browser experience is complete.
2. User Profiles
The following profiles describe the intended users of CaterFlow. Their presence in this document does not mean that every profile-specific interface or workflow has already been implemented.
2.1 Platform Administrator
Responsible for the SaaS platform itself.

Main activities:
- Manage tenant accounts.
- Monitor platform operation.
- Manage subscription-related settings when implemented.
- Provide platform-level support.
Platform administrators must not automatically have unrestricted access to tenant business information.

Implementation status: platform-level authentication foundations exist. A complete platform administration and support workflow remains planned.
2.2 Company Owner
Responsible for the catering company's overall operation.

Main activities:
- Configure company information.
- Manage users and permissions.
- Manage customers, quotations, catalog items and events.
- Monitor payments and expenses.
- Access financial reports.
Implementation status: tenant membership and permission foundations exist. Backend capabilities for customers, catalog items, quotations and events are available. Company profile configuration, payments, expenses and financial reports remain pending.
2.3 Company Administrator
Responsible for company configuration and administrative operations.

Main activities:
- Manage users.
- Configure company settings.
- Manage catalogs and pricing.
- Access authorized business information.
Implementation status: role and permission management foundations exist. Complete company settings and the full administrative user experience remain pending.
2.4 Manager
Responsible for commercial and operational coordination.

Main activities:
- Register customers.
- Create and manage quotations.
- Coordinate event preparation.
- Assign employees.
- Track payments and expenses.
Implementation status: customer, quotation and basic event backend workflows are available subject to permissions. Employee assignments, payments and expenses remain planned.
2.5 Chef
Responsible for food preparation and kitchen coordination.

Main activities:
- View assigned events.
- Access menus and relevant technical information.
- Review guest counts and operational requirements.
- Coordinate kitchen activities.
Implementation status: planned. Dedicated employee access, assignments and kitchen workflows have not yet been implemented.
2.6 Fixed Employee
Responsible for performing assigned event activities.

Main activities:
- View assigned events.
- Consult schedules and responsibilities.
- Access relevant operational information.
- Record working hours when authorized.
Implementation status: planned. Employee registration, employee-specific access and assignment workflows have not yet been implemented.
2.7 Freelancer
Responsible for temporary event assignments.

Main activities:
- View accepted or assigned event information.
- Consult schedules and responsibilities.
- Access relevant operational information.
- Record working hours when authorized.
Employee access must be restricted to information required for their responsibilities.

Implementation status: planned. Freelancer registration, access and assignment workflows have not yet been implemented.
2.8 Roles and permissions
The backend uses permission codes to authorize operations. Authorization must not depend on a role's display name. A user may have multiple roles within a tenant, and the effective permissions are derived from those assignments.

The current permission system includes tenant-scoped roles, memberships and role-permission assignments. The Owner default role receives the available permissions; other default role grants are limited according to the permission catalog.

The intended personas above must be mapped to permissions as the product's user and workforce workflows are implemented. Chef, fixed employee and freelancer access policies remain to be defined.
3. Main Event Lifecycle
The intended end-to-end CaterFlow workflow is:
1. Customer registration.
2. Event request registration.
3. Quotation creation.
4. Quotation review and revision.
5. Customer approval.
6. Event creation from the approved quotation.
7. Operational planning.
8. Event execution.
9. Expense and payment tracking.
10. Event closure and financial review.
Implementation status: Partially implemented — Backend.

The customer, catalog, quotation and basic event modules are implemented. However, the complete lifecycle is not yet available:
- Quotations can be created, listed, retrieved, updated while in draft, sent and duplicated.
- The quotation status model contains additional statuses, but a complete customer approval/rejection and versioning workflow is not implemented.
- Events can be created and managed independently, but conversion from an approved quotation into an event is not implemented.
- Employee planning, payments, expenses, dashboards and event financial closure remain planned.
The implemented event status transitions are described in Section 7.3. The workflow must not be presented as an end-to-end operational process until the missing dependencies are delivered.
4. Customer Management Flow
4.1 Register a Customer
Actor: Owner, Administrator or Manager, subject to assigned permissions.
Implementation status: Implemented — Backend.

Steps:
1. Open the Customers section (frontend workflow planned).
2. Select the option to create a customer.
3. Enter the customer type and identifying information.
4. Provide at least an email address or phone number.
5. Save the registration.
6. Retrieve the customer profile.
Expected backend result:
- The customer is registered within the active tenant.
- The customer can be associated with quotations and events.
- Customer records can be listed, searched, retrieved and updated through the API.
- Customer records support individual and company customer types.
4.2 Update Customer Information
Implementation status: Implemented — Backend.

Steps:
1. Search for the customer within the active tenant.
2. Retrieve the customer profile.
3. Submit the permitted changes.
4. Save the changes.
Customer updates must not delete or cascade-delete related quotations or events. The current quotation and event models retain their customer references; a full immutable snapshot of every customer profile field is not currently implemented.
4.3 Archive a Customer
Implementation status: Implemented — Backend.

Steps:
1. Retrieve the customer.
2. Request the archive operation.
3. The backend marks the customer as archived.
Expected result:
- The customer is not physically deleted.
- Existing quotations and events remain available.
- Archived customers cannot be selected for new operations that require an active customer.
5. Catalog Management Flow
5.1 Manage Product Categories
Actor: Owner, Administrator or another user with the relevant category permissions.
Implementation status: Implemented — Backend.

Steps:
1. Create a category with a name and optional description.
2. Optionally select a parent category to create a subcategory.
3. List, search and retrieve categories.
4. Update category information or hierarchy when allowed.
5. Archive a category when it is no longer needed.
Rules:
- Categories belong to a tenant.
- Category names are unique within the tenant.
- A category cannot be its own parent or create a hierarchy cycle.
- A category must be active when selected for a new or updated product.
- A category that still has products or child categories cannot be archived.
5.2 Register a Product or Service
Actor: Owner, Administrator or another user with the relevant product permissions.
Implementation status: Implemented — Backend.

CaterFlow uses one Product model for both physical products and services. The type field distinguishes product from service.

Steps:
1. Open the catalog management area (frontend workflow planned).
2. Create a product or service.
3. Enter its name and optional description.
4. Select its type and unit.
5. Optionally associate an active category.
6. Optionally provide a tenant-unique SKU.
7. Set sale and cost prices.
8. Save the record.
Expected backend result:
- The record belongs to the active tenant.
- Monetary values use decimal precision and cannot be negative.
- SKU uniqueness is enforced within the tenant when a SKU is provided.
- Products and services can be listed, searched, filtered, retrieved and updated.
5.3 Archive a Product or Service
Implementation status: Implemented — Backend.

Steps:
1. Retrieve the catalog item.
2. Request the archive operation.
3. The backend sets the item as inactive.
Archived products and services cannot be added to new quotation items. Existing quotation items retain their snapshots and references. Catalog archiving does not rewrite historical quotation data.
5.4 Menus, Recipes and Inventory
Implementation status: Planned.

Menu packages, menu composition, recipe information, ingredient-level costing and inventory movements have not been implemented. The current catalog supports individual products and services with categories and units; it must not be described as a complete menu or inventory system.
6. Quotation Management Flow
6.1 Create a Quotation
Actor: Owner, Administrator or Manager, subject to quotes.create.
Implementation status: Implemented — Backend.

Steps:
1. Start a quotation.
2. Select an active registered customer.
3. Optionally associate an event belonging to that customer.
4. Enter the quotation title and optional description, validity date, notes and terms.
5. Add at least one item.
6. For each item, either select a catalog product/service or provide a custom item.
7. Enter the quantity and position.
8. Review the calculated subtotal, discount, tax and total.
9. Save the quotation.
Catalog item behavior:
- A catalog item is selected using product_id.
- The backend verifies that the item exists within the current tenant and is active.
- The item's name, description, unit and sale price are used to populate the quotation item when values are not explicitly supplied.
- A user may provide a negotiated unit price.
- A custom item does not require a catalog reference; its name and unit price are required.
Expected backend result:
- The quotation belongs to the active tenant and references an active customer.
- A tenant-scoped sequential quotation number is generated (for example, Q-000001).
- The initial status is draft.
- The quotation has at least one item.
- The backend calculates item totals and quotation totals using decimal arithmetic.
- A discount greater than the subtotal is rejected.
6.2 Quotation Item Snapshot
Implementation status: Implemented — Backend.

Each quotation item stores its own commercial information, including name, description, unit, quantity, unit price and total price. product_id is optional and records the catalog reference when one was used.

Changes to a product or service after quotation creation must not silently change the existing quotation item's stored name, description, unit or price. The catalog relationship is a reference, not the source from which historical quotation values are recalculated on every read.

A catalog item's negotiated price is stored on the quotation item and does not change the catalog's sale price.
6.3 Update a Quotation
Implementation status: Implemented — Backend, with limitations.

Steps:
1. Retrieve the quotation.
2. Confirm that its status is draft.
3. Submit permitted changes to quotation fields.
4. If the items are provided, replace the quotation's current item collection with the submitted items.
5. Recalculate totals.
6. Save the changes.
Rules and limitations:
- Only draft quotations can be updated.
- Item replacement can use catalog-linked or custom items.
- Catalog products/services must be active and belong to the current tenant.
- The backend recalculates subtotal, discount, tax and total.
- This operation updates the draft; it does not create an immutable quotation version.
- Historical versioning and revision comparison remain planned.
6.4 Send a Quotation
Implementation status: Implemented — Backend.

Steps:
1. Retrieve a draft quotation.
2. Request the send operation.
3. The backend changes its status to sent.
The current operation records the status transition. Email delivery, PDF generation, external sharing and customer-side confirmation are not part of the implemented flow.
6.5 Record Customer Approval or Rejection
Implementation status: Planned.

The quotation status model includes values such as accepted, rejected, expired and cancelled, but a complete approval/rejection workflow is not implemented.

The planned manual workflow remains:
1. Open the quotation.
2. Identify the exact quotation version approved or rejected.
3. Record the decision, date and responsible company user.
4. Preserve supporting information and the approved commercial terms.
Customer self-service approval remains outside the initial MVP unless the scope is changed.
6.6 Quotation Versions and Revisions
Implementation status: Planned.

The current update operation edits a draft quotation; it does not create a new immutable version. The duplicate operation creates an independent draft copy, not a version in a linked revision history.

A future versioning workflow must preserve previous versions, identify the approved version and prevent approved commercial information from being silently overwritten.
6.7 Duplicate a Quotation
Implementation status: Implemented — Backend.

Steps:
1. Retrieve the original quotation.
2. Request duplication.
3. The backend creates a new quotation with a new ID and quotation number.
4. The duplicated quotation starts in draft status.
5. The quotation items are copied as independent records.
The duplicate preserves item catalog references when present and copies the stored snapshots, quantities, negotiated prices, totals and positions. It does not re-read the current catalog to recalculate historical item values. Therefore, a quotation can be duplicated even if a referenced catalog item has since been archived.
6.8 Generate a Quotation PDF
Implementation status: Planned.

The future workflow is:
1. Open the quotation.
2. Select the document language.
3. Preview the proposal.
4. Generate the PDF.
5. Store or retrieve the document securely.
6. Make it available for external sharing.
PDF generation, company branding, document storage and delivery are not currently implemented.
7. Event Management Flow
7.1 Create an Event
Actor: Owner, Administrator or Manager, subject to event permissions.
Implementation status: Implemented — Backend, independently of quotation conversion.

Steps:
1. Start event creation.
2. Select an active customer belonging to the current tenant.
3. Enter the event name.
4. Enter start and end date/time.
5. Enter a positive guest count.
6. Enter event address and operational notes where applicable.
7. Save the event.
Expected backend result:
- The event belongs to the active tenant.
- The customer reference is valid and tenant-scoped.
- The end time must be later than the start time.
- The initial status is draft unless another allowed status is explicitly provided by the implemented operation.
- The event stores a country code, with ES as the model default.
The current event model does not represent a completed operational conversion from an approved quotation. An event may be associated with a customer and can optionally be linked to a quotation in future workflow development, but the approved-quotation conversion process is not implemented.
7.2 Retrieve, List and Update an Event
Implementation status: Implemented — Backend.

Users with the appropriate permissions can list and retrieve tenant-scoped events and update permitted event information. Cross-tenant records are not exposed.
7.3 Monitor Event Status
Implementation status: Implemented — Backend, with a limited status workflow.

The implemented statuses are:
Status	Description
draft	Event is in draft state
confirmed	Event has been confirmed
in_progress	Event execution is underway
completed	Event execution has finished
cancelled	Event has been cancelled


The backend validates status changes. The implemented progression is draft → confirmed → in_progress → completed. Cancellation is allowed from draft, confirmed or in_progress. Completed and already cancelled events cannot be cancelled again.

The broader operational planning stages such as staffing, preparation checklists and kitchen coordination remain planned.
7.4 Convert an Approved Quotation into an Event
Implementation status: Planned.

The intended workflow is:
1. Open an approved quotation.
2. Select Convert to Event.
3. Review event details and approved commercial information.
4. Confirm event creation.
5. Open the resulting event.
The conversion must be idempotent and preserve the approved commercial snapshot. This workflow cannot be completed today because quotation approval/versioning and the conversion operation have not yet been implemented.
7.5 Plan an Event
Implementation status: Planned.

The future workflow includes reviewing event date, location and guest count; reviewing approved menus and services; defining operational requirements; assigning employees; and recording responsibilities and schedules.

Employee assignment, staffing overview, planned/actual hours and kitchen planning are not currently implemented.
7.6 Cancel an Event
Implementation status: Implemented — Backend, with limited cancellation information.

Steps:
1. Retrieve an eligible event.
2. Request cancellation.
3. The backend validates that the current status permits cancellation.
4. The event status changes to cancelled.
The event is not physically deleted. A complete cancellation-reason workflow and financial consequences such as refunds or cancellation charges remain planned.
7.7 Operational and Financial Closure
Implementation status: Planned.

Operational completion and financial settlement must remain independent concepts. The current event workflow supports the completed status, but it does not implement a separate financial closure, reconciliation or reopening workflow.
8. Employee Management Flow
8.1 Register an Employee
Implementation status: Planned.

The intended workflow is:
1. Open the Employees section.
2. Select fixed employee or freelancer.
3. Enter personal and contact information.
4. Configure relevant compensation information.
5. Save the employee record.
Employee records, employee-specific authentication and workforce administration have not yet been implemented.
8.2 Assign an Employee to an Event
Implementation status: Planned.

The future workflow includes selecting an employee, defining responsibility and planned schedule, recording agreed compensation conditions and confirming the assignment.
8.3 Replace an Assigned Employee
Implementation status: Planned.

The future workflow must preserve the original assignment history, record the replacement and retain separate compensation conditions for the replacement assignment.
8.4 Record Working Hours
Implementation status: Planned.

Planned and actual hours must be distinguishable. Corrections must be authorized and auditable. Missing hour records must not be silently treated as zero.
9. Payment Management Flow
9.1 Generate Payment Installments
Implementation status: Planned.

The intended workflow is:
1. Retrieve the payment configuration applicable to the approved commercial agreement.
2. Generate installment amounts and due dates.
3. Reconcile installments with the approved quotation amount.
4. Associate the schedule with the event or relevant obligation.
Payment schedules and installment persistence have not yet been implemented. The trigger for generation (quotation approval or event conversion) remains a business decision.
9.2 Record a Payment
Implementation status: Planned.

Payment registration, partial payments, payment methods, installment balances and outstanding balances have not yet been implemented.
9.3 Handle Overdue Payments
Implementation status: Planned.

Overdue identification and follow-up workflows depend on payment installment functionality and are not currently available.
10. Event Expense Management Flow
10.1 Record an Expense
Implementation status: Planned.

The intended workflow is:
1. Open an event.
2. Access its Expenses section.
3. Select an expense category.
4. Enter description, amount and date.
5. Optionally attach a receipt.
6. Save the expense.
Expense records, categories, receipt attachments and expense permissions have not yet been implemented.
10.2 Review Event Financial Results
Implementation status: Planned.

A financial summary must distinguish approved quotation value, payments received, outstanding balances, actual expenses and estimated/actual results. These calculations depend on payment and expense modules that remain pending.
11. Event Closure Flow
Implementation status: Planned, except for the event completed status.

The intended workflow is:
1. Confirm that event execution has finished.
2. Review employee hours.
3. Review recorded expenses.
4. Review payments and outstanding balances.
5. Review the financial summary.
6. Perform operational closure and, separately, financial reconciliation where applicable.
The current backend can mark an eligible event as completed, but it does not perform the complete closure process described above. Corrections after closure, reopening and financial settlement workflows remain pending.
12. Dashboard Flow
Implementation status: Planned.

The intended flow is:
1. User authenticates.
2. User enters an authorized company context.
3. The dashboard loads information available to that user.
4. The user reviews relevant indicators.
5. The user navigates to events, quotations, payments or expenses.
Dashboard APIs, aggregated indicators and dashboard interface have not yet been implemented. Any future dashboard must respect tenant isolation and backend permissions.
13. Tenant and Company Context
Implementation status: Partially implemented — Backend.

The current backend provides:
- Users and tenant memberships.
- Tenant-scoped roles and permission assignments.
- Authentication context resolution.
- Tenant-scoped database sessions and ORM filtering.
- Backend permission checks.
- Tenant-isolation validation, including cross-tenant access tests.
The intended flow is:
1. User authenticates.
2. The backend identifies the user's authorized tenant membership/context.
3. Requests execute within that tenant context.
4. Each protected operation validates the active tenant and the required permission.
5. A user with multiple memberships must use an authorized tenant context for each operation.
The membership model supports a user having memberships in multiple tenants. A complete frontend tenant-selection and tenant-switching experience remains to be validated/implemented.

Tenant isolation currently relies on application/backend enforcement. PostgreSQL Row-Level Security (RLS) has explicitly been deferred and is not part of the current implementation.

Company profile configuration, branding, default currency/language/timezone settings and a complete company onboarding interface remain planned.
14. Authentication and Authorization Flow
Implementation status: Implemented — Backend foundations.

The current backend includes credential/security foundations, access-token validation, refresh-token persistence/lifecycle components, user identities, tenant memberships and permission-based authorization.

The intended protected-request flow is:
1. User authenticates and obtains an access token.
2. The client includes the token in a protected request.
3. The backend validates the token and resolves the authenticated user and tenant context.
4. The backend checks the required permission.
5. The request executes using a tenant-scoped database session.
6. Unauthorized or invalid requests are rejected.
Current API behavior includes authentication rejection for unauthenticated requests, permission rejection for users lacking the required permission, and tenant-scoped resource lookup. The exact user-facing login, refresh, logout and tenant-switch screens remain frontend work.

Authorization is based on permission codes, not role names. The backend remains the source of truth; frontend visibility restrictions alone are insufficient.
15. Internationalization Flow
Implementation status: Planned.

The intended flow is:
1. User selects a preferred language.
2. The interface displays translated content.
3. Dates and numeric values follow the selected locale.
4. Generated documents use the selected document language.
5. Company-specific defaults are applied where appropriate.
Initial supported product languages are Portuguese, Spanish and English. A complete translation system, language selection experience, locale-aware frontend formatting and multilingual PDF generation have not yet been implemented. The event model's default country code ES does not, by itself, mean that localization is complete.
16. Error and Exception Scenarios
The backend must handle at least the following cases. The listed HTTP statuses describe the current API behavior where the relevant operation is implemented; planned workflows will require their own error contracts.
Scenario	Current behavior/status
Unauthenticated request to protected endpoint	401 Unauthorized
Authenticated user without required permission	403 Forbidden
Attempt to access a resource belonging to another tenant	Resource is not exposed; typically 404 Not Found
Invalid request payload or business validation	422 Unprocessable Content
Unknown customer in quotation operation	404 Not Found
Unknown or cross-tenant product in quotation item	404 Not Found
Archived product used for a new quotation item	422 Unprocessable Content
Attempt to update a non-draft quotation	422 Unprocessable Content
Attempt to cancel an event in a terminal/ineligible status	422 Unprocessable Content


Additional planned scenarios include:
- Attempt to approve a quotation without a valid version.
- Attempt to create an event from an unapproved quotation.
- Duplicate event conversion requests.
- Invalid payment amounts or payments exceeding an outstanding balance.
- Event cancellation with existing payments.
- Employee assignment conflicts.
- Invalid or incomplete expense records.
- Unauthorized modifications to closed events.
Errors must be communicated clearly without exposing sensitive technical information.
17. Open Questions and Decisions
The following items remain open or require product validation before their related workflows are implemented:
1. Tenant membership: the data model supports one user belonging to multiple tenants. The complete tenant-selection and switching experience must still be defined and delivered.
2. Employee accounts: should employees have individual login accounts in the MVP, or should some companies manage them only through administrative accounts?
3. Assignment acceptance: can employees confirm or accept event assignments?
4. Working-hour approval: should recorded employee working hours require manager approval?
5. Event reopening: can a completed or closed event be reopened, and which permission is required?
6. Commercial changes: which event changes require a new quotation revision or a separate change order?
7. Customer contacts: should a customer support multiple contacts, or is one primary email and phone sufficient for the initial release?
8. Customer identity: the current customer model supports individual/company customer types. Further billing and contact requirements must be validated.
9. Employee visibility: which information must be visible to chefs, fixed employees and temporary staff?
10. Financial closure: operational completion and financial settlement are independent. The detailed financial closure criteria remain to be defined.
11. Quotation approval: what evidence, approval date and authorized user information must be stored?
12. Quotation versioning: should every revision create a new immutable version, and how should an approved version be locked?
13. Payment schedule trigger: should installments be generated at quotation approval or only when the quotation is converted into an event?
14. Audit history: which operations require audit events and what retention policy applies?
18. Current Workflow Readiness Summary
Workflow	Backend status	Main remaining work
Authentication and authorization	Implemented foundations	Complete frontend experience and release validation
Tenant context and isolation	Partially implemented	Company onboarding and complete tenant switching experience
Customer management	Implemented	Frontend experience and later enhancements as required
Product/service catalog and categories	Implemented	Frontend experience; menus and recipes remain separate work
Quotation creation and draft update	Implemented	Versioning and full approval workflow
Catalog-linked quotation items	Implemented	Continue integration validation as the product evolves
Quotation sending	Implemented status operation	Actual document generation and delivery
Quotation approval/rejection	Planned	Business workflow and audit trail
Quotation PDF	Planned	PDF generation, branding and storage
Basic event management	Implemented	Conversion from approved quotation and operational planning
Employee/workforce management	Planned	Employee records, assignments and working hours
Payments and installments	Planned	Payment schedules, registration and reconciliation
Expenses	Planned	Expense records, categories and receipts
Financial dashboards and reporting	Planned	Aggregations and reporting APIs/UI
Localization	Planned	Translation and locale-aware experience
Audit history	Planned	Audit model, capture and review workflows


19. Final Principles
CaterFlow user flows must remain consistent with the backend business rules and permission model.

A flow must not be considered implemented merely because it appears in this document or because a data model contains a related status or field. Completion requires the relevant backend behavior, authorization, tenant isolation, tests and any required interface to be validated.

The platform must preserve tenant isolation, financial accuracy and historical commercial information throughout the customer, catalog, quotation and event lifecycle.

Document status: Updated to reflect the backend implementation as of November 20, 2026. Planned flows remain product requirements and must be implemented and validated before being described as available functionality.