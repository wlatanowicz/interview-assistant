---
status: todo
---

# 10 — Scheduled email reminders

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Wysyłanie przypomnienia e-mail przed każdym nadchodzącym,
zaplanowanym `ApplicationEvent` (rozmową, telefonem, terminem), z użyciem
istniejącego stosu schedulera i powiadomień, zamiast polegać na tym, że
użytkownik sam sprawdzi widżet z zadania 09.

**Dlaczego:** Druga połowa MVP „systemu przypomnień”, jawnie wymieniona w
dokumencie discovery jako killer feature („przypomnienia follow-up”).
Repozytorium ma już runner zadań cron/interwałowych (`src/scheduler`) i
pipeline szablonowych e-maili (`src/apps/notifications`) zbudowany dla
przepływów autoryzacji — to zadanie podłącza wydarzenia aplikacji do tej
istniejącej infrastruktury, zamiast budować cokolwiek nowego.

**Zakres:** W zakresie: jeden e-mail z przypomnieniem na zaplanowane
wydarzenie, wysłany w ustalonym oknie czasowym przed `occurred_at`, bez
duplikatów. Poza zakresem: konfigurowalny per użytkownika czas wyprzedzenia lub
preferencje rezygnacji, kanały SMS/push — żadne z tych nie jest na liście MVP;
dodać osobne zadanie, jeśli pojawi się taka potrzeba.

## Summary

Send an email reminder ahead of each upcoming scheduled `ApplicationEvent`
(interview, call, deadline) using the existing scheduler + notifications stack,
instead of relying on the user to check the widget from task 09.

## Why

Second half of the MVP "reminder system", and explicitly named as a killer
feature ("follow-up reminders") in the discovery doc. The repo already has a
cron/interval task runner (`src/scheduler`) and a templated-email pipeline
(`src/apps/notifications`) built for auth flows — this task wires application
events into that existing machinery rather than building anything new.

## Scope

In: one reminder email per scheduled event, sent a fixed lookahead window before
`occurred_at`, no duplicates. Out: per-user configurable lead time or
opt-out preferences, SMS/push channels — none of that is in the MVP list; add a
follow-up task if requested later.

## Data model

`backend/src/apps/applications/models.py`, add to `ApplicationEvent`:

```python
reminder_sent_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
```

Migration: `ALTER TABLE application_events ADD COLUMN reminder_sent_at TIMESTAMPTZ NULL`.
This is the dedup marker — without it, a 15-minute periodic tick would re-send the
same reminder on every run while the event stays inside the lookahead window.

## Backend

- `backend/src/config.py`: add `REMINDER_LOOKAHEAD_HOURS = env_str(...)` or a
  simple constant (e.g. `timedelta(hours=24)`) — a fixed 24-hour lookahead is
  enough for MVP; don't build configurability the discovery doc never asked for.
- New `backend/src/apps/notifications/templates/event_reminder.html.tpl` and
  `event_reminder.plain.tpl`, following the existing two-file-per-template
  convention (see `registration_code.*.tpl`). Template variables: `$company`,
  `$position`, `$event_type`, `$occurred_at`, `$notes` (empty string if none).
- `backend/src/apps/notifications/service.py`: add
  `"event_reminder": "Upcoming: ${event_type} — ${company}"`-style entry to
  `_TEMPLATE_SUBJECTS` — actually `_TEMPLATE_SUBJECTS` values are static strings,
  not templated, so use a fixed subject like `"Upcoming interview reminder"` (the
  event-specific detail lives in the body).
- New `backend/src/apps/applications/tasks.py`:

  ```python
  from datetime import UTC, datetime, timedelta
  from src import scheduler
  from src.apps.notifications.service import send_templated_email

  @scheduler.task(queue="MESSAGES", interval=timedelta(minutes=15))
  def send_upcoming_event_reminders() -> None:
      now = datetime.now(UTC)
      window_end = now + timedelta(hours=24)
      # select ApplicationEvent joined to JobApplication and User where
      # outcome == scheduled, reminder_sent_at is null,
      # occurred_at between now and window_end
      # (this is exactly the partial index from task 07)
      for event, application, user in due_events:
          send_templated_email(
              "event_reminder",
              to=user.email,
              context={
                  "company": application.company,
                  "position": application.position,
                  "event_type": event.type.value,
                  "occurred_at": event.occurred_at.isoformat(),
                  "notes": event.notes or "",
              },
              purpose="event_reminder",
          )
          event.reminder_sent_at = now
      # commit once after the loop
  ```

  This is auto-discovered by `bootstrap_task_registry()` (it scans every
  `apps/*/tasks.py`) — no registration step needed beyond creating the file.
- Update the fixture/config that wires cron schedules into whatever deploys this
  (check `backend/src/scheduler/config.py` and any infra script under `scripts/`
  that provisions scheduled tasks) so the new interval task is picked up the same
  way `send_templated_email_task` already is — if tasks are auto-registered from
  the decorator alone with no separate infra step, no extra change is needed;
  confirm by reading how the existing task reaches production before assuming.

## Frontend

None. Confirmed intentionally — this task has no user-facing surface beyond the
email itself; the in-app view is task 09.

## Mobile

None, for the same reason as the web frontend above — this ships an email, not
a screen. (A push-notification channel would be a genuinely new capability, not
a parity gap, and is explicitly deferred as a follow-up in task 00.)

## Tests

`backend/src/apps/applications/tests/test_tasks.py` (or alongside
`notifications/tests/test_service.py`'s pattern):

- An event 12 hours out with `outcome=scheduled` and `reminder_sent_at IS NULL` →
  one email enqueued/sent (assert via the same fake/stub transport
  `notifications/tests` already uses, e.g. `local_eml`), and `reminder_sent_at`
  gets set.
- Running the task twice in a row sends the email only once (dedup via
  `reminder_sent_at`).
- An event outside the lookahead window, already completed/cancelled, or already
  reminded → no email sent.
- Multiple due events across different users each notify the correct user's
  email address.
