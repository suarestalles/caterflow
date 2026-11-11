# CaterFlow — Product Requirements Document (PRD)

**Version:** 0.1  
**Status:** Initial Draft  
**Product type:** Multi-tenant SaaS  
**Architecture:** Modular Monolith

## 1. Product Overview

CaterFlow is a multi-tenant SaaS platform designed to centralize the commercial, operational, and financial management of catering companies.

The platform aims to replace fragmented workflows involving messaging applications, spreadsheets, paper notes, and disconnected tools with a unified management system.

Each catering company can configure its own identity, users, permissions, services, menus, pricing rules, and operational settings.

## 2. Problem Statement

Many catering businesses manage their operations through disconnected processes, making it difficult to:

- Organize customer information and event requests.
- Create, revise, and track commercial proposals.
- Coordinate employees and event assignments.
- Monitor payments and outstanding balances.
- Record actual event expenses.
- Evaluate the financial performance of individual events.

CaterFlow addresses these challenges through a centralized and configurable platform.

## 3. Product Vision

Provide catering businesses with an accessible and reliable management platform that simplifies their daily operations, improves financial visibility, and supports business growth.

## 4. Target Users

- Small and medium-sized catering companies.
- Catering business owners and administrators.
- Commercial and operational managers.
- Chefs and kitchen coordinators.
- Event staff.

## 5. Product Objectives

1. Centralize customer and event information.
2. Standardize quotation and proposal management.
3. Improve event planning and employee coordination.
4. Track payment schedules and outstanding balances.
5. Record actual event expenses.
6. Provide financial indicators for business decisions.
7. Support multiple companies through a single SaaS platform.

## 6. User Roles

Initial role concepts:

| Role | Main responsibilities |
|---|---|
| Owner | Full company administration |
| Administrator | Manage company settings and users |
| Manager | Manage clients, quotes, events and finances |
| Chef | Access menus and operational event information |
| Staff | Access assigned event information |

The final permission matrix will be defined in a separate document.

## 7. Functional Requirements

### 7.1 Company Management

- Register and configure catering companies.
- Customize company name, logo, contact information, address and tax identification details.
- Configure company-specific settings.
- Manage users and permissions.

### 7.2 Customer Management

- Register and edit customers.
- Store contact information.
- Maintain customer history.
- Associate quotations and events with customers.

### 7.3 Catalog Management

- Register dishes and beverages.
- Organize catalog items into categories.
- Create menu packages.
- Maintain optional recipe and technical information for dishes.

Ingredient-level costing and inventory management are outside the initial MVP scope.

### 7.4 Pricing Management

- Configure pricing rules.
- Support different event types and service formats.
- Allow different menu and pricing proposals.
- Preserve the commercial values used in each approved quotation.

### 7.5 Quotation Management

- Create quotations associated with customers.
- Configure event details, guest count, menu, services and pricing.
- Generate PDF proposals.
- Maintain quotation versions.
- Record customer approval.
- Convert approved quotations into events.

Changes to an existing proposal must generate a new version without silently modifying previously approved information.

### 7.6 Event Management

- Create events from approved quotations.
- Manage event dates, locations and operational information.
- Track event status.
- Assign employees to events.
- Record planned and actual working hours.
- Maintain event history.

### 7.7 Payment Management

- Configure payment schedules.
- Define installment percentages and due dates.
- Track amounts due, paid and outstanding.
- Preserve payment conditions associated with approved quotations and events.

Integrated payment processing is outside the MVP.

### 7.8 Expense Management

- Record actual event expenses.
- Categorize expenses, such as:
  - Food and ingredients.
  - Beverages.
  - Staff.
  - Transportation.
  - Other expenses.
- Store descriptions, amounts, dates and responsible users.
- Compare estimated and actual financial results when sufficient information is available.

The MVP does not require individual ingredient costs.

### 7.9 Dashboard and Reports

Provide an overview of relevant business indicators, including:

- Number of events.
- Upcoming events.
- Quotation status.
- Revenue and outstanding payments.
- Recorded event expenses.
- Estimated versus actual event performance.

### 7.10 Audit History

Record relevant changes to important business information, including quotations, events, payments and expenses.

## 8. Non-Functional Requirements

### Security

- JWT-based authentication.
- Role-based access control.
-