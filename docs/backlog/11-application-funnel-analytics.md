---
status: todo
---

# 11 — Application funnel analytics

## Summary

A small stats view: response rate, interview rate, and offer rate across the
user's applications, plus a simple state-distribution breakdown, computed from
existing `JobApplication`/`ApplicationEvent` data.

## Why

"Analytics (response, interview, offer rates)" is listed as a killer feature in
the discovery doc. It's cheap once the underlying data exists (tasks 01–07) —
purely a read/aggregate on top of what's already stored, no new entity.

## Definitions

Pick simple, defensible definitions and encode them once server-side so frontend
and backend never disagree:

- **Total applications**: count of all `JobApplication` rows for the user
  (excluding `interested` — that state means "not yet applied", so it shouldn't
  count as an application sent, only as a saved lead).
- **Response rate**: applications that reached at least `screening` ÷ total
  applications (i.e., left `applied` without being `ghosted` while still
  `applied`). Approximate via: `state not in (applied, ghosted)` OR any
  `ApplicationEvent` exists for it other than `application_sent`/
  `application_updated`.
- **Interview rate**: applications that ever reached `interviewing` or later
  (`interviewing`, `assessment`, `offer`, `accepted`, `rejected` **if** they had
  passed through interviewing — simplify to "current or past state includes
  interviewing" by checking `state in (interviewing, assessment, offer,
  accepted)` OR an `ApplicationEvent` of type `interview_meeting`/`video_call`/
  `phone_call` exists) ÷ total applications.
- **Offer rate**: applications with `state in (offer, accepted)` OR an
  `offer_received` event ÷ total applications.

Document these exact rules as docstrings on the backend function — the point is
consistency, not statistical rigor; a PM reviewing the number needs to know
precisely what it counts.

## Backend

`backend/src/apps/applications/routes.py`:

- `GET /api/applications/stats` → 

  ```json
  {
    "total_applications": 12,
    "response_rate": 0.42,
    "interview_rate": 0.25,
    "offer_rate": 0.08,
    "state_counts": { "interested": 2, "applied": 5, "...": 0 }
  }
  ```

  `state_counts` includes every `ApplicationState` value, even zero counts (so
  the frontend can render a stable chart without filling gaps itself).
- Implementation: two queries — one `GROUP BY state` count over
  `JobApplication`, one existence check per application for the relevant event
  types (a single query with `EXISTS` subqueries or a join + `DISTINCT
  job_application_id`, whichever reads more clearly against SQLModel/SQLAlchemy
  here — avoid N+1 by not looping per application in Python).
- Returns all-zero/`0.0` rates when `total_applications` is 0 (guard the
  division, don't 500 or NaN).

## Frontend

- `api.ts`: `getApplicationStats(token)`.
- New `frontend/src/applications/AnalyticsPanel.tsx`: three Mantine stat cards
  (`response_rate`, `interview_rate`, `offer_rate`, formatted as percentages) and
  a simple horizontal bar or `Progress`-based breakdown of `state_counts` (no new
  charting dependency needed for a handful of bars — plain `Progress` components
  or CSS bars are enough; only reach for a chart library if this grows into a
  dedicated dashboard later).
- Add a third Mantine `Tabs` entry, "Analytics", alongside "Applications" and
  "Contacts" (tabs introduced in task 05), rendering `AnalyticsPanel`.
- i18n additions (all four locale files), new `analytics` namespace: `title`,
  `responseRate`, `interviewRate`, `offerRate`, `stateBreakdown`, `noData` (shown
  when `total_applications === 0`).

## Tests

- Zero applications → all rates `0.0`, no error.
- A crafted set of applications/events exercising each rate's edge (e.g. one
  `applied`-only app counts toward total but not response; one with an
  `interview_meeting` event but `state=applied` still counts toward interview
  rate) — assert the exact numbers to lock in the definitions above.
- `state_counts` includes all ten states with correct zero-fill.
