"""
교육학 자동 연구 에이전트 - Streamlit 웹 UI

로컬 실행:
    streamlit run app.py

클라우드 배포 (설치 없이 링크로 접속):
    Streamlit Community Cloud 또는 Hugging Face Spaces에 이 저장소를 연결하면 된다.
    자세한 절차는 README.md의 "클라우드 배포" 섹션 참고.
"""
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _load_secret(key: str) -> str | None:
    """st.secrets에서 값을 읽는다. secrets.toml이 없거나 키가 없으면 None."""
    try:
        return st.secrets[key]
    except Exception:
        return None


# Streamlit Community Cloud / Hugging Face Spaces에서는 API 키를 st.secrets로 주입한다.
# config.settings의 Settings(pydantic-settings)는 환경변수를 읽으므로, 여기서 미리 반영해둔다.
for _key in ("GROQ_API_KEY", "SERPER_API_KEY"):
    _value = _load_secret(_key)
    if _value and not os.environ.get(_key):
        os.environ[_key] = str(_value)

st.set_page_config(
    page_title="Education Research Desk",
    page_icon="◼",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --canvas: #f7f8fa;
        --surface: #ffffff;
        --ink: #17181a;
        --muted: #6d7178;
        --line: #e6e8eb;
        --accent: #5e6ad2;
        --accent-dark: #4f5bc4;
    }

    .stApp {
        background:
            radial-gradient(circle at 50% -20%, rgba(94, 106, 210, 0.10), transparent 34rem),
            var(--canvas);
        color: var(--ink);
    }

    .block-container {
        max-width: 850px;
        padding-top: 3rem;
        padding-bottom: 5rem;
    }

    .app-nav {
        align-items: center;
        display: flex;
        justify-content: space-between;
        margin-bottom: 4.5rem;
    }

    .brand {
        align-items: center;
        display: flex;
        font-size: 0.86rem;
        font-weight: 650;
        gap: 0.65rem;
        letter-spacing: -0.01em;
    }

    .brand-mark {
        background: var(--ink);
        border-radius: 4px;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,.16);
        height: 18px;
        position: relative;
        width: 18px;
    }

    .brand-mark::after {
        background: #ffffff;
        border-radius: 1px;
        content: "";
        height: 6px;
        left: 6px;
        position: absolute;
        top: 6px;
        width: 6px;
    }

    .status-pill {
        background: rgba(255,255,255,.7);
        border: 1px solid var(--line);
        border-radius: 999px;
        color: var(--muted);
        font-size: 0.72rem;
        padding: 0.36rem 0.65rem;
    }

    .status-dot {
        background: #37a26c;
        border-radius: 50%;
        display: inline-block;
        height: 6px;
        margin-right: 0.4rem;
        width: 6px;
    }

    .eyebrow {
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        margin-bottom: 0.9rem;
        text-transform: uppercase;
    }

    .hero-title {
        font-size: clamp(2.25rem, 7vw, 4.25rem);
        font-weight: 620;
        letter-spacing: -0.055em;
        line-height: 0.98;
        margin: 0;
        max-width: 720px;
    }

    .hero-copy {
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.7;
        margin: 1.5rem 0 2.5rem;
        max-width: 570px;
    }

    [data-testid="stForm"] {
        background: rgba(255,255,255,.9);
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 1px 2px rgba(20, 24, 32, .03), 0 16px 40px rgba(20, 24, 32, .045);
        padding: 1.65rem 1.65rem 1.2rem;
    }

    [data-testid="stWidgetLabel"] p {
        color: #383b40;
        font-size: 0.78rem;
        font-weight: 620;
    }

    .stTextInput input {
        background: #fbfbfc;
        border: 1px solid #dcdee2;
        border-radius: 8px;
        min-height: 46px;
    }

    .stTextInput input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(94,106,210,.12);
    }

    .stButton button, .stFormSubmitButton button, .stDownloadButton button {
        border-radius: 8px;
        font-weight: 620;
        min-height: 44px;
        transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
    }

    .stFormSubmitButton button {
        background: var(--accent);
        border-color: var(--accent);
        color: white;
        width: 100%;
    }

    .stFormSubmitButton button:hover {
        background: var(--accent-dark);
        border-color: var(--accent-dark);
        box-shadow: 0 6px 18px rgba(94,106,210,.22);
        color: white;
        transform: translateY(-1px);
    }

    .workflow {
        align-items: center;
        color: #8b8f96;
        display: flex;
        font-size: 0.72rem;
        gap: 0.55rem;
        margin: 1.25rem 0 4rem;
    }

    .workflow strong { color: #4b4f55; font-weight: 580; }
    .workflow-line { background: #dfe1e5; height: 1px; width: 22px; }

    .section-label {
        border-bottom: 1px solid var(--line);
        color: var(--muted);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: .1em;
        margin: 3.5rem 0 1.25rem;
        padding-bottom: .75rem;
        text-transform: uppercase;
    }

    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        letter-spacing: -0.025em;
    }

    [data-testid="stAlert"] { border-radius: 10px; }

    footer { visibility: hidden; }

    @media (max-width: 640px) {
        .block-container { padding: 1.5rem 1.1rem 3rem; }
        .app-nav { margin-bottom: 3.2rem; }
        .hero-title { font-size: 2.65rem; }
        .hero-copy { font-size: .92rem; }
        [data-testid="stForm"] { padding: 1.15rem 1.1rem .8rem; }
        .workflow { gap: .38rem; overflow-x: auto; white-space: nowrap; }
    }
    </style>

    <div class="app-nav">
        <div class="brand"><span class="brand-mark"></span> Education Research Desk</div>
        <div class="status-pill"><span class="status-dot"></span>Research system online</div>
    </div>
    <div class="eyebrow">Evidence-led research</div>
    <h1 class="hero-title">질문에서 근거까지,<br>한 번에 정리합니다.</h1>
    <p class="hero-copy">
        연구 주제와 검색어를 입력하면 관련 문헌을 탐색하고, 교육학적 관점에서 분석한 뒤
        근거와 한계를 점검한 보고서를 작성합니다.
    </p>
    """,
    unsafe_allow_html=True,
)

try:
    from config.settings import settings
except Exception:
    settings = None

if settings is None or not settings.groq_api_key:
    st.error(
        "GROQ_API_KEY가 설정되지 않았습니다. "
        "배포 환경의 Secrets 설정을 확인해주세요. (관리자에게 문의)"
    )
    st.stop()

from src.crew import run_research  # noqa: E402

with st.form("research_form"):
    topic = st.text_input(
        "연구 주제",
        placeholder="예: 원격 교육 환경에서 피드백 유형이 몰입도에 미치는 영향",
    )
    keywords = st.text_input(
        "영문 검색어",
        placeholder="예: remote learning feedback type engagement",
        help="논문 검색(arXiv 등)에 사용할 영문 핵심 단어를 입력하세요.",
    )
    submitted = st.form_submit_button("문헌 조사 시작  →")

st.markdown(
    """
    <div class="workflow" aria-label="연구 진행 단계">
        <strong>01 문헌 탐색</strong><span class="workflow-line"></span>
        <strong>02 근거 분석</strong><span class="workflow-line"></span>
        <strong>03 품질 검토</strong><span class="workflow-line"></span>
        <strong>04 보고서</strong>
    </div>
    """,
    unsafe_allow_html=True,
)

if submitted:
    if not topic.strip() or not keywords.strip():
        st.warning("연구 주제와 영문 키워드를 모두 입력해주세요.")
        st.stop()

    with st.spinner("문헌 탐색과 근거 분석을 진행하고 있습니다. 잠시만 기다려 주세요."):
        try:
            report = run_research(topic=topic, keywords=keywords)
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.stop()

    st.success("분석이 완료되었습니다.")
    st.markdown('<div class="section-label">Research report</div>', unsafe_allow_html=True)
    st.markdown(report)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_content = f"# {topic}\n\n*생성일: {generated_at}*\n\n{report}"
    st.download_button(
        "보고서 내려받기  ↓",
        data=file_content,
        file_name=f"research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
    )
