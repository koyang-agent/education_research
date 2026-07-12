"""
교육학 자동 연구 에이전트 - 메인 진입점

사용법:
    python main.py --topic "원격 교육 환경에서 피드백 유형이 몰입도에 미치는 영향" \\
                    --keywords "remote learning feedback engagement"
"""
import argparse
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from config.settings import settings  # noqa: E402  (load_dotenv 이후 임포트되어야 함)
from src.crew import run_research  # noqa: E402


def save_output(topic: str, content: str) -> str:
    os.makedirs(settings.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(settings.output_dir, f"research_summary_{timestamp}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {topic}\n\n*생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n{content}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="교육학 자동 연구 에이전트 (CrewAI 기반)")
    parser.add_argument("--topic", required=True, help="연구 주제 (한글)")
    parser.add_argument("--keywords", required=True, help="검색용 영문 핵심 키워드")
    args = parser.parse_args()

    print(f"=== 리서치 시작: {args.topic} ===")
    report = run_research(topic=args.topic, keywords=args.keywords)

    path = save_output(args.topic, report)
    print(f"\n=== 완료: 보고서 저장 위치 -> {path} ===")


if __name__ == "__main__":
    main()
