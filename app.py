"""
교육학 자동 연구 에이전트 - Streamlit 웹 UI

로컬 실행:
    streamlit run app.py

클라우드 배포 (설치 없이 링크로 접속):
    Streamlit Community Cloud 또는 Hugging Face Spaces에 이 저장소를 연결하면 된다.
    자세한 절차는 README.md의 "클라우드 배포" 섹션 참고.
"""
import json
import hmac
import os
import re
import time
import uuid
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote

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
for _key in (
    "APP_PASSWORD",
    "GROQ_API_KEY",
    "OPENALEX_API_KEY",
    "SEMANTIC_SCHOLAR_API_KEY",
    "CORE_API_KEY",
    "KCI_API_KEY",
):
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
        --canvas: var(--background-color, #f7f8fa);
        --surface: var(--secondary-background-color, #ffffff);
        --ink: var(--text-color, #17181a);
        --muted: color-mix(in srgb, var(--ink) 62%, transparent);
        --line: color-mix(in srgb, var(--ink) 14%, transparent);
        --accent: var(--primary-color, #5e6ad2);
        --accent-dark: color-mix(in srgb, var(--accent) 82%, black);
        --soft-accent: color-mix(in srgb, var(--accent) 12%, var(--canvas));
    }

    .stApp {
        background:
            radial-gradient(circle at 50% -20%, var(--soft-accent), transparent 34rem),
            var(--canvas);
        color: var(--ink);
    }

    .block-container {
        max-width: 850px;
        padding-top: 6.5rem;
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
        box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--canvas) 20%, transparent);
        height: 18px;
        position: relative;
        width: 18px;
    }

    .brand-mark::after {
        background: var(--canvas);
        border-radius: 1px;
        content: "";
        height: 6px;
        left: 6px;
        position: absolute;
        top: 6px;
        width: 6px;
    }

    .status-pill {
        background: color-mix(in srgb, var(--surface) 82%, transparent);
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
        background: color-mix(in srgb, var(--surface) 94%, transparent);
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 1px 2px color-mix(in srgb, var(--ink) 4%, transparent),
                    0 16px 40px color-mix(in srgb, var(--ink) 6%, transparent);
        padding: 1.65rem 1.65rem 1.2rem;
    }

    [data-testid="stWidgetLabel"] p {
        color: var(--ink);
        font-size: 0.78rem;
        font-weight: 620;
    }

    .stTextInput input {
        background: var(--canvas);
        border: 1px solid var(--line);
        color: var(--ink);
        border-radius: 8px;
        min-height: 46px;
    }

    .stTextInput input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px var(--soft-accent);
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
        box-shadow: 0 6px 18px color-mix(in srgb, var(--accent) 25%, transparent);
        color: white;
        transform: translateY(-1px);
    }

    .stDownloadButton button {
        background: var(--surface);
        border: 1px solid var(--line);
        color: var(--ink);
    }

    .stDownloadButton button:hover {
        background: color-mix(in srgb, var(--ink) 6%, var(--surface));
        border-color: color-mix(in srgb, var(--accent) 45%, var(--line));
        color: var(--ink);
    }

    .workflow {
        align-items: center;
        color: var(--muted);
        display: flex;
        font-size: 0.72rem;
        gap: 0.55rem;
        margin: 1.25rem 0 4rem;
    }

    .workflow strong { color: var(--ink); font-weight: 580; }
    .workflow-line { background: var(--line); height: 1px; width: 22px; }

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

    .reference-card {
        align-items: flex-start;
        background: color-mix(in srgb, var(--surface) 90%, transparent);
        border: 1px solid var(--line);
        border-radius: 11px;
        color: var(--ink) !important;
        display: flex;
        gap: 1rem;
        margin-bottom: .7rem;
        padding: 1rem 1.05rem;
        text-decoration: none !important;
        transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
    }

    .reference-card:hover {
        border-color: color-mix(in srgb, var(--accent) 40%, var(--line));
        box-shadow: 0 8px 24px color-mix(in srgb, var(--ink) 8%, transparent);
        transform: translateY(-1px);
    }

    .reference-index {
        align-items: center;
        background: color-mix(in srgb, var(--ink) 8%, var(--surface));
        border-radius: 6px;
        color: var(--muted);
        display: flex;
        flex: 0 0 30px;
        font-size: .68rem;
        font-weight: 700;
        height: 30px;
        justify-content: center;
    }

    .reference-title { display: block; font-size: .9rem; font-weight: 620; line-height: 1.45; }
    .reference-meta { color: var(--muted); display: block; font-size: .72rem; margin-top: .3rem; }
    .reference-arrow { color: var(--muted); margin-left: auto; padding-top: .2rem; }

    .detail-back {
        color: var(--muted) !important;
        display: inline-block;
        font-size: .78rem;
        margin-bottom: 2.5rem;
        text-decoration: none !important;
    }

    .detail-title {
        font-size: clamp(1.75rem, 5vw, 2.7rem);
        letter-spacing: -.04em;
        line-height: 1.12;
        margin: .7rem 0 1rem;
    }

    .detail-meta { color: var(--muted); font-size: .8rem; margin-bottom: 2.4rem; }

    .analysis-grid {
        display: grid;
        gap: .8rem;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        margin: 1rem 0 2rem;
    }

    .analysis-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 1.05rem;
    }

    .analysis-card.wide { grid-column: 1 / -1; }
    .analysis-label { color: var(--accent); font-size: .65rem; font-weight: 700; letter-spacing: .08em; margin-bottom: .55rem; text-transform: uppercase; }
    .analysis-text { color: var(--ink); font-size: .84rem; line-height: 1.65; }

    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        letter-spacing: -0.025em;
    }

    [data-testid="stAlert"] { border-radius: 10px; }

    footer { visibility: hidden; }

    @media (max-width: 640px) {
        .block-container { padding: 5.5rem 1.1rem 3rem; }
        .app-nav { margin-bottom: 3.2rem; }
        .hero-title { font-size: 2.65rem; }
        .hero-copy { font-size: .92rem; }
        [data-testid="stForm"] { padding: 1.15rem 1.1rem .8rem; }
        .workflow { gap: .38rem; overflow-x: auto; white-space: nowrap; }
        .analysis-grid { grid-template-columns: 1fr; }
        .analysis-card.wide { grid-column: auto; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _require_password() -> None:
    """Streamlit 이메일 로그인 대신 앱 공용 비밀번호로 접근을 제한한다."""
    if st.session_state.get("password_authenticated"):
        return

    st.markdown(
        """
        <div class="app-nav">
            <div class="brand"><span class="brand-mark"></span> Education Research Desk</div>
            <div class="status-pill"><span class="status-dot"></span>Private access</div>
        </div>
        <div class="eyebrow">Secure workspace</div>
        <h1 class="hero-title">연구 공간에<br>접속합니다.</h1>
        <p class="hero-copy">공유받은 비밀번호를 입력해주세요.</p>
        """,
        unsafe_allow_html=True,
    )

    expected_password = os.environ.get("APP_PASSWORD", "")
    if not expected_password:
        st.error("APP_PASSWORD가 설정되지 않았습니다. Streamlit Secrets를 확인해주세요.")
        st.stop()

    with st.form("password_form", clear_on_submit=True):
        entered_password = st.text_input(
            "비밀번호",
            type="password",
            placeholder="비밀번호 입력",
        )
        submitted_password = st.form_submit_button("접속하기  →")

    if submitted_password:
        if hmac.compare_digest(entered_password, expected_password):
            st.session_state["password_authenticated"] = True
            st.rerun()
        else:
            time.sleep(1)
            st.error("비밀번호가 올바르지 않습니다.")
    st.stop()


_require_password()

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
from src.result import ResearchResult  # noqa: E402


def _result_path(run_id: str) -> Path:
    """검증된 실행 ID에 대응하는 웹 결과 파일 경로를 반환한다."""
    if not re.fullmatch(r"[a-f0-9]{12}", run_id):
        raise ValueError("잘못된 결과 ID")
    return Path(settings.output_dir) / f"web_result_{run_id}.json"


def _save_web_result(topic: str, result: ResearchResult) -> str:
    run_id = uuid.uuid4().hex[:12]
    path = _result_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "topic": topic,
                "report": result.report,
                "references": [reference.to_dict() for reference in result.references],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return run_id


def _render_nav() -> None:
    st.markdown(
        """
        <div class="app-nav">
            <div class="brand"><span class="brand-mark"></span> Education Research Desk</div>
            <div class="status-pill"><span class="status-dot"></span>Research system online</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_reference_detail(run_id: str, reference_index: int) -> None:
    try:
        payload = json.loads(_result_path(run_id).read_text(encoding="utf-8"))
        reference = payload["references"][reference_index]
    except (ValueError, OSError, KeyError, IndexError, json.JSONDecodeError):
        st.error("참고문헌 상세 정보를 찾을 수 없습니다. 원래 결과 화면에서 다시 열어주세요.")
        st.stop()

    _render_nav()
    st.markdown(
        f'<a class="detail-back" href="?run={quote(run_id)}">← 연구 결과로 돌아가기</a>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="eyebrow">Reference analysis</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="detail-title">{escape(reference["title"])}</h1>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="detail-meta">{escape(reference["published"])} · {escape(payload["topic"])}</div>',
        unsafe_allow_html=True,
    )

    cards = (
        ("Abstract summary", reference["summary"], "wide"),
        ("Methodology", reference["methodology"], ""),
        ("Key findings", reference["findings"], ""),
        ("Why it matters", reference["relevance"], "wide"),
    )
    card_html = "".join(
        f'<div class="analysis-card {width}"><div class="analysis-label">{label}</div>'
        f'<div class="analysis-text">{escape(text)}</div></div>'
        for label, text, width in cards
    )
    st.markdown(f'<div class="analysis-grid">{card_html}</div>', unsafe_allow_html=True)
    st.link_button("논문 원문 열기  ↗", reference["url"], use_container_width=True)
    st.caption("분석 내용은 검색 시 확보한 초록을 기준으로 작성되며, 원문 전체의 내용과 다를 수 있습니다.")


def _render_saved_result(run_id: str) -> None:
    """저장된 실행의 보고서와 참고문헌 목록을 복원한다."""
    try:
        payload = json.loads(_result_path(run_id).read_text(encoding="utf-8"))
        references = payload["references"]
    except (ValueError, OSError, KeyError, json.JSONDecodeError):
        st.error("연구 결과를 찾을 수 없습니다. 새 연구를 시작해주세요.")
        st.stop()

    _render_nav()
    st.markdown('<a class="detail-back" href="./">← 새 연구 시작</a>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Research result</div>', unsafe_allow_html=True)
    st.markdown(
        f'<h1 class="detail-title">{escape(payload["topic"])}</h1>',
        unsafe_allow_html=True,
    )
    report_tab, references_tab = st.tabs(["보고서", f"참고문헌  {len(references)}"])
    with report_tab:
        st.markdown('<div class="section-label">Research report</div>', unsafe_allow_html=True)
        st.markdown(payload["report"])
    with references_tab:
        st.markdown('<div class="section-label">Reference library</div>', unsafe_allow_html=True)
        for index, reference in enumerate(references):
            detail_url = f"?run={quote(run_id)}&reference={index}"
            st.markdown(
                f'<a class="reference-card" href="{detail_url}" target="_blank">'
                f'<span class="reference-index">{index + 1:02d}</span>'
                f'<span><span class="reference-title">{escape(reference["title"])}</span>'
                f'<span class="reference-meta">{escape(reference["published"])} · 상세 분석 보기</span></span>'
                f'<span class="reference-arrow">↗</span></a>',
                unsafe_allow_html=True,
            )
    st.download_button(
        "보고서 내려받기  ↓",
        data=f'# {payload["topic"]}\n\n{payload["report"]}',
        file_name=f"research_summary_{run_id}.md",
        mime="text/markdown",
    )


run_param = st.query_params.get("run")
reference_param = st.query_params.get("reference")
if run_param and reference_param is not None:
    try:
        _render_reference_detail(str(run_param), int(reference_param))
    except ValueError:
        st.error("잘못된 참고문헌 링크입니다.")
    st.stop()
if run_param:
    _render_saved_result(str(run_param))
    st.stop()

_render_nav()
st.markdown(
    """
    <div class="eyebrow">Evidence-led research</div>
    <h1 class="hero-title">질문에서 근거까지,<br>한 번에 정리합니다.</h1>
    <p class="hero-copy">
        연구 주제와 검색어를 입력하면 관련 문헌을 탐색하고, 교육학적 관점에서 분석한 뒤
        근거와 한계를 점검한 보고서를 작성합니다.
    </p>
    """,
    unsafe_allow_html=True,
)

with st.form("research_form"):
    topic = st.text_input(
        "연구 주제",
        placeholder="예: 원격 교육 환경에서 피드백 유형이 몰입도에 미치는 영향",
    )
    keywords = st.text_input(
        "영문 검색어",
        placeholder="예: remote learning feedback type engagement",
        help="ERIC 및 활성화된 해외 학술 API 검색에 사용할 영문 핵심 단어를 입력하세요.",
    )
    korean_keywords = st.text_input(
        "한글 검색어",
        placeholder="예: 원격교육 피드백 학습 몰입",
        help="KCI 키가 설정된 경우 국내 논문 검색에 사용합니다. 비워두면 연구 주제를 사용합니다.",
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
            result = run_research(
                topic=topic,
                keywords=keywords,
                korean_keywords=korean_keywords,
            )
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.stop()

    st.success("분석이 완료되었습니다.")
    report_tab, references_tab = st.tabs(["보고서", f"참고문헌  {len(result.references)}"])

    with report_tab:
        st.markdown('<div class="section-label">Research report</div>', unsafe_allow_html=True)
        st.markdown(result.report)

    with references_tab:
        st.markdown('<div class="section-label">Reference library</div>', unsafe_allow_html=True)
        if result.references:
            run_id = _save_web_result(topic, result)
            for index, reference in enumerate(result.references):
                detail_url = f"?run={quote(run_id)}&reference={index}"
                st.markdown(
                    f'<a class="reference-card" href="{detail_url}" target="_blank">'
                    f'<span class="reference-index">{index + 1:02d}</span>'
                    f'<span><span class="reference-title">{escape(reference.title)}</span>'
                    f'<span class="reference-meta">{escape(reference.published)} · 상세 분석 보기</span></span>'
                    f'<span class="reference-arrow">↗</span></a>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("이번 결과에서는 구조화된 참고문헌을 추출하지 못했습니다. 보고서 내 출처 링크를 확인해주세요.")

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_content = f"# {topic}\n\n*생성일: {generated_at}*\n\n{result.report}"
    st.download_button(
        "보고서 내려받기  ↓",
        data=file_content,
        file_name=f"research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
    )
