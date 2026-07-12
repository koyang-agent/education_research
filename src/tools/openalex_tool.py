"""OpenAlex의 Education 하위 분야로 제한된 결정론적 논문 검색."""
import os

import requests
from tenacity import retry, stop_after_attempt, wait_fixed


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


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def search_education_literature(query: str, max_results: int = 5) -> list[dict]:
    """LLM을 거치지 않고 OpenAlex가 실제 반환한 Education 논문만 가져온다."""
    max_results = max(1, min(max_results, 10))
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
    records: list[dict] = []
    for work in response.json().get("results", []):
        location = work.get("primary_location") or {}
        source = location.get("source") or {}
        topic = work.get("primary_topic") or {}
        url = work.get("doi") or work.get("id", "")
        title = work.get("title") or ""
        if not title or not url.startswith(("https://doi.org/", "https://openalex.org/")):
            continue
        authors = [
            item.get("author", {}).get("display_name", "")
            for item in work.get("authorships", [])[:5]
        ]
        records.append(
            {
                "title": title,
                "url": url,
                "published": work.get("publication_date") or "정보 없음",
                "authors": ", ".join(author for author in authors if author) or "정보 없음",
                "journal": source.get("display_name") or "정보 없음",
                "education_topic": topic.get("display_name") or "Education",
                "citations": work.get("cited_by_count", 0),
                "abstract": _restore_abstract(work.get("abstract_inverted_index"))[:700],
            }
        )
    return records


def format_literature_for_llm(records: list[dict]) -> str:
    """검증된 API 레코드를 LLM이 분석하기 쉬운 읽기 전용 목록으로 만든다."""
    results: list[str] = []
    for index, record in enumerate(records, start=1):
        results.append(
            "\n".join(
                [
                    f"[검증된 논문 {index}]",
                    f"출처: {record.get('source', 'OpenAlex')}",
                    f"제목: {record['title']}",
                    f"URL: {record['url']}",
                    f"발행일: {record['published']}",
                    f"저자: {record['authors']}",
                    f"저널: {record['journal']}",
                    f"교육학 세부 주제: {record['education_topic']}",
                    f"인용 수: {record['citations']}",
                    f"초록: {record['abstract']}",
                ]
            )
        )
    return "\n\n".join(results)
