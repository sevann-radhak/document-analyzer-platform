from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database
    database_url: str = "sqlserver+pyodbc://username:password@localhost:1433/database_name?driver=ODBC+Driver+17+for+SQL+Server"

    # AWS
    aws_access_key_id: str = "your_aws_access_key_id"
    aws_secret_access_key: str = "your_aws_secret_access_key"
    aws_s3_bucket_name: str = "your_s3_bucket_name"
    aws_region: str = "us-east-1"

    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production-minimum-32-characters-long"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15

    # AI Services
    openai_api_key: Optional[str] = None
    azure_cognitive_services_key: Optional[str] = None
    azure_cognitive_services_endpoint: Optional[str] = None

    # Application
    app_name: str = "Document Analyzer Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"


settings = Settings()

