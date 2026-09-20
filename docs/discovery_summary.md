# Candidate Recruitment Assistant ("Job Search OS")

## Vision

A personal CRM that helps candidates organize, automate, and optimize
their job search.

## Problem

Candidates manage applications using spreadsheets, email, calendars, and
notes.

## Existing Solutions

-   Employer-focused ATS platforms
-   LinkedIn / Indeed
-   DIY spreadsheets and Notion

## Opportunity

Become the operating system for job seekers.

## MVP

-   Application tracker
-   Kanban pipeline
-   Interview notes
-   Reminder system
-   Company & recruiter contacts

Technical domain design: [Core domain model](domain-model.md) (`JobApplication`,
`ApplicationEvent`, `Contact`).

## Platforms

-   Web (React) — existing, primary surface today.
-   Native iOS/Android apps (React Native + Expo), against the same backend API.

Decision (2026-09-17): mobile development starts immediately, and from now on
every feature built for web ships on mobile at the same time — not staggered,
not a reduced subset. See [`backlog/00-mobile-app-bootstrap.md`](backlog/00-mobile-app-bootstrap.md)
for the scaffold this depends on and [`backlog/README.md`](backlog/README.md)
for how this changes every other ticket.

## Killer Features

-   Email parsing
-   Automatic interview detection
-   Follow-up reminders
-   Analytics (response, interview, offer rates)
-   AI interview preparation

## Future Features

-   Resume tailoring
-   Salary benchmarking
-   Recruiter relationship management
-   Career history
-   AI career coach

## Challenges

-   Retention after users find a job

## Validation

Recruit 10--20 active job seekers and observe whether they replace
spreadsheets with the app.
