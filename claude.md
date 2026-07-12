# 프로젝트 가이드라인: 교육학 자동 연구 에이전트 (EduResearch-Agent)

## 1. 프로젝트 개요
본 프로젝트는 교육학 연구 프로세스(문헌 조사, 분석·통합, 학술 요약문 작성)를 자동화하는
Multi-Agent 시스템입니다. 주요 프레임워크로 CrewAI를 사용하며, 향후 조건부 재검색 등
상태 제어가 필요해지면 LangGraph로 확장한다.

## 2. 기본 아키텍처 원칙
- **모듈화**: 각 Agent(문헌 조사관, 학술 분석가, 품질 검증관)의 역할과 도구(Tools)는 명확히 분리한다.
- **결과 중심**: 에이전트의 출력물은 학술 논문 스타일(IMRAD 구조 변형)의 Markdown 형식을 따른다.
- **오류 처리**: 외부 API(OpenAlex, LLM 등) 호출 실패 시 재시도 로직을 포함한다.
- **자체 검증**: 최종 출력 전 Self-Correction 단계에서 환각·근거 부족 여부를 반드시 검토한다.

## 3. 기술 스택
- Core Framework: CrewAI (Sequential Process)
- LLM Provider: Groq — 종합/검증에는 `llama-3.3-70b-versatile`, 단순 추출·정리에는
  `llama-3.1-8b-instant` 사용 (litellm 표기: `groq/llama-3.3-70b-versatile`)
- Development Tool: Claude Code CLI

## 4. 코딩 컨벤션
- Python 3.11+ 문법을 준수하며, 모든 함수와 클래스에는 Type Hinting을 필수 적용한다.
- 에이전트 프롬프트(`backstory`, `goal`)는 학술적이고 객관적인 톤앤매너를 유지하도록 한글로 작성한다.
- API Key는 반드시 `.env` 파일에서 관리하며, `pydantic-settings`로 로드한다 (`config/settings.py`).
- 새 도구는 `src/tools/`에 `BaseTool` 서브클래스로 추가하고, `src/agents.py`에서 참조한다.
- 커밋 전 `python -m py_compile` 로 문법 오류가 없는지 확인한다.

## 5. 확장 시 우선순위
1. ERIC / RISS / KCI 등 교육학 전문 DB 연동 도구 추가 (`src/tools/`)
2. Self-Correction 단계에서 반려(reject) 시 Literature Agent로 되돌아가는 재시도 루프
   → 이 지점부터 LangGraph 도입 고려
3. 결과물 알림 (Slack/이메일) 및 스케줄링 (cron/GitHub Actions)
