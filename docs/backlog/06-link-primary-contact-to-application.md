---
status: todo
---

# 06 — Link a primary contact to an application

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Dodanie `JobApplication.primary_contact_id`, umożliwiające
wybór, który `Contact` (z zadania 05) jest głównym rekruterem/osobą kontaktową
dla danej roli, oraz pokazanie tego powiązania na karcie i w panelu szczegółów.

**Dlaczego:** Model domenowy jawnie definiuje ten klucz obcy
(`JobApplication.primary_contact_id`, „domyślny rekruter / właściciel HR dla
danej roli”). To najtańszy sposób połączenia dwóch encji przed większą pracą
nad uczestnikami wydarzeń w zadaniu 08.

## Summary

Add `JobApplication.primary_contact_id`, letting a user pick which `Contact` (from
task 05) is the main recruiter/point of contact for a given role, and show that
link on the card and detail drawer.

## Why

Domain model defines this FK explicitly (`JobApplication.primary_contact_id`,
"Default recruiter / HR owner for the role"). It's the cheapest way to connect the
two entities before the bigger timeline-participants work in task 08.

## Data model

`backend/src/apps/applications/models.py`:

```python
primary_contact_id: UUID | None = Field(default=None, foreign_key="contacts.id")
```

Migration: `ALTER TABLE job_applications ADD COLUMN primary_contact_id UUID NULL`,
`ADD CONSTRAINT fk_job_applications_primary_contact FOREIGN KEY (primary_contact_id)
REFERENCES contacts(id) ON DELETE SET NULL` (deleting a contact shouldn't delete or
break the application — just clear the reference), plus an index on the column
since it'll be used for joins/filters.

Depends on task 05 (the `contacts` table must exist first).

## Backend

- `JobApplicationPublic`, `JobApplicationCreate`, `JobApplicationUpdate`: add
  `primary_contact_id: UUID | None`.
- On create/update, if `primary_contact_id` is provided, verify a `Contact` with
  that id exists **and belongs to `user.id`** before saving — cross-tenant or
  nonexistent id → `ApiErrorCode.contact_not_found` (422, not 404, since it's a
  field on the applications endpoint — follow the existing convention where
  cross-entity validation errors on this router return 422 with a specific code,
  e.g. `invalid_application_state`'s usage).
- Consider (and implement if trivial given the ORM setup) embedding a lightweight
  `primary_contact: ContactSummary | None` (`id`, `name`, `company`) in
  `JobApplicationPublic` via a join, so the frontend doesn't need a second request
  per card to show the contact's name. If that join is awkward with the current
  session/response pattern, ship with just `primary_contact_id` and let the
  frontend resolve names from the already-fetched contacts list (acceptable since
  `ContactsPage` already fetches everything, and the number of contacts is small
  per user) — pick whichever keeps this task small; note the choice in the PR
  description.

## Frontend

- `types.ts`: add `primary_contact_id: string | null` to `JobApplication`,
  `JobApplicationCreatePayload`, `JobApplicationUpdatePayload`.
- `NewApplicationModal.tsx` / `ApplicationDetailDrawer.tsx`: add a `Select`
  (searchable) populated from `listContacts`, labeled "Primary contact", with an
  option to clear it. Loading the contacts list here is a new dependency of the
  applications feature on the contacts feature — fetch once when the modal/drawer
  opens.
- `KanbanBoard.tsx` card: show the linked contact's name as a small subtitle when
  set.
- `ContactsPage.tsx`: no change required for this task (reverse lookup —
  "applications this contact is linked to" — is a nice-to-have, not required by
  the domain doc's MVP shape; skip unless it's essentially free once the join
  above exists).
- i18n additions (all four locale files): `applications.primaryContact`,
  `applications.noPrimaryContact`.

## Mobile

- Add the same searchable contact picker to the mobile create screen (task 00)
  and detail screen (task 01's mobile section), sourced from the mobile
  Contacts list (task 05's mobile section).
- Show the linked contact's name as a subtitle on mobile kanban cards (task
  03's mobile section) and on the Applications list row.

## Tests

- Create/update an application with a valid own contact id → succeeds, returned
  in the response.
- Create/update with another user's contact id → 422 `contact_not_found`.
- Create/update with a nonexistent contact id → 422 `contact_not_found`.
- Deleting a contact that's referenced as a primary contact → application still
  loads afterward with `primary_contact_id: null`.
