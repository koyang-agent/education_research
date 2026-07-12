"""
Crew 정의: Sequential Process로 Literature -> Summarizer -> Quality 순서 실행.
"""
from crewai import Crew, Process

from src.agents import build_agents
from src.tasks import build_tasks


def run_research(topic: str, keywords: str) -> str:
    """주제와 키워드를 받아 파이프라인을 실행하고 최종 마크다운 보고서 텍스트를 반환."""
    agents = build_agents()
    tasks = build_tasks(agents, topic, keywords)

    crew = Crew(
        agents=[agents["literature"], agents["summarizer"], agents["quality"]],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)
