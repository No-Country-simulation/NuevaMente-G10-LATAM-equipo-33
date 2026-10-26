from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field
from shared.config import ENV_FILE
from typing import Literal

class Settings(BaseSettings):

    app_name: str = "NuevaMente"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = Field(default=False, validation_alias=AliasChoices("APP_DEBUG", "DEBUG"))

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    llm_provider: str = "gemini"

    gemini_api_keys: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    vector_store: str = "faiss"
    top_k: int = 5
    vectorstore_path: str = "./data/vectorstore"

    oci_config_file: str = "~/.oci/config"
    oci_profile: str = "DEFAULT"
    oci_namespace: str | None = None
    oci_bucket_name: str | None = None
    oci_region: str | None = None
    oci_auth_mode: Literal["api_key", "instance_principal"] = "api_key"
    storage_backend: Literal["local", "oci"] = "local"

    documents_path: str = "./data/documents"
    generated_path: str = "./data/generated"
    max_upload_mb: int = Field(default=10, ge=1, le=50)

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    
settings = Settings()
