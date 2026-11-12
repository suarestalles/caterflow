# CaterFlow — User Flows

**Version:** 0.1  
**Status:** Initial Draft  
**Product:** CaterFlow SaaS

## 1. Purpose

This document describes the main user journeys and operational workflows supported by CaterFlow.

It establishes how users interact with the platform, how business processes progress, and how information moves between the commercial, operational and financial areas.

These flows will guide interface design, backend implementation and database modeling.

## 2. User Profiles

### 2.1 Platform Administrator

Responsible for the SaaS platform itself.

Main activities:
- Manage tenant accounts.
- Monitor platform operation.
- Manage subscription-related settings when implemented.
- Provide platform-level support.

Platform administrators must not automatically have unrestricted access to tenant business information.

### 2.2 Company Owner

Responsible for the catering company's overall operation.

Main activities:
- Configure company information.
- Manage users and permissions.
- Manage customers, quotations and events.
- Monitor payments and expenses.
- Access financial reports.

### 2.3 Company Administrator

Responsible for company configuration and administrative operations.

Main activities:
- Manage users.
- Configure company settings.
- Manage catalogs and pricing.
- Access authorized business information.

### 2.4 Manager

Responsible for commercial and operational coordination.

Main activities:
- Register customers.
- Create and manage quotations.
- Coordinate event preparation.
- Assign employees.
- Track payments and expenses.

### 2.5 Chef

Responsible for food preparation and kitchen coordination.

Main activities:
- View assigned events.
- Access menus and relevant technical information.
- Review guest counts and operational requirements.
- Coordinate kitchen activities.

### 2.6 Fixed Employee

Responsible for performing assigned event activities.

Main activities:
- View assigned events.
- Consult schedules and responsibilities.
- Access relevant operational information.
- Record working hours when authorized.

### 2.7 Freelancer

Responsible for temporary event assignments.

Main activities:
- View accepted or assigned event information.
- Consult schedules and responsibilities.
- Access relevant operational information.
- Record working hours when authorized.

Employee access must be restricted to information required for their responsibilities.

## 3. Main Event Lifecycle

The primary CaterFlow workflow follows this sequence:

1. Customer registration.
2. Event request registration.
3. Quotation creation.
4. Quotation review and revision.
5. Customer approval.
6. Event creation.
7. Operational planning.
8. Event execution.
9. Expense and payment tracking.
10. Event closure.

Each stage must have clearly defined status transitions and permissions.

## 4. Customer Management Flow

### 4.1 Register a Customer

**Actor:** Owner, Administrator or Manager.

Steps:

1. Open the Customers section.
2. Select the option to create a customer.
3. Enter customer information.
4. Save the registration.
5. Open the customer profile.

Expected result:

- Customer is registered within the active tenant.
- Customer information is available for quotation creation.
- The system maintains the customer's history.

### 4.2 Update Customer Information

1. Search for the customer.
2. Open the customer profile.
3. Edit the required information.
4. Save the changes.

Historical quotations and events must preserve relevant snapshots of commercial and billing information where required.

## 5. Quotation Management Flow

### 5.1 Create a Quotation

**Actor:** Owner, Administrator or Manager.

Steps:

1. Open the Quotations section.
2. Select a registered customer.
3. Enter event information:
   - Event type.
   - Date and time.
   - Location.
   - Number of guests.
   - Service format.
4. Select dishes and beverages.
5. Configure additional services.
6. Define staffing requirements.
7. Review pricing calculations.
8. Apply authorized manual adjustments.
9. Save the quotation.

Expected result:

- A quotation is created.
- A first version is stored.
- The quotation receives an initial status.
- The quotation can be previewed and exported as a PDF.

### 5.2 Generate a Quotation PDF

1. Open the quotation.
2. Select the document language.
3. Preview the proposal.
4. Generate the PDF.
5. Save the generated document.
6. Make the document available for external sharing.

The PDF must contain the appropriate company identity and the commercial information associated with the quotation version.

### 5.3 Revise a Quotation

**Trigger:** Customer requests changes.

Steps:

