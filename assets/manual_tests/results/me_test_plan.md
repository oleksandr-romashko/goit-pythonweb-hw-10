# 🧪 CURRENT USER (`/users/me`) TEST PLAN — FastAPI Contacts App

**Goal:** Manual verification of current user retrieval & self-service operations: profile info, password update, avatar management.
**Scope:** `api/users/me` endpoints (GET, PATCH), role-based responses, validation, partial updates.  
**Version:** 1 for Stage 3 — Current User / About Me  
**Date:** 2025-12-08 
**Tester:** Oleksandr Romashko
**Testing Environment:** OS: Ubuntu 24.04.3 LTS, Browser: Firefox Browser 145.0.2 (64-bit)

---

## ✅ CHECKLIST OVERVIEW
- [x] Show current user profile
- [x] Role-based response differences (Admin view vs regular user view)
- [x] Contacts count included
- [x] Password update
- [x] Avatar update
- [x] Cloud upload error handling
- [x] Avatar reset
- [x] Rate limiter
- [x] Edge cases - Deleted / inactive user behavior
- [x] End-to-end integration

---

## 🔹 1. Show Current User (`GET /users/me`)

**Goal:** Verify retrieval of user info based on JWT access token.

| #  | Description             | Input             | Expected Result               | Status |
| -- | ----------------------- | ----------------- | ----------------------------- | ------ |
| 1  | Not authenticated user / Missing token  | `GET` request     | ❌ 401 Unauthorized `"Not authenticated"` | ✅ Passed      |
| 2  | Active regular user (USER role)   | `GET` request | ✅ 200 returns fields: id, username, email, avatar, contacts_count, is_email_confirmed, no role field      | ✅ Passed      |
| 3  | Active moderator user (MODERATOR role)   | `GET` request | ✅ 200 returns fields: id, username, email, avatar, contacts_count, is_email_confirmed, incl. role field      | ✅ Passed      |
| 4  | Active admin user (ADMIN role)   | `GET` request | ✅ 200 returns fields: id, username, email, avatar, contacts_count, is_email_confirmed, incl. role field      | ✅ Passed      |
| 5  | Superadmin user (SUPERADMIN role)   | `GET` request | ✅ 200 returns fields: id, username, email, avatar, contacts_count, is_email_confirmed, incl. role field      | ✅ Passed      |
| 6  | Inactive user   | `GET` request | ❌ 403 Forbidden `"Inactive user"`      | ✅ Passed      |
| 7  | Deleted user (previously logged in and deleted meanwhile) / invalid token   | `GET` request | ❌ 401 Unauthorized `"Invalid authentication credentials"`      | ✅ Passed      |

> **Notes:**  
> - Contacts count is always included.  
> - Role is shown for moderator, admin and superadmin user.
> - Timestamps are sanitized for all users.

---

## 🔹 2. Update Current User Password (`PATCH /users/me/password`)

**Goal:** Verify partial updates of current user info with validations.

| #   | Description    | Input         | Expected Result  | Status   |
| --- | -------------- | ------------- | ---------------- | -------- |
| 1   | Update password (with correct current password) | `PATCH` `/api/users/me/password` `{ "current_password": "OldPass123!", "password": "NewPass123!" }` | ✅ 200 `"Password updated successfully"` | ✅ Passed |
| 2   | Update password with incorrect current password | `PATCH` `/api/users/me/password` `{ "current_password": "IncorrectPass123!", "password": "NewPass123!" }` | ❌ 403 Forbidden `"Invalid user credentials: Incorrect current password"` | ✅ Passed |
| 3   | Weak new password | `PATCH` `/api/users/me/password` `{ "current_password": "OldPass123!", "password": "123" }` | ❌ 422 Unprocessable Entity with explaining message | ✅ Passed |
| 4   | Update password without current_password | `PATCH` `/api/users/me/password` `{ "password": "NewPass123!" }` | ❌ 400 Bad Request `{ "errors": { "current_password": "This field is required."}, "message": "Invalid request data." }`, do not expose any password values back to user in error message | ✅ Passed |
| 5   | Empty body | `PATCH` `/api/users/me/password` `{}` | ❌ 400 Bad Request `{ "errors": { "current_password": "This field is required."}, "message": "Invalid request data." }`, do not expose any password values back to user in error message | ✅ Passed |
| 6   | Extra unexpected field | `PATCH` `/api/users/me/password` `{ "current_password": "CurrentPass123!", "password": "NewPass123!", "extra": "field" }` | ❌ 422 Unprocessable Entity `"Extra inputs are not permitted"` | ✅ Passed |
| 7   | Not authenticated user / Missing token | `PATCH` `/api/users/me/password` | ❌ 401 Unauthorized `"Not authenticated"` | ✅ Passed |
| 8   | Update password for inactive user | `PATCH` `/api/users/me/password` `{ "current_password": "CurrentPass123!", "password": "NewPass123!" }` | ❌ 403 Forbidden `"Inactive user"` | ✅ Passed |


## 🔹 3. Update Current User Avatar (`PATCH /users/me/avatar`)

**Goal:** Verify partial updates of current user info with validations.

