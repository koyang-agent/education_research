"""
Crew 정의: Sequential Process로 Literature -> Summarizer -> Quality 순서 실행.
"""
import re

from crewai import Crew, Process

from src.agents import build_agents
from src.result import Reference, ResearchResult
from src.tasks import build_tasks
from src.tools.academic_sources import search_all_sources
from src.tools.openalex_tool import format_literature_for_llm


_REFERENCE_FIELDS = (
    "TITLE",
    "URL",
    "PUBLISHED",
    "SUMMARY",
    "METHODOLOGY",
    "FINDINGS",
    "RELEVANCE",
)


def _parse_references(raw: str, records: list[dict]) -> list[Reference]:
    """문헌 조사 에이전트의 구분자 기반 출력을 참고문헌 객체로 변환한다."""
    analyses: dict[str, dict[str, str]] = {}
    for block in raw.split("REFERENCE_START")[1:]:
        block = block.split("REFERENCE_END", 1)[0]
        values: dict[str, str] = {}
        for index, field in enumerate(_REFERENCE_FIELDS):
            following = "|".join(_REFERENCE_FIELDS[index + 1 :]) or "REFERENCE_END"
            match = re.search(
                rf"{field}:\s*(.*?)(?=\n(?:{following}):|\Z)",
                block,
                flags=re.DOTALL,
            )
            values[field] = match.group(1).strip() if match else ""

        url = values["URL"].strip("<> ")
        if url:
            analyses[url] = values

    return [
        Reference(
            title=record["title"],
            url=record["url"],
            published=record["published"],
            summary=record["abstract"],
            methodology=analyses.get(record["url"], {}).get("METHODOLOGY")
            or "초록에서 확인되지 않음",
            findings=analyses.get(record["url"], {}).get("FINDINGS")
            or "초록에서 확인되지 않음",
            relevance=analyses.get(record["url"], {}).get("RELEVANCE")
            or "연구 주제와의 관련성 분석 없음",
        )
        for record in records
    ]


def run_research(topic: str, keywords: str, korean_keywords: str = "") -> ResearchResult:
    """파이프라인을 실행하고 보고서와 구조화된 참고문헌을 반환한다."""
    records = search_all_sources(
        keywords, korean_keywords or topic, settings.max_papers_per_topic
    )
    if not records:
        return ResearchResult(
            report=(
                "## 검색 결과 없음\n\n입력한 영문 검색어와 일치하는 Education 분야 저널 논문을 "
                "연동된 교육학 데이터베이스에서 찾지 못했습니다. 영문·한글 키워드를 더 "
                "일반적인 표현으로 바꾸거나 추가 API 키 설정을 확인해주세요."
            ),
            references=[],
        )

    agents = build_agents()
    tasks = build_tasks(agents, topic, keywords, format_literature_for_llm(records))

    crew = Crew(
        agents=[agents["literature"], agents["summarizer"], agents["quality"]],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    task_outputs = getattr(result, "tasks_output", [])
    retrieval_raw = str(task_outputs[0].raw) if task_outputs else ""
    return ResearchResult(
        report=str(result),
        references=_parse_references(retrieval_raw, records),
    )
