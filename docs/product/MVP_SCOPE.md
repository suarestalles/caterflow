# CaterFlow — MVP Scope

**Version:** 0.1  
**Status:** Initial Draft  
**Product:** CaterFlow SaaS  
**Initial Market:** Spain  
**Deployment Model:** Cloud SaaS  
**Supported Languages:** Portuguese, Spanish and English

## 1. MVP Objective

The objective of the CaterFlow MVP is to deliver a functional catering management platform that centralizes the essential commercial, operational and financial workflows of small and medium-sized catering companies.

The MVP must provide sufficient functionality for a real catering company to manage its customers, quotations, events, employees, payments and expenses without relying on disconnected spreadsheets and paper-based processes.

The first release will prioritize reliability, usability, data security and operational efficiency.

## 2. Target Users

The MVP will support the following user profiles:

| Profile | Description |
|---|---|
| Platform Administrator | Manages the SaaS platform and its tenants |
| Company Owner | Manages company configuration and business operations |
| Company Administrator | Manages users, settings and company data |
| Manager | Manages customers, quotations, events and finances |
| Chef | Accesses menus and operational event information |
| Fixed Employee | Accesses assigned events and work information |
| Freelancer | Accesses assigned events and work information |

Permissions will be configurable according to the user's role and company policies.

## 3. Functional Scope

### 3.1 Tenant and Company Management

**Priority: P0 — Essential**

- Company registration.
- Company profile configuration.
- Company name, logo, address and contact details.
- Tax identification information.
- Company timezone and currency settings.
- Language preferences.
- User invitations and management.
- Tenant-specific application settings.

Each company must access only its own data.

### 3.2 Authentication and Access Control

**Priority: P0 — Essential**

- User login and logout.
- JWT-based authentication.
- Secure password storage.
- Password recovery.
- User invitation and account activation.
- Role-based permissions.
- Active company context.
- Secure tenant isolation.

### 3.3 Customer Management

**Priority: P0 — Essential**

- Create, edit and archive customers.
- Store customer names and contact information.
- Store billing and identification information when required.
- Maintain customer history.
- Associate customers with quotations and events.

### 3.4 Catalog Management

**Priority: P0 — Essential**

- Register dishes.
- Register beverages.
- Organize products into categories.
- Maintain item descriptions.
- Configure active and inactive catalog items.
- Create menu packages.
- Maintain optional recipe and technical information.

Ingredient-level costing and inventory control are excluded from the MVP.

### 3.5 Pricing Configuration

**Priority: P0 — Essential**

- Configure pricing rules.
- Define different service formats.
- Support different event types.
- Configure menu package prices.
- Allow manual price adjustments.
- Support different commercial proposals.

Pricing rules must be configurable per company.

Historical quotations must preserve the prices and conditions used when they were created or approved.

### 3.6 Quotation Management

**Priority: P0 — Essential**

- Create quotations for registered customers.
- Define event type, date, location and guest count.
- Select menus, beverages and additional services.
- Configure staffing requirements.
- Calculate quotation totals.
- Allow manual adjustments.
- Create multiple quotation versions.
- Generate branded PDF proposals.
- Record quotation status.
- Record customer approval manually.
- Convert approved quotations into events.

Each quotation version must preserve its own commercial information.

### 3.7 Event Management

**Priority: P0 — Essential**

- Create events from approved quotations.
- View events in a calendar.
- Manage event details and locations.
- Track event status.
- Assign fixed employees and freelancers.
- Define employee responsibilities.
- Record planned and actual working hours.
- Store operational notes.
- Maintain event history.

### 3.8 Employee Management

**Priority: P0 — Essential**

- Register fixed employees.
- Register freelancers.
- Store contact information.
- Define employee type.
- Configure compensation information where applicable.
- Assign employees to events.
- Record working hours.
- Maintain assignment history.

Historical event costs must not change when an employee's default compensation settings are updated.

