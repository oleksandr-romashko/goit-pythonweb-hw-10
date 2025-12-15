# 🧪 USERS TEST PLAN — FastAPI Contacts App

**Goal:** Manual verification of Users CRUD operations, role-based access control, and validation logic.  
**Scope:** `api/users/*` routes, role enforcement, password/email validation, Gravatar fallback.  
**Version:** 1 for Stage 4 — Users Management  
**Date:** 2025-12-13  
**Tester:** Oleksandr Romashko
**Testing Environment:** OS: Ubuntu 24.04.3 LTS, Browser: Firefox Browser 145.0.2 (64-bit)

---

## ✅ CHECKLIST OVERVIEW
- [x] Create user
- [x] Get all users
- [x] Get user by ID
- [x] Update other users
- [x] Delete user
- [x] Role-based access control
- [x] Gravatar fallback verification
- [ ] Security / logging checks

---

## 🔹 1. Create User (`POST /users/`)

**Goal:** Verify user creation and role-based restrictions.

| #  | Description                        | Input / Role              | Expected Result                | Status    |
| -- | ---------------------------------- | ------------------------- | ------------------------------ | --------- |
| 1  | SUPERADMIN creates USER            | role=`USER`               | ✅ 201 Created                 | ✅ Passed |
| 2  | SUPERADMIN creates MODERATOR       | role=`MODERATOR`          | ✅ 201 Created                 | ✅ Passed |
| 3  | SUPERADMIN creates ADMIN           | role=`ADMIN`              | ✅ 201 Created                 | ✅ Passed |
| 4  | SUPERADMIN creates SUPERADMIN      | role=`SUPERADMIN`         | ❌ 403 Forbidden               | ✅ Passed |
| 5  | ADMIN creates USER                 | role=`USER`               | ✅ 201 Created                 | ✅ Passed |
| 7  | ADMIN creates MODERATOR            | role=`MODERATOR`          | ✅ 201 Created                 | ✅ Passed |
| 7  | ADMIN creates ADMIN                | role=`ADMIN`              | ❌ 403 Forbidden               | ✅ Passed |
| 8  | ADMIN creates SUPERADMIN           | role=`SUPERADMIN`         | ❌ 403 Forbidden               | ✅ Passed |
| 9  | USER tries to create any user      | any role                  | ❌ 403 Forbidden               | ✅ Passed |
| 10 | MODERATOR tries to create any user | any role                  | ❌ 403 Forbidden               | ✅ Passed |
| 11 | Missing email/password             | SUPERADMIN                | ❌ 422 Validation Error        | ✅ Passed |
| 12 | Create inactive user               | SUPERADMIN                | ✅ 201 Created                 | ✅ Passed |
| 13 | Duplicate username/email           | SUPERADMIN                | ❌ 409 Conflict                | ✅ Passed |
| 14 | Restricted username                | SUPERADMIN, ADMIN         | ✅ 201 Created                 | ✅ Passed |
| 15 | Avatar fallback                    | email provided, no avatar | ✅ Avatar URL set via Gravatar | ✅ Passed |

---

## 🔹 2. Get All Users (`GET /users/`)

**Goal:** Verify users listing, filters, pagination, and role-based visibility.

| # | Description                       | Role / Filters                | Expected Result                                                   | Status    |
| - | --------------------------------- | ----------------------------- | ----------------------------------------------------------------- | --------- |
| 1 | SUPERADMIN sees all users         | none                          | ✅ Full list (except SUPERADMINs) with contact counts             | ✅ Passed |
| 2 | SUPERADMIN filters users          | by username/email/role/active | ✅ List filtered correctly                                        | ✅ Passed |
| 3 | ADMIN sees ADMINs (partially), MODERATORs, USERs | none           | ✅ Users visible, contact counts hidden for other admins          | ✅ Passed |
| 4 | MODERATOR tries to list users     | any                           | ❌ 403 Forbidden                                                  | ✅ Passed |
| 5 | USER tries to list users          | any                           | ❌ 403 Forbidden                                                  | ✅ Passed |
| 6 | Any user see full self-info       | any                           | ✅ Full list with contact counts (SUPERADMINs still filtered out) | ✅ Passed |
| 7 | Pagination                        | skip/limit                    | ✅ Pagination respected                                           | ✅ Passed |
| 8 | Sort results by role then by name | any                           | ✅ List shown correctly                                           | ✅ Passed |
| 9 | Show inactive users at the end    | any                           | ✅ List filtered correctly (unsorted or at the end of role group) | ✅ Passed |

