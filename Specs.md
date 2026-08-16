# Expense Tracker / Splitter — Specification

**Status:** Draft for comparison / reference
**Owner:** [you]
**Version:** 0.3 — admin promotion paths, successor rule, soft delete, post-leave lock, join-request expiry all resolved

---

## 1. Overview

A shared-expense tracking application that lets groups of friends record shared
costs (rent, trips, dinners, etc.) and automatically calculates who owes whom,
removing the need for manual mental math or spreadsheets.

## 2. Problem Statement

Friends who share recurring or one-off costs currently track and settle those
costs manually (memory, chat messages, notes apps). This is error-prone, slow,
and leads to disputes over "who paid for what" and "who owes how much."

## 3. Goals

- Let users organize shared spending into **groups**.
- Let any group member **log an expense** and specify exactly who it applies to.
- Support both **equal split** and **custom split** for an expense.
- Automatically **calculate net balances** (who owes whom, how much) per group,
  counting only **approved** expenses.
- Keep a **permanent history** of every expense for transparency — including
  expenses tied to members who have since left the group.
- Make it easy to **invite people** into a group, subject to admin approval.
- Support **multiple admins per group** so the group survives any single
  admin leaving.

## 4. Non-Goals / Out of Scope (v1)

- In-app payment / settlement (actually transferring money between users).
- Multi-currency support.
- Recurring/auto-generated expenses (e.g., auto-add rent every month).
- Any in-app "enforcement" mechanism for members who leave with an unpaid
  balance — this is explicitly a manual, off-app matter between group members
  (see §9).

## 5. Target Users

**Primary persona: "Friend Group Organizer"**
A person who frequently ends up coordinating shared costs for a group —
roommates, a trip, a recurring hangout circle. Comfortable with apps like
WhatsApp; wants something lightweight, not a full accounting tool.

**Secondary persona: "Group Member"**
Someone invited into a group who mainly needs to see what they owe, confirm
their share of expenses, and check the history — not necessarily creating
groups themselves.

## 6. User Roles

Three-tier hierarchy, in order of authority:

- **Super Admin** — exactly **one** per group; the group creator becomes
  Super Admin by default. Has full control over admins and members: can
  promote a member to admin, and is the **only** role that can remove/demote
  an existing admin. Before leaving the group, the Super Admin **must**
  assign a successor Super Admin — this is the one role-transfer that blocks
  leaving.
- **Admin** — a group can have **unlimited** admins. Can approve join
  requests, can promote a member to admin (by approving the member's own
  request, or by directly assigning it), and can remove any regular member
  from the group. An admin **cannot** remove or demote another admin — only
  the Super Admin can do that. Admins can leave the group freely, with no
  successor requirement (group continuity is guaranteed by the Super Admin,
  not by admin headcount).
- **Member** — becomes a full member only after an admin approves their join
  request. Can create expenses, approve/reject shares, edit/delete expenses
  they personally created, and can request to become an admin.

Role changes (promotions, approvals) happen **silently** — no notification is
sent to other members.

## 7. User Stories

- As a **user**, I want to create an account so my expense history is tied to me.
- As a **user**, I want to request to join a group (e.g., via invite link) and
  have an admin approve me, so group membership stays controlled.
- As an **admin**, I want to approve or reject join requests, so only
  intended people enter the group.
- As an **admin**, I want to promote a member to admin, so the group isn't
  dependent on a single person.
- As an **admin**, I want to remove a disruptive member from the group.
- As an **admin**, I want to leave the group freely at any time.
- As the **Super Admin**, I want to remove or demote an admin if needed,
  since regular admins can't do this to each other.
- As the **Super Admin**, I want to be required to assign a successor before
  I leave, so the group is never left without top-level ownership.
- As a **group member**, I want to log an expense and choose exactly who it
  applies to, so people who didn't participate aren't charged.
- As a **group member**, I want to choose between an equal split or a custom
  split when logging an expense.
- As a **group member**, I want to be asked to approve my share of an expense
  someone else logged, so nothing counts against me without my confirmation.
- As an **expense owner**, I want to edit or delete an expense I created, so
  I can fix mistakes — but no one else should be able to alter my entries.
- As a **group member**, I want to see the full history of expenses, even
  ones tied to a member who has since left, so the record stays accurate.
- As a **group member**, I want to see a running summary of who owes whom in
  the group, based only on approved expenses.

## 8. Functional Requirements

### 8.1 Accounts, Groups & Membership
- FR1: Users can register and log in.
- FR2: Users can create a group; the creator becomes its **Super Admin**.
- FR3: Users can request to join a group (e.g., via invite link).
- FR4: A join request only becomes membership after approval by an admin or
  the Super Admin.
- FR4a: A pending join request that receives no action is automatically
  removed after **7 days**.
- FR-A1: A group has exactly **one Super Admin** and can have **unlimited**
  Admins.
- FR-A2: A member can be promoted to Admin two ways — the member **requests**
  it and an Admin/Super Admin approves, or an Admin/Super Admin **directly
  assigns** it without a request.
- FR-A3: An Admin can remove any regular Member from the group. An Admin
  **cannot** remove or demote another Admin.
- FR-A4: Only the **Super Admin** can remove or demote an existing Admin.
- FR-A5: An Admin can leave the group at any time, with no successor
  requirement.