### 3.9 Payment Management

**Priority: P0 — Essential**

- Configure payment schedules.
- Define installment percentages.
- Define payment due dates.
- Generate installments associated with approved quotations or events.
- Record payments manually.
- Track outstanding balances.
- Display overdue installments.

Payment processing through external providers is excluded.

### 3.10 Event Expense Management

**Priority: P0 — Essential**

- Record actual event expenses.
- Categorize expenses.
- Record descriptions and amounts.
- Record expense dates.
- Associate expenses with responsible users.
- Support optional receipt attachments.

Initial expense categories:

- Food and ingredients.
- Beverages.
- Staff.
- Transportation.
- Other expenses.

The MVP will not require individual ingredient prices or inventory movements.

### 3.11 Dashboard and Basic Reports

**Priority: P1 — Important**

- Display upcoming events.
- Display event counts.
- Display quotation status.
- Display total quotation values.
- Display paid and outstanding amounts.
- Display recorded expenses.
- Display estimated versus actual event results.

Financial indicators must clearly distinguish estimated values from recorded actual values.

### 3.12 Audit History

**Priority: P0 — Essential**

- Record important changes to quotations.
- Record quotation approvals.
- Record event status changes.
- Record payment updates.
- Record expense creation and updates.
- Associate changes with users and timestamps.

## 4. Internationalization

**Priority: P0 — Essential**

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

The initial market is Spain. EUR will be the initial default currency, with currency configuration designed to support future markets.

## 5. Cloud Deployment

**Priority: P0 — Essential**

- Centralized cloud-hosted application.
- Shared application infrastructure.
- Shared PostgreSQL database schema.
- Tenant data isolation.
- HTTPS communication.
- Automated database migrations.
- Backup strategy.
- Environment-based configuration.
- Centralized application logging.
- File storage abstraction.

The platform must be accessible through modern web browsers on desktop and mobile devices.

## 6. MVP Exclusions

The following capabilities will not be developed in the initial release:

| Feature | Reason |
|---|---|
| Public marketplace | Requires a separate commercial and customer acquisition strategy |
| Customer self-service portal | Not essential for internal operations |
| Integrated payment processing | Adds financial and provider integration complexity |
| WhatsApp integration | Can be considered after core workflows are validated |
| Native mobile applications | Responsive web interface is sufficient initially |
| Advanced inventory management | Outside the initial operational scope |
| Automated fiscal integrations | Requires additional legal and technical validation |
| Banking integrations | Not essential for the first release |
| AI recommendations | Future enhancement |
| Advanced analytics | Basic business indicators are sufficient |
| Custom code per tenant | The product must remain a shared SaaS platform |

## 7. Priority Definitions

- **P0 — Essential:** Required for the MVP to be considered operational.
- **P1 — Important:** Strongly recommended for the first commercial release, but can be delivered after core workflows.
- **P2 — Future:** Not required for the MVP.

## 8. MVP Acceptance Criteria

The MVP will be considered ready for pilot validation when:

1. A company can register and configure its tenant.
2. Company users can authenticate securely.
3. Tenant data is isolated and tested.
4. Customers can be registered and managed.
5. Dishes, beverages and menu packages can be configured.
6. A manager can create and revise a quotation.
7. A quotation PDF can be generated using company branding.
8. An approved quotation can become an event.
9. Fixed employees and freelancers can be assigned to events.
10. Payment installments can be configured and tracked.
11. Actual event expenses can be recorded.
12. Basic financial indicators can be displayed.
13. Important operations are recorded in the audit history.
14. The interface supports Portuguese, Spanish and English.
15. The application can be accessed through its cloud deployment.
16. Automated tests validate critical business workflows and tenant isolation.

## 9. Pilot Validation

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

Feedback from the pilot will determine the next development priorities.

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

---

**Document status:** Initial draft. The scope must be reviewed against business requirements and pilot company needs before implementation.