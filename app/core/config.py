from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    database_url: Optional[str] = None
    
    db_server: Optional[str] = None
    db_database: Optional[str] = None
    db_username: Optional[str] = None
    db_password: Optional[str] = None
    db_use_windows_auth: bool = False
    db_driver: Optional[str] = None
    
    auto_init_db: bool = True
    
    def get_database_url(self) -> str:
        """Get database URL, building it automatically if not directly provided."""
        if self.database_url:
            return self.database_url
        
        if not self.db_server:
            raise ValueError("DB_SERVER must be set in .env file")
        if not self.db_database:
            raise ValueError("DB_DATABASE must be set in .env file")
        if not self.db_use_windows_auth:
            if not self.db_username:
                raise ValueError("DB_USERNAME must be set in .env file when not using Windows Authentication")
            if not self.db_password:
                raise ValueError("DB_PASSWORD must be set in .env file when not using Windows Authentication")
        
        from app.utils.db_utils import build_database_url
        
        return build_database_url(
            username=self.db_username or "",
            password=self.db_password or "",
            server=self.db_server,
            database=self.db_database,
            use_windows_auth=self.db_use_windows_auth,
            driver=self.db_driver
        )

    aws_access_key_id: str = "your_aws_access_key_id"
    aws_secret_access_key: str = "your_aws_secret_access_key"
    aws_s3_bucket_name: str = "your_s3_bucket_name"
    aws_region: str = "us-east-1"

    jwt_secret_key: str = "dev-secret-key-change-in-production-minimum-32-characters-long"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 15

    openai_api_key: Optional[str] = None
    azure_cognitive_services_key: Optional[str] = None
    azure_cognitive_services_endpoint: Optional[str] = None

    app_name: str = "Document Analyzer Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"


settings = Settings()

