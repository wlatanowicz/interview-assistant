---
status: todo
---

# 03 — Kanban pipeline board

## Summary

Replace the flat table on the dashboard with a kanban board: one column per
non-terminal `ApplicationState`, cards for each application, drag-and-drop (or an
accessible menu fallback) to move a card between columns. Terminal-state
applications (`accepted`, `rejected`, `withdrawn`, `ghosted`) are collapsed into a
"Closed" section below the board rather than taking up column space.

## Why

"Kanban pipeline" is its own line item in the MVP list, distinct from the tracker
table — it's the primary way a user is expected to see where every active
application stands at a glance.

## Scope

In: board layout, drag/drop or menu-based state change, closed-applications
section. Out: reordering within a column (no manual sort field exists or is
needed — order by `updated_at desc`, matching the current list endpoint), swimlanes,
saved filters.

## Data / backend

None. This task is pure frontend — it reuses `GET /api/applications` (list, called
without the `active` filter so both open and closed applications are fetched once)
and `PATCH /api/applications/{id}` from task 01 to persist a column move. Calling
this out explicitly rather than skipping backend for this task by omission: there
is genuinely no server-side change needed here, because task 01 already shipped a
complete, independently useful PATCH endpoint.

## Frontend

- New `frontend/src/applications/KanbanBoard.tsx`:
  - Columns, in order: `interested`, `applied`, `screening`, `interviewing`,
    `assessment`, `offer` (from `NON_TERMINAL_APPLICATION_STATES`).
  - Group the already-fetched `JobApplication[]` client-side by `state`; no new
    query params.
  - Each card shows `company`, `position`, `started_on`, and opens
    `ApplicationDetailDrawer` (task 01) on click.
  - Drag-and-drop: implement with the browser's native HTML5 Drag and Drop API
    (`draggable`, `onDragStart`, `onDragOver`, `onDrop`) — no new dependency
    needed for a single-axis card move. On drop into a different column, call
    `updateApplication(token, id, { state: newState })` and optimistically move
    the card, rolling back on failure (show the existing error alert pattern).
  - Accessible/mobile fallback: each card also gets a small "Move to…" menu
    (Mantine `Menu`) listing the other non-terminal states plus "Mark closed…"
    which opens the detail drawer's state `Select` — native drag alone would lock
    out keyboard and touch users.
  - A "Closed" `Paper` below the board lists terminal-state applications as a
    compact table (company, position, state badge, `finished_on`), collapsed by
    default (Mantine `Accordion` or a simple toggle), reusing the existing table
    rendering from `Dashboard.tsx`.
- `Dashboard.tsx`: replace the current `Table` rendering of applications with
  `<KanbanBoard applications={applications} onChanged={loadApplications} token={token} />`,
  keeping the header, "New application" button, loading/error/empty states as-is.
- i18n additions (all four locale files): `applications.closedSection`,
  `applications.moveTo`, `applications.markClosed`.

## Tests

No new backend tests (no backend change). If a frontend test setup exists by the
time this is picked up, cover: grouping applications into the right columns,
optimistic move + rollback on a failed `PATCH`. If no frontend test runner exists
yet in the repo, note that as a gap rather than introducing one as a side effect of
this task.
