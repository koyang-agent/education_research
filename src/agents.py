"""
Agent 정의.
- Literature Agent: 논문/웹 자료 검색 및 원자료 추출
- Summarizer Agent: 교육학 이론과 매핑, 공통점/차이점/한계 분석
- Quality Reviewer Agent: Self-Correction (환각·논리 비약·톤앤매너 검증)
"""
from crewai import Agent, LLM

from config.settings import settings
from src.tools.arxiv_tool import ArxivSearchTool
from src.tools.search_tool import get_web_search_tool


def build_agents() -> dict[str, Agent]:
    extraction_llm = LLM(model=settings.extraction_model, temperature=0.2)
    synthesis_llm = LLM(model=settings.synthesis_model, temperature=0.3)

    tools = [ArxivSearchTool()]
    web_tool = get_web_search_tool()
    if web_tool:
        tools.append(web_tool)

    literature_agent = Agent(
        role="교육학 문헌 조사관",
        goal="주어진 연구 주제에 대해 신뢰할 수 있는 최신 학술 자료를 폭넓게 수집한다",
        backstory=(
            "당신은 교육학 분야의 체계적 문헌고찰(Systematic Review) 경험이 풍부한 "
            "리서치 라이브러리언입니다. 관련성이 낮은 자료는 걸러내고, 방법론과 핵심 결과가 "
            "명확한 자료를 우선적으로 선별합니다."
        ),
        tools=tools,
        llm=extraction_llm,
        verbose=True,
    )

    summarizer_agent = Agent(
        role="교육학 학술 분석가",
        goal="수집된 자료를 교육학 이론과 연결해 공통점, 차이점, 한계를 분석하고 시사점을 도출한다",
        backstory=(
            "당신은 구성주의, 자기결정성이론 등 교육학 주요 이론에 정통한 연구자입니다. "
            "개별 연구 결과를 나열하는 데 그치지 않고, 이론적 틀 안에서 의미를 해석합니다."
        ),
        llm=synthesis_llm,
        verbose=True,
    )

    quality_agent = Agent(
        role="품질 검증관",
        goal="최종 보고서에 환각, 근거 없는 비약, 부적절한 톤앤매너가 없는지 검증하고 수정한다",
        backstory=(
            "당신은 학술지 편집자 출신으로, 근거 없는 주장이나 과장된 표현을 정확히 찾아내 "
            "교정하는 데 엄격합니다. 원자료에 없는 내용은 절대 남겨두지 않습니다."
        ),
        llm=synthesis_llm,
        verbose=True,
    )

    return {
        "literature": literature_agent,
        "summarizer": summarizer_agent,
        "quality": quality_agent,
    }
