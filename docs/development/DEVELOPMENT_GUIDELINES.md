# Development Guidelines

**Project:** CaterFlow  
**Document:** Development Guidelines  
**Version:** 0.1  
**Status:** Initial specification  
**Last updated:** November 2026

---

## 1. Purpose

This document defines the development standards and conventions for the CaterFlow codebase.

Its objectives are to:

- Maintain consistency across backend and frontend development.
- Encourage readable, maintainable, and testable code.
- Establish clear responsibilities between application layers.
- Reduce unnecessary coupling between modules.
- Prevent security and data-isolation mistakes.
- Make future contributions easier to review and understand.

These guidelines apply to all new features, bug fixes, refactoring, and infrastructure-related code.

## 2. General Development Principles

All development must follow these principles:

### 2.1 Readability First

Code should be easy to understand without requiring excessive comments or external explanations.

Prefer explicit and descriptive names over abbreviations.

### 2.2 Single Responsibility

Each module, class, and function should have a clearly defined responsibility.

### 2.3 Avoid Unnecessary Complexity

Do not introduce abstractions, patterns, or dependencies without a concrete need.

### 2.4 Reuse Without Overengineering

Common behavior should be reused when appropriate, but unrelated business concepts must not be forced into generic abstractions.

### 2.5 Explicit Business Rules

Business rules must be implemented in the backend and covered by tests.

The frontend must never be the only place where a business rule is enforced.

### 2.6 Consistency

Existing project conventions should be followed unless there is a documented reason to change them.

## 3. Repository Organization

The project will use separate backend and frontend applications.

```text
caterflow/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── migrations/
│   ├── pyproject.toml
│   └── ...
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── docs/
├── .github/
├── docker-compose.yml
└── README.md
```

The exact internal structure may evolve during implementation, but the separation between backend, frontend, and documentation must be preserved.

## 4. Backend Development Standards

### 4.1 Technology

The backend will use:

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy 2.x.
- Alembic.
- PostgreSQL.
- Pytest.

### 4.2 Modular Monolith

The backend must follow a modular monolith architecture.

Each business module must own its domain responsibilities and expose clear interfaces to other modules.

Initial modules:

- Identity
- Tenants
- Customers
- Catalog
- Pricing
- Quotations
- Events
- Workforce
- Payments
- Expenses
- Reporting
- Audit
- Storage

Modules must not directly manipulate another module's internal implementation.

Cross-module operations should use explicit service interfaces or application use cases.

### 4.3 Suggested Module Structure

A module may use the following organization:

```text
app/
├── modules/
│   ├── customers/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── api/
│   │   └── exceptions.py
│   ├── quotations/
│   └── events/
├── core/
├── infrastructure/
├── api/
└── main.py
```

Not every module needs every directory.

Directories should only be introduced when they provide a meaningful separation of responsibilities.

### 4.4 Layer Responsibilities

**API layer**

- Defines HTTP endpoints.
- Validates request and response schemas.
- Applies authentication and authorization dependencies.
- Converts application results into HTTP responses.
- Must not contain complex business logic.

**Service / application layer**

- Implements use cases.
- Coordinates domain operations.
- Enforces business rules.
- Controls transaction boundaries where appropriate.
- Coordinates interactions between modules through explicit interfaces.

**Repository layer**

- Encapsulates database access.
- Implements queries and persistence operations.
- Enforces tenant-scoped query requirements.
- Must not contain HTTP-specific logic.

**Model / domain layer**

- Represents business entities and domain behavior.
- Defines domain-level invariants where appropriate.
- Must not depend on FastAPI request or response objects.

**Infrastructure layer**

- Provides technical integrations such as database sessions, storage adapters, email providers, and external services.

The exact implementation may vary by module, but responsibilities must remain clear.

### 4.5 Python Conventions

- Follow PEP 8.
- Use type hints for function arguments and return values.
- Prefer descriptive names.
- Use `snake_case` for functions, variables, and modules.
- Use `PascalCase` for classes.
- Use `UPPER_SNAKE_CASE` for constants.
- Avoid functions with excessive responsibilities.
- Avoid deeply nested conditional logic.
- Use explicit exceptions rather than silently ignoring failures.
- Avoid mutable default arguments.
- Use asynchronous functions only where asynchronous I/O is actually required.

### 4.6 Pydantic Schemas

Pydantic schemas must explicitly define accepted and returned data.

Separate schemas should be used for different operations when their responsibilities differ.

Examples:

- `CustomerCreate`
- `CustomerUpdate`
- `CustomerResponse`
- `QuotationCreate`
- `QuotationApproval`

Do not expose SQLAlchemy models directly as API responses.

Sensitive internal fields must never be included in response schemas without an explicit requirement.

### 4.7 SQLAlchemy and Database Access

Use SQLAlchemy 2.x patterns.

Requirements:

