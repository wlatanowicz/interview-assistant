---
status: todo
---

# 03 — Kanban pipeline board

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Zastąpienie płaskiej tabeli na dashboardzie boardem kanban:
jedna kolumna na każdy nieterminalny `ApplicationState`, karty dla każdej
aplikacji, przeciąganie (lub dostępne menu jako alternatywa) do przenoszenia
karty między kolumnami. Aplikacje w stanie terminalnym (`accepted`, `rejected`,
`withdrawn`, `ghosted`) są zwijane w sekcję „Zamknięte” pod boardem, zamiast
zajmować miejsce w kolumnach.

**Dlaczego:** „Kanban pipeline” to osobna pozycja na liście MVP, odrębna od
tabeli trackera — to podstawowy sposób, w jaki użytkownik ma widzieć na
pierwszy rzut oka, na jakim etapie jest każda aktywna aplikacja.

**Zakres:** W zakresie: układ boardu, zmiana stanu przez przeciąganie lub menu,
sekcja zamkniętych aplikacji. Poza zakresem: ręczne sortowanie w obrębie
kolumny (nie istnieje i nie jest potrzebne pole sortowania — kolejność wg
`updated_at desc`, tak jak w obecnym endpoincie listy), swimlane, zapisane
filtry.

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

## Mobile

The web ticket already treats the "Move to…" menu as a first-class interaction,
not just an accessibility fallback — that's the one to ship on mobile, since
HTML5 drag-and-drop has no native-app equivalent and a touch drag gesture isn't
required for parity here:

- Screen layout: a full multi-column board doesn't fit a phone width. Ship
  columns as horizontally swipeable pages (one `ApplicationState` per page,
  paged `ScrollView`/`FlatList`) with a segmented header showing the current
  column and counts for the others — pick the exact widget once building this,
  note the choice here.
- Each card opens the task 01 mobile detail screen on tap, and exposes the same
  "Move to…" action sheet (native `ActionSheetIOS`/a cross-platform action-sheet
  component) offering the other non-terminal states plus "Mark closed…".
  Moving calls the same `updateApplication` added in task 01's mobile section,
  with the same optimistic-update-then-rollback behavior as web.
- Closed applications: a separate collapsible section or its own screen/tab,
  listing terminal-state applications as a simple list (not a table — phone
  width), same fields as the web closed section.
- A later, purely additive task can add a native long-press drag gesture (e.g.
  via `react-native-draggable-flatlist`) if wanted — not required by this
  ticket's own parity bar.

## Tests

No new backend tests (no backend change). If a frontend test setup exists by the
time this is picked up, cover: grouping applications into the right columns,
optimistic move + rollback on a failed `PATCH`. If no frontend test runner exists
yet in the repo, note that as a gap rather than introducing one as a side effect of
this task. Same applies to mobile — cover the same two behaviors if/when a
mobile test setup exists.
