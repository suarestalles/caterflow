from dataclasses import dataclass
from enum import StrEnum


class PermissionCode(StrEnum):
    """Canonical permission codes available in the application."""

    # Dashboard
    DASHBOARD_READ = "dashboard.read"

    # Events
    EVENTS_READ = "events.read"
    EVENTS_CREATE = "events.create"
    EVENTS_UPDATE = "events.update"
    EVENTS_CANCEL = "events.cancel"

    # Quotes
    QUOTES_READ = "quotes.read"
    QUOTES_CREATE = "quotes.create"
    QUOTES_UPDATE = "quotes.update"
    QUOTES_SEND = "quotes.send"

    # Clients
    CLIENTS_READ = "clients.read"
    CLIENTS_CREATE = "clients.create"
    CLIENTS_UPDATE = "clients.update"
    CLIENTS_ARCHIVE = "clients.archive"

    # Menus
    MENUS_READ = "menus.read"
    MENUS_CREATE = "menus.create"
    MENUS_UPDATE = "menus.update"
    MENUS_ARCHIVE = "menus.archive"

    # Staff
    STAFF_READ = "staff.read"
    STAFF_CREATE = "staff.create"
    STAFF_UPDATE = "staff.update"
    STAFF_ARCHIVE = "staff.archive"
    STAFF_ASSIGN = "staff.assign"

    # Finance
    FINANCE_READ = "finance.read"
    FINANCE_EXPENSES_MANAGE = "finance.expenses.manage"
    FINANCE_PAYMENTS_MANAGE = "finance.payments.manage"

    # Reports
    REPORTS_READ = "reports.read"

    # Users
    USERS_READ = "users.read"
    USERS_INVITE = "users.invite"
    USERS_UPDATE = "users.update"
    USERS_DEACTIVATE = "users.deactivate"

    # Roles
    ROLES_READ = "roles.read"
    ROLES_MANAGE = "roles.manage"

    # Settings
    SETTINGS_READ = "settings.read"
    SETTINGS_UPDATE = "settings.update"


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    """Metadata associated with an application permission."""

    code: PermissionCode
    module: str
    description: str


PERMISSION_CATALOG: tuple[PermissionDefinition, ...] = (
    # Dashboard
    PermissionDefinition(
        PermissionCode.DASHBOARD_READ,
        "dashboard",
        "View the company dashboard.",
    ),
    # Events
    PermissionDefinition(
        PermissionCode.EVENTS_READ,
        "events",
        "View company events.",
    ),
    PermissionDefinition(
        PermissionCode.EVENTS_CREATE,
        "events",
        "Create events.",
    ),
    PermissionDefinition(
        PermissionCode.EVENTS_UPDATE,
        "events",
        "Update events.",
    ),
    PermissionDefinition(
        PermissionCode.EVENTS_CANCEL,
        "events",
        "Cancel events.",
    ),
    # Quotes
    PermissionDefinition(
        PermissionCode.QUOTES_READ,
        "quotes",
        "View quotes.",
    ),
    PermissionDefinition(
        PermissionCode.QUOTES_CREATE,
        "quotes",
        "Create quotes.",
    ),
    PermissionDefinition(
        PermissionCode.QUOTES_UPDATE,
        "quotes",
        "Update quotes.",
    ),
    PermissionDefinition(
        PermissionCode.QUOTES_SEND,
        "quotes",
        "Send quotes to clients.",
    ),
    # Clients
    PermissionDefinition(
        PermissionCode.CLIENTS_READ,
        "clients",
        "View clients.",
    ),
    PermissionDefinition(
        PermissionCode.CLIENTS_CREATE,
        "clients",
        "Create clients.",
    ),
    PermissionDefinition(
        PermissionCode.CLIENTS_UPDATE,
        "clients",
        "Update clients.",
    ),
    PermissionDefinition(
        PermissionCode.CLIENTS_ARCHIVE,
        "clients",
        "Archive clients.",
    ),
    # Menus
    PermissionDefinition(
        PermissionCode.MENUS_READ,
        "menus",
        "View menus.",
    ),
    PermissionDefinition(
        PermissionCode.MENUS_CREATE,
        "menus",
        "Create menus.",
    ),
    PermissionDefinition(
        PermissionCode.MENUS_UPDATE,
        "menus",
        "Update menus.",
    ),
    PermissionDefinition(
        PermissionCode.MENUS_ARCHIVE,
        "menus",
        "Archive menus.",
    ),
    # Staff
    PermissionDefinition(
        PermissionCode.STAFF_READ,
        "staff",
        "View staff members.",
    ),
    PermissionDefinition(
        PermissionCode.STAFF_CREATE,
        "staff",
        "Create staff records.",
    ),
    PermissionDefinition(
        PermissionCode.STAFF_UPDATE,
        "staff",
        "Update staff records.",
    ),
    PermissionDefinition(
        PermissionCode.STAFF_ARCHIVE,
        "staff",
        "Archive staff records.",
    ),
    PermissionDefinition(
        PermissionCode.STAFF_ASSIGN,
        "staff",
        "Assign staff members to events.",
    ),
    # Finance
    PermissionDefinition(
        PermissionCode.FINANCE_READ,
        "finance",
        "View financial information.",
    ),
    PermissionDefinition(
        PermissionCode.FINANCE_EXPENSES_MANAGE,
        "finance",
        "Manage company expenses.",
    ),
    PermissionDefinition(
        PermissionCode.FINANCE_PAYMENTS_MANAGE,
        "finance",
        "Manage event payments.",
    ),
    # Reports
    PermissionDefinition(
        PermissionCode.REPORTS_READ,
        "reports",
        "View company reports.",
    ),
    # Users
    PermissionDefinition(
        PermissionCode.USERS_READ,
        "users",
        "View company users.",
    ),
    PermissionDefinition(
        PermissionCode.USERS_INVITE,
        "users",
        "Invite users to the company.",
    ),
    PermissionDefinition(
        PermissionCode.USERS_UPDATE,
        "users",
        "Update company user information.",
    ),
    PermissionDefinition(
        PermissionCode.USERS_DEACTIVATE,
        "users",
        "Deactivate company users.",
    ),
    # Roles
    PermissionDefinition(
        PermissionCode.ROLES_READ,
        "roles",
        "View company roles.",
    ),
    PermissionDefinition(
        PermissionCode.ROLES_MANAGE,
        "roles",
        "Create, update and manage company roles.",
    ),
    # Settings
    PermissionDefinition(
        PermissionCode.SETTINGS_READ,
        "settings",
        "View company settings.",
    ),
    PermissionDefinition(
        PermissionCode.SETTINGS_UPDATE,
        "settings",
        "Update company settings.",
    ),
)


PERMISSION_BY_CODE: dict[PermissionCode, PermissionDefinition] = {
    permission.code: permission for permission in PERMISSION_CATALOG
}
