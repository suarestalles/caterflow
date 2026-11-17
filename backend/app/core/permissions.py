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
    ROLES_CREATE = "roles.create"
    ROLES_UPDATE = "roles.update"
    ROLES_DELETE = "roles.delete"

    # Role permissions
    ROLES_PERMISSIONS_VIEW = "roles.permissions.view"
    ROLES_PERMISSIONS_MANAGE = "roles.permissions.manage"

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
        PermissionCode.ROLES_CREATE,
        "roles",
        "Create company roles.",
    ),
    PermissionDefinition(
        PermissionCode.ROLES_UPDATE,
        "roles",
        "Update company roles.",
    ),
    PermissionDefinition(
        PermissionCode.ROLES_DELETE,
        "roles",
        "Delete company roles.",
    ),
    # Role permissions
    PermissionDefinition(
        PermissionCode.ROLES_PERMISSIONS_VIEW,
        "roles",
        "View permissions assigned to company roles.",
    ),
    PermissionDefinition(
        PermissionCode.ROLES_PERMISSIONS_MANAGE,
        "roles",
        "Manage permissions assigned to company roles.",
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

DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[PermissionCode]] = {
    "Owner": frozenset(PermissionCode),
    "Admin": frozenset(
        {
            PermissionCode.DASHBOARD_READ,
            PermissionCode.EVENTS_READ,
            PermissionCode.EVENTS_CREATE,
            PermissionCode.EVENTS_UPDATE,
            PermissionCode.EVENTS_CANCEL,
            PermissionCode.QUOTES_READ,
            PermissionCode.QUOTES_CREATE,
            PermissionCode.QUOTES_UPDATE,
            PermissionCode.QUOTES_SEND,
            PermissionCode.CLIENTS_READ,
            PermissionCode.CLIENTS_CREATE,
            PermissionCode.CLIENTS_UPDATE,
            PermissionCode.CLIENTS_ARCHIVE,
            PermissionCode.MENUS_READ,
            PermissionCode.MENUS_CREATE,
            PermissionCode.MENUS_UPDATE,
            PermissionCode.MENUS_ARCHIVE,
            PermissionCode.STAFF_READ,
            PermissionCode.STAFF_CREATE,
            PermissionCode.STAFF_UPDATE,
            PermissionCode.STAFF_ARCHIVE,
            PermissionCode.STAFF_ASSIGN,
            PermissionCode.FINANCE_READ,
            PermissionCode.FINANCE_EXPENSES_MANAGE,
            PermissionCode.FINANCE_PAYMENTS_MANAGE,
            PermissionCode.REPORTS_READ,
            PermissionCode.USERS_READ,
            PermissionCode.USERS_INVITE,
            PermissionCode.USERS_UPDATE,
            PermissionCode.USERS_DEACTIVATE,
            PermissionCode.ROLES_READ,
            PermissionCode.SETTINGS_READ,
        }
    ),
    "Manager": frozenset(
        {
            PermissionCode.DASHBOARD_READ,
            PermissionCode.EVENTS_READ,
            PermissionCode.EVENTS_CREATE,
            PermissionCode.EVENTS_UPDATE,
            PermissionCode.QUOTES_READ,
            PermissionCode.QUOTES_CREATE,
            PermissionCode.QUOTES_UPDATE,
            PermissionCode.QUOTES_SEND,
            PermissionCode.CLIENTS_READ,
            PermissionCode.CLIENTS_CREATE,
            PermissionCode.CLIENTS_UPDATE,
            PermissionCode.MENUS_READ,
            PermissionCode.MENUS_CREATE,
            PermissionCode.MENUS_UPDATE,
            PermissionCode.STAFF_READ,
            PermissionCode.STAFF_CREATE,
            PermissionCode.STAFF_UPDATE,
            PermissionCode.STAFF_ASSIGN,
            PermissionCode.FINANCE_READ,
            PermissionCode.REPORTS_READ,
            PermissionCode.ROLES_READ,
        }
    ),
    "Member": frozenset(
        {
            PermissionCode.DASHBOARD_READ,
            PermissionCode.EVENTS_READ,
            PermissionCode.QUOTES_READ,
            PermissionCode.CLIENTS_READ,
            PermissionCode.MENUS_READ,
            PermissionCode.STAFF_READ,
        }
    ),
}

DEFAULT_ROLE_DESCRIPTIONS: dict[str, str] = {
    "Owner": "Full access to all tenant resources and permissions.",
    "Admin": "Administrative access to daily operations and user management.",
    "Manager": "Access to operational management and reports.",
    "Member": "Limited access to operational information.",
}
