from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    APP_ENV: str = "development"  
    DATABASE_URL: str
    JWT_PUBLIC_KEY_PATH: str
    JWT_ALGORITHM: str = "RS256"
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_TLS: bool = False
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SIGNATURE_SECRET_KEY: bytes = b"secret key"
    CLERK_LIST: str = "http://host.docker.internal:8020/users/clerks"
    FRONTEND_URL: str
    
    # Admin panel credentials
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "password"

    TIMEZONE: str = "Europe/Berlin"

    ALLOWED_HOSTS: Annotated[list[str], NoDecode] = ["*"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def split_allowed_hosts(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            s = v.strip()
            if s in ("", "*"):
                return ["*"]
            # split by comma, trim whitespace, drop empties
            return [h.strip() for h in s.split(",") if h.strip()]
        return v

    @property
    def signature_secret_key(self) -> bytes:
        return self.SIGNATURE_SECRET_KEY.encode() if isinstance(self.SIGNATURE_SECRET_KEY, str) else self.SIGNATURE_SECRET_KEY

    class Config:
        env_file = ".env"  
        case_sensitive = True


settings = Settings()
