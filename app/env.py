from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"  
    DATABASE_URL: str
    JWT_PUBLIC_KEY_PATH: str
    JWT_ALGORITHM: str = "RS256"

    class Config:
        env_file = ".env"  
        case_sensitive = True


settings = Settings()
