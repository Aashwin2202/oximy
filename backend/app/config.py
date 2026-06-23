from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres connection string. Defaults to the docker-compose service.
    database_url: str = "postgresql+psycopg://oximy:oximy@db:5432/oximy"

    # Bearer token required by POST /ingest.
    ingest_token: str = "dev-ingest-token"

    # Path the collector scans for Claude Code sessions.
    claude_dir: str = "/data/claude"

    # When true, the lineage endpoint may re-read raw JSONL lines from disk.
    # Raw prompt text is NEVER persisted regardless of this flag.
    debug_raw: bool = False

    # CORS origins for the frontend.
    cors_origins: str = "*"

    # Maximum events per POST /ingest request. Clients must chunk beyond this.
    max_ingest_batch: int = 5000


@lru_cache
def get_settings() -> Settings:
    return Settings()
