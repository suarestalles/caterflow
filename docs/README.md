CaterFlow Documentation
Project: CaterFlow
Document: Documentation Index
Version: 0.2
Status: Implementation-aligned documentation index
Last updated: November 2026
Welcome to the technical and product documentation for CaterFlow.

CaterFlow is a planned cloud-based, multi-tenant SaaS platform for catering companies. Its intended scope includes customer and catalog management, quotations, events, workforce, payments, expenses, and financial reporting.

This documentation describes both the approved product direction and the current implementation. A feature described as planned or specified must not be assumed to be implemented. The implementation status in the relevant documents is authoritative for that distinction.
1. Documentation Structure
docs/
├── README.md
│
├── product/
│   ├── PRD.md
│   ├── MVP_SCOPE.md
│   ├── USER_FLOWS.md
│   └── BUSINESS_RULES.md
│
├── architecture/
│   ├── ARCHITECTURE.md
│   ├── MULTI_TENANCY.md
│   ├── AUTHENTICATION.md
│   ├── DATABASE.md
│   ├── STORAGE.md
│   └── SECURITY.md
│
├── development/
│   ├── ROADMAP.md
│   ├── DEVELOPMENT_GUIDELINES.md
│   ├── TESTING.md
│   └── DEPLOYMENT.md
│
└── adr/
    └── README.md
The tree represents the documentation structure. Individual documents may be expanded as the project evolves.
2. Product Documentation
Product documents describe what CaterFlow is intended to do, who it serves, and the business rules that govern its workflows.
Document	Description
[PRD.md](product/PRD.md)	Product vision, objectives, target users, requirements, constraints, and success metrics.
[MVP_SCOPE.md](product/MVP_SCOPE.md)	MVP priorities, included capabilities, exclusions, and acceptance criteria, distinguishing implemented functionality from remaining work.
[USER_FLOWS.md](product/USER_FLOWS.md)	User journeys and operational workflows, with their implementation status.
[BUSINESS_RULES.md](product/BUSINESS_RULES.md)	Business constraints, financial rules, operational behavior, and domain requirements.


Recommended reading order
1. Product Requirements Document.
2. MVP Scope.
3. User Flows.
4. Business Rules.
3. Architecture Documentation
Architecture documents describe the system structure, security boundaries, persistence model, and infrastructure abstractions.
Document	Description
[ARCHITECTURE.md](architecture/ARCHITECTURE.md)	Overall system architecture, technology stack, backend modules, and component responsibilities.
[MULTI_TENANCY.md](architecture/MULTI_TENANCY.md)	Tenant context, data ownership, tenant isolation, and cross-tenant protection.
[AUTHENTICATION.md](architecture/AUTHENTICATION.md)	Authentication, JWT lifecycle, sessions, memberships, roles, and permissions.
[DATABASE.md](architecture/DATABASE.md)	Database conventions, implemented entities, relationships, constraints, and migrations.
[STORAGE.md](architecture/STORAGE.md)	File storage abstraction, uploads, downloads, and file security requirements.
[SECURITY.md](architecture/SECURITY.md)	Security requirements, threat considerations, data protection, and production safeguards.


Recommended reading order
1. System Architecture.
2. Multi-Tenancy.
3. Authentication.
4. Database Design.
5. Storage Strategy.
6. Security Requirements.
4. Development Documentation
Development documents define the implementation workflow, quality practices, project milestones, and operational procedures.
Document	Description
[ROADMAP.md](development/ROADMAP.md)	Development milestones, dependencies, deliverables, and implementation progress.
[DEVELOPMENT_GUIDELINES.md](development/DEVELOPMENT_GUIDELINES.md)	Coding standards, project organization, implementation patterns, and Git workflow.
[TESTING.md](development/TESTING.md)	Testing strategy, current test infrastructure, quality requirements, and release criteria.
[DEPLOYMENT.md](development/DEPLOYMENT.md)	Environment configuration, infrastructure, CI/CD, deployment, backups, and recovery.


