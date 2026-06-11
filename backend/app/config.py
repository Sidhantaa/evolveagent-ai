import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    app_name: str = Field(default="EvolveAgent AI", alias="APP_NAME")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    mistral_api_key: str | None = Field(default=None, alias="MISTRAL_API_KEY")
    default_provider: str = Field(default="openai", alias="DEFAULT_PROVIDER")
    llm_mode: str = Field(default="mock", alias="LLM_MODE")
    openai_text_model: str = Field(default="gpt-4o-mini", alias="OPENAI_TEXT_MODEL")
    openai_master_model: str = Field(default="gpt-5.5", alias="OPENAI_MASTER_MODEL")
    openai_reasoning_model: str = Field(default="gpt-5.4", alias="OPENAI_REASONING_MODEL")
    openai_cheap_model: str = Field(default="gpt-5.4-mini", alias="OPENAI_CHEAP_MODEL")
    anthropic_strong_model: str = Field(default="claude-opus-4.5", alias="ANTHROPIC_STRONG_MODEL")
    anthropic_balanced_model: str = Field(default="claude-sonnet-4.5", alias="ANTHROPIC_BALANCED_MODEL")
    anthropic_fast_model: str = Field(default="claude-haiku-4.5", alias="ANTHROPIC_FAST_MODEL")
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", alias="ANTHROPIC_MODEL")
    gemini_pro_model: str = Field(default="gemini-pro", alias="GEMINI_PRO_MODEL")
    gemini_fast_model: str = Field(default="gemini-flash", alias="GEMINI_FAST_MODEL")
    gemini_model: str = Field(default="gemini-1.5-pro", alias="GEMINI_MODEL")
    mistral_strong_model: str = Field(default="mistral-large", alias="MISTRAL_STRONG_MODEL")
    mistral_code_model: str = Field(default="devstral", alias="MISTRAL_CODE_MODEL")
    mistral_fast_model: str = Field(default="mistral-small", alias="MISTRAL_FAST_MODEL")
    mistral_model: str = Field(default="mistral-large-latest", alias="MISTRAL_MODEL")
    image_mode: str = Field(default="mock", alias="IMAGE_MODE")
    image_provider: str = Field(default="mock_image", alias="IMAGE_PROVIDER")
    openai_image_model: str = Field(default="gpt-image-1.5", alias="OPENAI_IMAGE_MODEL")
    transcription_mode: str = Field(default="mock", alias="TRANSCRIPTION_MODE")
    openai_transcription_model: str = Field(default="whisper-1", alias="OPENAI_TRANSCRIPTION_MODEL")
    linear_api_key: str | None = Field(default=None, alias="LINEAR_API_KEY")
    linear_team_id: str | None = Field(default=None, alias="LINEAR_TEAM_ID")
    linear_project_id: str | None = Field(default=None, alias="LINEAR_PROJECT_ID")
    linear_workspace_name: str | None = Field(default=None, alias="LINEAR_WORKSPACE_NAME")
    linear_sync_enabled: bool = Field(default=False, alias="LINEAR_SYNC_ENABLED")
    linear_poll_interval_seconds: int = Field(default=60, alias="LINEAR_POLL_INTERVAL_SECONDS")
    linear_cursor_worker: bool = Field(default=True, alias="LINEAR_CURSOR_WORKER")
    auto_git_push: bool = Field(default=False, alias="AUTO_GIT_PUSH")
    git_default_branch: str = Field(default="main", alias="GIT_DEFAULT_BRANCH")
    git_remote_name: str = Field(default="origin", alias="GIT_REMOTE_NAME")
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @property
    def use_mock_llm(self) -> bool:
        return self.llm_mode.lower() == "mock"

    @property
    def linear_configured(self) -> bool:
        return bool(self.linear_api_key and self.linear_team_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
