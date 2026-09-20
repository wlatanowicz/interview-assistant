---
status: todo
---

# 05 — Contacts directory

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Wprowadzenie encji `Contact` z modelu domenowego: przypisanej
do użytkownika książki kontaktów rekruterów, hiring managerów i innych osób
poznanych podczas szukania pracy. Dostarczone jako samodzielna funkcja CRUD
(lista, tworzenie, edycja, usuwanie) z własną zakładką — jeszcze niepowiązana z
aplikacjami ani wydarzeniami (to zadania 06 i 08).

**Dlaczego:** „Kontakty firmowe i rekruterów” to samodzielny filar MVP.
Zbudowanie tego najpierw jako samodzielnej funkcji (zamiast doczepienia do
formularza aplikacji) utrzymuje to zadanie w małym rozmiarze i daje zadaniu 06
gotowy selektor do podłączenia.

## Summary

Introduce the `Contact` entity from the domain model: a user-scoped rolodex of
recruiters, hiring managers, and other people met during the job search. Ship as a
standalone CRUD feature (list, create, edit, delete) with its own tab — not yet
linked to applications or events (that's tasks 06 and 08).

## Why

"Company & recruiter contacts" is an MVP pillar in its own right. Building it
standalone first (rather than bolted onto the application form) keeps this task
small and gives task 06 a finished picker to link against.

## Data model

New `backend/src/apps/contacts/` package (own app module, per the domain doc's
suggestion once the surface grows beyond a couple of fields):

- `backend/src/apps/contacts/models.py`:

  ```python
  class Contact(SQLModel, table=True):
      __tablename__ = "contacts"
      __table_args__ = (Index("ix_contacts_user_id_name", "user_id", "name"),)

      id: UUID = Field(default_factory=uuid4, primary_key=True)
      user_id: UUID = Field(foreign_key="users.id", index=True)
      name: str = Field(max_length=255)
      emails: list[str] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
      phones: list[str] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
      company: str | None = Field(default=None, max_length=255)
      job_title: str | None = Field(default=None, max_length=255)
      notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
      created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
      updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
  ```

- Migration: create `contacts` table + `(user_id)` and `(user_id, name)` indexes,
  per the indexing strategy in `domain-model.md`. Register `Contact` in
  `backend/alembic/env.py` alongside the existing model imports.

## Backend

`backend/src/apps/contacts/routes.py`, `api_errors.py` (new: `contact_not_found`),
`tests/` — mirror the `applications` app's structure exactly:

- `GET /api/contacts` → `{ contacts: ContactPublic[] }`, ordered by `name` asc,
  scoped to `user.id`.
- `POST /api/contacts` → `ContactPublic`, 201. Body: `name` (required,
  non-empty-after-trim, reuse the trim validator), `emails`/`phones` (optional
  list of strings — validate each email with a simple regex/`EmailStr`-style
  check and reject obviously-invalid entries with a 422; phone entries just
  trimmed, no strict E.164 enforcement for MVP per the domain doc's "preferred,
  not required" note), `company`, `job_title`, `notes` all optional.
- `GET /api/contacts/{id}`, `PATCH /api/contacts/{id}` (partial update, same
  `exclude_unset` pattern as applications), `DELETE /api/contacts/{id}` → 204.
- All four scoped by `user_id`; 404 via `contact_not_found` otherwise.
- Register the new router in the FastAPI app alongside the existing
  `applications` router (wherever that's wired — same file/pattern).

## Frontend

- New `frontend/src/contacts/` mirroring `frontend/src/applications/`:
  `types.ts`, `api.ts` (`listContacts`, `createContact`, `updateContact`,
  `deleteContact`), `ContactsPage.tsx` (table: name, company, job title, primary
  email/phone, edit/delete actions), `ContactFormModal.tsx` (create/edit, reused
  for both via an optional `contact` prop like `ApplicationDetailDrawer`'s pattern
  once task 01 exists).
- **Navigation**: this is the first task that needs more than one top-level
  section. Add a Mantine `Tabs` to `App.tsx` with "Applications" (existing
  `Dashboard`) and "Contacts" (`ContactsPage`) tabs — no router library needed for
  two tabs; introduce `react-router` only if a later task needs deep-linkable
  URLs, which none currently do.
- `emails`/`phones` inputs: `TagsInput` (same component chosen for
  `estimated_stages` in task 04), one for emails one for phones.
- i18n additions (all four locale files), new top-level `contacts` namespace:
  `title`, `new`, `newTitle`, `name`, `emails`, `phones`, `company`, `jobTitle`,
  `notes`, `save`, `cancel`, `delete`, `deleteConfirmTitle`, `empty`, plus
  `errors.contactNotFound`.

## Mobile

Fills in the "Contacts" tab placeholder left by task 00's navigation shell:

- `mobile/src/contacts/` mirroring the web module: `types.ts`, `api.ts`, a list
  screen, and a create/edit form screen (push navigation rather than a modal,
  matching how task 01's mobile detail screen is structured).
- Same field set and validation as web (`name` required, `emails`/`phones` as
  chip inputs, `company`, `job_title`, `notes`).
- Same locale keys as web (already shared per task 00).

## Tests

- Create/list/get/update/delete happy paths, scoped-per-user isolation (mirror
  the existing `test_users_cannot_see_other_users_applications` test).
- Empty `name` → 422. Malformed email in `emails` → 422.
- `PATCH` partial update leaves other fields untouched; explicit `null` clears an
  optional field.
