"""
arXiv API 기반 논문 검색 도구 (키 불필요).
CrewAI의 BaseTool을 상속해 Agent가 직접 호출할 수 있게 한다.
"""
import xml.etree.ElementTree as ET

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed


class ArxivSearchInput(BaseModel):
    query: str = Field(..., description="검색할 영문 키워드 (예: 'personalized learning adaptive instruction')")
    max_results: int = Field(5, description="가져올 논문 개수")


class ArxivSearchTool(BaseTool):
    name: str = "arxiv_search"
    description: str = (
        "arXiv에서 학술 논문을 검색한다. 제목, 저자, 초록, URL, 발행일을 반환한다. "
        "교육공학/학습과학 관련 영문 키워드로 검색할 때 사용한다."
    )
    args_schema: type[BaseModel] = ArxivSearchInput

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def _run(self, query: str, max_results: int = 5) -> str:
        resp = requests.get(
            "http://export.arxiv.org/api/query",
            params={
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
            timeout=15,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        entries = root.findall("atom:entry", ns)
        if not entries:
            return "검색 결과 없음."

        lines = []
        for e in entries:
            title = e.find("atom:title", ns).text.strip().replace("\n", " ")
            link = e.find("atom:id", ns).text.strip()
            summary = e.find("atom:summary", ns).text.strip().replace("\n", " ")[:400]
            published = e.find("atom:published", ns).text.strip()[:10]
            lines.append(f"- 제목: {title}\n  URL: {link}\n  발행일: {published}\n  초록: {summary}")

        return "\n\n".join(lines)
