---
status: todo
---

# 04 — Stage estimate & deadline fields

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Dodanie trzech pól „szybkich faktów” zaprojektowanych już w
modelu domenowym, ale pominiętych w pierwszej iteracji implementacji:
`estimated_stage_count`, `estimated_stages` (uporządkowane etykiety) i
`estimated_deadline_on`. Pokazanie ich przy tworzeniu/edycji oraz jako małe
odznaki na karcie kanban.

**Dlaczego:** Model domenowy (`domain-model.md`) definiuje te pola jako
„prawie-MVP” (szybki wskaźnik „~3 rundy”), pomagający kandydatowi ocenić, na
jakim etapie jest, bez otwierania osi czasu. To czysta metadana — żadnej nowej
encji — więc to mały, samodzielny wycinek.

## Summary

Add the three "quick facts" fields the domain model already designs for but that
were left out of the first implementation pass: `estimated_stage_count`,
`estimated_stages` (ordered labels), and `estimated_deadline_on`. Surface them on
create/edit and as small badges on the kanban card.

## Why

Domain model (`domain-model.md`) specifies these as MVP-adjacent fields ("quick
'~3 rounds' indicator") to help a candidate gauge how far along they are without
opening the timeline. They're pure metadata — no new entity — so this is a small,
self-contained slice.

## Data model

`backend/src/apps/applications/models.py`, add to `JobApplication`:

```python
estimated_stage_count: int | None = Field(default=None, ge=0)
estimated_stages: list[str] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
estimated_deadline_on: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
```

(`ge=0` is a Pydantic-level constraint; add a DB `CHECK (estimated_stage_count IS
NULL OR estimated_stage_count >= 0)` in the migration for defense in depth, matching
how other invariants in this app are enforced at the service layer plus DB
constraints where practical per the domain doc.)

Migration (new Alembic revision, chained after `b7e4a1c9023f`):

- `ALTER TABLE job_applications ADD COLUMN estimated_stage_count INTEGER NULL`
- `ADD COLUMN estimated_stages JSONB NULL`
- `ADD COLUMN estimated_deadline_on DATE NULL`
- `ADD CONSTRAINT ck_job_applications_estimated_stage_count CHECK (estimated_stage_count IS NULL OR estimated_stage_count >= 0)`

## Backend

- `JobApplicationPublic`, `JobApplicationCreate`, `JobApplicationUpdate` (task 01):
  add all three fields, optional everywhere.
- Validation:
  - `estimated_stages`, if provided, must be a list of non-empty trimmed strings
    (reuse the trim-and-reject-empty pattern from `non_empty_stripped`, applied
    per-item).
  - `estimated_deadline_on >= started_on` when both are set, else
    `ApiErrorCode.invalid_application_state` (422) — same code family already used
    for cross-field date invariants on this model (see task 01's
    `started_on`/`finished_on` check).
- `_to_public` / update logic: pass the three fields through unchanged (`None` is a
  valid "unknown" state, not "clear on omission" — only clear when the client
  explicitly sends `null` in a `PATCH`, consistent with `exclude_unset` semantics
  from task 01).

## Frontend

- `types.ts`: add the three optional fields to `JobApplication`,
  `JobApplicationCreatePayload`, and `JobApplicationUpdatePayload`.
- `NewApplicationModal.tsx` and `ApplicationDetailDrawer.tsx`: add
  - `NumberInput` for `estimated_stage_count` (min 0),
  - Mantine `TagsInput` for `estimated_stages` (free-entry chips, ordered),
  - a date input for `estimated_deadline_on`.
  Keep these below the existing fields, all optional, no `required` marker.
- `KanbanBoard.tsx` (task 03): show a small badge on the card when
  `estimated_stage_count` or `estimated_stages` is set (e.g. "3 rounds" or the
  first/next unresolved label), and a deadline chip when
  `estimated_deadline_on` is within 14 days (reuse a simple date-diff helper, no
  new dependency).
- i18n additions (all four locale files): `applications.estimatedStageCount`,
  `applications.estimatedStages`, `applications.estimatedDeadline`.

## Mobile

- `mobile/src/types.ts`: same three optional fields.
- Add the equivalent inputs (numeric input, a chip/tag input for
  `estimated_stages`, a native date picker for `estimated_deadline_on`) to the
  mobile create screen (task 00) and detail screen (task 01's mobile section).
- Mobile kanban cards (task 03's mobile section): same "3 rounds" / deadline
  badge treatment as web.

## Tests

- Create/update with all three fields round-trips correctly.
- `estimated_deadline_on` before `started_on` → 422.
- Negative `estimated_stage_count` → 422 (Pydantic-level).
- Omitting the fields on `PATCH` leaves existing values untouched; sending
  `estimated_stages: null` explicitly clears them.
