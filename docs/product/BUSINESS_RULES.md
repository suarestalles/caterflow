CaterFlow — Business Rules
Version: 0.2
Status: Reviewed against current backend implementation
Product: CaterFlow SaaS
Initial Market: Spain
Default Currency: EUR
Last updated: November 20, 2026
Document status and implementation legend
This document defines the business rules for CaterFlow and records their current implementation status. The status labels refer to the backend behavior implemented and validated so far; they do not mean that the complete MVP, frontend, production deployment, or pilot validation is finished.
Status	Meaning
Implemented	The backend rule is implemented and covered by the current automated tests.
Partially implemented	Part of the rule exists, but one or more requirements remain outstanding.
Planned	The rule remains part of the intended product scope but has not yet been implemented.
Open decision	The business behavior still requires a product decision before implementation.


Rules remain normative even when their status is Planned. They must be enforced when the corresponding functionality is implemented.
1. Purpose
This document defines the business rules governing CaterFlow's commercial, operational and financial workflows.

These rules must be enforced by the backend, regardless of the frontend interface or user actions.

The purpose is to maintain data consistency, financial accuracy, operational reliability and historical traceability.
2. General Business Principles
BR-001 — Tenant Data Isolation
Implementation status: Implemented (application-level isolation).

Every company operates within its own tenant context.
- Company-owned records must be associated with a tenant.
- Users may only access data belonging to authorized tenants.
- Cross-tenant access must be rejected.
- Tenant isolation must be enforced by the backend.
- Changing the active tenant must not expose data from another company.
Current implementation: tenant-scoped ORM sessions apply tenant filters and validate writes. Tenant context is resolved through authentication dependencies, and the protected business modules use tenant-scoped database access. Composite foreign keys are used for important tenant-owned relationships, including client/event/quote/catalog relationships where applicable.

PostgreSQL Row-Level Security (RLS) is explicitly deferred. The current isolation strategy is enforced by the application and database constraints; RLS must not be described as implemented.
BR-002 — Historical Data Preservation
Implementation status: Partially implemented.

Historical commercial and financial information must remain consistent.
- Approved quotations must preserve their approved values.
- Payment schedules must preserve the conditions agreed upon.
- Employee assignments must preserve their agreed compensation conditions.
- Changes to default company settings must not modify historical transactions.
- Important modifications must generate audit records.
Current implementation: quote items store their own name, description, unit, quantity, unit price and line total. When a catalog product/service is selected, these values are copied into the quote item as a snapshot. Changing catalog details or prices does not rewrite existing quote items. Quote duplication copies the snapshot and the optional product reference.

Quotation approval/version history, payment schedule snapshots, employee compensation snapshots and general audit records are not implemented yet.
BR-003 — Financial Precision
Implementation status: Partially implemented.

All monetary calculations must use decimal arithmetic.
- Floating-point arithmetic must not be used for financial calculations.
- Monetary amounts must use an explicit currency.
- Rounding rules must be consistent.
- Financial calculations must be performed and validated by the backend.
Current implementation: product prices and quote monetary fields use SQL Numeric columns and Python Decimal. Quote line totals and quote totals are calculated in the backend using decimal arithmetic and explicit cent rounding (ROUND_HALF_UP).

An explicit currency code on product, quote, and financial transaction records, as well as tenant currency configuration and multi-currency behavior, has not been implemented yet.
BR-004 — Company-Specific Configuration
Implementation status: Planned.

Each tenant may configure its own:
- Pricing rules.
- Payment conditions.
- Event settings.
- Employee compensation defaults.
- Language preferences.
- Timezone.
- Currency, subject to supported currencies.
One tenant's configuration must never affect another tenant.

Tenant-specific company settings and configuration APIs are not implemented yet. The default country value ES on events is not a substitute for a complete tenant configuration module.
3. Customer Rules
BR-005 — Customer Registration
Implementation status: Implemented for core client management; partially implemented against the full rule.
- A customer must belong to one tenant.
- A customer must have a minimum set of identifying information.
- Contact information may be updated by authorized users.
- Customers may have multiple contact details.
- Customers may have multiple quotations and events.
Current implementation: the Client model supports individual/business client records, requires at least an email address or phone number, and stores address and notes. Clients are tenant-scoped and can be associated with events and quotes.

