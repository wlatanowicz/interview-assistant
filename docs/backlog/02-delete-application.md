---
status: todo
---

# 02 — Delete an application

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Umożliwienie użytkownikowi trwałego usunięcia aplikacji
rekrutacyjnej dodanej przez pomyłkę (duplikat, zła firma, wpis testowy). To
twarde usunięcie, różne od oznaczenia aplikacji jako `withdrawn` (co zachowuje
historię i odbywa się przez edycję stanu z zadania 01).

**Dlaczego:** Bez tego pomyłki gromadzą się w trackerze bez możliwości poprawy.
Zadanie małe i samodzielne, potrzebne zanim board z zadania 03 zacznie zbierać
realne dane użytkowe.

**Zakres:** W zakresie: endpoint `DELETE`, interfejs potwierdzenia. Poza
zakresem: usuwanie masowe, miękkie usuwanie/cofnięcie (nie wymagane przez
dokument discovery; dodać tylko jeśli zapotrzebuje na to kolejne zadanie).

## Summary

Let a user permanently remove a job application they added by mistake (duplicate,
wrong company, test entry). This is a hard delete, distinct from marking an
application `withdrawn` (which keeps history and is done via the state edit from
task 01).

## Why

Without it, mistakes accumulate forever in the tracker with no correction path.
Small, self-contained, and needed before task 03's board gets real usage data.

## Scope

In: `DELETE` endpoint, confirmation UI. Out: bulk delete, soft delete/undo (not
requested by the discovery doc; add only if a later task needs it).

## Backend

`backend/src/apps/applications/routes.py`:

- `DELETE /api/applications/{application_id}` → `204 No Content`. Scoped by
  `user_id` like the other endpoints; 404 via `ApiErrorCode.application_not_found`
  (added in task 01) if missing or not owned by the caller.
- `session.delete(application)` then `session.flush()`. No response body.

Note for later tasks: once `ApplicationEvent` exists (task 07) with a
`job_application_id` foreign key, that FK must be declared
`ondelete="CASCADE"` (and the SQLModel relationship configured to match) so
deleting an application here also removes its timeline — call this out again in
task 07 rather than retrofitting it later.

## Frontend

- `frontend/src/applications/api.ts`: add `deleteApplication(token, id)` — `DELETE`
  request, returns `{ ok: true }` on 204 or the standard `ApiFailure` shape
  otherwise.
- `ApplicationDetailDrawer.tsx` (from task 01): add a "Delete" button, styled
  `color="red" variant="subtle"`, that opens a Mantine `Modal`/`modals.openConfirmModal`
  asking for confirmation ("Delete this application? This cannot be undone."). On
  confirm, call `deleteApplication`, close the drawer, and refresh the dashboard
  list.
- i18n additions (all four locale files): `applications.delete`,
  `applications.deleteConfirmTitle`, `applications.deleteConfirmBody`.

## Mobile

- `mobile/src/api.ts`: add `deleteApplication`.
- Delete action on the detail screen from task 01's mobile section (button or
  swipe-to-delete on the Applications list row), confirmed via `Alert.alert`
  (native equivalent of Mantine's confirm modal) rather than a custom dialog.

## Tests

- `DELETE` own application → 204, subsequent `GET` on it → 404.
- `DELETE` another user's application → 404, and the row still exists for its
  owner afterward.
- `DELETE` nonexistent id → 404.
