"""
Shared constants for error messages and other reusable values.
"""

# Auth
AUTH_PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?"

# Error messages
MESSAGE_ERROR_DB_CONNECTION_ERROR = "Error connecting to the database"
MESSAGE_ERROR_DB_INVALID_CONFIG = "Database is not configured correctly"

MESSAGE_ERROR_INVALID_LOGIN_CREDENTIALS = "Invalid username or password"
MESSAGE_ERROR_NOT_AUTHENTICATED = "Not authenticated"
MESSAGE_ERROR_INVALID_AUTH_TOKEN = "Invalid or missing JWT token"
MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS = "Invalid authentication credentials"
MESSAGE_ERROR_INACTIVE_USER = "Inactive user"
MESSAGE_ERROR_UNAUTHORIZED = "Unauthorized"
MESSAGE_ERROR_FORBIDDEN = "Forbidden"
MESSAGE_ERROR_ACCESS_DENIED = "Access denied"

MESSAGE_ERROR_NOT_FOUND = "Not found"
MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS = "Resource already exists"
MESSAGE_ERROR_INTERNAL_SERVER_ERROR = "Internal server error"

MESSAGE_ERROR_USERNAME_IS_RESERVED = "This username is reserved and cannot be used."

MESSAGE_ERROR_CONTACT_NOT_FOUND = "Contact not found"
