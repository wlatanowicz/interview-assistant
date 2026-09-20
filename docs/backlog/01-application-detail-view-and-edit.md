---
status: todo
---

# 01 — Application detail view & edit

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Dodanie możliwości otwarcia jednej aplikacji rekrutacyjnej,
zobaczenia wszystkich jej pól i ich edycji — w tym zmiany stanu (`state`) w
pipeline. Dziś API obsługuje tylko tworzenie i listowanie; nic nie da się
zmienić po utworzeniu.

**Dlaczego:** MVP „trackera aplikacji” jest bezużyteczny, jeśli literówka albo
zmiana statusu wymaga usunięcia i ponownego utworzenia wiersza. To także
fundament, na którym każde kolejne zadanie (przeciąganie na kanbanie, kontakty,
oś czasu) buduje swoją funkcję edycji, dlatego jest pierwsze.

**Zakres:** W zakresie: odczyt jednej aplikacji po id, edycja `company`,
`position`, `started_on`, `ad_link`, `state` (dowolny stan, nie tylko
nieterminalny jak przy tworzeniu). Poza zakresem: usuwanie (zadanie 02), pola
szacowanych etapów (zadanie 04), kontakty/oś czasu (kolejne zadania).

## Summary

Add a way to open one job application, see all of its fields, and edit them —
including changing its pipeline `state`. Today the API only supports create and
list; nothing can be changed after creation.

## Why

The MVP "application tracker" is unusable if a typo or a status change requires
deleting and re-creating the row. This is also the foundation every later task
(kanban drag, contacts, timeline) builds its edit affordance on top of, so it goes
first.

## Scope

In: read one application by id, update `company`, `position`, `started_on`,
`ad_link`, `state` (any state, not just non-terminal, unlike create). Out: delete
(task 02), stage estimate fields (task 04), contacts/timeline (later tasks).

## Backend

`backend/src/apps/applications/routes.py`:

- `GET /api/applications/{application_id}` → `JobApplicationPublic`. 404 via new
  `ApiErrorCode.application_not_found` if missing or owned by another user (do not
  distinguish the two cases in the response).
- `PATCH /api/applications/{application_id}` with a new `JobApplicationUpdate`
  Pydantic model — all fields optional:

  ```python
  class JobApplicationUpdate(BaseModel):
      company: str | None = Field(default=None, max_length=255)
      position: str | None = Field(default=None, max_length=255)
      started_on: date | None = None
      ad_link: str | None = Field(default=None, max_length=2048)
      state: ApplicationState | None = None
  ```

  Reuse the `non_empty_stripped` / `strip_ad_link` validators from
  `JobApplicationCreate` (pull them into a shared mixin or module-level function so
  both models call the same code — don't duplicate the validation body).

- Update semantics:
  - Only fields present in the request body are changed (use
    `payload.model_dump(exclude_unset=True)`).
  - `updated_at = datetime.now(UTC)` on every successful update.
  - **Terminal-state invariant** (from `domain-model.md`): if the resulting `state`
    is in `TERMINAL_APPLICATION_STATES` and `finished_on` is not already set,
    set `finished_on = date.today()` automatically. If the resulting `state` moves
    from terminal back to non-terminal, clear `finished_on` to `None`. This mirrors
    the invariant already documented but not yet enforced anywhere in the model.
  - `started_on` cannot be moved later than an existing `finished_on` — return
    `ApiErrorCode.invalid_application_state` (422) if that would happen.
- New error code in `api_errors.py`: `application_not_found`.
- Both endpoints require `get_current_user` and filter by `JobApplication.user_id
  == user.id`, same pattern as `list_applications`.

## Frontend

- `frontend/src/applications/api.ts`: add `getApplication(token, id)` and
  `updateApplication(token, id, payload)` following the existing `fetch` +
  `failureFromBody` pattern.
- `frontend/src/applications/types.ts`: add `JobApplicationUpdatePayload` (all
  fields optional, mirrors the backend model).
- New `frontend/src/applications/ApplicationDetailDrawer.tsx` (Mantine `Drawer`,
  consistent with `NewApplicationModal`'s field set): shows `company`, `position`,
  `started_on`, `ad_link` as editable inputs and `state` as a `Select` offering
  **all** `APPLICATION_STATES` (not just non-terminal — a user must be able to mark
  something rejected/withdrawn/accepted). Save button calls `updateApplication`
  and calls `onUpdated()` to refresh the list; show field errors the same way
  `NewApplicationModal` does today (single `Text c="red"` line from
  `translateApiError`).
- `Dashboard.tsx`: make each `Table.Tr` clickable (row click or a trailing "view"
  icon button) to open `ApplicationDetailDrawer` for that row's application.
- i18n additions (all four locale files) under `applications`: `viewDetails`,
  `save`, `detailsTitle`, plus `errors.applicationNotFound` wired through
  `translateApiError.ts`'s existing error-code → message map.

## Mobile

Ships alongside the web slice above, on top of the scaffold from task 00:

- `mobile/src/api.ts`: add `getApplication`/`updateApplication`, same shapes as
  web's `api.ts`.
- A detail screen (pushed from tapping a row on the Applications list screen
  from task 00) with the same editable fields; `state` via a native picker/
  action sheet listing all `APPLICATION_STATES`.
- Same locale keys as web — task 00 already points the mobile app at the same
  four JSON files, so no separate translation pass is needed here.

## Tests

`backend/src/apps/applications/tests/test_routes.py`:

- `GET` own application succeeds; `GET` another user's application → 404.
- `PATCH` partial update (only `position`) leaves other fields untouched.
- `PATCH` to a terminal state auto-sets `finished_on`; `PATCH` back to
  non-terminal clears it.
- `PATCH` with `started_on` after an existing `finished_on` → 422 with
  `invalid_application_state`.
- `PATCH`/`GET` on a nonexistent id → 404 with `application_not_found`.
