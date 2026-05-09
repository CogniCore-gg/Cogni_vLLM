from functools import lru_cache
from typing import Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gateway_port: int = Field(default=8101, alias="GATEWAY_PORT")
    gateway_timeout_seconds: int = Field(default=600, alias="GATEWAY_TIMEOUT_SECONDS")
    gateway_api_key: str = Field(default="", alias="GATEWAY_API_KEY")
    gateway_log_level: str = Field(default="INFO", alias="GATEWAY_LOG_LEVEL")
    gateway_rate_limit_rpm: int = Field(default=120, alias="GATEWAY_RATE_LIMIT_RPM")
    gateway_trust_x_forwarded_for: bool = Field(default=False, alias="GATEWAY_TRUST_X_FORWARDED_FOR")
    gateway_cors_allowed_origins: str = Field(default="", alias="GATEWAY_CORS_ALLOWED_ORIGINS")

    qwen_main_alias: str = Field(default="qwen-main", alias="QWEN_MAIN_ALIAS")
    coder_alias: str = Field(default="coder", alias="CODER_ALIAS")
    deepseek_alias: str = Field(default="deepseek", alias="DEEPSEEK_ALIAS")
    bge_alias: str = Field(default="bge-large", alias="BGE_ALIAS")

    qwen_main_model: str = Field(default="Qwen/Qwen3.6-35B-A3B", alias="QWEN_MAIN_MODEL")
    coder_model: str = Field(default="Qwen/Qwen3-Coder-Next", alias="CODER_MODEL")
    deepseek_model: str = Field(default="deepseek-ai/DeepSeek-V3.2", alias="DEEPSEEK_MODEL")
    bge_model: str = Field(default="BAAI/bge-large-en-v1.5", alias="BGE_MODEL")

    qwen_main_url: str = "http://qwen-main-vllm:8000"
    coder_url: str = "http://coder-vllm:8000"
    deepseek_url: str = "http://deepseek-vllm:8000"
    bge_url: str = "http://bge-large-vllm:8000"

    @property
    def llm_aliases(self) -> set[str]:
        return {self.qwen_main_alias, self.coder_alias, self.deepseek_alias}

    @property
    def all_aliases(self) -> set[str]:
        return self.llm_aliases | {self.bge_alias}

    @property
    def alias_to_backend(self) -> Dict[str, str]:
        return {
            self.qwen_main_alias: self.qwen_main_url,
            self.coder_alias: self.coder_url,
            self.deepseek_alias: self.deepseek_url,
            self.bge_alias: self.bge_url,
        }

    @property
    def alias_to_model_id(self) -> Dict[str, str]:
        return {
            self.qwen_main_alias: self.qwen_main_model,
            self.coder_alias: self.coder_model,
            self.deepseek_alias: self.deepseek_model,
            self.bge_alias: self.bge_model,
        }

    @property
    def cors_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.gateway_cors_allowed_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
