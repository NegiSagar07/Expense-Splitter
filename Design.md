# Expense Tracker / Splitter — Design Document

**Status:** Draft v0.1
**Companion to:** `expense-splitter-spec.md` (v0.3+)
**Stack:** FastAPI (Python) · PostgreSQL · React · Tailwind CSS 

This document translates the finalized spec's *behavior* requirements into an
implementation plan: data model, API contracts, architecture, and key
technical decisions. It intentionally does not re-litigate product behavior
already decided in the spec — if something here conflicts with the spec, the
spec wins and this doc needs updating.

---

## 1. Architecture Overview

```
┌─────────────────┐        HTTPS/JSON         ┌──────────────────────┐
│  React + Tailwind │ ───────────────────────▶ │   FastAPI (REST API)  │
│  (SPA, client-side│ ◀─────────────────────── │   + Pydantic models   │
│   routing)         │                          │   + JWT auth          │
└─────────────────┘                            └──────────┬───────────┘
                                                            │ SQLAlchemy 2.0+ / asyncpg
                                                            ▼
                                                  ┌──────────────────┐
                                                  │   PostgreSQL      │
                                                  └──────────────────┘
```

- **Frontend:** React SPA, Tailwind for styling, talks to the backend only
  via REST (no server-rendered pages).
- **Backend:** FastAPI serving a JSON REST API, stateless (auth via JWT so
  any instance can handle any request — matters if you ever scale
  horizontally).
- **Database:** PostgreSQL as the single source of truth. No caching layer
  in v1 — not needed at this scale, added complexity isn't justified yet.

## 2. Data Model

### 2.1 Entity-Relationship Summary

```
User ──< GroupMembership >── Group
              │
              ├── role: super_admin | admin | member
              │
Group ──< Expense >── User (owner)
              │
              └──< ExpenseShare >── User (participant)

Group ──< JoinRequest >── User
```

### 2.2 Tables

**`users`**
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| name | text | |
| email | text, unique | |
| password_hash | text | bcrypt/argon2 — never store plaintext |
| created_at | timestamptz | |

**`groups`**
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| name | text | |
| created_by | UUID (FK → users.id) | |
| created_at | timestamptz | |

**`group_memberships`** — the role table (this is where Super
Admin/Admin/Member is tracked, per group, per FR-A1)
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| group_id | UUID (FK → groups.id) | |
| user_id | UUID (FK → users.id) | |
| role | enum(`super_admin`, `admin`, `member`) | exactly one `super_admin` row per group — enforce via partial unique index (see §2.3) |
| status | enum(`active`, `left`) | supports FR6: history stays even after leaving |
| joined_at | timestamptz | |
| left_at | timestamptz, nullable | |

**`join_requests`** — FR3/FR4/FR4a
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| group_id | UUID (FK) | |
| user_id | UUID (FK) | |
| status | enum(`pending`, `approved`, `rejected`, `expired`) | |
| requested_at | timestamptz | |
| resolved_at | timestamptz, nullable | |
| resolved_by | UUID (FK → users.id), nullable | |

**`admin_requests`** — separate from join requests; a member asking to
become an admin (FR-A2)
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| group_id | UUID (FK) | |
| user_id | UUID (FK) | |
| status | enum(`pending`, `approved`, `rejected`) | |
| requested_at | timestamptz | |
| resolved_by | UUID (FK → users.id), nullable | admin/super_admin who approved |

**`expenses`** — FR7–FR11
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| group_id | UUID (FK) | |
| owner_id | UUID (FK → users.id) | creator; only this user can edit/delete (FR10) |
| description | text | |
| total_amount | numeric(12,2) | use `numeric`, never float, for money |
| split_type | enum(`equal`, `custom`) | FR9 |
| is_deleted | boolean, default false | soft delete (FR10a) |
| owner_locked | boolean, default false | set true when owner leaves group (FR10b) |
| created_at | timestamptz | |
| updated_at | timestamptz | |

**`expense_shares`** — one row per participant per expense; this is where
approval and per-person amount lives (FR8, FR12–FR14)
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| expense_id | UUID (FK → expenses.id) | |
| user_id | UUID (FK → users.id) | |
| amount | numeric(12,2) | this participant's share |
| status | enum(`pending`, `approved`, `rejected`) | FR13 |
| responded_at | timestamptz, nullable | |

### 2.3 Key Constraints

- **Exactly one Super Admin per group:** partial unique index —
  `CREATE UNIQUE INDEX one_super_admin_per_group ON group_memberships (group_id) WHERE role = 'super_admin' AND status = 'active';`
