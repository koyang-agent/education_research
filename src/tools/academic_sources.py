"""교육학 문헌 소스별 API 커넥터와 결과 병합."""
import html
import os
import xml.etree.ElementTree as ET

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from src.tools.openalex_tool import search_education_literature


def _record(title: str, url: str, published: str, authors: str, journal: str,
            topic: str, abstract: str, source: str) -> dict:
    return {
        "title": html.unescape(title).strip(),
        "url": url.strip(),
        "published": str(published),
        "authors": authors.strip() or "정보 없음",
        "journal": journal.strip() or "정보 없음",
        "education_topic": topic.strip() or "Education",
        "citations": 0,
        "abstract": html.unescape(abstract).strip()[:700] or "초록 정보 없음",
        "source": source,
    }


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def search_eric(query: str, limit: int) -> list[dict]:
    response = requests.get(
        "https://api.ies.ed.gov/eric/",
        params={"search": f"({query}) AND peerreviewed:T", "format": "json", "rows": limit},
        timeout=20,
    )
    response.raise_for_status()
    records = []
    for item in response.json().get("response", {}).get("docs", []):
        eric_id = item.get("id", "")
        if not eric_id:
            continue
        records.append(_record(
            item.get("title", ""), f"https://eric.ed.gov/?id={eric_id}",
            item.get("publicationdateyear", "정보 없음"),
            ", ".join(item.get("author", [])), item.get("publisher", "ERIC"),
            ", ".join(item.get("subject", [])[:4]), item.get("description", ""), "ERIC",
        ))
    return records


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
def search_semantic_scholar(query: str, limit: int) -> list[dict]:
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if not api_key:
        return []
    response = requests.get(
        "https://api.semanticscholar.org/graph/v1/paper/search/bulk",
        params={"query": query, "fieldsOfStudy": "Education", "limit": limit,
                "fields": "title,url,abstract,authors,year,venue,externalIds,fieldsOfStudy"},
        headers={"x-api-key": api_key}, timeout=20,
    )
    response.raise_for_status()
    records = []
    for item in response.json().get("data", []):
        external = item.get("externalIds") or {}
        doi = external.get("DOI")
        url = f"https://doi.org/{doi}" if doi else item.get("url", "")
        if not url:
            continue
        records.append(_record(
            item.get("title", ""), url, item.get("year", "정보 없음"),
            ", ".join(author.get("name", "") for author in item.get("authors", [])),
            item.get("venue", "Semantic Scholar"), "Education",
            item.get("abstract") or "", "Semantic Scholar",
        ))
    return records


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
def search_core(query: str, limit: int) -> list[dict]:
    api_key = os.getenv("CORE_API_KEY")
    if not api_key:
        return []
    response = requests.get(
        "https://api.core.ac.uk/v3/search/works",
        params={"q": f'({query}) AND (education OR teaching OR learning)', "limit": limit},
        headers={"Authorization": f"Bearer {api_key}"}, timeout=20,
    )
    response.raise_for_status()
    records = []
    for item in response.json().get("results", []):
        doi = item.get("doi")
        url = f"https://doi.org/{doi}" if doi else item.get("downloadUrl") or item.get("id", "")
        if not str(url).startswith("http"):
            continue
        raw_authors = item.get("authors", [])
        authors = [
            author.get("name", "") if isinstance(author, dict) else str(author)
            for author in raw_authors
        ]
        records.append(_record(
            item.get("title", ""), str(url), item.get("yearPublished", "정보 없음"),
            ", ".join(author for author in authors if author), item.get("publisher", "CORE"),
            "Education", item.get("abstract", ""), "CORE",
        ))
    return records


def _xml_text(element: ET.Element, *names: str) -> str:
    for node in element.iter():
        if node.tag.split("}")[-1].lower() in {name.lower() for name in names} and node.text:
            return node.text.strip()
    return ""


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
def search_kci(query: str, limit: int) -> list[dict]:
    api_key = os.getenv("KCI_API_KEY")
    if not api_key or not query.strip():
        return []
    response = requests.get(
        "https://open.kci.go.kr/po/openapi/openApiSearch.kci",
        params={"apiCode": "articleSearch", "key": api_key, "title": query,
                "displayCount": limit},
        timeout=20,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    records = []
    for item in root.iter():
        title = _xml_text(item, "title", "article-title", "artiTitle")
        article_id = _xml_text(item, "id", "article-id", "artiId")
        if not title or not article_id:
            continue
        url = (article_id if article_id.startswith("http") else
               f"https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?"
               f"sereArticleSearchBean.artiId={article_id}")
        records.append(_record(
            title, url, _xml_text(item, "pubiYr", "year", "date") or "정보 없음",
            _xml_text(item, "author", "creator"), _xml_text(item, "journal", "publisher"),
            "국내 교육학", _xml_text(item, "abstract", "description"), "KCI",
        ))
        if len(records) >= limit:
            break
    return records


def search_all_sources(english_query: str, korean_query: str, limit: int) -> list[dict]:
    """영문·국문 소스를 검색하고 출처를 순환하며 중복 없이 합친다."""
    sources = [search_eric(english_query, limit)]
    if os.getenv("OPENALEX_API_KEY"):
        sources.append(search_education_literature(english_query, limit))
        for record in sources[-1]:
            record["source"] = "OpenAlex"
    sources.extend([search_semantic_scholar(english_query, limit), search_core(english_query, limit)])
    if korean_query.strip():
        sources.append(search_kci(korean_query, limit))

    merged: list[dict] = []
    seen: set[str] = set()
    for index in range(limit):
        for source in sources:
            if index >= len(source):
                continue
            record = source[index]
            key = record["url"].lower().rstrip("/")
            if key not in seen:
                seen.add(key)
                merged.append(record)
            if len(merged) >= limit:
                return merged
    return merged
