---
status: todo
---

# 08 — Event participants

## Summary

Add the `ApplicationEventContact` junction table so an event can list which
contacts were involved (e.g. a panel interview with two interviewers), and let the
timeline UI show/edit that list.

## Why

Domain model calls this out as a distinct many-to-many relationship, separate from
`primary_contact_id`. Kept as its own task after task 07 so the timeline CRUD
lands first without being entangled with a junction-table editor.

## Data model

`backend/src/apps/applications/models.py`:

```python
class ApplicationEventContact(SQLModel, table=True):
    __tablename__ = "application_event_contacts"

    application_event_id: UUID = Field(foreign_key="application_events.id", primary_key=True)
    contact_id: UUID = Field(foreign_key="contacts.id", primary_key=True)
```

Migration:

- Create `application_event_contacts` with composite PK
  `(application_event_id, contact_id)`, FK on `application_event_id` with
  `ON DELETE CASCADE` (deleting an event drops its participant rows) and FK on
  `contact_id` with `ON DELETE CASCADE` (deleting a contact drops them from any
  event's participant list — unlike `primary_contact_id`'s `SET NULL`, there's no
  nullable column here to fall back to).
- Per the domain doc's indexing strategy: index on `application_event_id` (mostly
  covered by the PK's leading column, but add if the query planner needs the
  reverse) and an explicit index on `contact_id` for "this contact's activity
  history" lookups.
- Register `ApplicationEventContact` in `backend/alembic/env.py`.

## Backend

- `EventPublic` (task 07): add `contact_ids: list[UUID]` (or a light
  `ContactSummary` list if the join is cheap given how task 06 was implemented —
  keep it consistent with whatever choice was made there).
- `PUT /api/events/{event_id}/contacts` — replaces the full participant list in
  one call (matches the domain doc's suggested endpoint shape). Body:
  `{ "contact_ids": ["...", "..."] }`. Validate every id exists and belongs to
  `user.id` (422 `contact_not_found` otherwise, same code from task 05/06);
  diff against existing rows and insert/delete only what changed (or simplest:
  delete-all-then-insert inside one transaction — fine at this scale, note the
  simplification rather than hiding it).
- Include `contact_ids`/participant summaries in the `GET`/`POST`/`PATCH` event
  responses from task 07 so the frontend doesn't need a separate fetch per event.

## Frontend

- `EventFormModal.tsx` (task 07): add a multi-select (`MultiSelect` or
  `TagsInput`-with-existing-options) sourced from `listContacts`, labeled
  "Participants". On save, call the event create/update first, then
  `PUT /events/{id}/contacts` with the selected ids (two calls is fine for a
  form submit; don't over-engineer into a single combined endpoint).
- `TimelineSection.tsx` (task 07): show participant names as small chips under
  each event row.
- i18n additions (all four locale files): `events.participants`,
  `events.noParticipants`.

## Tests

- `PUT` participants with a mix of valid own-contact ids → event now reports
  them; calling again with a different set fully replaces the previous list.
- `PUT` including another user's contact id → 422 `contact_not_found`, and the
  previously-set list is unchanged (the whole request fails atomically — no
  partial replace).
- Deleting a contact removes it from any event's participant list without
  deleting the event.
- Deleting an event removes its junction rows (no orphaned
  `application_event_contacts`).
