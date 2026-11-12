# CaterFlow — Business Rules

**Version:** 0.1  
**Status:** Initial Draft  
**Product:** CaterFlow SaaS  
**Initial Market:** Spain  
**Default Currency:** EUR

## 1. Purpose

This document defines the business rules governing CaterFlow's commercial, operational and financial workflows.

These rules must be enforced by the backend, regardless of the frontend interface or user actions.

The purpose is to maintain data consistency, financial accuracy, operational reliability and historical traceability.

## 2. General Business Principles

### BR-001 — Tenant Data Isolation

Every company operates within its own tenant context.

- Company-owned records must be associated with a tenant.
- Users may only access data belonging to authorized tenants.
- Cross-tenant access must be rejected.
- Tenant isolation must be enforced by the backend.
- Changing the active tenant must not expose data from another company.

### BR-002 — Historical Data Preservation

Historical commercial and financial information must remain consistent.

- Approved quotations must preserve their approved values.
- Payment schedules must preserve the conditions agreed upon.
- Employee assignments must preserve their agreed compensation conditions.
- Changes to default company settings must not modify historical transactions.
- Important modifications must generate audit records.

### BR-003 — Financial Precision

All monetary calculations must use decimal arithmetic.

- Floating-point arithmetic must not be used for financial calculations.
- Monetary amounts must use an explicit currency.
- Rounding rules must be consistent.
- Financial calculations must be performed and validated by the backend.

### BR-004 — Company-Specific Configuration

Each tenant may configure its own:

- Pricing rules.
- Payment conditions.
- Event settings.
- Employee compensation defaults.
- Language preferences.
- Timezone.
- Currency, subject to supported currencies.

One tenant's configuration must never affect another tenant.

## 3. Customer Rules

### BR-005 — Customer Registration

- A customer must belong to one tenant.
- A customer must have a minimum set of identifying information.
- Contact information may be updated by authorized users.
- Customers may have multiple contact details.
- Customers may have multiple quotations and events.

### BR-006 — Customer Archiving

- Customers with historical transactions must not be permanently deleted through normal application operations.
- Archiving a customer must not delete quotations, events, payments or expenses.
- Archived customers must remain available for historical consultation.
- Archived customers must not be selectable for new commercial operations unless explicitly reactivated.

## 4. Catalog and Menu Rules

### BR-007 — Catalog Items

- Dishes and beverages belong to a tenant.
- Catalog items may be active or inactive.
- Inactive items cannot be selected for new quotations.
- Existing quotations must preserve their historical item descriptions and prices.
- Changes to catalog information must not silently modify existing quotations.

### BR-008 — Menu Packages

- A menu package may contain multiple dishes and beverages.
- Packages may have configurable prices.
- Package prices may depend on company-specific pricing rules.
- A package can be modified or archived without changing historical quotations.
- Recipe information is optional in the MVP.

### BR-009 — Ingredient and Inventory Limitations

- The MVP does not require ingredient-level costing.
- The MVP does not maintain stock quantities.
- Recipe information may be stored for operational reference.
- Actual food and ingredient expenses are recorded as financial expense entries.

## 5. Pricing Rules

### BR-010 — Quotation Pricing

A quotation may include:

- Menu packages.
- Individual dishes.
- Beverages.
- Additional services.
- Staffing costs.
- Other configurable commercial items.

The final quotation amount must be calculated from its commercial components and authorized adjustments.

### BR-011 — Manual Price Adjustments

- Authorized users may apply discounts or additional charges.
- Adjustments must be explicitly recorded.
- The system must preserve the original amount and adjusted amount.
- Adjustment reasons should be recorded.
- Permission to apply adjustments may depend on the user's role.

### BR-012 — Pricing Configuration Changes

- Changes to pricing rules apply to future quotations.
- Existing quotations must retain their original calculated values.
- New quotation versions may use updated prices when recalculated.
- Previously approved quotations must not be recalculated automatically.

## 6. Quotation Rules

### BR-013 — Quotation Creation

- Every quotation must belong to one tenant.
- Every quotation must reference a customer.
- A quotation must contain the minimum required event and commercial information.
- A quotation must have at least one version.
- Each version must preserve its own commercial snapshot.

### BR-014 — Quotation Versions

- Every revision must create a new version.
- Previous versions must remain accessible.
- A version must not be silently overwritten.
- Each version must preserve its items, quantities, prices, discounts, totals and relevant commercial conditions.
- The system must identify which version was approved.
- Only an authorized user may create or approve quotation versions.

### BR-015 — Quotation Approval

- Approval must be recorded by an authorized company user in the MVP.
- The approved version must be explicitly identified.
- The approval date and responsible user must be recorded.
- Supporting information may be stored, such as an approval note or external communication reference.
- Approval must preserve the quotation's commercial snapshot.

Customer self-service approval is outside the MVP.

### BR-016 — Quotation Rejection and Expiration

