# 🧪 CONTACTS TEST PLAN — FastAPI Contacts App

**Goal:** Manual verification of contacts CRUD, upcoming birthdays, and advanced checks (concurrency, email, caching).  
**Scope:** `api/contacts/*` routes, including creation, listing, updating, deletion, and birthdays.  
**Version:** 1 of Stage 5 — Contacts Management  
**Date:** 2025-12-15  
**Tester:** Oleksandr Romashko
**Testing Environment:** OS: Ubuntu 24.04.3 LTS, Browser: Firefox Browser 145.0.2 (64-bit)

---

## ✅ CHECKLIST OVERVIEW
- [x] Create new contact
- [x] Retrieve single contact
- [x] Retrieve all contacts (with filters & pagination)
- [ ] Update contact (full & partial)
- [ ] Delete contact
- [ ] Upcoming birthdays retrieval
- [ ] Error handling (404, validation errors)
- [ ] Field validation (email, phone, birthdate)
- [ ] Advanced checks: concurrency, email notifications, caching

---

## 🔹 1. Create Contact (`POST /contacts/`)

**Goal:** Verify creation of a new contact with valid and invalid data, including name validation rules.

| # | Description                                | Input                                    | Expected Result                                          | Status    |
| - | ------------------------------------------ | ---------------------------------------- | -------------------------------------------------------- | --------- |
| 1 | Create valid contact                       | All required fields valid                | ✅ 201 Created, contact returned with correct data       | ✅ Passed |
| 2 | Create valid contact (first_name only)     | `first_name="John"`, `last_name` omitted | ✅ 201 Created, contact returned with correct data, `last_name=""` | ✅ Passed |
| 3 | Create valid contact (last_name only)      | `last_name="Doe"`, `first_name` omitted  | ✅ 201 Created, contact returned with correct data, `first_name=""` | ✅ Passed |
| 4 | Create valid contact (both names provided) | `first_name="John"`, `last_name="Doe"`   | ✅ 201 Created, contact returned with correct data       | ✅ Passed |
| 5 | Missing both first_name and last_name      | omit `first_name` and `last_name`        | ❌ 400 Bad Request (at least one name field is required) | ✅ Passed |
| 6 | Invalid email                              | `email="not-email"`                      | ❌ 422 Validation Error                                  | ✅ Passed |
| 7 | Birthdate in the future                    | `birthdate="2100-01-01"`                 | ❌ 422 Validation Error                                  | ✅ Passed |
| 8 | Optional info field missing                | omit `info`                              | ✅ 201 Created, `info=""`                                | ✅ Passed |

---

## 🔹 2. Retrieve Single Contact (`GET /contacts/{contact_id}`)

**Goal:** Verify single contact retrieval and 404 handling.

| # | Description                       | Input                                     | Expected Result                     | Status    |
| - | --------------------------------- | ----------------------------------------- | ----------------------------------- | --------- |
| 1 | Valid contact ID of owned contact | Existing `contact_id`                     | ✅ 200 OK, correct contact returned | ✅ Passed |
| 2 | Non-existent contact ID           | `contact_id=9999`                         | ❌ 404 Not Found                    | ✅ Passed |
| 2 | Existing contact (not owner)      | Existing `contact_id` but other `user_id` | ❌ 404 Not Found                    | ✅ Passed |
| 3 | Invalid contact ID                | `contact_id=-1`                           | ❌ 422 Validation Error             | ✅ Passed |

---

## 🔹 3. Retrieve All Contacts (`GET /contacts/`)

**Goal:** Verify pagination, filtering, and empty list handling.

| # | Description                      | Input                 | Expected Result                  | Status    |
| - | -------------------------------- | --------------------- | -------------------------------- | --------- |
| 1 | Retrieve all owned contacts      | None                  | ✅ 200 OK, list of contacts       | ✅ Passed |
| 2 | Pagination (`skip=0`, `limit=5`) | Query params          | ✅ 200 OK, 5 contacts max         | ✅ Passed |
| 3 | Filter by first_name partial     | `first_name=ann`      | ✅ 200 OK, only matching contacts | ✅ Passed |
| 4 | Filter by last_name partial      | `last_name=doe`       | ✅ 200 OK, only matching contacts | ✅ Passed |
| 5 | Filter by email partial          | `email=@example.com`  | ✅ 200 OK, only matching contacts | ✅ Passed |
| 6 | No contacts exist                | User with no contacts | ✅ 200 OK, empty list             | ✅ Passed |

---

## 🔹 4. Update Contact Fully (`PUT /contacts/{contact_id}`)

**Goal:** Verify full update of an existing contact.

