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

    class Config:
        env_file = ".env"  
        case_sensitive = True


settings = Settings()