- Rejected quotations must remain available for historical consultation.
- The rejection date must be recorded.
- A rejection reason may be stored.
- Quotation expiration must follow company-defined policies.
- Expired quotations cannot be converted into events without an explicit authorized action.

### BR-017 — Quotation Conversion

- Only approved quotations may be converted into events.
- Conversion must preserve the approved commercial information.
- Each approved quotation may generate only one primary event.
- Repeated conversion requests must not create duplicate events.
- The system must preserve the relationship between the event and its originating quotation version.

## 7. Event Rules

### BR-018 — Event Creation

An event created from a quotation must preserve:

- Customer information relevant to the transaction.
- Event date and location.
- Number of guests.
- Approved menu and services.
- Approved quotation amount.
- Agreed payment conditions.
- Relevant commercial notes.

### BR-019 — Event Status

Initial event statuses:

| Status | Description |
|---|---|
| Scheduled | Event has been created and scheduled |
| Confirmed | Event has been confirmed operationally |
| In Preparation | Planning and preparation are underway |
| In Progress | Event is currently happening |
| Completed | Event execution has finished |
| Cancelled | Event has been cancelled |

Status transitions must be validated by the backend.

An event cannot be marked as completed before it has entered an appropriate operational stage, unless an authorized correction is recorded.

### BR-020 — Operational and Financial Closure

Operational completion and financial closure are independent concepts.

- An event may be operationally completed while payments remain outstanding.
- An event may be financially settled before its operational completion.
- The event's operational status must not automatically imply that all financial obligations are settled.
- The system must display operational and financial information separately.

### BR-021 — Event Cancellation

- Only authorized users may cancel an event.
- A cancellation reason must be recorded.
- Existing payments must be preserved.
- Existing expenses must be preserved.
- Employee assignments must remain available in the event history.
- Refunds and cancellation charges must be represented through explicit financial records.
- Cancellation must not automatically delete or reverse financial transactions.

### BR-022 — Changes After Approval

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

## 8. Employee Rules

### BR-023 — Employee Types

The MVP supports:

- Fixed employees.
- Freelancers.

Both employee types may be assigned to events.

Their contractual and administrative information must be handled according to applicable legal requirements.

### BR-024 — Employee Assignment

- Employees may be assigned to one or more events.
- Assignments must identify the employee, event and responsibility.
- Planned working hours should be recorded.
- Assignment compensation conditions must be preserved when applicable.
- Employee availability and scheduling conflicts should be considered.

### BR-025 — Compensation

The system may support:

- Hourly compensation.
- Fixed compensation per event.
- Other explicitly configured compensation arrangements.

The applicable compensation method must be identified for each assignment.

The agreed compensation values must be preserved as historical snapshots.

Updating an employee's default compensation must not modify previous event assignments.

### BR-026 — Working Hours

- Planned and actual working hours must be distinguishable.
- Actual hours may be entered by authorized users.
- Corrections must generate audit records.
- Calculated staff costs must use the applicable assignment compensation conditions.
- Missing working-hour information must not be silently interpreted as zero.

### BR-027 — Employee Replacement

- Replacing an employee must preserve the original assignment history.
- The replacement must create or update the appropriate assignment record.
- Compensation conditions must be recorded independently for the replacement.
- Historical costs must remain traceable.

## 9. Payment Rules

### BR-028 — Payment Configuration

Each tenant may configure its payment conditions.

A payment schedule may define:

- Number of installments.
- Percentage or fixed amount per installment.
- Due dates or due-date calculation rules.
- Relevant payment descriptions.

### BR-029 — Payment Schedule Validation

For percentage-based installment schedules:

- The sum of installment percentages must equal 100%.
- Generated installment amounts must reconcile with the approved quotation total.
- Rounding differences must be handled explicitly.
- The final installment may absorb a documented rounding adjustment.

For fixed-amount schedules:

- The total scheduled amount must reconcile with the approved quotation total.
- Any remaining balance must be represented explicitly.

### BR-030 — Payment Schedule Snapshot

- Payment schedules must be generated using the configuration applicable at the time of approval.
- Changes to default payment settings must not alter existing schedules.
- Changes to an approved commercial total must follow an explicit change process.
- Previous payment conditions must remain available for historical consultation.

### BR-031 — Payment Registration

- Payments must be associated with an event and, where applicable, an installment.
- Each payment must record its amount, date and method.
- Payment records must identify the responsible user.
- Partial payments must be supported.
- The system must calculate outstanding balances.

### BR-032 — Payment Validation

- Payment amounts must be greater than zero.
- A payment must not exceed the outstanding balance of the relevant obligation unless an explicit overpayment workflow is supported.
- Invalid payment operations must be rejected.
- Payment corrections must preserve the original record through controlled reversal or correction operations.

### BR-033 — Payment Status

Initial installment statuses:

