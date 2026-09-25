from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    app_name: str = "NuevaMente"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    llm_provider: str = "gemini"

    gemini_api_key: str | None = None
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

    documents_path: str = "./data/documents"
    generated_path: str = "./data/generated"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    
settings = Settings()