from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str

    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    PUBLIC_BASE_URL: str
    RATE_LIMIT_STORAGE_URL: str = "memory://"
    PRESIGNED_URL_EXPIRY_SECONDS: int = 60
    SENTRY_DSN: str | None = None
    CF_API_TOKEN: str | None = None
    CF_ZONE_ID: str | None = None
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
