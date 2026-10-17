from unittest.mock import patch

import psycopg
import pytest

from app import create_app


@pytest.fixture
def client(monkeypatch):
    # Keep tests independent from the terminal environment.
    for name in (
        "APP_VERSION",
        "APP_ENV",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


@pytest.fixture
def db_config(client, monkeypatch):
    # Dummy values only; tests do not contact this database.
    values = {
        "DB_HOST": "test-db",
        "DB_PORT": "5432",
        "DB_NAME": "test_database",
        "DB_USER": "test_user",
        "DB_PASSWORD": "dummy-test-password",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_home_returns_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"


def test_health_does_not_depend_on_database(client, db_config):
    with patch(
        "app.psycopg.connect",
        side_effect=psycopg.OperationalError("database unavailable"),
    ) as connect:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    connect.assert_not_called()


def test_version_defaults(client):
    response = client.get("/version")

    assert response.status_code == 200
    assert response.get_json() == {
        "version": "v1",
        "environment": "local",
    }


def test_version_uses_environment(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "test-version")
    monkeypatch.setenv("APP_ENV", "ci")

    response = client.get("/version")

    assert response.status_code == 200
    assert response.get_json() == {
        "version": "test-version",
        "environment": "ci",
    }


def test_ready_without_database_configuration(client):
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.get_json() == {
        "status": "not_ready",
        "reason": "database_not_configured",
    }


def test_ready_when_database_query_succeeds(client, db_config):
    with patch("app.psycopg.connect") as connect:
        connection = connect.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1,)

        response = client.get("/ready")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ready",
        "database": "connected",
    }


def test_ready_when_database_is_unavailable(client, db_config):
    with patch(
        "app.psycopg.connect",
        side_effect=psycopg.OperationalError("internal-db-error"),
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.get_json() == {
        "status": "not_ready",
        "reason": "database_unavailable",
    }
    assert b"internal-db-error" not in response.data


def test_unknown_route_returns_404(client):
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
