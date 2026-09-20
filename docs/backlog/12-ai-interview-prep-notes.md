---
status: todo
---

# 12 — AI interview prep notes

## Podsumowanie (PL)

*Wersja angielska jest wiążąca do budowy aplikacji; ta sekcja istnieje wyłącznie
dla wygody utrzymania backlogu.*

**Streszczenie:** Dla danego nadchodzącego wydarzenia typu rozmowa
kwalifikacyjna, wygenerowanie krótkiej listy przygotowawczej (prawdopodobne
tematy, mądre pytania do zadania, kątów specyficznych dla firmy) przez
wywołanie LLM, i umożliwienie użytkownikowi zapisania wyniku w notatkach tego
wydarzenia.

**Dlaczego:** „Przygotowanie do rozmowy z AI” jest wymienione jako killer
feature w dokumencie discovery. Zaplanowane na koniec, ponieważ — inaczej niż
każde wcześniejsze zadanie — wymaga zupełnie nowej zdolności, której w kodzie
jeszcze nie ma: integracji z zewnętrznym dostawcą LLM — więc niesie więcej
ryzyka wdrożeniowego (nowa zależność, nowy sekret, nowa powierzchnia kosztowa)
niż zadania w stylu CRUD wcześniej. Potwierdzić budżet/wybór dostawcy przed
rozpoczęciem.

**Zakres:** W zakresie: jeden endpoint, który przyjmuje wydarzenie wraz z
kontekstem jego aplikacji i zwraca wygenerowany tekst; akcja „Wygeneruj notatki
przygotowawcze” w formularzu wydarzenia, wypełniająca pole notatek (użytkownik
nadal jawnie zapisuje — nigdy automatyczny zapis bez przeglądu). Poza zakresem:
rozmowa w stylu czatu, odpowiedzi strumieniowe, wieloetapowy coaching rozmów
kwalifikacyjnych — wszystko to zbyt duże jak na „killer feature #5 na liście
MVP”; wrócić do tego jako osobna inicjatywa, jeśli to się sprawdzi.

## Summary

For a given upcoming interview-type event, generate a short prep checklist (likely
topics, smart questions to ask, company-specific angles) via an LLM call, and let
the user save the result into that event's notes.

## Why

"AI interview preparation" is named as a killer feature in the discovery doc. It's
sequenced last because, unlike every earlier task, it needs a genuinely new
capability the codebase doesn't have yet — an outbound LLM provider integration —
so it carries more setup risk (new dependency, new secret, new cost surface) than
the CRUD-shaped tasks before it. Confirm budget/provider choice before starting.

## Scope

In: one endpoint that takes an event + its application context and returns
generated text; a "Generate prep notes" action in the event form that fills the
notes field (user still explicitly saves — never auto-write without review). Out:
chat-style follow-up, streaming responses, multi-turn interview coaching — all
bigger than "killer feature #5 in an MVP list" warrants; revisit as a separate
initiative if this lands well.

## New dependency & config

- Add an Anthropic SDK dependency to `backend/pyproject.toml` (`anthropic`),
  matching the version pinning style already used for other deps
  (`>=X.Y.Z,<N`).
- `backend/src/config.py`: add `ANTHROPIC_API_KEY = env_str("ANTHROPIC_API_KEY",
  default=None)`, following the existing `env_str`/`env_list` pattern (see
  `DATABASE_URL`).
- New `backend/src/apps/applications/ai_prep.py`: a thin wrapper function
  `generate_prep_notes(*, company, position, event_type, existing_notes) -> str`
  that builds a single prompt (short, deterministic instructions — "generate a
  bullet list of likely topics and 3 questions to ask", cap output length) and
  calls the Anthropic Messages API once, non-streaming. If `ANTHROPIC_API_KEY` is
  unset, raise a clear internal error the route below turns into a 503 (same
  shape as the existing `database_not_configured` handling for
  `DATABASE_URL` — mirror that pattern for a missing API key rather than
  inventing a new style).

## Backend

`backend/src/apps/applications/routes.py`:

- `POST /api/events/{event_id}/prep` → `{ "prep_notes": "..." }`. Loads the event
  and its parent `JobApplication` (scoped to `user.id`, 404
  `event_not_found` otherwise, from task 07). Calls `generate_prep_notes(...)`
  with `company`, `position` from the application and `event.type` /
  `event.notes` for context. Returns the generated text; **does not** write it to
  the event — saving is a normal `PATCH /api/events/{event_id}` call the frontend
  makes afterward with the user's (possibly edited) text, reusing task 07's
  existing endpoint rather than adding a second write path.
- New `ApiErrorCode.ai_provider_not_configured` (503) and
  `ApiErrorCode.ai_provider_error` (502, for upstream failures/timeouts — set a
  short client timeout, e.g. 20s, and don't retry automatically from within the
  request/response cycle; this is a synchronous user-initiated action, not a
  background task).
- Rate-limit lightly at the application layer if easy (e.g. reject if called more
  than N times per minute per user) — optional, note as a follow-up if it doesn't
  fit the task cleanly, since an unauthenticated-cost surface on a paid API is a
  real risk worth flagging even if not solved here.

## Frontend

- `api.ts`: `generatePrepNotes(token, eventId)`.
- `EventFormModal.tsx` (task 07): show a "Generate prep notes ✨" button, enabled
  only for interview-shaped event types (`phone_call`, `video_call`,
  `interview_meeting`) and only when the event is `scheduled`/future. On click,
  call the endpoint, populate (or append to, if notes already exist — ask before
  overwriting) the notes `Textarea`, and let the user edit before hitting the
  form's existing "Save" button — no separate save action for the AI output.
  Show a loading state and the standard error-translation pattern on failure.
- i18n additions (all four locale files): `events.generatePrepNotes`,
  `events.generatingPrepNotes`, `events.prepNotesOverwriteConfirm`, plus
  `errors.aiProviderNotConfigured`, `errors.aiProviderError`.

## Mobile

- `mobile/src/api.ts`: `generatePrepNotes`.
- Same "Generate prep notes ✨" action on the mobile event form screen (task
  07's mobile section), same eligibility rule (interview-shaped, scheduled/
  future events only), same overwrite confirmation via `Alert.alert` before
  replacing existing notes, same loading/error handling as web.

## Tests

- With `ANTHROPIC_API_KEY` unset, the endpoint returns 503
  `ai_provider_not_configured` (mock/patch the config value in the test, don't
  require a real key in CI).
- With the provider client mocked, a successful call returns the generated text
  and does not modify the event's stored `notes`.
- Simulated upstream error/timeout → 502 `ai_provider_error`.
- Endpoint is scoped like every other event route: another user's event → 404.
- No real network calls in the test suite — the Anthropic client must be mocked
  at the boundary (`ai_prep.py`'s call site), matching how `notifications/tests`
  already avoids hitting a real email transport in CI.
