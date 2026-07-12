"""
Task 정의. process_pipeline.md의 Step 2~4를 Sequential Task로 매핑한다.
  Step 2 Retrieval      -> retrieval_task
  Step 3 Analysis        -> analysis_task
  Step 4 Quality Check   -> quality_task (Step 5 Output은 crew.py에서 파일로 저장)
"""
from crewai import Agent, Task

def build_tasks(
    agents: dict[str, Agent], topic: str, keywords: str, verified_sources: str
) -> list[Task]:
    retrieval_task = Task(
        description=(
            f"연구 주제: '{topic}'\n"
            f"핵심 키워드: {keywords}\n\n"
            "아래 '검증된 OpenAlex 검색 결과'만 사용하라. 새 자료를 검색하거나 제목, URL, "
            "저자 정보를 만들지 마라. 각 자료에서 제목, URL, 발행일, "
            "핵심 초록(Abstract)/요지를 추출해 목록으로 정리하라. 초록에 명시된 범위 안에서 "
            "방법론과 주요 발견을 요약하고, 이 연구 주제와의 관련성을 한 문장으로 분석하라. "
            "정보가 초록에 없으면 추측하지 말고 '초록에서 확인되지 않음'이라고 작성하라.\n\n"
            "검색 결과가 부족하더라도 arXiv나 일반 웹 자료 또는 다른 학문 분야의 논문으로 "
            "채우지 마라. 관련성 높은 교육학 논문만 남겨라.\n\n"
            "반드시 각 자료를 아래 형식으로 출력하라. 필드명과 구분자는 바꾸지 마라.\n"
            "REFERENCE_START\n"
            "TITLE: 논문 제목\n"
            "URL: https://...\n"
            "PUBLISHED: YYYY-MM-DD\n"
            "SUMMARY: 초록 핵심 요약\n"
            "METHODOLOGY: 연구 방법론\n"
            "FINDINGS: 주요 발견\n"
            "RELEVANCE: 현재 연구 주제와의 관련성\n"
            "REFERENCE_END"
            f"\n\n검증된 OpenAlex 검색 결과:\n{verified_sources}"
        ),
        expected_output=(
            "각 자료가 REFERENCE_START와 REFERENCE_END 사이에 지정된 7개 필드를 모두 포함한 목록. "
            "관련성이 낮은 자료는 제외하고 URL은 원문 주소를 그대로 유지."
        ),
        agent=agents["literature"],
    )

    analysis_task = Task(
        description=(
            f"연구 주제: '{topic}'\n\n"
            "이전 단계에서 수집된 자료들을 바탕으로 다음을 수행하라:\n"
            "1. 각 자료의 방법론(Methodology)과 결론(Conclusion)을 파악\n"
            "2. 교육학 이론(예: 구성주의, 자기결정성이론 등)과 연결지어 해석\n"
            "3. 연구들 간의 공통점, 차이점, 한계점을 분석\n"
            "4. 실무적/정책적 시사점을 도출\n\n"
            "IMRAD 구조를 변형한 마크다운 형식으로 작성하고, 모든 주장 뒤에는 "
            "어떤 자료(제목 또는 [번호])에 근거했는지 명시하라."
        ),
        expected_output=(
            "## 개요 / ## 주요 발견 / ## 상충되거나 다른 시각 / ## 시사점 / ## 추가로 살펴볼 질문 "
            "섹션을 갖춘 마크다운 초안. 모든 주장에 출처 표기 포함."
        ),
        agent=agents["summarizer"],
        context=[retrieval_task],
    )

    quality_task = Task(
        description=(
            "이전 단계의 마크다운 초안을 검토하라:\n"
            "1. 원자료에 없는 내용(환각)이 있는지 확인하고 있다면 제거하거나 근거를 명시\n"
            "2. 논리적 비약이 있는 문장을 찾아 완화하거나 보강\n"
            "3. 학술적이고 객관적인 톤앤매너를 유지하는지 확인 (과장된 표현 제거)\n"
            "4. 마크다운 포맷팅이 일관적인지 확인\n\n"
            "문제를 발견하면 직접 수정한 최종본을 출력하라. 문제가 없다면 원문을 그대로 출력하라."
        ),
        expected_output="검증 및 필요시 수정을 거친 최종 마크다운 보고서 전체.",
        agent=agents["quality"],
        context=[retrieval_task, analysis_task],
    )

    return [retrieval_task, analysis_task, quality_task]
