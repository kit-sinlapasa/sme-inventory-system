from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sme_inventory"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # NFR-PRIV-01 (CR-001) — จำนวนปีที่เก็บข้อมูลผู้ซื้อก่อนถูก purge
    DATA_RETENTION_YEARS: int = 3

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
