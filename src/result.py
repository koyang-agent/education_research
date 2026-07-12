"""연구 실행 결과와 참고문헌 메타데이터 모델."""
from dataclasses import asdict, dataclass


@dataclass
class Reference:
    title: str
    url: str
    published: str
    summary: str
    methodology: str
    findings: str
    relevance: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class ResearchResult:
    report: str
    references: list[Reference]

    def __str__(self) -> str:
        """기존 CLI의 문자열 저장 동작을 유지한다."""
        return self.report