| # | Description             | Input               | Expected Result           | Status    |
| - | ----------------------- | ------------------- | ------------------------- | --------- |
| 1 | Valid full update       | All fields provided | ✅ 200 OK, contact updated | ✅ Passed |
| 2 | Missing required field  | Omit `email`        | ❌ 422 Validation Error    | ✅ Passed |
| 3 | Non-existent contact ID | `contact_id=9999`   | ❌ 404 Not Found           | ✅ Passed |
| 3 | Not-owned contact ID    | `contact_id=13`     | ❌ 404 Not Found           | ✅ Passed |

---

## 🔹 5. Update Contact Partially (`PATCH /contacts/{contact_id}`)

**Goal:** Verify partial update of a contact.

| # | Description                    | Input                                              | Expected Result              | Status    |
| - | ------------------------------ | -------------------------------------------------- | ---------------------------- | --------- |
| 1 | Update one field (e.g., email) | `{"email": "new@mail.com"}`                        | ✅ 200 OK, only email changed | ✅ Passed |
| 2 | Update multiple fields         | `{"first_name":"Ann","phone_number":"+123456789"}` ("`last_name`" in DB is not empty) | ✅ 200 OK, fields updated     | ✅ Passed |
| 3 | Empty body                     | `{}`                                               | ❌ 400 Bad Request            | ✅ Passed |
| 4 | Other name field is DB empty   | `{"first_name":"","phone_number":"+123456789"}` ("`last_name`" in DB is empty `""`) | ❌ 400 Bad Request     | ✅ Passed |
| 5 | Non-existent contact ID        | `contact_id=9999`                                  | ❌ 404 Not Found              | ✅ Passed |
| 6 | Invalid email format           | `{"email":"not-email"}`                            | ❌ 422 Validation Error       | ✅ Passed |

---

## 🔹 6. Delete Contact (`DELETE /contacts/{contact_id}`)

**Goal:** Verify contact deletion and error handling.

| # | Description                 | Input              | Expected Result                     | Status    |
| - | --------------------------- | ------------------ | ----------------------------------- | --------- |
| 1 | Delete existing contact     | Valid `contact_id` | ✅ 200 OK, deleted contact returned | ✅ Passed |
| 2 | Delete non-existent contact | `contact_id=9999`  | ❌ 404 Not Found                    | ✅ Passed |
| 3 | Delete not-owned contact    | `contact_id=13`    | ❌ 404 Not Found                    | ✅ Passed |

---

## 🔹 7. Upcoming Birthdays (`GET /contacts/upcoming-birthdays`)

**Goal:** Verify retrieval of contacts with birthdays in the next 7 days, including weekend adjustment.

| # | Description           | Input            | Expected Result                         | Status    |
| - | --------------------- | ---------------- | --------------------------------------- | --------- |
| 1 | Birthdays on weekdays | None             | ✅ 200 OK, correct `celebration_date`   | ✅ Passed |
| 2 | Birthdays on weekend  | None             | ✅ 200 OK, shifted to Monday if Sat/Sun | ✅ Passed |
| 3 | Pagination applied    | `skip=0&limit=5` | ✅ 200 OK, max 5 contacts               | ✅ Passed |
| 4 | No upcoming birthdays | None             | ✅ 200 OK, empty list                   | ✅ Passed |

---

## 🔹 8. Advanced Checks — Concurrency, Email, Caching

**Goal:** Verify system behavior for concurrent updates, email notifications, and caching consistency.

| # | Description                            | Input / Role             | Expected Result                                    | Status    |
| - | -------------------------------------- | ------------------------ | -------------------------------------------------- | --------- |
| 1 | Concurrent PATCH on same contact       | any / same contact       | ✅ Last update wins, no data corruption            | ⏳ Pending |
| 2 | Concurrent PATCH on different contacts | multiple contacts        | ✅ Updates isolated per contact                    | ⏳ Pending |
| 3 | Email notification on contact creation | any user                 | ❌ No email sent                                   | ✅ Passed |
| 4 | Attempt invalid email update           | any / self               | ❌ 422 Validation Error                            | ✅ Passed |
| 5 | Cache consistency after update         | any / affected endpoints | ✅ Updated contact visible immediately             | ⏳ Pending |
| 6 | Cache invalidation on delete           | any / deleted contact    | ✅ Deleted contact removed from caches             | ⏳ Pending |
| 7 | Pagination cache test                  | any / GET /contacts/     | ✅ Pagination reflects latest additions/deletions  | ⏳ Pending |
| 8 | Multiple concurrent DELETE + PATCH     | same contact             | ✅ Proper 404/400 responses, no partial corruption | ⏳ Pending |

---

📋 **Notes & Observations**
> Use this section for findings, anomalies, or suggestions:
>
> - Ensure all email, phone, and birthdate validations work.  
> - Check that users cannot access other users' contacts.  
> - Verify `info` field can store multiline notes correctly.  
> - Monitor logs for deletion/update actions.  