- **Balance calculation only counts approved shares:** `SUM(amount) WHERE
  status = 'approved' AND expense.is_deleted = false`, grouped by user pair —
  this directly implements FR13/FR15.
- **7-day join request expiry (FR4a):** a scheduled job (see §5) flips
  `pending → expired`, rather than deleting rows — keeps an audit trail.

## 3. API Contracts

Base path: `/api/v1`. Auth via JWT bearer token unless noted.

### 3.1 Auth
| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/auth/register` | `{name, email, password}` | |
| POST | `/auth/login` | `{email, password}` | returns JWT |

### 3.2 Groups & Membership
| Method | Path | Notes |
|---|---|---|
| POST | `/groups` | creates group, caller becomes `super_admin` |
| GET | `/groups/{id}` | |
| POST | `/groups/{id}/join-requests` | member requests to join (FR3) |
| POST | `/groups/{id}/join-requests/{req_id}/approve` | admin/super_admin only |
| POST | `/groups/{id}/join-requests/{req_id}/reject` | admin/super_admin only |
| POST | `/groups/{id}/admin-requests` | member requests admin role (FR-A2) |
| POST | `/groups/{id}/admin-requests/{req_id}/approve` | admin/super_admin only |
| POST | `/groups/{id}/members/{user_id}/promote` | direct promotion, admin/super_admin only |
| POST | `/groups/{id}/members/{user_id}/remove` | admin/super_admin only; **403 if target is an admin and caller is not super_admin** (FR-A3/A4) |
| POST | `/groups/{id}/leave` | if caller is super_admin, **requires `successor_id` in body**, else 400 (FR-A6) |

### 3.3 Expenses
| Method | Path | Notes |
|---|---|---|
| POST | `/groups/{id}/expenses` | `{description, total_amount, split_type, participants: [{user_id, amount?}]}` — `amount` required if `split_type=custom`, ignored/computed if `equal` |
| PATCH | `/expenses/{id}` | **403 unless caller is expense owner AND owner_locked=false** (FR10, FR10b) |
| DELETE | `/expenses/{id}` | soft delete only — sets `is_deleted=true`, same ownership check (FR10a) |
| POST | `/expenses/{id}/shares/{share_id}/approve` | only the named participant |
| POST | `/expenses/{id}/shares/{share_id}/reject` | only the named participant |
| GET | `/groups/{id}/expenses` | full history, including soft-deleted (flagged) |

### 3.4 Balances
| Method | Path | Notes |
|---|---|---|
| GET | `/groups/{id}/balances` | net "who owes whom" — server computes from approved shares only (FR15/FR16) |

## 4. Authorization Model

Middleware/dependency layer checks role **per group**, since a user's role
differs by group (FR5 — membership and role are group-scoped):

```
require_role(group_id, min_role: Literal["member","admin","super_admin"])
```

Role hierarchy for permission checks: `super_admin > admin > member`. Some
actions are role-specific rather than "min role," e.g. removing an admin is
**super_admin-only**, not "admin or above" — implement as an explicit check,
not just a hierarchy comparison, to correctly express FR-A4.

## 5. Background Jobs

- **Join-request expiry sweep** — a scheduled task (e.g., APScheduler or a
  cron-triggered endpoint) runs periodically, marking `join_requests` older
  than 7 days as `expired` (FR4a).
- No other async jobs needed in v1 — balance calculation is done
  synchronously on read since expected data volume per group is small.

## 6. Frontend Structure (React + Tailwind)

- `/login`, `/register`
- `/groups` — list of groups the user belongs to
- `/groups/:id` — group home: members, pending join/admin requests (if
  caller has permission), expense list, balance summary
- `/groups/:id/expenses/new` — create expense form (equal/custom split toggle)
- `/groups/:id/expenses/:expenseId` — detail + edit (owner only, disabled if
  `owner_locked`)
- Shared components: `RoleBadge`, `ApprovalPill` (pending/approved/rejected),
  `BalanceTable`

State: React Query (or SWR) for server state/caching; no global client state
library needed at this scope — avoid over-engineering.

## 7. Security Notes

- Passwords hashed with bcrypt or argon2, never stored/logged in plaintext.
- JWT short-lived access token; refresh token flow if session length becomes
  an issue (not a v1 blocker).
- All role checks enforced **server-side** — the frontend hiding a button is
  UX only, never the actual authorization boundary.

## 8. Open Design Questions

1. Invite links (FR3) — signed token with expiry, or a persistent
   group-level code? Signed token is simpler to invalidate/rotate.
2. Do we need rate limiting on join/admin requests to prevent spam? Likely
   yes before public launch, not a v1 blocker for a friends-only app.