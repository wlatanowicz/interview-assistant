from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from src.apps.applications.models import ApplicationState, JobApplication
from src.apps.users.tests.helpers import register_user
from src.utils.db import session_scope


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_list_applications_requires_auth(auth_client) -> None:
    r = auth_client.get("/api/applications")
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "not_authenticated"


def test_create_and_list_active_applications(auth_client) -> None:
    user = register_user(auth_client, "apps@example.com", "password123456")
    token = user["access_token"]
    headers = _auth_header(token)

    create = auth_client.post(
        "/api/applications",
        headers=headers,
        json={
            "company": "Acme Corp",
            "position": "Software Engineer",
            "started_on": "2026-07-01",
            "state": "applied",
            "ad_link": "https://example.com/jobs/1",
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["company"] == "Acme Corp"
    assert body["position"] == "Software Engineer"
    assert body["state"] == "applied"
    assert body["started_on"] == "2026-07-01"
    assert body["finished_on"] is None
    assert body["ad_link"] == "https://example.com/jobs/1"
    assert "id" in body

    listed = auth_client.get("/api/applications?active=true", headers=headers)
    assert listed.status_code == 200
    apps = listed.json()["applications"]
    assert len(apps) == 1
    assert apps[0]["id"] == body["id"]


def test_active_filter_excludes_finished_applications(auth_client) -> None:
    user = register_user(auth_client, "finished@example.com", "password123456")
    token = user["access_token"]
    headers = _auth_header(token)

    create = auth_client.post(
        "/api/applications",
        headers=headers,
        json={
            "company": "Beta Inc",
            "position": "Engineer",
            "started_on": "2026-06-01",
            "state": "interviewing",
        },
    )
    assert create.status_code == 201
    app_id = create.json()["id"]

    with session_scope() as session:
        application = session.get(JobApplication, UUID(app_id))
        assert application is not None
        application.state = ApplicationState.rejected
        application.finished_on = date(2026, 6, 15)
        application.updated_at = datetime.now(UTC)
        session.add(application)

    listed = auth_client.get("/api/applications?active=true", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["applications"] == []

    all_apps = auth_client.get("/api/applications", headers=headers)
    assert all_apps.status_code == 200
    assert len(all_apps.json()["applications"]) == 1


def test_users_cannot_see_other_users_applications(auth_client) -> None:
    user_a = register_user(auth_client, "user-a@example.com", "password123456")
    user_b = register_user(auth_client, "user-b@example.com", "password123456")

    create = auth_client.post(
        "/api/applications",
        headers=_auth_header(user_a["access_token"]),
        json={
            "company": "Private Co",
            "position": "Role",
            "started_on": "2026-07-01",
        },
    )
    assert create.status_code == 201

    listed = auth_client.get(
        "/api/applications?active=true",
        headers=_auth_header(user_b["access_token"]),
    )
    assert listed.status_code == 200
    assert listed.json()["applications"] == []


def test_create_rejects_empty_company(auth_client) -> None:
    user = register_user(auth_client, "validate@example.com", "password123456")
    r = auth_client.post(
        "/api/applications",
        headers=_auth_header(user["access_token"]),
        json={
            "company": "   ",
            "position": "Engineer",
            "started_on": "2026-07-01",
        },
    )
    assert r.status_code == 422


def test_create_rejects_terminal_state(auth_client) -> None:
    user = register_user(auth_client, "terminal@example.com", "password123456")
    r = auth_client.post(
        "/api/applications",
        headers=_auth_header(user["access_token"]),
        json={
            "company": "Acme",
            "position": "Engineer",
            "started_on": "2026-07-01",
            "state": "rejected",
        },
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "invalid_application_state"