A flexible collection of multiple contact persons/details and a complete customer activity/history view are not implemented.
BR-006 — Customer Archiving
Implementation status: Implemented for core behavior.
- Customers with historical transactions must not be permanently deleted through normal application operations.
- Archiving a customer must not delete quotations, events, payments or expenses.
- Archived customers must remain available for historical consultation.
- Archived customers must not be selectable for new commercial operations unless explicitly reactivated.
Current implementation: clients are soft-archived. Archived clients are rejected when creating new events or quotes. Existing records remain stored and related historical data is not deleted by the archive operation. A dedicated reactivation workflow has not been established.
4. Catalog and Menu Rules
BR-007 — Catalog Items
Implementation status: Implemented for the product/service catalog; menu-specific capabilities remain planned.
- Dishes and beverages belong to a tenant.
- Catalog items may be active or inactive.
- Inactive items cannot be selected for new quotations.
- Existing quotations must preserve their historical item descriptions and prices.
- Changes to catalog information must not silently modify existing quotations.
Current implementation: CaterFlow uses one Product model for both physical products and services, differentiated by ProductType (product or service). Catalog records are tenant-scoped and can be active or archived. Archived products/services cannot be added to new quote items. Quote items preserve a snapshot of the catalog values used when the quote was created or updated.

The catalog is generic; dedicated dish, beverage, menu, allergen and nutrition models are not implemented.
BR-008 — Menu Packages
Implementation status: Planned.
- A menu package may contain multiple dishes and beverages.
- Packages may have configurable prices.
- Package prices may depend on company-specific pricing rules.
- A package can be modified or archived without changing historical quotations.
- Recipe information is optional in the MVP.
Menu packages and their composition are not implemented. The current product/service catalog must not be treated as a completed menu-package module.
BR-009 — Ingredient and Inventory Limitations
Implementation status: Scope decision recorded; inventory/recipe functionality not implemented.
- The MVP does not require ingredient-level costing.
- The MVP does not maintain stock quantities.
- Recipe information may be stored for operational reference.
- Actual food and ingredient expenses are recorded as financial expense entries.
Ingredient-level costing, stock control, purchasing and inventory movements remain outside the current implementation. Expense registration is also still pending.
BR-053 — Product and Service Catalog Structure
Implementation status: Implemented.
- A single catalog entity represents both products and services.
- ProductType differentiates product from service.
- A product/service belongs to exactly one tenant.
- A product/service may optionally belong to a category.
- Categories may have a parent category, allowing subcategories.
- A category cannot be archived while it is referenced by products or has child categories.
- A product/service may have an optional SKU; when present, the SKU must be unique within its tenant.
- Sale and cost prices use decimal precision and cannot be negative.
- Units are selected from a standardized enum maintained in application code for the MVP.
- Products/services and categories use logical archiving rather than normal hard deletion.
Current implementation: product and category repositories, services, schemas, API endpoints, permission codes and database migration are implemented and tested. The unit list is currently static in code; a tenant-configurable unit catalog has not been implemented.
5. Pricing Rules
BR-010 — Quotation Pricing
Implementation status: Partially implemented.

A quotation may include:
- Menu packages.
- Individual dishes.
- Beverages.
- Additional services.
- Staffing costs.
- Other configurable commercial items.
The final quotation amount must be calculated from its commercial components and authorized adjustments.

Current implementation: a quote contains one or more quote items. Items may be manually defined or optionally linked to a catalog product/service. The backend calculates line totals, subtotal, discount amount, tax amount and total amount. A discount cannot exceed the subtotal.

