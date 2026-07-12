"""
Crew 정의: Sequential Process로 Literature -> Summarizer -> Quality 순서 실행.
"""
import re

from crewai import Crew, Process

from src.agents import build_agents
from src.result import Reference, ResearchResult
from src.tasks import build_tasks


_REFERENCE_FIELDS = (
    "TITLE",
    "URL",
    "PUBLISHED",
    "SUMMARY",
    "METHODOLOGY",
    "FINDINGS",
    "RELEVANCE",
)


def _parse_references(raw: str) -> list[Reference]:
    """문헌 조사 에이전트의 구분자 기반 출력을 참고문헌 객체로 변환한다."""
    references: list[Reference] = []
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
        if values["TITLE"] and url.startswith(("http://", "https://")):
            references.append(
                Reference(
                    title=values["TITLE"],
                    url=url,
                    published=values["PUBLISHED"] or "발행일 정보 없음",
                    summary=values["SUMMARY"] or "요약 정보 없음",
                    methodology=values["METHODOLOGY"] or "초록에서 확인되지 않음",
                    findings=values["FINDINGS"] or "초록에서 확인되지 않음",
                    relevance=values["RELEVANCE"] or "연구 주제와의 관련성 분석 없음",
                )
            )
    return references


def run_research(topic: str, keywords: str) -> ResearchResult:
    """파이프라인을 실행하고 보고서와 구조화된 참고문헌을 반환한다."""
    agents = build_agents()
    tasks = build_tasks(agents, topic, keywords)

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
        references=_parse_references(retrieval_raw),
    )
