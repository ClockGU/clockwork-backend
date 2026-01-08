from pydantic_settings import BaseSettings

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

    ALLOWED_HOSTS: list[str] = ["*"]

    @property
    def signature_secret_key(self) -> bytes:
        return self.SIGNATURE_SECRET_KEY.encode() if isinstance(self.SIGNATURE_SECRET_KEY, str) else self.SIGNATURE_SECRET_KEY

    class Config:
        env_file = ".env"  
        case_sensitive = True


settings = Settings()
