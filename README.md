# 교육학 자동 연구 에이전트 (CrewAI 기반)

문서에 제안된 아키텍처(`claude.md` + 3계층 구조 + 5단계 파이프라인)를 그대로 구현한 CrewAI 멀티에이전트 프로젝트입니다.

## 구조

```
research_agent_crewai/
├── claude.md              # Claude Code가 참조하는 프로젝트 규칙
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py         # pydantic-settings 기반 환경설정 (API 키, 모델 라우팅)
├── src/
│   ├── tools/
│   │   ├── academic_sources.py # ERIC/OpenAlex/Semantic Scholar/CORE/KCI 통합
│   │   └── openalex_tool.py    # Education 분야로 제한된 OpenAlex 검색
│   ├── agents.py            # 문헌 조사관 / 학술 분석가 / 품질 검증관
│   ├── tasks.py              # Retrieval -> Analysis -> Quality Check
│   └── crew.py               # Sequential Process로 Crew 조립 및 실행
└── main.py                   # CLI 진입점 (Step 1 Input, Step 5 Output)
```

## 파이프라인 매핑

문서의 5단계가 코드에 이렇게 대응됩니다:

| 문서 단계 | 구현 위치 |
|---|---|
| Step 1 Input | `main.py`의 `--topic`, `--keywords` 인자 |
| Step 2 Retrieval | `src/tasks.py`의 `retrieval_task` (Literature Agent) |
| Step 3 Analysis & Synthesis | `src/tasks.py`의 `analysis_task` (Summarizer Agent) |
| Step 4 Quality Check | `src/tasks.py`의 `quality_task` (Quality Reviewer Agent) — **문서에는 없던 별도 에이전트로 구현** |
| Step 5 Output | `main.py`의 `save_output()` → `outputs/research_summary_{timestamp}.md` |

원래 문서는 Step 4를 "LLM 자체 검증"이라고만 적어놨는데, 실제로는 같은 에이전트가 스스로를 검증하면
느슨해지기 쉬워서 **별도의 Quality Reviewer 에이전트**를 하나 더 두고 Sequential Task로 연결했습니다.

## 빠른 시작

```bash
pip install -r requirements.txt
cp .env.example .env
# .env에 GROQ_API_KEY 입력 (학술 검색 API 키들은 선택)

python main.py --topic "원격 교육 환경에서 피드백 유형이 몰입도에 미치는 영향" \
                --keywords "remote learning feedback type engagement"
```

Groq 모델은 CrewAI의 LiteLLM 연동을 사용하므로 `requirements.txt`에서
`crewai[litellm]`을 설치한다.

## 모델 라우팅

- 자료 수집(단순 추출): `groq/llama-3.1-8b-instant` — 무료 한도 절약
- 분석/종합/품질 검증: `groq/llama-3.3-70b-versatile` — 품질 우선

`config/settings.py`에서 조정할 수 있습니다.

## 웹 UI로 실행하기

CLI가 아니라 브라우저에서 쓸 수 있도록 Streamlit 웹 UI(`app.py`)를 제공한다.

```bash
pip install -r requirements.txt
cp .env.example .env   # .env에 GROQ_API_KEY 입력
streamlit run app.py
```

## 주의사항

- CrewAI는 내부적으로 LLM 호출이 많아(에이전트 3개 × Task마다 여러 번) 순수 API 직접 호출 방식보다
  토큰 비용이 더 발생합니다. 비용이 걱정되면 먼저 `max_papers_per_topic`을 낮춰 테스트하세요.
- 해외 문헌은 ERIC을 기본으로 검색합니다. 키가 있으면 Education 분야로 제한한 OpenAlex,
  Semantic Scholar, CORE 결과를 추가합니다. 국내 문헌은 `KCI_API_KEY`가 있을 때 한글로 검색합니다.
- RISS API는 공식 정책상 비영리 기관·대학 대상이므로 개인 배포에는 연결하지 않습니다.
- `verbose=True`로 되어 있어 실행 중 에이전트의 사고 과정이 콘솔에 출력됩니다. 프로덕션에서는 끄는 것을 권장합니다.
