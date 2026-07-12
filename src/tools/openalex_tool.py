"""OpenAlex의 Education 하위 분야로 제한된 학술 논문 검색 도구."""
import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed


class EducationLiteratureSearchInput(BaseModel):
    query: str = Field(..., description="교육학 논문을 찾기 위한 영문 검색어")
    max_results: int = Field(5, ge=1, le=10, description="가져올 논문 개수")


def _restore_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """OpenAlex의 역색인 초록을 일반 문장 순서로 복원한다."""
    if not inverted_index:
        return "초록 정보 없음"
    positions = [position for values in inverted_index.values() for position in values]
    words = [""] * (max(positions) + 1)
    for word, indices in inverted_index.items():
        for index in indices:
            words[index] = word
    return " ".join(words)


class EducationLiteratureSearchTool(BaseTool):
    name: str = "education_literature_search"
    description: str = (
        "OpenAlex에서 주 분류가 Education인 저널 논문만 검색한다. "
        "교육학 하위 분야 필터가 API 수준에서 강제되며 제목, 저자, 저널, 초록, DOI, "
        "발행일, 교육학 세부 주제와 인용 수를 반환한다."
    )
    args_schema: type[BaseModel] = EducationLiteratureSearchInput

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _run(self, query: str, max_results: int = 5) -> str:
        params = {
            "search": query,
            "filter": "primary_topic.subfield.id:3304,type:article",
            "sort": "relevance_score:desc",
            "per-page": max_results,
            "select": (
                "id,doi,title,publication_date,authorships,primary_location,"
                "abstract_inverted_index,primary_topic,cited_by_count"
            ),
        }
        api_key = os.getenv("OPENALEX_API_KEY")
        if api_key:
            params["api_key"] = api_key

        response = requests.get("https://api.openalex.org/works", params=params, timeout=20)
        response.raise_for_status()
        works = response.json().get("results", [])
        if not works:
            return "Education 분야에서 일치하는 저널 논문을 찾지 못했습니다."

        results: list[str] = []
        for work in works:
            location = work.get("primary_location") or {}
            source = location.get("source") or {}
            topic = work.get("primary_topic") or {}
            authors = [
                item.get("author", {}).get("display_name", "")
                for item in work.get("authorships", [])[:5]
            ]
            authors = [author for author in authors if author]
            url = work.get("doi") or location.get("landing_page_url") or work.get("id", "")
            abstract = _restore_abstract(work.get("abstract_inverted_index"))[:700]
            results.append(
                "\n".join(
                    [
                        f"- 제목: {work.get('title', '제목 없음')}",
                        f"  URL: {url}",
                        f"  발행일: {work.get('publication_date') or '정보 없음'}",
                        f"  저자: {', '.join(authors) or '정보 없음'}",
                        f"  저널: {source.get('display_name') or '정보 없음'}",
                        f"  교육학 세부 주제: {topic.get('display_name') or 'Education'}",
                        f"  인용 수: {work.get('cited_by_count', 0)}",
                        f"  초록: {abstract}",
                    ]
                )
            )
        return "\n\n".join(results)
