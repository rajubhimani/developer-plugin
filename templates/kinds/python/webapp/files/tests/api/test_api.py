"""API tests: routes, status codes and the error format, through the real app."""

import pytest
from fastapi.testclient import TestClient

from {{package}}.adapters.memory import InMemoryItemRepository
from {{package}}.main import create_app
from {{package}}.settings import Settings


def make_settings() -> Settings:
    return Settings(database_url="postgresql://test", api_key="test", _env_file=None)  # pyright: ignore[reportCallIssue]


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(make_settings(), InMemoryItemRepository()))


def test_liveness_and_readiness(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").status_code == 200


def test_readiness_fails_while_a_dependency_is_down() -> None:
    app = create_app(make_settings(), InMemoryItemRepository())

    def down() -> None:
        raise ConnectionError("secret host name that must not leak")

    app.state.readiness_checks.append(down)
    response = TestClient(app).get("/readyz")
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "secret host" not in response.text
    assert TestClient(app).get("/healthz").status_code == 200  # liveness never checks dependencies


def test_create_then_list_items(client: TestClient) -> None:
    created = client.post("/items", json={"name": "pen"})
    assert created.status_code == 201
    assert client.get("/items").json() == [created.json()]


def test_a_rule_violation_is_a_problem_response(client: TestClient) -> None:
    response = client.post("/items", json={"name": "   "})
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Invalid item"


def test_an_unknown_route_is_a_problem_without_internals(client: TestClient) -> None:
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "Traceback" not in response.text
