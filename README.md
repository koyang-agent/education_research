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
│   │   ├── arxiv_tool.py    # arXiv 논문 검색 (키 불필요)
│   │   └── search_tool.py   # Serper 웹서치 (키 없으면 자동 생략)
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
# .env에 GROQ_API_KEY 입력 (SERPER_API_KEY는 선택 — 없으면 arXiv만 사용됨)

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

## 클라우드 배포 (설치 없이 링크로 공유하기)

설치 없이 "링크만 열면 되는" 버전이 필요하면 아래 두 방법 중 하나로 무료 배포할 수 있다.
둘 다 이 저장소가 **GitHub에 올라가 있어야** 한다 (Public repo 권장 — Private도 두 서비스 모두 지원은 하지만 계정 연결이 한 단계 더 필요함).

### 방법 A: Streamlit Community Cloud (추천)

1. 이 저장소를 GitHub에 push한다.
2. [share.streamlit.io](https://share.streamlit.io)에 GitHub 계정으로 로그인 후 "New app" 클릭.
3. 저장소 / 브랜치를 선택하고, Main file path에 `app.py` 입력.
4. 배포 전 **Settings → Secrets**에 아래 내용을 입력 (`.env`는 배포되지 않으므로 반드시 여기에 등록):
   ```toml
   GROQ_API_KEY = "gsk_..."
   SERPER_API_KEY = ""
   ```
5. Deploy 클릭 → 발급된 `https://xxxx.streamlit.app` 링크를 언니에게 공유하면 끝. 설치·실행 없이 링크만 열면 바로 사용 가능.
6. **접근 제한 (필수 권장)**: 배포된 앱 우측 하단 메뉴 → **Settings → Sharing**에서 "This app is public and searchable"을 끄고, "Invite viewers by email"에 언니의 구글 이메일만 등록한다. 이렇게 하면 링크를 알아도 등록된 구글 계정으로 로그인해야만 앱을 열 수 있어, API 키 남용(비용 발생)을 막을 수 있다. 무료 기능이며 앱 재배포 없이 대시보드에서 바로 설정 가능.

> 참고: 무료 플랜은 리소스가 제한적이고(≈1GB RAM), 일정 시간 미사용 시 앱이 sleep 상태가 되어 다음 접속 시 수십 초 정도 깨어나는 시간이 걸릴 수 있다.

### 방법 B: Hugging Face Spaces

1. [huggingface.co/new-space](https://huggingface.co/new-space)에서 새 Space 생성, SDK는 **Streamlit** 선택.
2. 이 저장소 파일들(`app.py`, `requirements.txt`, `src/`, `config/` 등)을 Space 저장소에 push (Git remote로 추가하거나 웹 UI로 업로드).
3. Space 페이지의 **Settings → Repository secrets**에 `GROQ_API_KEY`, `SERPER_API_KEY`를 등록.
4. 빌드가 끝나면 `https://huggingface.co/spaces/<사용자명>/<space명>` 링크를 공유하면 된다.

### 로컬에서 배포 전 미리 확인하기

`.streamlit/secrets.toml.example`을 참고해 `.streamlit/secrets.toml`을 만들면(둘 다 `.gitignore`에 등록되어 있어 커밋되지 않음) 로컬에서도 클라우드와 동일한 방식(`st.secrets`)으로 키를 읽는지 테스트할 수 있다.

## Claude Code로 이어서 개발하기

`claude.md`가 이미 프로젝트 루트에 있으므로, Claude Code CLI에서 바로 다음처럼 지시할 수 있습니다:

> "src/tools/에 ERIC API 연동 도구를 추가하고, Literature Agent가 arxiv_search와 함께 쓰도록 agents.py를 수정해줘."

`claude.md`의 "5. 확장 시 우선순위"에 다음 확장 순서를 이미 적어뒀습니다:
1. ERIC / RISS / KCI 연동 도구
2. Quality Check 반려 시 Literature Agent로 되돌아가는 재시도 루프 (이 지점부터 LangGraph 고려)
3. Slack/이메일 알림 + 스케줄링

## 주의사항

- CrewAI는 내부적으로 LLM 호출이 많아(에이전트 3개 × Task마다 여러 번) 순수 API 직접 호출 방식보다
  토큰 비용이 더 발생합니다. 비용이 걱정되면 먼저 `max_papers_per_topic`을 낮춰 테스트하세요.
- Serper API는 유료(무료 크레딧 있음)이므로, 없어도 arXiv만으로 최소 동작하도록 만들어뒀습니다.
- `verbose=True`로 되어 있어 실행 중 에이전트의 사고 과정이 콘솔에 출력됩니다. 프로덕션에서는 끄는 것을 권장합니다.
