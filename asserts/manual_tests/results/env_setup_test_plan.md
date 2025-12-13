# 🧪 ENVIRONMENT SETUP TEST PLAN — FastAPI Contacts App

**Goal:** Manual verification of application initialization, Users CRUD, Contacts CRUD, role-based access control, and validation logic.  
**Scope:** Full system, including Docker Compose startup, environment variables, DB initialization, migrations, superuser, pgAdmin setup, Users and Contacts endpoints.  
**Version:** 1 for Stage 1 — Full System Setup 
**Date:** 2025-12-07  
**Tester:** Oleksandr Romashko
**Testing Environment:** OS: Ubuntu 24.04.3 LTS, Browser: Firefox Browser 145.0.2 (64-bit)

---

## ✅ CHECKLIST OVERVIEW
- [x] App initialization and environment
- [x] Docker Compose services (DEV/PROD)
- [x] DB and Redis ready
- [x] Alembic migrations applied
- [x] Superuser seeded
- [x] pgAdmin profile setup
- [ ] Users CRUD operations
- [ ] Contacts CRUD operations 
- [ ] Upcoming birthdays
- [ ] Role-based access control
- [ ] Field validation (email, password, phone, birthdate)
- [ ] Security / logging
- [ ] End-to-end "happy path"

---

## 🔹 0. App Initialization

| #     | Description                                    | Expected Result                                                   | Status |
| ----- | ---------------------------------------------- | ----------------------------------------------------------------- | ------ |
| 1 | Docker Compose services start (api, db, cache) | ✅ All containers running, no unnecessary ports exposed            |    ⚠️ Passed*  |
| 2 | Profile `tools` starts pgAdmin                 | ✅ pgAdmin container running                                       | ✅ Passed      |
| 3 | Healthchecks pass                              | ✅ API `/api/healthchecker/`, `/docs/`; Redis PONG; Postgres ready | ✅ Passed      |
| 4 | Required environment variables                 | ✅ All `required_vars` set, no default placeholder values          | ✅ Passed      |
| 5 | DB initialized with app user                   | ✅ `${DB_APP_USER}` exists, privileges correct                     | ✅ Passed      |
| 6 | Alembic migrations applied                     | ✅ `alembic upgrade head` completes                                | ✅ Passed      |
| 7 | Superuser seeded                               | ✅ Created if not exists; logs show "already exists" if exists     | ✅ Passed      |
| 8 | pgAdmin setup                                  | ✅ `servers.json` rendered; login works; can connect to DB         | ✅ Passed      |
| 9 | App startup modes                              | ✅ DEV: uvicorn reload works; PROD: python -m src.main             | ✅ Passed      |

---

## 🔹 1. Users CRUD (`/users/*`)

| #     | Description                   | Input / Role              | Expected Result                | Status |
| ----- | ----------------------------- | ------------------------- | ------------------------------ | ------ |
| [ ] 1 | SUPERADMIN creates USER       | role=`USER`               | ✅ 201 Created                 | ☐      |
| [ ] 2 | SUPERADMIN creates ADMIN      | role=`ADMIN`              | ✅ 201 Created                 | ☐      |
| [ ] 3 | SUPERADMIN creates SUPERADMIN | role=`SUPERADMIN`         | ❌ 400 Restricted              | ☐      |
| [ ] 4 | ADMIN creates USER            | role=`USER`               | ✅ 201 Created                 | ☐      |
| [ ] 5 | ADMIN creates ADMIN           | role=`ADMIN`              | ❌ 403 Forbidden               | ☐      |
| [ ] 6 | USER tries to create any user | any role                  | ❌ 403 Forbidden               | ☐      |
| [ ] 7 | Missing email/password        | SUPERADMIN                | ❌ 422 Validation Error        | ☐      |
| [ ] 8 | Duplicate username/email      | SUPERADMIN                | ❌ 409 Conflict                | ☐      |
| [ ] 9 | Avatar fallback               | email provided, no avatar | ✅ Avatar URL set via Gravatar | ☐      |

---

## 🔹 2. Users — Get / Update / Delete

| #     | Description                       | Role / Target  | Expected Result  | Status |
| ----- | --------------------------------- | -------------- | ---------------- | ------ |
| [ ] 1 | Get all users — SUPERADMIN        | any            | ✅ Full list     | ☐      |
| [ ] 2 | Get user by ID — ADMIN→USER       | active USER    | ✅ Full data     | ☐      |
| [ ] 3 | Update self — invalid role        | any            | ❌ 403 Forbidden | ☐      |
| [ ] 4 | Update another — SUPERADMIN→ADMIN | any            | ✅ Success       | ☐      |
| [ ] 5 | Delete user — ADMIN→USER          | allowed target | ✅ Success       | ☐      |

