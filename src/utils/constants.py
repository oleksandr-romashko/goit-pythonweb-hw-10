"""
Shared constants for error messages and other reusable values.
"""

# ==============
# Regex patterns
# ==============

AUTH_PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?"

# ==============
# Success messages
# ==============

MESSAGE_SUCCESS_CONFIRMATION_EMAIL_SENT = (
    "Please check your email for the confirmation letter"
)
MESSAGE_SUCCESS_EMAIL_VERIFIED = "Email verified successfully"
MESSAGE_SUCCESS_PASSWORD_UPDATED = "Password updated successfully"

# ==============
# Error messages
# ==============

# Template error messages

MESSAGE_ERROR_UNSUPPORTED_X_ERROR_TEMPLATE = (
    "Unsupported {subject}: {provided}. Allowed {subject}: {supported}."
)
MESSAGE_ERROR_FILE_TOO_LARGE_ERROR_TEMPLATE = (
    "File is too large: {size} bytes. Maximum allowed is {max_allowed_size} bytes."
)
MESSAGE_ERROR_FAILED_TO_UPLOAD_FILE_ERROR_TEMPLATE = "Failed to upload {file_type}"

# Static error messages

MESSAGE_ERROR_DB_CONNECTION_ERROR = "Error connecting to the database"
MESSAGE_ERROR_DB_INVALID_CONFIG = "Database is not configured correctly"

MESSAGE_ERROR_INVALID_LOGIN_CREDENTIALS = "Invalid username or password"
MESSAGE_ERROR_NOT_AUTHENTICATED = "Not authenticated"
MESSAGE_ERROR_INVALID_OR_EXPIRED_AUTH_TOKEN = "Invalid or expired token"
MESSAGE_ERROR_INVALID_OR_EXPIRED_ACCESS_TOKEN = "Invalid or expired access token"
MESSAGE_ERROR_INVALID_OR_EXPIRED_REFRESH_TOKEN = "Invalid or expired refresh token"
MESSAGE_ERROR_INVALID_OR_EXPIRED_MAIL_TOKEN = "Invalid or expired mail token"
MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS = "Invalid authentication credentials"
MESSAGE_ERROR_INACTIVE_USER = "Inactive user"
MESSAGE_ERROR_UNAUTHORIZED = "Unauthorized"
MESSAGE_ERROR_FORBIDDEN = "Forbidden"
MESSAGE_ERROR_ACCESS_DENIED = "Access denied"
MESSAGE_ERROR_NOT_AUTHORIZED = "You are not authorized to perform this action"
MESSAGE_ERROR_ADMIN_CANNOT_CREATE_ADMIN = (
    "Admin is not allowed to create other admin user"
)

MESSAGE_ERROR_BAD_REQUEST = "Bad request"
MESSAGE_ERROR_BAD_REQUEST_EMPTY = "Request can't be empty"
MESSAGE_ERROR_BAD_REQUEST_NO_TOKEN = "Bad request: Missing token parameter"
MESSAGE_ERROR_NOT_FOUND = "Not found"
MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS = "Resource already exists"
MESSAGE_ERROR_PAYLOAD_TOO_LARGE = "Payload Too Large"
MESSAGE_ERROR_UNSUPPORTED_MEDIA_TYPE = "Unsupported Media Type"
MESSAGE_ERROR_TOO_MANY_REQUESTS = "Too Many Requests"
MESSAGE_ERROR_INTERNAL_SERVER_ERROR = "Internal server error"
MESSAGE_ERROR_SERVER_ERROR_NOT_IMPLEMENTED = "Not implemented yet"

MESSAGE_ERROR_FEATURE_IS_PLANNED = "Feature is planned for the implementation"

MESSAGE_ERROR_USERNAME_IS_RESERVED = "This username is reserved and cannot be used"

MESSAGE_ERROR_CONTACT_NOT_FOUND = "Contact not found"

MESSAGE_ERROR_EMAIL_CHANGE_IS_FORBIDDEN = "Email change is forbidden."
MESSAGE_ERROR_USER_ROLE_IS_INVALID = "Invalid or not supported user role"
MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS = "Not authorized to perform this action"
MESSAGE_ERROR_EMAIL_VERIFICATION_REQUIRED = "Email verification is required"
MESSAGE_ERROR_USER_EMAIL_IS_ALREADY_VERIFIED = "Your email is already verified."
MESSAGE_ERROR_USER_NOT_FOUND = "User not found"
MESSAGE_ERROR_USER_VIEW_IS_RESTRICTED = "User view is restricted"
MESSAGE_ERROR_USER_DELETION_IS_RESTRICTED = "User deletion is restricted"
MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED = (
    "User does not exist or you are not allowed to perform this action with this user"
)

MESSAGE_ERROR_EMPTY_UPLOAD_FILE = "Uploaded file is empty"
MESSAGE_ERROR_CLOUD_UPLOAD_ERROR = "Failed to upload file to the cloud"
MESSAGE_ERROR_CLOUD_DELETE_ERROR = "Failed to delete file in the cloud"

# ==============
# Default ENV variables values
# ==============

DEFAULT_AUTH_JWT_SECRET = "your_auth_jwt_secret_here"
DEFAULT_CACHE_PASSWORD = "your_cache_password_here"
DEFAULT_DB_ADMIN_USER_PASSWORD = "your_db_admin_user_password_here"
DEFAULT_DB_APP_USER_PASSWORD = "your_db_app_user_password_here"
DEFAULT_DB_ADMIN_PANEL_ACCESS_EMAIL = "pgadmin@local.dev"
DEFAULT_DB_ADMIN_PANEL_PASSWORD = "your_pgadmin_user_secret_password_here"
DEFAULT_SUPERADMIN_EMAIL = "superadmin@example.com"
DEFAULT_SUPERADMIN_PASSWORD = "your_superadmin_secret_password"
DEFAULT_MAIL_USERNAME = "example@meta.ua"
DEFAULT_MAIL_JWT_SECRET = "your_mail_jwt_secret_here"
DEFAULT_MAIL_PASSWORD = "your_mail_secret_password"
DEFAULT_MAIL_FROM = "example@meta.ua"
DEFAULT_CLOUDINARY_NAME = "your_cloud_name"
DEFAULT_CLOUDINARY_API_KEY = "your_cloudinary_api_key"
DEFAULT_CLOUDINARY_API_SECRET = "your_api_cloudinary_api_secret"
DEFAULT_SALT_USER = "your_user_identifier_salt"
DEFAULT_SALT_AVATAR = "your_avatar_identifier_salt"

# ==============
# Log templates
# ==============

LOG_CONTACT_TEMPLATE = "[%s] user_id=%s contact_id=%s"