Menu package composition, staffing-cost calculation, event-specific pricing rules and configurable pricing engines are not implemented.
BR-011 — Manual Price Adjustments
Implementation status: Partially implemented.
- Authorized users may apply discounts or additional charges.
- Adjustments must be explicitly recorded.
- The system must preserve the original amount and adjusted amount.
- Adjustment reasons should be recorded.
- Permission to apply adjustments may depend on the user's role.
Current implementation: quote creation/update accepts explicit discount and tax amounts, validates nonnegative values and recalculates totals in the backend. Quote create/update permissions are enforced.

Dedicated adjustment reasons, separate permissions or approval thresholds for discounts, and a complete before/after adjustment audit history are not implemented.
BR-012 — Pricing Configuration Changes
Implementation status: Partially implemented.
- Changes to pricing rules apply to future quotations.
- Existing quotations must retain their original calculated values.
- New quotation versions may use updated prices when recalculated.
- Previously approved quotations must not be recalculated automatically.
Current implementation: selecting a catalog product/service copies its current descriptive and pricing values into the quote item. The quote item stores its own price and totals, so subsequent catalog changes do not alter it. A draft quote can be updated, and its items are resolved again when the items are explicitly replaced. Non-draft quotes cannot be updated through the current service.

Quotation versioning and an approval-specific immutable snapshot are not implemented.
6. Quotation Rules
BR-013 — Quotation Creation
Implementation status: Implemented for the current quote workflow; partially implemented against the full rule.
- Every quotation must belong to one tenant.
- Every quotation must reference a customer.
- A quotation must contain the minimum required event and commercial information.
- A quotation must have at least one version.
- Each version must preserve its own commercial snapshot.
Current implementation: every quote is tenant-scoped, requires a client, title and at least one item. An event association is optional; when supplied, it must belong to the selected client and same tenant. Quote numbers are generated sequentially per tenant in the format Q-000001. Quote statuses include draft, sent, accepted, rejected, expired and cancelled.

The current model represents one quote record with editable draft items; it does not yet have a separate quotation-version entity or version history.
BR-014 — Quotation Versions
Implementation status: Planned.
- Every revision must create a new version.
- Previous versions must remain accessible.
- A version must not be silently overwritten.
- Each version must preserve its items, quantities, prices, discounts, totals and relevant commercial conditions.
- The system must identify which version was approved.
- Only an authorized user may create or approve quotation versions.
The current implementation does not create a new version when a draft quote is edited. Draft updates replace the submitted items and recalculate totals. The duplicate operation creates an independent draft quote with a new quote number; it is not quotation versioning.
BR-014A — Draft Editing and Quote Duplication
Implementation status: Implemented.
- Only quotes in draft status may be edited through the current quote service.
- Sending a quote changes its status from draft to sent.
- Sending a quote is only allowed while it is in draft status.
- Duplicating a quote creates a new independent quote in draft status with a new sequential quote number.
- Duplication copies quote items, their commercial snapshots, optional product_id references, units, quantities, prices and line totals.
- Duplicating a quote does not update the original quote.
This behavior is implemented and covered by service/API/repository tests. Customer acceptance/rejection and full version history remain separate pending workflows.
BR-015 — Quotation Approval
Implementation status: Planned.
- Approval must be recorded by an authorized company user in the MVP.
- The approved version must be explicitly identified.
- The approval date and responsible user must be recorded.
- Supporting information may be stored, such as an approval note or external communication reference.
- Approval must preserve the quotation's commercial snapshot.
Customer self-service approval is outside the MVP.

