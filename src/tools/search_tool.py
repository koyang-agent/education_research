"""
Serper.dev 기반 웹서치 도구 래퍼.
SERPER_API_KEY가 없으면 None을 반환해, 상위 코드가 arXiv만으로 동작하도록 한다
(claude.md 컨벤션: 외부 API 실패/미설정 시에도 파이프라인이 죽지 않도록 처리).
"""
from typing import Optional

from config.settings import settings


def get_web_search_tool() -> Optional[object]:
    if not settings.serper_api_key:
        print("[info] SERPER_API_KEY 미설정 — 웹서치 없이 arXiv 소스만 사용합니다.")
        return None

    from crewai_tools import SerperDevTool

    return SerperDevTool()