Recommended reading order
1. Development Roadmap.
2. Development Guidelines.
3. Testing Strategy.
4. Deployment Strategy.
5. Architecture Decision Records
The adr/ directory contains Architecture Decision Records (ADRs).

ADRs capture significant technical decisions and their context, including:
- The problem or context behind a decision.
- The alternatives considered.
- The selected approach and rationale.
- Consequences, limitations, and trade-offs.
- Whether a decision supersedes an earlier ADR.
Create an ADR when a significant architectural decision is made or an existing decision is intentionally changed. See [README.md](adr/README.md) for the process and template.
6. Project Baseline
The following table summarizes the current technical direction. It does not imply that every listed product capability or infrastructure component has already been delivered.
Area	Current baseline
Product model	Multi-tenant SaaS
Initial market	Spain
Intended application languages	Portuguese, Spanish, English
Hosting model	Cloud SaaS target
Initial default currency	EUR
Initial default timezone	Europe/Madrid
Backend	Python + FastAPI
Frontend direction	Next.js + React + TypeScript
UI direction	Tailwind CSS + shadcn/ui
Database	PostgreSQL, shared database and schema
ORM	SQLAlchemy 2.x
Migrations	Alembic
API style	Versioned REST API under /api/v1
Authentication	JWT-based authentication
Authorization	Tenant-scoped RBAC using permission codes
Architecture	Modular monolith
Tenant isolation	Application-level enforcement, tenant-aware ORM session behavior, and composite foreign keys where applicable
File storage	Storage abstraction; local development storage and production object storage are planned
Backend testing	Pytest with a dedicated PostgreSQL test database
Local orchestration	Docker Compose where appropriate


Important architecture status
- PostgreSQL Row-Level Security (RLS) is deferred. Current tenant isolation is enforced at the application/backend level; RLS must not be described as enabled.
- Production object storage, deployment provider, and production infrastructure remain subject to the deployment plan.
- The application is being developed as a modular monolith. Microservices are not part of the initial architecture.
- The backend currently includes authentication/tenant membership/RBAC foundations and the Clients, Events, Products, Product Categories, and Quotes modules. See the Roadmap and the relevant module documentation for precise scope and status.
7. Documentation Standards
7.1 Language
Technical documentation must be written in English to support international collaboration. The application is intended to support Portuguese, Spanish, and English.
7.2 Consistency
Product, architecture, and development documents must remain consistent. When a requirement or implementation decision changes, review all documents affected by that change.
7.3 Versioning and status
Documents should identify their title, project, version, status, and last-updated date where appropriate. Version numbers describe document revisions; they do not indicate implementation completion.