The accepted value exists in the quote status enumeration, but the approval endpoint, approver identity, approval timestamp and approval workflow are not implemented. The existence of the status value alone does not mean approval is available.
BR-016 — Quotation Rejection and Expiration
Implementation status: Planned.
- Rejected quotations must remain available for historical consultation.
- The rejection date must be recorded.
- A rejection reason may be stored.
- Quotation expiration must follow company-defined policies.
- Expired quotations cannot be converted into events without an explicit authorized action.
The rejected, expired and cancelled status values exist in the quote status enumeration, but dedicated rejection/expiration operations, timestamps, reasons and transition rules are not implemented.
BR-017 — Quotation Conversion
Implementation status: Planned.
- Only approved quotations may be converted into events.
- Conversion must preserve the approved commercial information.
- Each approved quotation may generate only one primary event.
- Repeated conversion requests must not create duplicate events.
- The system must preserve the relationship between the event and its originating quotation version.
The current event creation workflow is independent of quote approval/conversion. No quote-to-event conversion operation or idempotency mechanism exists yet.
BR-054 — Catalog-Linked Quote Items and Commercial Snapshots
Implementation status: Implemented.
- A quote item may optionally reference a catalog product/service through product_id.
- A quote item without product_id is a manually defined item and must contain its own name and unit price.
- When product_id is supplied, the product/service must exist in the active tenant and must not be archived.
- A product/service belonging to another tenant must be treated as not found.
- For a catalog-linked item, the backend uses catalog values as defaults for name, description, unit and sale price.
- A caller may provide a negotiated unit price; an explicitly supplied price, including zero, takes precedence over the catalog sale price.
- The quote item stores its own name, description, unit, quantity, unit price and line total.
- Subsequent catalog changes must not silently change existing quote item snapshots.
- Catalog archiving must not prevent consultation or duplication of historical quote items.
- Quote duplication must preserve the optional product reference and all original item snapshots without re-resolving the current catalog values.
Current implementation: the optional product relationship is protected by a composite tenant/product foreign key. Product lookup is tenant-scoped. Missing or cross-tenant products are rejected; archived products are rejected when creating or replacing quote items. Quote-item snapshots and duplication behavior are covered by automated tests.
7. Event Rules
BR-018 — Event Creation
Implementation status: Partially implemented.

An event created from a quotation must preserve:
- Customer information relevant to the transaction.
- Event date and location.
- Number of guests.
- Approved menu and services.
- Approved quotation amount.
- Agreed payment conditions.
- Relevant commercial notes.
Current implementation: events can be created independently and must reference an active client in the same tenant. Event records include name, start/end timestamps, guest count, status, country, address and notes. Date range and positive guest count are validated.

Creation from an approved quote and preservation of an approved commercial/payment snapshot are not implemented.
BR-019 — Event Status
Implementation status: Partially implemented; current backend lifecycle is defined.

The current event statuses are:
Status	Description
draft	Event has been created as a draft
confirmed	Event has been confirmed
in_progress	Event is currently in progress
completed	Event execution has finished
cancelled	Event has been cancelled


The backend validates status transitions:
- draft can transition to confirmed.
- confirmed can transition to in_progress.
- in_progress can transition to completed.
- Cancellation is allowed from draft, confirmed and in_progress.
- completed and cancelled events cannot be cancelled again.
The previously proposed labels scheduled and in_preparation are not current enum values. A calendar workflow and full event history/audit trail remain pending.
BR-020 — Operational and Financial Closure
Implementation status: Planned.

Operational completion and financial closure are independent concepts.
- An event may be operationally completed while payments remain outstanding.
- An event may be financially settled before its operational completion.
- The event's operational status must not automatically imply that all financial obligations are settled.
- The system must display operational and financial information separately.
Payment and expense modules are not implemented yet, so financial closure and its relationship to event status remain pending.
BR-021 — Event Cancellation
Implementation status: Partially implemented.
- Only authorized users may cancel an event.
- A cancellation reason must be recorded.
- Existing payments must be preserved.
- Existing expenses must be preserved.
- Employee assignments must remain available in the event history.
- Refunds and cancellation charges must be represented through explicit financial records.
- Cancellation must not automatically delete or reverse financial transactions.
Current implementation: event cancellation is exposed through a permission-protected endpoint and validated by the event service. It is allowed only from draft, confirmed and in_progress; completed and already cancelled events are rejected. There are no payment, expense or workforce records to preserve yet, and a dedicated cancellation-reason field/workflow is not implemented.
BR-022 — Changes After Approval
Implementation status: Planned.

Changes to event information must be classified according to their impact.

Operational changes, such as replacing an assigned employee, may be managed without modifying the approved quotation.

Changes affecting commercial conditions, such as guest count, menu, services or total price, must follow an explicit change process.

