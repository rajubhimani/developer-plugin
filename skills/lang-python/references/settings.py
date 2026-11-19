"""Application settings: the one place that reads the environment.

Add the dependency first:  uv add pydantic-settings

Every value arrives as an environment variable named APP_<FIELD> (upper case).
Sources, highest priority first:
  1. arguments passed to Settings(...) (tests)
  2. real environment variables (the cluster, Compose, your shell)
  3. the .env file (local work only; git-ignored and docker-ignored)
  4. files in a secrets directory, when APP_SECRETS_DIR is set (a mounted secret)
  5. the defaults below

A required field has no default, so a missing value stops the app at start-up with
the field's name. Credentials use SecretStr so they print as stars; never log the
whole settings object.

Keep three lists in step: the fields here, `.env.example`, and the Kubernetes
ConfigMap (plain values) and Secret (credentials). `make check-env` compares them.
Use plain field names: aliases are not supported by that check.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated settings. Create it once with get_settings()."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        # Unset by default so a missing directory does not warn. A cluster mounts
        # secrets as files and sets APP_SECRETS_DIR to that folder.
        secrets_dir=os.environ.get("APP_SECRETS_DIR"),
        # .env also holds values only Compose reads (image tags, DB_PASSWORD).
        extra="ignore",
        frozen=True,
    )

    # ---- plain settings: ConfigMap in Kubernetes ------------------------------
    env: Literal["local", "staging", "production"] = "local"
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    log_format: Literal["console", "json"] = "json"
    request_timeout_seconds: float = Field(default=10.0, gt=0, le=300)

    # ---- credentials: Secret in Kubernetes, required, never defaulted ---------
    database_url: SecretStr
    api_key: SecretStr


class MigrationSettings(BaseSettings):
    """What the migration job needs and nothing else.

    A job that changes the schema holds the database credential only; it never receives
    the application's other secrets (least privilege). Same prefix, same variable name.
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        secrets_dir=os.environ.get("APP_SECRETS_DIR"),
        extra="ignore",
        frozen=True,
    )

    database_url: SecretStr


@lru_cache
def get_settings() -> Settings:
    """Return the settings, read and validated once."""
    return Settings()  # pyright: ignore[reportCallIssue]


@lru_cache
def get_migration_settings() -> MigrationSettings:
    """Return the migration job's settings (the database URL only)."""
    return MigrationSettings()  # pyright: ignore[reportCallIssue]
