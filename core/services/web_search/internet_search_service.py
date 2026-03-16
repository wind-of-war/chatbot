from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from configs.settings import settings


class InternetSearchService:
    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self) -> None:
        self.timeout_seconds = settings.internet_fallback_timeout_seconds
        self.max_results = settings.internet_fallback_max_results
        self.allowed_domains = tuple(
            d.strip().lower() for d in settings.internet_fallback_domains.split(",") if d.strip()
        )

    def enabled(self) -> bool:
        return settings.internet_fallback_enabled

    @staticmethod
    def _decode_result_url(raw_url: str) -> str:
        candidate = html.unescape(raw_url or "").strip()
        if candidate.startswith("//"):
            candidate = f"https:{candidate}"
        parsed = urlparse(candidate)
        if "duckduckgo.com" not in parsed.netloc:
            return candidate
        query = parse_qs(parsed.query)
        uddg = query.get("uddg", [])
        return unquote(uddg[0]) if uddg else candidate

    @staticmethod
    def _clean_html_text(value: str) -> str:
        text = re.sub(r"(?is)<script.*?>.*?</script>", " ", value or "")
        text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = html.unescape(text)
        return " ".join(text.split())

    def _is_allowed_domain(self, url: str) -> bool:
        if not self.allowed_domains:
            return True
        host = (urlparse(url).netloc or "").lower()
        return any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)

    def _search(self, question: str) -> list[dict]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            )
        }
        with httpx.Client(timeout=self.timeout_seconds, headers=headers, follow_redirects=True) as client:
            response = client.get(self.SEARCH_URL, params={"q": question})
            response.raise_for_status()
            payload = response.text

        links = re.findall(r'(?is)class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', payload)
        snippets = re.findall(r'(?is)class="result__snippet"[^>]*>(.*?)</.*?>', payload)

        results: list[dict] = []
        for idx, (raw_url, raw_title) in enumerate(links):
            url = self._decode_result_url(raw_url)
            title = self._clean_html_text(raw_title)
            snippet = self._clean_html_text(snippets[idx]) if idx < len(snippets) else ""
            results.append({"url": url, "title": title, "snippet": snippet})
        return results

    def _fetch_excerpt(self, url: str) -> str:
        if url.lower().endswith(".pdf"):
            return ""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            )
        }
        with httpx.Client(timeout=self.timeout_seconds, headers=headers, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            body = response.text[:200000]
        return self._clean_html_text(body)[:1600]

    def search(self, question: str, language: str) -> list[dict]:
        if not self.enabled():
            return []

        try:
            raw_results = self._search(question)
        except Exception:
            return []

        trusted = [item for item in raw_results if self._is_allowed_domain(item["url"])]
        selected = trusted if trusted else raw_results

        docs: list[dict] = []
        for item in selected[: self.max_results]:
            excerpt = ""
            try:
                excerpt = self._fetch_excerpt(item["url"])
            except Exception:
                excerpt = ""

            text = excerpt or item["snippet"] or item["title"]
            if not text:
                continue

            docs.append(
                {
                    "source": item["url"],
                    "section": item["title"] or "Web search",
                    "text": text,
                    "page_start": None,
                    "page_end": None,
                    "web_result": True,
                    "language": language,
                }
            )
        return docs