The company must be able to identify:
- The original approved conditions.
- The requested changes.
- The revised conditions.
- The responsible user.
- The date of the change.
Whether a change requires a new quotation revision or an event change order must be defined by the company's workflow.
8. Employee Rules
BR-023 — Employee Types
Implementation status: Planned.

The MVP supports:
- Fixed employees.
- Freelancers.
Both employee types may be assigned to events.

Their contractual and administrative information must be handled according to applicable legal requirements.
BR-024 — Employee Assignment
Implementation status: Planned.
- Employees may be assigned to one or more events.
- Assignments must identify the employee, event and responsibility.
- Planned working hours should be recorded.
- Assignment compensation conditions must be preserved when applicable.
- Employee availability and scheduling conflicts should be considered.
BR-025 — Compensation
Implementation status: Planned.

The system may support:
- Hourly compensation.
- Fixed compensation per event.
- Other explicitly configured compensation arrangements.
The applicable compensation method must be identified for each assignment.

The agreed compensation values must be preserved as historical snapshots.
BR-026 — Working Hours
Implementation status: Planned.
- Planned and actual working hours must be distinguishable.
- Actual hours may be entered by authorized users.
- Corrections must generate audit records.
- Calculated staff costs must use the applicable assignment compensation conditions.
- Missing working-hour information must not be silently interpreted as zero.
BR-027 — Employee Replacement
Implementation status: Planned.
- Replacing an employee must preserve the original assignment history.
- The replacement must create or update the appropriate assignment record.
- Compensation conditions must be recorded independently for the replacement.
- Historical costs must remain traceable.
9. Payment Rules
BR-028 — Payment Configuration
Implementation status: Planned.

Each tenant may configure its payment conditions.

A payment schedule may define:
- Number of installments.
- Percentage or fixed amount per installment.
- Due dates or due-date calculation rules.
- Relevant payment descriptions.
BR-029 — Payment Schedule Validation
Implementation status: Planned.

For percentage-based installment schedules:
- The sum of installment percentages must equal 100%.
- Generated installment amounts must reconcile with the approved quotation total.
- Rounding differences must be handled explicitly.
- The final installment may absorb a documented rounding adjustment.
For fixed-amount schedules:
- The total scheduled amount must reconcile with the approved quotation total.
- Any remaining balance must be represented explicitly.
BR-030 — Payment Schedule Snapshot
Implementation status: Planned.
- Payment schedules must be generated using the configuration applicable at the time of approval.
- Changes to default payment settings must not alter existing schedules.
- Changes to an approved commercial total must follow an explicit change process.
- Previous payment conditions must remain available for historical consultation.
BR-031 — Payment Registration
Implementation status: Planned.
- Payments must be associated with an event and, where applicable, an installment.
- Each payment must record its amount, date and method.
- Payment records must identify the responsible user.
- Partial payments must be supported.
- The system must calculate outstanding balances.
BR-032 — Payment Validation
Implementation status: Planned.
- Payment amounts must be greater than zero.
- A payment must not exceed the outstanding balance of the relevant obligation unless an explicit overpayment workflow is supported.
- Invalid payment operations must be rejected.
- Payment corrections must preserve the original record through controlled reversal or correction operations.
BR-033 — Payment Status
Implementation status: Planned.

Initial installment statuses:
Status	Description
Pending	No payment has been recorded
Partially Paid	Some amount has been received
Paid	The full installment amount has been received
Overdue	The due date has passed and an outstanding balance remains
Cancelled	The installment has been cancelled through an authorized operation


Overdue status must be based on the due date and remaining balance.
BR-034 — Refunds and Reversals
Implementation status: Planned.
- Refunds must be explicitly recorded.
- A refund must reference the original payment when applicable.
- Reversed or corrected payments must remain traceable.
- Refunds must update the financial balance consistently.
- The system must not silently delete financial transactions.
Integrated payment processing is outside the MVP.
10. Expense Rules
BR-035 — Expense Registration
Implementation status: Planned.