Use explicit status language such as:
- Implemented: delivered in the codebase and supported by relevant tests.
- Partially implemented: only part of the documented capability is delivered.
- Planned: intended but not yet implemented.
- Open decision: requires a decision before implementation or release.
- Deferred: intentionally postponed; do not implement unless the decision is revisited.
7.4 Open decisions and assumptions
Unresolved technical or business decisions must be identified as open. Assumptions must not silently become implementation requirements.
7.5 Updates
Documentation must be reviewed when:
- Requirements or acceptance criteria change.
- A feature is introduced, modified, or deferred.
- An architectural or security decision is approved or changed.
- Business rules change.
- Development or testing standards evolve.
- Deployment or operational procedures change.
Documentation should describe the actual approved system and clearly distinguish it from the intended future design.
8. Implementation Reference
Use the following documents as the starting point when implementing a feature. Consult additional documents whenever the change crosses module, security, data, or operational boundaries.
Implementation area	Primary references
User registration and login	[AUTHENTICATION.md](architecture/AUTHENTICATION.md), [MULTI_TENANCY.md](architecture/MULTI_TENANCY.md)
Tenant configuration	[MULTI_TENANCY.md](architecture/MULTI_TENANCY.md), [BUSINESS_RULES.md](product/BUSINESS_RULES.md)
Clients	[MVP_SCOPE.md](product/MVP_SCOPE.md), [USER_FLOWS.md](product/USER_FLOWS.md), [DATABASE.md](architecture/DATABASE.md)
Products and product categories	[BUSINESS_RULES.md](product/BUSINESS_RULES.md), [DATABASE.md](architecture/DATABASE.md)
Quotes and quote items	[BUSINESS_RULES.md](product/BUSINESS_RULES.md), [USER_FLOWS.md](product/USER_FLOWS.md), [DATABASE.md](architecture/DATABASE.md)
Events	[USER_FLOWS.md](product/USER_FLOWS.md), [BUSINESS_RULES.md](product/BUSINESS_RULES.md), [DATABASE.md](architecture/DATABASE.md)
Workforce	[BUSINESS_RULES.md](product/BUSINESS_RULES.md), [USER_FLOWS.md](product/USER_FLOWS.md)
Payments and expenses	[BUSINESS_RULES.md](product/BUSINESS_RULES.md), [DATABASE.md](architecture/DATABASE.md)
Dashboard and reports	[PRD.md](product/PRD.md), [MVP_SCOPE.md](product/MVP_SCOPE.md)
File uploads and generated documents	[STORAGE.md](architecture/STORAGE.md), [DEPLOYMENT.md](development/DEPLOYMENT.md)
API and backend implementation	[ARCHITECTURE.md](architecture/ARCHITECTURE.md), [DEVELOPMENT_GUIDELINES.md](development/DEVELOPMENT_GUIDELINES.md)
Automated tests	[TESTING.md](development/TESTING.md)
Production release	[SECURITY.md](architecture/SECURITY.md), [DEPLOYMENT.md](development/DEPLOYMENT.md)


9. Documentation Governance
The documentation is the shared reference for product and implementation decisions.
1. Product requirements and acceptance criteria should be clarified before implementing a feature.
2. Business rules must be explicit before related financial or operational logic is implemented.
3. Architectural and security changes must be documented.
4. Significant technical decisions should have an ADR.
5. Tenant isolation and authorization requirements must not be weakened to make implementation or tests pass.
6. Code must not silently contradict an approved decision. If implementation reveals that a decision must change, update the relevant documentation and record the decision where appropriate.
7. Documentation updates should accompany the code changes they describe.
8. Tests must validate critical business rules and security boundaries; documentation alone is not evidence that a feature is implemented.
10. Current Documentation and Implementation Status
The documentation set contains product, architecture, and development specifications. The implementation is progressing incrementally; the presence of a specification does not mean the corresponding module is complete.

The current backend baseline includes:
- Authentication, tenant membership, and permission-based RBAC foundations.
- Tenant-scoped persistence and application-level tenant isolation.
- Clients management.
- Events management and status transitions.
- Products and product categories.
- Quotes and quote items, including optional product catalog links and commercial snapshots.
- Alembic-managed schema migrations.
- A dedicated PostgreSQL test database and automated backend tests.
The following capabilities remain future work or require further implementation before they can be considered delivered: full quotation versioning and approval workflow, conversion of approved quotes into events, PDF generation, payments, workforce management, expenses, reporting, production storage integration, and production deployment. Refer to [ROADMAP.md](development/ROADMAP.md), [MVP_SCOPE.md](product/MVP_SCOPE.md), and [USER_FLOWS.md](product/USER_FLOWS.md) for the current status and dependencies.

The next development work should follow the roadmap and maintain consistency between code, tests, and documentation. A feature should be marked implemented only when its agreed scope is delivered and validated.
11. Guiding Principle
CaterFlow should be developed as a maintainable, secure, and scalable SaaS product. This documentation exists to reduce ambiguity, guide implementation, preserve technical decisions, and support future collaboration. It must evolve alongside the product and accurately distinguish current capabilities from future plans.