- Use explicit database sessions.
- Use transactions for operations that modify related records.
- Avoid unnecessary database queries.
- Prevent N+1 query problems.
- Use eager loading where appropriate.
- Define relationships and constraints explicitly.
- Avoid raw SQL unless there is a justified technical need.
- Use parameterized queries for raw SQL.
- Keep database access inside repositories or clearly defined persistence components.

All tenant-owned queries must enforce the authorized tenant context.

### 4.8 Database Migrations

Alembic must manage database schema changes.

Requirements:

- Every schema change must have a migration.
- Migrations must be reviewed before deployment.
- Destructive migrations require additional care.
- Existing production data must be considered.
- Migrations must be tested against representative database states.
- Schema changes must not be performed manually in production.

Migration files must be committed to version control.

### 4.9 Financial Calculations

Financial operations require additional care.

Requirements:

- Use `Decimal` for monetary calculations.
- Never use binary floating-point values for financial arithmetic.
- Use database `NUMERIC` columns for monetary values.
- Define rounding rules explicitly.
- Preserve historical financial snapshots.
- Keep estimated and actual amounts separate.
- Avoid duplicate expense recognition.
- Use transactions for operations involving multiple financial records.

Financial calculations must be implemented in reusable backend services and covered by dedicated tests.

## 5. Frontend Development Standards

### 5.1 Technology

The frontend will use:

- Next.js.
- React.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.

### 5.2 Feature-Based Organization

The frontend should be organized by business feature rather than placing all application logic in a single global directory.

Suggested structure:

```text
frontend/
└── src/
    ├── app/
    ├── components/
    │   ├── ui/
    │   └── shared/
    ├── features/
    │   ├── customers/
    │   ├── quotations/
    │   ├── events/
    │   ├── workforce/
    │   ├── payments/
    │   └── expenses/
    ├── hooks/
    ├── lib/
    ├── services/
    ├── types/
    └── i18n/
```

The final structure may be adjusted as the frontend grows.

### 5.3 React Components

Components should have a clear responsibility.

Requirements:

- Prefer small, reusable components.
- Separate presentation from complex application logic.
- Avoid excessively large page components.
- Use shared components for repeated interface patterns.
- Keep business rules out of purely presentational components.
- Avoid unnecessary state and effects.
- Use React Server Components where appropriate.
- Use Client Components only when browser interaction or client-side state requires them.

### 5.4 TypeScript

TypeScript must be used throughout the frontend.

Requirements:

- Avoid `any`.
- Define explicit interfaces or types for API contracts.
- Reuse types when appropriate.
- Handle nullable and optional values explicitly.
- Avoid unsafe type assertions.
- Keep frontend types aligned with backend API contracts.

### 5.5 API Communication

Frontend API communication must use a centralized service layer.

Requirements:

- Avoid duplicating HTTP configuration across components.
- Centralize API base URL configuration.
- Handle authentication consistently.
- Normalize API errors.
- Handle loading, success, empty, and error states.
- Avoid placing authorization decisions exclusively in frontend code.

The backend remains the source of truth for permissions and business rules.

### 5.6 UI Components and Design Consistency

Tailwind CSS and shadcn/ui will be used to maintain consistent interface patterns.

Requirements:

- Reuse common form, dialog, table, and navigation components.
- Maintain consistent spacing and typography.
- Provide accessible labels and interaction states.
- Support responsive layouts.
- Avoid duplicating large blocks of styling.
- Keep tenant branding configurable rather than hardcoded.

### 5.7 Internationalization

All user-facing text must support the application's localization strategy.

Requirements:

- Do not hardcode interface text directly into components when it should be translated.
- Use translation keys.
- Support Portuguese, Spanish, and English.
- Format dates, numbers, and currencies according to the selected locale.
- Use the tenant's configured timezone for business dates and times.
- Generate PDFs in the selected language where supported.

The initial default locale and timezone must follow tenant configuration.

## 6. Naming Conventions

### 6.1 Backend

| Element | Convention | Example |
|---|---|---|
| Modules | snake_case | `quotations` |
| Files | snake_case | `quotation_service.py` |
| Classes | PascalCase | `QuotationService` |
| Functions | snake_case | `create_quotation` |
| Variables | snake_case | `tenant_id` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_CURRENCY` |

### 6.2 Frontend

| Element | Convention | Example |
|---|---|---|
| Components | PascalCase | `QuotationForm.tsx` |
| Hooks | camelCase with `use` | `useCustomers.ts` |
| Functions | camelCase | `createQuotation` |
| Variables | camelCase | `tenantId` |
| Types and interfaces | PascalCase | `QuotationResponse` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_PAGE_SIZE` |

Naming must communicate intent and business meaning.

## 7. Error Handling

Errors must be handled consistently across the application.

### 7.1 Backend

The backend must distinguish between:

- Validation errors.
- Authentication errors.
- Authorization errors.
- Resource not found errors.
- Business rule violations.
- Conflict errors.
- Unexpected internal errors.

Expected application errors should use consistent response structures.

