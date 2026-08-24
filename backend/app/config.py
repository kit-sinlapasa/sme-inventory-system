from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sme_inventory"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # NFR-PRIV-01 (CR-001) — จำนวนปีที่เก็บข้อมูลผู้ซื้อก่อนถูก purge
    DATA_RETENTION_YEARS: int = 3

    # FR-012 / CR-006 — แจ้งเตือนสต็อกใกล้หมดผ่านอีเมล
    # ว่างไว้ = dev-mode (log แทนการส่งจริง) — ทีมต้องตั้งค่าเองทั้ง local/.env และบน Render
    # AI ไม่เคยเห็นหรือขอ credential เหล่านี้ ตั้งใจปล่อยว่างไว้ตลอด
    ALERT_EMAIL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_postgres_scheme(cls, v: str) -> str:
        """
        Render (เหมือน Heroku เดิม) ให้ connection string ขึ้นต้นด้วย postgres://
        แต่ SQLAlchemy 1.4+/2.0 ต้องการ postgresql:// เท่านั้น ไม่งั้น
        create_engine() จะ raise NoSuchModuleError ทันทีตอน startup —
        เป็นสาเหตุ deploy fail ที่พบบ่อยที่สุดบน platform กลุ่มนี้
        """
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v


settings = Settings()
