"""HTTP tests for routes defined on ``src.main`` (app shell)."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database_configured"] is False


def test_list_applications_without_database(client: TestClient) -> None:
    r = client.get("/api/applications")
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "database_not_configured"