1. Open the existing quotation.
2. Review the customer's requested changes.
3. Create a new quotation version.
4. Modify the required information.
5. Recalculate the quotation.
6. Generate a new PDF.
7. Share the revised proposal.

Expected result:

- The previous version remains available.
- The new version contains the updated information.
- The quotation history identifies the versions and their creation dates.

Previously approved information must never be silently overwritten.

### 5.4 Record Customer Approval

**Actor:** Owner, Administrator or Manager.

Steps:

1. Open the quotation.
2. Confirm which version the customer approved.
3. Record the approval.
4. Record the approval date and available supporting information.
5. Confirm the commercial conditions.
6. Convert the approved quotation into an event.

For the MVP, approval is recorded manually by an authorized company user.

The customer does not need a CaterFlow account.

### 5.5 Reject or Cancel a Quotation

If the customer declines the proposal:

1. Open the quotation.
2. Change its status to rejected.
3. Optionally record the reason.
4. Preserve the quotation history.

A quotation may also expire according to company-defined commercial policies.

## 6. Event Management Flow

### 6.1 Create an Event from an Approved Quotation

**Actor:** Owner, Administrator or Manager.

Steps:

1. Open an approved quotation.
2. Select Convert to Event.
3. Review the event details.
4. Confirm the event creation.
5. Open the event management page.

Expected result:

- A new event is created.
- The customer is associated with the event.
- Relevant quotation information is preserved.
- Approved commercial values remain historically consistent.
- The event receives its initial status.

The conversion must not create duplicate events if the operation is repeated accidentally.

### 6.2 Plan an Event

1. Open the event.
2. Review the event date, location and guest count.
3. Review the approved menu and services.
4. Define operational requirements.
5. Assign chefs and other employees.
6. Define responsibilities and schedules.
7. Save the operational plan.

Changes affecting approved commercial conditions must follow an explicit change process.

### 6.3 Monitor Event Status

Managers can update the event status as the operation progresses.

Initial status concepts:

- Scheduled.
- Confirmed.
- In Preparation.
- In Progress.
- Completed.
- Cancelled.

The final status transition rules will be defined in BUSINESS_RULES.md.

### 6.4 Cancel an Event

1. Open the event.
2. Select the cancellation action.
3. Record the cancellation reason.
4. Review existing payment and financial information.
5. Confirm cancellation.

The system must preserve the event history and financial records.

Cancellation must not automatically erase payments or expenses.

Refunds and cancellation fees will follow company-defined policies and require explicit financial records.

## 7. Employee Management Flow

### 7.1 Register an Employee

**Actor:** Owner, Administrator or authorized Manager.

Steps:

1. Open the Employees section.
2. Select the employee type:
   - Fixed employee.
   - Freelancer.
3. Enter personal and contact information.
4. Configure relevant compensation information.
5. Save the employee record.

Employment and contractual information must be handled according to applicable legal requirements.

### 7.2 Assign an Employee to an Event

1. Open the event.
2. Access the team assignment section.
3. Select an employee or freelancer.
4. Define the assigned responsibility.
5. Define the planned working schedule.
6. Record the agreed compensation conditions when applicable.
7. Confirm the assignment.

The system must preserve the agreed compensation snapshot for that assignment.

### 7.3 Replace an Assigned Employee

1. Open the event.
2. Locate the employee assignment.
3. Record the replacement or cancellation of the original assignment.
4. Select the replacement employee.
5. Define the new assignment conditions.
6. Save the changes.

The assignment history must remain available.

### 7.4 Record Working Hours

1. Open the employee assignment.
2. Enter actual start and end times or total hours.
3. Review the recorded information.
4. Save the record.

Authorized users may correct recorded hours while preserving an audit trail.

## 8. Payment Management Flow

### 8.1 Generate Payment Installments

When a quotation is approved and converted into an event:

1. Retrieve the applicable payment configuration.
2. Generate the installment schedule.
3. Calculate the amounts based on the approved quotation total.
4. Assign due dates.
5. Associate installments with the event.

The payment schedule must preserve the conditions applicable at approval time.

### 8.2 Record a Payment