An expense must contain:
- Tenant.
- Associated event.
- Category.
- Description.
- Amount.
- Currency.
- Expense date.
- Responsible user.
Optional receipt attachments may be supported.
BR-036 — Expense Categories
Implementation status: Planned.

Initial categories:
- Food and ingredients.
- Beverages.
- Staff.
- Transportation.
- Other expenses.
Categories may be configurable by tenant in a future enhancement.
BR-037 — Expense Validation
Implementation status: Planned.
- Expense amounts must be greater than zero.
- Expenses must be associated with an authorized tenant.
- Expenses must be associated with an event.
- Corrections must preserve the previous information in the audit history.
- Expense records must not be silently deleted after financial reporting or event closure.
BR-038 — Expense Calculation
Implementation status: Planned.

Actual event expenses must be calculated from recorded expense entries.

The system must not require individual ingredient costs.

Staff costs may be calculated from recorded employee assignments and applicable compensation conditions, but the system must avoid counting the same staff cost twice when a corresponding expense entry has already been recorded.

The final accounting treatment of manually entered staff expenses and calculated staff costs must be clearly defined before financial reporting is implemented.
11. Financial Reporting Rules
BR-039 — Financial Indicators
Implementation status: Planned.

The event financial summary must distinguish:
- Approved quotation amount.
- Payments received.
- Outstanding payment balance.
- Recorded actual expenses.
- Estimated expenses, if available.
- Actual financial result, based on recorded data.
BR-040 — Revenue and Cash Flow
Implementation status: Planned.

The system must distinguish commercial revenue from cash received.
- Approved quotation values represent agreed commercial amounts.
- Recorded payments represent received amounts.
- Outstanding balances represent amounts not yet received.
- Cancelled quotations and events must not be treated as automatically collected revenue.
BR-041 — Event Financial Result
Implementation status: Planned.

When all required data is available, the system may calculate:

Estimated result:

Approved quotation amount minus estimated costs.

Actual result:

Recognized event revenue minus recorded actual expenses.

The dashboard must clearly identify which values are estimated and which are based on actual records.

The result shown by CaterFlow is an operational management indicator and must not be presented as a legally certified accounting or tax result.
12. Internationalization and Localization Rules
BR-042 — Supported Languages
Implementation status: Planned.

The MVP supports:
- Portuguese.
- Spanish.
- English.
The backend currently does not provide a completed localization system or language-selection workflow.
BR-043 — Locale Formatting
Implementation status: Planned.
- Dates must follow the selected locale.
- Numbers must follow the selected locale.
- Monetary values must display the appropriate currency.
- Generated documents must use the selected language.
- Internal timestamps must be stored consistently and displayed according to the applicable timezone.
BR-044 — Timezone
Implementation status: Partially implemented.

The initial default timezone for Spanish companies is Europe/Madrid.

Each tenant must have an explicit timezone configuration.

Event dates and schedules must be interpreted in the company's configured timezone.

Current implementation: event start/end fields are timezone-aware. A tenant-level timezone setting and locale-aware event presentation have not been implemented.
BR-045 — Currency
Implementation status: Partially implemented.

EUR is the initial default currency.

Monetary transactions must store an explicit currency code.

Changing a tenant's default currency must not silently convert historical financial records.

Multi-currency financial consolidation is outside the initial MVP unless explicitly added to scope.

Current implementation: monetary values use decimal precision, but currency codes and tenant currency configuration are not yet represented in the current product/quote models.
13. Audit and Data Integrity Rules
BR-046 — Audit Records
Implementation status: Planned.

Important operations must generate audit records containing, where applicable:
- Tenant.
- User.
- Action.
- Entity type.
- Entity identifier.
- Timestamp.
- Relevant change information.
BR-047 — Historical Traceability
Implementation status: Partially implemented.

The system must preserve the history of:
- Quotation versions.
- Quotation approvals.
- Event status transitions.
- Employee assignments.
- Payment records.
- Expense records.
- Relevant administrative changes.
Current implementation: quote-item commercial snapshots and quote duplication preserve item data. Client, event, product and category archiving avoids normal hard deletion of those records. A general audit log, quote version history, approval history and workforce/payment/expense histories are not implemented.
BR-048 — Controlled Corrections
Implementation status: Partially implemented.

