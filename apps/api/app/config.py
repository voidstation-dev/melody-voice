from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "sqlite+aiosqlite:///../../data/app.db"
    audio_storage_dir: Path = Path("../../data/audio")
    preview_storage_dir: Path = Path("../../data/previews")
    raw_response_dir: Path = Path("../../data/raw-responses")
    capcut_catalog_path: Path = Path("../../vendor/capcut-tts-api/Voice.json")
    tts_max_text_chars: int = 500000
    tts_min_rate: float = 0.5
    tts_max_rate: float = 2.0
    tts_provider_timeout_seconds: float = 90.0
    tts_audio_max_bytes: int = 52428800
    save_raw_provider_responses: bool = True
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