---

## 🔹 3. Get User by ID (`GET /users/{id}`)

**Goal:** Verify single user retrieval and role-based restrictions.

| # | Description                             | Role / Target            | Expected Result                     | Status    |
| - | --------------------------------------- | -------------------------| ----------------------------------- | ----------|
| 1 | SUPERADMIN gets any non-SUPERADMIN user | any non-SUPERADMIN       | ✅ Full user data                   | ✅ Passed |
| 2 | ADMIN gets other MODERATOR, USER        | target: MODERATOR, USER  | ✅ Full data                        | ✅ Passed |
| 3 | ADMIN gets another ADMIN                | target: ADMIN            | ✅ Partial data (no contacts count) | ✅ Passed |
| 4 | MODERATOR tries any                     | any                      | ❌ 403 Forbidden                    | ✅ Passed |
| 5 | USER tries any                          | any                      | ❌ 403 Forbidden                    | ✅ Passed |
| 6 | Any user gets other SUPERADMIN          | target: other SUPERADMIN | ❌ 404 Not Found                    | ✅ Passed |
| 7 | Non-existent user                       | any                      | ❌ 404 Not Found                    | ✅ Passed |

---

## 🔹 4. Update Current User (`PATCH /users/{id}` self)

**Goal:** Verify restricted self-update using `users` endpoint.

| # | Description                          | Role / Payload | Expected Result                                  | Status    |
| - | ------------------------------------ | -------------- | ------------------------------------------------ | --------- |
| 1 | Change current user                  | any            | ❌ 403 Forbidden                                 | ✅ Passed |

---

## 🔹 5. Update Another User (`PATCH /users/{id}` other)

**Goal:** Verify admin/superadmin updates other users with restrictions.

| #  | Description                         | Role / Target  | Expected Result  | Status    |
| -- | ----------------------------------- | -------------- | ---------------- | --------- |
| 1  | SUPERADMIN updates USER             | any            | ✅ Success       | ✅ Passed |
| 2  | SUPERADMIN updates MODERATOR        | any            | ✅ Success       | ✅ Passed |
| 3  | SUPERADMIN updates ADMIN            | any            | ✅ Success       | ✅ Passed |
| 4  | SUPERADMIN updates other SUPERADMIN | any            | ❌ 403 Forbidden | ✅ Passed |
| 5  | Any updates SUPERADMIN              | any            | ❌ 403 Forbidden | ✅ Passed |
| 6  | ADMIN updates USER                  | allowed fields | ✅ Success       | ✅ Passed |
| 7  | ADMIN updates MODERATOR             | allowed fields | ✅ Success       | ✅ Passed |
| 8  | ADMIN updates other ADMIN           | any            | ❌ 403 Forbidden | ✅ Passed |
| 9  | MODERATOR updates any               | any            | ❌ 403 Forbidden | ✅ Passed |
| 10 | USER updates any                    | any            | ❌ 403 Forbidden | ✅ Passed |

---

## 🔹 6. Delete User (`DELETE /users/{id}`)

**Goal:** Verify deletion rules and role restrictions.

| #  | Description                         | Role / Target  | Expected Result  | Status    |
| -- | ----------------------------------- | -------------- | ---------------- | --------- |
| 1  | SUPERADMIN deletes USER             | any            | ✅ Success       | ✅ Passed |
| 2  | SUPERADMIN deletes MODERATOR        | any            | ✅ Success       | ✅ Passed |
| 3  | SUPERADMIN deletes ADMIN            | any            | ✅ Success       | ✅ Passed |
| 4  | SUPERADMIN deletes SUPERADMIN       | any            | ❌ 403 Forbidden | ✅ Passed |
| 5  | SUPERADMIN deletes self             | self           | ❌ 403 Forbidden | ✅ Passed |
| 6  | ADMIN deletes USER                  | allowed target | ✅ Success       | ✅ Passed |
| 7  | ADMIN deletes MODERATOR             | allowed target | ✅ Success       | ✅ Passed |
| 8  | ADMIN deletes ADMIN                 | any            | ❌ 403 Forbidden | ✅ Passed |
| 9  | ADMIN deletes self                  | any            | ❌ 403 Forbidden | ✅ Passed |
| 10 | MODERATOR deletes any               | any            | ❌ 403 Forbidden | ✅ Passed |
| 11 | USER deletes any                    | any            | ❌ 403 Forbidden | ✅ Passed |
| 12 | Non-existent user                   | any            | ❌ 404 Not Found | ✅ Passed |
| 13 | When deleting user, remove avatar   | any            | ✅ Success       | ✅ Passed |
| 13 | When deleting user, remove contacts | any            | ✅ Success       | ✅ Passed |

