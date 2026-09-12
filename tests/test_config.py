import pytest

from src.shared import config


@pytest.fixture(autouse=True)
def database_environment(monkeypatch):
    config.db_settings.cache_clear()
    monkeypatch.setenv("DB_SECRET_ARN", "test-db-secret")
    monkeypatch.setenv("DB_NAME", "numberone")
    monkeypatch.setenv("DB_SSL_MODE", "require")
    monkeypatch.delenv("DB_HOST", raising=False)
    yield
    config.db_settings.cache_clear()


@pytest.mark.parametrize("secret_host", [None, "legacy-db.example"])
def test_db_host_from_environment_takes_priority(monkeypatch, secret_host):
    payload = {"username": "test-user", "password": "test-password"}
    if secret_host is not None:
        payload["host"] = secret_host
    monkeypatch.setattr(config, "_read_secret", lambda arn: payload)
    monkeypatch.setenv("DB_HOST", "infra-db.example")

    assert config.db_settings() == {
        "host": "infra-db.example",
        "port": 5432,
        "dbname": "numberone",
        "username": "test-user",
        "password": "test-password",
        "sslmode": "require",
    }


def test_db_host_falls_back_to_secret(monkeypatch):
    monkeypatch.setattr(config, "_read_secret", lambda arn: {
        "host": "legacy-db.example",
        "username": "test-user",
        "password": "test-password",
    })

    assert config.db_settings()["host"] == "legacy-db.example"


def test_db_host_missing_raises(monkeypatch):
    monkeypatch.setattr(config, "_read_secret", lambda arn: {
        "username": "test-user",
        "password": "test-password",
    })

    with pytest.raises(RuntimeError, match="^Missing secret settings: host$"):
        config.db_settings()