| #   | Description    | Input         | Expected Result  | Status   |
| --- | -------------- | ------------- | ---------------- | -------- |
| 1 | Update avatar with valid file | `PATCH /api/users/me/avatar` with valid image (`.jpg/.png/.webp`, size < max) | ✅ 200 OK, `{ "avatar": "<NEW_CLOUDINARY_AVATAR_URL>" }`, file uploaded and publicly accessible, file replaces existing one if there is an avatar associated with user in the cloud | ✅ Passed |
| 2 | No file provided | `PATCH /api/users/me/avatar` without `file` form field | ❌ 422 Unprocessable Entity (FastAPI validation error) | ✅ Passed |
| 3 | Unsupported file MIME type | `PATCH /api/users/me/avatar` with file `assets/manual_tests/test_files/wrong_mime_type.odt` | ❌ 415 Unsupported Media Type | ✅ Passed |
| 4 | Unsupported file extension | `PATCH /api/users/me/avatar` with file `assets/manual_tests/test_files/wrong_extension.bmp` | ❌ 400 Bad Request, `"Unsupported file type"` | ⚠️ Passed* |
| 5 | Empty file (0 bytes) | `PATCH /api/users/me/avatar` with empty file (e.g. `assets/manual_tests/test_files/empty.jpg`) | ❌ 400 Bad Request, `"Uploaded file is empty"` | ✅ Passed |
| 6 | File too large | `PATCH /api/users/me/avatar` with file size > `AVATAR_MAX_FILE_SIZE` (e.g. `assets/manual_tests/test_files/big.jpg`) | ❌ 413 Payload Too Large | ✅ Passed |
| 7 | Auth token missing | `PATCH /api/users/me/avatar` without `Authorization` header | ❌ 401 Unauthorized | ✅ Passed |
| 8 | Inactive user | `PATCH /api/users/me/avatar` as inactive user | ❌ 403 Forbidden `"Inactive user"` | ✅ Passed |
| 9 | Cloud provider upload failure (faked valid file type) | Valid faked file type but Cloudinary returns error (e.g. `assets/manual_tests/test_files/fake.jpg`) | ❌ 400 Bad Request `"Failed to upload avatar"` | ✅ Passed |
| 10 | Cloud provider upload failure (any other Cloudinary error) | Cloudinary returns error | ❌ 400 Bad Request `"Failed to upload avatar"` | ✅ Passed |

> **Notes:**  
> - ⚠️ Unsupported file extension wasn't able to test without turning off mime test check. Hard to reproduce scenario when mime test passed and extension test failed.
> - Change of user email change is not implemented yet and will be done in a separate flow
> - Avatar has not check for minimum size as small files are allowed.

---


## 🔹 4. Reset Current User Avatar (`PATCH /users/me/avatar/reset`)

**Goal:** Verify partial updates of current user info with validations.

| #   | Description    | Input         | Expected Result  | Status   |
| --- | -------------- | ------------- | ---------------- | -------- |
| 1   | Reset user avatar from avatar uploaded to a cloud | `PATCH /api/users/me/avatar/reset` | ✅ 200 OK, new avatar assigned to Gravatar, avatar image in the cloud is removed | ✅ Passed  |
| 2   | Reset user avatar that is Gravatar avatar already | `PATCH /api/users/me/avatar/reset` | ✅ 200 OK, no changes if Gravatar is the same, no cloud deletion request | ✅ Passed  |
| 3   | Gravatar service provider is unavailable or has error | `PATCH /api/users/me/avatar/reset` | ✅ 200 OK, avatar assigned with `null`, no cloud deletion request | ✅ Passed*  |

> **Notes:**  
> - *Gravatar is unavailable - synthetic test case to check Gravatar error handling as Gravatar is an external service/dependency.

---

## 🔹 5. /me Rate Limit Testing (`GET /users/me`)

**Goal:** Ensure correct rate limiting behavior and proper retry flow.


| #   | Description    | Input         | Expected Result  | Status   |
| --- | -------------- | ------------- | ---------------- | -------- |
| 1 | Burst requests within limit | `GET /api/users/me` ≤ limit requests | ✅ 200 OK for all requests | ✅ Passed |
| 2 | Exceed limit | `GET /api/users/me` limit+1 requests | ❌ 429 Too Many Requests `"Too Many Requests"` | ✅ Passed |
| 3 | Retry after cooldown | `GET /api/users/me` wait X seconds | ✅ 200 OK | ✅ Passed |
| 4 | Rate limit is per user (each user has independent counters) | `GET /api/users/me` two user access tokens | ✅ 200 OK | ✅ Passed |

---

## 🔹 6. End-to-End Flow

**Scenario ""happy path":** ✅ Passed
1. Login as a valid user → obtain access token  
2. GET `/users/me` → verify correct schema and sanitized fields for USER or full fields for ADMIN  
3. PATCH `/users/me/password` → update password  
4. PATCH `/users/me/avatar` → update password/avatar  
5. GET `/users/me` → verify updated values reflected  

---

📋 **Notes & Observations**
> - Contacts count must always be present when getting current user info
> - Non-admin users should never see role/timestamps or other technical information  
> - Ensure proper 401 responses for inactive or deleted users