---

## 🔹 7. Role-Based Access Control

**Goal:** Verify enforcement for `USER`, `MODERATOR`, `ADMIN`, `SUPERADMIN`.

| #  | Scenario                              | Role       | Expected Result  | Status            |
| -- | ------------------------------------- | ---------- | ---------------- | ----------------- |
| 1  | Active USER → `/users/me`             | USER       | ✅ 200 OK        | ✅ Passed         |
| 2  | Inactive USER → `/users/me`           | USER       | ❌ 403 Forbidden | ✅ Passed         |
| 3  | USER accessing moderator route        | USER       | ❌ 403 Forbidden | ⏳ Pending*       |
| 4  | USER accessing admin route            | USER       | ❌ 403 Forbidden | ✅ Passed         |
| 5  | USER accessing superadmin route       | USER       | ❌ 403 Forbidden | ⏳ Pending**      |
| 6  | MODERATOR accessing admin route       | MODERATOR  | ❌ 403 Forbidden | ✅ Passed         |
| 7  | MODERATOR accessing superadmin route  | MODERATOR  | ❌ 403 Forbidden | ⏳ Pending***     |
| 8  | ADMIN accessing moderator route       | ADMIN      | ✅ 200 OK        | ⏳ Pending****    |
| 9  | ADMIN accessing admin route           | ADMIN      | ✅ 200 OK        | ✅ Passed         |
| 10 | ADMIN accessing superadmin route      | ADMIN      | ❌ 403 Forbidden | ⏳ Pending*****   |
| 11 | SUPERADMIN accessing moderator route  | SUPERADMIN | ✅ 200 OK        | ⏳ Pending******  |
| 12 | SUPERADMIN accessing admin route      | SUPERADMIN | ✅ 200 OK        | ✅ Passed         |
| 13 | SUPERADMIN accessing superadmin route | SUPERADMIN | ✅ 200 OK        | ⏳ Pending******* |

> **Notes:**  
> - *"USER accessing moderator route" - no such endpoint yet.
> - **"USER accessing superadmin route" - no such endpoint yet.
> - ***"MODERATOR accessing superadmin route" - no such endpoint yet.
> - ****"ADMIN accessing moderator route" - no such endpoint yet.
> - *****"ADMIN accessing superadmin route" - no such endpoint yet.
> - *****"ADMIN accessing superadmin route" - no such endpoint yet.
> - ******"SUPERADMIN accessing moderator route" - no such endpoint yet.
> - *******"SUPERADMIN accessing superadmin route" - no such endpoint yet.

---

## 🔹 8. Gravatar Fallback

| # | Scenario                  | Input / Role | Expected Result                      | Status |
| - | ------------------------- | ------------ | ------------------------------------ | ------ |
| 1 | Email provided, no avatar | any          | ✅ Avatar URL generated via Gravatar | ✅ Passed      |
| 2 | Invalid email             | any          | ✅ Avatar remains None, no exception | ⏳ Pending      |
| 3 | Service unavailable       | any          | ✅ Avatar remains None, no exception | ⏳ Pending      |

---

## 🔹 9. Security / Logging

- Passwords are never logged (masked `<hidden>`).  
- Deactivated users cannot access protected endpoints but may login.  
- Role escalation attempts are rejected.  
- Deletion and update actions are logged properly.  

---

## 🔹 10. End-to-End "Happy Path"

1. SUPERADMIN creates USER  
2. USER logs in and accesses `/users/me`  
3. USER updates own avatar/email  
4. ADMIN updates a USER (allowed fields)  
5. SUPERADMIN deletes a USER  
6. All actions comply with RBAC and logs are generated  

