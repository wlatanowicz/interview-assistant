---
status: todo
---

# 00 — Mobile app bootstrap (React Native + Expo)

## Summary

Stand up a new Expo (React Native, TypeScript) app that talks to the *same*
backend API as the web frontend, with a working sign-in flow and a navigation
shell mirroring the web app's sections. This is the foundation every later
ticket's "Mobile" section builds on — nothing else can ship on mobile before
this exists.

## Why

Product decision (2026-09-17, see `discovery_summary.md`): mobile starts ASAP,
and every feature built for web from now on ships on mobile at the same time.
That parity requirement is meaningless without an app to put features into, so
this is inserted at the front of the execution order (`00`, ahead of `01`) even
though it ships zero net-new product features itself.

## Scope

In: Expo app scaffold, shared API client talking to the existing FastAPI
backend, email/password + email-code sign-in and registration (the flows that
are plain JSON today), secure token storage, a bottom-tab navigation shell with
placeholder/real screens for each existing web section, i18n wired to the same
locale strings as web, and a read+create Applications screen matching what's
*actually* shipped on web today (list + create only — see `82d6d38`).

Out (explicit follow-ups, not silently promised here):

- **Google/Facebook OAuth sign-in.** `backend/src/apps/users/oauth.py` completes
  a successful login by redirecting the browser to
  `AUTH_FRONTEND_URL#access_token=...&token_type=bearer` — a web-only pattern
  (URL fragment read by frontend JS). A native app can't consume that as-is; it
  needs either an Expo `AuthSession` proxy flow or a registered deep-link scheme
  (`interviewassistant://auth-callback#...`) accepted as a valid redirect target
  server-side. Ship email/password + code first; file OAuth as its own ticket
  once the redirect strategy is picked.
- Push notifications, offline support/caching, app-store signing & submission
  (Apple Developer / Play Console accounts, bundle identifiers, store listings)
  — each is its own project once the app has real features to publish.
- Every feature beyond what's already on web (kanban, contacts, timeline,
  reminders, analytics, AI prep) — those land per their own ticket's new
  "Mobile" section (01–12), not here.

## Setup

- New top-level `mobile/` package (sibling to `backend/` and `frontend/`):
  `npx create-expo-app` with the TypeScript template, Expo Router or React
  Navigation for the tab shell (pick one and note the choice in this file once
  decided — don't leave both half-wired).
- `mobile/src/api.ts`: same shape as `frontend/src/api.ts` (a thin fetch wrapper
  keyed off a configurable API base URL — `EXPO_PUBLIC_API_URL` via Expo's env
  var convention, not a hardcoded host, since it must point at a dev machine's
  LAN IP or a real backend depending on how it's run).
- Token storage: `expo-secure-store` (Keychain/Keystore-backed), not
  `AsyncStorage`, since this holds a bearer token.
- Auth screens: sign in, register (send-code → verify-code → complete), password
  recovery (send-code → verify-code → complete) — all hitting the existing
  `/api/auth/*` JSON endpoints from `backend/src/apps/users/routes.py`, no
  backend changes needed for this slice.
- Navigation shell: bottom tabs for "Applications" (real screen, see below) and
  placeholder screens for "Contacts" and "Analytics" (empty "coming soon" state)
  so the shell already has the slots tasks 05 and 11 will fill in, rather than
  restructuring navigation later.
- Applications screen: list (`GET /api/applications`) + a create form (`POST
  /api/applications`) matching the fields the web `NewApplicationModal`
  collects today (`company`, `position`, `started_on`, `ad_link`, `state`
  restricted to non-terminal on create, per the existing backend validation).
  No edit/delete/kanban yet — those are tasks 01–03's mobile sections once this
  scaffold exists.
- i18n: `i18next` + `react-i18next` work in React Native; point the mobile app
  at the same four locale JSON files as web (`en`, `de`, `pl`, `uk`) — as a
  symlink/shared package if the monorepo tooling supports it easily, or as a
  duplicated copy kept in sync manually if not (note here which was chosen once
  decided; don't let the two copies silently drift without at least a comment
  pointing at the source of truth).

## Tests

No dedicated mobile test framework exists yet (matching the web frontend's
current state — no frontend test runner in the repo per the README's
cross-cutting conventions). Manual verification for this ticket: app builds and
runs in Expo Go / a simulator, sign-in/register/password-recovery flows work
end-to-end against a running backend, and the Applications list/create screen
round-trips against a real dev database.

## Follow-ups this ticket deliberately defers

- OAuth sign-in on mobile (needs the deep-link redirect decision above).
- App-store distribution (signing, bundle IDs, TestFlight/Play internal
  testing, store listings).
- Push notifications for the reminder system (task 10 ships email only; a push
  channel would be a separate ticket building on this scaffold).
