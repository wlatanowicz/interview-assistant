# Backlog

Derived from [`discovery_summary.md`](../discovery_summary.md) (MVP scope + killer
features) and [`domain-model.md`](../domain-model.md) (data design), cross-checked
against the code actually shipped so far (`82d6d38` — job application create/list
only: no edit, no delete, no kanban, no contacts, no timeline).

Files are numbered in execution order. Each is a single deliverable: model/migration
+ API + UI + tests, no file leaves half of a feature for a later ticket.

**Platform decision (2026-09-17):** mobile (React Native + Expo) starts
immediately, and every feature built for web from now on ships on mobile at
the same time — see `00` below and `discovery_summary.md`'s new "Platforms"
section. Tasks `01`–`12` each carry a `## Mobile` section alongside their
`## Frontend` section for this reason.

## What's covered

Each ticket file carries a `status` frontmatter field (`todo` or `done`) —
check there for the current source of truth; the table below is a snapshot.

| # | Task | MVP pillar | Status |
|---|------|------------|--------|
| 00 | Mobile app bootstrap (React Native + Expo) | Platform foundation | todo |
| 01 | Application detail view & edit | Application tracker | todo |
| 02 | Delete an application | Application tracker | todo |
| 03 | Kanban pipeline board | Kanban pipeline | todo |
| 04 | Stage estimate & deadline fields | Application tracker | todo |
| 05 | Contacts directory | Company & recruiter contacts | todo |
| 06 | Link a primary contact to an application | Company & recruiter contacts | todo |
| 07 | Application timeline (events) | Interview notes | todo |
| 08 | Event participants | Company & recruiter contacts | todo |
| 09 | Upcoming reminders widget | Reminder system | todo |
| 10 | Scheduled email reminders | Reminder system / killer feature | todo |
| 11 | Application funnel analytics | Killer feature (analytics) | todo |
| 12 | AI interview prep notes | Killer feature (AI interview preparation) | todo |

## Explicitly out of scope (not ticketed here)

Per discovery doc, these are either "Future Features" (post-MVP) or killer features
that require infrastructure this repo doesn't have yet (an inbound email pipeline,
an LLM provider integration). Flagging so they aren't mistaken for omissions:

- **Email parsing / automatic interview detection** — needs inbound email receiving
  (the repo only has an outbound SES transport) plus a parsing pipeline. Worth its
  own discovery spike before it's ticketed. Traces back to the "przekierowywanie
  maili od rekruterów" idea in [`IDEAS.md`](IDEAS.md).
- **Resume tailoring, salary benchmarking, recruiter relationship management beyond
  a rolodex, career history, AI career coach** — listed as "Future Features",
  post-MVP by the discovery doc's own framing.
- **`Company` entity normalization, `Attachment` model, contact merge** — called out
  as future extensions in the domain model doc; nothing in the MVP list depends on
  them yet.

## Validated against IDEAS.md

[`IDEAS.md`](IDEAS.md) is the raw (Polish-language) brainstorm this backlog
ultimately traces back to, one idea per paragraph. `discovery_summary.md` is meant
to be the triaged version of that list (MVP / Killer / Future), and this backlog
derives from `discovery_summary.md`, not from `IDEAS.md` directly. Checking each
`IDEAS.md` paragraph against that chain:

| IDEAS.md idea (paraphrased) | Status |
|---|---|
| Track recruitment progress, full history, offers, free-form notes | Covered — tracker (01) + timeline (07) |
| Configurable number of stages per recruitment (tests, multi-round interviews, pair programming) | Covered — 04 (`estimated_stage_count`/`estimated_stages`) |
| Save company representatives' contact info | Covered — 05 (contacts directory) |
| Kanban-style board, reconciled across companies with different stage counts | Covered — 03 (generalized `ApplicationState` columns) + 04 (per-application stage detail) |
| Eventually, anonymous cross-user statistics (e.g. a given company's response time) | **Gap** — see below |
| Detect ghosting (long silence) | **Gap** — see below |
| Forward recruiter emails for automatic assignment to a recruitment | Out of scope, listed above |
| Calendar | **Gap** — see below |
| Native iOS/Android apps (React Native + Expo) sharing the existing backend API | Decided (2026-09-17) — see task `00` and the "Mobile" section on every ticket below |

Three ideas were never carried forward into `discovery_summary.md`'s MVP/Killer/
Future lists, so they also never got a backlog ticket. That's a product-scope
decision, not something this backlog should decide unilaterally — flagging here
rather than ticketing. (The fourth, mobile apps, got the same "not this backlog's
call" flag in the previous review — the user has since made that call explicitly,
so it's ticketed as `00` instead of listed here.)

- **Ghosting detection.** The domain model has a `ghosted` `ApplicationState`
  (`domain-model.md`), but it's a manual selection today — nothing flags a
  gone-quiet application automatically. Would need a defined "no activity for N
  days while non-terminal" rule and either a dashboard badge or a background task.
- **Calendar view.** The upcoming-reminders widget (09) is a *list* of scheduled
  events, not a calendar/month-grid view. Distinct enough from 09 that it should be
  scoped separately if wanted.
- **Anonymous cross-user statistics** (e.g. a given company's typical response
  time). Fundamentally different from task 11's analytics — that's a private,
  per-user rollup; this needs cross-user aggregation, an anonymization/consent
  design, and probably a `Company` entity (already deferred above) to key on.
  Not safe to ticket without its own discovery pass.

If any of these should be in scope, they belong in `discovery_summary.md` first
(MVP, Killer, or Future Features) before being broken into tasks here.

## Cross-cutting conventions assumed by every task below

- Backend: FastAPI + SQLModel, one `apps/<name>/` package with `models.py`,
  `routes.py`, `api_errors.py`, `tests/`. New enums via `to_sql_enum` +
  `alembic-postgresql-enum`. Every table/query is scoped by `user_id`.
- Migrations: Alembic, one file per task, autogenerate then hand-review (matching
  the existing `b7e4a1c9023f_add_job_applications.py` style). Register any new
  SQLModel class in `backend/alembic/env.py` before autogenerating.
- Frontend: React + Mantine 9, no router installed — navigation between sections
  uses Mantine `Tabs` inside `App.tsx`, detail/edit uses `Modal`/`Drawer`, matching
  the existing `NewApplicationModal` pattern. i18n via `react-i18next`; every
  user-facing string added to **all four** locale files
  (`en.json`, `de.json`, `pl.json`, `uk.json` — only `en` needs real copy for the
  others to be reviewed by a translator, but keys must exist in all four so the
  build doesn't fall back silently).
- Tests: backend integration tests against a real Postgres via the existing
  `auth_client` fixture (see `apps/applications/tests/test_routes.py`); no new
  frontend test framework introduced unless a task says so.
- Mobile: `mobile/` (Expo, React Native, TypeScript), scaffolded in task `00`.
  Every ticket from `01` onward ships its web slice and mobile slice together —
  a ticket isn't done with only one platform built. Mobile screens reuse the
  same backend endpoints and the same four locale JSON files as web; no
  separate translation pass. Interaction patterns translate rather than
  copy 1:1 (Mantine `Modal`/`Drawer` → a pushed screen, `modals.openConfirmModal`
  → `Alert.alert`, HTML5 drag-and-drop → the same menu/action-sheet-based move
  already speced for web in task 03) — each ticket's `## Mobile` section says
  what that translation is for that feature.