---

## 🔹 11. Advanced Checks — Concurrency, Email, Caching

**Goal:** Verify system behavior for concurrent updates, email notifications, and caching consistency.

| #  | Description                           | Role / Target            | Expected Result                                      | Status    |
| -- | ------------------------------------- | ------------------------ | ---------------------------------------------------- | --------- |
| 1  | Concurrent PATCH on same user         | any / same user          | ✅ Last update wins, no data corruption              | ⏳ Pending |
| 2  | Concurrent PATCH on different users   | ADMIN / multiple USERs   | ✅ Updates isolated per user                         | ⏳ Pending |
| 3  | Email notification on user creation   | SUPERADMIN               | ❌ SUPERADMIN creation is restricted                 | ✅ Passed |
| 3  | Email notification on user creation   | ADMIN → USER             | ✅ Email sent with correct content & format          | ✅ Passed |
| 4  | Email notification on password update | any / self               | ✅ Email sent confirming password change             | ⏳ Pending |
| 5  | Attempt role escalation via PATCH     | USER / SUPERADMIN        | ❌ 403 Forbidden, no email sent                      | ⏳ Pending |
| 6  | Cache consistency after update        | any / affected endpoints | ✅ Updated data visible immediately                  | ✅ Passed |
| 7  | Cache invalidation on delete          | ADMIN / USER             | ✅ Deleted user removed from caches                  | ✅ Passed |
| 8  | Pagination cache test                 | SUPERADMIN / GET /users/ | ✅ Pagination reflects latest additions/deletions    | ⏳ Pending |
| 9  | Email formatting / HTML validation    | any / generated email    | ✅ Email HTML valid, no broken links or placeholders | ✅ Passed |
| 10 | Multiple concurrent DELETE + PATCH    | ADMIN / same USER        | ✅ Proper 403/404 responses, no partial corruption   | ⏳ Pending |

### 🟦 Contacts Count Cache (Redis)

**Goal:** Verify correct behavior of the contacts-count caching layer used during `/users/` listing, ensuring performance and consistency of the cached `contacts_count` field.

| #  | Description                            | Steps                     | Expected Result                                            | Status |
| - | --------------------------------------- | ------------------------- | ---------------------------------------------------------- | ------ |
| 1 | Cache warm-up on first access           | 1. Create several contacts for a user<br>2. Call `GET /users/` as SUPERADMIN/ADMIN | First call: DB hit → value cached                                         | ⏳ Pending      |
| 2 | Cache hit                               | 1. Call `GET /users/` again<br>2. Ensure Redis entry exists                        | Second call: No DB query for contacts count, returned instantly           | ⏳ Pending      |
| 3 | Cache invalidation on contact create    | 1. Create contact<br>2. Call `GET /users/`<br>3. Compare returned `contacts_count` | Count updated immediately (cache invalidated & recalculated)              | ⏳ Pending      |
| 4 | Cache invalidation on contact update    | 1. Update or patch a contact<br>2. Call `GET /users/`                              | Cache is invalidated (or TTL expiry respected) and updated value returned | ⏳ Pending      |
| 5 | Cache invalidation on contact delete    | 1. Delete a contact<br>2. Call `GET /users/`                                       | `contacts_count` decreases correctly and cache refreshed                  | ⏳ Pending      |
| 6 | Behavior when cache disabled (optional) | Temporarily disable provider in DI                                                 | System falls back to DB count without errors                              | ⏳ Pending      |
| 7 | TTL expiration behavior                 | 1. Manually reduce TTL<br>2. Wait TTL+1 sec<br>3. Call `GET /users/`               | Cache rebuilt after expiration                                            | ⏳ Pending      |
| 8 | Consistency in pagination of users list | Add/remove contacts for multiple users → Call `GET /users/` with pagination        | Each user's `contacts_count` reflects updated numbers despite pagination  | ⏳ Pending      |

**Notes:**
- `contacts_count` is cached per user: `app-cache:user:{user_id}:contacts-count`
- Cache is updated only inside `GET /users/*` flows, not inside mutation methods
- Invalidations occur on: `create_contact`, `update_contact`, `remove_contact`


---

📋 **Notes & Observations**
> Record any findings, anomalies, or improvement suggestions:
>
> - ...
> - ...