Unexpected exceptions must be handled by centralized error handling and must not expose internal details.

### 7.2 Frontend

The frontend must:

- Display understandable error messages.
- Avoid exposing stack traces or internal API details.
- Preserve form data when practical.
- Provide clear validation feedback.
- Handle expired sessions consistently.
- Distinguish between network failures and application errors.

## 8. Security Requirements During Development

Security must be considered in every feature.

Mandatory rules:

- Never trust frontend-provided tenant identifiers without backend validation.
- Never rely on hidden buttons or frontend routes for authorization.
- Never expose secrets in source code.
- Never log passwords, tokens, or credentials.
- Validate all external input.
- Enforce tenant ownership in database queries.
- Verify permissions before sensitive operations.
- Protect file uploads and downloads.
- Use secure password and session handling.
- Add security tests for sensitive operations.

Security requirements are detailed in `SECURITY.md`.

## 9. Testing Standards

Tests must be created alongside application features.

Backend tests must cover:

- Unit behavior.
- Application services.
- API endpoints.
- Database operations.
- Tenant isolation.
- Authorization.
- Financial calculations.
- Error scenarios.

Frontend tests must cover:

- Component behavior.
- Form validation.
- User interactions.
- Loading and error states.
- Feature-level workflows.

Critical end-to-end workflows must be tested before production releases.

See `TESTING.md`.

## 10. Code Quality and Tooling

The project should use automated tools to maintain code quality.

### 10.1 Backend

Recommended tools:

- Ruff for linting and formatting.
- Pytest for automated tests.
- Mypy or an equivalent static type checker where appropriate.
- Coverage reporting.
- Dependency vulnerability scanning.

### 10.2 Frontend

Recommended tools:

- ESLint.
- Prettier.
- TypeScript compiler checks.
- Vitest or an equivalent component testing framework.
- Playwright or an equivalent end-to-end testing framework.
- Dependency vulnerability scanning.

Exact tool versions and configurations must be defined during project setup.

### 10.3 Continuous Integration

CI pipelines should execute:

1. Dependency installation using lockfiles.
2. Formatting and lint checks.
3. Static type checks.
4. Backend tests.
5. Frontend tests.
6. Production build validation.
7. Dependency security checks where configured.

A change should not be merged if mandatory quality checks fail.

## 11. Git and Commit Conventions

Git must be used for all project development.

Commit messages should follow a consistent convention.

Recommended format:

```text
<type>: <short description>
```

Examples:

```text
feat: add customer management
fix: prevent cross-tenant customer access
docs: update authentication guidelines
test: add quotation calculation tests
refactor: simplify payment service
chore: configure backend linting
```

Suggested commit types:

- `feat`: New functionality.
- `fix`: Bug fixes.
- `docs`: Documentation changes.
- `test`: Test-related changes.
- `refactor`: Code restructuring without intended behavior changes.
- `chore`: Maintenance and tooling.
- `security`: Security-related changes.

Commits should be small enough to review and describe one coherent change.

## 12. Pull Request and Code Review

Before merging a change, review:

- Whether the implementation satisfies the requirement.
- Whether business rules are enforced in the backend.
- Whether tenant isolation is preserved.
- Whether authorization is correct.
- Whether tests cover expected behavior and failure scenarios.
- Whether database migrations are included when needed.
- Whether translations are included.
- Whether documentation needs updating.
- Whether secrets or sensitive data were introduced accidentally.

Security-sensitive changes must receive additional scrutiny.

## 13. Documentation Requirements

Documentation must evolve with the codebase.

When introducing a significant feature, update relevant documentation.

Examples:

- New business rules: update `BUSINESS_RULES.md`.
- New user workflows: update `USER_FLOWS.md`.
- Architectural changes: update architecture documentation and create an ADR when appropriate.
- New environment variables: update deployment documentation and `.env.example`.
- API changes: update the API documentation.
- New test procedures: update `TESTING.md`.

Documentation must describe implemented behavior accurately and must not present planned functionality as already available.

## 14. Development Workflow

The recommended workflow for each feature is:

1. Review the relevant product and architecture requirements.
2. Define the expected behavior and acceptance criteria.
3. Identify affected modules and data entities.
4. Review security and tenant-isolation implications.
5. Implement backend schemas and business logic.
6. Implement persistence and migrations when necessary.
7. Create backend tests.
8. Implement frontend integration and interface.
9. Add frontend tests where appropriate.
10. Run quality checks.
11. Review documentation.
12. Commit the completed change.

Features should be implemented in small, verifiable increments.

## 15. Final Principles

The CaterFlow codebase must prioritize clarity, correctness, security, and maintainability.

The architecture should remain a modular monolith unless concrete requirements justify a different approach.

Developers must avoid unnecessary complexity while preserving clear boundaries between business modules.

All critical business rules, financial calculations, permissions, and tenant-isolation requirements must be enforced by the backend and covered by automated tests.

**End of document.**