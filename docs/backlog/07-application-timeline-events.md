---
status: todo
---

# 07 — Application timeline (events)

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Implementacja `ApplicationEvent` z modelu domenowego:
append-only oś czasu punktów kontaktu (rozmowy, spotkania rekrutacyjne,
zadania domowe, notatki — przeszłe lub zaplanowane) przypisanych do jednej
aplikacji. Dostarczenie pełnego CRUD wraz z sekcją osi czasu w panelu
szczegółów.

**Dlaczego:** „Notatki z rozmów” to filar MVP, a dokument discovery traktuje oś
czasu jako źródło prawdy („stan odpowiada na pytanie »na jakim jestem etapie«,
wydarzenia odpowiadają na »co się wydarzyło«”). Kontakty (zadania 05/06)
istnieją wcześniej, aby wydarzenie mogło opcjonalnie wskazać, kto brał udział —
pełne powiązanie uczestników to zadanie 08, celowo wydzielone, by ograniczyć
rozmiar tego zadania.

## Summary

Implement `ApplicationEvent` from the domain model: the append-only timeline of
touchpoints (calls, interviews, take-homes, notes — past or scheduled) attached to
one application. Ship full CRUD plus a timeline section in the detail drawer.

## Why

"Interview notes" is an MVP pillar and the domain doc treats the timeline as the
system of record ("state answers 'where am I now', events answer 'what
happened'"). Contacts (task 05/06) exist first so an event can optionally note who
was involved — full participant linking is task 08, kept separate to bound this
task's size.

## Data model

`backend/src/apps/applications/models.py` (same app package — the domain doc
allows this), add:

```python
class EventType(enum.StrEnum):
    application_sent = "application_sent"
    application_updated = "application_updated"
    recruiter_outreach = "recruiter_outreach"
    phone_call = "phone_call"
    video_call = "video_call"
    interview_meeting = "interview_meeting"
    online_test_submission = "online_test_submission"
    take_home_received = "take_home_received"
    take_home_submitted = "take_home_submitted"
    reference_check = "reference_check"
    offer_received = "offer_received"
    offer_accepted = "offer_accepted"
    offer_declined = "offer_declined"
    rejection_received = "rejection_received"
    follow_up_sent = "follow_up_sent"
    note = "note"

class EventOutcome(enum.StrEnum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class ApplicationEvent(SQLModel, table=True):
    __tablename__ = "application_events"
    __table_args__ = (
        Index("ix_application_events_job_application_id_occurred_at", "job_application_id", "occurred_at"),
        Index(
            "ix_application_events_user_id_occurred_at_scheduled",
            "user_id", "occurred_at",
            postgresql_where=text("outcome = 'scheduled'"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)  # denormalized, per domain-model.md
    job_application_id: UUID = Field(foreign_key="job_applications.id")
    occurred_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    type: EventType = Field(sa_column=Column(to_sql_enum(EventType, name="eventtype"), nullable=False))
    outcome: EventOutcome | None = Field(default=None, sa_column=Column(to_sql_enum(EventOutcome, name="eventoutcome"), nullable=True))
    title: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    duration_minutes: int | None = Field(default=None, ge=0)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
```

Migration:

- Create `eventtype`, `eventoutcome` Postgres enums and the `application_events`
  table with both indexes above (the partial index on `outcome = 'scheduled'`
  is exactly the "upcoming reminders" index called out in the domain doc — build
  it now so task 09 doesn't need its own migration).
- `job_application_id` FK: `ON DELETE CASCADE` — per the note left in task 02,
  deleting an application removes its timeline.
- Register `ApplicationEvent` in `backend/alembic/env.py`.

## Backend

`backend/src/apps/applications/routes.py` (or split into
`applications/events_routes.py` if the file is getting long — either is fine, keep
the router prefix as below):

- `GET /api/applications/{application_id}/events` → list, scoped to the
  application **and** `user.id`, ordered `occurred_at desc`. 404
  `application_not_found` if the application doesn't exist/isn't owned.
- `POST /api/applications/{application_id}/events` → `EventPublic`, 201. Body:
  `occurred_at` (required), `type` (required), `outcome`, `title`, `notes`,
  `duration_minutes` (all optional). Set `user_id` from the authenticated user
  (not from the client) even though it's denormalized onto the row.
- `GET /api/events/{event_id}`, `PATCH /api/events/{event_id}` (partial update,
  `exclude_unset`), `DELETE /api/events/{event_id}` → 204. All scoped by
  `user_id`; new `ApiErrorCode.event_not_found` (404) otherwise.
- Optional suggestion behavior from the domain doc ("may **suggest** state
  changes... must not auto-overwrite"): when creating an event whose `type` maps
  to an obvious state (`offer_received` → `offer`, `rejection_received` →
  `rejected`), include a `suggested_state: ApplicationState | None` field in the
  `EventPublic` response so the frontend can prompt — do **not** change
  `JobApplication.state` server-side. Keep the mapping to a small module-level
  dict of the few unambiguous cases; skip ambiguous ones (e.g. `phone_call`
  isn't a state) rather than guessing.

## Frontend

- `frontend/src/applications/eventTypes.ts` (or inline in `types.ts`): the
  `EventType`/`EventOutcome` literal unions + display order.
- `api.ts`: `listEvents`, `createEvent`, `updateEvent`, `deleteEvent`.
- New `frontend/src/applications/TimelineSection.tsx`, rendered inside
  `ApplicationDetailDrawer` (task 01): chronological list (most recent first),
  each row showing type label, date/time, outcome badge, duration, notes
  (truncated with expand); "Add event" button opens `EventFormModal.tsx`
  (type `Select`, datetime input, outcome `Select`, title, notes `Textarea`,
  duration `NumberInput`); edit/delete affordances per row matching the
  application delete pattern from task 02 (confirm modal on delete).
- When a create/update response includes `suggested_state`, show a small inline
  banner ("Mark this application as **Offer**?" with an "Update" button that
  calls `updateApplication` from task 01) rather than a blocking modal.
- i18n additions (all four locale files), new `events` namespace: `title`, `new`,
  `newTitle`, `type`, `occurredAt`, `outcome`, `titleField`, `notes`,
  `durationMinutes`, `save`, `cancel`, `delete`, `deleteConfirmTitle`, `empty`,
  `suggestStatePrompt`, plus enum label sub-namespaces `events.types.*` and
  `events.outcomes.*` for every value listed above, and
  `errors.eventNotFound`.

## Mobile

- `mobile/src/api.ts`: `listEvents`, `createEvent`, `updateEvent`,
  `deleteEvent`.
- A timeline section on the mobile detail screen (task 01), same
  chronological list; "Add event" pushes an event form screen (type picker,
  native date/time picker, outcome picker, title, notes, duration) rather than
  a modal.
- Same `suggested_state` inline banner treatment as web, wired to the mobile
  `updateApplication` call from task 01's mobile section.
- Same locale keys as web (shared per task 00).

## Tests

- Create/list/get/update/delete happy paths, scoped per application and per user.
- Events for another user's application → 404 on every sub-route.
- Deleting a `JobApplication` cascades and removes its events (verify via direct
  DB check like `test_active_filter_excludes_finished_applications` does).
- `offer_received` event creation returns `suggested_state: "offer"`; a `type`
  with no mapping (e.g. `phone_call`) returns `suggested_state: null`.