Historical business records must be corrected through explicit operations.

Corrections must not silently overwrite important financial or commercial history.

Current implementation: sent/non-draft quotes cannot be updated through the current quote service, and catalog changes do not rewrite quote snapshots. General correction workflows for approved quotes, events, payments and expenses remain pending.
BR-049 — Data Retention
Implementation status: Planned.

Retention and deletion policies must consider applicable legal, tax, contractual and data protection requirements.

Personal data must not be retained indefinitely without a valid basis.

Audit and financial records must follow an appropriate retention policy rather than being deleted simply to reduce storage costs.

Retention schedules, user-facing deletion workflows and formal data lifecycle procedures have not been implemented.
14. Authorization Rules
BR-050 — Permission Validation
Implementation status: Implemented for current protected backend operations.
- Every protected operation must validate the authenticated user.
- Every protected operation must validate the active tenant context.
- Every protected operation must validate the user's permissions.
- Frontend restrictions alone are insufficient.
- Unauthorized requests must be rejected by the backend.
Current implementation: authentication dependencies resolve the user and tenant context. Protected API endpoints use backend permission dependencies based on permission codes. Users may have multiple roles and effective permissions are derived from those roles. Authorization is based on permission codes, not role names. The permission catalog and default role grants are maintained in the backend.

This status applies to the operations implemented so far; future modules must define and enforce their own permission requirements.
BR-051 — Sensitive Financial Operations
Implementation status: Planned.

Access to payment corrections, refunds, financial reports and expense modifications must be controlled by explicit permissions.

The payment, expense and financial-reporting operations do not exist yet, so their detailed permission codes and role grants remain to be defined when those modules are implemented.
BR-052 — Employee Information
Implementation status: Planned.

Employees must only access information required for their assigned responsibilities.

Personal, compensation and administrative information must be restricted to authorized users.

Employee self-service and workforce access rules are not implemented.
15. Open Business Decisions
The following decisions require validation before the corresponding functionality is implemented:
1. Should payment schedules be generated at quotation approval or only when the quotation is converted into an event?
2. Should the company be allowed to modify payment schedules after approval, provided the change is recorded and agreed upon?
3. Should staff compensation be included automatically in the financial result or only through recorded expenses?
4. Should employees confirm their event assignments?
5. Which event changes require a new quotation version?
6. Should a closed event be reopened through an authorized workflow?
7. Should payment overpayments be supported?
8. Should expense categories be configurable by each tenant in the MVP?
9. Which user roles may approve refunds and financial corrections?
10. Which retention periods and deletion procedures are required under applicable Spanish and EU regulations?
Decisions already established during implementation
The following design decisions have been made and should be treated as current implementation constraints unless explicitly revisited:
- Products and services share one Product model and are differentiated by ProductType.
- Product units are maintained as a static standardized enum in application code for the MVP; a database-backed or tenant-configurable unit catalog is deferred.
- Product categories support parent/child hierarchy.
- Product category and product records are tenant-scoped and use logical archiving.
- A quote item may be manually defined or linked optionally to a catalog product/service.
- Catalog-linked quote items store commercial snapshots. Catalog price/name/description/unit changes do not rewrite existing quote items.
- A negotiated quote-item price takes precedence over the catalog sale price for that quote item and does not modify the catalog.
- Archived products/services cannot be selected when creating or replacing quote items, but historical quote items remain viewable and can be duplicated with their snapshots.
- Quote item catalog relationships use tenant-aware referential integrity.
- PostgreSQL RLS is deferred; current tenant isolation is implemented at the application layer and reinforced by database constraints.
Document status: Reviewed against the current backend implementation as of November 20, 2026. This document is a living record of intended business rules and implementation progress. Planned rules remain requirements for their respective future modules; they must not be interpreted as completed functionality. The MVP is not yet ready for pilot validation because workforce, payments, expenses, approval/conversion, reporting, localization, audit and production-readiness capabilities remain outstanding.