| Status | Description |
|---|---|
| Pending | No payment has been recorded |
| Partially Paid | Some amount has been received |
| Paid | The full installment amount has been received |
| Overdue | The due date has passed and an outstanding balance remains |
| Cancelled | The installment has been cancelled through an authorized operation |

Overdue status must be based on the due date and remaining balance.

### BR-034 — Refunds and Reversals

- Refunds must be explicitly recorded.
- A refund must reference the original payment when applicable.
- Reversed or corrected payments must remain traceable.
- Refunds must update the financial balance consistently.
- The system must not silently delete financial transactions.

Integrated payment processing is outside the MVP.

## 10. Expense Rules

### BR-035 — Expense Registration

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

### BR-036 — Expense Categories

Initial categories:

- Food and ingredients.
- Beverages.
- Staff.
- Transportation.
- Other expenses.

Categories may be configurable by tenant in a future enhancement.

### BR-037 — Expense Validation

- Expense amounts must be greater than zero.
- Expenses must be associated with an authorized tenant.
- Expenses must be associated with an event.
- Corrections must preserve the previous information in the audit history.
- Expense records must not be silently deleted after financial reporting or event closure.

### BR-038 — Expense Calculation

Actual event expenses must be calculated from recorded expense entries.

The system must not require individual ingredient costs.

Staff costs may be calculated from recorded employee assignments and applicable compensation conditions, but the system must avoid counting the same staff cost twice when a corresponding expense entry has already been recorded.

The final accounting treatment of manually entered staff expenses and calculated staff costs must be clearly defined before financial reporting is implemented.

## 11. Financial Reporting Rules

### BR-039 — Financial Indicators

The event financial summary must distinguish:

- Approved quotation amount.
- Payments received.
- Outstanding payment balance.
- Recorded actual expenses.
- Estimated expenses, if available.
- Actual financial result, based on recorded data.

### BR-040 — Revenue and Cash Flow

The system must distinguish commercial revenue from cash received.

- Approved quotation values represent agreed commercial amounts.
- Recorded payments represent received amounts.
- Outstanding balances represent amounts not yet received.
- Cancelled quotations and events must not be treated as automatically collected revenue.

### BR-041 — Event Financial Result

When all required data is available, the system may calculate:

**Estimated result:**

Approved quotation amount minus estimated costs.

**Actual result:**

Recognized event revenue minus recorded actual expenses.

The dashboard must clearly identify which values are estimated and which are based on actual records.

The result shown by CaterFlow is an operational management indicator and must not be presented as a legally certified accounting or tax result.

## 12. Internationalization and Localization Rules

### BR-042 — Supported Languages

The MVP supports:

- Portuguese.
- Spanish.
- English.

### BR-043 — Locale Formatting

- Dates must follow the selected locale.
- Numbers must follow the selected locale.
- Monetary values must display the appropriate currency.
- Generated documents must use the selected language.
- Internal timestamps must be stored consistently and displayed according to the applicable timezone.

### BR-044 — Timezone

The initial default timezone for Spanish companies is Europe/Madrid.

Each tenant must have an explicit timezone configuration.

Event dates and schedules must be interpreted in the company's configured timezone.

### BR-045 — Currency

EUR is the initial default currency.

Monetary transactions must store an explicit currency code.

Changing a tenant's default currency must not silently convert historical financial records.

Multi-currency financial consolidation is outside the initial MVP unless explicitly added to scope.

## 13. Audit and Data Integrity Rules

### BR-046 — Audit Records

Important operations must generate audit records containing, where applicable:

- Tenant.
- User.
- Action.
- Entity type.
- Entity identifier.
- Timestamp.
- Relevant change information.

### BR-047 — Historical Traceability

The system must preserve the history of:

- Quotation versions.
- Quotation approvals.
- Event status transitions.
- Employee assignments.
- Payment records.
- Expense records.
- Relevant administrative changes.

### BR-048 — Controlled Corrections

Historical business records must be corrected through explicit operations.

Corrections must not silently overwrite important financial or commercial history.

### BR-049 — Data Retention

Retention and deletion policies must consider applicable legal, tax, contractual and data protection requirements.

Personal data must not be retained indefinitely without a valid basis.

Audit and financial records must follow an appropriate retention policy rather than being deleted simply to reduce storage costs.

## 14. Authorization Rules

### BR-050 — Permission Validation

- Every protected operation must validate the authenticated user.
- Every protected operation must validate the active tenant context.
- Every protected operation must validate the user's permissions.
- Frontend restrictions alone are insufficient.
- Unauthorized requests must be rejected by the backend.

### BR-051 — Sensitive Financial Operations

Access to payment corrections, refunds, financial reports and expense modifications must be controlled by explicit permissions.

### BR-052 — Employee Information

Employees must only access information required for their assigned responsibilities.

Personal, compensation and administrative information must be restricted to authorized users.

## 15. Open Business Decisions

The following decisions require validation before implementation:

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

---

**Document status:** Initial draft. Business rules must be validated before database modeling and implementation.