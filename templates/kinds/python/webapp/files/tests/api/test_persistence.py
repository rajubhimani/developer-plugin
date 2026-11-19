"""The real storage path: migrations create the table and items survive a restart."""

from pathlib import Path

from fastapi.testclient import TestClient

from {{package}}.main import create_app
from {{package}}.migrate import upgrade
from {{package}}.settings import Settings


def test_migrated_database_keeps_items_across_app_instances(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'app.db'}"
    upgrade(url)  # the same function the migration job runs
    settings = Settings(database_url=url, api_key="test", _env_file=None)  # pyright: ignore[reportCallIssue]

    first = TestClient(create_app(settings))
    assert first.post("/items", json={"name": "pen"}).status_code == 201
    assert first.get("/readyz").status_code == 200  # the database ping works

    restarted = TestClient(create_app(settings))  # a new process would see the same rows
    assert [item["name"] for item in restarted.get("/items").json()] == ["pen"]


def test_running_the_migrations_twice_changes_nothing(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'app.db'}"
    upgrade(url)
    upgrade(url)  # idempotent: the job can be retried
