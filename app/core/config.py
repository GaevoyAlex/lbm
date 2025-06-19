from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Auth API"
    API_V1_STR: str = "/api/v1"
    
    # JWT настройки
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # База данных
    DATABASE_URL: str
    
    # Добавляем эти поля, которые есть в .env файле
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        # Разрешаем дополнительные поля, если не хотите добавлять все переменные из .env
        # extra="ignore"  # Раскомментируйте эту строку, если не хотите добавлять все поля
    )

settings = Settings()