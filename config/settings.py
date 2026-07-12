"""
프로젝트 전역 설정. .env 파일을 읽어 Settings 객체로 노출한다.
API Key는 반드시 pydantic-settings로 로드.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str
    serper_api_key: str | None = None

    # 모델 라우팅
    synthesis_model: str = "groq/llama-3.3-70b-versatile"  # 종합·검증용 (품질 우선)
    extraction_model: str = "groq/llama-3.1-8b-instant"  # 단순 추출·정리용 (무료 한도 절약)

    output_dir: str = "outputs"
    max_papers_per_topic: int = 5


settings = Settings()
