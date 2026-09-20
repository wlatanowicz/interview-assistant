---
status: todo
---

# 09 — Upcoming reminders widget

## Summary

Add a dashboard widget listing every scheduled, future `ApplicationEvent` across
all of the user's applications ("what's coming up"), sorted soonest-first, each
linking straight to its application.

## Why

First half of the MVP "reminder system" — an in-app view of what's ahead — kept
separate from task 10's outbound email reminders so this ships as soon as the
timeline (task 07) exists, without waiting on the notifications/scheduler
integration.

## Data / backend

The exact query this needs — `WHERE user_id = ? AND outcome = 'scheduled' AND
occurred_at >= now()` — is already covered by the partial index created in task 07
(`ix_application_events_user_id_occurred_at_scheduled`), so no new migration.

`backend/src/apps/applications/routes.py`:

- `GET /api/events/upcoming?limit=10` → `{ events: EventWithApplicationPublic[] }`.
  Query: `ApplicationEvent` joined to `JobApplication` (for `company`/`position`
  display), filtered to `user_id == user.id`, `outcome == EventOutcome.scheduled`,
  `occurred_at >= datetime.now(UTC)`, ordered `occurred_at asc`, capped at `limit`
  (default 10, max 50 — validate with `Query(le=50)`).
- Response item shape: the existing `EventPublic` fields (task 07) plus
  `job_application_id`, `company`, `position` (denormalized into the response, not
  the table) so the widget can render without a second round trip per row.

## Frontend

- `api.ts`: `listUpcomingEvents(token, { limit? })`.
- New `frontend/src/applications/UpcomingEventsWidget.tsx`: a `Paper` above or
  beside the kanban board (task 03) showing up to N rows —
  date/time, event type label, company + position, a "view" action that opens
  `ApplicationDetailDrawer` (task 01) for that application with the timeline
  section (task 07) expanded/scrolled to that event if easy, otherwise just
  opened at the top — don't force deep-linking machinery for this.
  Empty state: "Nothing scheduled" message, consistent with `Dashboard`'s
  existing empty-state pattern.
- Mount it in `Dashboard.tsx` above the kanban board, refreshed on the same
  `loadApplications` cadence plus its own fetch (separate endpoint, separate
  loading state — don't block the board render on this call).
- i18n additions (all four locale files): `dashboard.upcomingTitle`,
  `dashboard.upcomingEmpty`.

## Mobile

- `mobile/src/api.ts`: `listUpcomingEvents`.
- A widget at the top of the mobile Applications screen (task 00), same
  fields, tapping a row navigates to the task 01 mobile detail screen for that
  application. Fetched separately from the applications list, same
  non-blocking loading behavior as web.

## Tests

- Returns only `scheduled` events with `occurred_at` in the future, excludes
  `completed`/`cancelled`/`no_show` and past-dated scheduled events.
- Ordered soonest-first; respects `limit`; `limit` above 50 → 422.
- Only returns the authenticated user's events, across multiple applications.
