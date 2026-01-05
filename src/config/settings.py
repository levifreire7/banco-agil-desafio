from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Configurações das variáveis de ambiente da aplicação."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    openai_api_key: str = Field(
        ...,
        description="Chave de API da OpenAI",
        min_length=1
    )

    llm_model: str = Field(
        default="gpt-4o",
        description="Modelo de linguagem a ser usado"
    )
    
    llm_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperatura do modelo (0.0 a 2.0)"
    )

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Valida que a chave da OpenAI não está vazia."""
        if not v or v == "your_openai_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY inválida. Configure uma chave válida no arquivo .env"
            )
        return v

    @property
    def is_configured(self) -> bool:
        """Verifica se a aplicação está configurada corretamente."""
        return bool(self.openai_api_key and
                   self.openai_api_key != "your_openai_api_key_here")