- FR-A6: The **Super Admin** must assign a successor Super Admin before they
  are allowed to leave the group — this is the only leave action the system
  blocks.
- FR-A7: Promotions, approvals, and role changes happen **silently** — no
  notification is sent to other members.
- FR5: A user can belong to multiple groups simultaneously; balances are
  scoped per group (not merged across groups).
- FR6: If a member leaves a group, their past expenses and history remain
  visible in the group permanently. The app does not attempt to
  collect/enforce any outstanding balance on their behalf — that is left to
  the group to handle manually.

### 8.2 Expenses
- FR7: Any group member can create an expense within a group.
- FR8: When creating an expense, the creator specifies which group members
  the expense applies to (not automatically "everyone in the group").
- FR9: The creator chooses the split type per expense:
  - **Equal split** — total divided evenly among selected members.
  - **Custom split** — creator manually assigns an amount to each selected
    member.
- FR10: Only the **expense owner** (creator) can edit or delete that expense.
  No other member — including admins — can modify someone else's expense.
- FR10a: Deleting an expense is a **soft delete** — the expense is marked as
  deleted and remains in the group's history (not erased), consistent with
  the permanent-history principle in FR6.
- FR10b: If the expense owner **leaves the group**, they lose the ability to
  edit or delete any expense they created — those expenses become locked/
  read-only, still visible in history as normal.
- FR11: Every expense (including edited/soft-deleted ones) is recorded in a
  viewable history for the group.

### 8.3 Approval
- FR12: When a user is included in an expense they didn't create, they must
  explicitly approve their share before it counts.
- FR13: An **unapproved expense stays in a "pending" state** and does **not**
  count toward any balance calculation until approved.
- FR14: A member can reject a share; rejection should be visible to the
  expense owner rather than silently disappearing.

### 8.4 Balance Calculation
- FR15: The system calculates, per group, the net amount each member owes or
  is owed, based only on **approved** expenses.
- FR16: The calculation must net out multi-directional debts (if A owes B and
  B owes A, show the simplified net, not two separate entries).

## 9. Edge Cases & Error Handling

- A user belongs to many groups — balances must stay correctly isolated per
  group.
- A member leaves the group: history stays intact; any outstanding balance
  they owed remains visible in the group's record, but resolving it
  ("punishing them for ghosting," in your words) is a manual, off-app matter
  between the remaining members — the app is not responsible for enforcement.
- An Admin leaves the group: allowed at any time, no successor needed
  (FR-A5). The **Super Admin** is the only role blocked from leaving until
  they assign a successor (FR-A6).
- An Admin tries to remove another Admin: blocked — only the Super Admin can
  remove/demote an Admin (FR-A3, FR-A4).
- Deleting an expense is a **soft delete** — it stays in history, marked
  deleted, rather than being erased (FR10a).
- An expense owner who has left the group can no longer edit or delete
  expenses they created — those entries lock as read-only (FR10b).
- A pending join request with no admin action **auto-expires after 7 days**
  (FR4a).

## 10. Constraints & Assumptions

- Not every group member participates in every expense (e.g., someone who
  doesn't drink shouldn't be charged for the bar tab) — supported at the
  expense level via FR8.
- The app deliberately does **not** mediate disputes or enforce payment
  beyond showing accurate, approved balances — this is a stated design
  choice, not a gap.
- Assumes members join only via admin-approved requests — there is no fully
  open/self-service join path.

## 11. Acceptance Criteria

- [ ] A user can register and create an account.
- [ ] A user can create a group and becomes its first admin.
- [ ] A user can request to join a group via invite link.
- [ ] An admin can approve or reject a join request.
- [ ] A pending join request auto-expires after 7 days with no admin action.
- [ ] A member can request to become an admin, and an admin/Super Admin can
      directly promote a member — both paths work.
- [ ] An admin can remove a regular member, but cannot remove/demote another
      admin.
- [ ] Only the Super Admin can remove/demote an admin.
- [ ] An admin can leave the group at any time, freely.
- [ ] The Super Admin must assign a successor before they're allowed to leave.
- [ ] A member can create an expense, choosing participants and split type
      (equal or custom).
- [ ] A member included in an expense can approve or reject their share.
- [ ] An unapproved expense shows as "pending" and is excluded from balance
      totals.
- [ ] Only the expense owner can edit or delete their own expense; deletion
      is a soft delete (stays in history, marked deleted).
- [ ] An expense owner who has left the group can no longer edit/delete
      expenses they created.
- [ ] A member who leaves the group no longer appears as active, but their
      past expenses remain visible in group history.
- [ ] The group shows an accurate "who owes whom" summary based only on
      approved expenses.

## 12. Open Questions (remaining)

All open questions have been resolved. Role model, promotion paths, removal
rules, succession, split logic, approval, and deletion behavior are all
defined.

## 13. Success Metrics (optional, worth defining even roughly)

- Time to log an expense and get it approved by all parties.
- % of expenses that get rejected/disputed (signals split-logic clarity).
- Number of active groups per user after 30 days (signals retention).

---

*Design-level concerns intentionally excluded from this document per your own
scoping decision: data model/schema, API contracts, tech stack, and security
implementation details. Those belong in `plan.md` / a design doc that follows
once this spec is finalized.*