**Actor:** Owner, Administrator or authorized Manager.

Steps:

1. Open the event's financial section.
2. Select the relevant installment.
3. Enter the amount received.
4. Enter the payment date.
5. Select the payment method.
6. Optionally enter a reference or note.
7. Save the payment.

Expected result:

- The payment is recorded.
- The installment balance is recalculated.
- The event's outstanding balance is updated.

Partial payments must be supported.

### 8.3 Handle Overdue Payments

1. Identify installments past their due dates.
2. Display the overdue status.
3. Allow authorized users to record subsequent payments.
4. Preserve the payment history.

The MVP does not automatically charge customers or process refunds.

## 9. Event Expense Management Flow

### 9.1 Record an Expense

**Actor:** Owner, Administrator or authorized Manager.

Steps:

1. Open the event.
2. Access the Expenses section.
3. Select an expense category.
4. Enter a description.
5. Enter the total amount.
6. Enter the expense date.
7. Optionally attach a receipt.
8. Save the expense.

Initial categories:

- Food and ingredients.
- Beverages.
- Staff.
- Transportation.
- Other expenses.

The MVP records actual expenses by amount and category. It does not require individual ingredient pricing.

### 9.2 Review Event Financial Results

1. Open the event's financial summary.
2. Review the approved quotation value.
3. Review recorded payments.
4. Review actual expenses.
5. Review estimated and actual financial indicators.

The system must clearly distinguish revenue, amounts received, outstanding balances and expenses.

## 10. Event Closure Flow

**Actor:** Owner, Administrator or authorized Manager.

Steps:

1. Open the completed event.
2. Confirm that the event execution has finished.
3. Review employee hours.
4. Review recorded expenses.
5. Review payments and outstanding balances.
6. Review the financial summary.
7. Mark the event as closed.

Closure must preserve historical information.

If corrections are needed after closure, authorized users must perform them through controlled operations that generate an audit record.

## 11. Dashboard Flow

1. User authenticates.
2. User selects or enters the appropriate company context.
3. The dashboard loads information available to that user.
4. The user reviews relevant indicators.
5. The user navigates to events, quotations, payments or expenses.

Dashboard data must always respect tenant isolation and role permissions.

## 12. Tenant and Company Context

1. User authenticates.
2. The system identifies the user's authorized tenant memberships.
3. The user enters an authorized company context.
4. All subsequent operations are scoped to that tenant.
5. Switching companies requires selecting another authorized tenant context.

Tenant context must be validated by the backend, not trusted solely from frontend input.

## 13. Internationalization Flow

1. User selects a preferred language.
2. The interface displays translated content.
3. Dates and numeric values follow the selected locale.
4. Generated documents use the selected document language.
5. Company-specific defaults may be applied where appropriate.

Initial supported languages:

- Portuguese.
- Spanish.
- English.

## 14. Error and Exception Scenarios

The system must handle at least the following cases:

- Attempt to access another tenant's data.
- Invalid or expired authentication.
- Missing required quotation information.
- Attempt to approve a quotation without a valid version.
- Attempt to create an event from an unapproved quotation.
- Duplicate event conversion requests.
- Invalid payment amounts.
- Payments exceeding the outstanding balance, requiring explicit handling.
- Event cancellation with existing payments.
- Employee assignment conflicts.
- Invalid or incomplete expense records.
- Unauthorized modifications to closed events.

Errors must be communicated clearly without exposing sensitive technical information.

## 15. Open Questions

The following details require validation before implementation:

1. Can one user belong to multiple catering companies?
2. Should employees have individual login accounts in the MVP, or should some companies manage them only through administrative accounts?
3. Can employees confirm or accept event assignments?
4. Should employee working hours require manager approval?
5. Can a closed event be reopened?
6. Which event changes require a revised quotation?
7. Can a customer have multiple contacts?
8. Should customers have individual or company-based registration?
9. Which information must be visible to chefs and temporary staff?
10. Should an event be considered financially closed when all payments are received, or can operational closure happen independently?

---

**Document status:** Initial draft. Detailed business rules and status transitions will be defined in BUSINESS_RULES.md.