---

## 🔹 3. Contacts CRUD (`/contacts/*`)

| #     | Description              | Input                       | Expected Result                              | Status |
| ----- | ------------------------ | --------------------------- | -------------------------------------------- | ------ |
| [ ] 1 | Create valid contact     | All required fields valid   | ✅ 201 Created, contact returned             | ☐      |
| [ ] 2 | Retrieve single contact  | Existing `contact_id`       | ✅ 200 OK, correct contact returned          | ☐      |
| [ ] 3 | Retrieve all contacts    | None / filters / pagination | ✅ 200 OK, list of contacts, filters applied | ☐      |
| [ ] 4 | Update contact fully     | All fields provided         | ✅ 200 OK, contact updated                   | ☐      |
| [ ] 5 | Update contact partially | Subset of fields            | ✅ 200 OK, only updated fields changed       | ☐      |
| [ ] 6 | Delete contact           | Valid `contact_id`          | ✅ 200 OK, deleted contact returned          | ☐      |
| [ ] 7 | Upcoming birthdays       | None / pagination           | ✅ 200 OK, `celebration_date` correct        | ☐      |

---

## 🔹 4. Role-Based Access Control (Users & Contacts)

| #     | Scenario                         | Role       | Expected Result  | Status |
| ----- | -------------------------------- | ---------- | ---------------- | ------ |
| [ ] 1 | USER accessing `/users/me`       | USER       | ✅ 200 OK        | ☐      |
| [ ] 2 | USER accessing admin route       | USER       | ❌ 403 Forbidden | ☐      |
| [ ] 3 | ADMIN accessing superadmin route | ADMIN      | ❌ 403 Forbidden | ☐      |
| [ ] 4 | SUPERADMIN accessing all routes  | SUPERADMIN | ✅ 200 OK        | ☐      |

---

## 🔹 5. Field Validation

| #     | Description         | Input             | Expected Result         | Status |
| ----- | ------------------- | ----------------- | ----------------------- | ------ |
| [ ] 1 | Email format        | Invalid email     | ❌ 422 Validation Error | ☐      |
| [ ] 2 | Password rules      | Too short / empty | ❌ 422 Validation Error | ☐      |
| [ ] 3 | Birthdate in future | `2100-01-01`      | ❌ 422 Validation Error | ☐      |
| [ ] 4 | Optional fields     | Missing info      | ✅ Allowed              | ☐      |

---

## 🔹 6. Security / Logging

| #     | Description                       | Expected Result            | Status |
| ----- | --------------------------------- | -------------------------- | ------ |
| [ ] 1 | Passwords never logged            | ✅ Masked `<hidden>`       | ☐      |
| [ ] 2 | Role escalation attempts rejected | ❌ 403 Forbidden           | ☐      |
| [ ] 3 | Deactivated users cannot access   | ❌ 403 Forbidden           | ☐      |
| [ ] 4 | Deletion / update actions logged  | ✅ Logs show action & user | ☐      |

---

## 🔹 7. End-to-End "Happy Path"

| #     | Step                                      | Expected Result                       | Status |
| ----- | ----------------------------------------- | ------------------------------------- | ------ |
| [ ] 1 | Start DEV environment (`make dev`)        | ✅ Containers up, hot reload works    | ☐      |
| [ ] 2 | Start PROD environment (`make prod`)      | ✅ Containers up, API responds        | ☐      |
| [ ] 3 | SUPERADMIN creates USER                   | ✅ Success                            | ☐      |
| [ ] 4 | USER logs in and accesses `/users/me`     | ✅ Success                            | ☐      |
| [ ] 5 | USER creates / updates / deletes contacts | ✅ Operations succeed, RBAC respected | ☐      |
| [ ] 6 | Admin updates a USER (allowed fields)     | ✅ Success                            | ☐      |
| [ ] 7 | SUPERADMIN deletes a USER                 | ✅ Success                            | ☐      |
| [ ] 8 | API healthchecks & Swagger UI             | ✅ 200 OK                             | ☐      |
| [ ] 9 | Redis cache accessible                    | ✅ PONG                               | ☐      |

---

📋 **Notes & Observations**
> Record anomalies, misconfigurations, or startup delays:  
> - Ensure secrets are never exposed in logs or container environment.  
> - DEV mode hot reload works correctly.  
> - pgAdmin profile connects without exposing root password.  
> - Alembic migrations applied successfully.  
> - Superuser seed idempotent.  
> - Containers restart on failure.  
> - All RBAC and field validations enforced.

0.1 Only local test. This point need to have testing in the production environment with env variables out of `.env` file (CI/CD, e.g. using GitHub).
0.1 Running prod in local requires uncommenting `env_file` option in the `compose.yaml` and adding `.env` file with variables.