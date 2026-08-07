from __future__ import annotations

from enum import StrEnum


class ApiErrorCode(StrEnum):
    database_not_configured = "database_not_configured"
    not_authenticated = "not_authenticated"
    invalid_or_expired_token = "invalid_or_expired_token"
    invalid_token = "invalid_token"
    user_not_found = "user_not_found"
    account_not_active = "account_not_active"
    auth_not_configured = "auth_not_configured"
    invalid_application_state = "invalid_application_state"
