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

st.set_page_config(page_title="교육학 자동 연구 에이전트", page_icon="📚")
st.title("📚 교육학 자동 연구 에이전트")
st.caption("연구 주제를 입력하면 문헌 조사 → 분석 → 품질 검증을 자동으로 수행해 보고서를 작성합니다.")

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
        "연구 주제 (한글)",
        placeholder="예: 원격 교육 환경에서 피드백 유형이 몰입도에 미치는 영향",
    )
    keywords = st.text_input(
        "검색용 영문 키워드",
        placeholder="예: remote learning feedback type engagement",
        help="논문 검색(arXiv 등)에 사용할 영문 핵심 단어를 입력하세요.",
    )
    submitted = st.form_submit_button("연구 시작")

if submitted:
    if not topic.strip() or not keywords.strip():
        st.warning("연구 주제와 영문 키워드를 모두 입력해주세요.")
        st.stop()

    with st.spinner("문헌을 조사하고 보고서를 작성하는 중입니다... (수 분 정도 걸릴 수 있어요)"):
        try:
            report = run_research(topic=topic, keywords=keywords)
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.stop()

    st.success("완료되었습니다!")
    st.markdown(report)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_content = f"# {topic}\n\n*생성일: {generated_at}*\n\n{report}"
    st.download_button(
        "보고서 다운로드 (.md)",
        data=file_content,
        file_name=f"research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
    )
